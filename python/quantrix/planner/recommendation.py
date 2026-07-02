"""Research planner recommendation engine.

Combines question parser + decision tree to produce ranked method
recommendations with rationale and assumptions.
"""

from __future__ import annotations

from quantrix.core.dataset import Dataset
from quantrix.core.metadata import VariableMetadata
from quantrix.planner.decision_tree import DecisionTree, MethodCandidate, ResearchGoal
from quantrix.planner.question_parser import (
    classify_question,
    extract_variable_roles,
    infer_design_from_text,
)
from quantrix.stats.registry import get_registry


def _map_question_type(qt: str) -> str:
    """Map question parser output to DecisionTree goal."""
    mapping = {
        "descriptive": ResearchGoal.DESCRIBE,
        "difference": ResearchGoal.COMPARE_GROUPS,
        "association": ResearchGoal.ASSOCIATION,
        "prediction": ResearchGoal.PREDICT,
        "causal": ResearchGoal.PREDICT,  # Causal → prediction methods
    }
    return mapping.get(qt, ResearchGoal.DESCRIBE)


class ResearchPlanner:
    """Main entry point: research question → analysis plan."""

    def __init__(self) -> None:
        self.tree = DecisionTree()

    def plan_structured(
        self,
        goal: str,
        dv_name: str | None,
        iv_names: list[str],
        dataset: Dataset,
    ) -> dict:
        """Generate a plan from explicit goal + variable selections (no NLP)."""
        goal_map = {
            "describe": ResearchGoal.DESCRIBE,
            "compare_groups": ResearchGoal.COMPARE_GROUPS,
            "find_association": ResearchGoal.ASSOCIATION,
            "predict": ResearchGoal.PREDICT,
        }
        mapped = goal_map.get(goal, ResearchGoal.DESCRIBE)
        question_map = {
            "describe": "descriptive",
            "compare_groups": "difference",
            "find_association": "association",
            "predict": "prediction",
        }

        dv = dataset.get_variable(dv_name) if dv_name else None
        ivs = [dataset.get_variable(n) for n in iv_names if n in dataset.variable_names]

        candidates = self._implemented_only(
            self.tree.recommend(goal=mapped, dependent=dv, independents=ivs)
        )

        if not candidates and dv is None:
            candidates = self._fallback(dataset, mapped)

        return {
            "question": f"{goal}: {dv_name or '?'} {'~ ' + ' + '.join(iv_names) if iv_names else ''}",
            "question_type": question_map.get(goal, "descriptive"),
            "design": "cross-sectional",
            "recommendations": self._format(candidates, dv, ivs),
        }

    def plan(self, question: str, dataset: Dataset) -> dict:
        qt = classify_question(question)
        goal = _map_question_type(qt)
        roles = extract_variable_roles(question, dataset.variable_names)
        design = infer_design_from_text(question)

        dv_name = roles.get("dependent")
        iv_names = roles.get("independent", [])

        dv = dataset.get_variable(str(dv_name)) if dv_name else None
        ivs = [dataset.get_variable(str(n)) for n in (iv_names or []) if isinstance(n, str)]

        # Get recommendations from decision tree
        candidates = self._implemented_only(
            self.tree.recommend(goal=goal, dependent=dv, independents=ivs)
        )

        # Fallback: if no variables extracted, try all variables
        if not candidates and dv is None:
            candidates = self._fallback(dataset, goal)

        return {
            "question": question,
            "question_type": qt,
            "design": design,
            "recommendations": self._format(candidates, dv, ivs),
        }

    def _fallback(self, dataset: Dataset, goal: str) -> list[MethodCandidate]:
        """Try all reasonable variable combos as fallback."""
        results: list[MethodCandidate] = []
        seen: set[str] = set()

        continuous = dataset.get_variables_by_type("continuous")
        nominal = dataset.get_variables_by_type("nominal")
        ordinal = dataset.get_variables_by_type("ordinal")
        categorical = nominal + ordinal

        # Try common patterns
        if goal in (ResearchGoal.COMPARE_GROUPS, ResearchGoal.PREDICT):
            for dv in continuous[:2]:
                for iv in categorical[:2]:
                    r = self.tree.recommend(goal=goal, dependent=dv, independents=[iv])
                    for c in self._implemented_only(r):
                        if c.method_name not in seen:
                            seen.add(c.method_name)
                            results.append(c)

        if not results:
            for var in dataset.variables[:5]:
                r = self.tree.recommend(goal=ResearchGoal.DESCRIBE, dependent=var, independents=[])
                for c in self._implemented_only(r):
                    if c.method_name not in seen:
                        seen.add(c.method_name)
                        results.append(c)

        results.sort(key=lambda c: c.confidence, reverse=True)
        return results[:5]

    @staticmethod
    def _implemented_only(candidates: list[MethodCandidate]) -> list[MethodCandidate]:
        """Keep recommendations executable by the current stats registry."""
        supported = set(get_registry())
        return [c for c in candidates if c.method_name in supported]

    @staticmethod
    def _format(
        candidates: list[MethodCandidate],
        dv: VariableMetadata | None,
        ivs: list[VariableMetadata],
    ) -> list[dict]:
        """Format MethodCandidate list for API response."""
        return [
            {
                "rank": i + 1,
                "method_name": c.method_name,
                "display_name": c.display_name,
                "method_family": c.method_family,
                "confidence": round(c.confidence, 2),
                "rationale": c.reason,
                "assumptions": c.assumptions,
                "alternative_methods": c.alternatives,
                "matched_variables": {
                    "dependent": dv.name if dv else None,
                    "independents": [v.name for v in ivs],
                },
            }
            for i, c in enumerate(candidates)
        ]
