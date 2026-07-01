"""Runtime tracker for reproducibility DAG."""

from __future__ import annotations

from uuid import UUID

from quantrix.dag.graph import AnalysisDAG, NodeKind, ProvenanceNode


class OperationTracker:
    def __init__(self):
        self.dag = AnalysisDAG()

    def record_import(self, dataset, file_path):
        node = ProvenanceNode(
            kind=NodeKind.IMPORT,
            label=f"Import {dataset.name}",
            method="import",
            parameters={"file": file_path, "format": dataset.source_format},
            description=f"{dataset.name} ({dataset.n_rows}x{dataset.n_columns}) from {dataset.source_format}",
        )
        self.dag.add_node(node)
        return str(node.id)

    def record_analysis(self, method_name, params, depends_on=None, label=""):
        node = ProvenanceNode(
            kind=NodeKind.ANALYSIS,
            label=label or method_name,
            method=method_name,
            parameters=params,
            description=f"Ran {method_name}",
        )
        self.dag.add_node(node)
        if depends_on:
            deps = depends_on if isinstance(depends_on, list) else [depends_on]
            for dep_id in deps:
                self.dag.add_edge(UUID(dep_id), node.id, "depends_on")
        return str(node.id)

    def record_transform(self, transform_name, params, depends_on=None):
        node = ProvenanceNode(
            kind=NodeKind.TRANSFORM,
            label=transform_name,
            method=transform_name,
            parameters=params,
            description=f"Applied {transform_name}",
        )
        self.dag.add_node(node)
        if depends_on:
            deps = depends_on if isinstance(depends_on, list) else [depends_on]
            for dep_id in deps:
                self.dag.add_edge(UUID(dep_id), node.id, "depends_on")
        return str(node.id)


_tracker = None


def get_tracker():
    global _tracker
    if _tracker is None:
        _tracker = OperationTracker()
    return _tracker


def reset_tracker():
    global _tracker
    _tracker = OperationTracker()
