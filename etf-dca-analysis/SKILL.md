---
name: etf-dca-analysis
description: "ETF定投回测分析技能。通过 westock-data（腾讯自选股数据接口）获取 ETF 日 K 线行情，模拟定期定额（周定投/月定投）与一次性投入的收益对比，输出总投入、期末市值、累计收益率、资金加权年化收益率(IRR)、区间最大回撤、超额收益及累计投入/市值走势图，并生成暗色主题 Chart.js HTML 报告。当用户想了解定投收益、回测定投、比较定投与一次性买入、评估某只ETF长期持有收益、获取ETF定投分析报告时使用。触发词：ETF定投、定投回测、定投分析、定投收益、基金定投、定投报告、月定投、周定投、一次性投入对比、ETF长期收益。"
agent_created: true
---

# ETF定投回测分析

## 概述

通过 **westock-data**（腾讯自选股数据接口）获取 ETF 日 K 线行情，模拟**定期定额（定投）** 与 **一次性投入** 的收益对比，生成包含以下部分的完整 ETF 定投回测报告：

1. **ETF基础概念 + 定投原理**：什么是 ETF、什么是定投、代码规则、主流 ETF 分类
2. **定投回测指标**：总投入、期末市值、定投累计收益、年化收益率(IRR)、区间最大回撤、与一次性投入的超额收益
3. **走势可视化**：累计投入成本 vs 组合市值的随时间变化曲线

> 本技能为 `etf-analysis`（ETF持仓与收益归因分析）的兄弟技能，沿用相同的数据源、ETF 代码规范与暗色 Chart.js 报告风格，但聚焦**定投回测**这一差异化场景。

## 数据源

| 数据源 | 工具 | 用途 |
|--------|------|------|
| westock-data `kline` | CLI | ETF 日 K 线（前复权/后复权） |
| westock-data `search --type etf` | CLI | 按关键词搜索 ETF 代码 |
| westock-data `etf detail` | CLI | ETF 名称/分类/规模等基础信息 |
| 东方财富 push2his | HTTPS(备选) | K 线数据备选源 |
| 腾讯财经 qt.gtimg.cn | HTTPS(备选) | ETF 名称轻量查询 |

> **主数据源为 westock-data**。脚本中保留东方财富 API 作为备选，当 westock-data 不可用时自动降级。

## 前置依赖

- westock-data 为内置技能，无需额外安装。
- 运行备选/回测脚本需 Node（执行 westock-data CLI）与 Python 3（运行 `etf_dca_backtest.py`）。
- 优先使用托管运行时（脚本自动从 `~/.workbuddy/binaries/` 按版本推导，无需写死路径）：
  - Node: `~/.workbuddy/binaries/node/versions/<版本>/node.exe`
  - Python: `~/.workbuddy/binaries/python/versions/<版本>/python.exe`
  - 也可用环境变量覆盖：`NODE_BIN`、`WESTOCK_CLI`

## westock-data 命令速查

```bash
# westock-data 入口（脚本会自动探测本机路径，以下为参考）
WESTOCK="D:/workbudy/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js"

# ETF日K线（日K，前复权）
node $WESTOCK kline sh510300 --period day --limit 500 --fq qfq

# 按关键词搜索ETF
node $WESTOCK search 沪深300 --type etf

# ETF详情（名称/分类/规模）
node $WESTOCK etf detail sh510300
```

## 工作流程

### 第一步：ETF基础与定投原理展示

1. 加载 `references/etf_basics_dca.md`，向用户介绍：
   - **什么是 ETF**：定义、特点、风险
   - **什么是定投(DCA)**：原理、周定投/月定投、与一次性投入的区别
   - **ETF代码市场前缀规则** 与自动补全逻辑
2. 列出主流 ETF 分类与代表性代码（宽基/行业/跨境/策略/商品/债券）
3. 引导用户输入想要回测的 ETF 代码

> 如用户想查看更多 ETF，可使用 `westock-data search <关键词> --type etf` 实时搜索。

### 第二步：引导用户输入 ETF 代码与定投参数

1. 询问 ETF 代码（支持 `sh/sz+6位`、`6位纯数字`、或名称→从参考目录/搜索解析）
2. 询问定投参数（提供默认值，用户可改）：
   - **频率**：周定投（默认）/ 月定投
   - **每期金额**：默认 1000 元
   - **回测周期**：1y / 2y（默认）/ 3y / 5y / all
3. 通过 westock-data 校验代码有效性并取名称：

```bash
node $WESTOCK etf detail <代码>
```

### 第三步：运行定投回测并生成报告

执行回测脚本：

```bash
python scripts/etf_dca_backtest.py <ETF代码> \
  --freq weekly|monthly --amount 1000 --period 2y --fq qfq
```

参数说明：
- `--freq`：定投频率，`weekly`（周定投，每交易周首日为定投日）或 `monthly`（月定投，每月首日为定投日）
- `--amount`：每期定投金额（元），默认 1000
- `--period`：回测周期，`1y/2y/3y/5y/all`，默认 2y
- `--fq`：复权方式，`qfq`(前复权，默认)/`hfq`(后复权)/`none`
- `--output`：`json`(默认) 或 `table`

脚本执行流程：
1. 获取 ETF 日 K 线（优先 westock-data，备选东方财富 push2his + 重试）
2. 按频率日历对齐选取定投日（周定投=每周首个交易日，月定投=每月首个交易日）
3. 逐期以 `金额/当日收盘价` 买入，累计份额与总投入
4. 计算期末市值、定投累计收益率、资金加权年化收益率(IRR，二分法求解)
5. 一次性投入对照：期初以等额资金一次性买入，计算其收益率与年化
6. 计算区间最大回撤与超额收益
7. 输出 JSON（含 `metrics` 与 `series` 走势序列）

将脚本输出的 JSON 注入 `assets/report_template.html` 的 `window.__REPORT_DATA__`，生成完整 HTML 报告（核心指标卡 + 定投vs一次性对比表 + 累计投入/市值走势图）。

## 注意事项

- **历史局限**：回测基于历史价格，采用"收盘价买入"简化假设，未计入交易费用、申赎价差与流动性限制
- **IRR 口径**：定投年化采用资金加权收益率（IRR），与一次性持有的简单年化口径不同，二者不宜直接横比
- **westock-data优先**：所有行情优先使用 westock-data，脚本保留东方财富 API 备选
- **中国市场配色**：涨用红色(#f85149)、跌用绿色(#3fb950)，遵循中国股市惯例
- **代码格式**：`sh` / `sz` 前缀 + 6 位代码（如 sh510300、sz159915）

## 参考资源

| 文件 | 用途 |
|------|------|
| `references/etf_basics_dca.md` | ETF基础 + 定投原理 + 代码规则 + 主流分类速查 |
| `scripts/etf_dca_backtest.py` | ETF定投回测脚本（westock-data K线优先 + 东财API备选） |
| `assets/report_template.html` | HTML 报告模板（暗色主题 + Chart.js 走势图） |
