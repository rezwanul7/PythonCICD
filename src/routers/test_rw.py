import socket
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/test-rw", tags=["test-rw"])

UPLOADED_FILE = Path(__file__).resolve().parents[2] / "uploads" / "uploaded.txt"


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
        try:
            existing = UPLOADED_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            existing = ""
        separator = "" if not existing or existing.endswith("\n") else "\n"
        appended_content = "\n".join(values)
        with UPLOADED_FILE.open("a", encoding="utf-8") as uploaded_file:
            uploaded_file.write(f"{separator}{appended_content}\n")
    else:
        UPLOADED_FILE.touch(exist_ok=True)

    return UploadContent(content=read_content())


def read_content() -> list[str]:
    try:
        return UPLOADED_FILE.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file does not exist",
        ) from error


def default_content() -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"{socket.gethostname()} - {timestamp}"
