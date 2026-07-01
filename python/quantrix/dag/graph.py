"""Reproducibility DAG — graph data structure."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
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
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    input_hash: str = ""
    output_hash: str = ""
    description: str = ""


class ProvenanceEdge(BaseModel):
    source_id: UUID
    target_id: UUID
    label: str = ""


class AnalysisDAG:
    def __init__(self):
        self.nodes: dict[UUID, ProvenanceNode] = {}
        self.edges: list[ProvenanceEdge] = []

    def add_node(self, node):
        self.nodes[node.id] = node

    def add_edge(self, source, target, label=""):
        self.edges.append(ProvenanceEdge(source_id=source, target_id=target, label=label))

    def get_downstream(self, node_id):
        downstream = set()
        stack = [node_id]
        while stack:
            cur = stack.pop()
            for e in self.edges:
                if e.source_id == cur and e.target_id not in downstream:
                    downstream.add(e.target_id)
                    stack.append(e.target_id)
        return list(downstream)

    def mark_stale(self, node_id):
        for sid in [node_id] + self.get_downstream(node_id):
            if sid in self.nodes:
                self.nodes[sid].status = NodeStatus.STALE

    def topological_order(self):
        in_deg = dict.fromkeys(self.nodes, 0)
        for e in self.edges:
            in_deg[e.target_id] = in_deg.get(e.target_id, 0) + 1
        queue = [nid for nid, d in in_deg.items() if d == 0]
        result = []
        while queue:
            nid = queue.pop(0)
            if nid in self.nodes:
                result.append(self.nodes[nid])
            for e in self.edges:
                if e.source_id == nid:
                    in_deg[e.target_id] -= 1
                    if in_deg[e.target_id] == 0:
                        queue.append(e.target_id)
        return result

    def to_dict(self):
        return {
            "nodes": [
                {
                    "id": str(n.id),
                    "kind": n.kind.value,
                    "label": n.label,
                    "status": n.status.value,
                    "method": n.method,
                    "description": n.description,
                }
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": str(e.source_id), "target": str(e.target_id), "label": e.label}
                for e in self.edges
            ],
        }

    @property
    def node_count(self):
        return len(self.nodes)
