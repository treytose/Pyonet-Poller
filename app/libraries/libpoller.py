import requests, asyncio
from app import db
from app.tools.p3log import P3Log

class Poller:
    def __init__(self):
        self.p3log = P3Log("poller.log")
        self.poll_task = None        
        self.devices = []
    
    async def init_polling(self):     
        ''' Retrieves devices from Pyonet-API and starts the polling loop
        '''   
        try: 
            # Start polling loop
            loop = asyncio.get_event_loop()
            self.poll_task = loop.create_task(self.start_poll_loop())               

        except Exception as e:
            self.p3log.log_error(f"Initialization failed. Error: {str(e)}")
            return False

    # Main Polling Loop
    async def start_poll_loop(self):
        ''' Polls devices in a loop
        '''
        try:
            for i in range(10):
                await self.poll_devices()
                await asyncio.sleep(1)            
        except asyncio.CancelledError as e:
            self.p3log.log(f"Polling loop exited")
            return False

    async def poll_devices(self):
        for device in self.devices:
            print("Polling device: ", device["name"])            
        