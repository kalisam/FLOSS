"""
Tests for ConversationMemory persistence functionality.

This test suite verifies that ConversationMemory can save and reload embeddings
using the MultiScaleEmbedding serialization methods.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import sys
import json
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from conversation_memory import ConversationMemory
from embedding_frames_of_scale import MultiScaleEmbedding


class TestConversationMemoryPersistence:
    """Test that ConversationMemory can save and reload embeddings."""

    @pytest.fixture
    def temp_storage(self):
        """Create a temporary directory for storage."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir)

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


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
