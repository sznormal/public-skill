# P2 · 架构决策（Pattern 5 版）

> AFP Skill Creator · Stage 02
> 目的：帮用户判断要做的 skill 属于三种类型之一——Independent / Orchestrator / Shared Primitive

---

## 一、Pattern 5 架构总览

AFP-ecosystem 采用 **Pattern 5 · Orchestrated Independent Collection**：

- **每个 skill 都是顶层可独立触发的 first-class 单元**（都在 `~/.claude/skills/` 目录直接下）
- **每个 skill 命名必须带命名空间前缀**（`yiping-*` / `xuejun-*` / `qingni-*` / `afp-shared-*` / `afp-*`）
- **每次调用都是独立事件**，积分精确记账到 skill ID

在这个框架下，你要做的 skill 只可能属于三种类型之一：

| 类型 | 定位 | 例子 |
|---|---|---|
| **Independent** | 独立可触发的单点能力 | `yiping-literature-review` / `xuejun-thematic-analysis` |
| **Orchestrator** | 引导用户走完流程的总控 | `yiping-phd-orchestrator` / `qingni-framework-cn-navigator` |
| **Shared Primitive** | 贡献到共同体资产层的通用能力 | `afp-shared-cnki-search` / `afp-shared-review-theater` |

---

## 二、三选一判定树

### 分支 1 · 你的 skill 会引导用户走多个阶段吗？

**Yes**（会引导用户走 P1 → P2 → P3 → … 多个阶段，每个阶段可能触发不同的独立 skill）
→ **Orchestrator**（跳到 §三 Orchestrator 详情）

**No**（只处理一个明确的单点任务）
→ 继续问分支 2

### 分支 2 · 你的能力会被其他合伙人的 skill 反复复用吗？

**Yes**（是一种通用的原子能力，比如 CNKI 检索、DOI 校验、四审剧场深化）
→ **Shared Primitive**（跳到 §五 Shared Primitive 详情）

**No**（是你自己命名空间下的领域独立能力，主要面向终端用户）
→ **Independent**（跳到 §四 Independent 详情）

### 判定树可视化

```
你的 skill 会引导用户走多个阶段吗？
├── Yes → Orchestrator
└── No → 你的能力会被其他合伙人 skill 反复复用吗？
         ├── Yes → Shared Primitive
         └── No → Independent（默认）
```

**默认推荐**：如果不确定，选 **Independent**——这是 Pattern 5 下最常见、门槛最低、覆盖最广的类型。

---

## 三、Orchestrator 详情

### 定位

Orchestrator 是**引导者**，不是**执行者**。它的核心工作：
1. 识别用户的当前意图和阶段
2. 维护跨阶段的状态（HUD）
3. 完成一个阶段后，**通过分段引导话术把用户"交接"给下一个独立 skill**
4. 提供备用直击提示：如果用户不想走全流程，告诉他"可以直接触发 xxx skill"

### Orchestrator 不做的事

**Orchestrator 最容易犯的反模式是"侵占子 skill 能力"**——把本该独立 skill 承担的业务逻辑塞进 orchestrator 主控里。

正确边界：
- ✅ Orchestrator 做：路由 + 状态传递 + 分段引导话术 + 备用直击提示
- ❌ Orchestrator 不做：具体业务逻辑（如"如何写文献综述的漏斗结构"——这是 `yiping-literature-review` 的事）

**如果 Orchestrator 塞入太多具体逻辑**：
1. 主控 SKILL.md 会变得又厚又重（违反渐进披露）
2. 子独立 skill 会失去被独立触发的价值
3. 积分记账会失衡（Orchestrator 吃掉子 skill 的调用点）

### Orchestrator 骨架

参考 `templates/orchestrator-template.md` 里的 orchestrator 骨架模板，核心结构：

```markdown
## 一、状态管理骨架（HUD）
## 二、阶段路由表 · Pattern 5 分段引导
    | 当前阶段 | 完成后引导话术 | 用户触发的独立 skill |
## 三、状态跨 skill 传递（磁盘持久化）
## 四、备用直击提示（用户可跳过 orchestrator 直接触发独立 skill）
## 五、Shared Primitive 复用
```

### Orchestrator 命名规则

`<partner>-<domain>-orchestrator`

例：
- `yiping-phd-orchestrator`
- `xuejun-journal-orchestrator`
- `qingni-framework-cn-navigator`（navigator 是 orchestrator 的别名，学术志青泥体系用 navigator）

### Orchestrator 触发词特征

- 全流程宽口令：`帮我写博士论文` / `开始博论一条龙`
- **精确单点口令交给对应 Independent skill**（避免抢触发权）

---

## 四、Independent 详情

### 定位

Independent 是**单点任务执行者**：
- 承担一个明确的、可交付的、可独立完成的任务
- 用户可以直接触发（说精确任务口令）
- 也可以被 Orchestrator 分段引导后触发

### Independent 的典型场景

| 学术领域 | 咨询领域 | 医疗领域 |
|---|---|---|
| 文献综述写作 | SCQA 报告框架 | 病例分析 |
| 理论框架建构 | 假设树拆解 | 循证综述 |
| 方法论撰写 | 尽调报告 | 临床指南 |
| 实证分析 | 提案设计 | 医学统计 |
| 结论写作 | 路演材料 | ... |
| 答辩准备 | 案例研究 | ... |

### Independent 骨架

参考 `templates/independent-skill-template.md` 里的独立 skill 骨架，核心结构：

```markdown
## 一、frontmatter（含 partner / skill_type / afp_spec_target）
## 二、状态管理（本 skill 内部 HUD，不跨 skill）
## 三、分阶段引导（可选：如果任务复杂到需要多步 Hard Stop）
## 四、Shared Primitive 调用清单（Read on demand）
## 五、AFP-SPEC 合规检查（Hard Stop / Evidence Chain / Output Structure）
## 六、跨 skill 状态传递（如果需要接受 orchestrator 传入的状态 或 传递给下一个 skill）
```

### Independent 命名规则

`<partner>-<specific-task>`

例：
- `yiping-literature-review`
- `xuejun-thematic-analysis`
- `qingni-quant-modeling`

### Independent 触发词特征

- 精确单点口令：`帮我做文献综述部分` / `分析这份问卷`
- **避免全流程口令**（避免抢 Orchestrator 触发权）
- 明确"触发隔离"：用户处理其他阶段请触发对应独立 skill

---

## 五、Shared Primitive 详情

### 定位

Shared Primitive 是**共同体资产**：
- 是一种可被跨合伙人 skill 反复复用的原子能力
- 归属**AFP 行动派共同体**（不属于个人合伙人）
- 上架需 **Steering Committee 审议**
- 享受 **2x 复用积分奖励**——被其他 skill 内嵌 Read 时按 2 点记

### Shared Primitive 的典型场景

| 类别 | 例子 |
|---|---|
| **原子能力** | CNKI 检索 / 外文检索 / DOI 校验 / 引用格式化 |
| **通用方法论** | 四审剧场（学君原创）/ 考古发掘 / 莫比乌斯环 / 抗压缩协议（一平原创）/ 断点续传 |
| **协议校验** | AFP-SPEC 合规验证 / 触发词冲突预检 |
| **状态协议** | 跨 skill 状态传递 / 上下文压缩恢复 |

### Shared Primitive 的双重身份

Shared Primitive **既能被独立 skill 内嵌 Read**（复用），**也能被用户直接触发**（作为独立 skill）：

- 被独立 skill 内嵌 Read → **2 点复用积分**
- 被用户直接触发 → **1 点普通独立积分**

### Shared Primitive 骨架

结构接近 Independent，但要额外说明**复用协议**：

```markdown
## 一、frontmatter（partner: afp / skill_type: shared_primitive）
## 二、能力边界（这个 primitive 能做什么，不能做什么）
## 三、独立触发模式（当用户直接触发时的行为）
## 四、内嵌调用模式（当被其他 skill Read 时的行为）
## 五、调用契约（输入格式 / 输出格式 / 状态影响）
## 六、AFP-SPEC 合规（Gold 级最低门槛）
```

### Shared Primitive 命名规则

`afp-shared-<capability>`

例：
- `afp-shared-cnki-search`
- `afp-shared-review-theater`
- `afp-shared-continuation`

### Shared Primitive 上架流程（比其他类型更严格）

1. **合伙人自开发**：先在自己命名空间下做出可用版本（`yiping-review-theater`）
2. **提交 Steering Committee 审议**：填写贡献申请（能力描述 + 通用性论证 + 与已有 primitive 的关系）
3. **Committee 审议要点**：
   - 通用性：是否真的能被跨合伙人反复复用（不是特定领域的私有能力）
   - 独特性：是否与已有 primitive 重复
   - 质量：是否达到 AFP-SPEC Gold 级
   - 命名：是否与已有 primitive 冲突
4. **通过后授予 `afp-shared-*` 命名空间**：合伙人的原独立 skill 保留，同时创建 `afp-shared-*` 副本
5. **积分归属保留给贡献者**：终身署名 + 分成（虽然归属共同体，但积分记账仍归贡献者）

---

## 六、类型转换与升级路径

### Independent → Shared Primitive（升级）

如果你的 Independent skill 被越来越多其他合伙人复用（内嵌 Read 或 Committee 观察到复用请求）——
你可以主动申请**升级为 Shared Primitive**，享受 2x 复用积分。

升级动作：
1. 在你的命名空间下保留原 Independent skill（不删除）
2. 提交 Committee 审议，通过后授予 `afp-shared-*` 命名空间副本
3. 后续两个版本并存——用户既能触发 `<partner>-<skill>`（1 点）也能通过其他 skill 复用 `afp-shared-<capability>`（2 点）

### 多个 Independent → Orchestrator（成组）

如果你在自己命名空间下做了 3 个以上相关的 Independent skill（如 `yiping-phd-topic` / `yiping-phd-literature` / `yiping-phd-methodology` / ...），
你可以再做一个 Orchestrator（`yiping-phd-orchestrator`）来引导用户走完整全流程。

**Orchestrator 不会抢走 Independent 的调用积分**——它俩是并行的 first-class：
- 用户直击 Independent → Independent 得点
- 用户走 Orchestrator → Orchestrator 得点 + 引导后触发的 Independent 也得点

---

## 七、Hard Stop · 交付确认单

```
╭─ P2 架构决策 完成 ────────────────────────────────╮
│ 🧩 skill_type: {independent | orchestrator | shared_primitive}
│ 📄 判定依据：{分支 1 答案} / {分支 2 答案}
│ 🎯 你的 skill 角色：{ONE-LINE 描述}
│ 📋 命名规则建议：{partner}-<name>
│ 🔗 相关文档：
│    - Independent → 参考 templates/independent-skill-template.md
│    - Orchestrator → 参考 templates/orchestrator-template.md
│    - Shared Primitive → 需 Steering Committee 审议流程
│ 👉 NEXT：输入 "Next" 进入 P3 方法论来源确认
╰────────────────────────────────────────────────╯
```

---

## 八、反模式警告

架构决策阶段常见错误：

- ❌ **把 Orchestrator 当 Independent 做**：只考虑一个阶段的能力，但用户实际期望是全流程引导——会导致用户体验断裂
- ❌ **把 Independent 当 Orchestrator 做**：明明只是单点任务，却塞入大量分段引导话术——违反渐进披露
- ❌ **随便申请 Shared Primitive**：未经 Committee 审议就用 `afp-shared-*` 命名——上架会被拒
- ❌ **想做"大而全的 Bundle"**：Pattern 5 下没有 Bundle 这个概念，想做全流程请做 Orchestrator + 一组 Independent
- ❌ **Independent 触发词太宽**：抢占 Orchestrator 触发权，导致用户走单点想要全流程

---

*P2 完成后，主控加载 stages/03-methodology-source.md*
