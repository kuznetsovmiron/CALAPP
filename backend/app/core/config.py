import os
import json
from dotenv import load_dotenv
from pathlib import Path

# Link to .env
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

# Main
DB_LINK = os.environ.get("DB_LINK")
API_ROOT_PREFIX = os.environ.get("API_ROOT_PREFIX")

# Security
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_HOURS = os.environ.get("ACCESS_TOKEN_EXPIRE_HOURS")

# Google Auth
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET =  os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI =  os.environ.get("GOOGLE_REDIRECT_URI") + API_ROOT_PREFIX + "/handlers/callback"
GOOGLE_SCOPES = json.loads(os.environ.get("GOOGLE_SCOPES"))

# AI
AI_KEY = os.environ.get("AI_KEY")
AI_ASSISTANT_ID = os.environ.get("AI_ASSISTANT_ID")