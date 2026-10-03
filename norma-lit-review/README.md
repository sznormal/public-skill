# Norma 理工科文献综述 Skill

> 维护者：Norma
> AFP-SPEC 目标等级：Silver

一个专为职教本科 / 应用型本科理工教师设计的文献综述助手。输入一个研究方向，走完 10 个阶段
（**综述类型选择(P0)** → 检索策略 → 多库检索 → 文献筛选 → 文献分析 → 综述撰写 →
**参考文献真实性核验** → 质量审核 → **审稿人角色发表级审查** → **审稿后修订闭环**），
输出一份结构清晰、引用规范、**每篇参考文献都经联网核验为真实存在**、且达到投稿就绪标准的综述。

**本 skill 是"综述研究方法流水线"，而不只是"综述写作流水线"**：
检索可复现留痕（检索日志 + 种子召回率测试 + 遗漏风险评估）、筛选决策逐篇留痕、
论断-证据映射（E0–E4 强度分级 + 孤证/无据显式标记）——正面回答审稿人四问：
**怎么检索的？为什么选这些文献？有没有遗漏？判断有没有足够证据？**

---

## 一、这是什么

- 它不是「一键生成全文」的玩具，而是一套**可质控的学术生产流程**。
- 核心能力：类型前置（Type-First）、参考文献真实性硬门槛、双审制（助手自审 + 审稿人角色）、
  审稿后修订闭环。
- 每一道护栏，都是被一次真实的拒稿翻车逼出来的。

## 二、适用场景

- 写论文的 Related Work / 文献综述章节
- 选题前快速摸底某个方向的可行性（对应 T1 叙述型 / T3 范围型）
- 带学生做文献研读（对应 T1 / T5 观点型）
- 备战学术写作 / 智能体类比赛

---

## 三、安装说明

本 skill 以文件夹形式分发，**不依赖任何第三方依赖**（核验脚本仅用 Python 标准库）。

**方式 A：放入用户级技能目录（对所有项目生效）**
```
# 把解压出的 norma-lit-review/ 整个文件夹放到：
Windows:  %USERPROFILE%\.workbuddy\skills\norma-lit-review\
macOS/Linux: ~/.workbuddy/skills/norma-lit-review/
```

**方式 B：放入项目级技能目录（仅当前项目生效）**
```
把 norma-lit-review/ 放到：
{你的项目}/.workbuddy/skills/norma-lit-review/
```

**验证安装**
- 重启 / 刷新 WorkBuddy 后，在对话里输入「帮我写一篇 XXX 方向的文献综述」，
  若它先询问研究主题、时间范围、目标期刊，并进入 P0 类型选择，即安装成功。

**可选依赖（仅检索 / 核验脚本需要）**
- Python 3.8+（建议用 WorkBuddy 自带的 managed Python）。
- 无需 `pip install`，三个脚本都只用 stdlib（urllib / xml / json / difflib）。
- **arXiv 不需要任何 API key**：`scripts/fetch_arxiv.py` 直连免费的 arXiv Export API，
  自带 3 秒/请求限速；只有给 Semantic Scholar 提速时才可选配 `S2_API_KEY`（见第四节第 5 条）。
- **正式刊出三库也不需要任何 API key**：`scripts/fetch_lit.py` 直连 OpenAlex / Crossref /
  OpenCitations，三者均免费、无需注册，自带 0.5–1.5 秒/请求限速。
  唯一"要填"的是**一个邮箱**（进 polite pool）——不是注册、不是密钥，
  脚本会在运行时**交互式询问**你，也可 `--mailto` 或设环境变量 `LIT_MAILTO`；
  不填也能正常运行，仅限速更严。

---

## 四、使用指南

### 1. 触发
直接说以下任一即可触发：
- "帮我写一篇 XXX 方向的文献综述"
- "做一下 XXX 的文献调研"
- "梳理 XXX 方向的研究现状"
- "写 literature review"

### 2. 十个阶段（每阶段完成后会落盘，并弹出 Hard Stop 等你确认）
| 阶段 | 名称 | 产出 |
|------|------|------|
| P0 | 综述类型选择（Type-First 硬门槛） | type_profile.md |
| P1 | 检索策略制定（概念组块+种子文献表） | search_strategy.md |
| P2 | 多库检索执行（检索日志+召回率+遗漏评估） | raw_literature_list.json + search_log.md |
| P3 | 文献筛选与分类（筛选决策留痕 + **选文确认**：逐篇按类型给选取理由，用户确认/增删后才进 P4） | screened_literature.md + screening_decisions.md |
| P4 | 文献分析与综合（预备论断清单） | analysis_report.md + gap_summary.md |
| P5 | 综述撰写（论断-证据回填） | literature_review_draft.md + claim_evidence_map.md + references.bib |
| P6 | 参考文献真实性核验（逐条联网） | reference_verification_report.md |
| P7 | 质量审核（助手自审 + 字数闸门 + 证据一致性） | review_quality_report.md |
| P8 | 审稿人角色发表级审查（含 **8 维度量化评分**：≥85 投稿水平 / <85 自动进 P9 修订后回 P8 复分） | reviewer_review_report.md |
| P9 | 审稿后修订闭环 | submission 版 + response_letter.md |

### 3. 通用指令
- `Next`：确认当前阶段，进入下一步
- `Back`：回退到上一阶段
- `Edit <字段>=<新值>`：修改状态字段
- `Status`：查看当前进度
- `Continue`：从磁盘恢复上次断点续传

### 4. 断点续传
- 状态文件：`{project}/outputs/lit-review/hud_state.json`
- 每阶段完成后自动写入；新对话说 `Continue {project}` 即可接着干。
- 老师时间碎，这点很关键。

### 5. 关于 API Key 与邮箱（重要）
**本 skill 不内置任何 API key，也绝不会替你保存密钥或邮箱。**

- **arXiv 完全不需要 key**：`scripts/fetch_arxiv.py` 直连 arXiv Export API，
  免费、无需注册、无需认证，脚本自带 3 秒/请求限速。
- **正式刊出三库也不需要 key，只要一个邮箱（可选）**：OpenAlex / Crossref /
  OpenCitations 均免费开放。`scripts/fetch_lit.py` 运行时会以**交互式提示**询问邮箱
  ——它不是注册、不是 API key，官方仅作限流时的联系方式（不会发营销邮件）。
  你可以：直接回车（用公共池，限流更严）／输入邮箱（进 polite pool，限额更高）／
  提前设环境变量 `LIT_MAILTO` ／用 `--mailto you@example.com` ／
  脚本化调用加 `--no-prompt` 跳过询问。**邮箱不会写入任何配置文件。**
- **唯一可选用到密钥的**是 P6 核验脚本对 Semantic Scholar 的限速解除：
  未配置 `S2_API_KEY` 也能正常运行，仅限速更严（≈1 req/s）。
- 若想提速到 ≈10 req/s，请**自行**到 https://www.semanticscholar.org/product/api
  免费申请 `S2_API_KEY`，然后用环境变量传入（不要写进会被云盘/版本库同步的文件）：
  ```bash
  # Linux / macOS
  export S2_API_KEY="你的key"
  python scripts/verify_references.py --input refs.json

  # Windows (cmd)
  set S2_API_KEY=你的key
  python scripts/verify_references.py --input refs.json
  ```
- 也可在调用时直接传参：`python scripts/verify_references.py --api-key "你的key" --input refs.json`

---

## 五、文件结构

```
norma-lit-review/
├── SKILL.md                              # 薄主控（路由 + 10 阶段定义 + HUD 状态机）
├── README.md                             # 本文件（安装 + 使用指南）
├── stages/                               # 10 个阶段，按需加载
│   ├── 00-type-selection.md              # P0 综述类型选择（Type-First 硬门槛）
│   ├── 01-search-strategy.md             # P1 检索策略制定
│   ├── 02-multi-db-search.md             # P2 多库检索执行
│   ├── 03-screening.md                   # P3 文献筛选与分类
│   ├── 04-analysis.md                    # P4 文献分析与综合
│   ├── 05-draft-generation.md            # P5 综述撰写
│   ├── 06-reference-verification.md      # P6 参考文献真实性核验（逐条联网）
│   ├── 07-quality-review.md              # P7 质量审核（含字数闸门）
│   ├── 08-publication-review.md          # P8 审稿人角色发表级审查
│   └── 09-revision.md                    # P9 审稿后修订闭环
├── modules/                              # 10 个按需模块，触发才加载
│   ├── stem-databases.md                 # 理工科数据库配置
│   ├── citation-standards.md             # 引用规范（GB7714 / IEEE）
│   ├── review-types.md                   # 综述类型定义与字数门禁
│   ├── review-structures.md              # 综述结构设计指南
│   ├── stem-review-anti-patterns.md      # 常见反模式清单（34 条）
│   ├── verified-retrieval-protocol.md    # 真实检索 / 核验协议
│   ├── search-methodology.md             # 检索方法论（检索日志/召回率/滚雪球/遗漏评估）
│   ├── evidence-mapping.md               # 论断-证据映射（E0-E4 强度分级/孤证披露/大纲推导）
│   ├── figure-export.md                  # 图稿矢量导出（SVG→PDF/EPS，中文字体注册）
│   └── quantitative-synthesis.md         # 定量综合可行性探针与可比性边界（元分析组件）
└── scripts/
    ├── fetch_arxiv.py                    # P2/P6 用：arXiv 检索与核验（仅 stdlib，无需 API key，3 秒/请求限速）
    ├── fetch_lit.py                      # P2/P6/T4 用：OpenAlex 检索 + Crossref DOI 核验 + OpenCitations 引文（免 key）
    └── verify_references.py              # P6 用：arXiv ID/DOI 批量核验并出报告（仅 stdlib）
```

## 六、设计理念

1. **AFP 薄路由**：SKILL.md 只做调度，细节在 stages/ 中按需加载，上下文不爆。
2. **人在回路**：P0（类型）、P1（策略）、P3（筛选+选文确认）、P5（大纲）四处 Hard Stop，用户确认才推进。
3. **落盘思维**：每阶段产物写入磁盘，支持断点续传。
4. **理工科专属**：IEEE / GB7714 双语引用，实验 / 仿真 / 系统设计方法分析。
5. **类型前置（Type-First）**：P0 先定综述类型（T1–T5），检索深度、分析维度、结构、门禁全链路分支。
6. **真实性硬门槛**：P6 逐条联网核验，未通过则 P7 不得判「可提交」，杜绝占位符与编造。
7. **双审制 + 修订闭环**：P7 自审、P8 审稿人审查、P9 逐条修订并跑复检闸门，确保零静默忽略。
8. **研究方法化**：不止是"写作流水线"——检索日志+召回率测试+
   遗漏评估（怎么检索/有无遗漏）、筛选决策留痕（为什么选这些）、论断-证据映射（判断有无证据）。

## 七、版权与作者

- **作者 / 维护者**：Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
- **许可证**：**PolyForm Noncommercial License v1.0.0**（自 **v0.10.0** 起适用），完整条款见仓库根目录 `LICENSE`。
  - **允许**：阅读、复制、修改、创作衍生作品、再分发。
  - **允许**：个人学习研究、非营利教学使用——协议**明文豁免教育机构**（educational institution），
    且**与 funding 来源无关**，高校教师用本 skill 备课教学属许可用途。
  - **禁止**：任何商业用途（销售、付费服务、企业内部经营性使用、SaaS 化）。
  - **含专利条款**：授予专利许可；若使用者对本 skill 提起专利侵权诉讼，专利许可**立即终止**。
  - **含终止条款**：使用者违约时给予 32 天补救期，仍不改正则许可终止。
  - **作者保留权利**：不限制作者另行签发商业许可（双重许可）。
  - © 2026 Norma（郑洪英）。基于 PolyForm Noncommercial v1.0.0 授权，转载与二次开发须保留本版权声明。
- **版本许可说明**：
  - **v0.10.0（2026-09-07）及之后**的全部版本适用 PolyForm Noncommercial v1.0.0。
  - **v0.9.x 及更早版本**为历史状态，不受上述声明追溯约束。
  - 本许可仅约束作者后续发布的新版本；他人已获得的旧版本许可不可撤销，作者无权收回。
- **历史变更**：本 skill 原为 GPL-3.0，因其明确允许商用（仅要求分发时附源码），与「可公开但禁止商用」的发布目标冲突，
  自 v0.10.0 起改用 PolyForm Noncommercial v1.0.0。GPL-3.0 全文留档于 `legacy/LICENSE-GPL-3.0-superseded.txt`，
  仅作历史溯源之用。
- **免责声明**：本 skill 输出仅供学术写作参考，所有引用的参考文献须由使用者逐条核验；
  因使用本工具产生的学术不端、误引或投稿风险，作者不承担任何责任。

---

*维护者：Norma*
