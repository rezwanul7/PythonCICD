import os

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.routers import health, items

APP_NAME = "PythonCICD"
APP_VERSION = "0.1.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)

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
    }
