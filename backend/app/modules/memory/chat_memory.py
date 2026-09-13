"""Short-term chat memory: per-session sliding window of recent messages.

Kept in-memory (lost on restart) — its job is conversational context for the
LLM within a session, not durability.
"""
from collections import defaultdict
from typing import Dict, List


class ChatMemory:
    """Stores the last ``max_messages`` messages per session."""

    def __init__(self, max_messages: int = 20):
        self.max_messages = max_messages
        self._sessions: Dict[str, List[dict]] = defaultdict(list)

    def add(self, session_id: str, role: str, content: str) -> None:
        messages = self._sessions[session_id]
        messages.append({"role": role, "content": content})
        # keep only the most recent messages
        if len(messages) > self.max_messages:
            del messages[: len(messages) - self.max_messages]

    def history(self, session_id: str) -> List[dict]:
        """Return a copy of the session's message history (oldest first)."""
        return list(self._sessions[session_id])

    def clear(self, session_id: str = None) -> None:
        """Clear one session, or all sessions when session_id is None."""
        if session_id is None:
            self._sessions.clear()
        else:
            self._sessions.pop(session_id, None)
