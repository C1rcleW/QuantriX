"""Golden snapshots for Python/R/SPSS exporter output."""

from __future__ import annotations

from quantrix.dag.exporters.python import export_python
from quantrix.dag.exporters.r import export_r
from quantrix.dag.exporters.syntax import export_syntax
from quantrix.dag.graph import AnalysisDAG, NodeKind, ProvenanceNode
from tests.golden._snapshot import assert_text_snapshot
from tests.golden.data import METHOD_CASES


def _build_dag() -> AnalysisDAG:
    dag = AnalysisDAG()
    import_node = ProvenanceNode(
        kind=NodeKind.IMPORT,
        label="Import golden",
        method="import",
        parameters={"file": "golden.csv", "format": "csv"},
        description="golden (24x6) from csv",
    )
    dag.add_node(import_node)
    for case in METHOD_CASES:
        node = ProvenanceNode(
            kind=NodeKind.ANALYSIS,
            label=f"{case.method}: {case.dv}",
            method=case.method,
            parameters={"dv": case.dv, "ivs": list(case.ivs)},
            description=f"Ran {case.method}",
        )
        dag.add_node(node)
        dag.add_edge(import_node.id, node.id)
    return dag


def test_exporter_snapshots() -> None:
    dag = _build_dag()
    assert_text_snapshot(export_python(dag, "golden"), "exports.json", "python")
    assert_text_snapshot(export_r(dag, "golden"), "exports.json", "r")
    assert_text_snapshot(export_syntax(dag, "golden"), "exports.json", "syntax")
