# AFP Skill Creator（Pattern 5 定型版 · 跨领域元 skill）

> AFP 行动派共同体的跨领域元 skill · 教你如何用 AFP 方法论做出任何领域的专业 skill
>
> **本 skill 本身就是 Pattern 5 · Independent skill 的实例——教你做 Pattern 5，自己也是 Pattern 5**

---

## 是什么

`afp-skill-creator` 是 AFP 行动派共同体的**跨领域元 skill**——用来创建 skill 的 skill。

它基于两个核心认识：

1. **AFP（Auto Flow Prompt）是通用内容生产方法论**，不只属于学术领域
2. **AFP-ecosystem 采用 Pattern 5 · Orchestrated Independent Collection 架构**——每个 skill 都是顶层可独立触发的 first-class 单元，合伙人贡献可见，积分精确可算（详见 F 文档《AFP Skill 架构学》v2.0）

AFP 通用内容生产方法论可以应用于：
- 学术研究
- 咨询报告
- 法律
- 医疗
- 投研分析
- 媒体新闻
- 产品设计
- 政策研究
- 教育培训
- 创作剧本
- ...

任何"结构化、可复用、需要判断力"的内容生产领域，都能用 AFP 方法论做出高质量 skill。

---

## 为什么需要它

Skill 设计有很多"坑"：主控太重、触发词冲突、frontmatter 死代码、缺少断点续传、违反 AFP-SPEC、**命名空间前缀缺失**、**Orchestrator 侵占子 skill 能力**（Pattern 5 新增反模式）等。这些**跨领域通用**。

同时每个领域又有自己的**专属反模式**（学术的"理论贴标签"、咨询的"MECE 违反"、法律的"要件遗漏"等）。

本 skill 用**"Pattern 5 通用架构 + 领域自适应模块"**架构：
- 主控 SKILL.md 处理跨领域通用的 skill 设计原则（Pattern 5 三选一 / 命名空间前缀 / 触发词治理）
- P1 意图澄清阶段识别用户所在领域 + 命名空间前缀
- P2 架构决策阶段判定 Independent / Orchestrator / Shared Primitive 三选一
- 加载对应 domain 模块（含该领域方法论、反模式、参考架构）

**目标**：让任何领域的合伙人都能做出高质量、符合 AFP-SPEC、符合 Pattern 5、能进入 AFP-ecosystem 的专业 skill。

---

## 架构：Pattern 5 · 通用 + 领域自适应

```
AFP-skill-creator/
├── SKILL.md                              ← 薄主控（~2500 token），Pattern 5 定型版
├── README.md                             ← 本文件
├── stages/                               ← 9 个跨领域通用流程阶段
│   ├── 01-intent-clarification.md         ✓ 已实现（含领域识别）
│   ├── 02-architecture-decision.md        ✓ 已实现（Pattern 5 三选一判定树）
│   ├── 03-methodology-source.md           ✓ 已实现（来源四类型 + 显性化五问 + 完整性检查）
│   ├── 04-structure-design.md             ✓ 已实现（Pattern 5 单 skill 内部结构）
│   ├── 05-frontmatter-writing.md          ✓ 已实现（Pattern 5 五段 frontmatter）
│   ├── 06-content-writing.md              ✓ 已实现（步进式六要素 + stage 骨架 + 分步写作）
│   ├── 07-integration.md                  ✓ 已实现（Committee 审议 + 触发词冲突预检）
│   ├── 08-conformance-check.md            ✓ 已实现（逐条验收 + 分级判定 + 合规证书）
│   └── 09-testing-guidance.md             ✓ 已实现（五类测试 + 迭代版本管理 + 发布 checklist）
├── modules/                              ← 通用按需模块（跨领域）
│   ├── thin-router-pattern.md            ✓ 已实现
│   ├── trigger-word-isolation.md         ✓ 已实现
│   ├── skill-anti-patterns.md            ✓ 已实现（通用 20 条 · v0.3 待补 5 条 Pattern 5 专属）
│   ├── afp-bundle-vs-primitive.md        ✓ 已实现（五代架构简史 + 新旧术语对照）
│   ├── afp-spec-checker.md               ✓ 已实现（四条款完整 checklist + 快速自检命令）
│   ├── review-theater.md                 ✓ 已实现（四审剧场 skill 开发版 · 学君原创移植）
│   ├── continuation-protocol.md          ✓ 已实现（断点续传 + 抗压缩协议 · 一平原创；含跨 skill 状态传递）
│   ├── orchestrator-design-pattern.md    待完成（暂由 stages/02 §三 + orchestrator-template 覆盖）
│   ├── trigger-word-governance.md        待完成（暂由 stages/05 §四-五 + stages/07 §四覆盖）
│   ├── temperature-tuning.md             待完成（复用学君原创，afp-shared-*）
│   └── domains/                          ← 领域自适应模块（按需 Read）
│       ├── academic.md                   ✓ 已实现（12 学术反模式 + 学术参考架构）
│       ├── consulting.md                 ✓ 已实现（13 咨询反模式 + 咨询参考架构）
│       ├── legal.md                      待完成
│       ├── medical.md                    待完成
│       ├── investment-research.md        待完成
│       ├── journalism.md                 待完成
│       ├── product.md                    待完成
│       ├── policy.md                     待完成
│       ├── education.md                  待完成
│       ├── creative-writing.md           待完成
│       └── generic.md                    ✓ 已实现（归并检查 + 领域档案五步引导 + 贡献通道）
└── templates/                            ← 复用模板
    ├── independent-skill-template.md     ✓ 已实现（Pattern 5 · Independent 模板）
    ├── orchestrator-template.md          ✓ 已实现（Pattern 5 · Orchestrator 模板）
    ├── shared-primitive-template.md      ✓ 已实现（Pattern 5 · Shared Primitive 模板 · 含调用契约）
    ├── stage-md-template.md              ✓ 已实现（stage 子文档统一骨架）
    ├── frontmatter-template.md           ✓ 已实现（五段 frontmatter 速查）
    └── bundle-master-template.md         ⚠️ Pattern 3 遗留 · 已废弃，仅作历史参考
```

**关键设计**：主控只加载**通用基础**，用户所在领域的**专属知识**通过 `modules/domains/{domain}.md` 按需加载——**符合渐进披露原则**。

---

## 使用方法

### 步骤 1 · 安装

```bash
# 复制到 Claude Code skills 目录
cp -r ~/qingni-strategy/AFP-skill-creator ~/.claude/skills/
```

### 步骤 2 · 触发

在 Claude Code 里说以下任一：
- "帮我创建一个 skill"
- "我想开发一个 AFP skill"
- "帮我做一个学术 skill"（学术领域）
- "帮我做一个咨询 skill"（咨询领域）
- "帮我做一个法律 skill"（法律领域，待 domain 模块完成）
- "帮我做一个投研 skill"
- ...

### 步骤 3 · P1 意图澄清 · 领域识别 + 命名空间前缀

主控启动后，会问你 5 个基础问题：
1. 你在哪个领域？
2. 你要创建的 skill 是做什么的？
3. 你要做的 skill 属于哪种类型？（**Pattern 5 三选一**：Independent / Orchestrator / Shared Primitive）
4. 你的命名空间前缀是什么？（**Pattern 5 强制字段**）
5. AFP-SPEC 合规等级？（Bronze / Silver / Gold）

回答后，加载对应领域模块，进入 P2 架构决策的 Pattern 5 判定树。

---

## 已实现 vs 待完成

**当前版本 v0.4 · 九阶段全通版（2026-07-23）**：

- ✅ 薄主控（SKILL.md，Pattern 5 五段 frontmatter + 三选一路由）
- ✅ **全部 9 个 stage**（P1 意图澄清 → P9 测试与迭代，主控路由表无断链）
- ✅ 7 个通用 module（薄路由 / 触发词隔离 / 通用反模式 / 架构学 Bundle→Pattern 5 / AFP-SPEC checker / 四审剧场 / 断点续传抗压缩协议）
- ✅ 3 个领域模块（academic + consulting + **generic 兜底**——未预置领域走领域档案五步引导，不再 404）
- ✅ 5 个 Pattern 5 模板（independent / orchestrator / shared-primitive / stage-md / frontmatter；bundle 旧模板已标废弃）

**v0.4 → v1.0 还需**：
- 5 个 Pattern 5 专属反模式（补进 skill-anti-patterns.md，达 25 条）
- 剩余 8 个预置领域模块（legal, medical, investment-research, journalism, product, policy, education, creative-writing；当前统一由 generic.md 兜底）
- 可选独立模块：orchestrator-design-pattern / trigger-word-governance（当前分别由 stages/02+模板、stages/05+07 覆盖）、temperature-tuning（学君原创待移植）
- 端到端测试 + 打磨

---

## 与其他 AFP 文档的关系

- **F 文档《AFP Skill 架构学》v2.0**：本 skill 的架构学理论基础（**Pattern 5 · Orchestrated Independent Collection** + 跨领域通用性 + 触发词治理机制）
- **E 文档《主控 skill 对比》**：诊断学君/一平主控的问题 → 本 skill 提供 Pattern 5 修正方法（每个子能力提升到顶层 first-class）
- **AFP-SPEC v0.1**：定义协议合规标准 → 本 skill 内置合规检查（P8）；v0.2 将纳入 Pattern 5 命名空间前缀 + 触发词治理规范
- **AFP 行动派宣言**：定义共同体精神（**跨领域**内容生产者共同体）→ 本 skill 是其第一个元产物
- **B 文档《双轨分成与后台看板》**：Pattern 5 极简两档积分算法（1 点普通 / 2 点复用奖励）

---

## 核心设计原则（本 skill 自己遵守的原则）

**本 skill 必须先做到自己教别人的所有原则**——**教你做 Pattern 5，自己也是 Pattern 5**：

1. **薄路由**：主控 ~2500 token（符合薄路由标准）
2. **按需 Read**：详情在 stages/ 和 modules/，主控只做索引
3. **领域自适应**：领域专属内容不预加载，按需 Read domain 模块
4. **触发词隔离**：明确"什么场景不触发"（见 SKILL.md frontmatter）
5. **触发词全覆盖**：涵盖所有领域用户可能表达的意图
6. **AFP-SPEC 合规**：Hard Stop + 状态管理 + 断点续传
7. **命名空间前缀**：本 skill 名为 `afp-skill-creator`——AFP 官方 skill（Steering Committee 授权）
8. **skill_type: independent**：本 skill 是 Independent 单点能力（用户想创建 skill 时触发），不是 orchestrator
9. **文档一致**：文件名、通用指令、Hard Stop 输出规范全部按 AFP 行动派标准

---

## 战略意义

### 1. AFP 从"学术共同体"升级为"跨领域内容生产者共同体"

本 skill 是这一升级的**第一个技术产物**。

### 2. AFP-ecosystem 开始有跨领域架构

原来只有学术 Bundles。v0.2 起，架构里明确了 `academia/` / `consulting/` / `legal/` / ... 多领域并列。

### 3. Agent 型 IP 头部收入天花板重估

跨领域后，**agent 型 IP 头部年收入天花板从 ¥500 万提升到 ¥5000 万级**（咨询/投研/法律等领域）。

### 4. AFP 行动派共同体成员画像扩大

从"博士/青年教师"扩为"任何领域的高质量内容生产者"。

---

## 贡献指南

如果你想扩展本 skill：

1. **补完剩余通用 stage / module / template** → 提交 PR 到 AFP-ecosystem 仓库
2. **贡献新的领域模块**（如 legal.md / medical.md）→ 通过 AFP 行动派 Steering Committee 审议
3. **加入新反模式到 skill-anti-patterns.md**（通用层）或 `domains/{domain}.md`（领域专属）→ 审议
4. **在实际使用中发现问题** → 提交 issue

---

## 版本历史

- **v0.1 · 2026-07-01（早）**：概念验证版。学术领域为主。3 stage + 3 module + 1 template
- **v0.2 · 2026-07-01（晚）**：**跨领域自适应版**。加入 domain routing。通用/领域反模式两层。学术 + 咨询作为 pattern 示范
- **v0.3 · 2026-07-05**：**Pattern 5 定型版**（阶段 A 骨架）。SKILL.md 4 问升 5 问 + Q3 三选一（Independent / Orchestrator / Shared Primitive）+ Q4 命名空间前缀强制；Frontmatter 三段扩为五段（新增 partner / skill_type / afp_spec_target）；新增 P2 架构决策 stage（三选一判定树）；新增 P4 结构设计 stage（Pattern 5 单 skill 内部结构 + Shared Primitive 调用协议 + 跨 skill 状态传递）；新增 P7 生态集成 stage（Steering Committee 审议 + 触发词冲突预检 + 上架流程）
- **v0.4 · 2026-07-23**：**九阶段全通版**。补齐剩余 4 个 stage（P3 方法论来源：来源四类型 + 显性化五问 + 完整性检查；P6 内容撰写：步进式六要素 + 分步写作纪律；P8 合规检查：逐条验收 + certified/provisional 分级 + 合规证书；P9 测试与迭代：五类测试 + 版本管理 + 发布 checklist）；补齐 4 个通用 module（afp-bundle-vs-primitive 架构学简史 / afp-spec-checker 完整 checklist / review-theater 四审剧场 skill 开发版 / continuation-protocol 断点续传抗压缩协议）；新增 domains/generic.md 未预置领域兜底（领域档案五步引导 + 贡献通道）；新增 5 个 Pattern 5 模板（independent / orchestrator / shared-primitive / stage-md / frontmatter），bundle-master-template 标注废弃；修复 P1/P2 断链引用
- **v0.4.1 · 2026-07-23**：**独家语料挂载规范**。P3 显性化五问收集独家语料（90 分样例 / 反面样例 / 话术库 / 评审意见，含脱敏要求）；P4 新增挂载规则（样例类 → `modules/exemplars.md` 分节存放，范文骨架 → `templates/`，三条纪律：按需 Read / 反面样例进反模式 / 必须落盘）；P6 话术规范新增第 6 条（产出类 stage 生成前 Read exemplars 作 few-shot 参照，输出后对齐自检）；independent / stage-md 两模板同步落地

---

## 维护者

AFP 行动派 Steering Committee
（一平 + 学君 + 首批合伙人共同治理）

---

*本 skill 是 AFP 行动派共同体的第一个"元贡献"——用 AFP 的方式教怎么做 AFP 的事。*

*架构与行动不再隔河相望——本 skill 就是它们成为同一件事的证明。*

*学术只是我们从哪起步，不是我们停留在哪。*

*Pattern 5 是学君和一平原始设计意图的正确技术化——**每个想独立触发的 skill 都是顶层可触发的 first-class 单元***。
