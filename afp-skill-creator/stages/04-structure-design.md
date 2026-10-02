# P4 · 结构设计（Pattern 5 版）

> AFP Skill Creator · Stage 04
> 目的：帮用户设计单个 skill 的内部结构——文件组织 + Shared Primitive 调用协议 + 状态传递机制

---

## 一、Pattern 5 下的单 skill 内部结构

Pattern 5 强调**每个 skill 是顶层可独立触发的单元**，所以每个 skill 都有自己独立的目录：

```
~/.claude/skills/<partner>-<skill-name>/
├── SKILL.md                          ← 必须·主入口·薄路由（2000-2500 token）
├── stages/                           ← 可选·局部展开（仅在任务复杂需要分阶段时）
│   ├── p1-xxx.md
│   ├── p2-xxx.md
│   └── ...
├── modules/                          ← 可选·本地按需模块（不共享）
│   ├── module-a.md
│   └── module-b.md
├── templates/                        ← 可选·复用模板
│   └── output-template.md
└── README.md                         ← 可选·使用说明
```

**关键原则**：

1. **SKILL.md 是唯一有 frontmatter 的文件**——所有子文档都是纯 markdown，无 frontmatter
2. **SKILL.md 是薄路由**——只做状态骨架 + 阶段路由 + 通用指令，具体业务逻辑放 `stages/` 或 `modules/`
3. **`stages/` 是局部展开**——只在 skill 内部使用，不能被外部触发（Claude Code 不递归扫描）
4. **`modules/` 是本地按需模块**——只在 skill 内部按需 Read，不是跨 skill 共享
5. **跨 skill 共享的能力**放在 `afp-shared-*` 里，不能放在自己的 `modules/`

---

## 二、三种 skill 类型的内部结构差异

### 2.1 Independent skill 结构

```
yiping-literature-review/
├── SKILL.md                              薄路由（含 frontmatter · Pattern 5 五段）
├── stages/                                任务分阶段（可选，只在综述写作复杂到需要分阶段时）
│   ├── p1-topic-parsing.md               主题解析
│   ├── p2-source-planning.md             五源检索规划
│   ├── p3-funnel-structuring.md          漏斗结构
│   ├── p4-gap-identification.md          研究缺口识别
│   ├── p5-writing.md                     写作
│   └── p6-self-audit.md                  自审
└── modules/
    ├── funnel-template.md                漏斗模板
    ├── discipline-branches.md            学科分支（社科 / 理工 / 医护 / 人文）
    └── citation-format.md                引用格式（本地版；也可 Read afp-shared-citation-format）
```

**判断要点**：
- 如果任务简单（单次交互 3-5 轮就能完成）→ 不需要 `stages/`，SKILL.md 内直接写引导逻辑
- 如果任务复杂（需要多个 Hard Stop 阶段）→ 用 `stages/` 展开
- 如果有可能复用给其他 skill 的能力 → 提交 Committee 升级为 `afp-shared-*`（不要放在自己的 `modules/`）

### 2.2 Orchestrator skill 结构

```
yiping-phd-orchestrator/
├── SKILL.md                              薄路由（含 orchestrator 分段引导表）
├── stages/                                orchestrator 内部阶段（可选）
│   ├── p0-user-onboarding.md             初次上手引导
│   ├── p1-status-detection.md            识别用户当前状态
│   ├── p2-handoff-planning.md            规划分段引导
│   └── p3-progress-review.md             跨阶段进度审视
└── modules/
    ├── handoff-phrases.md                分段引导话术库
    ├── state-persistence-format.md       状态磁盘持久化格式
    └── downstream-skill-map.md           下游独立 skill 映射表
```

**判断要点**：
- Orchestrator 的 `stages/` 通常比 Independent 少（因为 Orchestrator 不做业务）
- **不要在 Orchestrator 里塞下游 skill 的业务逻辑**——违反 Pattern 5 反模式 21
- **状态持久化**是 Orchestrator 的核心职责——必须设计跨 skill 的状态文件格式

### 2.3 Shared Primitive skill 结构

```
afp-shared-cnki-search/
├── SKILL.md                              薄路由（含双重身份说明：独立触发 + 内嵌复用）
├── stages/                                可选
│   ├── p1-query-planning.md              检索式规划
│   ├── p2-boolean-construction.md        布尔式构造
│   └── p3-result-consolidation.md        结果合并
├── modules/
│   ├── contract-schema.md                调用契约（输入 / 输出格式）
│   ├── discipline-adapters.md            学科适配器
│   └── error-handling.md                 错误处理
└── README.md                             使用说明（其他合伙人参考如何 Read 内嵌调用）
```

**判断要点**：
- **必须有明确的调用契约**（输入格式 / 输出格式 / 状态影响）——其他 skill Read 时依赖这个契约
- **必须支持双重身份**（既能独立触发也能内嵌调用）——设计时考虑两种入口的差异
- **文档要严格**——因为会被跨合伙人反复使用，任何模糊都会造成整个 ecosystem 的问题

---

## 三、SKILL.md 主入口的通用骨架（1500-2500 token）

不管三种类型哪一种，SKILL.md 都遵循这个通用结构：

```markdown
---
（frontmatter · 见 P5 详细设计）
---

# {skill 全称}

（一句话定位 · 30 字内）

## 一、核心设计理念（3-5 条）

（this skill 遵循什么原则）

## 二、全局状态管理（HUD）

```json
{ 状态骨架 JSON · 200-300 token }
```

## 三、阶段路由 / 触发意图路由

（用户口令 → 加载哪个 stage 或 module）

## 四、按需模块调用

（用户特殊指令 → Read 哪个 module）

## 五、Shared Primitive 复用清单

（本 skill 会 Read 哪些 afp-shared-*·记账时享受复用积分）

## 六、首次上手引导（100-200 token）

（简短的用户引导话术）

## 七、通用指令表（100 token）

（Next / Back / Edit / Skip / Export / Continue / Status / ...）

## 八、断点续传（跨对话抗压缩）

- 每阶段完成后写入 {project_path}/{skill_name}-state.md
- 用户新对话说 Continue {project_path} → 从磁盘恢复状态

## 九、Hard Stop 输出规范

（统一的状态确认框格式）

## 十、反模式警告（内嵌 8-10 条精选）

（完整清单见 modules/skill-anti-patterns.md）

## 十一、AFP-SPEC 合规目标

（bronze / silver / gold）

## 十二、维护者与版本
```

---

## 四、Shared Primitive 调用协议（Pattern 5 核心机制）

### 4.1 内嵌 Read 复用（最常见）

在自己的 SKILL.md 或 stage 里，明确 Read `afp-shared-*`：

```markdown
## 五、Shared Primitive 复用清单

本 skill 会在必要时 Read 以下 AFP shared primitives：

| Primitive | 用途 | 触发时机 |
|---|---|---|
| `afp-shared-cnki-search` | 知网检索 | P2 · 检索规划阶段 |
| `afp-shared-foreign-lit` | 外文检索 | P2 · 检索规划阶段（英文文献时）|
| `afp-shared-review-theater` | 四审剧场深化 | P5 · 写作后自审 |
| `afp-shared-citation-format` | 引用格式化 | P6 · 最终输出 |
```

**记账机制**：
- 你 Read `afp-shared-cnki-search` → 该 primitive 归属贡献者获得 **2 积分点**
- 你的 skill 本身被触发 → 你获得 **1 积分点**
- 两者独立计算，不冲突

### 4.2 调用契约（Shared Primitive 的规范）

每个 Shared Primitive 都必须有明确的调用契约，包括：

```markdown
## 调用契约

### 输入格式
- 参数 1：{name} = {type} · {description}
- 参数 2：...

### 输出格式
- 返回：{schema}

### 状态影响
- 本 primitive 不修改调用方的 HUD
- 本 primitive 只写自己命名空间下的临时文件

### 错误处理
- 输入格式错误 → 返回 error 结构，调用方决定如何处理
- 网络失败 → 自动重试 3 次，然后返回 error
```

**调用方（你的 skill）应该**：
1. 检查调用契约版本（防止 primitive 升级导致的 breaking change）
2. 按契约传参
3. 按契约解析返回
4. 按契约处理错误

### 4.3 Shared Primitive 命名与查询

在 P4 结构设计阶段，用户应该已经从 AFP-ecosystem 里查过：

- 我要用的能力是否已经存在 Shared Primitive？
- 如果存在 → 直接 Read 复用
- 如果不存在 → 是自己做一份（本地 `modules/`）还是提议新增 Shared Primitive？

**Committee 建议**：
- 短期只自己用 → 放本地 `modules/`
- 中期看有 3+ 合伙人可能用 → 提议新增 `afp-shared-*`
- **不要频繁提议新 Shared Primitive**——避免共同体资产层膨胀

---

## 五、跨 skill 状态传递（Pattern 5 关键机制）

Pattern 5 下 skill 之间**没有共享内存**——状态必须通过**磁盘持久化 + orchestrator 中介**传递。

### 5.1 磁盘持久化格式

约定统一的项目状态目录：

```
~/{project_path}/
├── {project_name}-state.md            全局状态（Orchestrator 维护）
├── stage-outputs/
│   ├── p1-topic.md                     每个 stage 的输出
│   ├── p2-literature-review.md
│   ├── p3-methodology.md
│   └── ...
└── conversation-log/
    ├── session-2026-07-05.md           每次对话的关键决策
    └── ...
```

### 5.2 状态传递协议

**Orchestrator 主导模式**：
1. Orchestrator 触发时先 Read `{project_path}/{project_name}-state.md`
2. 引导用户完成当前阶段，产出写入 `stage-outputs/{p-N}-{name}.md`
3. 更新全局状态
4. 分段引导话术告诉用户"请对我说'开始 P{N+1}'触发下一步"
5. Claude 加载下一个独立 skill
6. 下一个独立 skill 触发时先 Read 全局状态，续跑

**Independent 独立模式**：
1. 用户直接触发 Independent skill（不经过 Orchestrator）
2. Independent skill 检查 `{project_path}/` 是否存在状态文件
3. 存在 → 载入状态续跑；不存在 → 从零开始
4. 完成后写入自己的 stage-output 文件

### 5.3 复用 afp-shared-continuation

跨 skill 状态传递本身是一个通用能力——不要每个 skill 自己实现磁盘读写协议，而是 Read `afp-shared-continuation` 来处理：

```markdown
## 六、跨 skill 状态传递（Read afp-shared-continuation）

本 skill 通过 afp-shared-continuation 处理状态：
- 启动时 Read afp-shared-continuation 加载协议
- 完成阶段后调用协议里的 write_stage_output()
- 结束时调用协议里的 update_global_state()
```

---

## 六、内部 stages/ 和 modules/ 的边界

一个常见困惑：**什么放 stages/，什么放 modules/？**

| 判断标准 | stages/ | modules/ |
|---|---|---|
| **是任务的时序阶段吗？** | ✅ 是（P1 → P2 → P3 → …）| ❌ 不是（按需触发）|
| **有 Hard Stop 吗？** | ✅ 有 | ❌ 无 |
| **状态会更新 HUD 吗？** | ✅ 会 | 一般不会 |
| **顺序性？** | ✅ 有顺序 | ❌ 无顺序 |
| **例子** | P1 主题解析 / P2 检索规划 / ... | 学科分支 / 温度调控 / 反模式清单 |

**规则**：
- 时序性、有 Hard Stop、按顺序推进 → `stages/`
- 无序、按需 Read、辅助性内容 → `modules/`

### 独家语料挂载规则（P3 收集的语料放哪）

P3 显性化五问收集到的独家语料（90 分样例 / 反面样例 / 话术库 / 评审意见），按形态挂载：

| 语料形态 | 挂载位置 | 说明 |
|---|---|---|
| 样例、案例、话术、评审意见 | `modules/exemplars.md` | 分节存放：**90 分样例 / 反面样例 / 话术库**；每则标注来源与脱敏状态 |
| 成型可复用的范文骨架 / 空白表格 | `templates/` | 用户直接往里填的格式化模板 |

三条纪律：
1. **exemplars 是按需模块**——只在产出类 stage 生成前 Read 作 few-shot 参照（P6 落实），不进主控、不全程加载
2. **反面样例同样值钱**——被打回的稿子 + 打回理由，直接喂给对应 stage 的反模式清单
3. **语料必须落盘**——散落在开发对话里的经验，换个对话就没了

---

## 七、Hard Stop · 交付确认单

```
╭─ P4 结构设计 完成 ────────────────────────────────╮
│ 📁 skill 目录：~/.claude/skills/{name}/
│ 📄 SKILL.md 主入口：{✅ 计划创建 | 已有}
│ 🎬 stages/ 目录：{✅ 规划 N 个阶段 | 无 stages}
│ 🧩 modules/ 目录：{✅ 规划 N 个模块 | 无 modules}
│ 📦 独家语料挂载：{✅ modules/exemplars.md（N 则）+ templates/（N 份）| 无语料}
│ 📋 templates/ 目录：{✅ N 个模板 | 无 templates}
│ 📚 README.md：{✅ 计划创建 | 跳过}
│ 
│ 🔗 Shared Primitive 调用清单（{N} 个）：
│   - {primitive-1}：{用途} · {触发时机}
│   - {primitive-2}：...
│ 
│ 💾 跨 skill 状态传递：
│   {✅ Read afp-shared-continuation | ❌ 单 skill 无需跨传}
│ 
│ 👉 NEXT：输入 "Next" 进入 P5 Frontmatter 撰写
╰────────────────────────────────────────────────╯
```

---

## 八、反模式警告

结构设计常见错误：

- ❌ **SKILL.md 塞满所有内容**（违反渐进披露 / 违反薄路由 pattern）
- ❌ **子文档写 frontmatter**（死代码，浪费 token）
- ❌ **stages/ 里的内容和 modules/ 混淆**（顺序性与按需性搞错）
- ❌ **重复实现 Shared Primitive 能力**（自己的 `modules/` 里造 CNKI 检索的轮子）
- ❌ **状态传递不用磁盘持久化**（跨对话 / 跨 skill 时状态丢失）
- ❌ **忽略 afp-shared-continuation**（每个 skill 自己实现磁盘读写协议——重复劳动）
- ❌ **Orchestrator 在 stages/ 里塞子 skill 业务**（Pattern 5 反模式 21）
- ❌ **Independent 强行搞多个 stages/**（简单任务硬拆成多阶段——违反 KISS）
- ❌ **Shared Primitive 没有明确调用契约**（其他 skill 无法可靠复用）
- ❌ **独家语料不落盘**（P3 收集的样例散落在对话里——换个对话经验就丢，必须挂进 exemplars.md 或 templates/）
- ❌ **语料未脱敏就挂载**（客户 / 学生真实信息直接进 skill 文件——上架即泄密）

---

*P4 完成后，主控加载 stages/05-frontmatter-writing.md*
