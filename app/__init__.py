import os
import secrets
from rich import print
from dotenv import load_dotenv
from app.tools.asyncdb import AsyncDB

# load environment variables from .env 
load_dotenv()

# db init #
db = AsyncDB()

# auth settings #
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM") or "HS256"

API_KEY = os.getenv("API_KEY", None)
        
if not SECRET_KEY:
    raise Exception("Missing required environment variable SECRET_KEY. Suggested: use 'openssl rand -hex 32' to create one and add it to the .env file.")
