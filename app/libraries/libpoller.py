import requests, asyncio
from random import randint
from datetime import datetime, timedelta
from fastapi import HTTPException
from app import db, API_KEY
from app.tools.p3log import P3Log
from app.libraries.libsnmp import get_snmp_value

class Poller:
    def __init__(self):
        self.p3log = P3Log("poller.log")
        self.poller_obj = None # poller database object for this poller
        self.poll_task = None        
        self.devices = []
    
    async def init_polling(self):     
        ''' Retrieves devices from database and starts polling loop
        '''   
        # get devices
        self.poller_obj = await db.fetchone("SELECT * FROM poller WHERE api_key = :api_key", {"api_key": API_KEY})
        if not self.poller_obj:
            raise HTTPException(status_code=500, detail="Poller not found in database. Please check API_KEY in .env file.")
        
        self.devices = [dict(d) for d in await db.fetchall("SELECT * FROM device WHERE pollerid = :pollerid", {"pollerid": self.poller_obj["pollerid"]})]        
        if len(self.devices) == 0:
            raise HTTPException(status_code=500, detail="No devices found assigned to this poller.")
        
        # Retrieve checks and check groups for each device
        for d in self.devices:
            checks = [dict(c) for c in await db.fetchall("SELECT * FROM device_check WHERE deviceid = :deviceid", {"deviceid": d["deviceid"]})]
            for check in checks:
                if check["device_check_groupid"]:
                    check["device_check_group"] = dict(await db.fetchone("SELECT * FROM device_check_group WHERE device_check_groupid = :device_check_groupid", {"device_check_groupid": check["device_check_groupid"]}))
                else:
                    check["device_check_group"] = {}
                    
            d["checks"] = checks

    # Main Polling Loop
    async def start_polling(self):
       devices = [Device(d, d["checks"]) for d in self.devices]
       tasks = [d.run_checks() for d in devices]       
       
       self.poll_task = True       
       await asyncio.gather(*tasks)
       print("Polling loop ended")
       self.poll_task = None
       

    async def perform_check(self):
        await asyncio.sleep(randint(1, 5))
        
                
class Device:
    def __init__(self, device, checks):
        self.device = device
        self.checks = checks
        
    async def run_checks(self):
        tasks = [self.schedule_check(check) for check in self.checks]
        await asyncio.gather(*tasks)
        
    async def schedule_check(self, check):
        interval = check["check_interval"]
        
        while True:
            next_poll = datetime.now() + timedelta(seconds=interval)
            print(f"[{datetime.now().isoformat()}] Device {self.device['name']}: Performing check '{check['name']}'")
            await self.perform_check(check)
            await asyncio.sleep(max(0, (next_poll - datetime.now()).total_seconds()))
        
        
    async def perform_check(self, check):
        # perform check
        # save result to database
        # await asyncio.sleep(randint(1, 5)) # simulate check taking 1-5 seconds
        
        if check["check_type"] == "snmp":
            if self.device["snmp_version"] == "2c":
                print(await get_snmp_value(
                    oid=check["oid"],
                    host=self.device["hostname"],
                    port=self.device["snmp_port"],
                    community=self.device["snmp_community"]                    
                ))
                
        await asyncio.sleep(randint(1, 2))
            