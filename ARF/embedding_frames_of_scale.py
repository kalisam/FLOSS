"""embedding_frames_of_scale
==============================

This module provides utilities for working with *multi‑scale* embeddings,
where each embedding lives at a particular level of granularity.  A
**frame of reference** in this context is a *matrix of matrices* – a
mapping from one level of detail to another.  Fine‑grained vectors
represent individual agents or sensors, while coarse‑grained vectors
represent communities or aggregates.  The relationships between these
levels are *fractal* and **self‑similar**: a coarse embedding is built
from the sum (or mean) of its constituent fine embeddings, and this
pattern can repeat recursively.

The research inspiration for this design comes from recent work on
multi‑scale node embeddings for graph modelling and generation, where
Milocco et al. (2025) propose that coarse (block‑node) embeddings
should be statistically consistent with the sum of the embeddings of
their constituent nodes【44685813190291†L48-L69】.  By encoding this
property directly into the embedding data structure, we support
hierarchical reference frames that can be composed, decomposed and
embedded within one another.  This mirrors how biological and
agentic systems use nested coordinate frames – from retinal
retinotopic maps to head‑centred and world‑centred representations –
to interpret sensory input【86986790368444†L132-L141】.

In the spirit of FLOSSI0ULLK values:

* **Love** – Each embedding retains provenance metadata about its
  origin and the agents that contributed to it; coarse embeddings are
  transparent aggregations rather than opaque averages.
* **Light** – Logging is used throughout to illuminate how
  embeddings are constructed and combined, aiding observability and
  accountability.
* **Knowledge** – Hierarchical embeddings support collective
  intelligence by allowing local knowledge to be aggregated into
  global summaries without losing the ability to drill back down.

The classes in this module are written with type hints, clear
docstrings and modest error handling to encourage reuse in a
distributed intelligence system.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Iterable, Optional, Any
import numpy as np

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@dataclass
class Embedding:
    """Represents a single embedding vector along with optional metadata.

    Parameters
    ----------
    vector:
        A one‑dimensional numpy array containing the numeric embedding.
    metadata:
        Optional dictionary carrying provenance or descriptive information
        about this embedding (e.g. agent ID, timestamp, context).  This
        dictionary can be arbitrarily nested.  Storing metadata aligns
        with the FLOSSI0ULLK principle of **Love**, preserving the
        identity and agency of contributors.
    """
    vector: np.ndarray
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.vector, np.ndarray):
            raise TypeError("vector must be a numpy.ndarray")
        if self.vector.ndim != 1:
            raise ValueError("vector must be one‑dimensional")

class MultiScaleEmbedding:
    """Manages embeddings across multiple scales or reference frames.

    This class maintains a mapping from level identifiers (strings or
    integers) to dictionaries of embeddings.  It provides methods to
    add fine‑level embeddings and to generate coarser embeddings by
    aggregating finer ones.  A coarse embedding encapsulates the
    information of its child embeddings without discarding their
    individual contributions.  This supports fractal, recursive
    structures where a matrix of matrices emerges naturally from the
    relationships between levels.

    Attributes
    ----------
    levels:
        Dictionary mapping level identifiers to dictionaries of
        embeddings keyed by an embedding ID.  For example,
        ``levels['fine']['node_1']`` returns the ``Embedding`` object
        representing node 1 at the fine level.
    aggregator:
        Callable used to combine vectors when creating coarse
        embeddings.  By default it sums the vectors, consistent with
        the statistical requirements for multi‑scale embeddings
        proposed by Milocco et al. (2025)【44685813190291†L48-L69】.  An
        alternative aggregator (e.g. mean) can be supplied.

    Notes
    -----
    • When adding a coarse level, you must provide a grouping that
      specifies how fine IDs map to coarse IDs.  The aggregator is
      applied to the vectors of the fine embeddings belonging to the
      same coarse ID.
    • Metadata from the fine embeddings is merged into the coarse
      embedding's metadata under the key ``'children'``.  This
      preserves provenance and enables drilling down.
    • Logging at DEBUG level reports the construction of coarse
      embeddings and any issues encountered.
    """

    def __init__(self, aggregator: Callable[[Iterable[np.ndarray]], np.ndarray] | None = None) -> None:
        self.levels: Dict[str, Dict[str, Embedding]] = {}
        self.aggregator: Callable[[Iterable[np.ndarray]], np.ndarray] = (
            aggregator if aggregator is not None else self._default_aggregator
        )

    @staticmethod
    def _default_aggregator(vectors: Iterable[np.ndarray]) -> np.ndarray:
        """Default aggregator that sums vectors elementwise.

        This aggregator ensures that coarse embeddings are
        statistically consistent with the sum of their constituent
        embeddings【44685813190291†L48-L69】.
        """
        vectors = list(vectors)
        if not vectors:
            raise ValueError("No vectors provided for aggregation")
        result = np.sum(vectors, axis=0)
        return result

    def add_embedding(self, level: str, embedding_id: str, vector: np.ndarray, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add an embedding at a given level.

        Parameters
        ----------
        level:
            Identifier for the level (e.g. 'fine', 'coarse1').
        embedding_id:
            Unique key for this embedding within the level.
        vector:
            One‑dimensional numpy array representing the embedding.
        metadata:
            Optional dictionary with provenance info.  Defaults to empty.

        Raises
        ------
        ValueError
            If an embedding with the same ID already exists at the level.
        """
        if level not in self.levels:
            self.levels[level] = {}
        if embedding_id in self.levels[level]:
            raise ValueError(f"Embedding ID '{embedding_id}' already exists in level '{level}'")
        emb = Embedding(vector=vector, metadata=metadata or {})
        self.levels[level][embedding_id] = emb
        logger.debug("Added embedding %s at level %s", embedding_id, level)

    def add_coarse_level(self, coarse_level: str, fine_level: str, grouping: Dict[str, List[str]]) -> None:
        """Create a coarse level by aggregating fine‑level embeddings.

        Parameters
        ----------
        coarse_level:
            Name for the new coarse level.
        fine_level:
            Existing level from which to aggregate embeddings.
        grouping:
            Mapping from coarse embedding IDs to lists of fine IDs.  Each
            coarse ID will combine the vectors of its associated fine
            embeddings using the configured aggregator.

        Raises
        ------
        KeyError
            If ``fine_level`` does not exist or if a fine ID is missing.
        ValueError
            If ``coarse_level`` already exists.

        Notes
        -----
        This method constructs coarse embeddings by combining the
        vectors of the specified fine embeddings.  The metadata of
        these children is preserved in a list under the ``'children'``
        key of the coarse embedding's metadata.  If any fine IDs are
        missing, a KeyError is raised.
        """
        if fine_level not in self.levels:
            raise KeyError(f"Fine level '{fine_level}' does not exist")
        if coarse_level in self.levels:
            raise ValueError(f"Coarse level '{coarse_level}' already exists")
        self.levels[coarse_level] = {}
        fine_embeddings = self.levels[fine_level]
        for coarse_id, fine_ids in grouping.items():
            vectors = []
            children_meta: List[Dict[str, Any]] = []
            for fid in fine_ids:
                if fid not in fine_embeddings:
                    raise KeyError(f"Fine embedding ID '{fid}' not found in level '{fine_level}'")
                emb = fine_embeddings[fid]
                vectors.append(emb.vector)
                children_meta.append({
                    'id': fid,
                    'metadata': emb.metadata,
                })
            coarse_vector = self.aggregator(vectors)
            coarse_metadata = {
                'children': children_meta,
                'source_level': fine_level,
            }
            self.levels[coarse_level][coarse_id] = Embedding(vector=coarse_vector, metadata=coarse_metadata)
            logger.debug("Created coarse embedding %s at level %s from %d children", coarse_id, coarse_level, len(fine_ids))

    def get_embedding(self, level: str, embedding_id: str) -> Embedding:
        """Retrieve an embedding by level and ID.

        Parameters
        ----------
        level:
            Level identifier.
        embedding_id:
            ID of the embedding within the level.

        Returns
        -------
        Embedding
            The requested embedding.

        Raises
        ------
        KeyError
            If the level or embedding ID does not exist.
        """
        if level not in self.levels:
            raise KeyError(f"Level '{level}' does not exist")
        if embedding_id not in self.levels[level]:
            raise KeyError(f"Embedding ID '{embedding_id}' not found in level '{level}'")
        return self.levels[level][embedding_id]

    def get_all_embeddings(self, level: str) -> Dict[str, Embedding]:
        """Return all embeddings at a given level.

        Parameters
        ----------
        level:
            Level identifier.

        Returns
        -------
        Dict[str, Embedding]
            A dictionary mapping embedding IDs to embeddings.

        Raises
        ------
        KeyError
            If the level does not exist.
        """
        if level not in self.levels:
            raise KeyError(f"Level '{level}' does not exist")
        return self.levels[level].copy()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the multi-scale embedding to a dictionary.

        Converts all numpy arrays to lists for JSON serialization.
        Preserves all embedding metadata and level structure.

        Returns
        -------
        Dict[str, Any]
            Dictionary representation suitable for JSON serialization.

        Example
        -------
        >>> mse = MultiScaleEmbedding()
        >>> mse.add_embedding('fine', 'node1', np.array([1.0, 2.0]))
        >>> data = mse.to_dict()
        >>> 'levels' in data
        True
        """
        serialized_levels = {}
        for level_name, embeddings in self.levels.items():
            serialized_levels[level_name] = {}
            for emb_id, embedding in embeddings.items():
                serialized_levels[level_name][emb_id] = {
                    'vector': embedding.vector.tolist(),
                    'metadata': embedding.metadata,
                }

        return {
            'levels': serialized_levels,
            'is_default_aggregator': self.aggregator == self._default_aggregator,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiScaleEmbedding':
        """Reconstruct a MultiScaleEmbedding instance from dictionary representation.

        This is the inverse of to_dict(), enabling serialization round-trips.

        Parameters
        ----------
        data:
            Dictionary produced by to_dict().

        Returns
        -------
        MultiScaleEmbedding
            New MultiScaleEmbedding instance with restored state.

        Raises
        ------
        ValueError
            If data is malformed or missing required fields.
        TypeError
            If data types don't match expected schema.

        Example
        -------
        >>> original = MultiScaleEmbedding()
        >>> original.add_embedding('fine', 'test', np.array([1.0, 2.0]))
        >>> serialized = original.to_dict()
        >>> restored = MultiScaleEmbedding.from_dict(serialized)
        >>> np.allclose(
        ...     original.get_embedding('fine', 'test').vector,
        ...     restored.get_embedding('fine', 'test').vector
        ... )
        True
        """
        # Validate input type
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict, got {type(data).__name__}")

        # Validate required fields
        if 'levels' not in data:
            raise ValueError("Missing required field: 'levels'")

        # Create instance with appropriate aggregator
        # For now, only support default aggregator in deserialization
        # Custom aggregators would need separate handling
        is_default = data.get('is_default_aggregator', True)
        if not is_default:
            logger.warning(
                "Custom aggregator detected but not supported in deserialization; "
                "using default aggregator"
            )

        instance = cls()

        # Restore embeddings at each level
        levels_data = data['levels']
        if not isinstance(levels_data, dict):
            raise TypeError(f"Expected 'levels' to be dict, got {type(levels_data).__name__}")

        for level_name, embeddings_dict in levels_data.items():
            if not isinstance(embeddings_dict, dict):
                raise TypeError(
                    f"Expected embeddings at level '{level_name}' to be dict, "
                    f"got {type(embeddings_dict).__name__}"
                )

            for emb_id, emb_data in embeddings_dict.items():
                # Validate embedding data structure
                if not isinstance(emb_data, dict):
                    raise TypeError(
                        f"Expected embedding data for '{emb_id}' to be dict, "
                        f"got {type(emb_data).__name__}"
                    )

                if 'vector' not in emb_data:
                    raise ValueError(f"Missing 'vector' field in embedding '{emb_id}' at level '{level_name}'")

                # Convert list back to numpy array
                vector_data = emb_data['vector']
                if isinstance(vector_data, list):
                    try:
                        vector = np.array(vector_data, dtype=np.float32)
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Failed to convert vector for '{emb_id}' at level '{level_name}': {e}"
                        ) from e
                elif isinstance(vector_data, np.ndarray):
                    vector = vector_data.astype(np.float32)
                else:
                    raise TypeError(
                        f"Invalid vector type for '{emb_id}' at level '{level_name}': "
                        f"expected list or ndarray, got {type(vector_data).__name__}"
                    )

                # Restore metadata (default to empty dict if not present)
                metadata = emb_data.get('metadata', {})
                if not isinstance(metadata, dict):
                    raise TypeError(
                        f"Expected metadata for '{emb_id}' to be dict, "
                        f"got {type(metadata).__name__}"
                    )

                # Add the embedding to the instance
                instance.add_embedding(level_name, emb_id, vector, metadata)

        logger.debug(
            "Deserialized MultiScaleEmbedding with %d levels",
            len(instance.levels)
        )

        return instance

    def __repr__(self) -> str:
        return f"MultiScaleEmbedding(levels={list(self.levels.keys())})"