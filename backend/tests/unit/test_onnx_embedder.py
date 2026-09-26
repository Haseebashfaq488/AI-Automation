import pytest
import numpy as np
from app.modules.antigravity.onnx_embedder import get_onnx_embedder, OnnxEmbedder


def test_onnx_embedder_singleton():
    emb1 = get_onnx_embedder()
    emb2 = get_onnx_embedder()
    assert emb1 is emb2


def test_onnx_embedder_single_encoding():
    embedder = get_onnx_embedder()
    vec = embedder.encode("Hello world, this is a test query")
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (384,)
    # Verify L2 norm is ~1.0
    norm = np.linalg.norm(vec)
    assert pytest.approx(norm, 0.001) == 1.0


def test_onnx_embedder_batch_encoding():
    embedder = get_onnx_embedder()
    texts = [
        "First document about Google Drive files",
        "Second document about sending emails",
        "Third document about whatsapp automation"
    ]
    vecs = embedder.encode(texts)
    assert isinstance(vecs, np.ndarray)
    assert vecs.shape == (3, 384)
    for v in vecs:
        norm = np.linalg.norm(v)
        assert pytest.approx(norm, 0.001) == 1.0


def test_onnx_embedder_empty_input():
    embedder = get_onnx_embedder()
    empty = embedder.encode([])
    assert isinstance(empty, np.ndarray)
    assert empty.shape == (0, 384)
