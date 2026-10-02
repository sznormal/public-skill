# 断点续传 + 抗压缩协议

> AFP Skill Creator · Module
> 触发：用户说 "怎么做断点续传" / "抗压缩协议"；或 P6 内容撰写 / P8 合规检查由主控 Read
> 方法论来源：一平原创"抗压缩协议"（AFP Shared Primitive 候选：`afp-shared-continuation`）

---

## 一、要解决的两个问题

1. **跨对话断点**：用户今天走到 P4，明天新开对话——上下文全没了，流程必须能从磁盘恢复
2. **上下文压缩**：长对话中 Claude 的上下文被压缩（compact），HUD"记忆"可能失真——**磁盘状态永远比对话记忆可信**

核心原则一句话：**状态以磁盘为准，对话记忆只是缓存。**

---

## 二、状态文件格式

每个使用本协议的 skill，在用户项目目录维护一个状态文件 `{project_path}/{skill-name}-state.md`：

```markdown
# {skill-name} · 项目状态

> ⚠️ 本文件由 skill 自动维护。恢复流程以本文件为唯一事实来源。

## HUD 快照

```json
{
  "meta": { "current_stage": "P4", "project": "...", "updated_at": "2026-07-23 14:30" },
  "stages": {
    "P1": { "status": "done", "output_file": "stage-outputs/p1-xxx.md" },
    "P2": { "status": "done", "output_file": "stage-outputs/p2-xxx.md" },
    "P3": { "status": "done", "output_file": "stage-outputs/p3-xxx.md" },
    "P4": { "status": "in_progress", "output_file": "" },
    "P5": { "status": "locked", "output_file": "" }
  }
}
```

## 关键决策记录

- {date} · P2：用户选择方案 B（{理由一句话}）
- {date} · P3：Edit 目标期刊=《管理世界》

## 下次恢复提示

当前卡点：{P4 进行到哪一小步、还差什么}
```

**三个设计要点**：
- **HUD 快照**是 JSON——恢复时直接重建状态，不靠自然语言猜
- **关键决策记录**只记决策不记过程——防止状态文件本身膨胀
- **下次恢复提示**用一句人话描述卡点——压缩后恢复的第一锚点

产出物落盘到 `{project_path}/stage-outputs/p{N}-{name}.md`，状态文件只存路径不存内容。

---

## 三、写入时机

| 时机 | 动作 |
|---|---|
| 每次 Hard Stop 确认后 | 全量重写状态文件（HUD + 决策记录追加） |
| 每 5 轮对话 | auto-checkpoint：静默重写状态文件（不打断用户） |
| 用户 `Edit` 字段 | 立即写盘（决策记录追加一行） |
| 方案型决策选定后 | 立即写盘（这是最贵的状态，丢了最疼） |

**写盘是静默动作**——不需要每次向用户汇报"已保存"，只在 Hard Stop 确认单里带一行 `💾 状态已写盘`。

---

## 四、恢复流程（Continue 协议）

用户新对话说 `Continue {project_path}`（或触发 skill 后被检测到状态文件存在）：

```
Step 1  Read {project_path}/{skill-name}-state.md
Step 2  用 HUD 快照重建内存状态（不要求用户复述任何历史）
Step 3  向用户输出恢复确认单（见下），等用户确认
Step 4  从 current_stage 的卡点处续跑——需要历史产出时 Read stage-outputs/ 对应文件
```

恢复确认单：

```
╭─ 断点恢复 ────────────────────────────────────╮
│ 📂 项目：{project} · 上次更新：{updated_at}
│ 📍 恢复到：P{N} - {stage_name}
│ ✅ 已完成：P1 ✓ P2 ✓ P3 ✓
│ 🎯 当前卡点：{下次恢复提示原文}
│ 👉 确认续跑请说 Next；想回看历史说 Status
╰──────────────────────────────────────────────╯
```

---

## 五、抗压缩三条纪律

长对话中上下文被压缩后，skill 必须遵守：

1. **不信记忆信磁盘**：压缩后第一个动作是 Read 状态文件重建 HUD，即使"感觉还记得"
2. **不重问用户**：已在决策记录里的选择，禁止让用户再答一遍——重问 = 状态管理失败
3. **不静默重做**：发现某阶段产出文件缺失时，向用户报告并确认是否重做，不擅自重跑（重跑可能覆盖用户手改过的产出）

---

## 六、跨 skill 状态传递（Orchestrator 场景）

Pattern 5 下 skill 间无共享内存，状态经磁盘中转（详见 stages/04 §五）：

- Orchestrator 维护全局状态文件 `{project_path}/{project_name}-state.md`
- 每个下游 Independent skill 被触发时：先 Read 全局状态 → 干活 → 产出写 `stage-outputs/` → 回写全局状态的本阶段条目
- 下游 skill **只写自己阶段的条目**，不动其他阶段的状态——防止并发覆盖

---

## 七、给被创建 skill 的植入模板

在你创建的 skill 主控里加入这一节（直接改写复制）：

```markdown
## 断点续传（跨对话抗压缩）

- 每次 Hard Stop 后写入 `{project_path}/{skill-name}-state.md`（格式见 AFP continuation 协议）
- 每 5 轮对话 auto-checkpoint
- 新对话说 `Continue {project_path}` → Read 状态文件 → 输出恢复确认单 → 续跑
- 上下文压缩后：以磁盘状态为准，不重问用户已记录的决策
```

---

## 八、反模式警告

- ❌ **状态存对话不存盘**："我记住了"——压缩或新对话后全丢
- ❌ **状态文件存全文**：把每阶段产出全文塞进状态文件——文件膨胀到没法快速 Read，产出应落盘 stage-outputs/ 只存路径
- ❌ **恢复后重问用户**：决策记录里有的还问——用户体验崩塌的第一现场
- ❌ **多 skill 抢写全局状态**：下游 skill 全量重写全局文件——互相覆盖，只许写自己的条目
- ❌ **checkpoint 太吵**：每次写盘都汇报一遍——静默写，确认单里带一行即可
- ❌ **恢复不确认直接跑**：Read 完状态直接续写内容——先出恢复确认单，等用户 Next

---

*本协议是 `afp-shared-continuation` 的模块版。升级为 Shared Primitive 后，各 skill 应改为 Read 该 primitive（享受复用记账），本模块保留作为教学文档。*
