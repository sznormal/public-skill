# norma-lit-review v0.8.1 — 遗留项清理 + 完整触发测试报告

> 测试日期：2026-09-06 · 版本：0.8.0 → **0.8.1** · 位置：`~/.workbuddy/skills/norma-lit-review/`
> 备份：`~/.workbuddy/backups/norma-lit-review-v0.8.0-backup-20260906.zip`（改动前全量）

---

## 一、遗留项清理（4/4 完成）

| 遗留项 | 处理 | 验证 |
|------|------|------|
| 空 `templates/` 目录零引用 | `ls -la` 确认含隐藏文件也为空 → `rmdir` 删除 | 全包 grep `templates/` = 0 处 |
| `verify_references.py` 的 `--api-key` 走命令行（密钥会进 shell history） | 移除该参数，只保留环境变量 `S2_API_KEY`；误用 `--api-key` 时打印安全警告并正常降级运行 | 实测：警告出现；环境变量路径无警告 |
| frontmatter 非标准字段（partner / skill_type / afp_spec_target） | 删除，只留 `name / version / description / agent_created` | 回读 frontmatter 确认 |
| 阶段总表漏列产物 | P4 补 `gap_summary.md`，P5 补 `references.bib` | SKILL.md 路由表回读确认 |

版本号自增：0.8.0 → **0.8.1**（纯清理，无新能力 → PATCH）。

## 二、完整触发测试（三层，全部通过）

### 第 1 层：引用完整性扫描 ✅ 50/50
用正则扫描全部 `.md` 文件中出现的 `stages/`、`modules/`、`scripts/` 文件引用，逐一核对磁盘是否存在。
**结果：50 处引用全部真实存在**。这项是防 v0.7.0「引用不存在文件」硬伤复发的关键闸门。

### 第 2 层：文档命令可执行性 ✅ 8/8
把文档里写出的脚本命令示例逐条真跑（dry-run 或真实执行）：

| 文档位置 | 命令 | 结果 |
|------|------|------|
| stages/02 §2.3 | `fetch_arxiv.py search --query 'all:"embodied intelligence"' --categories cs.RO,eess.SY --year-from 2022 ...` | ✅ |
| stages/02 §2.3 | `fetch_arxiv.py search --query 'cat:cs.RO AND all:manipulation'` | ✅ |
| stages/02 §2.3 | `fetch_arxiv.py verify --input refs.json --output arxiv_verify.json`（真跑联网） | ✅ |
| stages/02 §2.4 | `fetch_lit.py search --query "machine vision defect detection" --year-from 2020 --type article --cited-by-min 10 ...` | ✅ |
| stages/02 §2.4 | `fetch_lit.py search --query "edge computing"` | ✅ |
| stages/06 §2-A | `fetch_lit.py verify --input refs.json --output doi_verify.json`（真跑联网） | ✅ |
| stages/04 T4 | `fetch_lit.py enrich --dois 10.1038/nature14539` | ✅ |
| stages/04 T4 | `fetch_lit.py citing --doi 10.1038/nature14539 --direction both` | ✅ |

### 第 3 层：端到端触发模拟 ✅
派**全新上下文**测试代理（未接触本对话），只给它 SKILL.md 路径与模拟用户提问：
「帮我梳理一下机器视觉缺陷检测方面的文献，准备投稿中文核心」。

| 检验点 | 结果 |
|------|------|
| 触发判定 | ✅ 按 description 触发词正确判定应触发，且符合触发隔离规则 |
| 第一轮回复 | ✅ 严格复现「首次上手」契约：四问（主题/时间范围/种子文献/目标期刊）+ 类型留给 P0 |
| P0 入口 | ✅ 第二轮自然进入 P0，推荐 T1 并给字数目标（中文 0.8–1.5 万字），列出五类型选项 |
| Hard Stop | ✅ 明示"必须用户明确选择后才进 P1，不替用户决定" |
| 边界遵守 | ✅ 未创建 outputs/lit-review、未写任何产物文件（测试约束被遵守） |

## 三、测试抓到的回归（已修复）

**P2-3 矛盾复发**：SKILL.md 写「检索策略、筛选标准、综述大纲**三处** Hard Stop」，README 写「P0（类型）、P1（策略）、P3（筛选）、P5（大纲）**四处**」——正是 v0.7.0 修过的问题，在后续编辑中静默复发。

**已修**：SKILL.md 统一为「P0（类型）、P1（检索策略）、P3（筛选标准）、P5（综述大纲）四处 Hard Stop」。

> **教训**：修复声明必须回归验证。发布前对旧问题关键词做一次 grep（如 `三处 Hard Stop`）成本极低，能拦住这类静默复发。

## 四、最终回归快照

- 失效引用（arxiv_client / ArxivClient / SemanticScholarClient）：**0 处**
- 正文版本标注（v0.x）：**0 处**（唯一 `v0.4` 为产物文档版本，非 skill 版本）
- `templates/` 残留引用：**0 处**
- 三脚本 `py_compile`：**全部通过**（编译缓存已清理）
- Hard Stop 口径：SKILL.md 与 README **一致（四处）**
- 备份链完整：v0.6 / v0.7.0 / v0.8.0 三份全量备份均在 `~/.workbuddy/backups/`

## 五、结论

**norma-lit-review v0.8.1 达到可交付状态**：审查发现的 P1/P2 全部闭环、遗留 P3 清零、三层测试全绿、触发行为经陌生上下文实测符合设计。

回滚方式：解压对应备份覆盖 `~/.workbuddy/skills/norma-lit-review/` 即可。
