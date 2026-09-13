"""Connection states of the WhatsApp sidecar and human-readable descriptions."""

DISCONNECTED = "disconnected"
QR = "qr"
AUTHENTICATED = "authenticated"
READY = "ready"
AUTH_FAILURE = "auth_failure"

_DESCRIPTIONS = {
    DISCONNECTED: "WhatsApp is disconnected. Start the sidecar and scan the QR code.",
    QR: "WhatsApp is waiting — scan the QR code (GET /qr or the sidecar console).",
    AUTHENTICATED: "WhatsApp authenticated, loading…",
    READY: "WhatsApp is connected and ready.",
    AUTH_FAILURE: "WhatsApp authentication failed. Delete .wwebjs_auth and scan the QR again.",
}


def describe(state: str) -> str:
    return _DESCRIPTIONS.get(state, f"Unknown state: {state}")
