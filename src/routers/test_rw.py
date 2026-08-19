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


@router.post("/uploads")
def upload(content: UploadContent | None = None) -> UploadContent:
    values = content_values(content)
    uploaded_content = "\n".join(values)
    if values:
        uploaded_content += "\n"
    UPLOADED_FILE.write_text(uploaded_content, encoding="utf-8")

    return UploadContent(content=read_content())


@router.put("/uploads")
def write_upload(content: UploadContent | None = None) -> UploadContent:
    values = content_values(content)
    read_content()

    if values:
        try:
            with UPLOADED_FILE.open("r+", encoding="utf-8") as uploaded_file:
                existing = uploaded_file.read()
                separator = "" if not existing or existing.endswith("\n") else "\n"
                appended_content = "\n".join(values)
                uploaded_file.seek(0, 2)
                uploaded_file.write(f"{separator}{appended_content}\n")
        except FileNotFoundError as error:
            raise missing_upload_error() from error

    return UploadContent(content=read_content())


def content_values(content: UploadContent | None) -> list[str]:
    if content is None or content.content is None:
        return [default_content()]
    return content.content


def read_content() -> list[str]:
    try:
        return UPLOADED_FILE.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError as error:
        raise missing_upload_error() from error


def missing_upload_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Uploaded file does not exist",
    )


def default_content() -> str:
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return f"{socket.gethostname()} - {timestamp}"
