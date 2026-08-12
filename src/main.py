import os
import socket
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.routers import health, items

APP_NAME = "PythonCICD"
APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.started = True
    application.state.ready = True
    try:
        yield
    finally:
        application.state.ready = False


app = FastAPI(title=APP_NAME, version=APP_VERSION, lifespan=lifespan)
app.state.started = False
app.state.ready = False

app.mount("/public", StaticFiles(directory="public"), name="public")
app.include_router(health.router)
app.include_router(items.router)


@app.get("/")
def read_root():
    return {
        "message": "hello world!",
        "name": APP_NAME,
        "version": APP_VERSION,
        "environment": os.getenv("APP_ENV", "UNKNOWN"),
        "served_by": socket.gethostname(),
    }
