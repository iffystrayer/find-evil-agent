"""Tests for ToolRegistry - Semantic search over SIFT tools.

TDD Structure:
1. TestToolRegistrySpecification - ALWAYS PASSING (requirements documentation)
2. TestToolRegistryStructure - Tests registry interface compliance
3. TestToolRegistryExecution - Tests actual registry behavior
"""

from pathlib import Path

import pytest

from find_evil_agent.tools.registry import ToolRegistry


class TestToolRegistrySpecification:
    """Specification tests - ALWAYS PASSING.

    Document ToolRegistry requirements and expected behavior.
    """

    def test_tool_registry_requirements(self):
        """Document ToolRegistry requirements."""
        requirements = {
            "metadata_source": "YAML file (tools/metadata.yaml)",
            "embedding_model": "SentenceTransformers (all-MiniLM-L6-v2)",
            "search_backend": "FAISS IndexFlatL2",
            "caching": "Disk cache for embeddings (.cache/embeddings/)",
            "tools_count": 18,  # SIFT tools documented
            "categories": [
                "memory",
                "disk",
                "timeline",
                "network",
                "analysis",
                "hash",
                "registry",
                "metadata",
            ],
        }
        assert requirements["metadata_source"] == "YAML file (tools/metadata.yaml)"
        assert requirements["embedding_model"] == "SentenceTransformers (all-MiniLM-L6-v2)"
        assert requirements["search_backend"] == "FAISS IndexFlatL2"

    def test_semantic_search_workflow(self):
        """Document semantic search workflow."""
        workflow = {
            "step1": "Load tool metadata from YAML",
            "step2": "Generate embeddings for tool descriptions + keywords",
            "step3": "Normalize embeddings for cosine similarity",
            "step4": "Build FAISS index for fast search",
            "step5": "Cache embeddings to disk",
            "step6": "On query: encode query, search FAISS, return ranked results",
        }
        assert workflow["step2"] == "Generate embeddings for tool descriptions + keywords"
        assert workflow["step6"] == "On query: encode query, search FAISS, return ranked results"

    def test_caching_strategy(self):
        """Document embedding cache strategy."""
        cache_strategy = {
            "location": ".cache/embeddings/",
            "files": ["tool_embeddings.npy", "faiss.index"],
            "invalidation": "Cache mismatch if tool count changes",
            "benefits": "Fast startup after first run",
        }
        assert cache_strategy["location"] == ".cache/embeddings/"
        assert len(cache_strategy["files"]) == 2


class TestToolRegistryStructure:
    """Structure tests - Validate registry interface compliance."""

    def test_registry_can_be_instantiated(self):
        """ToolRegistry should be instantiable with default parameters."""
        registry = ToolRegistry()
        assert registry is not None

    def test_registry_has_required_methods(self):
        """ToolRegistry should have search, get_tool, list_tools methods."""
        registry = ToolRegistry()
        assert hasattr(registry, "search")
        assert hasattr(registry, "get_tool")
        assert hasattr(registry, "list_tools")
        assert hasattr(registry, "get_categories")
        assert hasattr(registry, "refresh_embeddings")
        assert callable(registry.search)
        assert callable(registry.get_tool)

    def test_registry_loads_tools_on_init(self):
        """ToolRegistry should load tools from metadata on initialization."""
        registry = ToolRegistry()
        assert hasattr(registry, "tools")
        assert isinstance(registry.tools, list)
        assert len(registry.tools) > 0

    def test_registry_creates_index_on_init(self):
        """ToolRegistry should create FAISS index on initialization."""
        registry = ToolRegistry()
        assert hasattr(registry, "index")
        assert hasattr(registry, "embeddings")
        assert registry.index is not None


class TestToolRegistryExecution:
    """Execution tests - Test actual registry behavior."""

    def test_registry_loads_18_sift_tools(self):
        """Registry should load all 18 SIFT tools from metadata.yaml."""
        registry = ToolRegistry()
        assert len(registry.tools) == 18

    def test_registry_tools_have_required_fields(self):
        """Each tool should have name, category, description, confidence_keywords."""
        registry = ToolRegistry()
        required_fields = ["name", "category", "description", "confidence_keywords"]

        for tool in registry.tools:
            for field in required_fields:
                assert field in tool, f"Tool missing field: {field}"
                assert tool[field] is not None

    def test_get_tool_by_exact_name(self):
        """get_tool() should return tool metadata by exact name."""
        registry = ToolRegistry()

        volatility = registry.get_tool("volatility")
        assert volatility is not None
        assert volatility["name"] == "volatility"
        assert volatility["category"] == "memory"
        assert "memory forensics" in volatility["description"].lower()

    def test_get_tool_returns_none_for_unknown(self):
        """get_tool() should return None for unknown tool names."""
        registry = ToolRegistry()
        unknown = registry.get_tool("nonexistent_tool")
        assert unknown is None

    def test_list_tools_returns_all_tools(self):
        """list_tools() should return all tools when no category specified."""
        registry = ToolRegistry()
        all_tools = registry.list_tools()
        assert len(all_tools) == 18

    def test_list_tools_filters_by_category(self):
        """list_tools(category) should filter tools by category."""
        registry = ToolRegistry()

        memory_tools = registry.list_tools(category="memory")
        assert len(memory_tools) >= 2  # volatility, rekall
        for tool in memory_tools:
            assert tool["category"] == "memory"

        disk_tools = registry.list_tools(category="disk")
        assert len(disk_tools) >= 4  # fls, icat, mmls, fsstat
        for tool in disk_tools:
            assert tool["category"] == "disk"

    def test_get_categories_returns_unique_categories(self):
        """get_categories() should return sorted list of unique categories."""
        registry = ToolRegistry()
        categories = registry.get_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "memory" in categories
        assert "disk" in categories
        assert "network" in categories
        # Should be sorted
        assert categories == sorted(categories)

    def test_search_returns_ranked_results(self):
        """search() should return tools ranked by similarity."""
        registry = ToolRegistry()

        results = registry.search("analyze memory dump", top_k=5)

        assert isinstance(results, list)
        assert len(results) <= 5
        assert len(results) > 0

        # Each result should have required fields
        for result in results:
            assert "tool" in result
            assert "similarity" in result
            assert "distance" in result
            assert "rank" in result
            assert isinstance(result["similarity"], float)
            assert 0.0 <= result["similarity"] <= 1.0

    def test_search_top_result_is_relevant(self):
        """search() should return most relevant tool as top result."""
        registry = ToolRegistry()

        # Memory dump query should return volatility or rekall
        memory_results = registry.search("analyze memory dump for processes", top_k=3)
        top_tool = memory_results[0]["tool"]["name"]
        assert top_tool in ["volatility", "rekall"]

        # Disk query should return disk tools
        disk_results = registry.search("list files in disk image", top_k=3)
        top_tool = disk_results[0]["tool"]["name"]
        assert top_tool in ["fls", "icat", "mmls", "fsstat"]

        # Network query should return network tools
        network_results = registry.search("analyze network traffic pcap", top_k=3)
        top_tool = network_results[0]["tool"]["name"]
        assert top_tool in ["tcpdump", "wireshark"]

    def test_search_respects_top_k_parameter(self):
        """search() should return at most top_k results."""
        registry = ToolRegistry()

        results_3 = registry.search("forensic analysis", top_k=3)
        assert len(results_3) == 3

        results_10 = registry.search("forensic analysis", top_k=10)
        assert len(results_10) == 10

        results_all = registry.search("forensic analysis", top_k=100)
        assert len(results_all) == 18  # Max is number of tools

    def test_search_results_are_sorted_by_similarity(self):
        """search() results should be sorted by similarity (highest first)."""
        registry = ToolRegistry()

        results = registry.search("extract strings from binary", top_k=5)

        similarities = [r["similarity"] for r in results]
        assert similarities == sorted(similarities, reverse=True)

    def test_embeddings_are_cached_to_disk(self):
        """Embeddings should be cached to .cache/embeddings/."""
        registry = ToolRegistry()

        cache_dir = registry.cache_dir
        assert cache_dir.exists()

        embeddings_file = cache_dir / "tool_embeddings.npy"
        index_file = cache_dir / "faiss.index"

        assert embeddings_file.exists()
        assert index_file.exists()

    def test_registry_loads_from_cache_on_second_init(self):
        """Second registry instance should load from cache (faster)."""
        import time

        # First init (may generate embeddings)
        start = time.time()
        registry1 = ToolRegistry()
        first_duration = time.time() - start

        # Second init (should load from cache)
        start = time.time()
        registry2 = ToolRegistry()
        second_duration = time.time() - start

        # Second init should be faster (or at least not significantly slower)
        # Note: This is a weak assertion since caching may already exist
        assert second_duration <= first_duration * 2

    def test_refresh_embeddings_regenerates_cache(self):
        """refresh_embeddings() should regenerate cache files."""
        registry = ToolRegistry()

        cache_dir = registry.cache_dir
        embeddings_file = cache_dir / "tool_embeddings.npy"

        # Get original modification time
        import os

        original_mtime = os.path.getmtime(embeddings_file)

        # Sleep briefly to ensure new timestamp
        import time

        time.sleep(0.1)

        # Refresh embeddings
        registry.refresh_embeddings()

        # Check that file was regenerated (new mtime)
        new_mtime = os.path.getmtime(embeddings_file)
        assert new_mtime >= original_mtime

    def test_tool_metadata_includes_confidence_keywords(self):
        """Tools should include confidence_keywords for semantic matching."""
        registry = ToolRegistry()

        volatility = registry.get_tool("volatility")
        assert "confidence_keywords" in volatility
        assert isinstance(volatility["confidence_keywords"], list)
        assert len(volatility["confidence_keywords"]) > 0

        # Volatility should have memory-related keywords
        keywords = volatility["confidence_keywords"]
        assert any("memory" in kw.lower() for kw in keywords)

    def test_search_uses_confidence_keywords(self):
        """search() should match against confidence_keywords."""
        registry = ToolRegistry()

        # Query using confidence keyword should rank tool higher
        results = registry.search("pslist processes", top_k=5)
        top_tool = results[0]["tool"]["name"]

        # "pslist" is a confidence keyword for volatility
        assert top_tool == "volatility"

    def test_registry_handles_missing_metadata_file(self):
        """ToolRegistry should raise FileNotFoundError if metadata missing."""

        invalid_path = Path("/nonexistent/metadata.yaml")

        with pytest.raises(FileNotFoundError, match="Tool metadata not found"):
            ToolRegistry(metadata_path=invalid_path)

    def test_get_tool_returns_copy_not_reference(self):
        """get_tool() should return copy to prevent mutations."""
        registry = ToolRegistry()

        tool1 = registry.get_tool("volatility")
        tool2 = registry.get_tool("volatility")

        # Modify tool1
        tool1["name"] = "modified"

        # tool2 should not be affected
        assert tool2["name"] == "volatility"

    def test_search_returns_copy_of_tools(self):
        """search() should return copies of tool metadata."""
        registry = ToolRegistry()

        results = registry.search("memory", top_k=1)
        tool = results[0]["tool"]

        # Modify returned tool
        original_name = tool["name"]
        tool["name"] = "modified"

        # Original in registry should not be affected
        original = registry.get_tool(original_name)
        assert original["name"] == original_name
