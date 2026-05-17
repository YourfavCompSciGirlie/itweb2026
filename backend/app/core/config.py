from dotenv import load_dotenv
import os

load_dotenv()

VONAGE_API_KEY = os.getenv("VONAGE_API_KEY")
VONAGE_API_SECRET = os.getenv("VONAGE_API_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY", "dev-secret")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")