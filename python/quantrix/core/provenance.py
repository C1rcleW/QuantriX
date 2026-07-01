"""Reproducibility DAG — provenance tracking data structures.

These are placeholders for Phase 6. The types are defined now so that
all modules can reference them without circular imports later.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class NodeKind(StrEnum):
    """Types of nodes in the analysis DAG."""

    IMPORT = "import"
    TRANSFORM = "transform"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    REPORT = "report"


class NodeStatus(StrEnum):
    """Execution status of a DAG node."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STALE = "stale"  # Upstream changed, needs re-execution
    FAILED = "failed"


class ProvenanceNode(BaseModel):
    """A single step in the analysis workflow DAG.

    Each node represents one atomic operation: import, transform, analysis, etc.
    Nodes are connected by ProvenanceEdges to form the full workflow.
    """

    id: UUID = Field(default_factory=uuid4)
    kind: NodeKind
    label: str
    status: NodeStatus = NodeStatus.PENDING

    # What was done
    method: str = ""  # e.g., "ttest_independent", "filter_rows"
    parameters: dict[str, object] = Field(default_factory=dict)

    # When
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    executed_at: datetime | None = None
    execution_time_ms: float = 0.0

    # Input/output fingerprint (for staleness detection)
    input_hash: str = ""
    output_hash: str = ""

    # Human-readable description
    description: str = ""


class ProvenanceEdge(BaseModel):
    """A directed edge between two ProvenanceNodes.

    source → target means target depends on source.
    If source changes, target becomes stale.
    """

    source_id: UUID
    target_id: UUID
    label: str = ""  # e.g., "produces variable X", "filtered by Y"
