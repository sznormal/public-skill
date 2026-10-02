# 验证检索协议（Verified Retrieval & Verification Protocol）

> Norma理工科文献综述 · Module
> 被 P2（多库检索）、P6（参考文献核验）引用。
> 来源：deep-research skill 的 lit-review 模式 + 本环境**实测验证**的真实运行经验
>      （managed Python 3.13 + 沙箱实测跑通 scripts/fetch_arxiv.py 与 scripts/verify_references.py）。
> 核心思想：**检索与核验必须"真实可复现"，占位编号 / 编造标题 / 臆测被引一律零容忍。**

---

## 一、两层检索范式（优先级）

| 层级 | 方式 | 何时用 | 真实性保障 |
|------|------|--------|-----------|
| **L1 API 客户端**（优先） | 直接调 arXiv / OpenAlex / Crossref / OpenCitations API（见 §二） | 环境可联网、且有脚本运行能力 | 返回数据库原始字段，最可信 |
| **L2 WebSearch 兜底** | 用 WebSearch / WebFetch 找题录 + 逐条核 DOI/编号 | L1 不可用（无脚本能力 / 网络受限） | 必须**逐条**核对 DOI/arXiv ID 并透明披露"经联网核对" |

> 无论哪层，最终每条文献都必须带一个 `verifiable_id`（arXiv ID > DOI > 知网题名+一作）。
> **没有可核验标识的文献，宁可少收，绝不写入疑似编造条目。**

---

## 二、英文核验引擎（实测可用）

### 2.1 arXiv API（免费、无需认证、无需 API key）
```
GET https://export.arxiv.org/api/query?id_list=2308.08155&max_results=1
```
- 返回 Atom XML，含 `<title>` / `<author>` / `<published>`。
- 已封装为 **`scripts/fetch_arxiv.py`**（纯 stdlib、无需 key、**默认 3 秒/请求**限速）：
  - `lookup --ids 2308.08155` → 取回规范元数据（自动剥离版本号、带 `verifiable_id`）；
  - `verify --input refs.json` → **题目交叉校验**：与规范标题做 **0.70 相似度**比对，
    输出 `MATCH / ID_MISMATCH / NOT_FOUND / NO_ID` 四态——
    **能抓出"ID 有效但清单标题漂移"**的隐藏错误。

### 2.2 Semantic Scholar API（DOI 优先 + 标题兜底）
```
GET https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,authors,year,externalIds,venue
GET https://api.semanticscholar.org/graph/v1/paper/search?query={title}&limit=5&fields=...
```
- **先 DOI 后标题**：DOI 命中即交叉核对标题（相似度 ≥ 0.70 才认 matched）。
- 内置 **429 退避**（背压 sleep + 刷新锚点），符合未认证 1 req/s 节流。

### 2.3 S2_API_KEY（强烈建议配置，解除限流）
- 客户端读取环境变量 **`S2_API_KEY`**（或命令行 `--api-key`）。
- 有 key：限速从 **1 req/s → 10 req/s**（min_interval 0.1s），否则未认证层易持续触发 429。
- 获取：https://www.semanticscholar.org/product/api → API Keys（免费 tier）。
- ⚠️ **安全（重要）**：**本 skill 不内置任何密钥，也不会替你保存 key。**
  - 不要把 key 写进会被云盘/版本库同步的目录（如百度网盘、GitHub 仓库）。
  - 推荐：用环境变量临时传入，或在本地**不入库、不同步**的文件里保存，由驱动脚本读取。
  - 用法（一次性内联，避免落盘）：
  ```bash
  S2_API_KEY="你的key" python verify_references.py
  ```

### 2.4 环境实测结论
- 任意 Python 3.8+（含 WorkBuddy 自带的 managed Python）仅用 **stdlib（urllib / xml）即可跑**，
  无需建 venv、无需 pip。
- 脚本自带节流与 429 退避；arXiv(http) / S2(https) 均可正常访问。

### 2.5 正式刊出三库（OpenAlex / Crossref / OpenCitations，实测）

三者**全部免费、无需注册、无需 API key**，已封装为 `scripts/fetch_lit.py`。

| 库 | 认证 | 用途 | 限速（现行政策） |
|------|------|------|------|
| **OpenAlex** | 无 key；填邮箱进 polite pool | P2 正式刊出检索、T4 被引统计 | 无邮箱约 1 万积分/天（列表 10 分/次）；上限 100 req/s |
| **Crossref** | 无注册；填邮箱进 polite pool | P6 DOI 权威核验 | polite：单条 10 req/s、列表 3 req/s；公共：单条 5、列表 1 |
| **OpenCitations** | 完全开放，连邮箱都不用 | T4 引文网络（共引 / 施引） | 建议 1–5 req/s；脚本默认 1.5 秒/请求 |

**邮箱（polite pool）不是密钥**：官方仅作限流联系方式，不注册、不发营销邮件。
获取顺序：`--mailto` → 环境变量 `LIT_MAILTO` → **运行时交互询问** → 公共池。
不提供邮箱也能跑，仅限速更严；脚本化调用用 `--no-prompt` 或 `LIT_NO_PROMPT=1` 跳过询问。

**实测边界（2026-09，写文档时必须保留，勿凭记忆改写）**：

1. OpenCitations 的 `metadata` 端点**已下线，返回 HTTP 410 Gone** →
   取元数据走 OpenAlex（`fetch_lit.py enrich`）。
2. OpenCitations 的**施引（citations）对高被引 DOI 常超时**（实测 60s 无响应），
   脚本报 ERROR 并以退出码 2 结束，同时给出"改用 `enrich` 取 `cited_by_count`"的建议
   ——**这是服务端限制，不是脚本故障**。
3. OpenCitations **空数组 ≠ 零被引**，只表示未被 COCI 索引，
   不得据此判定文献不存在或无影响力。
4. Crossref 的 404 是**确定性不存在**，不重试；须与"网络错误 / 超时"分开对待。
5. OpenAlex 用 `--sort cited_by_count:desc` 会牺牲相关度，拉入"高被引但主题无关"的论文；
   要按影响力筛选用 `--cited-by-min` 过滤。
6. Crossref 用共用邮箱（如 `info@xxx.com`）会被**连坐限流**，必须让用户填个人邮箱。

**子命令与阶段对应**：

    search  → P2 正式刊出检索（OpenAlex）
    verify  → P6 DOI 核验（Crossref，0.70 标题相似度）
    citing  → T4 引文关系（OpenCitations，施引 / 参考文献）
    enrich  → 按 DOI 取规范元数据 + 被引数（OpenAlex）

---

## 三、中文核验（关键边界）

- **原装中文客户端不爬知网/万方**：受 ToS 与法律风险约束，CNKI/Wanfang 检索页与全文页
  **绝不抓取**（Zero-scraping）。因此中文题录无法用开放 API 自动"标题级"核验，
  只能核验到 DOI 存在性（doi.org RA 分诊 + Handle 存在）。
- **务实兜底（本环境验证有效）**：用 **WebSearch 直接搜"题名 + 第一作者 + 期刊"**，
  命中知网/万方页后**核对 DOI 与卷期页**，比调原装中文客户端更可靠——
  因为 WebSearch 能看到期刊页题录，而客户端只到"DOI 存在"为止。
- **三态语义**：`matched / unmatched / skipped`——一个 miss **永不**被判为"伪造"
  （precision over recall）；查不到只进人工确认清单，不自动删。

### 3.1 中文 DOI 的双轨体系（2026-10-01 实测确立，**易错点**）

**⚠️ 中文期刊的 DOI 注册在 CNKI/chndoi 体系，**不进 Crossref**。**
因此 `api.crossref.org/works/{DOI}` 或 Semantic Scholar 对中文刊返回 **404 是常态，毫无证明力**——
**绝不能据此判定"该文不存在/伪造"**。这是本条款最容易被违背的地方。

**正确的中文核验路径（三步）**：

| 步骤 | 动作 | 取到什么 |
|------|------|---------|
| ① DOI 解析 | `GET https://www.chndoi.org/Resolution/Handler?doi={DOI}` （中文 DOI 官方解析器，同方知网） | **HTTP 200** → 落地页给出题名、作者、出版机构、注册时间；并给出 CNKI 境内/境外跳转链接 |
| ② 期刊官网比对 | 直连期刊自有站点，逐字比对 `年, 卷(期): 起止页` 与 DOI | 卷/期/页码/DOI 字段级确认 |
| ③ 聚合侧证 | 百度学术 / 维普题录作旁证（**仅用于侧证，不用于字段定案**） | 存在性佐证 |

实测可用的期刊官网（均为出版社自有站点）：

| 期刊 | 官网 | 实测案例 |
|------|------|---------|
| 软件学报 | `jos.org.cn` | `2026, 37(8): 3180-3204, DOI: 10.13328/j.cnki.jos.007594, CSTR: 32375.14.jos.007594` |
| 计算机工程 | `www.ecice06.com` | `2026, Vol.52, Issue(1): 22-32, doi: 10.19678/j.issn.1000-3428.0252754` |
| 系统仿真学报 | chndoi 解析 `10.16182/...` | 作者序列经 ISSN 前缀确认 |

**边界澄清（与 Zero-scraping 的关系）**：本条款**不违背**"不爬 CNKI/万方"原则。
区别在于——**禁止**的是 CNKI/万方的**检索接口**与**全文批量抓取**；
**允许**的是通过 WebSearch/WebFetch 读取**单篇公开题录页**取 Title/Author/卷期页，
这等价于人工在浏览器查证一条引文，属于核验而非抓取。

**注意数据源可用性**：万方详情页常有滑块人机校验会导致"查无"，
此时应改用 **CNKI 公开题录页（cfed.cnki.net / kns.cnki.net 单篇）或期刊官网**，不要据此判 miss。

**自洽性校验技巧**：题录页常同时给出 `页数` 与 `起止页码`，二者必须自洽。
实测《计算机应用》`2025(S2): 64-70` 标注 `页数:7` —— 64~70 恰为 7 页，交叉印证成立。

---

## 四、标题漂移（ID_MISMATCH）处理

实测案例（2026-08-18）：清单标题与 API 规范标题不符，但论文**真实存在**——
- E3 清单"Collaborative LLMs…" → 规范"*LLMs Working in Harmony: A Survey on the Technological Aspects of Building Effective LLM-Based Multi Agent Systems*"
- E13 清单"Surfer 2: Free Multilingual Reasoning LLM" → 规范"*Surfer 2: The Next Generation of Cross-Platform Computer Use Agents*"
- E14 清单"CoELA: Collaborative Embodied Language Agents" → 规范"*Building Cooperative Embodied Agents Modularly with Large Language Models*"

→ **以 API 规范标题为准修正清单**，并记一行勘误。这正是纯 WebSearch 检索易漏的盲区，
   API 级交叉校验的价值所在。

### 4.1 作者错配（标题校验抓不到的盲区）

**标题相似度校验有一个结构性盲点：标题对，不代表引用对。** 作者字段从不参与比对，
于是"标题正确 + 作者张冠李戴"这类错误可以完整穿过 `verify_references.py`。

实测案例（2026-09-26，多智能体系统综述稿件）：

| 项 | 稿内写法 | 一手核实（arXiv abs 页） |
|---|---|---|
| 编号 | `arXiv:2404.04834` | 同一篇，编号有效 |
| 标题 | LLM-Based Multi-Agent Systems for Software Engineering: Vision and the Road Ahead | 实为 *…: Literature Review, Vision and the Road Ahead*（仅差一词，相似度高于阈值） |
| **作者** | Z. Rasheed, M. Waseem, A. B. M. N. P., K. Systä, P. Abrahamsson | **J. He, C. Treude, D. Lo**（完全不同） |

编号与标题都"看起来对"，只有作者全错——疑似把另一篇同主题工作（Rasheed 等）的作者
误配到该编号上。**若只跑标题校验会判 MATCH 并放行。**

→ **硬性动作**：凡条目带 arXiv ID 或 DOI，核验时必须**同时**比对作者姓氏序列
（一作 + 通讯/末位作者即可命中）。`fetch_arxiv.py lookup` 返回的 Atom XML 含完整
`<author>` 列表，取回来做序比对成本极低，不要只看标题。

#### 4.1.1 作者位次错配（数量全对、顺序错——比集合错配更隐蔽）

作者错配有两个子形态，**后者更阴险**：

| 子形态 | 特征 | 能否被"作者集合比对"抓到 |
|---|---|---|
| **集合错配** | 作者完全不同（如 §4.1 的 Rasheed vs He） | ✅ 能 |
| **位次错配** | 一个不少、一个不多，**只有顺序颠倒** | ❌ **抓不到** |

**位次错配实测案例（2026-10-02，条目 [53] / Cognitive Computation）**：

| 位次 | Crossref | OpenAlex | 稿件原文（错） |
|---|---|---|---|
| 1 | Sparsh Bajoria | Sparsh Bajoria | S. Bajoria ✅ |
| 2 | Shreyanshu Ranjan | Sumit Ranjan | S. Ranjan ✅ |
| 3 | Adhitya M | Adhitya M | A. M. ✅ |
| 4 | **Vineet Suri** | **Vineet Suri** | **V. Hassija** ❌ |
| 5 | **Vikas Hassija** | **Vikas Hassija** | **V. Suri** ❌ |
| 6 | Vinay Chamola | Vinay Chamola | V. Chamola ✅ |
| 7 | Amir Hussain | Amir Hussain | A. Hussain ✅ |

7 位作者**一个不少**，只有第 4/5 位颠倒。人数检查、集合检查、标题检查**全部放行**。

→ **规则升级**：作者比对必须是**逐位次序列比对**（`list == list` 而非 `set == set`）。
  建议核验脚本输出 diff 时同时报告 `missing`（集合缺）与 `order_conflict`（位次冲突）两类。
  缩写名（`S. Ranjan`）与全名比对时，只比**姓氏**，名/缩写差异不计入冲突
  ——上例 Crossref 作 `Shreyanshu`、OpenAlex 作 `Sumit`，稿件用缩写 `S.`，不受影响。

#### 4.1.2 一处修改要横扫全部衍生文件

参考文献条目常**同时存在于多个文件**（主稿 v2/v3、IEEE 补充参考表、扩充清单表格、bib）。
实测教训：某条目在一次修订中只补进了 v3，`v2 / ieee / 扩充清单` 三处全部遗漏，
直到下一轮全仓 grep 才发现。

→ **规则**：凡改动参考文献条目，**必须以 DOI 或标题特征串全仓 grep 一次**
  （`grep -rn "<特征串>" --include=*.md --include=*.bib`），逐处同步后再回读验证。
  不要假设"改主稿就够了"。

#### 4.1.3 「拼写类指控」的终审源 = 出版方 camera-ready PDF 首页（2026-10-02 实测）

**场景**：外部核查给出的名单与稿件**只差一个字母**（`Fourrier` → `Fournier`），
其余 5 位作者全对，看起来极度可信。实测 [74] GAIA 第二作者，
**六源一致为 `Clémentine Fourrier`，质疑不成立，零改动。**

| # | 判源 | 证据强度 | 说明 |
|---|------|----------|------|
| 1 | **出版方 camera-ready PDF 首页** | ★★★★★ 终审 | 作者姓名最终权威。本例 ICLR 2024 首页原文 `Clémentine Fourrier²`，且**机构邮箱 `clementine@huggingface.com` 与姓氏自洽**（`Fournier` 与该邮箱无法对应） |
| 2 | **arXiv API**（`export.arxiv.org`，无反爬） | ★★★★★ | 取 `<author>` 列表；顺带 grep XML 中两种拼法的出现次数（本例 Fournier=0 / Fourrier=1）。注意看 `<updated>` 是否为当前版本 |
| 3 | **arXiv abs 页面 grep** | ★★★★★ | 直接数两种拼法的命中数 |
| 4 | **OpenAlex** | ★★★★☆ | **DOI 路径 + 标题检索路径各查一次**，避免单路径偏差 |
| 5 | **Semantic Scholar** | ★★★★☆ | 注意 429 ≠ NOT_FOUND（见 §4.6） |
| 6 | **Google Scholar 作者主页引用条目** | ★★★☆☆ | 顺带可拿到出版版页码（聚合侧证，投稿前须人工终核） |

**反爬取道顺序**（arXiv PDF / OpenReview / DBLP 常挂 Cloudflare / Anubis）：
`arXiv API`（无阻） → **搜索引擎结果中缓存的出版版 PDF 首页文本**（本例的决定性证据即来自此） → `Google Scholar 作者主页` → `OpenAlex / S2` 双路径。

**两条硬规则**：

1. **外部指控的名单本身也是待核验对象。**
   若指控的其余字段全对、只有 1 个字符不同，**恰恰要提高警惕**——
   这是幻觉最容易伪装成功的位置（"高精度 + 单字符漂移"）。
   必须**独立取一手源重建完整名单**，而不是拿指控名单去"找不同"。

2. **多源一致 → 不改稿**，并向用户明确说明"质疑不成立 + 给出证据表"。
   绝不因为"对方说得具体、还给全了名单"就改。
   改稿的门槛是**一手源推翻稿件**，不是"外部提出了异议"。

#### 4.1.4 预印本 vs 正式版：作者顺序可能不同，以**正式出版版**为终审源（2026-10-02 实测）

**场景**：[96] MAD 论文（arXiv:2311.17371）的 **arXiv 预印本 Atom 元数据**作者顺序为
`Smit, **Duckworth**, Grinsztajn, Barrett, Pretorius`（Duckworth 第 2），
但 **ICML 2024 正式出版版**（DBLP BibTeX `conf/icml/SmitGDBP24` + 论文 PDF/ar5iv 渲染）为
`Smit, **Grinsztajn**, Duckworth, Barrett, Pretorius`（Grinsztajn 第 2）。
稿件采用后者 —— **与正式版一致、与 arXiv 预印本不同**。

> ⚠️ **若只查 arXiv API 就去"修正"，会把对的改成错的。**
> 本例实测中，arXiv 预印本 v1/v2/v3 的 Atom 元数据顺序 ≠ 会议正式版顺序
> （论文标注 Equal contribution，作者位次在接收前后发生过调整）。

**规则**：
1. 作者位次的最终权威是 **正式出版版**（PMLR / DBLP / 会议官网 PDF 首页 / 论文 LaTeX 渲染的 ar5iv），
   **不是 arXiv 预印本的 `<author>` 元数据**。
2. 核验位次时，**必须同时拉取正式版源**（DBLP BibTeX 最干净）与预印本源，
   先看"稿件 vs 正式版"是否一致；只有"稿件 vs 正式版"冲突才改。
3. 预印本与正式版位次不一致、但**稿件与正式版一致** → **不改稿**，并在报告中记下两源差异。

### 4.2 题录错误的三种形态与对应处置

不要把题录错误一律当作"编造"处理——处置方式取决于**编号一手内容与清单描述的偏离类型**：

| 形态 | 特征 | 正确处置 |
|---|---|---|
| **标题漂移** | 编号一手内容与清单描述是同一篇，仅措辞不同 | 以一手规范标题为准改写清单（§四） |
| **字段错配** | 编号一手内容正确，但作者/期刊/卷期页写错 | 以一手元数据逐字段覆盖（4.1 案例） |
| **编号错配** | 编号一手内容与清单描述**主题完全不同** | 该条不可用：要么换回正确编号，要么按一手内容重写整条 |

**编号错配的实测案例（2026-09-26）**：多处二手引文把 `arXiv:2402.05718` 著录为
"L. Wang et al., *A comprehensive survey on multi-agent systems with large language models*"。
打开该 arXiv abs 页，真实内容是 **REMEDI: Corrective Transformations for Improved Neural
Entropy Estimation**（V. Nilsson 等，ICML 2024）——神经熵估计，与多智能体毫无关系。
**此类条目不采用**，且不得因为"多个来源都这么写"就采信。

### 4.3 二手引文的效力边界（重要）

**规则：二手引文只能"加"存在性证据，不能"定"字段内容；凡与一手来源冲突，一手胜。**

本次核查中两条线索恰好构成一组对照，说明为什么必须这样切分：

- **ACM CSUR《Multi-agent systems with large language models: A survey》** — Crossref 精确题名
  查询未命中、WebSearch 未命中，仅在一篇 IEEE Software 正式论文的参考文献表内有著录
  （vol. 57, no. 1, pp. 1–39, 2025）。判定：**存在性成立（可引），DOI 字段保持"待核"**。
  二手证据在此"加"了存在性，没有超出这个范围。
- **`arXiv:2402.05718`** — 二手指向一个不存在的题录，一手 arXiv 页直接推翻。
  判定：**不采用**。

推论：**正式发表的论文的参考文献表也会有错**（上例即在 CSUR 的著录链上出现），
所以二手来源不能作为字段级依据；但它是存在性证据的有效补充，尤其在
Crossref 索引不全（ACM 的部分条目即如此）时，是唯一可得的存在性线索。

### 4.4 `NOT_FOUND` ≠ 编造（英文侧的对齐）

§三 已为中文核验确立"一个 miss 永不被判为伪造（precision over recall）"。
英文侧须执行同一原则，否则会误删真实文献：

- 若清单标题是**对论文的改写式概括**（如把 ChemCrow 论文概括为
  "LLM Agents for Autonomous Chemical Discovery"），按该标题检索必然 `NOT_FOUND`，
  但论文**真实存在**——真实著录为 *Augmenting large language models with chemistry tools*,
  *Nature Machine Intelligence*, 6(5): 525–535, 2024（实测案例，2026-09-26）。
- 因此 **`NOT_FOUND` 只触发人工确认，绝不自动删除**。要判定"编造"，需一手来源
  明确证伪（例：编号有效但主题完全无关，见 4.2）。
- §五 IRON RULE 第 5 条的"默认删除"应**限缩为**：*一手来源证伪的条目*删除；
  *检索未命中*的条目进人工确认清单。

⚠️ 另须提醒作者：**预印本 → 正式版升级要单独核，不能靠印象**。
本次为 `arXiv:2404.04834` 找到 TOSEM 正式版（DOI 10.1145/3712003）是检索命中的结果；
而为 MAST（`arXiv:2503.13657`）找到的两条线索互相冲突（NeurIPS 2025 D&B vs ICLR 2025
Workshop），**正确处理是维持预印本引用并如实告知冲突**，而不是任选其一。

### 4.5 预印本→正式版的 DOI 归属：**先看 arXiv 的 `arxiv:doi`**（2026-10-01 实测）

上一段说"预印本→正式版升级要单独核"。**怎么核最稳？答案是 arXiv 自己的 `<arxiv:doi>` 字段。**

```
GET https://export.arxiv.org/api/query?id_list=2308.11432
→ 取其 <arxiv:doi> 与 <arxiv:journal_ref>
```
该字段**由论文作者在 arXiv 自行登记**，直接声明了"本预印本的正式版 DOI 是哪个"。
它比任何出版商网页都可靠，因为**不依赖站点是否可访问**。

**判定优先级**：`arXiv arxiv:doi` → `api.crossref.org/works/{DOI}` → `api.openalex.org/works/doi:{DOI}` → 期刊官网 / 全期目录。

实测案例（2026-10-01 晚）：稿件 [50]（Wang et al., *A Survey on Large Language Model based Autonomous Agents*）
被指"DOI 严重错误"，提议换成另外两个 DOI。核验结果：

| 证据源 | `10.1007/s11704-024-40231-1` | 被提议的两个替代 DOI |
|---|---|---|
| **arXiv `arxiv:doi`** | ✅ **命中**（作者自登记） | — |
| Crossref `/works/` | ✅ 标题逐字 + 13 位作者全中 + FCS vol.18 iss.6 art.186345 | ❌ 404 |
| OpenAlex | ✅ 被引 1672 | ❌ 404 |
| Crossref 全期目录 | ✅ FCS 2024 全 147 条中，vol.18/iss.6 共 12 篇，本 DOI 对应本标题 | ❌ 全年无此记录 |

→ **原 DOI 正确，指控不成立。** 附带写错的可能诱因：`link.springer.com` 返回 Cloudflare
人机校验（`is verifying your browser...`），此类 CDN 拦截态下的站内搜索极易返回错配结果。

> **推论（重要）**：不可因某个出版商网页打不开 / 显示不符，就推断"DOI 指向别处"。
> **网页不可达 ≠ DOI 错配。** 换常态 API 通道再判。

### 4.6 限流 / 超时 ≠ `NOT_FOUND`（假阴性防线）

`S2 HTTP 429`、`arXiv timed out` 曾被直接落账为 `NOT_FOUND`，是本环境**反复出现**的错误
（累计已导致 [21][31][33] 三条真实文献险些被降级/删除，其中两条是证据分级的承重源）。

**硬规则**：任何 429 / 5xx / timeout，**一律不得直接记作 NOT_FOUND**。
必须**换源或退避重试后再定**；连续失败时应记为 `UNVERIFIED`（待核），而非失败。

区分表：

| 返回 | 含义 | 正确处置 |
|---|---|---|
| `404 / Resource not found` | **仅对该数据源**无此 DOI/ID | 换源复证；中文刊见 §3.1（Crossref 404 无效） |
| `429 Too Many Requests` | 限流，**无任何证明力** | 退避重试或换 API（配 `S2_API_KEY` 可提到 10 req/s） |
| `-1 / timed out` | 网络问题，**无任何证明力** | 重试；换 HTTP/HTTPS 端点 |

---

## 五、IRON RULE（反幻觉硬律）

1. 每条论断必须有引文。
2. 每个引用必须**独立核验**（L1/L2 任一）。
3. **"难以验证"= 不合格**：灰区即 FAIL，不能标"不确定"了事。
4. 占位编号（`arXiv:xxxx.x` / `24xx.x`）一律拒绝；推断标题 / 编造作者一律拒绝。
5. 无法确认真实存在的文献 → 默认删除，不保留在可提交稿中。

---

## 六、配套脚本

- `scripts/verify_references.py`（仅 stdlib，自包含）：读参考文献 JSON，
  对 arXiv ID / DOI 调 API 核验，0.70 标题相似度交叉校验，429 退避，
  支持 `S2_API_KEY` 环境变量；输出核验报告。详见该脚本头部说明。
- `scripts/fetch_arxiv.py`（仅 stdlib，自包含）：**arXiv 单库**——按检索式检索（P2）、
  按 ID 取规范元数据、ID+标题 0.70 交叉校验；免费无需 key，默认 sleep 3 秒/请求，
  429/5xx 指数退避；输出 UTF-8 JSON。
- `scripts/fetch_lit.py`（仅 stdlib，自包含）：**正式刊出三库**——
  `search`（OpenAlex 正式刊出检索，P2）、`verify`（Crossref DOI 核验，P6）、
  `citing`（OpenCitations 引文关系，T4）、`enrich`（按 DOI 取规范元数据 + 被引数）；
  四者均**免费、无需 API key**，自带限速（0.5–1.5 秒/请求），只需一个邮箱即可进 polite pool
  （不提供也能跑）。详见 §二.5 与脚本头部说明。

**三个脚本的分工（避免重复造轮子）**：

- `fetch_arxiv.py` → **arXiv 单库**：按检索式检索、按 ID 取规范元数据、ID+标题交叉校验。
- `fetch_lit.py` → **正式刊出**：OpenAlex 检索、Crossref DOI 核验、OpenCitations 引文、按 DOI 补元数据。
- `verify_references.py` → **混合批量出报告**：arXiv ID + DOI 一起跑，输出 Markdown 报告（DOI 走 S2）。

P2 用 `fetch_arxiv.py search` + `fetch_lit.py search` 取真实题录；
P6 用 `fetch_arxiv.py verify`（arXiv 条目）+ `fetch_lit.py verify`（DOI 条目），
需要合并报告时再用 `verify_references.py`。
