<p align="right">
  <a href="README.md"><img src="https://img.shields.io/badge/English-README-1f6feb?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87-README-d73a49?style=for-the-badge" alt="中文"></a>
</p>

# Quantrix v0.1.0

**A quantitative research platform for the social sciences**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![CI](https://github.com/C1rcleW/QuantriX/actions/workflows/ci.yml/badge.svg)](https://github.com/C1rcleW/QuantriX/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)]()

Quantrix turns a dataset into a guided analysis: import data, choose a research goal and variables, run a statistical method, check assumptions, read an interpretation, and generate a report. The core analysis is deterministic and does not require an LLM.

> Pre-alpha. The main analysis workflow works end-to-end; the GUI is functional but still rough.

---

## What it does

- Imports CSV, TSV, TXT, and SPSS SAV/ZSAV files.
- Detects variable types, missing values, and basic distributions.
- Supports two ways to ask a question: **Guided** (goal + variable dropdowns) or **Free Text** (keyword-based question parsing).
- Runs 10 statistical methods and renders the corresponding charts in the browser.
- Checks statistical assumptions before execution. Errors block the analysis; warnings are shown to the user.
- Produces a template-based interpretation and a Markdown/HTML report for the current analysis.
- Tracks imports and analyses in a provenance graph. Python/R/SPSS code export is available through the API.

## Analysis modes

**Guided (recommended)** — choose one of four goals:

| Goal | Example |
|---|---|
| Describe | Summarize the distribution of a variable |
| Compare Groups | Compare a continuous outcome across groups |
| Find Association | Measure the relationship between two variables |
| Predict | Model a continuous outcome from one or more predictors |

**Free Text** — type a question such as “Does education affect income?”. The parser is keyword-based; Guided mode is more reliable for complex designs.

If a statistically appropriate method is not implemented, the planner shows an explicit note with the closest available alternatives instead of silently returning nothing.

## Statistical methods

| Method | Use | Chart |
|---|---|---|
| Descriptive Statistics | Mean, SD, median, quartiles, range | Histogram |
| Frequency Analysis | Counts and percentages for categories | Bar chart |
| Independent Samples t-test | Compare a continuous outcome between 2 groups | Box plot + grouped bar |
| One-Way ANOVA | Compare a continuous outcome across 3+ groups | Box plot + grouped bar |
| Mann-Whitney U | Nonparametric comparison of 2 groups | Box plot |
| Kruskal-Wallis H | Nonparametric comparison of 3+ groups | Box plot |
| Pearson Correlation | Linear association between two continuous variables | Scatter + fitted line |
| Spearman Correlation | Monotonic association | Scatter |
| Chi-Square Test | Association between categorical variables | Bar chart |
| Linear Regression | Continuous outcome prediction | Scatter/line, box, or fitted-vs-observed depending on predictors |

Linear regression supports categorical predictors through dummy coding, and the engine supports multiple predictors. The guided UI currently selects one dependent and one independent variable.

## Safety, interpretation, and reporting

- Six checks run before an analysis: variable-type compatibility, sample size, normality (skewness/kurtosis heuristic), homogeneity of variance (SD ratio heuristic), outliers (IQR), and multiple-comparison reminders.
- Safety errors block execution; warnings are advisory.
- Interpretations are generated from deterministic templates for all 10 methods.
- Reports are generated for the current analysis as Markdown and HTML; the GUI currently opens the Markdown version.

## Current limitations

- Free-text parsing is keyword-based; use Guided mode for complex questions.
- No post-hoc tests, eta-squared, logistic regression, or crosstabulation. The planner explains these gaps when relevant.
- SPSS value labels are loaded, but result tables and charts currently show raw values.
- Reports cover the current analysis only; there is no multi-analysis document or chart embedding.
- The GUI does not yet expose the provenance graph or code export; these are available through the API.
- The guided UI selects one independent variable; multiple-predictor regression is available through the API.
- Datasets are held in memory for the current server process; there are no user accounts or multi-user support.
- The core is deterministic and does not include an LLM or agent layer.
- No dark mode, mobile layout, or desktop packaging.

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for the frontend)

### Backend

```bash
git clone https://github.com/C1rcleW/QuantriX.git
cd QuantriX/python

pip install -e ".[dev,stats]"
python -m uvicorn quantrix.server.app:app --host 127.0.0.1 --port 8532
```

### Frontend

```bash
cd QuantriX/frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173` in a browser. API documentation is available at `http://127.0.0.1:8532/docs`.

Run the backend test suite with:

```bash
cd QuantriX/python
pytest
```

### How to use

1. Open the **Data** tab and import a CSV or SAV file.
2. Open **Analysis**, choose Guided or Free Text, and select a goal and variables.
3. Click a recommended method to run the safety check and analysis.
4. Review the tables, charts, and warnings.
5. Click **Explain Results** for a written interpretation, then **Report** for a Markdown report.

---

## API

The backend exposes a compact HTTP API; the full schema is at `/docs`.

- `POST /api/data/import` — upload a CSV/SAV file.
- `GET /api/data/{id}`, `/variables`, `/profile`, `/table` — inspect the dataset.
- `POST /api/analysis/plan`, `/plan-structured` — get method recommendations.
- `POST /api/analysis/execute` — run a method after the safety gate.
- `POST /api/safety/check` — inspect assumptions and warnings.
- `POST /api/chat/interpret` — generate a template-based interpretation.
- `POST /api/report/generate` — render Markdown and HTML.
- `GET /api/dag`, `POST /api/dag/export` — inspect provenance and export Python/R/SPSS code.

---

## Design

- **Statistics first** — methods are computed with Polars, SciPy, and statsmodels; results are deterministic.
- **Template before LLM** — interpretations come from explicit templates, not generated prose.
- **Provenance by default** — imports and analyses are recorded; code export is available through the API.

---

## License

GNU Affero General Public License v3.0 — see [LICENSE](./LICENSE).

## Citation

```bibtex
@software{quantrix2026,
  author = {Quantrix Contributors},
  title = {Quantrix: A Quantitative Research Platform for the Social Sciences},
  year = {2026},
  version = {0.1.0},
  url = {https://github.com/C1rcleW/QuantriX}
}
```

<p align="right"><a href="README.zh-CN.md">中文版 →</a></p>
