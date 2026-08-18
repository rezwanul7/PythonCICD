import socket
from json import dumps, loads
from typing import Any

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class ServedByMiddleware:
    """Add the serving hostname to every JSON object response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_message: Message | None = None
        body_parts: list[bytes] = []

        async def send_with_served_by(message: Message) -> None:
            nonlocal start_message

            if message["type"] == "http.response.start":
                start_message = message
                return

            if message["type"] != "http.response.body" or start_message is None:
                await send(message)
                return

            body_parts.append(message.get("body", b""))
            if message.get("more_body", False):
                return

            body = b"".join(body_parts)
            headers = MutableHeaders(raw=start_message["headers"])
            if headers.get("content-type", "").startswith("application/json"):
                body, changed = _add_served_by(body)
                if changed:
                    headers["content-length"] = str(len(body))

            await send(start_message)
            await send({"type": "http.response.body", "body": body})

        await self.app(scope, receive, send_with_served_by)


def _add_served_by(body: bytes) -> tuple[bytes, bool]:
    try:
        payload: Any = loads(body)
    except (UnicodeDecodeError, ValueError):
        return body, False

    if not isinstance(payload, dict):
        return body, False

    payload["served_by"] = socket.gethostname()
    encoded = dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    return encoded, True
