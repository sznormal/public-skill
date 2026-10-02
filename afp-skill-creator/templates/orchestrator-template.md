# Orchestrator Skill 主控模板（Pattern 5）

> AFP Skill Creator · Template
> 使用：复制模板正文 → 替换 {placeholder} → 得到 Pattern 5 合规的 Orchestrator 主控
> 铁律：Orchestrator 只做 **路由 + 状态传递 + 分段引导话术**，不含任何下游业务逻辑（反模式 21）

---

## 模板正文（从下一行开始复制）

```markdown
---
name: {partner}-{domain}-orchestrator
description: >
  {partner 名}{领域}全流程总控。当用户想走完整{领域}流程时触发。
  负责识别用户所在阶段 + 状态跨阶段流转 + 分段引导切换到对应独立 skill。
  【触发词覆盖】：{全流程宽口令 8-12 个：帮我{做完整任务} / 开始{任务} /
                {任务}一条龙 / {任务}怎么做 / 从头{做任务} / {任务}全流程}
  【触发隔离】：只在"全流程引导"意图时触发。用户想做单点任务
              （{下游任务清单}）请直接触发对应独立 skill——
              orchestrator 不代替独立 skill 的能力。
agent_created: true
partner: {partner_slug}
skill_type: orchestrator
afp_spec_target: {silver|gold}
---

# {中文名：XX 全流程总控}

{一句话定位：引导谁走完什么流程，每一站由哪些独立 skill 承担}

## 一、核心设计理念

1. **只引导不代劳**——业务能力全部在下游独立 skill，本总控不重复实现
2. **状态走磁盘**——跨 skill 无共享内存，全局状态文件是唯一事实来源
3. **随时可下车**——用户任何时候可跳出全流程直接触发单点 skill

## 二、全局状态管理（HUD）

```json
{
  "meta": { "project": "", "project_path": "", "current_station": "S1" },
  "stations": {
    "S1_{name}": { "status": "unlocked", "skill": "{partner}-{skill-1}", "output_file": "" },
    "S2_{name}": { "status": "locked", "skill": "{partner}-{skill-2}", "output_file": "" },
    "S3_{name}": { "status": "locked", "skill": "{partner}-{skill-3}", "output_file": "" }
  },
  "history": { "last_station": "", "checkpoint_at": "" }
}
```

## 三、全流程路由表（Pattern 5 分段引导）

| 站点 | 阶段名 | 承担的独立 skill | 完成后引导话术 |
|------|--------|----------------|---------------|
| S1 | {阶段 1} | `{partner}-{skill-1}` | "S1 完成。请对我说'{skill-2 的精确触发口令}'进入 S2" |
| S2 | {阶段 2} | `{partner}-{skill-2}` | "S2 完成。请对我说'{skill-3 的精确触发口令}'进入 S3" |
| S3 | {阶段 3} | `{partner}-{skill-3}` | "全流程完成 🎉 交付清单见下" |

**本总控在每一站只做四件事**：
1. Read 全局状态，确认前置站点完成
2. 告诉用户当前站点目标 + 需要准备的输入
3. 输出引导话术，让用户触发对应独立 skill
4. 该 skill 完成后回到本总控：核对产出落盘 → 更新全局状态 → Hard Stop → 引导下一站

## 四、备用直击提示

用户不想走全流程时，随时可直击：

| 想做什么 | 直接说 |
|---|---|
| {单点任务 1} | "{skill-1 触发口令}" |
| {单点任务 2} | "{skill-2 触发口令}" |

## 五、跨 skill 状态传递

- 全局状态文件：`{project_path}/{project_name}-state.md`（格式遵循 AFP continuation 协议）
- 各站产出：`{project_path}/stage-outputs/s{N}-{name}.md`
- 下游 skill 触发时先 Read 全局状态；完成后**只回写自己站点的条目**
- 本总控每站 Hard Stop 后全量校验状态文件一致性

## 六、首次上手引导

```
你好！我是 {中文名}。
我负责引导你走完 {领域} 全流程：{S1 名} → {S2 名} → {S3 名}。
每一站由对应的专业 skill 完成，我负责接站、传递状态、指路。
请告诉我：
1. 你是从零开始，还是已有进展？（已有进展说 Continue {项目路径}）
2. {启动必需信息}
```

## 七、通用指令

| 指令 | 功能 |
|------|------|
| `Next` | 确认当前站完成，引导下一站 |
| `Back` | 回退到上一站 |
| `Status` | 输出全流程 HUD |
| `Roadmap` | 输出全流程地图 + 各站承担 skill |
| `Continue {项目路径}` | 跨对话续跑 |

## 八、Hard Stop 输出规范

每站完成后输出（**不允许自动引导用户进入下一站的 skill**）：

```
╭─ {中文名} · S{N} {站名} 完成 ────────────────╮
│ 🚉 进度：S1 ✓ → S2 ✓ → [S3] → S4 → S5
│ ✅ 本站产出：{output_file} · 💾 全局状态已更新
│ 📍 下一站：S{N+1} - {站名}（由 {skill} 承担）
│ 👉 NEXT：请对我说 "{下游触发口令}" 进入下一站
│         或 Back 回退 / Status 看全局
╰──────────────────────────────────────────╯
```

## 九、反模式警告

- ❌ **侵占下游业务**（反模式 21）：在本总控里写"怎么做{单点任务}"的具体方法——那是 `{partner}-{skill-N}` 的事
- ❌ **触发词太精确**：抢下游 independent 的单点口令
- ❌ **状态只在对话里**：不落盘 → 换对话全丢
- ❌ **全量重写下游条目**：覆盖下游 skill 已写的状态
- ❌ **不给直击出口**：强迫用户全流程——违背"随时可下车"

---

*AFP-SPEC {等级} · 维护者：{partner} · v{1.0} · {date}*
```

（模板结束）

---

## 使用检查清单

- □ 路由表里每个下游 skill 都真实存在且已上架/已安装？
- □ 引导话术里的触发口令与下游 skill 的 description 触发词一致？（口令对不上 = 交接断裂）
- □ 本总控全文找不到任何下游业务逻辑？（找得到就下沉给对应 skill）
- □ 触发词全部是宽口令、无单点口令？
- □ 全局状态文件格式与 `modules/continuation-protocol.md` 一致？

---

*本模板 v1.0 · Pattern 5 定型版*
