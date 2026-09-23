"""Validation helpers for WhatsApp tools."""
import re
from typing import Optional

CHAT_ACTIONS = {"pin", "unpin", "mute", "unmute", "archive", "unarchive", "mark_read", "clear"}
GROUP_ACTIONS = {"create", "add", "remove", "promote", "demote", "leave"}

_NON_DIGITS = re.compile(r"\D+")


def normalize_phone(phone: str) -> str:
    """Normalize a phone number to bare digits (no +, spaces, or dashes)."""
    return _NON_DIGITS.sub("", phone or "")


def to_chat_id(value: str) -> str:
    """Convert a phone number or bare number to a WhatsApp chat id ('<digits>@c.us')."""
    digits = normalize_phone(value)
    if not digits:
        raise ValueError(f"Invalid phone number or chat id: {value!r}")
    return f"{digits}@c.us"


def validate_chat_action(action: str) -> str:
    action = (action or "").strip().lower()
    if action not in CHAT_ACTIONS:
        raise ValueError(f"Invalid chat action: {action!r}. Valid: {sorted(CHAT_ACTIONS)}")
    return action


def validate_group_action(action: str) -> str:
    action = (action or "").strip().lower()
    if action not in GROUP_ACTIONS:
        raise ValueError(f"Invalid group action: {action!r}. Valid: {sorted(GROUP_ACTIONS)}")
    return action


def resolve_recipient(value: str) -> str:
    """Return a value the sidecar can resolve: a full chat id, or a name/number string."""
    value = (value or "").strip()
    if not value:
        raise ValueError("Recipient (to/chat) must not be empty")
    lowered = value.lower()
    if lowered in ("me", "myself", "haseeb", "self", "haseeb hamza", "owner"):
        return to_chat_id("923098956995")
    digits = normalize_phone(value)
    if digits and (digits == value or value.startswith("+")) and "@" not in value:
        return to_chat_id(digits)
    return value

