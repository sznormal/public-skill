# Skill 设计反模式清单（通用 20 条）

> AFP Skill Creator · Module · 通用层
> 目的：帮助所有领域的合伙人在贡献 skill 前自检
>
> **本清单为跨领域通用反模式**。领域专属反模式（如学术的"理论贴标签"、
> 咨询的"MECE 违反"）见 `modules/domains/{domain}.md`。

---

## 一、Frontmatter 反模式（5 条）

### ❌ 1. name 过于笼统

```yaml
name: helper  # ❌ 不知道帮什么
name: assistant  # ❌ 太宽
```

**修正**：具体到领域和角色（如 `phd-methodology-guide` / `consulting-scqa-writer` / `medical-case-analysis`）

### ❌ 2. description 过短

```yaml
description: 帮用户做内容  # ❌ 触发范围窄，用户找不到
```

**修正**：8-15 个触发词变体 + 触发隔离说明

### ❌ 3. description 过长（> 800 字）

一大段包罗万象的描述，Claude 无法有效解析

**修正**：分段设计（一句话定义 / 触发词覆盖 / 触发隔离）

### ❌ 4. 触发词太广（抢占其他 skill 触发权）

```yaml
description: 任何内容生产问题都调用本 skill
```

**修正**：明确本 skill 的能力边界（领域 + 阶段 + 场景）

### ❌ 5. 子文档写 frontmatter（死代码）

`stages/xxx/SKILL.md` 里加 name/description → **Claude 不递归扫描，字段无效**

**修正**：子文档直接改成 `xxx.md`（无 frontmatter）

---

## 二、架构反模式（5 条）

### ❌ 6. 主控 SKILL.md 塞满所有内容

主控 > 3000 token，把所有阶段的执行细节、方法论、示例都塞进去

**修正**：薄路由 pattern（详见 `thin-router-pattern.md`）

### ❌ 7. 独立 skill 泛滥（Sparse Collection）

50+ 独立 skill 各有触发词，用户被 skill 触发冲突淹没

**修正**：合并为 Bundle 或 Federated Bundle（详见 F 文档架构学）

### ❌ 8. Bundle 之间未隔离触发词

两个 Bundle 主控都能被同一口令触发，用户不知道会跳到哪个

**修正**：见 `trigger-word-isolation.md` 的三种策略

### ❌ 9. Shared primitive 被独立触发

用户直接触发了本应由 Bundle 内部调用的 primitive

**修正**：primitive 的 description 加"仅供 Bundle 调用，不响应用户直接触发"

### ❌ 10. 循环依赖

Bundle A 的 stage 引用 Bundle B 的 stage，Bundle B 又引用 A → 加载死循环

**修正**：Bundle 之间只通过 shared primitives 通信

---

## 三、AFP-SPEC 合规反模式（5 条）

### ❌ 11. Hard Stop 缺失

关键决策点自动推进，用户没有确认机会

**修正**：AFP-SPEC §5——3 个 Hard Stops + 1 个 Auto Delivery

### ❌ 12. Hard Stop 崩溃

多个 Hard Stop 合并成一个"最终确认"

**修正**：分阶段独立 Hard Stop，每次只问一个决策

### ❌ 13. Evidence Chain 缺失

skill 输出未做证据链验证（无论学术引用、咨询数据源、法律判例、医疗证据）

**修正**：AFP-SPEC §6 Evidence Chain——所有事实性主张必须可追溯

### ❌ 14. 引用/事实混淆

`verified` 和 `hallucinated` 内容混在一起，用户分不清

**修正**：明确标注每条事实性主张的来源类别

### ❌ 15. 输出无结构

自由文本输出，无 JSON schema，无法被下游 skill 消费

**修正**：AFP-SPEC §7 Output Structure——按 schema 输出

---

## 四、状态管理反模式（3 条）

### ❌ 16. 长对话失控

跨多轮对话时，前面的状态丢失

**修正**：状态管理 HUD + 每几轮 checkpoint

### ❌ 17. 跨对话丢失

用户换个对话，状态全部重置

**修正**：断点续传（磁盘持久化）

### ❌ 18. 状态数据结构冗余

HUD JSON 塞了几百个字段，实际只用到几个

**修正**：只保留跨阶段流转必需的字段

---

## 五、协作反模式（2 条）

### ❌ 19. 未查触发词冲突

新 skill 上架时未查阅 AFP-ecosystem 现有 skill

**修正**：贡献前必查触发词冲突

### ❌ 20. 未复用 shared primitives

重复造轮子——已有的通用能力又自己写了一份

**修正**：先看 shared-primitives，能复用就复用（激励 3x）

---

## 六、检查清单（skill 发布前必查）

**通用层（本模块）**：

□ Frontmatter：name 具体 / description 分三段 / 触发词 8-15 个 / 隔离说明有
□ 架构：主控 < 3000 token / 子文档无 frontmatter / 无循环依赖
□ AFP-SPEC：Hard Stops 存在 / Evidence Chain 有 / 输出有 schema
□ 状态：HUD 简洁 / 有 checkpoint / 有续跑
□ 协作：查过触发词冲突 / 考虑过 shared primitives 复用

**领域层**（见 `modules/domains/{domain}.md`）：

□ 领域特定的方法论合规
□ 领域特定的反模式（10-15 条/领域）
□ 领域行文规范
□ 领域证据链标准

**所有通用 + 领域检查项都过 → 可以发布**
**任何一项没过 → 回到相应 stage 修正**

---

## 七、贡献新的通用反模式

如果你在实际使用中发现了新的**跨领域通用反模式**，欢迎贡献到本清单。

流程：
1. 用 P1 意图澄清确认这是真的通用反模式，不是领域专属
2. 提交提议到 AFP 行动派 Steering Committee 审议
3. 通过后加入本清单，编号继续排下去（21, 22, ...）

**领域专属反模式**请贡献到 `modules/domains/{domain}.md`，不要挤在这里。

---

*本清单持续演化。当前版本：v0.2（2026-07-01）· 通用 20 条*
