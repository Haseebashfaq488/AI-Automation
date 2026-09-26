"""Semantic memory retriever: Ultra-low latency ONNX + Keyword index over living memory facts.

Enables on-demand semantic retrieval for Bubbles' brain:
- Indexes 'Active Preferences & Habits', 'Active Projects', and 'Recent Scratchpad'.
- Fast-bypasses greetings & chitchat (0 tokens injected).
- Uses ONNX-quantized dense vector similarity (<5ms) + BM25 keyword boosting for project paths/tools.
- Re-indexes dynamically when JARVIS_MEMORY.md changes.
"""
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np

logger = logging.getLogger("jarvis.brain.memory_vector_index")

DEFAULT_MEMORY_PATH = Path(__file__).parent / "JARVIS_MEMORY.md"
MODEL_NAME = os.getenv("VECTOR_EMBEDDING_MODEL", "all-MiniLM-L6-v2-quantized-onnx")
DEFAULT_THRESHOLD = float(os.getenv("MEMORY_CONFIDENCE_THRESHOLD", "0.38"))

# Fast-path greeting tokens that require zero fact retrieval
GREETING_TOKENS = {
    "hi", "hello", "hey", "bubbles", "jarvis", "good", "morning", "evening",
    "night", "aoa", "assalam", "yo", "how", "are", "you", "doing", "today",
    "who", "am", "i", "what", "is", "my", "name"
}

_SHARED_EMBEDDER: Any = None


def _get_shared_embedder() -> Any:
    global _SHARED_EMBEDDER
    if _SHARED_EMBEDDER is None:
        try:
            from app.modules.antigravity.onnx_embedder import get_onnx_embedder
            _SHARED_EMBEDDER = get_onnx_embedder()
        except Exception as exc:
            logger.info("ONNX memory embedder not loaded (%s). Using keyword-lexical matcher.", exc)
            return None
    return _SHARED_EMBEDDER


async def prewarm_vector_embedder() -> None:
    """Pre-warm the ONNX embedder model in a background thread at startup."""
    import asyncio
    try:
        logger.info("Pre-warming ONNX semantic vector embedder (%s) in background...", MODEL_NAME)
        embedder = await asyncio.to_thread(_get_shared_embedder)
        if embedder is not None:
            # Micro-inference to warm execution graphs and CPU caches
            await asyncio.to_thread(embedder.encode, ["warmup"], normalize_embeddings=True)
            logger.info("ONNX semantic vector embedder warmed up and ready in RAM! ⚡")
            index = get_memory_vector_index()
            await asyncio.to_thread(index.refresh)
    except Exception as exc:
        logger.debug("ONNX embedder pre-warm skipped or failed: %s", exc)


class MemoryVectorIndex:
    """Manages dense ONNX + lexical indexing for Bubbles' living memory."""

    def __init__(self, memory_path: Optional[Path] = None, threshold: float = DEFAULT_THRESHOLD):
        self.memory_path = memory_path or DEFAULT_MEMORY_PATH
        self.threshold = threshold
        self._documents: List[str] = []
        self._doc_categories: List[str] = []
        self._doc_embeddings: Optional[np.ndarray] = None
        self._embedder: Any = None
        self._initialized: bool = False
        self._has_dense: bool = False
        self.refresh()

    def _extract_documents_from_markdown(self, markdown_text: str) -> List[Tuple[str, str]]:
        """Extract bullet points from memory sections (skipping invariants & profile)."""
        docs: List[Tuple[str, str]] = []
        if not markdown_text:
            return docs

        current_section = "General"
        sections_to_index = {
            "Active Preferences & Habits": "Preferences",
            "Active Projects & Workspaces": "Projects",
            "Recent Scratchpad (Rolling Active Notes)": "Scratchpad",
            "Scratchpad & Temporary Notes": "Scratchpad",
            "Active Knowledge & Notes": "Notes",
        }

        for line in markdown_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("## "):
                raw_header = line_str[3:].strip()
                # Remove emojis for cleaner section mapping
                clean_header = re.sub(r"[^\w\s&(),-]", "", raw_header).strip()
                current_section = "General"
                for sec_key, sec_name in sections_to_index.items():
                    if sec_key.lower() in clean_header.lower():
                        current_section = sec_name
                        break
            elif line_str.startswith("- ") and current_section != "General":
                fact = line_str[2:].strip()
                if fact:
                    docs.append((current_section, fact))

        return docs

    def _try_init_dense(self) -> bool:
        """Try loading ONNX embedder singleton."""
        embedder = _get_shared_embedder()
        if embedder is None:
            self._has_dense = False
            return False
        self._embedder = embedder
        self._has_dense = True
        return True

    def refresh(self) -> None:
        """Re-read JARVIS_MEMORY.md and rebuild the semantic index."""
        try:
            if not self.memory_path.exists():
                self._documents = []
                self._doc_categories = []
                self._doc_embeddings = None
                self._initialized = True
                return

            text = self.memory_path.read_text(encoding="utf-8")
            doc_tuples = self._extract_documents_from_markdown(text)
            self._documents = [fact for _, fact in doc_tuples]
            self._doc_categories = [cat for cat, _ in doc_tuples]

            if not self._documents:
                self._doc_embeddings = None
                self._initialized = True
                return

            if self._try_init_dense():
                raw_embeddings = self._embedder.encode(
                    self._documents,
                    normalize_embeddings=True,
                )
                self._doc_embeddings = np.array(raw_embeddings, dtype=np.float32)

            self._initialized = True
            logger.debug("Indexed %d memory facts for Bubbles using ONNX.", len(self._documents))
        except Exception as exc:
            logger.warning("Failed to refresh memory vector index: %s", exc)

    def _lexical_match_score(self, prompt_tokens: Set[str], fact: str) -> float:
        """Compute keyword overlap and path boosting score."""
        fact_lower = fact.lower()
        fact_tokens = set(re.findall(r"\w+", fact_lower))
        if not fact_tokens:
            return 0.0

        overlap = len(prompt_tokens & fact_tokens)
        score = overlap / max(len(fact_tokens), 1)

        # High-value path or domain boosts
        for token in prompt_tokens:
            if len(token) > 3 and token in fact_lower:
                score += 0.25

        return score

    def query_relevant_facts(self, prompt: str, top_k: int = 4) -> List[str]:
        """Retrieve the most relevant facts for Dum Dum's current prompt.

        Returns [] for greetings or when confidence is below threshold.
        """
        if not prompt or not self._documents:
            return []

        # Tokenize prompt
        raw_tokens = [w.lower() for w in re.findall(r"\w+", prompt)]
        clean_tokens = set(raw_tokens)

        # 1. Fast-path: Skip retrieval entirely for greetings / chitchat
        if len(clean_tokens) <= 5 and clean_tokens.issubset(GREETING_TOKENS):
            return []

        scored_results: List[Tuple[float, str]] = []

        # 2. Dense semantic vector retrieval via ONNX dot-product cosine similarity
        if self._has_dense and self._doc_embeddings is not None and self._embedder is not None:
            try:
                q_vec = self._embedder.encode(prompt, normalize_embeddings=True)
                # Dot product of normalized vectors = Cosine similarity
                sims = np.dot(self._doc_embeddings, q_vec)
                top_indices = np.argsort(sims)[::-1][:min(len(self._documents), top_k * 2)]

                for idx in top_indices:
                    score = float(sims[idx])
                    fact = self._documents[idx]
                    # Add hybrid keyword boost
                    lex_score = self._lexical_match_score(clean_tokens, fact)
                    hybrid_score = score * 0.7 + lex_score * 0.3
                    if hybrid_score >= self.threshold:
                        scored_results.append((hybrid_score, fact))
            except Exception as exc:
                logger.warning("Dense ONNX memory query failed: %s, falling back to lexical.", exc)

        # 3. Lexical fallback (if dense unavailable or returned nothing)
        if not scored_results:
            for fact in self._documents:
                score = self._lexical_match_score(clean_tokens, fact)
                if score >= 0.20:
                    scored_results.append((score, fact))

        # Sort descending by score, deduplicate, and pick top_k
        scored_results.sort(key=lambda x: x[0], reverse=True)
        seen: Set[str] = set()
        chosen: List[str] = []
        for _, fact in scored_results:
            if fact not in seen:
                seen.add(fact)
                chosen.append(fact)
                if len(chosen) >= top_k:
                    break

        return chosen


# Global singleton
_memory_index: Optional[MemoryVectorIndex] = None


def get_memory_vector_index() -> MemoryVectorIndex:
    """Return the global MemoryVectorIndex instance."""
    global _memory_index
    if _memory_index is None:
        _memory_index = MemoryVectorIndex()
    return _memory_index
