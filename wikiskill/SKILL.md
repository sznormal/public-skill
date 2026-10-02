---
name: wikiskill
description: >
  基于 WikiSkill (arXiv:2608.27454) 的技能进化框架——把智能体的执行经验编译成
  持久化知识库(Wiki)，让技能在验证集门控下逐轮进化。适用于：为某个具体任务
  自动迭代优化 agent skill / prompt / 工作流，并沉淀可复用的失败模式知识。
  【触发词覆盖】：wikiskill / wiki skill / 技能进化 / skill evolution /
                  迭代优化技能 / 让技能自我进化 / 从轨迹中沉淀技能 /
                  建立技能进化工作区
  【触发隔离】：一次性写完的普通 skill、单纯文档整理、日常聊天不触发。
               本 skill 针对的是"有可量化验证集、需要多轮迭代"的技能打磨场景。
agent_created: true
partner: norma
skill_type: independent
---

# WikiSkill 技能进化框架

你是**技能进化循环的调度者**。你的职责不是写一次性的技能，而是驱动一个
"跑任务 → 沉淀知识 → 改技能 → 验证门控"的闭环，让技能在**验证集分数**的
硬约束下逐轮变强，同时把每一轮的经验（包括失败的尝试）永久沉淀进 Wiki。

## 核心原则（违反即失效）

1. **Wiki 永不回滚，Skills 可回滚**
   技能是会被推翻的假设；Wiki 是不可否认的事实积累。
   被否决的提案要**连同 diff 一起永久留档**——这是整个方法最大的价值来源。

2. **原子提案**
   每轮只针对**单个 skill** 提出**一个**改动。一次改多个 skill，门控就无法归因。

3. **验证集是唯一裁判**
   不接受"看起来更好"。分数没涨就回滚，无论这个改动在逻辑上多么合理。

4. **红线：Inference Agent 在训练 rollout 期间禁止访问 `wiki/`**
   若执行任务时同时看到 skills 和 wiki，解题知识会直接来自 wiki，
   产出的轨迹对"技能开发"信息量骤降（论文消融：63.7% → 60.9%）。
   Wiki 只服务于 Wiki Maintainer 与 Skill Proposer。

5. **人在回路三个硬停止点**
   初始化参数、首轮提案、终止判定，必须经用户确认。

## 环境准备（每次会话先设定）

```bash
PY="C:/Users/29206/.workbuddy/binaries/python/versions/3.13.12/python.exe"
WS="C:/Users/29206/.workbuddy/skills/wikiskill/scripts/wikiskill.py"
ROOT="d:/cctest/workspace/wikiskill/<项目名>"     # 工作区根目录
```

> Windows 下 `--body-file` / `--diff-file` 支持 Git Bash 风格路径（`/tmp/x.md`、
> `/d/...`），脚本会自动映射。建议正文用文件传入，避免在命令行里转义中文与换行。

---

## 工作区三层结构

| 层 | 路径 | 生命周期 | 内容 |
|---|---|---|---|
| Raw | `raw/iter-XXXX/` | 只追加，不可修改 | 完整执行轨迹、任务摘要 |
| **Wiki** | `wiki/` | **永不回滚** | `patterns/`、`logs.md`、`skill-impact.md`、`index.md` |
| Skills | `skills/<name>/` | 可回滚（快照） | `SKILL.md`、`PURPOSE.md` |
| 元数据 | `.wikiskill/` | 自动 | `state.json` 状态机、`snapshots/` 技能快照 |

---

## 操作规程

### P0 · 立项（硬停止点）

先与用户确认四项，再动手：

| 项 | 说明 |
|---|---|
| 任务集 | `train` / `val` 各是什么，规模多大 |
| 评估命令 | 必须能输出 JSON：`{"score": 0.42, "details": [...]}` |
| 起始技能 | 从空集开始，还是从已有 skill 开始 |
| 终止条件 | 迭代上限 K、目标分、或连续 N 轮无提升 |

```bash
"$PY" "$WS" init --root "$ROOT" --name "<项目名>" \
  --eval-cmd "<评估命令，支持 {skills} {split} {root} 占位符>" \
  --train "<训练集描述>" --val "<验证集描述>"
```

若暂时没有可脚本化的评估命令，可省略 `--eval-cmd`，改用人工判分 +
`gate --score <x>` 手动喂分。**但必须事先约定评分标准**，否则门控无意义。

### P1 · 记录基线（无技能）

```bash
"$PY" "$WS" baseline --root "$ROOT"          # 自动跑 eval-cmd
# 或人工判分：
"$PY" "$WS" baseline --root "$ROOT" --score 0.30
```

基线分即初始门控阈值 `R_best`。**没有基线就没有门控。**

### P2 · 迭代循环（每轮四步）

> 循环从 `k=1` 开始。`"$PY" "$WS" status --root "$ROOT"` 可随时查看进度。

#### 第 ① 步 · Inference：产生轨迹

用**当前 `skills/`** 在训练集上跑任务，把轨迹写入 raw 层。

```bash
"$PY" "$WS" ingest --root "$ROOT" --run 1 --file traj-a.json traj-b.json ...
```

**红线**：执行任务的 agent 只能看到 `skills/`，不得读取 `wiki/` 任何内容。
同时整理一份任务级结果摘要（pass/fail、预测 vs 标准答案）供后续使用。

#### 第 ② 步 · Wiki Maintainer：编译经验

读 `wiki/index.md` 了解已有模式，再采样本轮的成功/失败轨迹做根因分析。

- **新发现的失败模式 / 成功策略** → 新建 pattern 页
  ```bash
  "$PY" "$WS" pattern new --root "$ROOT" --slug <短横线命名> \
    --title "<一句话现象>" --kind failure|success --run 1 --body-file body.md
  ```
- **已有模式出现新证据** → 增量补丁编辑（append / replace / insert 三选一）
  ```bash
  "$PY" "$WS" pattern edit --root "$ROOT" --slug <slug> --mode append \
    --run 1 --body-file new-evidence.md --note "<一句话说明这次更新>"
  "$PY" "$WS" pattern edit --root "$ROOT" --slug <slug> --mode replace \
    --run 1 --old "<原文精确片段>" --new "<替换文本>"
  "$PY" "$WS" pattern edit --root "$ROOT" --slug <slug> --mode insert \
    --run 1 --anchor "<锚点文本>" --body-file insert.md
  ```
- **本轮总结** → 追加进化日志
  ```bash
  "$PY" "$WS" log --root "$ROOT" --run 1 --body-file summary.md
  ```

**判据**：一个 pattern 只描述**一类**失败模式，不写成流水账。
判别标准是"以后遇到同类错误能靠它直接定位根因"。

#### 第 ③ 步 · Skill Proposer：提出原子提案

作为 ReAct 式分析者，**按需检索**而非通读全部：

1. 读 `wiki/index.md` 选相关 pattern → `pattern show` 看细节
2. 读 `wiki/skill-impact.md` —— **重点看被否决的提案，避免重犯**
3. 结合任务摘要定位根因，确定**唯一**要改的 skill 与**唯一**改动点

改动直接写入 `skills/<name>/SKILL.md`，同步更新 `PURPOSE.md`
（把每条规则映射回触发它的 pattern slug），然后登记提案：

```bash
"$PY" "$WS" propose --root "$ROOT" --run 1 --skill <name> \
  --action create|patch --diff-file changes.diff \
  --intent "<一句话：为什么改，期望解决什么>" \
  --sources <pattern-slug-1>,<pattern-slug-2>
```

**硬停止点（首轮）**：第 1 轮的提案必须给用户过目，确认方向后再验证。

#### 第 ④ 步 · Gating：验证门控

```bash
"$PY" "$WS" gate --root "$ROOT" --run 1              # 自动跑 eval-cmd
# 或人工判分：
"$PY" "$WS" gate --root "$ROOT" --run 1 --score 0.52
```

脚本自动执行，无需人工干预：

| 结果 | 脚本行为 |
|---|---|
| `score > R_best` → ACCEPTED | 建立技能快照 `snapshots/iter-XXXX/`，刷新 `R_best`，技能版本 +1 |
| `score <= R_best` → REJECTED | **技能回滚**到上一个已接受快照；审计记录照常写入 Wiki |

无论接受与否，都会向 `wiki/skill-impact.md` 追加一条含 unified diff 的审计记录。

### P3 · 终止与交付（硬停止点）

满足任一条件即停止：达到迭代上限 K / 达到目标分 / `R_best = 1.0`（早停）/
连续 N 轮无提升。

```bash
"$PY" "$WS" prune --root "$ROOT" --raw --keep 3          # 清理旧轨迹（不碰 wiki）
"$PY" "$WS" export --root "$ROOT" --target <导出目录> --with-wiki
```

导出后向用户交付：`skills/`（可直接用的成果）+ `wiki/patterns/`（沉淀的知识）
+ `wiki/skill-impact.md`（试错审计轨迹）+ `EXPORT-SUMMARY.md`（门控历史表）。

---

## 质量控制门禁

| 检查项 | 不通过的表现 | 处置 |
|---|---|---|
| 有基线分 | 从未执行 `baseline` | 补跑，否则门控无阈值 |
| 提案是原子的 | 一次改多个 skill / 多个改动点 | 拆分成多轮，每轮只改一处 |
| intent 非空 | `--intent` 为空 | 写不清意图说明根因没想透，退回第 ③ 步 |
| sources 有据 | `--sources` 为空 | 提案必须能溯源到具体 pattern |
| 训练轨迹纯净 | 执行时读过 `wiki/` | 本轮作废，重跑轨迹 |
| Wiki 有增量 | 连续多轮无新 pattern | 检查是否偷懒复用了旧结论 |

## 已知陷阱

详见 `references/pitfalls.md`。最关键的三个：

1. **负迁移**：小模型进化出的技能常编码低层 workaround（如"一行一条命令"），
   迁移到强模型反而限制其能力。跨模型复用前先判断是**通用程序**还是**特化 workaround**。
2. **Wiki 无自动剪枝**（论文已知缺陷）：长程运行会膨胀。用 `prune` 定期清理
   raw 与快照；pattern 页面若过度碎片化，需人工合并。
3. **门控过严会漏掉中性提案**：严格"必须涨分"可能拒绝掉后续才有收益的改动。
   若某提案被拒但你认为方向正确，可在 pattern 中记录，换一个更小的改动点重试。

## 文件索引

| 文件 | 何时读 |
|---|---|
| `references/architecture.md` | 需要理解设计原理、向他人解释时 |
| `references/loop-playbook.md` | 每步的详细判据、提示词模板、评估脚本样例 |
| `references/templates.md` | 新建 pattern / skill / eval 脚本时取模板 |
| `references/pitfalls.md` | 结果异常、出现负迁移、Wiki 膨胀时 |
| `scripts/wikiskill.py` | 全部命令的实现与参数说明 |
