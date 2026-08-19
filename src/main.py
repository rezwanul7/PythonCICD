import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

from src.middleware import ServedByMiddleware
from src.routers import health, items, test_rw

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
app.add_middleware(ServedByMiddleware)
app.state.started = False
app.state.ready = False

app.mount("/public", StaticFiles(directory="public"), name="public")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(health.router)
app.include_router(items.router)
app.include_router(test_rw.router)


@app.get("/")
def read_root():
    return {
        "message": "hello world!",
        "name": APP_NAME,
        "version": APP_VERSION,
        "environment": os.getenv("APP_ENV", "UNKNOWN"),
    }
