"""Tests for the question parser."""

from quantrix.planner.question_parser import (
    classify_question,
    extract_variable_roles,
    infer_design_from_text,
)


class TestClassifyQuestion:
    def test_descriptive(self):
        assert classify_question("What is the distribution of income?") == "descriptive"
        assert classify_question("Describe the demographics.") == "descriptive"

    def test_difference(self):
        assert (
            classify_question("Is there a difference in income between men and women?")
            == "difference"
        )
        assert classify_question("Compare scores across groups.") == "difference"

    def test_association(self):
        assert classify_question("Is income correlated with education?") == "association"
        assert classify_question("What is the relationship between X and Y?") == "association"

    def test_prediction(self):
        assert classify_question("What factors predict income?") == "prediction"
        assert classify_question("How does education affect income?") == "prediction"

    def test_causal(self):
        assert classify_question("What is the causal effect of the treatment?") == "causal"

    def test_chinese(self):
        assert classify_question("性别对收入有什么影响？") == "prediction"
        assert classify_question("不同组之间有显著差异吗？") == "difference"

    def test_default_fallback(self):
        assert classify_question("hello world") == "descriptive"


class TestExtractVariableRoles:
    def test_basic_extraction(self):
        roles = extract_variable_roles(
            "Does gender affect income?",
            ["income", "gender", "age", "education"],
        )
        assert roles["dependent"] == "income"
        assert "gender" in roles["independent"]

    def test_no_variables_mentioned(self):
        roles = extract_variable_roles("hello world", ["a", "b", "c"])
        assert roles["dependent"] is None
        assert roles["independent"] == []

    def test_single_variable(self):
        roles = extract_variable_roles("Describe income", ["income"])
        # Single var with "describe" → likely dependent
        assert roles["dependent"] is None  # No clear DV keyword
        assert "income" in roles["independent"]


class TestInferDesign:
    def test_default_cross_sectional(self):
        assert infer_design_from_text("What is the average income?") == "cross_sectional"

    def test_longitudinal(self):
        assert infer_design_from_text("How does income change over time?") == "longitudinal"

    def test_experimental(self):
        assert (
            infer_design_from_text("What is the effect of the randomized treatment?")
            == "experimental"
        )
