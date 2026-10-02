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
| `afp-skill-creator` | — | AFP 方法论元 skill：引导在任意领域产出符合 AFP-SPEC 的 skill 包（薄路由 + 触发词隔离 + 渐进披露） |
| `skill-packager` | — | 把 skill 目录打包为可分发 zip，打包前执行安全审计（拦截硬编码密钥、个人环境路径） |
| `skill-to-expert-team` | 1.4.0 | 把单 skill 改造为多角色协作专家团（expertType=team）：团长编排 + 按域拆成员 + 原 skill 内嵌为共享工具箱 |
| `norma-skills-publish` | — | 把单个本地自建 skill 并入 norma-skills monorepo 并推送 GitHub+Gitee 双远端（含 README 登记） |
| `skill-install-audit` | — | 从本地 zip / GitHub 仓库安全安装 skill，先执行 P0/P1/P2 安全审计再落盘 |
| `wikiskill` | — | 基于 WikiSkill(arXiv:2608.27454) 把执行经验编译成持久化知识库，使 skill 在验证集门控下逐轮进化 |

### 二、教学与科研

| Skill | 版本 | 说明 |
|---|---|---|
| `norma-lit-review` | 0.17.0 | 理工科文献综述全流程：检索策略 → 多库检索 → 筛选分类 → 研究缺口 → 结构化综述 |
| `sci-journal-selection` | 1.2.0 | SCI 选刊决策七阶段交互流：论文画像 → 期刊偏好 → 竞争格局 → 候选池 → 硬排雷 → 匹配打分 → 冲/稳/保 |
| `school-news-oa-writer` | — | 按学校 OA 规范生成可直接投稿的 Word 新闻稿（字数分级 + 排版模板 + norma 行文偏好） |
| `textbook-review` | 1.0.0 | 技术教材出版规范四维审查（小白可执行性 / 技术严谨性 / 教学法有效性 / 出版规范性）+ 自动化预检脚本 |
| `norma-textbook-deck` | — | 把教材 Markdown 章节稳定复现成飞书教学课件 + PPTX + 代码外置，科技深蓝风 |
| `textbook-deck-dark-blue` | — | 教材章节 → 教学课件，默认科技深蓝风，重流程/图示/对比，正文不贴代码 |
| `vocational-course-framework` | — | 职业本科智慧课程框架方法论，从政策依据到教材编写全流程 |
| `zhinengti-quan-format` | — | 智能体圈深度教程飞书文档标题层级规范（H1→H2→H3→H4 中文编号） |

### 三、内容创作

| Skill | 版本 | 说明 |
|---|---|---|
| `content-topic-finder` | — | 从爆款样本浸泡学习并结合网络热点输出选题清单 |
| `wechat-d2-concept` | — | 公众号「一文读懂 N 个术语」概念辨析型（D2）爆款文章写作 |
| `capcut` | 1.0.0 | 剪映 / CapCut 建图 / 设计 / 改稿 / 剪辑 / 建模 / 配置 / 教学助手 |
| `dashi-ppt` | — | 基于预置主题的 PPT 演示生成引擎，输出可离线 HTML 演示 + 导出 PPTX/PDF |
| `dashi-ppt-cn` | — | 中文教材章节 → 可编辑 PPTX 优化引擎（绕过 maxH / 6 条上限 / 英文泄漏） |
| `jianying-editor` | — | 剪映 AI 自动化剪辑 JyWrapper，Python 接口 + 字幕 + Web 动效合成 |
| `norma-video-style-teardown` | — | 拆解参考视频结构 / 风格 / 动画转场，产出可套拍复刻规格 |
| `web-animation-design` | — | Web 动画设计与实现，自然且有目的感的动效 |
| `xian-gong-video` | 1.0.0 | 云上仙宫 / 中式天庭 AI 视频生成规则与提示词模板 |

### 四、金融投研

| Skill | 版本 | 说明 |
|---|---|---|
| `etf-dca-analysis` | — | ETF 定投回测：周/月定投 vs 一次性投入，输出 IRR、最大回撤与暗色主题 HTML 报告 |
| `etf-three-lights` | — | ETF 四盏灯趋势分析 v6.0：顺风灯 / 风力灯 / 起锚灯 / 市场环境灯 + ADX 强度过滤 |
| `stock-holding-lights` | — | 个股持仓四灯信号监控：资金 + 估值 + 技术多维，操作语义（卖/等/持/买） |
| `A股全栈数据` | 3.2.3 | A股全栈数据工具包，行情 / 研报 / 信号 / 资金面 / 新闻 / 基础数据一体化查询 |
| `chokepoint-analysis` | — | 卡脖子技术投资分析，从技术维度评估产业链薄弱环节与国产替代 |

### 五、效率与工具

| Skill | 版本 | 说明 |
|---|---|---|
| `archive-doctor` | 1.1.0 | 压缩包「损坏 vs 加密」诊断与批量解压，含回收站文件消失取证 |
| `md-pdf-cover-watermark` | — | Markdown 批量转「封面 + 全页水印 + 页码」A4 PDF（纯标准库 CDP 打印 + mermaid 渲染） |
| `norma-resource-link-logger` | 1.3.0 | 把链接（仓库/网页/教程/论文/视频）记录到资源分享链接库，自动查重、抓元数据、分类、回读验证 |
| `norma-drawio-technical-roadmap` | 2.0.0 | 参考图版式 + 资料 → 可直接粘贴进 draw.io 的未压缩 XML 技术路线图（AFP Bronze 合规） |
| `opc-business-positioning-v2` | — | 一人公司定位方法论：锁定商业象限、优势甜蜜区与商业原力，生成一句话定位 |
| `html-to-docx-on-windows` | — | 在 Windows 让 tencent-docx 的 HTML→DOCX 转换跑通（绕过虚拟环境失败） |
| `html-tool-dom-stub-test` | — | 单文件 HTML 工具功能回归测试，Node + DOM 桩真跑脚本验证逻辑 |
| `kwiki-periodic-archive` | — | WPS 知识库周期性归档，旧内容归纳摘要写回并删原文（三重护栏） |
| `library-doc-to-pptx` | 1.0.0 | 资料库在线文档正文 → 可编辑 PPTX（XML 转 MD + slidep 链路上手） |
| `llm-wiki-ingest` | — | LLM Wiki 自动知识库维护，对话产出 / 上传文件自动摄入 Obsidian 知识库 |
| `office-readback-verify` | 1.0.0 | 零依赖读取 Office 文件并对写入结果逐格回读校验 |
| `scanned-pdf-ocr` | — | 扫描件 PDF OCR 提取全文（本地 Rapid 引擎） |
| `tencent-docs-smartsheet-form` | — | 把题目清单做成腾讯文档在线可填报问卷（智能表格 + 表单视图） |
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
- 双远端：`origin` = GitHub，`gitee` = Gitee，推送时两个远端同步。

```bash
git add -A
git commit -m "feat(skill-name): 说明"
git tag v1.0.0
git push origin main --tags
git push gitee  main --tags
```

## 纳入范围

- ✅ 仅纳入自建 skill。
- ❌ 不纳入第三方 skill：`academic-research-skills`、`openmaic__skillhub`（各自有独立 LICENSE，需单独授权管理）。
- ❌ 不纳入 WorkBuddy 运行时状态文件（`.*_migration.json`）、打包产物（`*.zip`）与构建产物（`scripts/build/`）。

## 注意

部分 skill 的脚本内含 Windows 绝对路径兜底值（如 `C:/Users/admin/.workbuddy/binaries/...`）。当前仓库为私有，可保留；**若将来转为公开，需先运行 `skill-packager` 的审计流程做路径泛化与密钥排查**。
