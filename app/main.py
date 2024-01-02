import os
from typing import Union

from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def read_root():
    app_env = os.getenv("APP_ENV", "UNKNOWN")
    return {
        "message": "hello world!",
        "env": app_env
    }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/info")
def info():
    return {"name": "ob-sample-fast-api", "version": "1.0.0"}
