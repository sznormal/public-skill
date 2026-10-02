# Independent Skill 主控模板（Pattern 5）

> AFP Skill Creator · Template
> 使用：复制模板正文 → 替换 {placeholder} → 得到 Pattern 5 合规的 Independent 主控
> 配套：stage 子文档用 `stage-md-template.md`；frontmatter 详解见 `frontmatter-template.md`

---

## 模板正文（从下一行开始复制）

```markdown
---
name: {partner}-{specific-task}
description: >
  {一句话定义：帮助谁完成什么单点任务}。{方法论/核心机制一句话}，
  符合 AFP-SPEC {Silver} 合规。
  【触发词覆盖】：{精确单点口令 10-15 个，用 / 分隔——
                对象词 × 阶段词 × 场景词 × 服务词组合}
  【触发隔离】：只处理"{本任务}"这一独立任务。用户处理 {相邻阶段清单}
              请直接触发对应独立 skill——本 skill 不代替。
              用户 {不相关场景} 时，本 skill 不触发。
agent_created: true
partner: {partner_slug}
skill_type: independent
afp_spec_target: {bronze|silver|gold}
---

# {skill 中文名}

{一句话定位 · 30 字内：谁在什么场景用它得到什么}

## 一、核心设计理念（3-5 条）

1. **{理念 1：来自你的方法论}**
2. **{理念 2}**
3. **{理念 3}**

## 二、全局状态管理（HUD）

```json
{
  "meta": { "current_stage": "P1", "project": "", "target_deliverable": "" },
  "stages": {
    "P1_{name}": { "status": "unlocked", "output_file": "" },
    "P2_{name}": { "status": "locked", "output_file": "" },
    "P3_{name}": { "status": "locked", "output_file": "" }
  },
  "decisions": {},
  "history": { "last_action": "", "checkpoint_at": "" }
}
```

## 三、阶段路由（每阶段 Hard Stop）

| 阶段 | 名称 | 加载文档 | 前置条件 |
|------|------|---------|---------|
| P1 | {阶段 1 名} | `stages/01-{name}.md` | 无 |
| P2 | {阶段 2 名} | `stages/02-{name}.md` | P1 完成 |
| P3 | {阶段 3 名} | `stages/03-{name}.md` | P2 完成 |

（任务简单到 3-5 轮交互可完成时，删除本表和 stages/，引导逻辑直接写在 §六）

## 四、按需模块

| 用户说 / 触发时机 | 加载文档 |
|--------|---------|
| "{特殊指令 A}" | `modules/{module-a}.md` |
| 产出类阶段生成前（自动） | `modules/exemplars.md`（独家语料：90 分样例 / 反面样例 / 话术库，few-shot 参照） |
| "审查一下" | Read `~/.claude/skills/afp-shared-review-theater/SKILL.md`（未上架前用本地替代） |

## 五、Shared Primitive 复用清单

| Primitive | 用途 | 触发时机 |
|---|---|---|
| `afp-shared-{capability}` | {用途} | P{N} · {阶段名} |

## 六、首次上手引导

```
你好！我是 {skill 中文名}。
我可以帮你完成 {任务}——{方法论一句话}。
请告诉我：
1. {启动必需输入 1}
2. {启动必需输入 2}
准备好后我们从 P1 {阶段 1 名}开始。
```

## 七、通用指令

| 指令 | 功能 |
|------|------|
| `Next` | 确认当前阶段完成，进入下一步 |
| `Back` | 回到上一阶段修改 |
| `Edit <字段>=<新值>` | 修改状态字段 |
| `Skip` | 跳过可选阶段 |
| `Export` | 导出当前所有 artifact |
| `审查一下` | 加载 review 模块自检 |
| `Status` | 输出当前 HUD 状态 |
| `Continue {项目路径}` | 跨对话续跑 |

## 八、断点续传（跨对话抗压缩）

- 每次 Hard Stop 后写入 `{project_path}/{skill-name}-state.md`
- 每 5 轮对话 auto-checkpoint
- 新对话 `Continue {project_path}` → Read 状态文件 → 恢复确认单 → 续跑
- 上下文压缩后：以磁盘状态为准，不重问已记录的决策

## 九、Hard Stop 输出规范

每阶段完成后输出（**即使结果非常明确，也不允许自动进入下一阶段**）：

```
╭─ {skill 中文名} · P{N} 完成 ─────────────────╮
│ 📊 项目：{project}
│ ✅ 产出：{artifact} · 💾 状态已写盘
│ 📍 下一步：P{N+1} - {next_stage}
│ 👉 NEXT：Next 继续 / Back 回退 / Edit 修改
╰──────────────────────────────────────────╯
```

## 十、反模式警告（内嵌精选，完整清单按需 Read）

- ❌ {领域反模式 1（从 domain 模块/领域档案选 3-5 条最致命的）}
- ❌ {领域反模式 2}
- ❌ 一次性输出多阶段内容（违反单步输出）
- ❌ 替用户拍板方向性决策（方案型决策必须多方案）

## 十一、最终交付物

1. {交付物 1}
2. {交付物 2}

---

*AFP-SPEC {等级} · 维护者：{partner} · v{1.0} · {date}*
```

（模板结束）

---

## 使用检查清单

- □ 所有 {placeholder} 已替换？
- □ name 前缀 = partner 字段？
- □ 触发词 10-15 个且全部是**精确单点口令**（不抢 orchestrator 的全流程口令）？
- □ 触发隔离列出了相邻阶段和不相关场景？
- □ 阶段数 = 方法论步骤数（P3 五问的"问 2"）？
- □ 主控总量 2000-2500 token（`wc -m` 约 3000-6000 字符）？
- □ 至少检查过一遍 Shared Primitive 复用机会？
- □ 独家语料已脱敏并挂载 `modules/exemplars.md` / `templates/`？（无语料则删除对应表行）

---

*本模板 v1.0 · Pattern 5 定型版 · 取代 bundle-master-template.md（Pattern 3 遗留）*
