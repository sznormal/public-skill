# norma-skills

Norma 的自建 WorkBuddy Skill 集合（单体仓库 / monorepo）。

本仓库以「一个 skill 一个顶层目录」的方式集中管理全部自建 skill，便于统一版本记录、批量分发与跨设备同步。

- 仓库可见性：**私有**
- 远程：GitHub + Gitee 双远端
- 本地运行目录：`~/.workbuddy/skills/`（仓库根即 skill 加载目录，改动即入库）

---

## Skill 清单

### 一、元技能与工程化

| Skill | 版本 | 说明 |
|---|---|---|
| `afp-skill-creator` | 0.4.0 | AFP 方法论元 skill：引导在任意领域产出符合 AFP-SPEC 的 skill 包（薄路由 + 触发词隔离 + 渐进披露） |
| `skill-packager` | 1.0.0 | 把 skill 目录打包为可分发 zip，打包前执行安全审计（拦截硬编码密钥、个人环境路径） |
| `skill-to-expert-team` | 1.4.0 | 把单 skill 改造为多角色协作专家团（expertType=team）：团长编排 + 按域拆成员 + 原 skill 内嵌为共享工具箱 |
| `norma-skills-publish` | 1.0.0 | 把单个本地自建 skill 并入 norma-skills monorepo 并推送 GitHub+Gitee 双远端（含 README 登记） |
| `skill-install-audit` | 1.0.0 | 从本地 zip / GitHub 仓库安全安装 skill，先执行 P0/P1/P2 安全审计再落盘 |
| `wikiskill` | 1.0.0 | 基于 WikiSkill(arXiv:2608.27454) 把执行经验编译成持久化知识库，使 skill 在验证集门控下逐轮进化 |

### 二、教学与科研

| Skill | 版本 | 说明 |
|---|---|---|
| `suit-sz-teaching-suite-norma` | 1.2.0 | 高校教学文件写作套件：闭环完成《课程标准》（含课程思政融入表）→ 教案 → 学期授课计划三类文档撰写，并对三份文件做版本 / 格式 / 内容 / 学时勾稽的督导一致性核查；内置空白模板、确定性渲染与回读校验脚本，产出版式可机器校验的 docx |
| `norma-lit-review` | 0.23.0 | 理工科文献综述全流程：检索策略 → 多库检索 → 筛选分类 → 研究缺口 → 结构化综述 → 按目标期刊格式出第二语言版 |
| `norma-paper-format-check` | 1.2.0 | 论文排版与投稿前检查：按目标刊官网 Author Instructions 提取硬约束（重点参考文献格式），覆盖 LaTeX/Word/PDF 三栈排版；含著者-年份制（biblatex/JAIR）四式引用修正经验；沉淀轻量引用标记方法论（从 Markdown 重跑不丢排版修正，去括号铁律）；脚本门禁 `verify_submission.py` 支持编号制（零孤儿/缺项/越界/连续）+ `--author-year` 反模式扫描，加人工复核双保险核对引用正确性与投稿就绪度 |
| `norma-topic-selection` | 1.0.0 | 理工科选题助手（AFP 构建）：证据矩阵 → 双轴定位（8 类性质 × 四区地形）→ 六重门验伪 → Gap Statement 与可证伪假设 → 带一票否决的 8 维评分卡 → MVP 止损 → 研究计划与投稿策略；内容综合四版方案评估，附 7 份交付模板 + 2 个纯标准库体检脚本 |
| `bibagent` | 1.0.0 | 科学文献错误引用(miscitation)检测智能体：五类引用错误分类 + Evidence Committee 机制 + 付费墙双分支验证，产出可追踪引用完整性报告 |
| `norma-sci-journal-selection` | 1.5.0 | SCI 选刊决策七阶段交互流：论文画像 → 期刊偏好 → 竞争格局 → 候选池 → 硬排雷 → 匹配打分（证据等级 E0–E3 门槛 + 双维加权 + Desk Reject Risk）→ 冲/稳/保；IF/分区可列参考值但须四件套（数值+来源+查询日期+限制说明）且不计分；内置成品 Prompt 模板库 |
| `norma-ssci-journal-selector` | 1.4.0 | SSCI 选刊 6 步证据流（论文指纹→候选池→3D 匹配打分 Topic/Method/Audience→投稿序列），支持 PDF/DOCX/TXT，产出 Excel 评分表+Markdown 报告+投稿信草稿（英文体系，与 norma-sci-journal-selection 并存）；G1/G2 用户确认前置；v1.3.0 修复 PDF/DOCX 绕过章节识别（参考文献 0→118）、PDF 逐条切分、刊眉噪声去重、英文作者-年制刊名解析（候选池 0→9） |
| `norma-cn-core-journal-selection` | 1.0.0 | 中文核心期刊选刊七阶段交互流（同构 AFP）：稿件画像（含学科归属/栏目契合/时效）→ 偏好采集（认定目录体系/学科类目/见刊时限/版面费/发文类型）→ 栏目级竞争扫描 → 候选池 → 五关排雷（含假刊/套刊/增刊/代发识别）→ 匹配打分 → 冲/稳/保三档；内置四大核心目录体系（北大核心/CSSCI/CSCD/科技核心）与 2026 换届窗口情报；G1/G2 硬门槛，评分含时效 20%（赶不上截止日期则总分作废）；红线：不代投不代办 |
| `school-news-oa-writer` | 1.0.0 | 按学校 OA 规范生成可直接投稿的 Word 新闻稿（字数分级 + 排版模板 + norma 行文偏好） |
| `textbook-review` | 1.0.0 | 技术教材出版规范四维审查（小白可执行性 / 技术严谨性 / 教学法有效性 / 出版规范性）+ 自动化预检脚本 |
| `norma-textbook-deck` | 1.0.0 | 把教材 Markdown 章节稳定复现成飞书教学课件 + PPTX + 代码外置，科技深蓝风 |
| `textbook-deck-dark-blue` | 1.0.0 | 教材章节 → 教学课件，默认科技深蓝风，重流程/图示/对比，正文不贴代码 |
| `norma-vocational-course-framework` | 1.0.0 | 职业本科智慧课程框架方法论，从政策依据到教材编写全流程（AFP-SPEC silver·provisional） |
| `zhinengti-quan-format` | 1.0.0 | 智能体圈深度教程飞书文档标题层级规范（H1→H2→H3→H4 中文编号） |

### 三、内容创作

| Skill | 版本 | 说明 |
|---|---|---|
| `content-topic-finder` | 1.0.0 | 从爆款样本浸泡学习并结合网络热点输出选题清单 |
| `wechat-d2-concept` | 1.0.0 | 公众号「一文读懂 N 个术语」概念辨析型（D2）爆款文章写作 |
| `capcut` | 1.0.0 | 剪映 / CapCut 建图 / 设计 / 改稿 / 剪辑 / 建模 / 配置 / 教学助手 |
| `dashi-ppt` | 1.0.0 | 基于预置主题的 PPT 演示生成引擎，输出可离线 HTML 演示 + 导出 PPTX/PDF |
| `dashi-ppt-cn` | 1.0.0 | 中文教材章节 → 可编辑 PPTX 优化引擎（绕过 maxH / 6 条上限 / 英文泄漏） |
| `norma-video-style-teardown` | 1.0.0 | 拆解参考视频结构 / 风格 / 动画转场，产出可套拍复刻规格 |
| `web-animation-design` | 1.0.0 | Web 动画设计与实现，自然且有目的感的动效 |
| `xian-gong-video` | 1.0.0 | 云上仙宫 / 中式天庭 AI 视频生成规则与提示词模板 |

### 四、金融投研

| Skill | 版本 | 说明 |
|---|---|---|
| `etf-dca-analysis` | 1.0.0 | ETF 定投回测：周/月定投 vs 一次性投入，输出 IRR、最大回撤与暗色主题 HTML 报告 |
| `etf-three-lights` | 6.0.0 | ETF 四盏灯趋势分析 v6.0：顺风灯 / 风力灯 / 起锚灯 / 市场环境灯 + ADX 强度过滤 |
| `stock-holding-lights` | 1.0.0 | 个股持仓四灯信号监控：资金 + 估值 + 技术多维，操作语义（卖/等/持/买） |
| `a-stock-data` | 3.2.3 | A股全栈数据工具包，行情 / 研报 / 信号 / 资金面 / 新闻 / 基础数据一体化查询（第三方，源：github.com/simonlin1212/a-stock-data） |
| `chokepoint-analysis` | 1.0.0 | 卡脖子技术投资分析，从技术维度评估产业链薄弱环节与国产替代 |

### 五、效率与工具

| Skill | 版本 | 说明 |
|---|---|---|
| `archive-doctor` | 1.1.0 | 压缩包「损坏 vs 加密」诊断与批量解压，含回收站文件消失取证 |
| `md-pdf-cover-watermark` | 1.0.0 | Markdown 批量转「封面 + 全页水印 + 页码」A4 PDF（纯标准库 CDP 打印 + mermaid 渲染） |
| `norma-resource-link-logger` | 1.3.0 | 把链接（仓库/网页/教程/论文/视频）记录到资源分享链接库，自动查重、抓元数据、分类、回读验证 |
| `norma-drawio-technical-roadmap` | 2.0.0 | 参考图版式 + 资料 → 可直接粘贴进 draw.io 的未压缩 XML 技术路线图（AFP Bronze 合规） |
| `opc-business-positioning-v2` | 1.0.0 | 一人公司定位方法论：锁定商业象限、优势甜蜜区与商业原力，生成一句话定位 |
| `html-to-docx-on-windows` | 1.0.0 | 在 Windows 让 tencent-docx 的 HTML→DOCX 转换跑通（绕过虚拟环境失败） |
| `html-tool-dom-stub-test` | 1.0.0 | 单文件 HTML 工具功能回归测试，Node + DOM 桩真跑脚本验证逻辑 |
| `kwiki-periodic-archive` | 1.0.0 | WPS 知识库周期性归档，旧内容归纳摘要写回并删原文（三重护栏） |
| `library-doc-to-pptx` | 1.0.0 | 资料库在线文档正文 → 可编辑 PPTX（XML 转 MD + slidep 链路上手） |
| `llm-wiki-ingest` | 1.0.0 | LLM Wiki 自动知识库维护，对话产出 / 上传文件自动摄入 Obsidian 知识库 |
| `office-readback-verify` | 1.2.0 | 零依赖读取 Office 文件并对写入结果逐格回读校验 |
| `scanned-pdf-ocr` | 1.0.0 | 扫描件 PDF OCR 提取全文（本地 Rapid 引擎） |
| `tencent-docs-smartsheet-form` | 1.0.0 | 把题目清单做成腾讯文档在线可填报问卷（智能表格 + 表单视图） |
| `wps-knowledgebase` | 2.0.2 | WPS / zhishi 云端知识库列表 / 详情 / 问答 / 分享 / CRUD / 导入 |

---

## 目录结构

```
skills/
├── afp-skill-creator/
│   ├── SKILL.md          # 薄主控（路由 + 触发词）
│   ├── modules/          # 按需加载的模块文档
│   ├── stages/           # 阶段执行文档
│   └── templates/        # 模板
├── norma-lit-review/
│   ├── SKILL.md
│   └── ...
├── <skill-name>/
│   ├── SKILL.md          # 必须：frontmatter + 主控说明
│   ├── references/       # 参考文档（可选）
│   ├── scripts/          # 可执行脚本（可选）
│   └── assets/           # 静态资源（可选）
└── README.md
```

## 版本记录约定

- 分支：`main` 为唯一长期分支，功能改动走短生命周期分支后合并。
- 提交信息：`<type>(<skill>): <summary>`，type 取 `feat` / `fix` / `docs` / `refactor` / `chore`。
  - 例：`feat(etf-three-lights): 新增 ADX 趋势强度过滤`
- 打标签：整仓里程碑用 `vX.Y.Z`（如 `v1.0.0`）；单 skill 版本以各 `SKILL.md` 的 `version` 字段为准。
- **基线版本（2026-10-02 补登）**：此前 30 个自建 skill 的 `SKILL.md` 缺 `version` 字段，本次统一补登。其中 5 个取自 skill 自身的版本声明——`afp-skill-creator` 0.4.0、`etf-three-lights` 6.0.0、`stock-holding-lights` 1.0.0、`norma-textbook-deck` 1.0.0、`textbook-review` 1.0.0；**其余 25 个为声明式起点 `1.0.0`，不代表历史迭代次数**（此前从未纳入版本管理，无历史可考），此后按语义化版本递增。
- **一致性核对**：`norma-skills-publish/scripts/check_readme_versions.py`，比对 README 版本列与各 `SKILL.md` frontmatter，有漂移则退出码 1。
- 双远端：`origin` = GitHub，`gitee` = Gitee，推送时两个远端同步。

```bash
git add -A
git commit -m "feat(skill-name): 说明"
git tag v1.0.0
git push origin main --tags
git push gitee  main --tags
```

## 版权与许可

本仓库内**全部自建 skill** 统一适用 **PolyForm Noncommercial License v1.0.0**（完整条款见根目录 `LICENSE`，
官方文本 <https://polyformproject.org/licenses/noncommercial/1.0.0>）。

| 维度 | 条款 |
|---|---|
| ✅ 允许 | 阅读、复制、修改、创作衍生作品、再分发 |
| ✅ 允许 | 个人学习研究、非营利教学使用 |
| ✅ 教育豁免 | 协议明文豁免教育机构（educational institution），**与 funding 来源无关** |
| ❌ 禁止 | 任何商业用途（销售、付费服务、企业内部经营性使用、SaaS 化） |
| ⚠️ 专利 | 授予专利许可；使用者提起专利侵权诉讼则专利许可**立即终止** |
| ⚠️ 终止 | 违约给予 32 天补救期，仍不改正则许可终止 |
| ⚠️ 作者权利 | 不限制作者另行签发商业许可（双重许可） |

**Required Notice: Copyright 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院**

### 版本许可说明

| skill | 适用起始版本 | 依据 |
|---|---|---|
| `norma-lit-review` | **自 v0.10.0 起** | 原为 GPL-3.0，因其允许商用与本仓库目标冲突而更换；v0.9.x 及更早为历史状态 |
| `norma-paper-format-check` | **自初始版本起** | 首次公开发布即适用本协议 |
| 其余 44 个自建 skill | **自初始版本起** | 首次公开发布即适用本协议 |

**本许可仅约束作者后续发布的新版本。** 任何人已获得的旧版本许可不可撤销，作者无权收回；旧版本可继续按其原许可流转。
若本仓库将来接受外部贡献，改协议前需取得每位贡献者同意（建议预先签署 CLA）。

### 第三方 skill 不适用本许可

`academic-research-skills`、`openmaic__skillhub`、`jianying-editor` 各自持独立 LICENSE，
版权不属于本仓库作者，**本仓库无权修改其许可条款**。其中 `jianying-editor` 为 MIT 协议（Copyright (c) 2026 luoluoluo22），
**MIT 明确允许商用**，不适用本仓库的 NC 约束，已移出 git 跟踪范围、仅保留本地使用。

## 纳入范围

- ✅ 仅纳入自建 skill。
- ❌ 不纳入第三方 skill：`academic-research-skills`、`openmaic__skillhub`、`jianying-editor`（各自有独立 LICENSE，需单独授权管理）。
  - `jianying-editor` 为 **MIT 协议、Copyright (c) 2026 luoluoluo22**，非本仓库自建。MIT 允许商用，且版权不属本仓库作者，**无权将其改标为 NC**，故移出统一许可范围，仅保留本地使用。
- ❌ 不纳入 WorkBuddy 运行时状态文件（`.*_migration.json`）、打包产物（`*.zip`）与构建产物（`scripts/build/`）。

## 注意

部分 skill 的脚本内含 Windows 绝对路径兜底值（如 `C:/Users/admin/.workbuddy/binaries/...`）。当前仓库为私有，可保留；**若将来转为公开，需先运行 `skill-packager` 的审计流程做路径泛化与密钥排查**。
