# norma-lit-review 修复报告（v0.6 → v0.7.0）

修复日期：2026-09-06
修复范围：P1（1 项）+ P2（4 项），并新增 arXiv 取数脚本
备份位置：`~/.workbuddy/backups/norma-lit-review-v0.6-backup-20260906.zip`（83 KB，全量 24 条目，已校验可读）
回滚方式：解压该 zip，覆盖 `~/.workbuddy/skills/norma-lit-review/` 即可；新脚本 `fetch_arxiv.py` 为纯新增，删除即可回退

---

## 一、总体结论

| 项 | 修复前 | 修复后 |
|------|--------|--------|
| 综合评级 | 8.9 / 10（需修改） | **可交付**（原审查报告的阻塞项已清零） |
| `version` 字段 | ❌ 缺失 | ✅ `0.7.0` |
| 失效脚本引用 | ❌ 4 处指向不存在的 `arxiv_client.py` | ✅ 0 处，全部指向真实脚本 |
| 正文版本标注 | ❌ 8 处 `v0.6` | ✅ 0 处 |
| Hard Stop 表述 | ❌ SKILL.md「三处」vs README「四处」自相矛盾 | ✅ 统一为四处关键 Hard Stop |
| 章节编号 | ❌ stage01 四-B 排在四前；stage04 两个四-B | ✅ 单调有序 |
| arXiv 取数能力 | ❌ 只有核验、**不能按检索式检索** | ✅ 新增 `fetch_arxiv.py`（检索 / 取元数据 / 交叉校验） |

---

## 二、逐项修复对照

### P1 · frontmatter 缺 version（阻塞安装与更新）

| | 内容 |
|------|------|
| 文件 | `SKILL.md` |
| 修改 | 新增 `version: 0.7.0` |
| 版本依据 | 新增兼容能力（arXiv 检索脚本）→ MINOR 自增，0.6 → 0.7.0 |

### P2-1 · 失效脚本引用（最高优先，会让模型跑偏）

原文档 4 处引用了包内**根本不存在**的 `arxiv_client.py` / `ArxivClient` / `SemanticScholarClient`：

| 位置 | 修复前 | 修复后 |
|------|--------|--------|
| `stages/02` §2.3 | `ArxivClient.arxiv_id_lookup(id, title)` | `scripts/fetch_arxiv.py search` + `verify` |
| `stages/06` §2-A | `ArxivClient.arxiv_id_lookup` | `scripts/fetch_arxiv.py verify`（含四态说明） |
| `stages/06` §2-A | `SemanticScholarClient.lookup(...)` | `scripts/verify_references.py --input refs.json` |
| `modules/verified-retrieval-protocol` §2.1 | `ArxivClient.arxiv_id_lookup` | `scripts/fetch_arxiv.py` 的 `lookup` / `verify` |
| `modules/verified-retrieval-protocol` §六 | "复用 academic-research-skills 的脚本" | 改为描述本包两个脚本及配合方式 |

同时修掉 `stage06` 原有自相矛盾：既说"用 arxiv_client.py"又说"批量运行 verify_references.py"。
现以**分工表**明确：

| 场景 | 脚本 | 特点 |
|------|------|------|
| arXiv 单库（取规范标题 / 抓漂移） | `fetch_arxiv.py verify` | 免费、**无需 API key**、默认 3 秒/请求限速、输出 JSON |
| 混合批量（arXiv ID + DOI，出 Markdown 报告） | `verify_references.py` | 仅 stdlib，DOI 走 S2，可选 `S2_API_KEY` |

### P2-2 · 正文版本标注（违反"版本归 frontmatter"纪律）

清除 8 处 `v0.6` 标注：`SKILL.md` 设计原则第 11 条与文末页脚、`README.md` 页眉/引言/文件树注释/设计理念/版权节/页脚、`modules/stem-review-anti-patterns.md` 章节标题。
`stages/09` 中「保留 v0.4 终稿」是**用户稿件的版本号**，属业务内容，保留。

### P2-3 · Hard Stop 数量自相矛盾

`SKILL.md` 原写"检索策略、筛选标准、综述大纲**三处**"，漏了 P0，与 README 的"四处"冲突。
统一为：**P0 类型 / P1 策略 / P3 筛选 / P5 大纲**四处关键 Hard Stop（其余阶段结束亦有确认点）。

### P2-4 · 章节编号混乱

| 文件 | 修复前 | 修复后 |
|------|--------|--------|
| `stages/01` | 三 → 三-B → **四-B → 四** → 五 → 六（倒序） | 三 → 三-B → 四 → 五 → 六 → 七 |
| `stages/04` | 四 → **四-B → 四-B**（重复） | 四 → 四-B → 四-C |

---

## 三、新增 `scripts/fetch_arxiv.py`

**定位**：补上 P2 阶段缺失的"**按检索式检索**"能力——原有 `verify_references.py` 只能按已知 ID 核验，不能检索。

- 纯 Python 标准库（urllib / xml / difflib），**无需 pip、无需 venv、无需任何 API key**
- **限速为默认行为**：串行请求，相邻请求间隔默认 **sleep 3 秒**（arXiv 礼貌要求 ≈1 req/3s），`--sleep` 可调；429/5xx 指数退避重试
- 三个子命令：`search`（检索）、`lookup`（按 ID 取规范元数据）、`verify`（ID+标题 0.70 相似度交叉校验）
- `--dry-run` 只打印最终 API URL，便于把可复现检索式写进 `search_log.md`
- 输出 UTF-8 JSON，字段含 `verifiable_id` / `arxiv_id` / `primary_category` / `year`，可直接并入 `raw_literature_list.json`

### 实测证据

| 测试 | 方法 | 结果 |
|------|------|------|
| 语法编译 | `py_compile` | ✅ 通过 |
| 离线：参数/dry-run/错误处理 | 本地运行 | ✅ URL 拼装正确；缺参数退出 1；非法输入退出 1 |
| 离线：Atom 解析 | 本地样本 XML | ✅ `2409.05556v1` → id `2409.05556` + version `1`；错误条目被识别 |
| 离线：相似度 | 协议记载的真实漂移案例（CoELA） | ✅ 算得 **0.547 < 0.70**，正确判为 ID_MISMATCH |
| **联网：search** | 真实检索 cs.RO + embodied | ✅ 取回真实论文，字段完整（含 `verifiable_id`） |
| **联网：lookup** | `1706.03762` | ✅ 返回 "Attention Is All You Need"（v7 / 2017） |
| **联网：verify 四态** | 正常 / 漂移 / 伪造 / 无 ID | ✅ MATCH 1.0 / ID_MISMATCH 0.28 / NOT_FOUND / NO_ID |

> 修复过程中实测发现并修掉 2 个真实缺陷：`--dry-run` 等公共参数放在子命令后会被 argparse 拒绝（子命令默认值覆盖顶层赋值问题），已改为共享解析器 + SUPPRESS 方案，两种参数位置均可用。

---

## 四、遗留项（P3，本次未动，按最小侵入原则）

1. `templates/` 空目录未被任何文档引用 → 可删除或补模板
2. frontmatter 中 `partner` / `skill_type` / `afp_spec_target` 为非标准字段 → 不影响运行，参赛前可清理
3. SKILL.md 阶段总表漏列 `gap_summary.md`、`references.bib` 两个产出物
4. `verify_references.py` 的 `--api-key` 走命令行参数，可能进 shell history → README 已主推环境变量，风险可控

---

## 五、安装状态

本次修改**直接在用户级目录** `~/.workbuddy/skills/norma-lit-review/` 完成，无需额外安装步骤，刷新后即生效。
回滚：解压备份 zip 覆盖同名目录即可。
