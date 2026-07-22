-- LinuxRemotePlayer — Supabase schema
-- Run this in the Supabase SQL editor before enabling cloud licensing/rate-limiting.

create table if not exists licenses (
    token              text primary key,
    commands_today     integer     not null default 0,
    last_reset         text,                 -- ISO date 'YYYY-MM-DD' of the last counter reset
    created_at         timestamptz not null default now(),
    email              text,
    active             boolean     not null default true,
    plan               text        not null default 'lifetime',
    stripe_customer_id text,
    stripe_session_id  text unique
);

-- Row Level Security. The backend uses the service_role key, which bypasses RLS.
alter table licenses enable row level security;

-- Explicit RLS Policies
create policy "Allow service_role full access" on licenses
    for all to service_role using (true) with check (true);

-- No access for anon or authenticated users by default (denied by RLS when no policies exist for them)

-- Optional: seed a development license token.
-- insert into licenses (token, last_reset) values ('dev-token-123', null);


-- ==========================================
-- v2 MIGRATION (For existing databases)
-- ==========================================

alter table licenses add column if not exists email text;
alter table licenses add column if not exists active boolean not null default true;
alter table licenses add column if not exists plan text not null default 'lifetime';
alter table licenses add column if not exists stripe_customer_id text;
alter table licenses add column if not exists stripe_session_id text unique;


-- SEC-08: consume_command stored procedure (atomic counter and reset check)
create or replace function consume_command(p_token text)
returns boolean as $$
declare
  updated boolean;
begin
  update licenses
  set commands_today = case
                         when last_reset is null or last_reset <> to_char(current_date, 'YYYY-MM-DD') then 1
                         else commands_today + 1
                       end,
      last_reset = to_char(current_date, 'YYYY-MM-DD')
  where token = p_token and active = true and (
    last_reset is null 
    or last_reset <> to_char(current_date, 'YYYY-MM-DD') 
    or commands_today < 60
  );
  return found;
end;
$$ language plpgsql;


-- check_license(): validation helper without usage increment
create or replace function check_license(p_token text)
returns json as $$
declare
  rec record;
  rem_today int;
  quota int;
begin
  select * into rec from licenses where token = p_token;
  if not found then
    return json_build_object('valid', false);
  end if;
  
  select daily_quota into quota from plan_quotas where plan = rec.plan;
  quota := coalesce(quota, 60);
  if rec.last_reset = to_char(current_date, 'YYYY-MM-DD') then
    rem_today := quota - rec.commands_today;
  else
    rem_today := quota;
  end if;
  if rem_today < 0 then
    rem_today := 0;
  end if;
  
  return json_build_object(
    'valid', true,
    'active', rec.active,
    'plan', rec.plan,
    'remaining_today', rem_today
  );
end;
$$ language plpgsql;

-- Restrict stored procedure execution to service_role only
revoke execute on function consume_command(text) from public, anon, authenticated;
grant execute on function consume_command(text) to service_role;

revoke execute on function check_license(text) from public, anon, authenticated;
grant execute on function check_license(text) to service_role;


-- ==========================================
-- v3 MIGRATION (v1.9: ai-proxy + 1 dispositivo + antiabuso)
-- ==========================================

-- Cuota diaria por plan (extensible; hoy solo 'lifetime')
create table if not exists plan_quotas (
    plan        text primary key,
    daily_quota integer not null
);
insert into plan_quotas (plan, daily_quota) values ('lifetime', 60)
on conflict (plan) do update set daily_quota = excluded.daily_quota;
alter table plan_quotas enable row level security;
create policy "plan_quotas service_role" on plan_quotas
    for all to service_role using (true) with check (true);

-- Activaciones: 1 dispositivo simultaneo por key
create table if not exists activations (
    token        text primary key references licenses(token) on delete cascade,
    device_id    text        not null,
    activated_at timestamptz not null default now(),
    last_seen    timestamptz not null default now()
);
alter table activations enable row level security;
create policy "activations service_role" on activations
    for all to service_role using (true) with check (true);

-- Metricas de uso de voz (base de costos reales)
create table if not exists usage_log (
    id          bigint generated always as identity primary key,
    token       text        not null,
    device_id   text,
    ts          timestamptz not null default now(),
    audio_bytes integer,
    ok          boolean     not null default true
);
alter table usage_log enable row level security;
create policy "usage_log service_role" on usage_log
    for all to service_role using (true) with check (true);
create index if not exists usage_log_ts_idx on usage_log (ts);

-- Estado global del servicio (kill-switch + cap global diario)
create table if not exists service_state (
    key   text primary key,
    value jsonb not null
);
alter table service_state enable row level security;
create policy "service_state service_role" on service_state
    for all to service_role using (true) with check (true);
insert into service_state (key, value)
values ('voice', '{"enabled": true, "daily_global_cap": 2000}'::jsonb)
on conflict (key) do nothing;

-- claim_device: activa/renueva la key en un dispositivo.
-- Regla: sin dueno / mismo device / last_seen>72h -> activa. Otro device activo
-- -> 'in_use_elsewhere' (salvo p_force=true, que es la mudanza confirmada).
create or replace function claim_device(p_token text, p_device_id text, p_force boolean default false)
returns json as $$
declare
  lic record;
  act record;
begin
  select * into lic from licenses where token = p_token;
  if not found or not lic.active then
    return json_build_object('status', 'invalid');
  end if;

  select * into act from activations where token = p_token for update;
  if not found then
    insert into activations (token, device_id) values (p_token, p_device_id);
    return json_build_object('status', 'activated');
  end if;

  if act.device_id = p_device_id then
    update activations set last_seen = now() where token = p_token;
    return json_build_object('status', 'activated');
  end if;

  if p_force or act.last_seen < now() - interval '72 hours' then
    update activations
       set device_id = p_device_id, activated_at = now(), last_seen = now()
     where token = p_token;
    return json_build_object('status', 'activated', 'takeover', true);
  end if;

  return json_build_object('status', 'in_use_elsewhere', 'last_seen', act.last_seen);
end;
$$ language plpgsql;

-- release_device: liberacion explicita (uninstall.sh, best-effort)
create or replace function release_device(p_token text, p_device_id text)
returns boolean as $$
begin
  delete from activations where token = p_token and device_id = p_device_id;
  return found;
end;
$$ language plpgsql;

-- consume_voice: chequeo ATOMICO completo de un comando de voz.
-- kill-switch -> cap global -> licencia -> activacion device -> cuota por plan
-- -> incrementa contador + loguea metrica. Lo llama SOLO el ai-proxy.
create or replace function consume_voice(p_token text, p_device_id text, p_audio_bytes integer default null)
returns json as $$
declare
  svc jsonb;
  used_global int;
  lic record;
  act record;
  quota int;
  used int;
  today text := to_char(current_date, 'YYYY-MM-DD');
begin
  -- 1. kill-switch + cap global diario
  select value into svc from service_state where key = 'voice';
  if svc is null or not coalesce((svc->>'enabled')::boolean, true) then
    return json_build_object('ok', false, 'reason', 'service_disabled');
  end if;
  select count(*) into used_global from usage_log where ts >= current_date;
  if used_global >= coalesce((svc->>'daily_global_cap')::int, 2000) then
    return json_build_object('ok', false, 'reason', 'global_cap');
  end if;

  -- 2. licencia
  select * into lic from licenses where token = p_token for update;
  if not found or not lic.active then
    return json_build_object('ok', false, 'reason', 'invalid_license');
  end if;

  -- 3. activacion de dispositivo (heartbeat / auto-takeover >72h)
  select * into act from activations where token = p_token for update;
  if not found then
    insert into activations (token, device_id) values (p_token, p_device_id);
  elsif act.device_id <> p_device_id then
    if act.last_seen < now() - interval '72 hours' then
      update activations
         set device_id = p_device_id, activated_at = now(), last_seen = now()
       where token = p_token;
    else
      return json_build_object('ok', false, 'reason', 'in_use_elsewhere');
    end if;
  else
    update activations set last_seen = now() where token = p_token;
  end if;

  -- 4. cuota diaria por plan
  select daily_quota into quota from plan_quotas where plan = lic.plan;
  quota := coalesce(quota, 60);
  if lic.last_reset is distinct from today then
    used := 0;
  else
    used := lic.commands_today;
  end if;
  if used >= quota then
    return json_build_object('ok', false, 'reason', 'quota_exceeded', 'remaining_today', 0);
  end if;

  -- 5. consumir + loguear
  update licenses set commands_today = used + 1, last_reset = today where token = p_token;
  insert into usage_log (token, device_id, audio_bytes) values (p_token, p_device_id, p_audio_bytes);

  return json_build_object('ok', true, 'remaining_today', quota - used - 1, 'plan', lic.plan);
end;
$$ language plpgsql;

-- Solo service_role ejecuta los RPCs v3
revoke execute on function claim_device(text, text, boolean) from public, anon, authenticated;
grant execute on function claim_device(text, text, boolean) to service_role;

revoke execute on function release_device(text, text) from public, anon, authenticated;
grant execute on function release_device(text, text) to service_role;

revoke execute on function consume_voice(text, text, integer) from public, anon, authenticated;
grant execute on function consume_voice(text, text, integer) to service_role;
