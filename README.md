# Quantrix v0.1.0

**A quantitative research platform for the social sciences**
**面向社会科学研究的定量分析平台**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![CI](https://github.com/C1rcleW/QuantriX/actions/workflows/ci.yml/badge.svg)](https://github.com/C1rcleW/QuantriX/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)]()

Quantrix turns a dataset into a guided analysis: import data, choose a research goal and variables, run a statistical method, check assumptions, read an interpretation, and generate a report. The core analysis is deterministic and does not require an LLM.

> Pre-alpha. The main analysis workflow works end-to-end; the GUI is functional but still rough.
> 预发布阶段。核心分析流程端到端可用；GUI 功能可用，但仍较粗糙。

---

## English

### What it does

- Imports CSV, TSV, TXT, and SPSS SAV/ZSAV files.
- Detects variable types, missing values, and basic distributions.
- Supports two ways to ask a question: **Guided** (goal + variable dropdowns) or **Free Text** (keyword-based question parsing).
- Runs 10 statistical methods and renders the corresponding charts in the browser.
- Checks statistical assumptions before execution. Errors block the analysis; warnings are shown to the user.
- Produces a template-based interpretation and a Markdown/HTML report for the current analysis.
- Tracks imports and analyses in a provenance graph. Python/R/SPSS code export is available through the API.

### Analysis modes

**Guided (recommended)** — choose one of four goals:

| Goal | Example |
|---|---|
| Describe | Summarize the distribution of a variable |
| Compare Groups | Compare a continuous outcome across groups |
| Find Association | Measure the relationship between two variables |
| Predict | Model a continuous outcome from one or more predictors |

**Free Text** — type a question such as “Does education affect income?”. The parser is keyword-based; Guided mode is more reliable for complex designs.

If a statistically appropriate method is not implemented, the planner shows an explicit note with the closest available alternatives instead of silently returning nothing.

### Statistical methods

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

### Safety, interpretation, and reporting

- Six checks run before an analysis: variable-type compatibility, sample size, normality (skewness/kurtosis heuristic), homogeneity of variance (SD ratio heuristic), outliers (IQR), and multiple-comparison reminders.
- Safety errors block execution; warnings are advisory.
- Interpretations are generated from deterministic templates for all 10 methods.
- Reports are generated for the current analysis as Markdown and HTML; the GUI currently opens the Markdown version.

### Current limitations

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

## 中文

### 能做什么

- 导入 CSV、TSV、TXT 和 SPSS SAV/ZSAV 文件。
- 自动识别变量类型、缺失值和基本分布。
- 两种提问方式：**引导模式**（选择目标 + 下拉框选择变量）或 **自由文本**（基于关键词的问题解析）。
- 运行 10 种统计方法，并在浏览器中绘制对应图表。
- 执行前进行统计假设检查：error 会阻断分析，warning 会提示给研究者。
- 生成基于模板的结果解读，以及当前分析的 Markdown/HTML 报告。
- 在溯源图中记录导入与分析步骤；可通过 API 导出 Python/R/SPSS 复现代码。

### 两种分析模式

**引导模式（推荐）**——四种研究目标：

| 目标 | 示例 |
|---|---|
| 描述 | 概括一个变量的分布 |
| 比较组间差异 | 比较连续变量在不同组之间的差异 |
| 查找关联 | 衡量两个变量之间的关系 |
| 预测 | 用一个或多个预测变量建模连续结果 |

**自由文本模式**——输入“教育程度是否影响收入？”这类问题。解析基于关键词；复杂设计建议使用引导模式。

如果统计上合适的方法尚未实现，规划器会明确说明，并给出当前可用的替代方法，而不是静默返回空结果。

### 统计方法

| 方法 | 用途 | 图表 |
|---|---|---|
| 描述统计 | 均值、标准差、中位数、四分位数、范围 | 直方图 |
| 频次分析 | 分类变量的频数与百分比 | 柱状图 |
| 独立样本 t 检验 | 比较两组连续结果 | 箱线图 + 分组柱状图 |
| 单因素方差分析 | 比较三组及以上连续结果 | 箱线图 + 分组柱状图 |
| Mann-Whitney U | 两组非参数比较 | 箱线图 |
| Kruskal-Wallis H | 三组及以上非参数比较 | 箱线图 |
| Pearson 相关 | 两个连续变量的线性关联 | 散点图 + 拟合线 |
| Spearman 相关 | 单调关联 | 散点图 |
| 卡方检验 | 分类变量之间的关联 | 柱状图 |
| 线性回归 | 连续结果预测 | 散点/拟合线、箱线图或拟合值-观察值图 |

线性回归支持分类预测变量（自动哑变量编码），统计引擎支持多个预测变量；引导界面当前选择一个因变量和一个自变量。

### 安全、解释与报告

- 分析前运行 6 项检查：变量类型匹配、样本量、正态性（偏度/峰度启发式）、方差齐性（标准差比值启发式）、离群值（IQR）和多重比较提醒。
- 安全 error 会阻断执行；warning 仅作提示。
- 10 种方法均有确定性的模板化解读。
- 报告针对当前分析生成 Markdown 和 HTML；GUI 当前打开 Markdown 版本。

### 当前限制

- 自由文本解析基于关键词；复杂问题请使用引导模式。
- 尚无事后检验、eta-squared、logistic 回归和交叉表；规划器会在相关场景说明这些缺口。
- SPSS 值标签已加载，但结果表和图表当前仍显示原始数值。
- 报告仅覆盖当前一次分析；尚不支持多分析汇总和图表嵌入。
- GUI 尚未提供溯源图和代码导出入口；相关能力可通过 API 使用。
- 引导界面选择一个自变量；多自变量回归可通过 API 使用。
- 数据集保存在当前服务进程的内存中；暂无用户账户或多用户支持。
- 核心分析是确定性的，不包含 LLM 或 agent 层。
- 暂不支持暗色模式、移动端布局或桌面打包。

---

## Quick Start / 快速开始

### Prerequisites / 环境要求

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

### How to use / 使用步骤

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

## Design / 设计原则

- **Statistics first** — methods are computed with Polars, SciPy, and statsmodels; results are deterministic.
- **Template before LLM** — interpretations come from explicit templates, not generated prose.
- **Provenance by default** — imports and analyses are recorded; code export is available through the API.

---

## License / 许可证

GNU Affero General Public License v3.0 — see [LICENSE](./LICENSE).

---

## Citation / 引用

```bibtex
@software{quantrix2026,
  author = {Quantrix Contributors},
  title = {Quantrix: A Quantitative Research Platform for the Social Sciences},
  year = {2026},
  version = {0.1.0},
  url = {https://github.com/C1rcleW/QuantriX}
}
```
