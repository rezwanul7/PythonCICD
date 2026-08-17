import socket
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/test-rw", tags=["test-rw"])

PUBLIC_DEMO_FILE = Path(__file__).resolve().parents[2] / "public" / "demo.txt"


class PublicContent(BaseModel):
    content: str | None = None


@router.get("/public")
def read_public() -> PublicContent:
    return PublicContent(content=PUBLIC_DEMO_FILE.read_text(encoding="utf-8"))


@router.put("/public")
def write_public(content: PublicContent | None = None) -> PublicContent:
    if content is None or content.content is None:
        value = default_content()
    else:
        value = content.content
    PUBLIC_DEMO_FILE.write_text(value, encoding="utf-8")
    return PublicContent(content=value)


def default_content() -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"{socket.gethostname()} - {timestamp}"
