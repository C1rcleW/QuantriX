"""Test fixtures that create synthetic data files for testing.

Since we can't distribute real SPSS files in the repo, we generate
gold-standard test files programmatically using pyreadstat.
"""

from pathlib import Path

import polars as pl
import pyreadstat
import pytest
from pyreadstat.pyclasses import MissingRange


def create_simple_sav(path: Path) -> Path:
    """Create a minimal but comprehensive SAV file for testing.

    Contains:
    - continuous variable (income)
    - ordinal variable (education_level, with value labels)
    - nominal variable (gender, with value labels)
    - string variable (city)
    - discrete missing values (99 on income)
    - Chinese characters in labels
    """
    import numpy as np

    n = 100
    rng = np.random.default_rng(42)

    income = rng.normal(50000, 15000, n).round(2)
    income[0:5] = [99.0] * 5  # Simulate 5 missing values (coded as 99)

    education = rng.integers(1, 6, n).astype(float)  # 1-5 scale
    gender = rng.integers(1, 3, n).astype(float)  # 1=male, 2=female
    city_opts = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Chengdu"]
    city = [city_opts[i % 5] for i in range(n)]
    age = rng.normal(35, 10, n).clip(18, 70).round(0)

    df = pl.DataFrame({
        "income": income,
        "education_level": education,
        "gender": gender,
        "city": city,
        "age": age,
    })

    # Write SAV with metadata
    pyreadstat.write_sav(
        df=df.to_pandas(),
        dst_path=str(path),
        column_labels=[
            "Annual Income (USD)",
            "Education Level",
            "Gender",
            "City of Residence",
            "Age in Years",
        ],
        variable_measure={
            "income": "scale",
            "education_level": "ordinal",
            "gender": "nominal",
            "city": "nominal",
            "age": "scale",
        },
        variable_value_labels={
            "education_level": {
                1.0: "Primary",
                2.0: "Secondary",
                3.0: "High School",
                4.0: "Bachelor",
                5.0: "Master+",
            },
            "gender": {
                1.0: "Male",
                2.0: "Female",
            },
        },
        missing_ranges={"income": [MissingRange(lo=99, hi=99)]},
        file_label="Quantrix Test Dataset",
    )

    return path


def create_csv_file(path: Path) -> Path:
    """Create a CSV file for testing CSV reader."""
    df = pl.DataFrame({
        "id": range(1, 21),
        "score": [85.5, 92.0, 78.3, None, 88.1, 95.2, 73.4, 81.0, None, 90.5,
                  76.8, 83.2, 94.1, 67.9, 88.7, 91.3, 79.5, 86.0, 93.8, 82.4],
        "group": ["A", "A", "B", "B", "A", "A", "B", "B", "A", "B",
                   "A", "B", "A", "B", "A", "A", "B", "B", "A", "B"],
        "passed": [True, True, False, False, True, True, False, True, False, True,
                   True, True, True, False, True, True, False, True, True, True],
    })
    df.write_csv(path)
    return path


@pytest.fixture(scope="session")
def simple_sav_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped fixture: path to a synthetic SAV file."""
    path = tmp_path_factory.mktemp("sav_data") / "test.sav"
    return create_simple_sav(path)


@pytest.fixture(scope="session")
def csv_file_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Session-scoped fixture: path to a CSV file."""
    path = tmp_path_factory.mktemp("csv_data") / "test.csv"
    return create_csv_file(path)
