# 投稿约束清单 · <刊名>

> 复制本模板，改名 `submission_checklist_<刊名>.md`，逐条从期刊官网 Author Instructions 填妥。
> 每次结构调整后重新核对"待修"项。访问日期：____-__-__；官网链接：<url>

## 一、基本信息
- 目标期刊：
- 出版社 / 格式族（Elsevier / Springer / IEEE / Wiley / APA 等）：
- 首选刊 / 稳投刊 / 保底刊：
- 交付格式（LaTeX / Word / PDF / Markdown 学术稿）：
- 署名场合（校内投稿 = 郑洪英；英文姓在后；机构英文全称照指定表）：

## 二、参考文献样式族（先定族，再写题录）
- [ ] 引用体系：编号制（Numbered/Vancouver/IEEE）□ / 著者-年份制（APA/Harvard）□
- [ ] 正文标记：方括号 `[1]` □ / 上标 ¹ □ / 括号 `(Author, Year)` □
- [ ] 编号顺序：首次出现顺序 □ / 作者字母序 □

## 三、参考文献九项检查（逐条对齐官网）
| 项 | 官网规定 | 本稿落实 | 状态 |
|---|---|---|---|
| 作者名写法 |  |  | ⬜ |
| et al. 规则（阈值） |  |  | ⬜ |
| 期刊名缩写标准 | 全称 / ISO 4 / MEDLINE |  | ⬜ |
| DOI 格式 | 是否强制 `https://doi.org/xxx` |  | ⬜ |
| 页码 / 文章号 | 区间 en dash / 文章号 `nwae403` |  | ⬜ |
| 类型分流 | [J]/[C]/[EB/OL] 各自写法 |  | ⬜ |
| 中文文献处理 | 补英文译名 + 拼音 |  | ⬜ |
| 预印本/arXiv 著录 | 是否接受、怎么写 |  | ⬜ |
| 条目完整性 | 七要素齐全 |  | ⬜ |

## 四、篇幅与结构硬约束
- [ ] 摘要上限：____ 词/字（实测计数：____）
- [ ] 关键词上限：____ 个（实测：____）
- [ ] Highlights：____ 条，每条 ≤____ 字符（若刊强制）
- [ ] 章节编号方式：
- [ ] 必备声明小节：competing interest □ / generative AI use □ / data availability □ / CRediT □
- [ ] Graphical Abstract：需要 □ / 可选 □

## 五、图表要求
- [ ] 题注位置：上方 □ / 下方 □
- [ ] 编号顺序：按正文首次出现单调 □
- [ ] 位图 dpi：halftone 300 □ / combination **500** □ / line art 1000 □
- [ ] 矢量格式偏好：EPS □ / PDF □
- [ ] 表为可编辑文本（非图片）□

## 六、模板与配套文件
- [ ] 官方 LaTeX 模板（cls/bst）：<路径/链接>
- [ ] 官方 Word 模板：<路径/链接>
- [ ] 需传配套文件清单：Manuscript / Highlights / Cover Letter / Tables / Figures / Graphical Abstract

## 七、预印本策略（先查平台、再查出版社）
- [ ] 投稿前能否挂 arXiv：____（CS 综述通常受限）
- [ ] 替代通道：SSRN □ / ChinaXiv □ / 其他 ____
- [ ] 可编辑源文件：是否需从 Markdown 转 `elsarticle` LaTeX 版 □

## 八、引用正确性门禁（跑 verify_submission.py）
- [ ] 零孤儿 / 零缺项 / 零越界 / 编号连续
- [ ] 图号、表号按正文顺序单调
- [ ] 图件内部文字编号无残留（如"表 8"应为"表 12"）

## 九、人工复核（脚本查不了）
- [ ] 正文绝对计数叙述已从权威产物重推
- [ ] Cover Letter 写了"与同题综述差异"，数字与正文一致
- [ ] 作者栏署名场合正确
- [ ] 图件真实渲染无溢出（getBBox 复核）
- [ ] 可编辑源文件已备
