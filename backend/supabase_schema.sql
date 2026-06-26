-- LinuxRemotePlayer — Supabase schema
-- Run this in the Supabase SQL editor before enabling cloud licensing/rate-limiting.

create table if not exists licenses (
    token          text primary key,
    commands_today integer     not null default 0,
    last_reset     text,                 -- ISO date 'YYYY-MM-DD' of the last counter reset
    created_at     timestamptz not null default now()
);

-- Row Level Security. The backend uses the service_role key, which bypasses RLS.
alter table licenses enable row level security;

-- No anon policies by default: only the backend (service_role) may read/write.
-- If you later expose anon access, add explicit policies here.

-- Optional: seed a development license token.
-- insert into licenses (token, last_reset) values ('dev-token-123', null);
