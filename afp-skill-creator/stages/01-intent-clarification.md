# P1 · 意图澄清

> AFP Skill Creator · Stage 01
> 目的：确认用户创建 skill 的真实意图 + 判断"该不该做"

---

## 一、意图梳理三问

如果用户回答不清晰，依次问：

### 问 1 · 你要解决的具体痛点是什么？

请求用户具体描述场景：

> 举例："学生每次做文献综述都不会梳理逻辑主线，我 1v1 讲了 50 次同一套方法论，太累。"

**痛点必须具体、真实、可重现**。抽象的"提升学术质量"不算痛点。

### 问 2 · 这个痛点当前用什么方式解决？

请求用户说明现有解法：

> 举例："现在靠 1v1 + PPT 讲解 + 学生自己练习。"

**了解现有解法** 是为了判断新 skill 的边际价值。

### 问 3 · 新 skill 打算怎么解决？

请求用户描述新 skill 的核心机制：

> 举例："让学生输入 3-5 篇核心文献，skill 自动生成主题矩阵和综述骨架。"

**必须能说出核心机制**，否则说明还没想清楚，需要先想清楚再做 skill。

---

## 二、判断"该不该做"

获取三个答案后，本 skill 自动判断以下 4 种情况：

### 情况 A · 可以做（推荐）

同时满足：
- 痛点具体真实
- 现有解法有明显效率瓶颈
- 新 skill 机制清晰可执行

→ 输出：**"意图明确，可以进入 P2 架构决策"**

### 情况 B · 应该做，但需要先想清楚方法论（多数情况）

痛点真实，但用户对"新 skill 怎么解决"还比较模糊。

→ 输出：**"建议先跳读 stages/03-methodology-source.md 的 §三『方法论显性化五问』，用 AFP 三支柱（Auto Flow Prompt）把方法论想清楚，再回来 P1 重新确认。"**

### 情况 C · 不该做——已有 skill 可以复用

如果用户意图和 AFP-ecosystem 已有 skill 高度重叠（如"帮学生做文献综述"和 `yiping-phd-literature-review` / `xuejun-literature-review-journal` 等已有独立 skill 重叠）：

→ 输出：**"你描述的场景已被 AFP-ecosystem 的 {existing_skill} 覆盖。建议：
- 先试用 {existing_skill}
- 如果不满足需求，回来 P1 说明具体不满足的点
- 我们再决定是改进现有 skill 还是做新 skill"**

**若你确实要做**：Pattern 5 允许同领域多个合伙人各做各的独立 skill，只要触发词精确度分级 + 通过 P7 触发词冲突预检即可。

### 情况 D · 不该做——这不是 skill 该解决的

如果用户意图更适合"课程"、"1v1 咨询"、"手册"等形态：

→ 输出：**"你描述的场景更适合 {alternative_form}，而不是 skill。skill 适合可复用的判断流程 / 决策路径 / 结构化产出。你的场景更需要个性化教学。"**

---

## 三、如果决定要做，输出以下确认单

```
╭─ P1 意图澄清 完成 ──────────────────────────╮
│ 📋 痛点：{user_pain_point}
│ 🎯 目标场景：{target_scenario}
│ 💡 核心机制：{core_mechanism}
│ 🌐 领域：{domain}
│ 🏷 建议 skill 名：{partner_slug}-{suggested_name}
│ 🎯 建议触发词覆盖场景：{trigger_scope}
│ 🏅 AFP-SPEC 合规目标：{bronze | silver | gold}（默认 silver）
│ 🔖 命名空间前缀：{yiping- | xuejun- | qingni- | afp-shared- | afp- | <partner_slug>- | 未授权}
│ 🧩 skill_type 预判：{independent | orchestrator | shared_primitive}（正式判定在 P2）
│ ✅ 决定：可以做（进入 P2 架构决策）
│ 👉 NEXT：输入 "Next" 进入架构决策 P2
╰──────────────────────────────────────────╯
```

---

## 四、隐性技术钩子（合伙人级用户看得到）

如果本 skill 的用户是**已经很熟悉 skill 开发的合伙人**，可以在 P1 结束前顺带提示：

- "你这个 skill 目标场景听起来可能会调用到 AFP Shared Primitive 里的 X（如 `afp-shared-cnki-search`）。P4 结构设计时会明确调用协议"
- "你这个 skill 触发词有可能和 `{existing-skill}` 冲突。P5 Frontmatter 撰写时会做触发词隔离 + 精确度分级"
- "你这个 skill 类型看起来是 Independent / Orchestrator / Shared Primitive 中的 X（Pattern 5 三选一）。P2 架构决策时会正式判定"
- "你的命名空间前缀应该是 `{partner_slug}-*`（如 `yiping-*` / `xuejun-*` / `qingni-*`）。若未定，请在 P1 末尾确认"

**这些提示让熟悉的用户提前预判问题**。

---

## 五、AFP-SPEC 早期锚定 + 命名空间前缀确认（Pattern 5 强制）

### 5.1 AFP-SPEC 合规等级

在 P1 结束前，让用户先决定：

**这个 skill 你希望是 Bronze / Silver / Gold 哪一级？**

- **Bronze**（最低）：只做 Hard Stops + Evidence Chain
  - 适合：探索期、内部试用、单人开发、暂不进入 AFP-ecosystem
- **Silver**（推荐大多数）：Bronze + Output Structure Schema
  - 适合：正式贡献到 AFP-ecosystem、合伙人自治命名空间下的 Independent / Orchestrator
- **Gold**（最高）：Silver + Multi-agent Handoff + 测试套件通过
  - 适合：作为 Shared Primitive（`afp-shared-*`）贡献、跨合伙人 skill 反复复用

**这个决定影响 P8 合规检查的严格度**。默认 Silver。

### 5.2 命名空间前缀确认（Pattern 5 强制）

同时确认你的命名空间前缀：

- `yiping-*` / `xuejun-*` / `qingni-*` / `<your_slug>-*` → 你已获合伙人授权
- `afp-shared-*` / `afp-*` → 需 Steering Committee 审议
- **未获授权** → 先走 Bronze 独立开发，不进入 AFP-ecosystem

**若你尚未加入 AFP 合伙人计划**：可以先走 Bronze 独立开发，未来加入合伙人计划时再迁移到 AFP-ecosystem。

---

## 六、Hard Stop

**P1 完成后必须等待用户 `Next` 确认才推进 P2**。

即使意图非常明确，也不允许自动进入 P2——这是本 skill 自身遵循 AFP-SPEC §5 Hard Stop Protocol 的示范。

---

*P1 完成后，主控加载 stages/02-architecture-decision.md*
