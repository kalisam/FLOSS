"""
Tests for conversation_memory.py

This test suite verifies that the ConversationMemory class works correctly
with real sentence-transformer embeddings.
"""

import pytest
import numpy as np
import shutil
from pathlib import Path
import sys

# Add ARF to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory


@pytest.fixture
def temp_memory():
    """Create a temporary memory instance that gets cleaned up after tests"""
    test_path = "./test_memory_temp"
    memory = ConversationMemory(agent_id="test-agent", storage_path=test_path)
    yield memory
    # Cleanup
    if Path(test_path).exists():
        shutil.rmtree(test_path)


def test_encode_deterministic(temp_memory):
    """Test that encoding the same text produces very similar embeddings"""
    embedding1 = temp_memory._encode_text("test")
    embedding2 = temp_memory._encode_text("test")

    # Embeddings should be VERY similar (cosine sim ~1.0)
    similarity = np.dot(embedding1, embedding2)
    assert similarity > 0.99, f"Expected similarity > 0.99, got {similarity}"


def test_embedding_dimensions(temp_memory):
    """Ensure embeddings maintain 384 dimensions and are normalized"""
    texts = ["short", "a longer piece of text", "This is an even longer piece of text for testing"]

    for text in texts:
        embedding = temp_memory._encode_text(text)
        assert embedding.shape == (384,), f"Expected 384-dim, got {embedding.shape}"

        # Check normalization
        norm = np.linalg.norm(embedding)
        assert np.abs(norm - 1.0) < 1e-6, f"Embedding not normalized: {norm}"


def test_semantic_similarity(temp_memory):
    """Test that semantically similar words have similar embeddings"""
    dog_emb = temp_memory._encode_text("dog")
    puppy_emb = temp_memory._encode_text("puppy")
    car_emb = temp_memory._encode_text("car")

    # Dog and puppy should be similar
    dog_puppy_sim = np.dot(dog_emb, puppy_emb)
    assert dog_puppy_sim > 0.5, f"Dog and puppy should be similar: {dog_puppy_sim}"

    # Dog and car should be less similar
    dog_car_sim = np.dot(dog_emb, car_emb)
    assert dog_car_sim < dog_puppy_sim, f"Dog should be more similar to puppy than car"


def test_transmit_and_recall(temp_memory):
    """Test that we can transmit and recall understandings"""
    # Transmit some understandings
    ref1 = temp_memory.transmit({
        'content': "Dogs are loyal pets that love their owners",
        'context': "Test context",
        'coherence': 0.9
    })

    ref2 = temp_memory.transmit({
        'content': "Cars are vehicles with four wheels",
        'context': "Test context",
        'coherence': 0.8
    })

    ref3 = temp_memory.transmit({
        'content': "Puppies are young dogs that are very playful",
        'context': "Test context",
        'coherence': 0.85
    })

    # Recall with dog-related query
    results = temp_memory.recall("canine animals", top_k=3)

    assert len(results) > 0, "Should find at least one result"

    # The dog-related understandings should be ranked higher
    top_result = results[0]
    assert 'dog' in top_result['content'].lower() or 'puppy' in top_result['content'].lower(), \
        f"Top result should be dog-related, got: {top_result['content']}"


def test_model_caching(temp_memory):
    """Test that the model is loaded once and cached"""
    # First encoding triggers model load
    _ = temp_memory._encode_text("test text 1")
    assert hasattr(temp_memory, '_embedding_model'), "Model should be cached"

    # Get reference to the model
    model_ref = temp_memory._embedding_model

    # Second encoding should use same model
    _ = temp_memory._encode_text("test text 2")
    assert temp_memory._embedding_model is model_ref, "Should reuse same model instance"


def test_empty_text_handling(temp_memory):
    """Test handling of empty or whitespace-only text"""
    # Empty string
    empty_emb = temp_memory._encode_text("")
    assert empty_emb.shape == (384,), "Empty text should still produce 384-dim embedding"
    assert np.abs(np.linalg.norm(empty_emb) - 1.0) < 1e-6, "Should be normalized"

    # Whitespace only
    ws_emb = temp_memory._encode_text("   ")
    assert ws_emb.shape == (384,), "Whitespace text should still produce 384-dim embedding"
    assert np.abs(np.linalg.norm(ws_emb) - 1.0) < 1e-6, "Should be normalized"


def test_special_characters(temp_memory):
    """Test handling of special characters and unicode"""
    texts = [
        "Hello! How are you?",
        "Testing @#$% special chars",
        "Unicode: 你好世界 🌍",
        "Newlines\nand\ttabs"
    ]

    for text in texts:
        embedding = temp_memory._encode_text(text)
        assert embedding.shape == (384,), f"Failed for text: {text}"
        assert np.abs(np.linalg.norm(embedding) - 1.0) < 1e-6, f"Not normalized for: {text}"


def test_long_text_handling(temp_memory):
    """Test handling of very long text"""
    long_text = "This is a test sentence. " * 100  # ~500 words

    embedding = temp_memory._encode_text(long_text)
    assert embedding.shape == (384,), "Long text should still produce 384-dim embedding"
    assert np.abs(np.linalg.norm(embedding) - 1.0) < 1e-6, "Should be normalized"


def test_embedding_return_type(temp_memory):
    """Test that embeddings are returned as numpy arrays"""
    embedding = temp_memory._encode_text("test")
    assert isinstance(embedding, np.ndarray), "Should return numpy array"
    assert embedding.dtype in [np.float32, np.float64], f"Should be float type, got {embedding.dtype}"


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
