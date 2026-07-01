# QuantriX

**AI-Native Quantitative Research Platform for Social Sciences**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Tests](https://img.shields.io/badge/tests-159%20passed-green)]()
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)]()

Quantrix is an open-source academic infrastructure for social science research. From data to paper, one straight line.

> ⚠️ **Pre-alpha.** Core pipeline works end-to-end. GUI is functional but rough. See [Current Status](#current-status).

---

## Why Quantrix?

Social science researchers face three barriers:

1. **Statistical anxiety** — knowing *which* method to use, not *how* to click
2. **Repetitive workflows** — hundreds of menu clicks in SPSS for every paper
3. **Reproducibility gaps** — copy-paste from SPSS output to Word, lose the trail

Quantrix replaces that with: **drag in data → describe your question → get results with interpretation → export reproducible code**.

---

## What It Does

```
CSV/SAV → Auto-detect types → Ask a question → Get method recommendation → Run analysis → Safety check → Interpretation → Report → Export Python/R/SPSS
```

| Step | Example |
|------|---------|
| Import | Drag `iris.csv` → auto-detects 4 continuous + 1 nominal variable |
| Ask | "Does SepalLength differ by Species?" |
| Plan | Recommends One-Way ANOVA (95% confidence) + Kruskal-Wallis as alternative |
| Execute | F(2,147) = 119.26, p < .001 |
| Safety | Checks normality, homogeneity, sample size, outliers |
| Interpret | "The comparison of SepalLength across groups of Species was statistically significant." |
| Report | One-click APA-format markdown report |
| Export | `python`, `r`, or `spss syntax` reproduction code |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Frontend (React + TypeScript)           │
│         Data Mode · Analysis Mode · Report Mode      │
├─────────────────────────────────────────────────────┤
│              HTTP API (FastAPI, 13 endpoints)        │
├──────────┬──────────┬──────────┬────────────────────┤
│ Research │ Safety   │ Result   │ Reproducibility    │
│ Planner  │ Net      │ Interp.  │ DAG + Export       │
├──────────┴──────────┴──────────┴────────────────────┤
│              Statistics Engine (10 methods)          │
│    scipy + statsmodels + polars                     │
├─────────────────────────────────────────────────────┤
│         Data Layer (SAV/CSV → Polars + Metadata)    │
└─────────────────────────────────────────────────────┘
```

---

## Current Status (v0.1.0)

### ✅ Working (end-to-end)

| Component | Status |
|-----------|--------|
| Data import (CSV, SAV) + auto-type detection | ✅ |
| Research question → method recommendation (15 paths) | ✅ |
| Statistical Safety Net (6 rule types) | ✅ |
| Statistics engine (10 methods — see below) | ✅ |
| Result interpretation (9 method templates) | ✅ |
| APA report generation (Markdown + HTML) | ✅ |
| Reproducibility DAG (Python/R/SPSS export) | ✅ |
| Web GUI (Data + Analysis + Report tabs) | ✅ |

### ✅ Statistics Methods

| Method | scipy/statsmodels |
|--------|-------------------|
| Descriptive Statistics | `polars` |
| Frequency Analysis | `polars` |
| Independent Samples t-test | `scipy.stats.ttest_ind` |
| One-Way ANOVA | `scipy.stats.f_oneway` |
| Mann-Whitney U | `scipy.stats.mannwhitneyu` |
| Kruskal-Wallis H | `scipy.stats.kruskal` |
| Pearson Correlation | `scipy.stats.pearsonr` |
| Spearman Correlation | `scipy.stats.spearmanr` |
| Chi-Square Test | `scipy.stats.chi2_contingency` |
| Linear Regression | `statsmodels.OLS` |

### ⚠️ Known Limitations

- **Question parser is keyword-based**, not LLM. Works for simple patterns ("does X differ by Y"), fails on complex phrasing.
- **Type detector** may misclassify small datasets (< 20 rows).
- **ANOVA effect size (η²)** is not yet computed.
- **No post-hoc tests** (Tukey HSD) — only flagged as a recommendation.
- **GUI Analysis Mode** works but error messages could be clearer.
- **No dark mode**, no mobile support.
- **No Electron packaging** — runs as local dev server only.

### ❌ Not Yet Built

- Structural Equation Modeling (SEM)
- Multilevel Modeling (HLM/MLM)
- Factor Analysis (EFA/CFA)
- Time Series
- Bayesian Statistics
- Visualization engine (charts)
- Plugin system
- Team collaboration

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- Git

### Backend

```bash
git clone https://github.com/quantrix/quantrix.git
cd quantrix/python

# Install
pip install -e ".[dev,stats]"

# Verify
pytest                          # 159 tests, should all pass

# Start backend
quantrix dev                    # http://127.0.0.1:8532
# or: python -m uvicorn quantrix.server.app:app --host 127.0.0.1 --port 8532
```

### Frontend

```bash
cd quantrix/frontend
npm install
npm run dev                     # http://127.0.0.1:5173
```

### Usage

1. Open `http://127.0.0.1:5173`
2. **Data tab** — drag a CSV or SPSS `.sav` file
3. **Analysis tab** — type a research question (e.g., "Does education affect income?")
4. Click **Ask** → see method recommendations → click a method → see results
5. Click **Explain Results** → read natural-language interpretation
6. **Report tab** — export as Markdown report

---

## API Endpoints

```
POST /api/data/import           # Upload CSV/SAV → parsed dataset
GET  /api/data/{id}/variables   # Variable metadata with types
GET  /api/data/{id}/profile     # Data quality profile
POST /api/analysis/plan         # Research question → method recommendations
POST /api/analysis/execute      # Run a statistical analysis
POST /api/safety/check          # Check assumptions before analysis
POST /api/chat/interpret        # Natural-language interpretation of results
POST /api/report/generate       # Generate APA-format report
GET  /api/dag                   # View analysis provenance graph
POST /api/dag/export            # Export Python/R/SPSS reproducible code
```

API docs: `http://127.0.0.1:8532/docs`

---

## Project Structure

```
quantrix/
├── python/
│   ├── quantrix/
│   │   ├── core/           # Dataset, VariableMetadata, Protocols
│   │   ├── data/           # Readers (SAV/CSV), TypeDetector, MissingDetector, Profile
│   │   ├── stats/          # Statistical methods (10 implementations)
│   │   ├── safety/         # Statistical Safety Net (6 rules)
│   │   ├── planner/        # Research question parser + decision tree
│   │   ├── interpreter/    # Result interpretation templates + engine
│   │   ├── report/         # Report generator (Markdown + HTML)
│   │   ├── dag/            # Provenance tracking + code exporters
│   │   └── server/         # FastAPI application + 13 routes
│   └── tests/              # 159 tests (pytest)
├── frontend/
│   └── src/                # React + TypeScript GUI
├── LICENSE                 # AGPL-3.0
└── README.md
```

Lines of code: **~9,000** (Python 8,000 + TypeScript 1,000)

---

## Development

```bash
cd python
pip install -e ".[dev,stats]"   # Install with dev dependencies
pytest                           # Run 159 tests
ruff check quantrix/ tests/      # Lint
```

### Running a single test

```bash
pytest tests/integration/test_stats_engine.py -v
```

### Adding a new statistical method

1. Create a class in `stats/` that extends `BaseStatMethod`
2. Implement `execute(dataset, dv, ivs, **params) → StatResult`
3. Register in `stats/registry.py`
4. Add an interpretation template in `interpreter/template_registry.py`
5. Add decision tree path in `planner/decision_tree.py` (optional)

---

## Contributing

Quantrix is an academic open-source project. Contributions are welcome.

- **Bug reports**: Open an issue with the dataset and question that triggered it
- **New statistical methods**: See [Adding a new statistical method](#adding-a-new-statistical-method)
- **GUI improvements**: The React frontend needs love — better error handling, visualization, variable drag-and-drop
- **Documentation**: Tutorials, method references, statistical best-practice guides

### Design Principles

1. **Statistics first.** Every method must produce results verifiable against SPSS/R/scipy.
2. **Researcher workflow.** Features are prioritized by what a social scientist actually does in a day.
3. **Template before LLM.** Core interpretation is deterministic; LLM is optional polish.
4. **Reproducible by default.** Every analysis step is tracked in the DAG.

---

## License

GNU Affero General Public License v3.0 — see [LICENSE](./LICENSE).

Free for academic use. Modifications must be shared under the same license.

---

## Citation

```bibtex
@software{quantrix2026,
  author = {Quantrix Contributors},
  title = {Quantrix: AI-Native Quantitative Research Platform for Social Sciences},
  year = {2026},
  version = {0.1.0},
  url = {https://github.com/quantrix/quantrix}
}
```
