# Quantrix v0.1.0 (bulind）

**AI-Native Quantitative Research Platform for Social Sciences**
**面向社会科学研究的 AI 原生定量分析平台**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Tests](https://img.shields.io/badge/tests-160%20passed-green)]()
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)]()

Quantrix is an open-source academic infrastructure for social science research. From data to paper, one straight line.

Quantrix 是一个面向社会科学研究的开源学术基础设施。从数据到论文，一条直线。

> Pre-alpha. Core pipeline works end-to-end. GUI is functional but rough.
> 预发布阶段。核心管线端到端可用，GUI 功能正常但较为粗糙。

---

## English

### Why Quantrix?

Social science researchers face three barriers:

1. **Statistical anxiety** -- knowing *which* method to use, not *how* to click
2. **Repetitive workflows** -- hundreds of menu clicks in SPSS for every paper
3. **Reproducibility gaps** -- copy-paste from SPSS output to Word, lose the trail

Quantrix replaces that with: **import data -> ask a question -> get results with interpretation -> export reproducible code**.

### What It Does

```
CSV/SAV -> Auto-detect types -> Ask a question -> Method recommendation
       -> Run analysis -> Safety check -> Interpretation -> Report -> Export Python/R/SPSS
```

| Step | Example |
|---|---|
| Import | Upload `iris.csv` -> auto-detects 4 continuous + 1 nominal variable |
| Ask | Select "Compare Groups" -> pick SepalLength ~ Species from dropdowns |
| Plan | Recommends One-Way ANOVA (95% confidence) + Kruskal-Wallis as alternative |
| Execute | F(2,147) = 119.27, p < .001 |
| Safety | Checks normality, homogeneity, sample size, outliers |
| Interpret | "The comparison of SepalLength across groups of Species was statistically significant." |
| Report | One-click APA-format report (Markdown + HTML) |
| Export | Python, R, or SPSS syntax reproduction code |

### Analysis Modes

**Guided (default)** -- No natural language required. Select your goal (Describe / Compare Groups / Find Association / Predict), pick variables from dropdowns, zero ambiguity.

**Free Text** -- Type a research question (e.g., "Does education affect income?"). Keyword-based NLP. Works for simple patterns.

### Statistics Methods (10)

| Method | Backend |
|---|---|
| Descriptive Statistics | polars |
| Frequency Analysis | polars |
| Independent Samples t-test | scipy.stats.ttest_ind |
| One-Way ANOVA | scipy.stats.f_oneway |
| Mann-Whitney U | scipy.stats.mannwhitneyu |
| Kruskal-Wallis H | scipy.stats.kruskal |
| Pearson Correlation | scipy.stats.pearsonr |
| Spearman Correlation | scipy.stats.spearmanr |
| Chi-Square Test | scipy.stats.chi2_contingency |
| Linear Regression | statsmodels.OLS |

### Known Limitations

- Free-text parser is keyword-based. Use Guided mode for complex questions.
- ANOVA eta-squared not yet computed.
- No post-hoc tests (Tukey HSD).
- No dark mode, no mobile support, no Electron packaging.

### Not Yet Built

SEM, HLM/MLM, EFA/CFA, Time Series, Bayesian Statistics, Visualization (charts), Plugin system, Multi-user support.

---

## 中文

### 为什么用 Quantrix？

社会科学研究者面临三大障碍：

1. **统计焦虑** —— 知道*该用什么方法*，但不知道*怎么操作*
2. **重复劳动** —— 每篇论文在 SPSS 里点几百次菜单
3. **可复现性断档** —— 从 SPSS 复制粘贴到 Word，丢失分析过程

Quantrix 的目标：**导入数据 -> 提出问题 -> 获得结果与解读 -> 导出可复现代码**。

### 能做什么

```
CSV/SAV -> 自动识别类型 -> 提出问题 -> 方法推荐
       -> 执行分析 -> 安全检测 -> 结果解读 -> 生成报告 -> 导出 Python/R/SPSS 代码
```

| 步骤 | 示例 |
|---|---|
| 导入 | 上传 `iris.csv` -> 自动识别 4 个连续变量 + 1 个分类变量 |
| 提问 | 选"比较组间差异" -> 下拉框选择 SepalLength ~ Species |
| 规划 | 推荐单因素方差分析（95% 置信度）+ Kruskal-Wallis 备选 |
| 执行 | F(2,147) = 119.27, p < .001 |
| 安全 | 检查正态性、方差齐性、样本量、离群值 |
| 解读 | "不同 Species 组间的 SepalLength 存在统计学显著差异。" |
| 报告 | 一键生成 APA 格式报告（Markdown + HTML） |
| 导出 | Python / R / SPSS 语法复现代码 |

### 两种分析模式

**引导模式（默认）** -- 无需自然语言。选择研究目标（描述/比较组间差异/查找关联/预测），从下拉框选择变量，零歧义。

**自由文本模式** -- 输入研究问题（如"教育程度是否影响收入？"）。基于关键词 NLP，处理简单句式。

### 统计方法（10 种）

| 方法 | 实现 |
|---|---|
| 描述统计 | polars |
| 频次分析 | polars |
| 独立样本 t 检验 | scipy.stats.ttest_ind |
| 单因素方差分析 | scipy.stats.f_oneway |
| Mann-Whitney U 检验 | scipy.stats.mannwhitneyu |
| Kruskal-Wallis H 检验 | scipy.stats.kruskal |
| Pearson 相关 | scipy.stats.pearsonr |
| Spearman 相关 | scipy.stats.spearmanr |
| 卡方检验 | scipy.stats.chi2_contingency |
| 线性回归 | statsmodels.OLS |

### 已知限制

- 自由文本解析为关键词匹配。复杂问题请使用引导模式。
- 尚未计算方差分析效应量（eta-squared）。
- 无事后检验（Tukey HSD）。
- 无暗色模式、无移动端支持、无 Electron 打包。

### 尚未构建

结构方程模型(SEM)、多层线性模型(HLM/MLM)、因子分析(EFA/CFA)、时间序列、贝叶斯统计、可视化引擎（图表）、插件系统、多用户协作。

---

## Quick Start / 快速开始

### Prerequisites / 环境要求

- Python 3.12+
- Node.js 18+ (for frontend / 前端)

### Backend / 后端

```bash
git clone https://github.com/C1rcleW/QuantriX.git
cd QuantriX/python

pip install -e ".[dev,stats]"
pytest                          # 160 tests / 160 个测试
python -m uvicorn quantrix.server.app:app --host 127.0.0.1 --port 8532
```

### Frontend / 前端

```bash
cd QuantriX/frontend
npm install
npm run dev                     # http://127.0.0.1:5173
```

### Usage / 使用步骤

1. Open `http://127.0.0.1:5173` / 打开浏览器访问
2. **Data tab / 数据标签页** -- drag a CSV or `.sav` file / 拖入文件
3. **Analysis tab / 分析标签页** -- select goal + variables, click Ask / 选择目标和变量
4. Click a method -> results appear / 点击方法 -> 显示结果
5. **Explain Results** -> interpretation / 自然语言解读
6. **Report** -> APA-format markdown / 生成报告

---

## Architecture / 架构

```
+-----------------------------------------------------+
|              Frontend / 前端 (React + TypeScript)      |
|         Data Mode  |  Analysis Mode  |  Report Mode   |
+-----------------------------------------------------+
|              HTTP API / 接口 (FastAPI, 14 endpoints)   |
+----------+----------+----------+---------------------+
| Research | Safety   | Result   | Reproducibility     |
| Planner  | Net      | Interp.  | DAG + Export         |
+----------+----------+----------+---------------------+
|         Statistics Engine / 统计引擎 (10 methods)      |
|              scipy + statsmodels + polars              |
+-----------------------------------------------------+
|        Data Layer / 数据层 (SAV/CSV -> Polars)         |
+-----------------------------------------------------+
```

## API Endpoints / 接口列表

```
POST /api/data/import              # Upload / 上传文件
POST /api/analysis/plan            # Free-text question / 自由文本提问
POST /api/analysis/plan-structured  # Goal + variables / 结构化提问
POST /api/analysis/execute         # Run analysis / 执行分析
POST /api/safety/check             # Assumptions check / 假设检验
POST /api/chat/interpret           # Interpretation / 结果解读
POST /api/report/generate          # APA report / 生成报告
GET  /api/dag                      # Provenance graph / 溯源图
POST /api/dag/export               # Python/R/SPSS code / 导出代码
```

API docs: `http://127.0.0.1:8532/docs`

---

## Project Structure / 项目结构

```
QuantriX/
├── python/
│   ├── quantrix/
│   │   ├── core/           # Dataset, Metadata, Protocols
│   │   ├── data/           # Readers (CSV/SAV), TypeDetector, Profile
│   │   ├── stats/          # 10 statistical methods / 10 种统计方法
│   │   ├── safety/         # 6 safety rules / 6 条安全规则
│   │   ├── planner/        # Question parser + decision tree
│   │   ├── interpreter/    # Result interpretation engine
│   │   ├── report/         # Report generator (Markdown + HTML)
│   │   ├── dag/            # Provenance tracking + export
│   │   └── server/         # FastAPI + 14 routes
│   └── tests/              # 160 tests (pytest)
├── frontend/
│   └── src/                # React + TypeScript GUI
├── LICENSE                 # AGPL-3.0
└── README.md
```

---

## Development / 开发

```bash
cd python
pip install -e ".[dev,stats]"
pytest                              # 160 tests
ruff check quantrix/ tests/         # Lint (0 errors)
mypy quantrix/                      # Type check
```

### Adding a new method / 添加新方法

1. Extend `BaseStatMethod` in `stats/` / 在 `stats/` 中继承 `BaseStatMethod`
2. Implement `execute() -> StatResult` / 实现 `execute()`
3. Register in `stats/registry.py` / 在 `registry.py` 中注册
4. Add interpretation template / 添加解读模板
5. Add decision tree path (optional) / 添加决策树路径（可选）

---

## Design Principles / 设计原则

1. **Statistics first / 统计优先** -- Every method verifiable against SPSS/R/scipy.
2. **Researcher workflow / 研究者工作流** -- Built for what a social scientist does in a day.
3. **Template before LLM / 模板优先于大模型** -- Core interpretation is deterministic.
4. **Reproducible by default / 默认可复现** -- Every analysis step tracked in the DAG.

---

## License / 许可证

GNU Affero General Public License v3.0 -- see [LICENSE](./LICENSE).

---

## Citation / 引用

```bibtex
@software{quantrix2026,
  author = {Quantrix Contributors},
  title = {Quantrix: AI-Native Quantitative Research Platform for Social Sciences},
  year = {2025},
  version = {0.1.0},
  url = {https://github.com/C1rcleW/QuantriX}
}
```
