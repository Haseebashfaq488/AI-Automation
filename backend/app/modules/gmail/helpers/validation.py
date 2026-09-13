from typing import Any


def validate_email_address(email: str) -> bool:
    """Basic validation for an email address string.

    Returns True if the string looks like an email address.
    """
    return "@" in email and "." in email.split("@")[-1]


def validate_query(query: str) -> bool:
    """Validate that a search query string is non‑empty."""
    return bool(query and query.strip())