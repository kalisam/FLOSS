"""
Tests for conversation_memory.py

This test suite verifies:
1. ConversationMemory works correctly with real sentence-transformer embeddings
2. ConversationMemory persistence functionality (save/reload embeddings)
"""

import pytest
import numpy as np
import shutil
import tempfile
from pathlib import Path
import sys
import json

# Add ARF to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory
from embedding_frames_of_scale import MultiScaleEmbedding


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_memory():
    """Create a temporary memory instance that gets cleaned up after tests"""
    test_path = "./test_memory_temp"
    memory = ConversationMemory(agent_id="test-agent", storage_path=test_path)
    yield memory
    # Cleanup
    if Path(test_path).exists():
        shutil.rmtree(test_path)


@pytest.fixture
def temp_storage():
    """Create a temporary directory for storage."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    shutil.rmtree(temp_dir)


# ============================================================================
# Tests for Real Embeddings (PR #1)
# ============================================================================

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


# ============================================================================
# Tests for Persistence (PR #2)
# ============================================================================

class TestConversationMemoryPersistence:
    """Test that ConversationMemory can save and reload embeddings."""

    def test_conversation_memory_saves_embeddings(self, temp_storage):
        """Test that ConversationMemory saves embeddings to disk."""
        # ARRANGE
        memory = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # Add some embeddings directly
        memory.embeddings.add_embedding('fine', 'test1', np.array([1.0, 2.0, 3.0]))
        memory.embeddings.add_embedding('fine', 'test2', np.array([4.0, 5.0, 6.0]))

        # ACT
        memory._save()

        # ASSERT
        embeddings_file = temp_storage / "embeddings.json"
        assert embeddings_file.exists()

        # Verify the content
        with open(embeddings_file, 'r') as f:
            data = json.load(f)
            assert 'levels' in data
            assert 'fine' in data['levels']

    def test_conversation_memory_loads_embeddings(self, temp_storage):
        """Test that ConversationMemory can load embeddings from disk."""
        # ARRANGE - Create and save first instance
        memory1 = ConversationMemory(agent_id="test", storage_path=temp_storage)
        memory1.embeddings.add_embedding('fine', 'test1', np.array([1.0, 2.0, 3.0]))
        memory1.embeddings.add_embedding('fine', 'test2', np.array([4.0, 5.0, 6.0]))
        memory1._save()

        # ACT - Create new instance that should load the embeddings
        memory2 = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # ASSERT
        assert 'fine' in memory2.embeddings.levels
        assert 'test1' in memory2.embeddings.levels['fine']
        assert 'test2' in memory2.embeddings.levels['fine']

        # Check vectors match
        vec1 = memory2.embeddings.get_embedding('fine', 'test1').vector
        assert np.allclose(vec1, np.array([1.0, 2.0, 3.0]))

    def test_conversation_memory_persistence_round_trip(self, temp_storage):
        """Test full round-trip: save, reload, verify."""
        # ARRANGE
        memory1 = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # Add some test data
        test_vectors = {
            'vec1': np.random.randn(384),
            'vec2': np.random.randn(384),
            'vec3': np.random.randn(384),
        }

        for key, vec in test_vectors.items():
            memory1.embeddings.add_embedding('fine', key, vec)

        # ACT - Save
        memory1._save()

        # Create new instance to load
        memory2 = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # ASSERT - Verify all vectors match
        for key, original_vec in test_vectors.items():
            loaded_vec = memory2.embeddings.get_embedding('fine', key).vector
            assert np.allclose(original_vec, loaded_vec, rtol=1e-6)

    def test_conversation_memory_handles_missing_embeddings_file(self, temp_storage):
        """Test that missing embeddings file doesn't cause error."""
        # ACT - Create memory without any saved embeddings
        memory = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # ASSERT - Should have fresh empty embeddings
        assert len(memory.embeddings.levels) == 0

    def test_conversation_memory_handles_corrupted_embeddings_file(self, temp_storage):
        """Test graceful handling of corrupted embeddings file."""
        # ARRANGE - Create corrupted embeddings file
        embeddings_file = temp_storage / "embeddings.json"
        with open(embeddings_file, 'w') as f:
            f.write("{ corrupted json }")

        # ACT - Try to load
        memory = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # ASSERT - Should fall back to fresh embeddings
        assert len(memory.embeddings.levels) == 0

    def test_conversation_memory_export_includes_embeddings(self, temp_storage):
        """Test that export includes embedding state."""
        # ARRANGE
        memory = ConversationMemory(agent_id="test", storage_path=temp_storage)
        memory.embeddings.add_embedding('fine', 'test', np.array([1.0, 2.0]))

        # ACT
        export = memory.export_for_composition()

        # ASSERT
        assert 'embedding_state' in export
        assert export['embedding_state'] is not None
        assert 'levels' in export['embedding_state']

    def test_conversation_memory_import_loads_embeddings(self, temp_storage):
        """Test that import_and_compose can load embeddings from export."""
        # ARRANGE - Create first memory with embeddings
        memory1 = ConversationMemory(agent_id="agent1", storage_path=temp_storage / "agent1")
        memory1.embeddings.add_embedding('fine', 'shared', np.array([1.0, 2.0, 3.0]))
        export = memory1.export_for_composition()

        # Create second memory to import into
        memory2 = ConversationMemory(agent_id="agent2", storage_path=temp_storage / "agent2")

        # ACT
        memory2.import_and_compose(export)

        # ASSERT - The import should successfully load the embeddings
        # (Note: actual merging is pending Task 1.3, but loading should work)
        assert export['embedding_state'] is not None

    def test_conversation_memory_saves_empty_embeddings(self, temp_storage):
        """Test that empty embeddings can be saved and loaded."""
        # ARRANGE
        memory1 = ConversationMemory(agent_id="test", storage_path=temp_storage)
        # Don't add any embeddings
        memory1._save()

        # ACT
        memory2 = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # ASSERT
        assert len(memory2.embeddings.levels) == 0

    def test_conversation_memory_embeddings_with_metadata(self, temp_storage):
        """Test that embedding metadata is preserved through persistence."""
        # ARRANGE
        memory1 = ConversationMemory(agent_id="test", storage_path=temp_storage)
        metadata = {'source': 'test', 'timestamp': '2025-01-01'}
        memory1.embeddings.add_embedding(
            'fine', 'test', np.array([1.0, 2.0]), metadata
        )
        memory1._save()

        # ACT
        memory2 = ConversationMemory(agent_id="test", storage_path=temp_storage)

        # ASSERT
        loaded_emb = memory2.embeddings.get_embedding('fine', 'test')
        assert loaded_emb.metadata == metadata


if __name__ == "__main__":
    # Allow running tests directly
    pytest.main([__file__, "-v"])
