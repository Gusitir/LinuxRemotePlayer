import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase init error: {e}")

def validate_license_and_increment(token: str) -> bool:
    if not supabase:
        print("Warning: Supabase disabled or missing keys. Allowing request by default.")
        return True

    try:
        res = supabase.table('licenses').select('commands_today, last_reset').eq('token', token).execute()

        if not res.data:
            return False

        from datetime import date
        today = date.today().isoformat()
        row = res.data[0]
        commands = row.get('commands_today', 0) or 0
        if row.get('last_reset') != today:
            commands = 0
            supabase.table('licenses').update({'commands_today': 0, 'last_reset': today}).eq('token', token).execute()
        if commands >= 60:
            print("Fair use policy exceeded.")
            return False

        # Increment usage counter
        supabase.table('licenses').update({'commands_today': commands + 1}).eq('token', token).execute()
        return True
    except Exception as e:
        print(f"License check error: {e}")
        return False


PAIRING_TOKEN = os.getenv("PAIRING_TOKEN")


def verify_access(token: str) -> bool:
    """Access gate WITHOUT incrementing usage. Returns True if token may control host.
    Modes:
    - Supabase configured: token must exist in 'licenses' table.
    - Supabase off + PAIRING_TOKEN set: token must equal PAIRING_TOKEN.
    - Supabase off + no PAIRING_TOKEN: dev mode -> allow with warning.
    """
    if not token:
        return False
    if not supabase:
        if PAIRING_TOKEN:
            return token == PAIRING_TOKEN
        print("Warning: No Supabase and no PAIRING_TOKEN. Access control DISABLED (dev mode).")
        return True
    try:
        res = supabase.table('licenses').select('token').eq('token', token).execute()
        return bool(res.data)
    except Exception as e:
        print(f"Access check error: {e}")
        return False
