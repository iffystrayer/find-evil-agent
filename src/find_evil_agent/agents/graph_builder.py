"""Graph Builder - Attack chain graph generation.

Extracts entity relationships from findings to build interactive
attack chain visualizations.

Key Features:
- Relationship extraction from finding descriptions
- Node deduplication and occurrence tracking
- Severity propagation from findings to entities
- Critical path identification
- Export to NetworkX, GraphML, GEXF, JSON formats
"""

import re
import json
from datetime import datetime
from collections import defaultdict
from typing import Any
import structlog
import networkx as nx

from .schemas import Finding, FindingSeverity
from .report_schemas import GraphNode, GraphEdge, AttackGraph

logger = structlog.get_logger(__name__)


# Relationship extraction patterns
RELATIONSHIP_PATTERNS = {
    "process_spawn": [
        r"([\w\.\-]+)\s+(?:spawned|created|launched|started)\s+([\w\.\-]+)",
        r"([\w\.\-]+)\s+→\s+([\w\.\-]+)",  # Arrow notation
    ],
    "file_created": [
        r"(?:created|wrote|modified|generated)\s+(?:file\s+)?([/\\\w\.\-]+)",
        r"file\s+([/\\\w\.\-]+)\s+(?:was\s+)?(?:created|written|modified)",
    ],
    "file_read": [
        r"(?:read|opened|accessed)\s+(?:file\s+)?([/\\\w\.\-]+)",
    ],
    "network_connection": [
        r"connected to\s+([\d\.]+)(?::(\d+))?",
        r"(?:to|from)\s+([\d\.]+)(?::(\d+))?",
    ],
    "registry_modification": [
        r"modified registry (?:key\s+)?([A-Z_]+\\[\w\\]+)",
        r"registry (?:key\s+)?([A-Z_]+\\[\w\\]+)",
    ],
    "dns_query": [
        r"(?:DNS|dns) query (?:for\s+)?([a-z0-9\.\-]+\.[a-z]{2,})",
        r"queried\s+([a-z0-9\.\-]+\.[a-z]{2,})",
    ],
}


# IOC type patterns for entity classification
IOC_PATTERNS = {
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "md5": r"\b[a-f0-9]{32}\b",
    "sha1": r"\b[a-f0-9]{40}\b",
    "sha256": r"\b[a-f0-9]{64}\b",
    "domain": r"\b[a-z0-9\-]+\.[a-z]{2,}\b",
    "email": r"\b[\w\.\-]+@[a-z0-9\.\-]+\.[a-z]{2,}\b",
}


# Severity ordering for propagation
SEVERITY_ORDER = {
    "critical": 4,
    "high": 3,
    "medium": 2,
    "low": 1,
    "info": 0,
}


class GraphBuilder:
    """Build attack chain graphs from findings.

    Extracts entity relationships from findings and builds directed
    graphs showing attack progression.
    """

    def __init__(self):
        """Initialize graph builder."""
        self.logger = structlog.get_logger(__name__)

    def build_graph(self, findings: list[Finding]) -> AttackGraph:
        """Build attack graph from findings.

        Args:
            findings: List of findings to process

        Returns:
            AttackGraph with nodes, edges, and metadata
        """
        if not findings:
            return AttackGraph(
                nodes=[],
                edges=[],
                entry_points=[],
                critical_path=[],
                metadata={
                    "node_count": 0,
                    "edge_count": 0,
                    "entry_point_count": 0,
                    "generated_at": datetime.utcnow().isoformat(),
                }
            )

        # Track nodes and edges with deduplication
        nodes_dict: dict[str, dict[str, Any]] = {}
        edges_list: list[dict[str, Any]] = []

        # Process each finding
        for finding in findings:
            # Extract IOCs as nodes
            for ioc in finding.iocs:
                node_id = self._generate_node_id(ioc.type, ioc.value)
                self._add_or_update_node(
                    nodes_dict,
                    node_id,
                    ioc.value,
                    self._classify_node_type(ioc.type, ioc.value),
                    finding.severity.value,
                    {
                        "ioc_type": ioc.type,
                        "finding_title": finding.title,
                        "tool_name": finding.tool_name,
                        "confidence": finding.confidence,
                    }
                )

            # Extract relationships from description
            relationships = self.extract_relationships(finding)
            for rel in relationships:
                # Add source and target nodes if not already present
                source_id = self._generate_node_id(rel["source_type"], rel["source"])
                target_id = self._generate_node_id(rel["target_type"], rel["target"])

                self._add_or_update_node(
                    nodes_dict,
                    source_id,
                    rel["source"],
                    rel["source_type"],
                    finding.severity.value,
                    {"finding_title": finding.title}
                )

                self._add_or_update_node(
                    nodes_dict,
                    target_id,
                    rel["target"],
                    rel["target_type"],
                    finding.severity.value,
                    {"finding_title": finding.title}
                )

                # Add edge
                edges_list.append({
                    "source": source_id,
                    "target": target_id,
                    "edge_type": rel["edge_type"],
                    "label": rel["label"],
                    "properties": {
                        "finding_title": finding.title,
                        "confidence": finding.confidence,
                    }
                })

        # Convert to schema objects
        nodes = [
            GraphNode(
                id=node_id,
                label=data["label"],
                node_type=data["node_type"],
                severity=data["severity"],
                properties=data["properties"],
                occurrences=data["occurrences"]
            )
            for node_id, data in nodes_dict.items()
        ]

        edges = [
            GraphEdge(
                source=edge["source"],
                target=edge["target"],
                edge_type=edge["edge_type"],
                label=edge["label"],
                properties=edge["properties"]
            )
            for edge in edges_list
        ]

        # Identify entry points (nodes with no incoming edges)
        target_nodes = {edge.target for edge in edges}
        entry_points = [node.id for node in nodes if node.id not in target_nodes]

        # Calculate critical path
        critical_path = self._calculate_critical_path(nodes, edges)

        # Generate metadata
        metadata = {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "entry_point_count": len(entry_points),
            "generated_at": datetime.utcnow().isoformat(),
            "severity_distribution": self._calculate_severity_distribution(nodes),
            "node_type_distribution": self._calculate_node_type_distribution(nodes),
        }

        return AttackGraph(
            nodes=nodes,
            edges=edges,
            entry_points=entry_points,
            critical_path=critical_path,
            metadata=metadata
        )

    def extract_relationships(self, finding: Finding) -> list[dict[str, Any]]:
        """Extract entity relationships from finding description.

        Args:
            finding: Finding to process

        Returns:
            List of relationship dicts with source, target, type
        """
        relationships = []
        description = finding.description.lower()

        # Process spawn patterns
        for pattern in RELATIONSHIP_PATTERNS["process_spawn"]:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    source, target = match
                else:
                    continue
                relationships.append({
                    "source": source,
                    "source_type": "process",
                    "target": target,
                    "target_type": "process",
                    "edge_type": "spawned",
                    "label": f"{source} spawned {target}"
                })

        # Process file creation patterns
        for pattern in RELATIONSHIP_PATTERNS["file_created"]:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                file_path = match if isinstance(match, str) else match[0]
                # Try to find the creating process in the description
                process_match = re.search(r"([\w\.\-]+)\s+(?:created|wrote)", description, re.IGNORECASE)
                if process_match:
                    process_name = process_match.group(1)
                    relationships.append({
                        "source": process_name,
                        "source_type": "process",
                        "target": file_path,
                        "target_type": "file",
                        "edge_type": "created",
                        "label": f"{process_name} created {file_path}"
                    })

        # Process network connections
        for pattern in RELATIONSHIP_PATTERNS["network_connection"]:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    ip = match[0]
                    port = match[1] if len(match) > 1 and match[1] else ""
                else:
                    ip = match
                    port = ""

                # Try to find the connecting process
                process_match = re.search(r"([\w\.\-]+)\s+connected", description, re.IGNORECASE)
                if process_match:
                    process_name = process_match.group(1)
                    target = f"{ip}:{port}" if port else ip
                    relationships.append({
                        "source": process_name,
                        "source_type": "process",
                        "target": target,
                        "target_type": "network",
                        "edge_type": "connected_to",
                        "label": f"{process_name} connected to {target}"
                    })

        # Process registry modifications
        for pattern in RELATIONSHIP_PATTERNS["registry_modification"]:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                registry_key = match if isinstance(match, str) else match[0]
                # Try to find the modifying process
                process_match = re.search(r"([\w\.\-]+)\s+modified", description, re.IGNORECASE)
                if process_match:
                    process_name = process_match.group(1)
                    relationships.append({
                        "source": process_name,
                        "source_type": "process",
                        "target": registry_key,
                        "target_type": "registry",
                        "edge_type": "modified",
                        "label": f"{process_name} modified {registry_key}"
                    })

        return relationships

    def add_node(self, graph: AttackGraph, node: GraphNode) -> AttackGraph:
        """Add node to graph.

        Args:
            graph: Graph to modify
            node: Node to add

        Returns:
            Updated graph
        """
        # Check if node already exists
        existing = next((n for n in graph.nodes if n.id == node.id), None)
        if existing:
            # Update occurrence count
            existing.occurrences += 1
            # Update severity if higher
            if SEVERITY_ORDER.get(node.severity, 0) > SEVERITY_ORDER.get(existing.severity, 0):
                existing.severity = node.severity
        else:
            graph.nodes.append(node)

        return graph

    def add_edge(self, graph: AttackGraph, edge: GraphEdge) -> AttackGraph:
        """Add edge to graph.

        Args:
            graph: Graph to modify
            edge: Edge to add

        Returns:
            Updated graph
        """
        # Check if edge already exists
        existing = next(
            (e for e in graph.edges if e.source == edge.source and e.target == edge.target and e.edge_type == edge.edge_type),
            None
        )
        if not existing:
            graph.edges.append(edge)

        return graph

    def export_networkx(self, graph: AttackGraph) -> nx.DiGraph:
        """Export graph to NetworkX format.

        Args:
            graph: Graph to export

        Returns:
            NetworkX directed graph
        """
        G = nx.DiGraph()

        # Add nodes
        for node in graph.nodes:
            G.add_node(
                node.id,
                label=node.label,
                node_type=node.node_type,
                severity=node.severity,
                occurrences=node.occurrences,
                **node.properties
            )

        # Add edges
        for edge in graph.edges:
            G.add_edge(
                edge.source,
                edge.target,
                edge_type=edge.edge_type,
                label=edge.label,
                **edge.properties
            )

        return G

    def export_graphml(self, graph: AttackGraph, output_path: str) -> None:
        """Export graph to GraphML format.

        Args:
            graph: Graph to export
            output_path: Output file path

        Raises:
            OSError: If file cannot be written
        """
        G = self.export_networkx(graph)
        nx.write_graphml(G, output_path)
        self.logger.info("graph_exported", format="graphml", path=output_path, nodes=len(graph.nodes), edges=len(graph.edges))

    def export_json(self, graph: AttackGraph) -> str:
        """Export graph to JSON format.

        Args:
            graph: Graph to export

        Returns:
            JSON string representation
        """
        data = {
            "nodes": [
                {
                    "id": node.id,
                    "label": node.label,
                    "type": node.node_type,
                    "severity": node.severity,
                    "occurrences": node.occurrences,
                    "properties": node.properties
                }
                for node in graph.nodes
            ],
            "edges": [
                {
                    "source": edge.source,
                    "target": edge.target,
                    "type": edge.edge_type,
                    "label": edge.label,
                    "properties": edge.properties
                }
                for edge in graph.edges
            ],
            "metadata": graph.metadata
        }
        return json.dumps(data, indent=2)

    # Private helper methods

    def _generate_node_id(self, node_type: str, value: str) -> str:
        """Generate unique node ID from type and value."""
        # Normalize value
        normalized = value.lower().strip()
        # Create ID with type prefix
        return f"{node_type}_{hash(normalized) & 0xFFFFFFFF:08x}"

    def _classify_node_type(self, ioc_type: str, value: str) -> str:
        """Classify entity as process/file/network/registry/ioc."""
        # Check if it's a hash (MD5, SHA1, SHA256)
        if ioc_type in ["md5", "sha1", "sha256"]:
            return "ioc"

        # Check if it's an IP address
        if ioc_type == "ipv4" or re.match(IOC_PATTERNS["ipv4"], value):
            return "network"

        # Check if it's a domain
        if ioc_type == "domain" or re.match(IOC_PATTERNS["domain"], value):
            return "network"

        # Check if it's a file path
        if "/" in value or "\\" in value:
            return "file"

        # Check if it's a registry key
        if "\\" in value and any(value.upper().startswith(k) for k in ["HKLM", "HKCU", "HKCR", "HKU"]):
            return "registry"

        # Check if it's a process (ends with .exe, .dll, etc.)
        if value.endswith((".exe", ".dll", ".sys", ".bat", ".ps1", ".cmd")):
            return "process"

        # Default based on ioc_type
        type_mapping = {
            "process": "process",
            "file": "file",
            "ipv4": "network",
            "domain": "network",
            "registry": "registry",
            "port": "network",
        }
        return type_mapping.get(ioc_type, "ioc")

    def _add_or_update_node(
        self,
        nodes_dict: dict[str, dict[str, Any]],
        node_id: str,
        label: str,
        node_type: str,
        severity: str,
        properties: dict[str, Any]
    ) -> None:
        """Add new node or update existing node with deduplication."""
        if node_id in nodes_dict:
            # Update existing node
            nodes_dict[node_id]["occurrences"] += 1
            # Update severity if higher
            current_severity = nodes_dict[node_id]["severity"]
            if SEVERITY_ORDER.get(severity, 0) > SEVERITY_ORDER.get(current_severity, 0):
                nodes_dict[node_id]["severity"] = severity
            # Merge properties
            nodes_dict[node_id]["properties"].update(properties)
        else:
            # Add new node
            nodes_dict[node_id] = {
                "label": label,
                "node_type": node_type,
                "severity": severity,
                "properties": properties,
                "occurrences": 1,
            }

    def _calculate_critical_path(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> list[str]:
        """Calculate most critical attack path through graph."""
        if not nodes or not edges:
            return []

        # Build NetworkX graph for path analysis
        G = nx.DiGraph()
        for node in nodes:
            G.add_node(node.id, severity=SEVERITY_ORDER.get(node.severity, 0))
        for edge in edges:
            G.add_edge(edge.source, edge.target)

        # Find highest severity nodes
        critical_nodes = sorted(
            nodes,
            key=lambda n: SEVERITY_ORDER.get(n.severity, 0),
            reverse=True
        )[:3]  # Top 3 most critical

        # Find paths between critical nodes
        paths = []
        for i, source in enumerate(critical_nodes):
            for target in critical_nodes[i+1:]:
                try:
                    if nx.has_path(G, source.id, target.id):
                        path = nx.shortest_path(G, source.id, target.id)
                        paths.append(path)
                except nx.NetworkXNoPath:
                    continue

        # Return longest critical path
        if paths:
            return max(paths, key=len)
        elif critical_nodes:
            return [critical_nodes[0].id]
        return []

    def _calculate_severity_distribution(self, nodes: list[GraphNode]) -> dict[str, int]:
        """Calculate severity distribution across nodes."""
        distribution = defaultdict(int)
        for node in nodes:
            distribution[node.severity] += 1
        return dict(distribution)

    def _calculate_node_type_distribution(self, nodes: list[GraphNode]) -> dict[str, int]:
        """Calculate node type distribution."""
        distribution = defaultdict(int)
        for node in nodes:
            distribution[node.node_type] += 1
        return dict(distribution)
