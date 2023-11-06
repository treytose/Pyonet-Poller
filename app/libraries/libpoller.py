''' This is the main polling loop. It is started by calling oPoller.start_polling() from main.py.
'''

import requests, asyncio
from asyncio import Queue
from random import randint
from datetime import datetime, timedelta
from fastapi import HTTPException
from app import db, API_KEY
from app.tools.p3log import P3Log
from app.libraries.libsnmp import get_snmp_value
from app.libraries.libinfluxdb import InfluxDB

class Poller:
    def __init__(self):
        self.p3log = P3Log("poller.log")
        self.poller_obj = None # poller database object for this poller
        self.devices = [] # list of dicts
                
        self.running = False
        self.STOP_SIGNAL = object() # sentinel object to stop polling loop
        self.polling_queue = Queue()
        self.polling_tasks = []                    
    
    async def _update_devices(self):
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
            
    async def update_device(self, deviceid):
        device = dict(await db.fetchone("SELECT * FROM device WHERE deviceid = :deviceid", {"deviceid": deviceid}))
        if not device:
            raise HTTPException(status_code=500, detail=f"Device with deviceid {deviceid} not found in database.")
        
        checks = [dict(c) for c in await db.fetchall("SELECT * FROM device_check WHERE deviceid = :deviceid", {"deviceid": deviceid})]
        for check in checks:
            if check["device_check_groupid"]:
                check["device_check_group"] = dict(await db.fetchone("SELECT * FROM device_check_group WHERE device_check_groupid = :device_check_groupid", {"device_check_groupid": check["device_check_groupid"]}))
            else:
                check["device_check_group"] = {}
                                        
        device["checks"] = checks
        
        found = False
        # find device in self.devices and replace it
        for i, d in enumerate(self.devices):
            if d["deviceid"] == deviceid:
                self.devices[i] = device
                found = True
                break       
            
        if not found:
            self.devices.append(device)
            await self.polling_queue.put(Device(device, device["checks"])) # add device to polling queue
            return
    
    async def remove_device(self, deviceid):
        found = False
        # find device in self.devices and remove it
        for i, d in enumerate(self.devices):
            if d["deviceid"] == deviceid:
                del self.devices[i]
                found = True
                break
            
        for i, task in enumerate(self.polling_tasks):
            if task["device"]["deviceid"] == deviceid:
                task["task"].cancel()
                del self.polling_tasks[i]
                break    
        
        if not found:
            raise HTTPException(status_code=500, detail=f"Device with deviceid {deviceid} not in polling queue.")
    
    async def stop_polling(self):     
        self.running = False     
        await self.polling_queue.put(self.STOP_SIGNAL) # add STOP_SIGNAL to queue to stop polling loop
        if self.polling_tasks:
            # cancel existing polling tasks
            for task in self.polling_tasks:
                task["task"].cancel()                
                try:
                    await task["task"]
                except asyncio.CancelledError:
                    pass
    
    async def init_polling(self):     
        ''' Retrieves devices from database and starts polling loop
        '''   
        # get devices
        self.poller_obj = await db.fetchone("SELECT * FROM poller WHERE api_key = :api_key", {"api_key": API_KEY})
        if not self.poller_obj:
            raise HTTPException(status_code=500, detail="Poller not found in database. Please check API_KEY in .env file.")
        
        await self._update_devices()
      
        
        self.polling_queue = Queue()
        self.polling_tasks = []
        
        for device in self.devices:
            await self.polling_queue.put(Device(device, device["checks"]))
        
    # Main Polling Loop
    async def start_polling(self):  
        self.running = True      
        while self.running:
            device_instance = await self.polling_queue.get() # This infinitely waits for a device to be added to the queue if it is empty
            if device_instance is self.STOP_SIGNAL:
                self.polling_queue.task_done()
                break
            
            task = asyncio.create_task(device_instance.run_checks())
            self.polling_tasks.append({
                "device": device_instance.device,
                "task": task
            })
                
class Device:
    def __init__(self, device, checks):
        self.device = device
        self.checks = checks
        self.influxdb = InfluxDB()      
        self.p3log = P3Log("poller.log")  
        
    async def run_checks(self):
        tasks = [self.schedule_check(check) for check in self.checks]
        await asyncio.gather(*tasks)
        
    async def schedule_check(self, check):
        interval = check["check_interval"]
        
        while True:
            next_poll = datetime.now() + timedelta(seconds=interval)
            # print(f"[{datetime.now().isoformat()}] Device {self.device['name']}: Performing check '{check['name']}'")
            await self.perform_check(check)
            await asyncio.sleep(max(0, (next_poll - datetime.now()).total_seconds()))
        
        
    async def perform_check(self, check):
        try:
            if check["check_type"] == "snmp":
                if self.device["snmp_version"] == "2c":
                    result = await get_snmp_value(
                        oid=check["oid"],
                        host=self.device["hostname"],
                        port=self.device["snmp_port"],
                        community=self.device["snmp_community"]                    
                    )
                    
                    print(f"[{datetime.now().isoformat()}] Device {self.device['name']}: Performing check '{check['name']}' with value '{result['value']}'")
                                                            
                    # await self.influxdb.store_check_result(
                    #     device_name=self.device["name"],
                    #     check_name=check["name"],
                    #     value=result["value"],
                    #     check_group_name=check["device_check_group"]["name"] if check["device_check_group"] else None
                    # )        
        except Exception as e:
            self.p3log.log_error(f"Error performing check '{check['name']}' for device '{self.device['name']}': {e}")
            