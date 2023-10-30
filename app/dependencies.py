from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from app import API_KEY
from jwt.exceptions import ExpiredSignatureError, InvalidSignatureError


async def verify_api_key(api_key: str = Depends(APIKeyHeader(name="PYONET-POLLER-API-KEY"))):
    if not api_key or api_key == "null":
        raise HTTPException(status_code=401, detail="Not authenticated")          

    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Bad API key")

    return api_key