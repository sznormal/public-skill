# norma-lit-review v0.8.0 补齐报告

> 日期：2026-09-06
> 版本：v0.7.0 → **v0.8.0**
> 位置：`~/.workbuddy/skills/norma-lit-review/`（用户级，已生效）
> 备份：`~/.workbuddy/backups/norma-lit-review-v0.7.0-backup-20260906.zip`

## 一、这次补的是什么

v0.7.0 只解决了 arXiv 单库。正式刊出文献（期刊/会议论文）在 skill 里仍是 WebFetch 兜底，
且 T4 文献计量型一上来就降级。本次补齐 **三个免 key 的正式刊出 API**，一次性接上三条链路：

| 链路 | 补前 | 补后 |
|------|------|------|
| **P2 多库检索** | 正式刊出靠 WebFetch / S2（1 req/s 易 429） | OpenAlex 脚本化检索（`fetch_lit.py search`） |
| **P6 参考文献核验** | DOI 靠 doi.org / S2 | Crossref 批量核验（`fetch_lit.py verify`），**DOI 注册源，判定更权威** |
| **T4 文献计量** | 无 WoS/Scopus 订阅即降级为 T1 | OpenAlex `cited_by_count` + OpenCitations 引文网络，**不再直接降级** |

---

## 二、新增 `scripts/fetch_lit.py`

纯 stdlib（urllib / json / difflib），**无需 pip、无需 venv、无需任何 API key**。

| 子命令 | 后端 | 用途 | 默认限速 |
|--------|------|------|---------|
| `search` | OpenAlex | P2 正式刊出检索 | 0.5 秒/请求 |
| `verify` | Crossref | P6 DOI 核验（0.70 标题相似度） | 0.5 秒/请求 |
| `citing` | OpenCitations | T4 引文关系（施引 / 参考文献） | 1.5 秒/请求 |
| `enrich` | OpenAlex | 按 DOI 取规范元数据 + 被引数 | 0.5 秒/请求 |

### 邮箱：按你的要求做成交互式提示

OpenAlex / Crossref 的 polite pool 需要一个邮箱（**不是注册、不是 API key**，官方仅作限流联系方式）。
获取顺序：

1. `--mailto you@example.com`
2. 环境变量 `LIT_MAILTO`
3. **运行时交互式询问**（默认，仅当 stdin 为交互终端）
4. 都没有 → 公共池，并在 stderr 明确告警

- **不落盘**：邮箱不写入任何配置文件，符合你"运行时再问我"的选择。
- 想免除询问：设 `LIT_MAILTO`，或加 `--no-prompt` / `LIT_NO_PROMPT=1`（脚本化调用用）。
- **不提供邮箱也能正常运行**，仅限速更严。

---

## 三、实测结果（全部联网真跑，非推断）

| 测试 | 结果 |
|------|------|
| `search`（相关度默认） | 返回 3 篇**全部贴题**：制造业具身智能 / 软体机器人 / 人在回路具身智能 |
| `enrich` | `10.1038/nature14539` → "Deep learning"（Nature 2015，LeCun/Bengio/Hinton），`cited_by_count=84258` |
| `verify` 四态 | MATCH 1.0 ／ DOI_MISMATCH 0.24 ／ NOT_FOUND ／ NO_DOI —— **全中** |
| `citing` 参考文献方向 | 正常取回（原始 40 条），DOI 提取正确 |
| `citing` 施引方向 | 高被引 DOI **60 秒超时** → 按预期降级，输出替代建议，退出码 2 |
| 离线分支 | `--help`、dry-run URL、缺参数退出码 1、非法输入退出码 1、邮箱四种路径全部正确 |

---

## 四、实测发现的真实问题（已修 / 已写进文档）

这几个如果不实测，照抄官方文档一定会踩：

1. **OpenCitations 的 `metadata` 端点已下线，返回 HTTP 410 Gone** → 脚本不提供该端点，
   取元数据走 `enrich`（OpenAlex）。
2. **OpenCitations 的施引查询对高被引 DOI 常超时**（实测 60s）→ 单独放宽到 60s 超时，
   超时报 ERROR + 退出码 2，并给出"用 `cited_by_count` 兜底"的建议。**不是脚本故障**，已写进文档。
3. **空数组 ≠ 零被引**，只表示未被 COCI 索引 → 输出固定带这条 note，禁止据此判定文献无影响力。
4. **OpenAlex 排序陷阱**：`--sort cited_by_count:desc` 会拉入"高被引但主题无关"的论文
   （实测搜具身智能返回 6G 综述）→ help 与文档均提示改用 `--cited-by-min` 过滤。
   已实测对照：默认相关度排序返回的全部贴题。
5. **argparse 共享参数陷阱**（延续 v0.7.0 的修法）：公共参数用 SUPPRESS + 双 parents，
   放在子命令前后都生效。
6. **`isatty` 判定不可靠**：本环境 `< /dev/null` 仍被判为交互终端 → 保留 EOFError 降级作最终保险，
   非交互时不会卡死，并支持 `LIT_NO_PROMPT=1` 显式跳过。
7. **Crossref 的 404 是确定性不存在**，不重试——与网络错误分开处理。

---

## 五、文档改动（7 个文件）

| 文件 | 改动 |
|------|------|
| `SKILL.md` | `version: 0.7.0 → 0.8.0`；设计理念第 4 条补 OpenAlex（免 key、免订阅） |
| `stages/01-search-strategy.md` | **T4 分支不再一上来降级**：改为 OpenAlex + OpenCitations 结构化替代源；数据库表加 OpenAlex 行 |
| `stages/02-multi-db-search.md` | 新增 §2.4 OpenAlex 检索（含命令示例、邮箱说明、排序陷阱）；原 IEEE/万方顺延为 2.5/2.6；检索摘要加 OpenAlex 行 |
| `stages/04-analysis.md` | T4 量化图谱补数据源与边界（超时兜底、空数组≠零被引、须透明披露） |
| `stages/06-reference-verification.md` | §2-A 脚本分工表加 `fetch_lit.py verify`（Crossref），补五态说明与邮箱交互规则 |
| `modules/verified-retrieval-protocol.md` | L1 层补三库；新增 §2.5 正式刊出三库（政策表 + **6 条实测边界**）；§六 明确三脚本分工，避免重复造轮子 |
| `modules/stem-databases.md` | 新增 OpenAlex / Crossref / OpenCitations 三节（含各自的坑）；决策树加"正式刊出无订阅"分支 |
| `README.md` | 依赖说明、API Key/邮箱章节、文件树 |

---

## 六、回滚

```bash
# 回滚到 v0.7.0
unzip -o ~/.workbuddy/backups/norma-lit-review-v0.7.0-backup-20260906.zip -d ~/.workbuddy/skills/
# 仅移除新脚本（其余改动保留）
rm ~/.workbuddy/skills/norma-lit-review/scripts/fetch_lit.py
```

---

## 七、遗留（本次未动）

- 空 `templates/` 目录仍未被引用。
- frontmatter 非标准字段 `partner` / `skill_type` / `afp_spec_target` 仍在。
- 阶段总表漏列 `gap_summary.md`、`references.bib`。
- `verify_references.py` 的 `--api-key` 会进 shell history（README 已主推环境变量，风险可控）。
- 中文正式刊出仍无解（知网/万方/维普无开放 API），维持既有路径：有 DOI 走 Crossref，无 DOI 走 WebSearch。
