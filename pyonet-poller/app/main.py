import signal, sys, asyncio
from fastapi import FastAPI, BackgroundTasks
from app.libraries.libpoller import Poller
from . import db

# routers 
from .routers import auth

app = FastAPI()
oPoller = Poller()

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
    oPoller.test_access_token()   
    await oPoller.init_polling()  
    

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Pyonet-Poller")
    await db.disconnect()
    oPoller.poll_task.cancel()
    

# register routers #
app.include_router(auth.router)

    

