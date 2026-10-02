# 触发词隔离策略

> AFP Skill Creator · Module
> 源自：一平博论主控原创设计
> 目的：让 skill 之间不打架，让用户找到正确的 skill

---

## 一、为什么需要触发词隔离

当用户机器上装了多个功能相近的 skill 时，说"帮我做文献综述"可能触发多个 skill 之一，Claude 无法确定：

- phd-master（博士论文全流程）
- cn-journal-master（中文期刊全流程）
- literature-review-writer（专门做文献综述）
- 学术志综述 skill（学术志已有）

**没有触发词隔离 = 用户体验灾难**。

---

## 二、隔离的三种设计

### 策略 1 · 精确触发词专用

**为主控 skill 设置"专用触发词"**——只有说这个词才触发主控，否则不触发。

例：一平博论主控的做法：

```yaml
description: >
  当用户明确说"开始博论总控过程"时使用本 skill。
  用户只是说"博士论文选题""写绪论""文献综述""理论框架"等单阶段需求时，
  不自动触发本总控 skill，应按具体任务调用对应子 skill。
```

**优点**：主控和相关 skill 完全不冲突
**代价**：用户必须知道这个专用触发词，无法通过自然口令触发

**适用**：**主控和子 skill 都是独立 skill 时**（Pattern 2）——一平当前博论 skills 家族的形态

### 策略 2 · 触发词全覆盖 + 隔离说明

**主控覆盖所有子场景触发词** + **明确说明什么场景不触发**。

例：AFP-skill-creator 的做法：

```yaml
description: >
  【触发词覆盖】：创建 skill / 做一个 skill / 写 skill / 开发 skill /
                 贡献 skill / 帮我写一个 skill / ...
  【触发隔离】：只在用户明确表达"要创建/做/写/开发/贡献/设计一个 skill"意图时触发。
              用户使用现有 skill 完成任务、询问某个 skill 用法、做非 skill 开发的
              其他工作时，本 skill 不触发。
```

**优点**：用户不需要知道专用触发词，自然口令即可触发
**代价**：description 更长，需要仔细维护
**适用**：**Bundle 模式主控**（Pattern 3）——所有子文档都无 frontmatter，冲突自然消除

### 策略 3 · 精确度分级

**让更精确的 skill 抢占触发权**。

例：
- 广义 skill：`paper-writing-helper`（帮助写论文，触发词广）
- 精确 skill：`social-qualitative-lit-review`（专精社会学质性文献综述）

用户说"帮我做社会学博士论文文献综述"时，Claude 更可能触发精确的那个。

**适用**：广义 skill 和精确 skill 共存 → 精确的抢先触发，广义的兜底

---

## 三、Bundle 模式下触发词隔离的最佳实践

**Bundle 主控只有唯一顶层 SKILL.md**，子文档无 frontmatter → **子文档不会独立触发** → **Bundle 内部无冲突**。

**Bundle 之间的冲突**通过策略 1 / 2 / 3 处理：

- 广义 Bundle（如 phd-master 覆盖博论全流程）→ **触发词全覆盖 + 触发隔离说明**（策略 2）
- 专用 Bundle（如 phd-master 触发词专用于"开始博论总控过程"）→ **精确触发词专用**（策略 1）
- 有精确度差异时 → **让更精确的 Bundle 优先**（策略 3）

---

## 四、AFP-shared-primitives 的触发词隔离

Shared primitives（如 cnki-advanced-search）**不应被用户直接触发**——它们是被 Bundle 调用的基础能力。

因此 shared primitives 的 SKILL.md description 应该：

```yaml
description: >
  AFP-shared-primitives 基础能力：中国知网高级检索。
  【触发词隔离】：本 skill 是 shared primitive，仅供 Bundle 主控通过
  `Read AFP-shared-primitives/cnki-advanced-search.md` 调用。
  **不响应用户的直接触发**——用户想搜文献时应触发对应 Bundle 主控。
```

**这一条隔离说明防止用户直接触发 primitive**。虽然 Claude 未必 100% 遵守，但显式声明会大幅降低误触发概率。

---

## 五、常见错误

### ❌ 错误 1 · 只写正面触发，不写反面隔离

```yaml
description: 帮用户写文献综述
```

问题：Claude 语义匹配范围过宽——用户问"综述有什么好文献"也可能触发。

**修正**：加"触发隔离说明"。

### ❌ 错误 2 · 触发词太少（找不到）

```yaml
description: >
  帮用户写文献综述。触发词：写综述。
```

问题：用户说"帮我做文献回顾""帮我梳理文献"都不会触发。

**修正**：列 8-15 个常见口令变体。

### ❌ 错误 3 · 触发词太广（抢占）

```yaml
description: 任何论文相关问题都可以调用本 skill。
```

问题：抢占其他 skill 触发权，用户体验混乱。

**修正**：明确本 skill 的能力边界。

### ❌ 错误 4 · 隔离过严（触发不了）

```yaml
description: >
  只在用户说"我要按照 xxx 方法论的第三阶段的第二步做文献综述"时触发。
```

问题：触发条件过窄，用户根本不知道怎么触发。

**修正**：主要触发词自然，只在冲突边界处做隔离。

---

## 六、触发词冲突自检清单

在 skill 发布前，运行以下检查：

1. □ 你的触发词列表是否覆盖 8-15 个常见口令？
2. □ 你的触发隔离说明是否明确了"不触发"场景？
3. □ AFP-ecosystem 里有没有其他 skill 会和你抢触发？
4. □ 如果有，你的 skill 更精确还是更广义？
5. □ 你是否明确写了"和 XX skill 的关系"？
6. □ 主控 SKILL.md 覆盖的场景，子文档能否处理全部？
7. □ 你的 skill 是否有可能被误触发在无关场景？

---

## 七、一个成熟的 Bundle 主控 description 模板

```yaml
description: >
  {一句话定义}。{核心方法论概述}。
  
  【触发词覆盖】（12-15 个常见口令，覆盖不同用户表达）：
  {trigger_word_1} / {trigger_word_2} / ... / {trigger_word_N}
  
  【触发词隔离】（明确不触发的场景）：
  只在用户明确表达 {intended_scope} 意图时触发。
  {non_trigger_scenario_1} 时本 skill 不触发。
  {non_trigger_scenario_2} 时本 skill 不触发。
  
  【与其他 skill 的关系】：
  本 skill 覆盖 {my_scope}，其他相关 skill：
  - {related_skill_A} 覆盖 {其他 scope}
  - 与之精度差异：{我更精确/更广义/互补}
```

这个模板既明确了本 skill 的领地，也帮助 Claude 判断触发优先级。

---

## 八、给 AFP 行动派贡献者的隐性建议

**触发词设计是 AFP-ecosystem 治理的一部分**。

- 独立 Bundle 之间要有清晰领地划分（一致的隔离策略）
- Shared primitives 要明确"不触发用户"（防止污染）
- 精确 skill 可以让广义 skill 兜底（分层设计）
- **AFP 行动派 Steering Committee 应该维护一份"触发词领地图谱"**，新 skill 发布前查阅

---

*本模块可被 P5（Frontmatter 撰写）P7（生态集成）阶段引用*
*源自 一平博论主控原创，扩展为 AFP-ecosystem 通用策略*
