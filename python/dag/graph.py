"""Reproducibility DAG — graph data structure and staleness tracking.

Every analysis operation is recorded as a node. Edges represent
data dependencies. When upstream changes, downstream becomes stale.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class NodeKind(StrEnum):
    IMPORT = "import"
    TRANSFORM = "transform"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    REPORT = "report"


class NodeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STALE = "stale"
    FAILED = "failed"


class ProvenanceNode(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    kind: NodeKind
    label: str
    status: NodeStatus = NodeStatus.COMPLETED

    method: str = ""
    parameters: dict[str, object] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    input_hash: str = ""
    output_hash: str = ""
    description: str = ""


class ProvenanceEdge(BaseModel):
    source_id: UUID
    target_id: UUID
    label: str = ""


class AnalysisDAG:
    """A directed acyclic graph of analysis operations.

    Supports:
    - Adding nodes and edges
    - Topological ordering
    - Staleness propagation (mark downstream nodes stale when upstream changes)
    - Export to serializable format
    """

    def __init__(self) -> None:
        self.nodes: dict[UUID, ProvenanceNode] = {}
        self.edges: list[ProvenanceEdge] = []

    def add_node(self, node: ProvenanceNode) -> UUID:
        self.nodes[node.id] = node
        return node.id

    def add_edge(self, source: UUID, target: UUID, label: str = "") -> None:
        self.edges.append(ProvenanceEdge(source_id=source, target_id=target, label=label))

    def get_downstream(self, node_id: UUID) -> list[UUID]:
        """Return all nodes downstream of the given node."""
        downstream: set[UUID] = set()
        stack = [node_id]
        while stack:
            current = stack.pop()
            for edge in self.edges:
                if edge.source_id == current and edge.target_id not in downstream:
                    downstream.add(edge.target_id)
                    stack.append(edge.target_id)
        return list(downstream)

    def mark_stale(self, node_id: UUID) -> None:
        """Mark a node and all its downstream nodes as stale."""
        stale_ids = self.get_downstream(node_id)
        stale_ids.append(node_id)
        for sid in stale_ids:
            if sid in self.nodes:
                self.nodes[sid].status = NodeStatus.STALE

    def topological_order(self) -> list[ProvenanceNode]:
        """Return nodes in topological order (imports first)."""
        in_degree: dict[UUID, int] = {nid: 0 for nid in self.nodes}
        for edge in self.edges:
            in_degree[edge.target_id] = in_degree.get(edge.target_id, 0) + 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result: list[ProvenanceNode] = []

        while queue:
            nid = queue.pop(0)
            if nid in self.nodes:
                result.append(self.nodes[nid])
            for edge in self.edges:
                if edge.source_id == nid:
                    in_degree[edge.target_id] -= 1
                    if in_degree[edge.target_id] == 0:
                        queue.append(edge.target_id)

        return result

    def to_dict(self) -> dict:
        return {
            "nodes": [
                {
                    "id": str(n.id),
                    "kind": n.kind.value,
                    "label": n.label,
                    "status": n.status.value,
                    "method": n.method,
                    "description": n.description,
                    "created_at": n.created_at.isoformat(),
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": str(e.source_id), "target": str(e.target_id), "label": e.label}
                for e in self.edges
            ],
        }

    @property
    def stale_count(self) -> int:
        return sum(1 for n in self.nodes.values() if n.status == NodeStatus.STALE)

    @property
    def node_count(self) -> int:
        return len(self.nodes)
