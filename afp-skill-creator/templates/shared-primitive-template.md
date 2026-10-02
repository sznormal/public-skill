# Shared Primitive 主控模板（Pattern 5）

> AFP Skill Creator · Template
> 使用：复制模板正文 → 替换 {placeholder} → 得到 Pattern 5 合规的 Shared Primitive
> 前置：`afp-shared-*` 命名空间需 Steering Committee 审议通过（流程见 stages/02 §五）；合规最低门槛 Gold

---

## 模板正文（从下一行开始复制）

```markdown
---
name: afp-shared-{capability}
description: >
  {能力一句话定义}·跨合伙人 skill 复用。{核心机制概述}。
  【触发词覆盖】：{直触口令 5-8 个——比 Independent 少，因为复用为主}
  【触发隔离】：既可被用户直接触发（作为独立 skill 记 1 点），
              也可被其他 skill 内嵌 Read 复用（记 2 点复用奖励）。
              不处理 {边界外场景}（请触发 {相邻 primitive 或 skill}）。
agent_created: true
partner: afp
skill_type: shared_primitive
afp_spec_target: gold
---

# {中文名}（AFP 共同体资产）

{一句话定位} · 原创贡献者：{contributor}（终身署名）

## 一、能力边界

**能做**：
- {能力 1}
- {能力 2}

**不能做**（越界请求的响应方式）：
- {边界 1} → 引导触发 {替代 skill}
- {边界 2} → 明确告知不支持

## 二、双重身份

### 模式 A · 独立触发（用户直接说触发口令）

按 §五首次引导走完整交互流程，含 Hard Stop。

### 模式 B · 内嵌调用（被其他 skill Read）

调用方在其 SKILL.md 声明复用后，按 §三契约传参调用。
**内嵌模式下不做首次引导、不抢调用方的 Hard Stop 节奏**——静默执行，按契约返回。

## 三、调用契约（v{1.0}）

### 输入格式

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| {param_1} | {string} | ✅ | {说明} |
| {param_2} | {list} | ❌ | {说明 · 默认值} |

### 输出格式

```json
{
  "status": "ok | error",
  "data": { {输出 schema} },
  "unverified_items": [ {无法验证的条目清单} ],
  "contract_version": "{1.0}"
}
```

### 状态影响

- 本 primitive **不修改调用方的 HUD**
- 只写自己命名空间下的临时文件：`{project_path}/.afp-shared-{capability}/`

### 错误处理

- 输入不合契约 → 返回 `{"status":"error","reason":"..."}`，由调用方决定处理
- 外部依赖失败（网络/工具）→ 重试 {3} 次后返回 error，**不静默降级**

### 契约变更纪律

- 新增可选参数 = 次版本；改动必填参数或输出 schema = 主版本 + Committee 备案 + 公告调用方
- 调用方应在复用清单中记录所依赖的 contract_version

## 四、全局状态管理（HUD · 仅独立触发模式使用）

```json
{
  "meta": { "mode": "standalone", "current_stage": "P1" },
  "stages": { {独立模式的阶段骨架} }
}
```

## 五、首次上手引导（仅独立触发模式）

```
你好！我是 {中文名}——AFP 共同体的共享能力。
我可以帮你 {能力}。请提供：
1. {输入 1}
2. {输入 2}
```

## 六、通用指令（独立模式）

| 指令 | 功能 |
|------|------|
| `Next` / `Back` / `Edit` / `Status` | 同 AFP 标准指令 |
| `Contract` | 输出当前调用契约全文 |

## 七、Hard Stop 输出规范（独立模式）

```
╭─ {中文名} · 完成 ─────────────────────────────╮
│ ✅ 产出：{artifact}
│ ⚠️  unverified：{N} 条（清单见产出文件）
│ 👉 NEXT：Next 确认 / Edit 调整参数重跑
╰──────────────────────────────────────────╯
```

## 八、复用记账说明

- 被其他 skill 内嵌 Read → 记 **2 点**（归属贡献者 {contributor}）
- 被用户直接触发 → 记 **1 点**
- 调用方记账不受影响（各记各的）

## 九、反模式警告

- ❌ 内嵌模式抢 Hard Stop（打断调用方流程节奏）
- ❌ 修改调用方 HUD（越权写状态）
- ❌ 契约外静默降级（错误必须显式返回）
- ❌ breaking change 不升主版本不公告
- ❌ 边界外请求硬接（能力边界模糊会毁掉跨合伙人信任）

---

*AFP-SPEC Gold · 归属：AFP 行动派共同体 · 贡献者：{contributor}（终身署名）· 契约 v{1.0} · {date}*
```

（模板结束）

---

## 使用检查清单

- □ Committee 审议已通过、`afp-shared-*` 命名空间已授予？
- □ 调用契约四节齐全（输入 / 输出 / 状态影响 / 错误处理）且有版本号？
- □ 双重身份行为差异写清楚了？（内嵌不引导、不抢停）
- □ 能力边界的"不能做"至少 2 条且给了去向？
- □ README 里有给其他合伙人看的内嵌调用示例？
- □ 达到 Gold 门槛计划？（peer-review ×3 + 运行历史的达成路径）

---

*本模板 v1.0 · Pattern 5 定型版*
