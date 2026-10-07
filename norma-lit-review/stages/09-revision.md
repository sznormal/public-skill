# P9 · 审稿后修订（Revision based on Review）

> 阶段定位：承接 **P8 审稿人发表级审查** 的产出（`publication_review.md`），把审稿意见逐条转化为可落地的修订，产出「修订版综述」+「Response to Reviewers（给审稿人的回信）」，并跑一轮**复检闸门**确认无遗漏。
>
> 核心原则：**审稿意见是待办清单，不是终点**。每一条 Major/Minor 必须「要么已修订、要么在回信中给出不退修的合理解释（需用户确认）」，不允许静默忽略。

---

## 一、输入物（前置 Hard Stop 检查）

1. ✅ `publication_review.md` 存在且含：四原型意见表 + 总体决定 + Response 骨架。
2. ✅ 综述终稿（如 `literature_review_final_zh.md`）路径已知。
3. ⚠️ 若 `publication_review.md` 缺位，先回退 P8，不得凭空编造审稿意见。

---

## 二、修订工作流（5 步）

### 步骤 1 · 拆条与定级
读取 `publication_review.md`，把每条意见抽成结构化任务：
```
| 编号 | 原型 | 严重度(Major/Minor/Accept) | 修订动作 | 落点(章节/字段) | 状态 |
```
- **Major**：必须修订，否则影响录用。
- **Minor**：建议修订，工作量小、收益高，默认全做。
- **Accept（正面）**：通常不改动正文，但若有「Cover Letter 声明」类动作，记入回信。

### 步骤 2 · 逐条修订（按落点）
常见修订类型与处理建议：

| 审稿意见类型 | 处理动作 |
|------|---------|
| 方法学措辞误导（如 PRISMA 式语言 vs 非系统综述） | 在对应段/表下加澄清注，明确"非 PRISMA 注册流程 / 叙事性整理示意" |
| 中文/小语种覆盖代表性弱 | 补 1–2 篇该语种核心综述，更新参考文献与正文引用；或补一段"选取口径说明" |
| 缺英文摘要/关键词 | 在正文开头（标题下）补 English Abstract + Keywords（GB7714 中文核心硬性项） |
| 独特增量/贡献未论证 | 在引言与结论各补一段"本文定位与增量"，点明相对已有综述的差异视角 |
| 经典域/论据锚点不足 | 补具名系统/年份/数据锚点，提升论断可证伪性 |
| 图表未实生成/不可编辑 | 用矢量(SVG)或表格生成可编辑图，存入 `outputs/lit-review/figures/` |
| 章节引导句缺失 | 在对应章首补 1 句"为什么/读者预期"引导 |
| 旧名/旧编号残留 | 全文检索旧名替换为规范名并加注 |

### 步骤 3 · 生成 Response to Reviewers
产出 `response_letter.md`，**逐条对应**审稿意见，格式：
```
[R{编号} → {原型}{编号}] 审稿人意见摘要
→ 修订动作：……
→ 正文改动位置：第 X 章 / 第 Y 行 / 新增段落
→ 验证：已复核 / 经用户确认不退修（理由：……）
```
- 对每条 Major 必须给出「已修订」证据（章节/行号/新增内容摘要）。
- 对不退修的项，必须写明理由且**交由用户确认**（Hard Stop）。

### 步骤 4 · 复检闸门（Revision Gate）
修订后跑一次轻量复检：
- 正文是否仍**自洽**（无新引入的矛盾/占位）。
- 新增文献是否已纳入参考文献列表且**格式一致**。
- 字数是否仍落在 P7-C 目标区间。
- 审稿意见 0 条"静默忽略"（Accept 除外）。

**⚠️ 每次内容编辑后必须重跑引用一致性 + 字数脚本（2026-09-07 实战教训）**：
孤儿文献会在**任何**增删段落时产生——实战中扩写修复 [30] 后，新增段落又让 [41] 变成孤儿；
字数在多轮编辑后同样会漂移。规则：
1. 引用一致性（孤儿/缺失）与字数脚本**不是 P9 收尾跑一次**，而是**每完成一处结构性编辑就重跑**；
2. 扩写字数时不得灌水——每段必须带可核查的分析论点（引用既有文献的第二/三次使用也算深化），
   单次引用 ≤1 次的文献数是"是否真深化"的量化信号（实战：六段深化使 25→13）；
3. 跨语言改写（中→英）另查**残留中文字符**（正则 `[\u4e00-\u9fff]` 扫正文，中文检索词行除外），
   并重校定位口径（国际读者 vs 国内读者）。

**P8↔P9 迭代环**：P8 < 85 分 → P9 修订 → 重跑 P8 → 仍 <85 则再入 P9。
每轮在 HUD `publication_review.history` 追加一行（round/date/target/score/decision/note），
未闭环项以 **R-# 编号跨轮携带**，处置表用 ✅（闭环）/ 🟡（部分闭环）/ ❌（未动）标记——
部分闭环项必须写明"为何无法完全闭环"（如：无更优学术源可替代），不得静默降级。

### 步骤 5 · 落盘与状态
- 修订版覆盖或另存为 `literature_review_submission_zh.md`（投稿就绪版，建议另存以保留 v0.4 终稿）。
- `response_letter.md` 一并落盘。
- 按 SKILL.md「阶段控制台·五」收尾：写产物（`literature_review_submission_zh.md` / `response_letter.md`）→ 记台账（`log --stage P9 --decision "修订闭环/部分闭环项"`）→ 快照（`snapshot --stage P9`）→ 更新 HUD（`current_stage=P9`、`revision.*` 字段、`history.completed_stages` 加 P9）→ 渲染仪表盘 → 输出 Hard Stop 卡。
- 输出硬停止卡（见 SKILL.md 通用格式）。

---

## 三、HUD 字段（P9 专用）

```json
"revision": {
  "review_source": "publication_review.md",
  "major_total": 0,
  "minor_total": 0,
  "resolved_major": 0,
  "resolved_minor": 0,
  "declined_items": [],
  "response_letter_path": "",
  "revision_gate_passed": false,
  "submission_draft_path": ""
}
```

---

## 四、产出物

| 产物 | 路径 |
|------|------|
| 修订版综述（投稿就绪） | `literature_review_submission_zh.md` |
| 给审稿人的回信 | `response_letter.md` |
| （可选）可编辑图表 | `figures/trend.svg` / `figures/domain_compare.svg` |

---

## 五、与其他阶段的关系

- **前置**：P8（审稿意见来源）。无 P8 不得进 P9。
- **后置**：无强制阶段。修订后可再次触发 P8（二轮审稿）形成迭代，或交付。
- **迭代提示**：若 P9 复检发现重大结构问题，可回退 P5 重写相关章节，再走 P6→P7→P8→P9。
