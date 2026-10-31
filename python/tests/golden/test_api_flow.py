"""End-to-end contract for the current analysis pipeline."""

from __future__ import annotations

from fastapi.testclient import TestClient

from quantrix.dag.tracker import reset_tracker
from quantrix.server.app import app


def test_import_plan_execute_interpret_report_export_contract() -> None:
    reset_tracker()
    client = TestClient(app)
    csv = (
        b"score,group\n"
        b"85,A\n90,A\n78,A\n92,A\n"
        b"76,B\n82,B\n95,B\n87,B\n"
    )

    imported = client.post(
        "/api/data/import",
        files={"file": ("golden.csv", csv, "text/csv")},
    )
    assert imported.status_code == 200
    dataset_id = imported.json()["dataset_id"]

    plan = client.post(
        "/api/analysis/plan-structured",
        json={
            "dataset_id": dataset_id,
            "goal": "compare_groups",
            "dependent": "score",
            "independents": ["group"],
        },
    )
    assert plan.status_code == 200
    recommendations = plan.json()["recommendations"]
    assert recommendations
    recommendation = recommendations[0]
    assert recommendation["method_name"] == "independent_ttest"

    method = recommendation["method_name"]
    dependent = recommendation["matched_variables"]["dependent"]
    independents = recommendation["matched_variables"]["independents"]

    safety = client.post(
        "/api/safety/check",
        json={
            "dataset_id": dataset_id,
            "method_name": method,
            "dependent": dependent,
            "independents": independents,
        },
    )
    assert safety.status_code == 200
    assert safety.json()["has_errors"] is False

    executed = client.post(
        "/api/analysis/execute",
        json={
            "dataset_id": dataset_id,
            "method_name": method,
            "dependent": dependent,
            "independents": independents,
        },
    )
    assert executed.status_code == 200
    result = executed.json()
    assert result["errors"] == []
    assert result["charts"]

    statistics = {
        "dv_label": result["dv_label"],
        "iv_label": result["iv_label"],
        "group_labels": result["group_labels"],
        **result["statistics"],
        **result["misc"],
        "cohens_d": result["effect_sizes"]["cohens_d"],
        "sig_text": result["sig_text"],
        "effect_size_text": result["effect_size_text"],
    }
    interpreted = client.post(
        "/api/chat/interpret",
        json={"method_name": method, "statistics": statistics},
    )
    assert interpreted.status_code == 200
    interpretation = interpreted.json()
    assert interpretation["summary"]
    assert interpretation["detailed"]
    assert "Template error" not in interpretation["detailed"]

    report = client.post(
        "/api/report/generate",
        json={
            "title": "Golden Pipeline",
            "sections": [
                {
                    "heading": method,
                    "interpretation": interpretation["detailed"],
                }
            ],
        },
    )
    assert report.status_code == 200
    assert "## Results" in report.json()["markdown"]
    assert report.json()["html"]

    exported = client.post(
        "/api/dag/export",
        json={"language": "python", "dataset_name": "golden"},
    )
    assert exported.status_code == 200
    assert "stats.ttest_ind" in exported.json()["code"]
