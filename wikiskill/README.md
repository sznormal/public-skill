# wikiskill — 技能进化框架

把 arXiv:2608.27454（WikiSkill）的论文方法落地为**可执行的工作流**：
让 agent 技能在验证集门控下逐轮进化，同时把每一轮的经验（含失败的尝试）
永久沉淀进一个**永不回滚**的知识库。

## 核心思想

| 层 | 是什么 | 生命周期 |
|---|---|---|
| `raw/` | 执行轨迹 | 只追加，不可修改 |
| `wiki/` | 编译后的失败模式、成功策略、提案审计 | **永不回滚** |
| `skills/` | 可执行技能 | 可回滚（快照） |

**技能是会被推翻的假设；Wiki 是不可否认的事实积累。**
被否决的提案连同 diff 一起永久留档——这是整个方法最大的价值来源。

## 快速开始

```bash
PY="C:/Users/29206/.workbuddy/binaries/python/versions/3.13.12/python.exe"
WS="C:/Users/29206/.workbuddy/skills/wikiskill/scripts/wikiskill.py"
ROOT="d:/cctest/workspace/wikiskill/<项目名>"

# 1. 立项（评估命令需输出 JSON: {"score": 0.42, "details": [...]}）
"$PY" "$WS" init --root "$ROOT" --name "<项目名>" \
  --eval-cmd "python eval.py --skills {skills} --split {split}"

# 2. 基线
"$PY" "$WS" baseline --root "$ROOT"

# 3. 每轮四步
"$PY" "$WS" ingest   --root "$ROOT" --run 1 --file traj/*.json
"$PY" "$WS" pattern new   --root "$ROOT" --slug <s> --title <t> --kind failure --run 1 --body-file b.md
"$PY" "$WS" propose  --root "$ROOT" --run 1 --skill <n> --action patch --diff-file d.diff --intent "..."
"$PY" "$WS" gate     --root "$ROOT" --run 1

# 4. 交付
"$PY" "$WS" export --root "$ROOT" --target <导出目录> --with-wiki
```

详细规程见 `SKILL.md`，每步判据与提示词模板见 `references/loop-playbook.md`。

## 命令速查

| 命令 | 作用 |
|---|---|
| `init` | 初始化三层工作区 + 基线快照 |
| `baseline` | 记录无技能基线分（门控阈值起点） |
| `ingest` | 写入本轮训练轨迹 |
| `pattern new/edit/list/show` | 维护 wiki 模式（append / replace / insert 三编辑原语） |
| `log` | 追加进化日志 |
| `propose` | 登记原子提案（含 diff 与溯源 pattern） |
| `gate` | 验证门控：接受建快照，拒绝则**回滚技能**并保留审计 |
| `status` | 状态面板（含门控历史与红线提醒） |
| `prune` | 清理旧轨迹与快照（**不触碰 wiki**） |
| `export` | 导出技能集 + 门控历史摘要 |

全部命令支持 `--json` 输出（status / gate / evaluate / pattern list）。

## 三条红线

1. **Wiki 永不回滚** — 工具未提供任何删除 wiki 内容的命令
2. **原子提案** — 每轮只改一个 skill 的一处
3. **训练 rollout 期间 Inference Agent 禁止访问 `wiki/`**
   （论文消融：给它看反而从 63.7% 掉到 60.9%）

## 目录结构

```
wikiskill/
├── SKILL.md                  主规程：四组件循环的操作步骤与门禁
├── README.md                 本文件
├── scripts/
│   └── wikiskill.py          工作区与状态机管理（纯标准库，Python 3）
└── references/
    ├── architecture.md       论文原理、关键实验数据、消融结论
    ├── loop-playbook.md      每步判据、提示词模板、评估脚本样例
    ├── templates.md          pattern / SKILL / PURPOSE / 日志 模板
    └── pitfalls.md           10 个已知陷阱与规避方法
```

## 与论文的差异

| 项 | 论文 | 本实现 |
|---|---|---|
| Wiki 剪枝 | 缺失（论文承认） | 补 `prune` 命令 |
| 技能注入 | 全量注入 prompt | 由使用者决定（导出后用） |
| 门控阈值 | 严格 `>` | 相同，日志区分"低于"与"持平" |
| Wiki Maintainer / Proposer | LLM agent | 由 AI 助手按 `SKILL.md` 规程扮演 |
