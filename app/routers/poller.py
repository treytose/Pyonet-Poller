from datetime import timedelta
from fastapi import APIRouter, Depends, Form, HTTPException
from pydantic import ValidationError
from app.dependencies import verify_api_key
from app.libraries.libutil import Util

router = APIRouter(tags=["poller"], dependencies=[Depends(verify_api_key)])
oUtil = Util()

@router.get("/poller/scan-interfaces")
async def scan_interfaces(deviceid: int, api_key = Depends(verify_api_key)):
  return await oUtil.scan_device_interfaces(deviceid)

@router.get("/poller/scan-storage")
async def scan_storage(deviceid: int, api_key = Depends(verify_api_key)):
  return await oUtil.scan_device_storage(deviceid)
