# P2 · 多库检索执行

> Norma理工科文献综述 · Stage 02
> 目标：按 P1 制定的策略，在选中数据库中执行检索，收集原始文献列表

---

## 一、检索前检查

1. 确认 P1 阶段产物已保存：`{project_path}/outputs/lit-review/search_strategy.md`
2. 确认用户已确认检索策略
3. 从 HUD 读取 `databases`、`keywords_cn`、`keywords_en`、`time_range`
4. **加载验证检索协议**：详读 `modules/verified-retrieval-protocol.md`（真实双语检索 +
   API 级核验的已验证流程，含 S2_API_KEY 配置与中文 WebSearch 核 DOI 边界）
5. **加载检索方法论**：详读 `modules/search-methodology.md`，并按 §二 **初始化检索日志**
   `search_log.md`（写入表头：日期/数据库/检索式/限定/命中数/备注）。
   此后**每执行一次检索，立刻追加一行日志**——检索式必须是可原样重跑的完整文本。

---

## 二、逐库检索执行

> **检索层级（详见验证协议 §一）**：优先 **L1 API 客户端**（arXiv API / Semantic Scholar API），
> 真实可复现、自带限速；当环境无脚本运行能力或网络受限时，退 **L2 WebSearch 兜底**，
> 但必须**逐条**核对 DOI/编号并透明披露"经联网核对"。两层都要求每条带 `verifiable_id`。

### 2.1 知网（CNKI）

**方式**：调用学术数据库 API 或 WebFetch 访问知网高级检索页面

**⚠️ 中文核验边界（验证协议 §三）**：原装中文客户端**不爬知网/万方**（ToS 与法律风险，
Zero-scraping），无法做"标题级"自动核验。务实做法——用 **WebSearch 直接搜「题名 + 第一作者 + 期刊」**，
命中知网/万方页后核对 **DOI 与卷期页**（这比调原装中文客户端更可靠）。三态语义：
`matched / unmatched / skipped`，查不到只进人工确认清单，**永不自动判伪造**。

**检索参数**：
- 主题/关键词组合：按 P1 检索式
- 时间范围：`{time_range}`
- 来源类型：期刊 + 会议 + 博硕（按需勾选）

**输出**：论文标题、作者、摘要、关键词、发表年份、来源期刊、被引次数

### 2.2 Semantic Scholar

**方式**：调用 Semantic Scholar API（L1 优先；详见验证协议 §二.2）

```
GET https://api.semanticscholar.org/graph/v1/paper/search?
  query={encoded_query}&
  year={start}-{end}&
  limit=100&
  fields=title,authors,abstract,year,venue,citationCount,externalIds
```

**优势**：字段丰富，含 DOI/ArXiv ID。
**⚠️ S2_API_KEY（验证协议 §二.3，可选）**：未认证层约 1 req/s，本环境 IP 易持续 429；
配置 `S2_API_KEY` 后限速升至 10 req/s。**本 skill 不内置任何密钥**——请用户自行到
Semantic Scholar 官网免费申请 S2_API_KEY，再以环境变量提供：
`export S2_API_KEY="你的key"`（Linux/macOS）或 `set S2_API_KEY=你的key`（Windows），
再运行 `python scripts/verify_references.py --input refs.json`。
未配置也能正常运行，仅限速更严。

### 2.3 arXiv

**方式**：运行 `scripts/fetch_arxiv.py`（L1 优先；**免费、无需任何 API key**、自带 3 秒/请求限速）

```bash
# 按检索式取回元数据：--categories 自动转 cat: 子句，--year-from/--year-to 限定提交年份
python scripts/fetch_arxiv.py search \
    --query 'all:"embodied intelligence"' \
    --categories cs.RO,eess.SY \
    --year-from 2022 --max-results 50 \
    --output raw_arxiv.json

# 只打印最终 API URL（写进 search_log.md 留痕用），不发起请求
python scripts/fetch_arxiv.py search --query 'cat:cs.RO AND all:manipulation' --dry-run
```

底层即 arXiv Export API（`https://export.arxiv.org/api/query`，返回 Atom XML）；脚本已封装
检索式拼装、分页、限速与 429/5xx 退避，输出 JSON 可直接并入 `raw_literature_list.json`
（自带 `verifiable_id`、`arxiv_id`、`primary_category`、`year` 等字段）。

**注意**：分类限定到理工科（cs.*, eess.*, stat.*, physics.*, math.*）。
**标题交叉校验**：同一脚本的 `verify` 子命令按 **0.70 相似度**比对清单标题与 API 规范标题，
可抓出"ID 有效但清单标题漂移"（验证协议 §四 案例）：

```bash
python scripts/fetch_arxiv.py verify --input refs.json --output arxiv_verify.json
```

### 2.4 OpenAlex（正式刊出主力，免订阅）

**方式**：运行 `scripts/fetch_lit.py search`（L1；**免费、无需 API key**、自带 0.5 秒/请求限速）

```bash
# 正式刊出检索：限定年份 / 类型 / 最低被引
python scripts/fetch_lit.py search \
    --query "machine vision defect detection" \
    --year-from 2020 --type article --cited-by-min 10 \
    --max-results 50 --output raw_openalex.json

# 只打印最终 API URL（写进 search_log.md 留痕用），不发起请求
python scripts/fetch_lit.py search --query "edge computing" --dry-run --no-prompt
```

输出字段含 `doi` / `verifiable_id` / `venue` / `year` / `cited_by_count` / `is_oa` / `topics`，
可直接并入 `raw_literature_list.json`；**`cited_by_count` 让 T4 计量不必依赖 WoS/Scopus 订阅**。

**邮箱（polite pool）**：首次运行会**交互式询问邮箱**——不是注册、不是 API key，
官方仅作限流联系方式；也可 `--mailto you@example.com` 传参，或设环境变量 `LIT_MAILTO`；
脚本化/无人值守调用加 `--no-prompt`。**不提供邮箱也能正常运行，仅限速更严。**

⚠️ **排序陷阱（实测）**：默认按相关度即可。用 `--sort cited_by_count:desc` 会拉入
"高被引但主题无关"的论文（实测搜具身智能却返回 6G 综述）。
要按影响力筛选，请用 `--cited-by-min` 过滤，而不是改排序。

### 2.5 IEEE Xplore（可选）

**方式**：WebFetch 访问 IEEE 搜索结果页（注意：可能需要机构订阅）

### 2.6 万方数据（可选）

**方式**：WebFetch 访问万方高级检索

---

## 三、去重与合并

### 去重规则
1. DOI 精确匹配（最可靠）
2. 标题相似度 > 90%（Levenshtein 距离）
3. 同一论文的中英文版本（中文期刊+英文会议）→ 保留英文版，标注中文版信息

### 合并输出
- 生成 `raw_literature_list.json`：
```json
[
  {
    "id": "lit_001",
    "title": "...",
    "title_cn": "...",
    "authors": ["..."],
    "year": 2024,
    "abstract": "...",
    "source": "cnki|arxiv|semantic_scholar",
    "doi": "...",
    "arxiv_id": "2409.05556",
    "verifiable_id": "arxiv:2409.05556",
    "citation_count": 42,
    "venue": "IEEE Access",
    "keywords": ["...", "..."]
  }
]
```

> ⚠️ **真实性前置约束**：每条文献必须记录一个**可联网核验的标识** `verifiable_id`
> （取值优先级：arXiv ID > DOI > 知网题名+第一作者），用于 P5 生成参考文献和
> P6 真实性核验。
> - 从 Semantic Scholar / arXiv API 返回结果中直接取 `externalIds.ArXiv` 或 `DOI`，
>   不要自己"编"或留占位符（如 `arXiv:xxxx.x`）。
> - 若某项确实查不到任何可核验标识，将该条 `verifiable_id` 置空并标 `"need_verify": true`，
>   提醒用户后续人工补全——**宁可少一条真实文献，也不要写入一条疑似编造的文献**。

---

## 三-B、按 review_type 分支的采集要求

- **T1 / T5**：采集代表性文献即可，每条记录 `verifiable_id`；数量达标（20–40）即可进入 P3。
- **T2 / T3**：每条文献**必须记录纳排判定与理由**（供 P3 生成 PRISMA 流程图）；去重后保留全部候选（含被排除的），不可只留入选的——排除文献也要进原始列表并标 `excluded_reason`。
- **T4**：除常规字段外，必须导出**结构化引文数据**（作者、年、期刊、被引、参考文献列表），供 P4 做共现 / 演进分析；建议导出为 CSV / RIS。

---

## 三-C、召回率测试（强制，查全率保障）

按 `modules/search-methodology.md` §三 执行：

1. 取 P1 登记的**种子文献表**，逐篇检查是否出现在 `raw_literature_list.json`；
2. 有漏召 → 分析原因（同义词缺失 / 库未覆盖 / 时间窗 / 字段限定），扩检索式补检，
   并在 `search_log.md` 追加"补检"行；
3. **漏召种子按类型诊断**（见 `modules/search-methodology.md` §3.5）：若漏召的是
   **具名系统/框架/基准**，主题检索式召不回它们——追加 3–5 组**具名查询组**
   （`all:"系统名1" OR all:"系统名2"`，每组 30–50 条，同域合组）；
4. 补检两轮仍漏 → 记录"手动/雪球补入"，并在综述方法节说明；
5. 结果写入摘要：`种子召回率：{hit}/{total}（漏召处置：...）`，并记录**逐轮诊断过程**
   （每轮配置 + 召回率 + 本轮诊断结论），而非只写最终值——审稿人视其为方法学证据。

**⚠️ 清单生成规则（强制）**：召回/漏召清单必须**由脚本从 `search_raw/*.json` 重新生成**，
禁止手抄历史输出；重算后有出入必须留"口径更正记录"，不回溯改写历史数字。

## 三-D、遗漏风险评估（P2 结束前必过）

按 `modules/search-methodology.md` §五 清单逐项自查（语言偏差 / 库覆盖 / 时间窗 /
术语漂移 / 灰色文献 / 付费墙盲区），结论写入 `search_log.md` 末尾"遗漏风险评估"节；
**残留风险不隐瞒**——写入综述"局限"段。

---

## 四、初步统计

输出检索摘要：

```
╭─ 检索结果摘要 ──────────────────────────────────╮
│ 知网：{N}篇
│ Semantic Scholar：{N}篇
│ arXiv：{N}篇
│ OpenAlex：{N}篇
│ -------------------------------------------------
│ 去重后总计：{N}篇
│ 时间分布：2020:{n} 2021:{n} 2022:{n} 2023:{n} 2024:{n}
│ 高引论文（>50次）：{N}篇
╰──────────────────────────────────────────────────╯
```

---

## 五、Hard Stop

展示检索结果摘要和去重后总数。如果结果过少（<20篇）或过多（>500篇），
建议调整检索策略回到 P1。否则用户确认后进入 P3。

---

## 六、产出物

- `{project_path}/outputs/lit-review/raw_literature_list.json`：原始文献列表
- `{project_path}/outputs/lit-review/search_log.md`：**检索日志**（逐次检索留痕 +
  种子召回率 + 遗漏风险评估）
- 更新 HUD：`literature.total_found`、`search_log.*`
