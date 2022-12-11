import signal, sys
from fastapi import FastAPI, BackgroundTasks
from app.libraries.libpoller import Poller
from . import db

# routers 
from .routers import auth

app = FastAPI()
oPoller = Poller()
background_tasks = BackgroundTasks()

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
    signal.signal(signal.SIGINT, sigint_handler)

    # Init Poller 
    oPoller.test_access_token()
    await oPoller.init_polling()
    

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down Pyonet-Poller")
    await db.disconnect()
    

# register routers #
app.include_router(auth.router)

    

