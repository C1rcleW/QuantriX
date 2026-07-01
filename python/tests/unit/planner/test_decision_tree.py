"""Tests for the DecisionTree."""

import pytest

from quantrix.core.metadata import VariableMetadata
from quantrix.core.types import VariableType
from quantrix.planner.decision_tree import DecisionTree, MethodCandidate, ResearchGoal


class TestDecisionTree:
    """Method selection logic tests."""

    @pytest.fixture
    def tree(self):
        return DecisionTree()

    # ── Descriptive ──

    def test_descriptive_continuous(self, tree):
        dv = VariableMetadata(name="income", variable_type=VariableType.CONTINUOUS)
        recs = tree.recommend(ResearchGoal.DESCRIBE, dv, [])
        assert len(recs) >= 1
        names = [r.method_name for r in recs]
        assert "descriptives" in names

    def test_descriptive_nominal(self, tree):
        dv = VariableMetadata(name="gender", variable_type=VariableType.NOMINAL)
        recs = tree.recommend(ResearchGoal.DESCRIBE, dv, [])
        names = [r.method_name for r in recs]
        assert "frequencies" in names

    # ── Compare groups ──

    def test_compare_continuous_by_nominal(self, tree):
        dv = VariableMetadata(name="income", variable_type=VariableType.CONTINUOUS)
        iv = VariableMetadata(name="gender", variable_type=VariableType.NOMINAL)
        recs = tree.recommend(ResearchGoal.COMPARE_GROUPS, dv, [iv])
        names = [r.method_name for r in recs]
        assert "independent_ttest" in names

    def test_compare_many_groups(self, tree):
        dv = VariableMetadata(name="score", variable_type=VariableType.CONTINUOUS)
        iv = VariableMetadata(name="education", variable_type=VariableType.ORDINAL, n_unique=5)
        recs = tree.recommend(ResearchGoal.COMPARE_GROUPS, dv, [iv])
        names = [r.method_name for r in recs]
        assert "oneway_anova" in names

    def test_compare_with_nonparametric(self, tree):
        dv = VariableMetadata(name="satisfaction", variable_type=VariableType.ORDINAL)
        iv = VariableMetadata(name="gender", variable_type=VariableType.NOMINAL)
        recs = tree.recommend(ResearchGoal.COMPARE_GROUPS, dv, [iv])
        names = [r.method_name for r in recs]
        assert "mann_whitney" in names

    # ── Association ──

    def test_association_continuous(self, tree):
        dv = VariableMetadata(name="income", variable_type=VariableType.CONTINUOUS)
        iv = VariableMetadata(name="education_years", variable_type=VariableType.CONTINUOUS)
        recs = tree.recommend(ResearchGoal.ASSOCIATION, dv, [iv])
        names = [r.method_name for r in recs]
        assert "pearson_correlation" in names

    def test_association_nominal(self, tree):
        dv = VariableMetadata(name="gender", variable_type=VariableType.NOMINAL)
        iv = VariableMetadata(name="region", variable_type=VariableType.NOMINAL)
        recs = tree.recommend(ResearchGoal.ASSOCIATION, dv, [iv])
        names = [r.method_name for r in recs]
        assert "chi_square" in names

    # ── Prediction ──

    def test_prediction_continuous(self, tree):
        dv = VariableMetadata(name="income", variable_type=VariableType.CONTINUOUS)
        iv1 = VariableMetadata(name="education_years", variable_type=VariableType.CONTINUOUS)
        iv2 = VariableMetadata(name="age", variable_type=VariableType.CONTINUOUS)
        recs = tree.recommend(ResearchGoal.PREDICT, dv, [iv1, iv2])
        names = [r.method_name for r in recs]
        assert "linear_regression" in names

    def test_prediction_binary(self, tree):
        dv = VariableMetadata(name="passed", variable_type=VariableType.NOMINAL, n_unique=2)
        iv = VariableMetadata(name="score", variable_type=VariableType.CONTINUOUS)
        recs = tree.recommend(ResearchGoal.PREDICT, dv, [iv])
        names = [r.method_name for r in recs]
        assert "binary_logistic" in names

    # ── Edge cases ──

    def test_empty_recommendations(self, tree):
        recs = tree.recommend(ResearchGoal.DESCRIBE, None, [])
        assert recs == []

    # ── Alternatives ──

    def test_alternatives_for_ttest(self, tree):
        dv = VariableMetadata(name="income", variable_type=VariableType.CONTINUOUS)
        iv = VariableMetadata(name="gender", variable_type=VariableType.NOMINAL)
        recs = tree.recommend(ResearchGoal.COMPARE_GROUPS, dv, [iv])
        primary = recs[0]
        assert len(primary.alternatives) > 0

    def test_confidence_scores(self, tree):
        dv = VariableMetadata(name="income", variable_type=VariableType.CONTINUOUS)
        iv = VariableMetadata(name="gender", variable_type=VariableType.NOMINAL)
        recs = tree.recommend(ResearchGoal.COMPARE_GROUPS, dv, [iv])
        for r in recs:
            assert isinstance(r, MethodCandidate)
            assert 0 <= r.confidence <= 1
            assert len(r.assumptions) > 0
