"""Shared paths for the WhatsApp module."""
from pathlib import Path

# backend/app/modules/whatsapp/helpers/ -> backend
BASE_DIR = Path(__file__).resolve().parents[4]

# Default download location for media pulled from chats.
MEDIA_ROOT = BASE_DIR / "whatsapp_media"
