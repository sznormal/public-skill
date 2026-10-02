# 咨询报告领域模块

> AFP Skill Creator · Domain Module
> 领域：咨询报告（战略、行业分析、案例、方案、路演）
> 适用用户：咨询顾问、独立顾问、in-house 战略、投行 IBD、行业分析师
>
> 本模块在 AFP-skill-creator P1 用户识别自己是"咨询报告"领域后被 Read on demand

---

## 一、领域概述

**咨询 skill** 目标：帮助咨询顾问完成从"问题定义"到"可行动方案"的结构化产出——高信息密度、强说服力、快节奏。

**典型场景**：
- 战略咨询报告
- 行业深度分析
- 尽调（Due Diligence）报告
- 客户提案（Proposal）
- 路演材料
- 案例分析
- 转型方案

---

## 二、AFP 三支柱在咨询领域的具象化

| AFP 支柱 | 咨询具象 |
|---|---|
| **Auto · 自主决策** | agent 自主推进"问题→假设→分析→结论"四阶段，Hard Stop 在关键假设验证点 |
| **Flow · 协同流动** | 问题定义 → 假设树 → 数据分析 → 洞察 → 建议 → 执行路径 跨阶段传递 |
| **Prompt · 提示词工程** | SCQA / MECE / 金字塔原理 等咨询范式的 prompt 标准化 |

---

## 三、咨询领域方法论参考

### 3.1 结构化框架

- **SCQA**（Situation-Complication-Question-Answer）：报告开头结构
- **金字塔原理**：结论先行 + MECE 分组 + 逻辑递进
- **MECE**（Mutually Exclusive, Collectively Exhaustive）：分类互斥完备
- **假设树**：从核心问题拆解到可验证子问题
- **议题树**：从议题拆解到子议题（BCG 常用）

### 3.2 分析框架

- **麦肯锡 7S**：组织诊断
- **Porter's Five Forces**：行业竞争分析
- **BCG 矩阵**：业务组合分析
- **SWOT**：内外部环境分析
- **PESTEL**：宏观环境
- **价值链分析**：企业内部
- **业务模式画布**：商业模式

### 3.3 数据类型

- **一手数据**：客户访谈 / 员工访谈 / 专家访谈 / 问卷 / 门店观察
- **二手数据**：公司财报 / 行业报告 / 数据库（Wind、Bloomberg、Euromonitor）
- **对标数据**：竞对分析 / 标杆研究
- **专家数据**：Expert Network（Guidepoint、AlphaSights）

### 3.4 交付形态

- **Deck**（PPT）：60-100 页典型咨询报告
- **Memo**：3-5 页决策备忘录
- **Executive Summary**：1-2 页高管摘要
- **Full Report**：完整报告 + 附录

skill 应根据用户目标交付形态调整输出结构。

---

## 四、咨询专属反模式（13 条）

**这些是咨询领域**特有的**内容质量反模式**，与 skill 结构反模式（`modules/skill-anti-patterns.md` 通用 20 条）互补。

### ❌ C1. MECE 违反 · 分类有交叉

分类既不互斥也不完备

**症状**："我们的客户分为：大客户 / VIP 客户 / 关键客户"——三个类别本质重叠

**修正**：skill 应对分类维度做 MECE 校验

### ❌ C2. MECE 违反 · 分类不完备

**症状**："竞对分为国内 / 海外"，遗漏了"跨境电商"

**修正**：skill 应主动询问"是否有其他类别未纳入"

### ❌ C3. 结论先行失败

金字塔原理要求结论先行，但报告写成"分析先行"

**症状**：读者读了 5 页才知道结论是什么

**修正**：skill 应在每章开头强制生成"本章核心结论"

### ❌ C4. 无洞察（Insight）

只有事实描述，没有洞察生成

**症状**："2020 年市场规模 100 亿，2023 年 200 亿"——纯陈述，无判断

**修正**：skill 应把"So what?"作为强制生成字段（这个数据意味着什么？）

### ❌ C5. 建议不可执行

建议高度抽象、无法落地

**症状**："建议加强创新" / "建议提升运营效率"

**修正**：skill 应把建议拆解为"谁、做什么、什么时候、什么资源、成功标准"

### ❌ C6. 假设未验证

分析基于假设，但未标注哪些是假设、哪些是事实

**症状**：读者读完不知道哪些结论依赖假设成立

**修正**：skill 应强制标注每条主张的证据类型（fact / assumption / hypothesis / expert opinion）

### ❌ C7. 数据无来源

引用数据未标注来源

**症状**："中国餐饮市场规模 4.5 万亿"——但没写来自 Euromonitor 2023 还是自己估算

**修正**：AFP-SPEC §6 在咨询领域的具体应用——每条数据必须标注 source + date

### ❌ C8. 逻辑链断裂

从 A 跳到 B 缺少论证步骤

**症状**："因为市场增长快 → 所以应该多招人"（中间跳过了"当前人力不足"）

**修正**：skill 应检查每个因果论证的中间步骤

### ❌ C9. 建议脱离客户情境

建议是通用最佳实践，不针对客户具体情境

**症状**："建议采用 OKR"——不管客户是不是适合

**修正**：skill 应把"客户情境适配度"作为建议生成的前置检查

### ❌ C10. 忽视执行风险

只讲机会，不讲实施风险

**症状**：转型建议不讨论组织阻力、资金压力、时间成本

**修正**：skill 应把风险识别作为建议章的强制字段

### ❌ C11. Deck 页面信息过载

单页塞入过多信息（图表 + 表格 + 长文字）

**症状**：一页 20+ 数据点，读者看不懂重点

**修正**：skill 应遵循"one page one message"原则

### ❌ C12. 数据可视化选错图表

用错图表类型误导读者

**症状**：用 pie chart 表达时间趋势 / 用 line chart 表达占比

**修正**：skill 应内置"图表类型 vs 数据类型"匹配表

### ❌ C13. 咨询术语过载

塞满 "leverage" "synergy" "value creation" 等术语，但缺乏具体内容

**症状**：读起来像 BuzzWord Bingo

**修正**：skill 应检查每个咨询术语后是否有具体实例支撑

---

## 五、咨询 Bundle 参考架构

咨询领域推荐走 **Federated Bundle** 架构：

```
AFP-ecosystem/consulting/
├── strategy-report-master/              ← 战略报告 Bundle
│   ├── SKILL.md                          薄路由，~2000 token
│   ├── stages/
│   │   ├── 01-problem-definition.md
│   │   ├── 02-scqa-opening.md
│   │   ├── 03-hypothesis-tree.md
│   │   ├── 04-analysis-framework.md
│   │   ├── 05-data-collection.md
│   │   ├── 06-insight-generation.md
│   │   ├── 07-recommendation.md
│   │   ├── 08-execution-roadmap.md
│   │   ├── 09-executive-summary.md
│   │   └── 10-deck-formatting.md
│   └── modules/
│       ├── frameworks-catalog.md         框架库（7S / SWOT / Porter / ...）
│       └── industry-branches.md          行业分支（TMT / 消费 / 金融 / ...）
│
├── industry-analysis-master/            ← 行业深度分析 Bundle
├── due-diligence-master/                ← 尽调报告 Bundle
├── proposal-master/                     ← 提案 Bundle
├── case-study-master/                   ← 案例分析 Bundle
└── pitch-deck-master/                   ← 路演材料 Bundle
```

咨询跨 Bundle 的 shared primitives：

```
AFP-shared-primitives/consulting/
├── scqa-structure.md
├── mece-checker.md
├── pyramid-principle.md
├── financial-modeling.md
├── market-sizing.md                    Bottom-up / Top-down 市场规模测算
├── competitive-benchmarking.md
├── expert-interview-guide.md
└── evidence-chain-consulting.md        咨询证据链验证
```

---

## 六、咨询领域典型触发词

设计咨询 skill 时，触发词应覆盖：

- 报告相关：咨询报告 / 战略报告 / 行业报告 / 尽调 / 深度分析 / 案例分析 / 路演材料
- 结构相关：SCQA / MECE / 金字塔 / 假设树 / 议题树
- 分析相关：SWOT / Porter / 5C / 7S / PESTEL / 价值链 / 业务模式
- 场景相关：战略咨询 / 管理咨询 / 投行 / 尽调 / 提案 / 路演 / 客户沟通
- 服务相关：帮我写 / 帮我做 / 帮我搭 / 帮我审 / 帮我改

主控 SKILL.md 的 description 应根据具体覆盖场景，选取 10-15 个组合。

---

## 七、咨询领域行文规范

skill 生成的咨询内容应符合：

1. **结论先行**：每章、每节、每段的开头都是结论/主张
2. **金字塔递进**：结论 → 分组理由 → 事实数据（3 层结构）
3. **句法简洁**：句均不超过 30 字，避免复合从句
4. **数字导向**：结论优先用数字支撑（"3 大 / 5 类 / 30%"）
5. **术语克制**：每个咨询术语后必配具体例子
6. **对比表达**：说清楚"从 X 到 Y"、"相比 A 优 B"（对比强化观点）

skill 应在输出后自动检查这些指标。

---

## 八、咨询证据链标准

AFP-SPEC §6 Evidence Chain 在咨询领域的具体要求：

| 证据类型 | 标准 |
|---|---|
| 行业规模/增长数据 | 数据源（Euromonitor/Frost/公司财报）+ 年份 + 口径 |
| 公司数据 | 公司名 + 年报编号 + 页码 |
| 专家访谈 | 专家角色 + 访谈日期 + 匿名化 ID |
| 客户访谈 | 客户角色 + 访谈日期 + 引言方式（direct/paraphrased） |
| 竞对分析 | 数据源 + 采集日期 + 分析师 |
| 案例研究 | 案例来源 + 时间 + 是否可公开 |

skill 生成的所有数据必须至少满足对应类型的最低标准，否则标记为 `estimate` 或 `assumption`。

---

## 九、AFP-SPEC 合规目标（咨询领域推荐）

咨询类 skill 的合规目标：

| 合规等级 | 适用场景 |
|---|---|
| **Bronze** | 个人使用、探索期、教学 |
| **Silver（推荐）** | 正式贡献 AFP-ecosystem、独立顾问日常工作 |
| **Gold** | 咨询公司标准 skill、企业咨询工具、专家 agent |

Gold 级咨询 skill 建议追加：
- 通过 3 位咨询合伙人 peer-review
- 至少在 10 个真实客户项目跑通
- MECE 检查通过率 > 95%
- 洞察生成质量评分 > 80/100

---

## 十、参考的咨询 skill（截至 v0.2）

**目前 AFP-ecosystem 尚无咨询 skill Bundle**——这是巨大的开拓空间。

第一批推荐做的咨询 skill：

1. `strategy-report-master`（战略咨询报告全流程）
2. `industry-analysis-master`（行业深度分析全流程）
3. `pitch-deck-master`（路演材料全流程）

**贡献这些 Bundle 的合伙人将成为 AFP 咨询领域的奠基者**——类似学术领域的一平/学君。

---

## 十一、咨询领域的合伙人画像

理想的咨询领域 AFP 合伙人：

- **背景**：MBB（麦肯锡/BCG/贝恩）/ 四大 / 精品咨询 / in-house 战略 3 年以上
- **能力**：既懂框架又懂落地，既能写 deck 又能给 recommendation
- **动机**：把自己的咨询方法论工程化为可复用产品

**此类合伙人的 agent 型 IP 头部年收入天花板 ¥1000-5000 万**（远高于学术领域）。

---

## 十二、贡献咨询反模式

如果你在咨询 skill 开发中发现了新的咨询专属反模式（C14, C15, ...），欢迎贡献到本模块。

---

*本模块 v0.2 · 2026-07-01*
*源自：麦肯锡/BCG/贝恩公开方法论 + AFP 三支柱 + 咨询实战沉淀*
*状态：待有咨询领域合伙人加入 AFP 行动派后进一步打磨*
