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

INFLUXDB_TOKEN= os.getenv("INFLUXDB_TOKEN")
INFLUX_DB_HOST = os.getenv("INFLUX_DB_HOST")
INFLUX_DB_PORT = os.getenv("INFLUX_DB_PORT") or 8086
INFLUX_DB_ORG = os.getenv("INFLUX_DB_ORG")
INFLUX_DB_BUCKET = os.getenv("INFLUX_DB_BUCKET")
        
if not SECRET_KEY:
    raise Exception("Missing required environment variable SECRET_KEY. Suggested: use 'openssl rand -hex 32' to create one and add it to the .env file.")
