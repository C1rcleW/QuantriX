"""Tests for the DAG, tracker, and exporters."""

import pytest

from quantrix.dag.exporters.python import export_python
from quantrix.dag.exporters.r import export_r
from quantrix.dag.exporters.syntax import export_syntax
from quantrix.dag.graph import AnalysisDAG, NodeKind, NodeStatus, ProvenanceNode
from quantrix.dag.tracker import OperationTracker, reset_tracker


class TestDAG:
    @pytest.fixture
    def dag(self):
        return AnalysisDAG()

    def test_add_node(self, dag):
        node = ProvenanceNode(kind=NodeKind.IMPORT, label="Import data")
        dag.add_node(node)
        assert dag.node_count == 1

    def test_add_edge(self, dag):
        n1 = ProvenanceNode(kind=NodeKind.IMPORT, label="Import")
        n2 = ProvenanceNode(kind=NodeKind.ANALYSIS, label="ttest")
        dag.add_node(n1)
        dag.add_node(n2)
        dag.add_edge(n1.id, n2.id)
        assert len(dag.edges) == 1

    def test_mark_stale_propagates(self, dag):
        n1 = ProvenanceNode(kind=NodeKind.IMPORT, label="Import")
        n2 = ProvenanceNode(kind=NodeKind.ANALYSIS, label="ttest")
        n3 = ProvenanceNode(kind=NodeKind.REPORT, label="Report")
        dag.add_node(n1)
        dag.add_node(n2)
        dag.add_node(n3)
        dag.add_edge(n1.id, n2.id)
        dag.add_edge(n2.id, n3.id)

        dag.mark_stale(n1.id)
        assert dag.nodes[n1.id].status == NodeStatus.STALE
        assert dag.nodes[n2.id].status == NodeStatus.STALE
        assert dag.nodes[n3.id].status == NodeStatus.STALE

    def test_topological_order(self, dag):
        n1 = ProvenanceNode(kind=NodeKind.IMPORT, label="Import")
        n2 = ProvenanceNode(kind=NodeKind.ANALYSIS, label="ttest")
        dag.add_node(n1)
        dag.add_node(n2)
        dag.add_edge(n1.id, n2.id)

        order = dag.topological_order()
        assert order[0].kind == NodeKind.IMPORT
        assert order[1].kind == NodeKind.ANALYSIS

    def test_to_dict(self, dag):
        node = ProvenanceNode(kind=NodeKind.IMPORT, label="Import")
        dag.add_node(node)
        d = dag.to_dict()
        assert len(d["nodes"]) == 1
        assert d["nodes"][0]["kind"] == "import"


class TestTracker:
    def test_track_import_and_analysis(self):
        reset_tracker()
        from quantrix.dag.tracker import get_tracker

        tracker = get_tracker()

        import_id = tracker.record_import(
            type(
                "DS", (), {"name": "test", "n_rows": 100, "n_columns": 5, "source_format": "csv"}
            )(),
            "test.csv",
        )
        tracker.record_analysis(
            "independent_ttest",
            {"dv": "income", "iv": "gender"},
            depends_on=import_id,
        )

        assert tracker.dag.node_count >= 2
        d = tracker.dag.to_dict()
        kinds = [n["kind"] for n in d["nodes"]]
        assert "import" in kinds
        assert "analysis" in kinds


class TestPythonExporter:
    @pytest.fixture
    def dag(self):
        dag = AnalysisDAG()
        tracker = OperationTracker()
        tracker.dag = dag  # hack to use the tracker with our dag
        import_id = tracker.record_import(
            type(
                "DS", (), {"name": "test", "n_rows": 100, "n_columns": 3, "source_format": "csv"}
            )(),
            "test.csv",
        )
        tracker.record_analysis(
            "independent_ttest", {"dv": "income", "iv": "gender"}, depends_on=import_id
        )
        return dag

    def test_python_export_contains_scipy(self, dag):
        code = export_python(dag)
        assert "import polars as pl" in code
        assert "from scipy import stats" in code
        assert "stats.ttest_ind" in code

    def test_r_export(self, dag):
        code = export_r(dag)
        assert "t.test" in code

    def test_syntax_export(self, dag):
        code = export_syntax(dag)
        assert "T-TEST" in code


class TestDAGAPI:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from quantrix.server.app import app

        return TestClient(app)

    def test_get_dag(self, client):
        r = client.get("/api/dag")
        assert r.status_code == 200
        data = r.json()
        assert "nodes" in data
        assert "edges" in data

    def test_export_python(self, client):
        r = client.post("/api/dag/export", json={"language": "python"})
        assert r.status_code == 200
        data = r.json()
        assert data["language"] == "python"
        assert len(data["code"]) > 0

    def test_export_r(self, client):
        r = client.post("/api/dag/export", json={"language": "r"})
        assert r.status_code == 200
        assert r.json()["language"] == "r"

    def test_export_syntax(self, client):
        r = client.post("/api/dag/export", json={"language": "syntax"})
        assert r.status_code == 200
        assert r.json()["language"] == "syntax"
