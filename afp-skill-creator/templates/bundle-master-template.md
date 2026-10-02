# Bundle 主控 SKILL.md 模板（⚠️ Pattern 3 遗留 · 仅作历史参考）

> AFP Skill Creator · Template（已废弃）
> ⚠️ 本模板属 Pattern 3 · Federated Bundle 时代。v0.3 起架构定型为 Pattern 5，**新建 skill 请勿使用本模板**，改用：
> - Independent → `templates/independent-skill-template.md`
> - Orchestrator → `templates/orchestrator-template.md`
> - Shared Primitive → `templates/shared-primitive-template.md`
> Bundle 与 Pattern 5 的术语换算见 `modules/afp-bundle-vs-primitive.md` §三。保留本文件仅供阅读旧 skill 文档时对照。

---

## 使用说明

以下是一个标准的 AFP-compliant Bundle 主控模板。总长度约 2000 token，符合薄路由 pattern。

复制下方内容到你的 Bundle 主控 SKILL.md，替换所有 `{placeholder}`。

---

## 模板正文（从下一行开始复制）

```yaml
---
name: {your-bundle-name}
description: >
  {一句话定义 Bundle 处理什么任务}。{方法论/核心机制概述}。
  【触发词覆盖】：{触发词 1} / {触发词 2} / {触发词 3} / {触发词 4} / 
                 {触发词 5} / {触发词 6} / {触发词 7} / {触发词 8} / 
                 {触发词 9} / {触发词 10} / {触发词 11} / {触发词 12}
  【触发词隔离】：只在用户明确表达 {intended_scope} 意图时触发。
              {non_trigger_scenario_1} 时本 skill 不触发。
              {non_trigger_scenario_2} 时本 skill 不触发。
  【与其他 skill 的关系】：本 skill 覆盖 {my_scope}。
              相关 skill：{related_skill_A}（覆盖 {其 scope}）。
agent_created: true
---

# {Bundle 中文名}

{一段话定位：这个 Bundle 是干什么的，谁在什么场景使用}

## 核心设计理念

1. **{理念 1}**
2. **{理念 2}**
3. **{理念 3}**
4. **{理念 4}**
5. **{理念 5}**

## 全局状态管理（HUD）

```json
{
  "meta": {
    "current_stage": "{initial_stage}",
    "target_deliverable": ""
  },
  "stages": {
    "{stage_1_name}": { "status": "unlocked", "output": "", "version": 0 },
    "{stage_2_name}": { "status": "locked", "output": "", "version": 0 },
    "{stage_3_name}": { "status": "locked", "output": "", "version": 0 }
  },
  "history": {
    "last_action": "",
    "checkpoint_at": ""
  }
}
```

## 阶段路由（每阶段 Hard Stop）

| 阶段 | 名称 | 触发关键词 | 加载文档 | 前置条件 |
|------|------|-----------|---------|---------|
| P1 | {stage_1_name} | {kw_1a} / {kw_1b} | `stages/01-{name}.md` | 无 |
| P2 | {stage_2_name} | {kw_2a} / {kw_2b} | `stages/02-{name}.md` | P1 完成 |
| P3 | {stage_3_name} | {kw_3a} / {kw_3b} | `stages/03-{name}.md` | P2 完成 |
| ... | ... | ... | ... | ... |

## 按需模块

| 用户说 | 加载文档 |
|--------|---------|
| "{keyword_a}" | `modules/{module_a}.md` |
| "{keyword_b}" | `modules/{module_b}.md` |
| "审查一下" | `../AFP-shared-primitives/review-theater.md` |
| "帮我检索文献" | `../AFP-shared-primitives/cnki-advanced-search.md` |

## 首次触发引导

```
你好！我是 {bundle_name}。

我可以帮你完成 {task_scope}。

请告诉我：
1. 你目前处于哪个阶段？（{阶段列表}）
2. 你的具体需求是什么？

如果不确定从哪开始，我建议从 {default_starting_stage} 开始。
```

## 通用指令

| 指令 | 功能 |
|------|------|
| `Next` | 确认当前阶段完成，进入下一步 |
| `Back` | 回到上一阶段修改 |
| `Edit <字段>=<新值>` | 修改状态字段 |
| `Skip` | 跳过可选阶段 |
| `Export` | 导出当前所有 artifact |
| `Review` / `审查一下` | 加载 review 模块自检 |
| `Status` | 输出当前 HUD 状态 |
| `Continue [项目路径]` | 跨对话续跑 |
| `Help` | 加载简介 |

## Hard Stop 输出规范

每阶段完成后：

```
╭─ {bundle_name} · P{N} 完成 ─────────────────╮
│ 📊 项目：{project_name}
│ 🎯 当前阶段：P{N} - {stage_name}
│ ✅ 生成 artifact：{files}
│ 📍 下一步：P{N+1} - {next_stage}
│ 👉 NEXT：Next 继续 / Back 回退 / Edit 修改
╰──────────────────────────────────────────╯
```

## 断点续传

- 每阶段完成后写入 `{project_path}/{bundle-name}-state.md`
- 用户新对话说 `Continue {project_path}` → 从磁盘恢复
- 每 5 轮 auto-checkpoint

## 反模式警告（内嵌 8 条，完整清单见 modules/skill-anti-patterns.md）

- ❌ 主控塞满
- ❌ frontmatter 死代码
- ❌ 触发词太窄 / 太宽
- ❌ 未做触发词隔离
- ❌ Hard Stop 缺失
- ❌ 引用未验证
- ❌ 输出无结构
- ❌ 无断点续传

---

*本 Bundle 是 AFP-ecosystem 的一部分。生成的 skill 应符合 AFP-SPEC v0.1 至少 Silver 等级。*
*维护者：{owner_name}*
*版本：{version} · {date}*
```

（模板结束）

---

## 模板使用检查清单

复制粘贴后：

- □ 是否替换所有 `{placeholder}`？
- □ 触发词是否列了 12-15 个变体？
- □ 触发隔离是否明确？
- □ 阶段路由表是否完整？
- □ 按需模块索引是否覆盖了所有可能的用户特殊需求？
- □ 总字符数是否在 3000-6000 之间？（用 `wc -m` 检查）
- □ 是否引用了至少一个 AFP-shared-primitives 模块？

**如果引用了 shared-primitives** → 你的 Bundle 是 Federated Bundle（架构学的最优形态）
**如果没有引用** → 考虑是否有可复用的 primitive 被漏掉

---

*本模板由 AFP-skill-creator 提供，v0.1 · 2026-07-01*
