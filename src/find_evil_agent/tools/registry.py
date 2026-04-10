"""Tool Registry - Central catalog of SIFT tools.

This module provides semantic search over SIFT forensic tools using:
- YAML metadata (tools/metadata.yaml)
- SentenceTransformers for embeddings
- FAISS for vector similarity search
- Disk caching for performance

Example:
    >>> registry = ToolRegistry()
    >>> results = registry.search("analyze memory dump", top_k=5)
    >>> for result in results:
    ...     print(f"{result['tool']['name']}: {result['similarity']:.3f}")
    volatility: 0.892
    rekall: 0.745
"""

from typing import Any
from pathlib import Path
import yaml
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import structlog

logger = structlog.get_logger()


class ToolRegistry:
    """Registry of available SIFT tools with semantic search.

    Provides:
    - Tool metadata loading from YAML
    - Semantic search using embeddings + FAISS
    - Disk caching for embeddings (fast subsequent loads)
    - Tool lookup by exact name
    - Category filtering

    Design:
        - Embeddings are generated from tool description + confidence keywords
        - FAISS IndexFlatL2 for similarity search (cosine via L2 normalization)
        - Embeddings cached to .cache/embeddings/ for fast startup
    """

    def __init__(
        self,
        metadata_path: Path | None = None,
        cache_dir: Path | None = None,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        """Initialize tool registry.

        Args:
            metadata_path: Path to tools/metadata.yaml
            cache_dir: Directory for caching embeddings (default: .cache/embeddings)
            embedding_model: SentenceTransformer model name

        Example:
            >>> registry = ToolRegistry()
            >>> len(registry.tools)
            18
        """
        # Paths
        if metadata_path is None:
            # Default to tools/metadata.yaml in project root
            metadata_path = Path(__file__).parent.parent.parent.parent / "tools" / "metadata.yaml"

        self.metadata_path = metadata_path
        self.cache_dir = cache_dir or Path(".cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Embedding model
        self.embedding_model_name = embedding_model
        self.model: SentenceTransformer | None = None  # Lazy load

        # Load tool metadata
        self.tools = self._load_metadata()

        # Load or create embeddings
        self.index, self.embeddings = self._load_or_create_embeddings()

        logger.info(
            "tool_registry_initialized",
            tool_count=len(self.tools),
            cache_dir=str(self.cache_dir)
        )

    def _load_metadata(self) -> list[dict[str, Any]]:
        """Load tool metadata from YAML file.

        Returns:
            List of tool metadata dicts

        Raises:
            FileNotFoundError: If metadata file not found
            yaml.YAMLError: If YAML parsing fails
        """
        if not self.metadata_path.exists():
            raise FileNotFoundError(
                f"Tool metadata not found: {self.metadata_path}\n"
                f"Expected file at: {self.metadata_path.absolute()}"
            )

        with open(self.metadata_path, 'r') as f:
            data = yaml.safe_load(f)

        if 'tools' not in data:
            raise ValueError("Metadata YAML must contain 'tools' key")

        return data['tools']

    def _get_model(self) -> SentenceTransformer:
        """Lazy load embedding model.

        Returns:
            SentenceTransformer model instance
        """
        if self.model is None:
            logger.info("loading_embedding_model", model=self.embedding_model_name)
            self.model = SentenceTransformer(self.embedding_model_name)
        return self.model

    def _load_or_create_embeddings(self) -> tuple[faiss.Index, np.ndarray]:
        """Load embeddings from cache or generate new ones.

        Cache files:
            - tool_embeddings.npy: NumPy array of embeddings
            - faiss.index: FAISS index for similarity search

        Returns:
            Tuple of (FAISS index, embeddings array)
        """
        cache_file = self.cache_dir / "tool_embeddings.npy"
        index_file = self.cache_dir / "faiss.index"

        # Check cache
        if cache_file.exists() and index_file.exists():
            try:
                embeddings = np.load(cache_file)
                index = faiss.read_index(str(index_file))

                # Verify cache matches current tools
                if len(embeddings) == len(self.tools):
                    logger.info(
                        "embeddings_loaded_from_cache",
                        count=len(embeddings),
                        cache_dir=str(self.cache_dir)
                    )
                    return index, embeddings
                else:
                    logger.warning(
                        "cache_mismatch",
                        cached=len(embeddings),
                        current=len(self.tools),
                        action="regenerating"
                    )
            except Exception as e:
                logger.warning("cache_read_failed", error=str(e), action="regenerating")

        # Generate embeddings
        logger.info("generating_embeddings", tool_count=len(self.tools))
        model = self._get_model()

        # Create combined text for each tool (description + keywords)
        tool_texts = []
        for tool in self.tools:
            # Combine description with confidence keywords for richer semantic matching
            combined = f"{tool['description']} {' '.join(tool.get('confidence_keywords', []))}"
            tool_texts.append(combined)

        # Generate embeddings
        embeddings = model.encode(
            tool_texts,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        embeddings = embeddings.astype('float32')

        # Normalize for cosine similarity (L2 distance on normalized vectors = cosine)
        faiss.normalize_L2(embeddings)

        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)

        # Save to cache
        try:
            np.save(cache_file, embeddings)
            faiss.write_index(index, str(index_file))
            logger.info("embeddings_cached", count=len(embeddings), cache_dir=str(self.cache_dir))
        except Exception as e:
            logger.warning("cache_write_failed", error=str(e))

        return index, embeddings

    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Semantic search for tools matching query.

        Uses embedding similarity to find tools that semantically match
        the user's query. Returns tools sorted by relevance.

        Args:
            query: Natural language query (e.g., "analyze memory dump")
            top_k: Number of results to return

        Returns:
            List of dicts with 'tool', 'similarity', 'distance' keys
            Sorted by similarity (highest first)

        Example:
            >>> results = registry.search("find deleted files", top_k=3)
            >>> for r in results:
            ...     print(f"{r['tool']['name']}: {r['similarity']:.3f}")
            fls: 0.867
            icat: 0.712
            bulk_extractor: 0.645
        """
        model = self._get_model()

        # Encode query
        query_embedding = model.encode([query], convert_to_numpy=True).astype('float32')

        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)

        # Search FAISS index
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.tools)))

        # Build results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            tool = self.tools[idx].copy()

            # Convert L2 distance on normalized vectors to similarity score
            # For normalized vectors: similarity = 1 - (distance^2 / 2)
            # Simpler: similarity ≈ 1 - distance (since normalized)
            similarity = max(0.0, 1.0 - float(distance))

            results.append({
                "tool": tool,
                "similarity": float(similarity),
                "distance": float(distance),
                "rank": len(results) + 1
            })

        logger.debug(
            "tool_search_completed",
            query=query,
            top_k=top_k,
            results_count=len(results),
            top_match=results[0]["tool"]["name"] if results else None
        )

        return results

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Get tool metadata by exact name.

        Args:
            name: Tool name (e.g., "volatility", "grep")

        Returns:
            Tool metadata dict or None if not found

        Example:
            >>> tool = registry.get_tool("volatility")
            >>> tool['category']
            'memory'
        """
        for tool in self.tools:
            if tool['name'] == name:
                return tool.copy()
        return None

    def list_tools(self, category: str | None = None) -> list[dict[str, Any]]:
        """List all tools, optionally filtered by category.

        Args:
            category: Filter by category (memory, disk, network, etc.)
                     If None, returns all tools

        Returns:
            List of tool metadata dicts

        Example:
            >>> memory_tools = registry.list_tools(category="memory")
            >>> [t['name'] for t in memory_tools]
            ['volatility', 'rekall']
        """
        if category:
            return [
                tool.copy()
                for tool in self.tools
                if tool.get('category') == category
            ]
        return [tool.copy() for tool in self.tools]

    def get_categories(self) -> list[str]:
        """Get list of all tool categories.

        Returns:
            List of unique category names

        Example:
            >>> registry.get_categories()
            ['memory', 'disk', 'timeline', 'network', 'analysis', 'hash', 'registry', 'metadata']
        """
        categories = set()
        for tool in self.tools:
            if 'category' in tool:
                categories.add(tool['category'])
        return sorted(list(categories))

    def refresh_embeddings(self) -> None:
        """Force regeneration of embeddings.

        Call this after updating tools/metadata.yaml to rebuild the embedding cache.

        Example:
            >>> registry.refresh_embeddings()
        """
        cache_file = self.cache_dir / "tool_embeddings.npy"
        index_file = self.cache_dir / "faiss.index"

        # Delete cache
        cache_file.unlink(missing_ok=True)
        index_file.unlink(missing_ok=True)

        # Regenerate
        self.index, self.embeddings = self._load_or_create_embeddings()

        logger.info("embeddings_refreshed", tool_count=len(self.tools))
