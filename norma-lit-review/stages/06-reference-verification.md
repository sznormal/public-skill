# P6 · 参考文献真实性核验

> Norma理工科文献综述 · Stage 06
> 目标：在质量审核（P7）之前，逐条核验参考文献是否真实存在——真实编号、真实作者、
>       真实标题、真实发表场所（venue）。杜绝占位符、推断标题、编造作者、未证实 venue。

---

## ⚠️ 为什么必须有这一步

综述初稿（P5）的参考文献由模型基于训练记忆生成，**极易出现以下事实性错误**：

- 占位符 arXiv 号：`arXiv:2409.x` / `arXiv:24xx.x`（`.x` 后缀一律视为未填）
- 推断/编造标题：根据正文内容"猜"论文标题，未在数据库核实
- 编造作者：`Anonymous`、仅凭首字母缩写推断（如 `Z. Zhang et al.` 无依据）
- 未证实 venue：标了 `ICRA 2025` / `NeurIPS 2024` 但无法在 OpenReview/官网核对
- 编号错但论文真：论文确实存在，但给的 arXiv/DOI 号是错的

**这些错误投稿前不修，会被审稿人一眼识破。** 本阶段是 P7 质量审核的强制前置门槛：
**真实性核验未通过，不得判定综述"达到提交标准"。**

---

## 一、禁止模式（Hard Forbidden）

生成或核验参考文献时，以下任意一条出现即 **STOP 并修正**，不得放行：

| 禁止项 | 示例 | 正确做法 |
|--------|------|---------|
| ❌ 占位符编号 | `arXiv:2409.x`、`arXiv:24xx.x` | 填真实完整编号 `arXiv:2409.05556` |
| ❌ 编造作者 | `Anonymous`、`Z. Zhang et al.`（无依据） | 从数据库核出真实第一作者+年份 |
| ❌ 推断标题 | 正文提到某工作，标题是模型"拼"的 | 用标题/作者回检 arXiv/DOI/Crossref 确认 |
| ❌ 未证实 venue | `in Proc. ICRA, 2025`（未核对） | 在 OpenReview/会议官网/Crossref 核对，或改标预印本 |
| ❌ 技术报告冒充论文 | 把公司系统（如某 AI co-scientist）写成署名论文 | 标为技术报告（Tech. Rep.）或公司博客，注明无正式出版编号 |

---

## 二、核验流程（逐条执行）

对 `literature_review_draft.md` 参考文献列表（及 `references.bib`）中 **每一条** 执行：

### 2.1 判定标识类型并选择核验源

| 标识 | 核验方式 | 核验源 |
|------|---------|--------|
| **arXiv ID**（如 `2409.05556`） | WebFetch `https://arxiv.org/abs/{id}` | arXiv 官方页：比对标题/作者/年份 |
| **DOI**（如 `10.1007/s10514-026-10257-4`） | WebFetch `https://doi.org/{doi}` 或查 Crossref API | 期刊/出版社页：比对标题/作者/卷期 |
| **中文文献（知网）** | WebSearch 标题 + 第一作者 | 知网/万方：确认存在与发表信息 |
| **会议论文（OpenReview venue）** | WebSearch 标题 + 会议名（如 `ICLR 2024`） | OpenReview / 会议官网 / Semantic Scholar |
| **技术报告/系统** | WebSearch 系统名 + 机构 | 机构官网/博客，确认性质（非署名论文） |

### 2-A、脚本级核验（L1，优先于 2.1 的 WebFetch 兜底）

> 当环境有脚本运行能力时，**优先用脚本做机器级核验**（真实、可复现、自动抓漂移）。
> 完整协议见 `modules/verified-retrieval-protocol.md` §二–§四。两个脚本分工如下：

| 场景 | 用哪个脚本 | 说明 |
|------|-----------|------|
| **arXiv 单库**（按 ID 取规范标题 / 抓标题漂移） | `scripts/fetch_arxiv.py verify` | 免费、**无需 API key**，默认 **3 秒/请求**限速，输出 JSON |
| **DOI（正式刊出）** | `scripts/fetch_lit.py verify` | 走 **Crossref**（DOI 的权威注册源）；免费、无需 key，**0.5 秒/请求**；仅需一个邮箱即可进 polite pool |
| **混合批量**（arXiv ID + DOI，出 Markdown 报告） | `scripts/verify_references.py` | 仅 stdlib；DOI 走 Semantic Scholar，可选 `S2_API_KEY` 提速 |

- **DOI（Crossref，正式刊出的权威注册源）**：
  `python scripts/fetch_lit.py verify --input refs.json --output doi_verify.json`
  - 五态输出：**✅ MATCH / ⚠️ DOI_MISMATCH / ❌ NOT_FOUND / ⚪ NO_DOI / 🔧 ERROR**，
    标题相似度阈值同为 **0.70**（与 arXiv 口径一致，便于合并统计）。
  - **邮箱（polite pool）**：首次运行时脚本会**交互式询问邮箱**——不是注册、不是 API key，
    官方仅作限流联系方式。也可 `--mailto you@example.com` 传参，或设环境变量 `LIT_MAILTO`；
    脚本化/无人值守调用请加 `--no-prompt`（或设 `LIT_NO_PROMPT=1`）直接使用公共池。
    **不提供邮箱也能正常运行，仅限速更严。**
  - 比 doi.org 更适合批量核验：Crossref 是 DOI 的注册源，判定更权威；404 即确定性不存在，不重试。
- **arXiv**：`python scripts/fetch_arxiv.py verify --input refs.json --output arxiv_verify.json`
  - ✅ **MATCH**：ID 解析成功且标题相似度 ≥ 0.70 → VERIFIED。
  - ⚠️ **ID_MISMATCH**：ID 真实存在但**清单标题与规范标题不符**（标题漂移）→
    以 API 规范标题为准**修正清单**，记一行勘误（案例见协议 §四：E3/E13/E14）。
  - ❌ **NOT_FOUND**：arXiv 查无此 ID → 疑似占位符 / 编造编号，须删除或重写。
  - ⚪ **NO_ID**：无 arXiv ID → 改走 DOI 或人工核对，**不得直接判伪造**。
- **Semantic Scholar / DOI**：`python scripts/verify_references.py --input refs.json --output report.md`
  **先 DOI 后标题**，标题相似度 ≥ 0.70 才认 matched；内置 **429 退避**。
  - 配置 `S2_API_KEY`（环境变量或 `--api-key`）可将限速从 1 req/s 升至 10 req/s，
    解除本环境未认证层持续 429（密钥安全见协议 §二.3）。
- 两者均**只依赖标准库**，managed Python 可直接跑，无需 pip（协议 §二.4）。

> 若 L1 不可用（无脚本能力 / 网络受限），回退 2.1 的 WebFetch / WebSearch 逐条核对，
> 但必须**透明披露"经联网核对"**，不得假装已 API 核验。

### 2.2 字段比对

将核验源返回的真实字段，与草稿条目逐一比对：

- [ ] **标题**：是否一致（允许翻译/缩写差异，但核心词须吻合）
- [ ] **第一作者**：是否一致
- [ ] **年份**：是否一致
- [ ] **编号/DOI**：是否准确（非占位符、非错号）
- [ ] **venue**：是否真实存在且论文确在该 venue

### 2.3 逐条结论

- ✅ **VERIFIED**：所有字段与核验源一致
- ⚠️ **PARTIAL**：论文真实，但草稿某字段有误（如编号错、venue 未证实）→ 必须修正
- ❌ **UNVERIFIED**：在核验源中**检索不到**该论文 → 视为疑似编造，须删除或重写

---

## 三、核验报告（落盘）

写入 `{project_path}/outputs/lit-review/reference_verification_report.md`：

```markdown
# 参考文献真实性核验报告

审核时间：{timestamp}
参考文献总数：{N}

| 编号 | 草稿标题 | 标识 | 核验源 | 结论 | 修正建议 |
|------|---------|------|--------|------|---------|
| [17] | SciAgents... | arXiv:2409.05556 | arxiv.org/abs/2409.05556 | ✅ VERIFIED | - |
| [23] | CoELA... | arXiv:2307.02485 | arxiv.org/abs/2307.02485 | ⚠️ PARTIAL | 标题应为 "Building Cooperative..."，一作 H. Zhang |
| [99] | ... | 无 | 全网检索无果 | ❌ UNVERIFIED | 删除或重写 |

统计：VERIFIED {v} / PARTIAL {p} / UNVERIFIED {u}
```

同时更新 HUD 的 `verification` 块：
```json
"verification": {
  "report_path": "{project_path}/outputs/lit-review/reference_verification_report.md",
  "verified": 0,
  "partial": 0,
  "unverified": 0,
  "gate_passed": false
}
```

---

## 四、修正闭环

- 对 ⚠️ / ❌ 条目：用 WebSearch 查真实编号/标题/作者，然后 **Edit** 修正
  `literature_review_draft.md` 与 `references.bib` 中对应条目。
- 修正后**重新核验**该条目，直到 ✅ VERIFIED 或用户明确以"人工核对为准"覆盖。
- ❌ UNVERIFIED 且无可靠来源支撑的条目：**默认删除**，不得保留在可提交稿中。

---

## 四-B、按 review_type 分支的额外核验

- **T2 / T3**：额外核验 **PRISMA 流程图与纳排标准的一致性**——流程图各阶段数量须与 P3 记录吻合，排除理由须真实存在；不一致 → 标 ⚠️ PARTIAL，必须修正后才可通过门禁。
- **T1 / T4 / T5**：不强制 PRISMA，按通用真实性核验（第二节）执行即可。

---

## 五、Hard Stop（强约束）

展示核验报告并明确结论。规则：

- 存在 ❌ **UNVERIFIED** 且用户未明确确认"以人工核对为准" → **不得**判定综述"达到提交标准"。
- 存在 ⚠️ **PARTIAL**（如编号错但论文真）→ 必须修正（或用户知情接受）后才可通过。
- 结论三选一输出：
  - ✅ **全部可核验**：N 条均 VERIFIED，可进入 P7。
  - ⚠️ **N 处已修正**：原 N 处 PARTIAL/UNVERIFIED，已修正为 VERIFIED。
  - ❌ **仍有 N 处未通过**：列出条目，需用户人工核对或删除。

用户确认后进入 **P7 质量审核**。

---

## 六、产出物

- `{project_path}/outputs/lit-review/reference_verification_report.md`：核验报告
- 修正后的 `literature_review_draft.md` + `references.bib`（如有修正）
- 更新 HUD：`verification.*` 全部字段，`verification.gate_passed = true/false`
