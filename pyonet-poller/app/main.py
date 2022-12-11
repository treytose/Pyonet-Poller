import sys, os, signal, psutil
from fastapi import FastAPI, BackgroundTasks
from app.libraries.libpoller import Poller
from app.tools.p3log import P3Log
from . import db

# routers 
from .routers import auth

app = FastAPI()
oPoller = Poller()
oLogger = P3Log("main")

poll_task = None

@app.get("/hello")
async def hello():
    return "Pyonet-Poller"

# app events #

# Stop the background task when Ctrl+C is pressed
def sigint_handler(signum, frame):    
    oPoller.loop_enabled = False    

@app.on_event("startup")
async def startup_event():
    await db.connect()
    success = await oPoller.test_access_token()       
    if not success:
        oLogger.log_error("Could not authenticate with Pyonet-API. Exiting...")
        os.kill(psutil.Process(os.getpid()).ppid(), signal.SIGINT)
    else:        
        await oPoller.init_polling()  
    

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Pyonet-Poller")
    await db.disconnect()
    if oPoller.poll_task:
        oPoller.poll_task.cancel()
    

# register routers #
app.include_router(auth.router)

    

