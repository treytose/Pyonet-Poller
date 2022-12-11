import requests, asyncio
from app import ACCESS_TOKEN, PYONET_API_URL, db
from app.tools.p3log import P3Log

class Poller:
    def __init__(self):
        self.p3log = P3Log("poller.log")
        self.poll_task = None        
        self.devices = []
    
    def test_access_token(self):
        try:
            r = requests.get(f"{PYONET_API_URL}/auth/test/api_key", headers={"Authorization": f"{ACCESS_TOKEN}"})
            r.raise_for_status()
            self.p3log.log_success("Successfully authenticated with Pyonet-API")
        except Exception as e:
            self.p3log.log_error(f"ACCESS_TOKEN is invalid. Suggested: generate a new access token from the Pyonet-Dashboard interface and add it to the .env file. {str(e)}")

    
    async def init_polling(self):        
        try: 
            r = requests.get(f"{PYONET_API_URL}/poller/devices", headers={"Authorization": ACCESS_TOKEN})
            r.raise_for_status()            
            self.devices = r.json()
            self.p3log.log_success(f"Successfully retrieved {len(self.devices)} devices from Pyonet-API")

            # Start polling loop
            loop = asyncio.get_event_loop()
            self.poll_task = loop.create_task(self.start_poll_loop())               

        except Exception as e:
            self.p3log.log_error(f"Initialization failed. Error: {str(e)}")
            return False

    # Main Polling Loop
    async def start_poll_loop(self):
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
        