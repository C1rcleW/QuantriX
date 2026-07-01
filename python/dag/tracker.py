"""Runtime tracker — records analysis operations as DAG nodes.

Integrates with the dataset registry to record each import and
analysis step as a provenance node in the DAG.
"""

from __future__ import annotations

from quantrix.core.dataset import Dataset
from quantrix.dag.graph import AnalysisDAG, NodeKind, ProvenanceNode


class OperationTracker:
    """Tracks analysis operations and builds a reproducibility DAG.

    Usage:
        tracker = OperationTracker()
        tracker.record_import(dataset, file_path)
        tracker.record_analysis("independent_ttest", {"dv": "income", "iv": "gender"},
                                depends_on=import_node_id)
        dag = tracker.dag
        print(dag.to_dict())
    """

    def __init__(self) -> None:
        self.dag = AnalysisDAG()

    def record_import(self, dataset: Dataset, file_path: str) -> str:
        """Record a data import operation."""
        node = ProvenanceNode(
            kind=NodeKind.IMPORT,
            label=f"Import: {dataset.name}",
            method="import",
            parameters={"file": file_path, "format": dataset.source_format},
            description=f"Imported {dataset.name} ({dataset.n_rows}×{dataset.n_columns}) from {dataset.source_format}",
        )
        self.dag.add_node(node)
        return str(node.id)

    def record_analysis(
        self,
        method_name: str,
        params: dict,
        depends_on: str | list[str] | None = None,
        label: str = "",
    ) -> str:
        """Record an analysis operation.

        Args:
            method_name: e.g., "independent_ttest"
            params: Analysis parameters (dv, iv, etc.)
            depends_on: Node ID(s) this analysis depends on.
            label: Human-readable label.
        """
        node = ProvenanceNode(
            kind=NodeKind.ANALYSIS,
            label=label or f"Analysis: {method_name}",
            method=method_name,
            parameters=params,
            description=f"Ran {method_name} with {params}",
        )
        self.dag.add_node(node)

        # Connect dependencies
        if depends_on:
            deps = depends_on if isinstance(depends_on, list) else [depends_on]
            from uuid import UUID

            for dep_id in deps:
                self.dag.add_edge(UUID(dep_id), node.id, "depends_on")

        return str(node.id)

    def record_transform(
        self,
        transform_name: str,
        params: dict,
        depends_on: str | list[str] | None = None,
    ) -> str:
        """Record a data transformation."""
        node = ProvenanceNode(
            kind=NodeKind.TRANSFORM,
            label=f"Transform: {transform_name}",
            method=transform_name,
            parameters=params,
            description=f"Applied {transform_name} with {params}",
        )
        self.dag.add_node(node)

        if depends_on:
            deps = depends_on if isinstance(depends_on, list) else [depends_on]
            from uuid import UUID

            for dep_id in deps:
                self.dag.add_edge(UUID(dep_id), node.id, "depends_on")

        return str(node.id)


# ── Global tracker (one per session) ──

_tracker: OperationTracker | None = None


def get_tracker() -> OperationTracker:
    global _tracker
    if _tracker is None:
        _tracker = OperationTracker()
    return _tracker


def reset_tracker() -> None:
    global _tracker
    _tracker = OperationTracker()
