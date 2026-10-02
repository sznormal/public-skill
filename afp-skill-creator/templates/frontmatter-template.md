# Frontmatter 模板速查（Pattern 5 五段标准）

> AFP Skill Creator · Template
> 使用：P5 阶段按 skill_type 取对应模板替换填写。字段详解与触发词设计原则见 stages/05-frontmatter-writing.md

---

## 一、五段字段速查

| 字段 | 必填 | 规则 |
|---|---|---|
| `name` | ✅ | `<partner>-<skill>`，前缀必须是已授权命名空间 |
| `description` | ✅ | 三段式：一句话定义 →【触发词覆盖】→【触发隔离】；总长 ≤800 字 |
| `agent_created` | ✅ | AFP 贡献者默认 `true` |
| `partner` | ✅ | 必须与 name 前缀一致（积分记账键） |
| `skill_type` | ✅ | `independent` / `orchestrator` / `shared_primitive` |
| `afp_spec_target` | 建议 | `bronze` / `silver` / `gold`（shared_primitive 最低 gold） |

触发词精确度分级：**Orchestrator 宽口令 / Independent 精确单点 / Shared Primitive 复用为主少量直触**。

## 二、Independent 模板

```yaml
---
name: {partner}-{specific-task}
description: >
  {帮助谁完成什么单点任务}。{方法论一句话}，符合 AFP-SPEC {Silver} 合规。
  【触发词覆盖】：{精确单点口令 10-15 个 / 用斜杠分隔}
  【触发隔离】：只处理"{本任务}"这一独立任务。用户处理 {相邻阶段}
              请直接触发对应独立 skill——本 skill 不代替。
              用户 {不相关场景} 时，本 skill 不触发。
agent_created: true
partner: {partner_slug}
skill_type: independent
afp_spec_target: silver
---
```

## 三、Orchestrator 模板

```yaml
---
name: {partner}-{domain}-orchestrator
description: >
  {partner}{领域}全流程总控。当用户想走完整{领域}流程时触发。
  负责识别用户所在阶段 + 状态跨阶段流转 + 分段引导切换到对应独立 skill。
  【触发词覆盖】：{全流程宽口令 8-12 个}
  【触发隔离】：只在"全流程引导"意图时触发。单点任务请直接触发
              对应独立 skill——orchestrator 不代替独立 skill 的能力。
agent_created: true
partner: {partner_slug}
skill_type: orchestrator
afp_spec_target: silver
---
```

## 四、Shared Primitive 模板（需 Committee 审议）

```yaml
---
name: afp-shared-{capability}
description: >
  {能力定义}·跨合伙人 skill 复用。{核心机制}。
  【触发词覆盖】：{直触口令 5-8 个}
  【触发隔离】：既可被用户直接触发（记 1 点），也可被其他 skill
              内嵌 Read 复用（记 2 点）。不处理 {边界外}（请触发 {相邻}）。
agent_created: true
partner: afp
skill_type: shared_primitive
afp_spec_target: gold
---
```

## 五、写完自查五条

- □ name 前缀 = partner？
- □ 触发词数量与精确度符合 skill_type 分级？
- □ 触发隔离至少写了 2 个不触发场景？
- □ description ≤800 字？
- □ 子文档（stages/modules/templates）全部**没有** frontmatter？

---

*本模板 v1.0 · Pattern 5 定型版 · 详解见 stages/05*
