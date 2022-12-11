from datetime import timedelta
from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import ValidationError
from app import ACCESS_TOKEN_EXPIRE_MINUTES
from app.dependencies import verify_api_key

router = APIRouter()

@router.get("/auth/test")
async def test(api_key = Depends(verify_api_key)):
    return "API key is valid"