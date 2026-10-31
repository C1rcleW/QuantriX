<p align="right">
  <a href="README.md"><img src="https://img.shields.io/badge/English-README-1f6feb?style=for-the-badge" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/%E4%B8%AD%E6%96%87-README-d73a49?style=for-the-badge" alt="中文"></a>
</p>

# Quantrix v0.1.0

**面向社会科学研究的定量分析平台**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![CI](https://github.com/C1rcleW/QuantriX/actions/workflows/ci.yml/badge.svg)](https://github.com/C1rcleW/QuantriX/actions/workflows/ci.yml)
[![Status](https://img.shields.io/badge/status-pre--alpha-orange)]()

Quantrix 把一份数据集变成一次有引导的分析：导入数据、选择研究目标和变量、运行统计方法、检查假设、阅读结果解读，并生成报告。核心分析是确定性的，不依赖 LLM。

> 预发布阶段。主要分析流程端到端可用；GUI 功能可用，但仍较粗糙。

---

## 能做什么

- 导入 CSV、TSV、TXT 和 SPSS SAV/ZSAV 文件。
- 自动识别变量类型、缺失值和基本分布。
- 两种提问方式：**引导模式**（选择目标 + 下拉框选择变量）或 **自由文本**（基于关键词的问题解析）。
- 运行 10 种统计方法，并在浏览器中绘制对应图表。
- 执行前进行统计假设检查：error 会阻断分析，warning 会提示给研究者。
- 生成基于模板的结果解读，以及当前分析的 Markdown/HTML 报告。
- 在溯源图中记录导入与分析步骤；可通过 API 导出 Python/R/SPSS 代码。

## 两种分析模式

**引导模式（推荐）**——四种研究目标：

| 目标 | 示例 |
|---|---|
| 描述 | 概括一个变量的分布 |
| 比较组间差异 | 比较连续变量在不同组之间的差异 |
| 查找关联 | 衡量两个变量之间的关系 |
| 预测 | 用一个或多个预测变量建模连续结果 |

**自由文本模式**——输入“教育程度是否影响收入？”这类问题。解析基于关键词；复杂设计建议使用引导模式。

如果统计上合适的方法尚未实现，规划器会明确说明，并给出当前可用的替代方法，而不是静默返回空结果。

## 统计方法

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

## 安全、解释与报告

- 分析前运行 6 项检查：变量类型匹配、样本量、正态性（偏度/峰度启发式）、方差齐性（标准差比值启发式）、离群值（IQR）和多重比较提醒。
- 安全 error 会阻断执行；warning 仅作提示。
- 10 种方法均有确定性的模板化解读。
- 报告针对当前分析生成 Markdown 和 HTML；GUI 当前打开 Markdown 版本。

## 当前限制

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

## 快速开始

### 环境要求

- Python 3.12+
- Node.js 18+（前端）

### 后端

```bash
git clone https://github.com/C1rcleW/QuantriX.git
cd QuantriX/python

pip install -e ".[dev,stats]"
python -m uvicorn quantrix.server.app:app --host 127.0.0.1 --port 8532
```

### 前端

```bash
cd QuantriX/frontend
npm install
npm run dev
```

打开 `http://127.0.0.1:5173`。API 文档位于 `http://127.0.0.1:8532/docs`。

运行后端测试：

```bash
cd QuantriX/python
pytest
```

### 使用步骤

1. 打开 **Data** 标签页，导入 CSV 或 SAV 文件。
2. 打开 **Analysis**，选择引导模式或自由文本，并选择研究目标与变量。
3. 点击推荐的方法，执行安全检查和统计分析。
4. 查看结果表、图表和警告。
5. 点击 **Explain Results** 获取文字解读，再点击 **Report** 生成 Markdown 报告。

---

## API

后端提供一组精简的 HTTP API，完整 schema 见 `/docs`。

- `POST /api/data/import` — 上传 CSV/SAV 文件。
- `GET /api/data/{id}`、`/variables`、`/profile`、`/table` — 查看数据集。
- `POST /api/analysis/plan`、`/plan-structured` — 获取方法推荐。
- `POST /api/analysis/execute` — 通过安全门禁后执行分析。
- `POST /api/safety/check` — 查看假设检查与警告。
- `POST /api/chat/interpret` — 生成模板化解读。
- `POST /api/report/generate` — 渲染 Markdown 和 HTML。
- `GET /api/dag`、`POST /api/dag/export` — 查看溯源并导出 Python/R/SPSS 代码。

---

## 设计原则

- **统计优先**——方法基于 Polars、SciPy、statsmodels 计算，结果是确定性的。
- **模板优先于 LLM**——解读来自显式模板，而不是生成式文本。
- **默认可溯源**——导入与分析步骤会被记录；代码导出通过 API 提供。

---

## 许可证

GNU Affero General Public License v3.0 — 见 [LICENSE](./LICENSE)。

## 引用

```bibtex
@software{quantrix2026,
  author = {Quantrix Contributors},
  title = {Quantrix: A Quantitative Research Platform for the Social Sciences},
  year = {2026},
  version = {0.1.0},
  url = {https://github.com/C1rcleW/QuantriX}
}
```

<p align="right"><a href="README.md">English version →</a></p>
