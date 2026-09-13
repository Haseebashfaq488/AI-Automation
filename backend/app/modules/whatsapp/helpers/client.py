"""Async HTTP client for the local WhatsApp sidecar (whatsapp_service)."""
import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("jarvis.whatsapp")


class WhatsAppUnavailableError(RuntimeError):
    """Raised when the WhatsApp sidecar is not reachable or not connected."""


class WhatsAppClient:
    """Thin async wrapper around the sidecar's REST API."""

    def __init__(self, base_url: Optional[str] = None, timeout: float = 60.0):
        self.base_url = (base_url or settings.WHATSAPP_SERVICE_URL).rstrip("/")
        self._client = httpx.AsyncClient(base_url=self.base_url, timeout=timeout)

    async def _get(self, path: str, **params) -> Dict[str, Any]:
        try:
            resp = await self._client.get(path, params={k: v for k, v in params.items() if v is not None})
        except httpx.TransportError as exc:
            raise WhatsAppUnavailableError(
                f"WhatsApp service is not running at {self.base_url}. "
                "Start it with: npm start (in backend/whatsapp_service)"
            ) from exc
        return self._handle(resp)

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            resp = await self._client.post(path, json=payload)
        except httpx.TransportError as exc:
            raise WhatsAppUnavailableError(
                f"WhatsApp service is not running at {self.base_url}. "
                "Start it with: npm start (in backend/whatsapp_service)"
            ) from exc
        return self._handle(resp)

    @staticmethod
    def _handle(resp: httpx.Response) -> Dict[str, Any]:
        if resp.status_code >= 400:
            try:
                message = resp.json().get("error", resp.text)
            except Exception:
                message = resp.text
            raise RuntimeError(f"WhatsApp service error ({resp.status_code}): {message}")
        return resp.json()

    # -- sidecar state ------------------------------------------------------
    async def status(self) -> Dict[str, Any]:
        return await self._get("/status")

    async def qr(self) -> Dict[str, Any]:
        return await self._get("/qr")

    # -- reads --------------------------------------------------------------
    async def list_chats(self, limit: int = 50) -> List[Dict[str, Any]]:
        data = await self._get("/chats", limit=limit)
        return data["chats"]

    async def get_messages(self, chat: str, limit: int = 20) -> Dict[str, Any]:
        return await self._get("/messages", chat=chat, limit=limit)

    async def contacts(self, query: Optional[str] = None) -> List[Dict[str, Any]]:
        data = await self._get("/contacts", query=query)
        return data["contacts"]

    async def chat_info(self, chat: str) -> Dict[str, Any]:
        return await self._get("/chat-info", chat=chat)

    async def download_media(self, chat: str, limit: int = 50) -> Dict[str, Any]:
        return await self._get("/media", chat=chat, limit=limit)

    # -- writes -------------------------------------------------------------
    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        return await self._post("/send", {"to": to, "message": message})

    async def send_file(self, to: str, path: str, caption: Optional[str] = None) -> Dict[str, Any]:
        return await self._post("/send-file", {"to": to, "path": path, "caption": caption})

    async def chat_action(self, chat: str, action: str) -> Dict[str, Any]:
        return await self._post("/chat/action", {"chat": chat, "action": action})

    async def group_action(self, action: str, chat: Optional[str] = None,
                           name: Optional[str] = None,
                           participants: Optional[List[str]] = None) -> Dict[str, Any]:
        return await self._post("/group", {
            "action": action, "chat": chat, "name": name, "participants": participants or [],
        })

    async def close(self) -> None:
        await self._client.aclose()


# Module-level singleton (tools share one connection pool).
_client: Optional[WhatsAppClient] = None


def get_client() -> WhatsAppClient:
    global _client
    if _client is None:
        _client = WhatsAppClient()
    return _client
