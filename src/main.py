import os

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

APP_NAME = "PythonCICD"
APP_VERSION = "0.1.0"

app = FastAPI(title=APP_NAME, version=APP_VERSION)

app.mount("/public", StaticFiles(directory="public"), name="public")


@app.get("/")
def read_root():
    return {
        "message": "hello world!",
        "name": APP_NAME,
        "version": APP_VERSION,
        "environment": os.getenv("APP_ENV", "UNKNOWN"),
    }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}


@app.get("/health")
def health():
    return {"status": "ok"}
