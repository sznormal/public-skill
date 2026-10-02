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

### 二、教学与科研

| Skill | 版本 | 说明 |
|---|---|---|
| `norma-lit-review` | 0.17.0 | 理工科文献综述全流程：检索策略 → 多库检索 → 筛选分类 → 研究缺口 → 结构化综述 |
| `sci-journal-selection` | 1.2.0 | SCI 选刊决策七阶段交互流：论文画像 → 期刊偏好 → 竞争格局 → 候选池 → 硬排雷 → 匹配打分 → 冲/稳/保 |
| `school-news-oa-writer` | — | 按学校 OA 规范生成可直接投稿的 Word 新闻稿（字数分级 + 排版模板 + norma 行文偏好） |
| `textbook-review` | 1.0.0 | 技术教材出版规范四维审查（小白可执行性 / 技术严谨性 / 教学法有效性 / 出版规范性）+ 自动化预检脚本 |

### 三、内容创作

| Skill | 版本 | 说明 |
|---|---|---|
| `content-topic-finder` | — | 从爆款样本浸泡学习并结合网络热点输出选题清单 |
| `wechat-d2-concept` | — | 公众号「一文读懂 N 个术语」概念辨析型（D2）爆款文章写作 |

### 四、金融投研

| Skill | 版本 | 说明 |
|---|---|---|
| `etf-dca-analysis` | — | ETF 定投回测：周/月定投 vs 一次性投入，输出 IRR、最大回撤与暗色主题 HTML 报告 |
| `etf-three-lights` | — | ETF 四盏灯趋势分析 v6.0：顺风灯 / 风力灯 / 起锚灯 / 市场环境灯 + ADX 强度过滤 |
| `stock-holding-lights` | — | 个股持仓四灯信号监控：资金 + 估值 + 技术多维，操作语义（卖/等/持/买） |

### 五、效率与工具

| Skill | 版本 | 说明 |
|---|---|---|
| `archive-doctor` | 1.1.0 | 压缩包「损坏 vs 加密」诊断与批量解压，含回收站文件消失取证 |
| `md-pdf-cover-watermark` | — | Markdown 批量转「封面 + 全页水印 + 页码」A4 PDF（纯标准库 CDP 打印 + mermaid 渲染） |
| `norma-resource-link-logger` | 1.2.0 | 把链接（仓库/网页/教程/论文/视频）记录到资源分享链接库，自动查重、抓元数据、分类、回读验证 |
| `norma-drawio-technical-roadmap` | 2.0.0 | 参考图版式 + 资料 → 可直接粘贴进 draw.io 的未压缩 XML 技术路线图（AFP Bronze 合规） |
| `opc-business-positioning-v2` | — | 一人公司定位方法论：锁定商业象限、优势甜蜜区与商业原力，生成一句话定位 |

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
