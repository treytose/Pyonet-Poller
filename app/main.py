import sys, os, signal, psutil, secrets, socket
from fastapi import FastAPI, Depends, BackgroundTasks
from app.libraries.libpoller import Poller
from app.dependencies import verify_api_key
from app.tools.p3log import P3Log
from rich import print
from . import db, API_KEY

# routers 
from .routers import auth
from .routers import poller

app = FastAPI()
oPoller = Poller()
oLogger = P3Log("main")

@app.get("/hello")
async def hello():
    return "Pyonet-Poller"

# app events #

# Stop the background task when Ctrl+C is pressed
def sigint_handler(signum, frame):    
    oPoller.loop_enabled = False    
    
def get_ip_address():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return ip_address

@app.on_event("startup")
async def startup_event():
    global API_KEY
    await db.connect()
    hostname = os.uname()[1]
    
    if not API_KEY:
        # generate API_KEY if not set
        API_KEY = secrets.token_urlsafe(32)
        ipaddr = get_ip_address()          
                
        await db.insert("poller", {
            "name": f"poller-{hostname}",
            "description": f"Auto generated poller for {hostname} ({ipaddr})",
            "api_key": API_KEY,
            "hostname": ipaddr,
            "port": 8000,
        })
                
        with open(".env", "a") as f:
            f.write(f"\nAPI_KEY={API_KEY}")
            
        print(f"[bold green]API_KEY generated and saved to .env file. Please restart Pyonet-Poller.")
        # exit without error
        try:
            sys.exit(0)        
        except SystemExit:
            os._exit(0)
    else:
        poller_object = await db.fetchone("SELECT * FROM poller WHERE API_KEY = :api_key", {"api_key": API_KEY})
        if not poller_object:
            print(f"[bold red]ERROR: API_KEY is set but does not match any poller in the database.\nPlease ensure the .env file does not contain a copy and pasted API_KEY from another poller.\nIf you are sure this is not the case, please delete the API_KEY from the .env file and restart Pyonet-Poller.")
            sys.exit(1)
        if poller_object.name != f"poller-{hostname}":
            print(f"[bold yellow]WARNING: API_KEY is set but does not match hostname.\nPlease ensure the .env file does not contain a copy and pasted API_KEY from another poller.\nIf you are sure this is not the case, please delete the API_KEY from the .env file and restart Pyonet-Poller.")
            
@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Pyonet-Poller")
    await db.disconnect()

@app.get("/poller/status", dependencies=[Depends(verify_api_key)])
async def poller_status():
    if oPoller.running:
        return {"status": "running"}
    else:
        return {"status": "idle"}

@app.post("/poller/start", dependencies=[Depends(verify_api_key)])
async def start_poller(background_tasks: BackgroundTasks):
    if oPoller.running:
        return {"status": "Poller already running"}
    else:        
        await oPoller.init_polling()        
        background_tasks.add_task(oPoller.start_polling)                
        return {"status": "Poller started"}

@app.post("/poller/stop", dependencies=[Depends(verify_api_key)])
async def stop_poller():
    await oPoller.stop_polling()
    return {"status": "Poller stopped"}    

@app.post("/poller/device/update/<deviceid>", dependencies=[Depends(verify_api_key)])
async def update_device(deviceid: int):
    await oPoller.update_device(deviceid)
    return {"status": "Device updated"}

@app.post("/poller/device/remove/<deviceid>", dependencies=[Depends(verify_api_key)])
async def remove_device(deviceid: int):
    await oPoller.remove_device(deviceid)
    return {"status": "Device removed"}

# register routers #
app.include_router(auth.router)
app.include_router(poller.router)

    

