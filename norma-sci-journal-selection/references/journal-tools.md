# 选刊工具分工与用法

## 工具总表

| 用途 | 工具 | 入口 | 口径与注意 |
|---|---|---|---|
| 官方收录状态（唯一权威） | Clarivate Master Journal List | `mjl.clarivate.com` | 确认 SCIE / ESCI 在录，查 **On Hold**，否决项先查这里 |
| 分区权威核验（2026 起） | 新锐分区 | `xr-scholar.com` | 免费；2026 年起的新标准；同时看 `under review` 标记 |
| 综合查询（分区 / IF / 周期 / 经验） | LetPub、科研通 | `letpub.com.cn` 等 | 国内最顺手，含期刊点评与投稿经验；**数值仅作参考，不直接转述** |
| 内容匹配（标题 + 摘要 → 刊） | JANE | `jane.biosemantics.org` | 生物医学最强，跨学科亦可用 |
| 内容匹配 | Elsevier Journal Finder | `journalfinder.elsevier.com` | Elsevier 系刊最全 |
| 内容匹配 | Springer Journal Suggester | `journalsuggester.springer.com` | Springer 系刊 |
| 内容匹配 | Wiley Journal Finder | `journalfinder.wiley.com` | Wiley 系刊 |
| 内容匹配 | Clarivate Manuscript Matcher | EndNote 在线版内 | 需 Web of Science 账号 |
| 学科横向对比 | Scimago (SJR) | `scimagojr.com` | 看学科相对位置，**防跨领域比 IF** |

> 入口若失效，用搜索引擎搜工具全名直达官方站点；不要照着旧链接硬点，也不要凭记忆复述域名。

## 使用顺序

1. **Master Journal List** → 定"是不是在录"（否决项）。
2. **新锐分区** → 定"分区口径"（按 H1 确认的版本执行）。
3. **Journal Finder / JANE** → 建候选池（输入标题 + 摘要，不是关键词）。
4. **Scimago** → 做同学科横向对比。
5. **LetPub / 科研通** → 看投稿经验与审稿周期（**仅作参考，须注明来源非官方**）。

## 输入写法（决定候选池质量）

- ❌ 关键词拼串：`embedded defect detection edge` → 返回一堆泛化刊。
- ✅ **标题 + 摘要全文**粘贴进 Journal Finder → 按语义匹配，命中精度高得多。
- 摘要过长时保留：研究对象 + 方法 + 主要结果三句，删掉引言与展望。

## 速度证据的可靠性分级（v1.4.0 新增）

「6 个月内在线」这类硬约束常与候选刊冲突，但**审稿周期是二手数据最容易失真的字段**——同一本刊在不同第三方站点可差 2—3 倍。按下列优先级取证：

| 等级 | 证据形态 | 示例（2026-10-02 实测） |
|---|---|---|
| **A 级（首选）** | 官网公布的**流程分段数据**（投稿→初审 / →接受 / →在线） | Neurocomputing：投稿→初审 8 天、→审稿后决定 62 天、→接受 139 天、接受→在线 8 天 —— **Elsevier 期刊首页 `Journal Insights` 直接给出（一手）**，与百度百科转引数值一致 |
| **B 级** | **可追溯的单篇时间线**——在出版方页面直接读到 Received / Accepted / Published 三个日期 | The Visual Computer 2026 年一篇综述：Received 2026-01-05 → Accepted 2026-03-03 → Published 2026-04-01（≈86 天在线） |
| **C 级** | 出版社官网的聚合指标 | ① Elsevier 各刊首页 `Journal Insights`（含 A 级细分字段）；② **Springer 期刊首页 `Submission to first decision (median)`**——例：The Visual Computer ＝ **2 天**（注意这是**编辑首决**中位，不等于审稿周期） |
| **D 级（仅参考）** | 第三方站的「平均审稿速度」、网友投稿经验 | LetPub / 科研通 / enterscholar |

> **纪律**：D 级数据**只能标「待核」、不进加权计分**；若 A/B 级与 D 级冲突，以 A/B 级为准。**只凭 D 级数据就判定某刊「超出速度约束」并剔除，是过度裁决**——应降为「待核」并保留在候选池，或明确写出证据等级。

> ⚠️ **C 级里两个易被误读的字段**：
> - Springer 的 `Submission to first decision (median)` 往往极低（2 天级）——它是**编辑初筛**耗时，**不能拿来证明「审稿快」**；B 级单篇时间线才是审稿速度的可信证据。
> - Elsevier 的 `Submission to first decision` 与 `Submission to decision after review` **必须成对读**：前者 8 天 + 后者 62 天说明「审稿后决定」发生在约 62 天，而非 8 天。

## Elsevier / Springer 期刊首页的一手字段清单（v1.5.0 新增）

这两处**不经过 `/how-to-publish-with-us` 拦截路径**，可直接取到关键字段，优先于第三方站：

| 通道 | 可直接读到的一手字段 |
|---|---|
| `sciencedirect.com/journal/<刊名>` | APC 金额与币种 + 「Subscription: No publication fee charged to authors」+ **Journal Insights 四段速度** + IF / CiteScore + Aims & Scope 全文 + 最新文章的文章类型标签（`Research article` / `Survey paper`） |
| `sciencedirect.com/journal/<刊名>/publish/guide-for-authors` | **Article types 全文**（例：Neurocomputing 官列 7 类，含 `Type 2: Survey/review study`）+ policy 章节名（如 `Declaration of generative AI use`）+ 结构 / 参考文献格式要求 |
| `link.springer.com/journal/<id>` | Publishing model（Hybrid / OA）+ `Submission to first decision (median)` + 收录库清单（含 **CNKI / Wanfang** 等国内库）+ 文章类型标签（`Review` / `Research`） |

> 用法要点：**排雷时的「综述稿能不能投」这一关，最硬的两条证据就在这两个页面**——① Guide for Authors 的 Article types 是否列出 survey/review；② 期刊首页最新文章的类型标签是否真出现 `Survey paper` / `Review`。都命中即可判定「非邀稿可投，无需邮件确认（保险起见仍可确认一次）」。

## 一手通道被拦截时的取数办法（v1.4.0 新增）

Springer（`link.springer.com`，含 `/how-to-publish-with-us`）与 Wiley（`onlinelibrary.wiley.com`）在自动化访问下常返回 **`Client Challenge`**（Cloudflare 人机校验），WebFetch 取不到正文。

**已实测同样被拦的镜像域（2026-10-02）**：`rd.springer.com`、`link-proxy.springer.com` —— 换 Springer 子域**不解决问题**，不要在这上面反复试。

替代通道：

1. **次优一手**：`springer.com/journal/<id>`（主站，与 link.springer 不同域，有时可通）、`journals.elsevier.com` / `sciencedirect.com/journal/<刊>`、`mjl.clarivate.com`。
2. **第三方转载页**：搜索引擎命中的期刊信息站（LetPub / enterscholar / fabiao / sciqk / xueshu / ea-iset 等）常**逐字转引**官网 Aims & Scope 与 APC 段落——可用于**读原文措辞**，但**APC 金额仍须标「待核」**，除非能确认转载自官网定价页。
3. **百科类**（百度百科等）偶有**转引官网流程数据**，但仍须标注转引来源；**若能找到原站字段，优先用原站**（本轮即把 Neurocomputing 的速度证据从百科转引升级为 Elsevier 期刊页一手）。
4. **越不过去就标「待核」**，不要用记忆值填空。
5. **要的是「某篇文章的摘要」时，绕开官网走公开题录页**——这些页面被搜索引擎完整索引，摘要往往全文可见：
   - **DOI 基金会**（`doi.org/<DOI>` 的落地摘要）、**ACM Literatum**（`acm-*.literatumonline.com/doi/<DOI>`，含 Abstract + Publication History + 参考文献数）
   - **Mendeley Catalogue**、**OUCI**（`ouci.dntb.gov.ua/works/…`，含卷期页码与**文献数**）、**Scilit**、**Dimensions**
   - 搜索引擎对**精确题名加引号**检索时，返回快照里常直接带完整 Abstract（Springer 刊亦有效）
   - **ScienceDirect 文章页反而可通**：`sciencedirect.com/science/article/abs/pii/<PII>` 可取到 `Survey paper` 类型标签 + 完整摘要 + References 计数；**PII 从 Crossref 记录的 `alternative-id` 字段取得**

## E2 精读的可复现取证法（v1.5.0 新增）

**目标**：E2 ＝ 精读目标刊近两年 **10—20 篇同类文章**（题名 + 摘要级理解）。这不是「随便点几篇看看」，而是**有采集口径、可复现、可交证据台账**的动作。

### 一、采集（题名级，一手且可穷举）

```text
入口：Crossref REST API  /journals/{ISSN}/works
参数：query.title = survey|review|systematic|overview|taxonomy|state-of-the-art|
                    advances in|progress in|recent developments|literature
      filter      = from-pub-date:<两年前>-01-01,until-pub-date:<今年>-12-31,type:journal-article
      select      = DOI,title,author,issued,volume,issue,page,type
      rows=100，按 published 倒序
```

- **必须本地正则复核**：`query.title` 是模糊匹配，会漏也会多。用 `\b(survey|review|systematic|overview|taxonomy|state-of-the-art|…)\b` 在标题上二次过滤，再按 `issued` 年份卡窗口。
- ISSN 要查准（**电子 ISSN 与印刷 ISSN 是两个名，Crossref 通常两者都可**）。
- 产出一份 `e2_harvest.json` 作为**可回溯的样本台账**——它同时给出「该刊年发多少篇综述」这一硬指标。

### 二、精读优先级

按**与本文的相关度**（技术底座 / 各应用域 / 部署约束 / 跨域整合）排序，取 **15—20 篇**，逐篇取摘要。**摘要取得顺序**：ScienceDirect 文章页（PII 来自 Crossref `alternative-id`）→ DOI 基金会 / ACM Literatum / Mendeley / OUCI / Scilit → 精确题名引号检索快照。

> **常见误判**：Crossref 与 OpenAlex 对 Elsevier / Springer 多数记录**不存摘要**（`abstract` 字段为空）。**abs=0 只说明该聚合器没有，不代表该文无摘要**，不要据此放弃精读。

### 三、★ E2 必看的四个「综述友好度」指标（本轮实战提炼）

只读摘要还不够——**这四项才是决定「能不能投」的关键**，也只有在 E2 阶段才拿得到：

| 指标 | 怎么量 | 判读规则 |
|---|---|---|
| **① 综述是否常规体裁** | 该刊两年内的综述**篇数**与年均量 | 年 ≥10 篇 → 综述是常规体裁，非邀稿亦可投；年 ≤2 篇 → 需邮件确认 |
| **② 图件常规量** | 抽样各篇的 Fig. 编号最大值 | 该刊综述常规 N 张；**本文图件数远低于 N → 「篇幅与体量」维度扣分，且投稿前必须补图** |
| **③ 附原创基准 / 元分析的比例** | 抽样统计「纯梳理」vs「含实证/元分析/复现」 | 比例高（如 ≥40%）→ 该刊默认期望「综述 + 你自己的对照证据」→ **「实验深度」维度按此扣分**；比例低 → 纯梳理可接受 |
| **④ 参考文献区间与中位** | 抽样各篇 References 计数 | 本文 refs 若低于该刊中位 → 「篇幅与体量」扣分（补元分析可自然增补） |

**规则**：以上四项的偏差**必须写进评分卡的对应维度依据**，而不是停留在印象里。它们是「E2 之后分数为什么下降」的可解释来源。

### 四、精读产出物

`07_e2_deepread.md` 一份，至少含：采集口径（可复现）、逐篇清单（题名/卷期页/年份/为何选读）、四项指标表、一手/二手证据台账、以及对 v1 评分的**修正记录**（哪一维度、由几分改到几分、依据哪一篇）。

---

## 记录要求

每次核查写清 **来源 + 查询日期**，例：

```text
收录状态：SCIE 在录（Master Journal List，2026-09-26 查询）
分区口径：待核（新锐分区站内检索，用户自行确认版本后回填）
```

未写来源与日期的字段，一律视为"待核"，不得进入评分卡计算。
