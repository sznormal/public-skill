# 模板库

## 1. Pattern 页正文模板

`pattern new --body-file` 传入的正文（元数据与"更新记录"由脚本自动生成，不要手写）：

```markdown
## 现象 / Evidence

<br>
可观测的事实。写清楚触发条件、频率、影响面。
例：Qwen-4B 处理超过 50 行的工作表时，逐行写入公式导致交互轮次耗尽（10/10 次复现）。

## 根因 / Root cause

<br>
为什么会发生。必须落在可操作的层面，不能停在症状描述。
反例："模型不够聪明" / "要注意格式"
正例："模型采用一行一次工具调用的串行策略，50 行即耗尽 50 轮预算"

## 处置 / Workaround

<br>
具体、可执行的动作。技能可以直接照做。
正例："把全部公式构造成单个列表，一次调用写入整列（`ws[col] = formulas`）"
```

### 命名规范（slug）

- 用短横线：`row-by-row-exhaustion`、`encoding-mismatch-csv`
- **按根因命名，不按症状命名**：`budget-exhausted`（症状）→ `row-by-row-exhaustion`（根因）
- 长度控制在 3~4 个词

### 粒度判断

| 信号 | 处置 |
|---|---|
| 一个 pattern 里出现多个不同根因 | 拆成多个页面 |
| 多个 pattern 根因相同、只有场景不同 | 合并，在"现象"里列多个场景 |
| 出现次数长期为 1 | 可能是偶发噪声，暂不据此改技能 |

---

## 2. SKILL.md 模板

```markdown
---
name: <skill-name>
description: <一句话说明做什么、什么时候用>
---

# <技能标题>

## 适用范围
<什么情况下启用本技能；什么情况下不该用>

## 操作步骤
1. <步骤>
2. <步骤>

## 已知陷阱
- <陷阱> → <规避动作>

## 变更记录
- iter-XXXX: <改了什么，为什么>
```

`description` 决定技能是否被正确触发，要写"做什么 + 什么时候用"。

---

## 3. PURPOSE.md 模板

技能目录下与 `SKILL.md` 并列，**把每条规则映射回触发它的 pattern**：

```markdown
# <skill-name> 溯源说明

## 本技能解决的模式
| Pattern | 类型 | 关联规则 |
|---|---|---|
| `row-by-row-exhaustion` | failure | 「操作步骤」第 2 条：批量写入 |
| `formula-relative-ref` | failure | 「已知陷阱」第 1 条 |

## 未解决的问题
- `merged-cell-detection`：尚未找到稳定处置方案，见 pattern 页

## 创建与演进
- iter-0001: 由 pattern `row-by-row-exhaustion` 触发创建
- iter-0004: 由 pattern `multi-operation-loop` 触发，新增「每种操作仅一次」
```

**"未解决的问题"一栏很重要**——它把 Wiki 里尚未转化的知识显式标出来，
是下一轮提案的候选池。

---

## 4. 进化日志摘要模板

`log --body-file` 传入：

```markdown
### 本轮概况
- 训练任务 20 条，通过 9 条（45%），上轮 40%
- 主要失败类别：A 类 6 条、B 类 3 条、C 类 2 条

### 新发现
- [NEW] `xxx-yyy`：<一句话>
- [UPDATE] `aaa-bbb`：<补充了什么证据>

### 与上次迭代的关系
- 上轮针对 `ccc-ddd` 的改动**已生效**：该类失败从 5 条降到 1 条
- 上轮针对 `eee-fff` 的改动**未见效**：仍失败 4 条，需换方向

### 下轮重点关注
- ...
```

"与上次迭代的关系"是最有价值的一节——它把跨迭代的因果链显式写出来。

---

## 5. 提案 diff 模板

`propose --diff-file` 传入。有 git 就用 `git diff`，没有就手写：

```diff
--- a/skills/excel-formula/SKILL.md
+++ b/skills/excel-formula/SKILL.md
@@ -11,3 +11,5 @@
 3. 保存文件
+
+## 已知陷阱
+- 合并单元格会导致批量写入错位 → 写入前先检测 merge_cells
```

**diff 会被永久写入 `skill-impact.md`**，所以即使提案被拒，
未来也能看清"当时具体改了什么"。不要省略。

---

## 6. 评估集 JSON 模板

`train.json` / `val.json`：

```json
[
  {
    "id": "T001",
    "input": "任务输入",
    "expected": "标准答案",
    "metadata": {"category": "A", "difficulty": "hard"}
  }
]
```

`metadata.category` 便于按失败类别聚合，直接对应 pattern 的分类。

---

## 7. state.json 字段说明

由脚本自动维护，一般无需手工编辑：

| 字段 | 含义 |
|---|---|
| `r_baseline` | 无技能基线分（P1 记录） |
| `r_best` | 当前门控阈值，只在 ACCEPTED 时刷新 |
| `current_run` | 已进行到的轮次 |
| `skills_version` | 接受次数 |
| `last_accepted_snapshot` | 回滚基准快照名 |
| `proposals[]` | 全部提案（含 verdict / score / diff） |
| `history[]` | 门控历史（score / prev_best / verdict） |
| `early_stopped` | `R_best = 1.0` 时置 true |
