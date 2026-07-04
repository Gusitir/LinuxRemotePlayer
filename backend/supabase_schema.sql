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
begin
  select * into rec from licenses where token = p_token;
  if not found then
    return json_build_object('valid', false);
  end if;
  
  if rec.last_reset = to_char(current_date, 'YYYY-MM-DD') then
    rem_today := 60 - rec.commands_today;
  else
    rem_today := 60;
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
