"""Unit tests for FAISS vector tool selection."""

import pytest
from app.modules.antigravity.tool_vector_index import query, TOOL_CORPUS, get_index


class TestToolVectorIndex:
    def test_vector_index_build(self):
        """Vector index should build and return a valid FAISS index with labels."""
        idx = get_index(TOOL_CORPUS)
        assert idx is not None
        assert idx.ntotal > 50

    def test_vector_query_ping_zahida(self):
        """Paraphrased WhatsApp message prompt should match send_message with high confidence."""
        tool, score = query("ping Zahida on WhatsApp", TOOL_CORPUS, threshold=0.60)
        assert tool == "send_message"
        assert score >= 0.60

    def test_vector_query_build_app(self):
        """Complex generative/coding task prompt should match fork with high confidence."""
        tool, score = query("build a calculator application in python", TOOL_CORPUS, threshold=0.60)
        assert tool == "fork"
        assert score >= 0.60

    def test_vector_query_unread_digest(self):
        """Unread digest paraphrase should match unread_digest."""
        tool, score = query("give me a summary of my unread WhatsApp chats", TOOL_CORPUS, threshold=0.60)
        assert tool == "unread_digest"
        assert score >= 0.60

    def test_vector_query_list_chats(self):
        """Listing chats paraphrase should match list_chats."""
        tool, score = query("show my recent WhatsApp conversations", TOOL_CORPUS, threshold=0.60)
        assert tool == "list_chats"
        assert score >= 0.60

    def test_vector_query_below_threshold(self):
        """Completely unrelated text should score below threshold or return None."""
        tool, score = query("the quick brown fox jumps over the lazy dog", TOOL_CORPUS, threshold=0.90)
        assert tool is None
