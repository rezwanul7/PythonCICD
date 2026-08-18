import socket
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/test-rw", tags=["test-rw"])

PUBLIC_DEMO_FILE = Path(__file__).resolve().parents[2] / "public" / "demo.txt"


class PublicContent(BaseModel):
    content: list[str] | None = None


@router.get("/public")
def read_public() -> PublicContent:
    return PublicContent(content=read_content())


@router.put("/public")
def write_public(content: PublicContent | None = None) -> PublicContent:
    if content is None or content.content is None:
        values = [default_content()]
    else:
        values = content.content

    if values:
        existing = PUBLIC_DEMO_FILE.read_text(encoding="utf-8")
        separator = "" if not existing or existing.endswith("\n") else "\n"
        appended_content = "\n".join(values)
        with PUBLIC_DEMO_FILE.open("a", encoding="utf-8") as demo_file:
            demo_file.write(f"{separator}{appended_content}\n")

    return PublicContent(content=read_content())


def read_content() -> list[str]:
    return PUBLIC_DEMO_FILE.read_text(encoding="utf-8").splitlines()


def default_content() -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"{socket.gethostname()} - {timestamp}"
