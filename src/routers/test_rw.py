import socket
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/test-rw", tags=["test-rw"])

UPLOAD_DEMO_FILE = Path(__file__).resolve().parents[2] / "uploads" / "demo.txt"


class UploadContent(BaseModel):
    content: list[str] | None = None


@router.get("/uploads")
def read_upload() -> UploadContent:
    return UploadContent(content=read_content())


@router.put("/uploads")
def write_upload(content: UploadContent | None = None) -> UploadContent:
    if content is None or content.content is None:
        values = [default_content()]
    else:
        values = content.content

    if values:
        existing = UPLOAD_DEMO_FILE.read_text(encoding="utf-8")
        separator = "" if not existing or existing.endswith("\n") else "\n"
        appended_content = "\n".join(values)
        with UPLOAD_DEMO_FILE.open("a", encoding="utf-8") as demo_file:
            demo_file.write(f"{separator}{appended_content}\n")

    return UploadContent(content=read_content())


def read_content() -> list[str]:
    return UPLOAD_DEMO_FILE.read_text(encoding="utf-8").splitlines()


def default_content() -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"{socket.gethostname()} - {timestamp}"
