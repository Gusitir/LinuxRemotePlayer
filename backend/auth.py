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
        res = supabase.table('licenses').select('commands_today').eq('token', token).execute()
        
        if not res.data:
            return False
            
        commands = res.data[0].get('commands_today', 0)
        if commands >= 60:
            print("Fair use policy exceeded.")
            return False
            
        # Increment usage counter
        supabase.table('licenses').update({'commands_today': commands + 1}).eq('token', token).execute()
        return True
    except Exception as e:
        print(f"License check error: {e}")
        return False
