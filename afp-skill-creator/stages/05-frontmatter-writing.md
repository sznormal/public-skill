# P5 · Frontmatter 撰写（Pattern 5 版）

> AFP Skill Creator · Stage 05
> 目的：写出 Pattern 5 合规的 frontmatter——让 Claude 系统能识别、能触发、不冲突、能被 AFP-ecosystem 后台正确记账

---

## 一、Frontmatter 的四层作用（Pattern 5 定型后）

`frontmatter` 是 SKILL.md 顶部的 YAML 块，决定：

1. **系统识别**：Claude 是否把这个文件当作独立可触发的 skill
2. **触发匹配**：用户口令怎么和这个 skill 关联
3. **归属与治理**：命名空间前缀 + 合伙人 slug → AFP-ecosystem 积分记账
4. **合规等级**：AFP-SPEC bronze / silver / gold 分级

**核心规则**：

- 顶层 SKILL.md 必须有 frontmatter
- 独立 skill 的子文档（stages/*.md / modules/*.md）**不写 frontmatter**——Claude Code 只扫描顶层一层
- Pattern 5 下**每个想独立触发的 skill 都要放在顶层**（`~/.claude/skills/<skill-name>/SKILL.md`），不能藏在子目录

---

## 二、Frontmatter 五大字段设计（Pattern 5 标准）

### 字段 1 · `name`（含命名空间前缀）

Pattern 5 下命名必须遵守 **`<partner>-<skill>` 或 `<partner>-<category>-<skill>`** 格式：

```yaml
name: yiping-literature-review
name: xuejun-thematic-analysis
name: qingni-framework-cn-navigator
name: afp-shared-cnki-search
name: afp-master-orchestrator
```

**命名空间前缀规则**：

| 前缀 | 用途 | 授权 |
|---|---|---|
| `yiping-*` | 一平贡献 | 一平自治 |
| `xuejun-*` | 学君贡献 | 学君自治 |
| `qingni-*` | 学术志研发/青泥官方 | 学术志研发团队 |
| `afp-shared-*` | 共同体 Shared Primitive | **Steering Committee 审议** |
| `afp-*` | AFP 官方总控 / 校验器 | **Steering Committee 审议** |
| `<partner_slug>-*` | 其他合伙人 | 合伙人加入时 Committee 授予 |

**反模式**：
- ❌ 无前缀：`literature-review`（会与其他合伙人抢命名）
- ❌ 错前缀：`yiping-shared-*`（`shared-*` 仅限 `afp-shared-*`）
- ❌ 过于笼统：`yiping-helper` / `yiping-assistant`（不描述能力）
- ❌ 未获授权：私自用 `afp-shared-*` 前缀（会被 Committee 拒绝上架）

### 字段 2 · `description`（**触发的灵魂**）

保留原来的三段设计：

#### 段 1 · 一句话定义

> "帮助博士生 / 青年教师完成博士论文文献综述章节。采用漏斗结构 + 五源检索 + 研究缺口识别，符合 AFP-SPEC Silver 合规。"

#### 段 2 · 触发词全覆盖列表

```
【触发词覆盖】：帮我写文献综述 / 综述怎么写 / 综述框架 / 文献回顾怎么做 /
              我要做文献回顾 / 文献梳理 / 文献述评 / 研究现状怎么梳理 /
              文献法 / 帮我梳理相关文献 / 博士论文综述章 / literature review
```

**Pattern 5 下触发词精确度分级原则**：

| skill 类型 | 触发词精确度 |
|---|---|
| **Orchestrator** | 宽泛（全流程口令）："帮我写博士论文" / "开始博论" |
| **Independent** | 精确（单点任务口令）："帮我做文献综述部分" / "分析这份问卷" |
| **Shared Primitive** | 内部触发为主（一般不直接暴露给用户，被其他 skill 内嵌调用） |

**同一合伙人内**：Orchestrator 和 Independent 触发词语义正交，不会冲突
**跨合伙人**：由 Steering Committee 审议保证不撞车

#### 段 3 · 触发词隔离说明

明确本 skill **不触发**的场景，防止误触：

```
【触发隔离】：只处理"文献综述写作"这一独立任务。用户处理其他阶段
            （选题 / 理论框架 / 方法论 / 实证分析 / 结论）时请直接
            触发对应的独立 skill——本 skill 不代替。
            用户询问文献推荐、跑数据分析、写导读等其他任务时，本 skill 不触发。
```

### 字段 3 · `agent_created`

- 表示是否由 AI agent 自主创建（`true` / `false`）
- AFP 行动派贡献者身份默认 `true`——象征"agent 型 IP 的产物"

### 字段 4 · `partner`（**Pattern 5 新增 · 必填**）

合伙人 slug，用于 AFP-ecosystem 后台积分归属：

```yaml
partner: yiping
partner: xuejun
partner: qingni
partner: afp
partner: <你的合伙人 slug>
```

**规则**：
- `partner` 值必须与 `name` 的前缀一致（如 `name: yiping-*` 则 `partner: yiping`）
- `partner` 是积分记账的直接归属键——后台 GROUP BY partner 就能算出每个合伙人的月度积分
- `afp` 类型的 skill 归属"共同体池"（用于运营/共建激励）

### 字段 5 · `skill_type`（**Pattern 5 新增 · 必填**）

三选一：

```yaml
skill_type: independent          # 独立可触发的单点 skill（默认）
skill_type: orchestrator         # 引导用户走完流程的总控
skill_type: shared_primitive     # 贡献到共同体资产层的通用能力
```

**规则**：
- `independent`：默认类型，每次触发 = 1 积分点
- `orchestrator`：不代替独立 skill 的能力，只做分段引导；每次触发 = 1 积分点
- `shared_primitive`：可被其他 skill 内嵌 Read 复用；**被复用时 = 2 积分点**，被用户直接触发时 = 1 积分点

### 字段 6 · `afp_spec_target`（**Pattern 5 新增 · 建议填**）

AFP-SPEC 合规目标等级：

```yaml
afp_spec_target: bronze          # 个人使用 / 教学 / 探索期
afp_spec_target: silver          # 正式贡献 AFP-ecosystem 的推荐等级
afp_spec_target: gold            # 官方推荐层 / Shared Primitive 层的最低门槛
```

**说明**：
- `bronze` → 允许进入 AFP-ecosystem，享受基础分成
- `silver` → 允许被列入"官方推荐" skill 首页曝光位（隐性激励）
- `gold` → 允许贡献到 `afp-shared-*` 层（享受复用 2x 高单价通道）

---

## 三、标准 Frontmatter 模板（Pattern 5 定型版）

### 3.1 Independent skill 模板

```yaml
---
name: yiping-literature-review
description: >
  帮助博士生 / 青年教师完成博士论文文献综述章节。采用漏斗结构 +
  五源检索 + 研究缺口识别 + 文献真实性校验，符合 AFP-SPEC Silver 合规。
  【触发词覆盖】：帮我写文献综述 / 综述怎么写 / 综述框架 /
                文献回顾 / 文献梳理 / 文献述评 / 研究现状梳理 /
                博士论文综述章 / literature review
  【触发隔离】：只处理"文献综述写作"这一独立任务。用户处理其他阶段
              请直接触发对应的独立 skill——本 skill 不代替。
              用户询问文献推荐 / 跑数据分析等其他任务时，本 skill 不触发。
agent_created: true
partner: yiping
skill_type: independent
afp_spec_target: silver
---
```

### 3.2 Orchestrator skill 模板

```yaml
---
name: yiping-phd-orchestrator
description: >
  一平博论全流程总控。当用户想走完整博士论文写作流程时触发。
  负责识别用户所在阶段 + 状态跨阶段流转 + 分段引导切换到对应独立 skill。
  【触发词覆盖】：帮我写博士论文 / 开始博论 / 博论一条龙 /
                博士论文怎么写 / 从头写博论 / 博论指导 / 博论全流程
  【触发隔离】：只在"全流程引导"意图时触发。用户想做单点任务
              （文献综述 / 方法论 / 实证分析等）请直接触发对应
              独立 skill——orchestrator 不代替独立 skill 的能力。
agent_created: true
partner: yiping
skill_type: orchestrator
afp_spec_target: silver
---
```

### 3.3 Shared Primitive 模板（需 Steering Committee 审议）

```yaml
---
name: afp-shared-cnki-search
description: >
  知网（CNKI）高级检索能力·跨合伙人 skill 复用。执行三阶段检索
  （主体联合 → 独立补充 → 汇总合并），输出统一 Excel。
  【触发词覆盖】：知网检索 / CNKI 检索 / 高级检索 /
                帮我在知网查 / 学术论文检索 / 文献数据库检索
  【触发隔离】：既可被用户直接触发（作为独立 skill 记 1 点），
              也可被其他 skill 内嵌 Read 复用（记 2 点复用奖励）。
              不处理非 CNKI 数据库检索（外文库请触发 afp-shared-foreign-lit）。
agent_created: true
partner: afp
skill_type: shared_primitive
afp_spec_target: gold
---
```

---

## 四、触发词冲突预检（Pattern 5 强制流程）

在 frontmatter 写完后，本 skill 会做一次**触发词冲突预检**：

### Step 1 · 收集你的触发词清单

从 description 段 2 里提取所有触发词，形成清单。

### Step 2 · 与 AFP-ecosystem 现有 skill 求交集

自动扫描 `~/.claude/skills/` 下所有已有 skill 的 description，识别可能触发词重叠的 skill：

- 命名空间前缀不同但触发词重叠 → **需要 Committee 仲裁**
- 命名空间前缀相同（同合伙人内）触发词重叠 → **合伙人自己调整**（比如 yiping-orchestrator 和 yiping-independent 之间的分工）

### Step 3 · 输出冲突预警

```
⚠️ 触发词冲突预警

你的 skill：yiping-literature-review
你的触发词：帮我写文献综述 / 综述怎么写 / 文献梳理 / ...

可能冲突：
─ qingni-framework-cn-navigator 的触发词 "研究现状梳理" 与你的 "研究现状梳理" 重叠
  → 由于两者都是 Independent 类型，需要 Committee 仲裁触发优先权
─ afp-master-orchestrator 的触发词 "帮我写论文" 与你的 "帮我写文献综述" 部分重叠
  → 由于 afp-master-orchestrator 是全流程口令、你是精确单点口令，
     根据"精确度优先"规则，用户说完整口令时优先触发你

建议：
1. 移除 "研究现状梳理" 触发词（改用更精确的 "帮我梳理博士论文相关文献"）
2. 触发词精确度分级：把你的 skill 的触发词都收窄到"博士论文文献综述"具体场景
3. 如果冲突不可调和 → 提交 Steering Committee 审议

预检结果：⚠️ 有可调整冲突，建议修改后再上架
```

### Step 4 · 修改后再检 或 直接进入 Committee 审议

- 如果冲突可自行解决 → 修改 description 后重新预检
- 如果冲突无法自行解决 → 提交 Steering Committee 审议（附冲突分析 + 修改提议）

---

## 五、触发词优先级判定

**Claude 的触发规则**：**更精确的 description 通常优先**。

Pattern 5 下的三级优先级：

| 层 | 精确度 | 触发时机 |
|---|---|---|
| **Shared Primitive**（`afp-shared-*`）| 内部高精确 | 一般不响应用户直接触发；被其他 skill 内嵌调用 |
| **Independent**（`<partner>-<specific>`）| 精确单点 | 用户说精确任务口令时优先触发（"帮我做文献综述"）|
| **Orchestrator**（`<partner>-*-orchestrator`）| 宽泛全流程 | 用户说全流程口令时触发（"帮我写博士论文"）|

**这意味着**：

- Orchestrator 的 description 广义 + 触发词全覆盖全流程
- Independent 的 description 精确到具体任务 + 触发词收窄
- Shared Primitive 的 description 描述能力边界 + 明确"复用为主"

---

## 六、Hard Stop · 交付确认单

```
╭─ P5 Frontmatter 撰写 完成 ────────────────────────╮
│ 📝 name: {name}
│ 🏷️  partner: {partner}
│ 🧩 skill_type: {independent | orchestrator | shared_primitive}
│ 🏅 afp_spec_target: {bronze | silver | gold}
│ 📄 description 段 1（一句话定义）：{summary}
│ 🎯 description 段 2（触发词覆盖 · {N} 个）：{trigger_words}
│ 🚧 description 段 3（触发词隔离）：{isolation_rules}
│ 🤖 agent_created: true
│ ⚠️  触发词冲突预检：{PASS | 需调整 X 项 | 需 Committee 审议}
│ ✅ 命名空间前缀验证：{PASS | FAIL - 原因}
│ 📋 生成的完整 frontmatter yaml：
│ {yaml_block}
│ 
│ 👉 NEXT：输入 "Next" 进入 P6 内容撰写
╰────────────────────────────────────────────────╯
```

---

## 七、反模式警告（Pattern 5 补强）

写 frontmatter 时避免：

**通用反模式**：
- ❌ **name 过于笼统**：`helper` / `assistant` / `tool`
- ❌ **description 过短**：只写一句"帮用户写论文"（触发词太少）
- ❌ **description 过长（超过 800 字）**：Claude 不能有效解析
- ❌ **触发词太广义**：抢占其他 skill 触发权
- ❌ **触发词太窄**：用户找不到触发方法
- ❌ **未做触发隔离**：与相关 skill 冲突
- ❌ **子文档也写 frontmatter**：死代码，浪费 token
- ❌ **描述夸大功能**：与 skill 实际能力不匹配

**Pattern 5 专属反模式**：
- ❌ **命名空间前缀缺失**：`name: literature-review`（应为 `yiping-literature-review`）
- ❌ **前缀与 partner 不匹配**：`name: yiping-*` 但 `partner: xuejun`
- ❌ **私自用受限前缀**：未获 Committee 授权就用 `afp-*` / `afp-shared-*`
- ❌ **skill_type 与实际能力不符**：写 `skill_type: independent` 但实际是 orchestrator 行为（包含大量分段引导）
- ❌ **skip 触发词冲突预检**：跳过 §四 直接上架 → 会被 Committee 打回
- ❌ **Orchestrator 触发词太精确**：Orchestrator 应该覆盖全流程宽口令
- ❌ **Independent 触发词太宽**：抢了 Orchestrator 的全流程口令

---

*P5 完成后，主控加载 stages/06-content-writing.md*
