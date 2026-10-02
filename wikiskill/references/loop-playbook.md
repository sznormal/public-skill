# 循环操作手册

SKILL.md 的补充：每一步的**详细判据、提示词模板、评估脚本样例**。
仅在需要时加载，不必一次读完。

---

## 第 ① 步 · Inference：轨迹采集规范

### 轨迹文件建议格式

`raw/iter-XXXX/<task-id>.json`：

```json
{
  "task_id": "T001",
  "input": "任务输入",
  "prediction": "模型最终输出",
  "ground_truth": "标准答案",
  "score": 0.0,
  "steps": [
    {"type": "reasoning", "content": "..."},
    {"type": "tool_call", "name": "bash", "args": "..."},
    {"type": "tool_output", "content": "..."}
  ],
  "metadata": {"steps_used": 42, "budget": 50, "terminated_by": "budget_exhausted"}
}
```

`metadata.terminated_by` 很有用——`budget_exhausted` 往往直接指向"交互预算耗尽"类
失败模式，是 pattern 的高价值来源。

### 采样策略

上下文窗口有限，不必全部送进分析。建议分层：

| 类别 | 采样量 | 用途 |
|---|---|---|
| 失败任务 | 优先全采（上限 10~15 条） | 根因分析 |
| 成功任务 | 采 3~5 条 | 提取成功策略 |
| 边界任务（勉强通过/轻微偏差） | 采 2~3 条 | 最有信息量，最容易被忽略 |

**优先采"上次修过但仍失败"的任务** —— 它们直接检验上一轮改动是否真的生效。

### 红线检查

执行任务的 agent 的 system prompt 中**只能注入 `skills/` 内容**。
若你在本轮为了让任务跑通而让执行 agent 读了 wiki，本轮轨迹作废。

---

## 第 ② 步 · Wiki Maintainer：根因分析提示词模板

把采样轨迹与该轮任务摘要一起交给分析，要求输出结构化结论：

```
你是 Wiki Maintainer。以下是第 {k} 轮的执行轨迹与任务结果摘要，
现有 wiki 模式目录如下：

{wiki/index.md 的内容}

请完成：
1. 对每条失败任务做根因分析，回答"为什么失败"而不是"失败了什么"
2. 从成功任务（尤其边界成功）中提取可复用策略
3. 判断每条结论属于：
   [NEW] 全新模式 → 给出 slug、title、kind
   [UPDATE] 已有模式的新证据 → 给出 slug 与补充内容
   [NONE] 已知模式的实例，无新信息 → 只增加出现次数

输出格式：
## NEW PATTERNS
（每条：slug / title / kind / 现象 / 根因 / 处置）

## PATTERN UPDATES
（每条：slug / 新增证据 / 是否需要修正原处置）

## RECURRING
（本轮重复出现的既有模式 slug 列表）

硬要求：
- 一个 pattern 只描述一类失败模式，不写流水账
- "处置"必须是可执行的具体动作，不能是"要小心"这类空话
- 区分症状与根因：超时是症状，逐行调用导致轮次耗尽才是根因
```

### 根因分析的三问

1. **这是症状还是根因？** 连续追问"为什么"直到落在可操作的动作上
2. **这个模式之前出现过吗？** 先查 `index.md`，避免重复建页
3. **处置是可执行的吗？** "注意格式"不合格，"写入前先用 `repr()` 检查转义"合格

---

## 第 ③ 步 · Skill Proposer：提案提示词模板

```
你是 Skill Proposer。你要基于持久知识库，提出**一个**原子技能改动。

可用资源（按需读取，不要一次全读）：
- wiki/index.md —— 模式目录
- wiki/patterns/*.md —— 某个模式的细节
- wiki/skill-impact.md —— 历史提案及其验证结果【必读，重点看 REJECTED】
- raw/iter-XXXX/*.json —— 原始轨迹

当前技能集：{skills/ 目录结构}
本轮任务结果摘要：{pass/fail 列表}

工作流程：
1. 先读 skill-impact.md，列出已被否决的改动方向，本轮不得重复
2. 从 index.md 中选出本轮最值得处理的 1~2 个 pattern
3. 读对应 pattern 与相关轨迹，确认根因
4. 提出唯一的改动：作用于单个 skill 的单个改动点

输出：
- target_skill: <技能名>
- action: create | patch
- intent: <一句话，为什么改、期望解决什么>
- sources: <触发该提案的 pattern slug 列表>
- diff: <unified diff 或清晰的变更描述>

硬约束：
- 只改一个 skill，只改一处
- 不得重复已被否决的改动方向
- 若本轮没有值得改的，明确输出 NO_PROPOSAL 并说明理由
```

### 判断提案质量的三个问题

| 问题 | 不合格的信号 |
|---|---|
| 能溯源到具体 pattern 吗？ | `--sources` 为空 |
| 一句话说得清意图吗？ | `--intent` 写得含糊冗长 |
| 是最小改动吗？ | 一次重写整个 SKILL.md |

### PURPOSE.md 必须同步更新

每条技能规则都应能映射回触发它的 pattern。格式见 `templates.md`。
这带来两个好处：技能可审计；pattern 变更时能定位受影响的技能。

---

## 第 ④ 步 · Gating：评估结果脚本样例

`eval-cmd` 的契约：接收 `{skills}` / `{split}` / `{root}` 占位符，
**stdout 输出 JSON**：

```json
{"score": 0.42, "details": [{"id": "T001", "pass": true}, {"id": "T002", "pass": false}]}
```

最小可用样例（`eval.py`）：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""用法: eval.py --skills <dir> --split val

约定: stdout 输出 JSON {"score": 0.42, "details": [...]}
      run_agent() 需自行实现——把 skill_text 作为 system prompt 调用你的 agent
"""
import argparse
import json
from pathlib import Path


def run_agent(task_input, system=""):
    """TODO: 接入你的 agent，返回预测字符串"""
    raise NotImplementedError


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skills", required=True)
    ap.add_argument("--split", default="val")
    a = ap.parse_args()

    cases = json.loads(Path(f"{a.split}.json").read_text(encoding="utf-8"))
    skill_text = ""
    for f in Path(a.skills).rglob("SKILL.md"):
        skill_text += f.read_text(encoding="utf-8") + "\n"

    details, total = [], 0.0
    for c in cases:
        pred = run_agent(c["input"], system=skill_text)
        ok = (pred.strip() == c["expected"].strip())
        details.append({"id": c["id"], "pass": ok})
        total += 1.0 if ok else 0.0

    print(json.dumps({"score": total / len(cases), "details": details}))

if __name__ == "__main__":
    main()
```

配置进工作区：

```bash
"$PY" "$WS" init --root "$ROOT" --name "proj" \
  --eval-cmd "python D:/cctest/workspace/proj/eval.py --skills {skills} --split {split}"
```

### 门控结果的解读

| 情况 | 含义 | 下一步 |
|---|---|---|
| ACCEPTED，涨幅大 | 改动命中根因 | 继续深挖同类 pattern |
| ACCEPTED，涨幅微小 | 改动有效但边际 | 换个方向，别在同一处打磨 |
| REJECTED，分数大跌 | 改动方向错误 | 在 pattern 中记录反证，换方向 |
| REJECTED，分数持平 | 中性改动 | 记录留档；若认为方向对，拆更小重试 |
| 连续 3 轮 REJECTED | 可能触及瓶颈 | 回到 P0 检查评估标准是否合理 |

---

## 完整一轮的命令序列（速查）

```bash
PY="C:/Users/29206/.workbuddy/binaries/python/versions/3.13.12/python.exe"
WS="C:/Users/29206/.workbuddy/skills/wikiskill/scripts/wikiskill.py"
ROOT="d:/cctest/workspace/wikiskill/<项目名>"
K=1

# ① 采集
"$PY" "$WS" ingest  --root "$ROOT" --run $K --file raw_traj/*.json
# ② 编译
"$PY" "$WS" pattern new   --root "$ROOT" --slug s --title t --kind failure --run $K --body-file b.md
"$PY" "$WS" pattern edit  --root "$ROOT" --slug s --mode append --run $K --body-file e.md --note n
"$PY" "$WS" log           --root "$ROOT" --run $K --body-file summary.md
# ③ 提案
"$PY" "$WS" propose --root "$ROOT" --run $K --skill sk --action patch \
  --diff-file d.diff --intent "..." --sources s1,s2
# ④ 门控
"$PY" "$WS" gate    --root "$ROOT" --run $K
# 查看
"$PY" "$WS" status  --root "$ROOT"
```
