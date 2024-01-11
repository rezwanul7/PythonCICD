import os
import getpass
from typing import Union
from datetime import datetime
from fastapi import FastAPI
from starlette.staticfiles import StaticFiles

app = FastAPI()

app.mount("/public", StaticFiles(directory="public"), name="public")


@app.get("/")
def read_root():
    app_env = os.getenv("APP_ENV", "UNKNOWN")

    dt_string = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    f = open("public/demo.txt", "a")
    f.write(f"{dt_string} \n")
    f.close()

    return {
        "message": "hello world!",
        "env": app_env,
        "sys_user": getpass.getuser()
    }


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get("/info")
def info():
    return {"name": "ob-sample-fast-api", "version": "1.0.0"}
