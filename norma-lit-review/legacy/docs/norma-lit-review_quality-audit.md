# norma-lit-review 质量审查报告

> 审查方式：技能匠人 · B 线（优化已有 Skill）只读五阶段审查
> 审查对象：`C:\Users\admin\.workbuddy\skills\norma-lit-review\`（v0.6）
> 审查日期：2026-08-23
> 审查纪律：只读，未改动包体任何文件；脚本仅做隔离环境离线冒烟

---

## 一、总体结论

**结论：需修改（距离"可参赛"只差一步）**

- 五阶段审查：结构体检命中 1 项 P1 + 4 项 P2；安全红线无问题；实测部分脚本离线冒烟通过、网络分支未实测；制作质量 11 维平均 **8.9**。
- 所有适用维度均 ≥ 8 分，但存在**未解决的 P2 项**（最关键的是文档引用了包里并不存在的脚本），且脚本的网络核验分支未实测——因此不满足"可参赛"门槛（要求无未解决 P2 且脚本实测有证据）。
- 这个 Skill 的**设计思想非常成熟**（Type-First 类型前置、P6 真实性硬门槛、双审制 + 修订闭环、研究方法化留痕），领域信息增量真实，不是模板拼凑。修掉下面 P1/P2 后即可参赛。

---

## 二、五阶段审查记录

### 第一阶段：结构体检
- [x] SKILL.md 存在，正文 228 行（≤500）
- [x] name 合规且与目录同名
- [ ] **P1：frontmatter 缺 `version` 字段**（本地模型创建的 Skill 须含有效 version + agent_created:true；当前仅 agent_created:true）
- [x] description 20–1024 字符，含做什么/何时用/触发短语
- [x] 加载式引用只存在于 SKILL.md 且 stages/ modules/ 真实存在
- [ ] **P2：stage 02 / stage 06 引用了包内并不存在的 `arxiv_client.py`（及 `ArxivClient`/`SemanticScholarClient` 类）**——引用逃逸
- [x] 无 TODO / 占位示例 / 改动注释 / 历史 log（注：正文版本号标注属另一问题，见 P2-2）
- [ ] **P2：SKILL.md 正文含"*版本：v0.6*"标注**（违反"正文内不出现版本标注"纪律）
- [x] 确定性操作已下沉 scripts（verify_references.py 仅 stdlib）
- [~] 非标准 frontmatter 字段（partner/skill_type/afp_spec_target）属噪音，见 P3-2

### 第二阶段：安全红线
- [x] 无硬编码密钥/凭据外发；S2_API_KEY 仅经环境变量或参数，明确"不内置、不保存"
- [x] 无混淆/编码隐藏逻辑；脚本无 eval/exec
- [x] 无提示词注入、工具诱导、数据外传；无静默删除（所有写盘均经 Hard Stop 确认）
- [x] 改变本地状态（写盘、Edit）均列明对象与确认机制
- [x] 无路径穿越/软链接逃逸（脚本读 --input 写 --output，无通配符）

### 第三阶段：实测验证
- 对话与触发：**未做端到端对话实测**（审查范围为静态质量评估；如需可补 3–5 场景触发测试）
- 脚本实测：**离线冒烟通过**——NO_ID 分支不联网正常输出；非法输入（非数组）exit=1 且有明确报错。网络核验分支（arXiv/S2）未执行（需联网+可选 key，且审查保持只读）。
- 静态预检：脚本仅用 stdlib（urllib/xml/difflib），含超时(30s)、429 退避、相似度阈值 0.70，无动态执行、无凭据收集、无路径穿越。

### 第四阶段：制作质量 11 维

| # | 维度 | 评分 | 关键证据 |
|---|------|------|---------|
| 1 | 选题价值 | 9 | 职教本科老师写 Related Work/综述为真实高频痛点；切口深（理工+职教+防编造被秒拒）；README 适用场景具体 |
| 2 | 定位清晰度 | 9 | description(4-11) 与正文(18-48)一致；一句话说清做什么/为谁 |
| 3 | 触发描述质量 | 9 | 触发词覆盖 12 个真实说法 + 触发隔离规则（仅"写综述/搜文献"触发） |
| 4 | 信息增量 | 9 | 真实领域知识：PRISMA/PRISMA-ScR、evidence-mapping E0-E4、34 条反模式、verified-retrieval 协议、检索方法论（召回率/滚雪球/遗漏评估） |
| 5 | 工作流完整性 | 9 | P0-P9 全链路；每阶段输入/产物/Hard Stop/断点续传；按类型分支；T4→T1 降级明确 |
| 6 | 输出可执行性 | 9 | 固定 Hard Stop 卡、审核报告模板、HUD 状态机、产物路径明确、验收标准明确（字数闸门/门禁） |
| 7 | 边界与停止条件 | 9 | P6 禁止模式、gate_passed 强约束、降级与停止清晰；不编造文献硬约束 |
| 8 | 复杂度适配 | 8 | 10 阶段+HUD 状态机偏重但领域确需；首版可用、非最小机制化 |
| 9 | 参考资料质量 | 8 | 顶层直达、stages/modules 单源按需加载；但存在引用逃逸(见 P2-1)拉低 |
| 10 | 脚本健壮性与实测 | 8 | 静态安全+离线冒烟通过；网络分支未实测、且文档指向不存在的类 |
| 11 | 安全与隐私 | 9 | 无密钥硬编码、env 优先、无静默删除、状态变更均确认 |

**平均分：8.9**（11 维等权，保留一位小数）

### 跨维度一致性检查
- **检查 1（维3 ↔ 维5/维7）**：SKILL.md 称"三处 Hard Stop"漏 P0，README 称四处含 P0，stage00 又明确 P0 为强制选择 → 文档自相矛盾，已列 P2-3。
- **检查 2（维9 ↔ 维10）**：文档引用的 `arxiv_client.py`/`ArxivClient` 与实际包内 `verify_references.py` 不符，直接削弱脚本可用性，已列 P2-1（最高优先）。
- **检查 3（维8 ↔ 结构体检）**：版本号散落在正文(v0.6)、README、却不在 frontmatter → 统一修复见 P1-1 + P2-2。

### 第五阶段：综合结论
- 未命中"需重做"（无 P1 阻断核心流程、无维度≤3、平均分≥6）。
- 命中"需修改"：存在未解决 P2、脚本网络分支未实测、维度 8/9/10 未达 9。

---

## 三、修复清单（P1 / P2 / P3）

### P1（必须修，阻断交付/更新）
- **P1-1 frontmatter 缺 `version`**
  位置：SKILL.md 2-16 行 frontmatter。
  现状：有 `agent_created: true`、`partner`、`skill_type`、`afp_spec_target`，但无 `version`。
  修复：新增 `version: 1.0.0`（当前标称 v0.6，可统一从 1.0.0 起，或保留 0.6.x 但须严格自增）；install/update 流程依赖此字段做版本自增与回滚。

### P2（需修改）
- **P2-1 引用了不存在的脚本/类（最高优先）**
  位置：stage/02-multi-db-search.md 76-77；stage/06-reference-verification.md 52-67。
  现状：
  - stage02：「用 `arxiv_client.py` 的 `ArxivClient.arxiv_id_lookup(id, title)` 做 0.70 相似度比对」
  - stage06：「用 `arxiv_client.py` 的 `ArxivClient.arxiv_id_lookup(...)`」「用 `SemanticScholarClient.lookup(...)`」
  - 但包内**只有** `scripts/verify_references.py`（flat 函数 `arxiv_lookup()`/`s2_lookup()`，无 class，无 `arxiv_client.py`）。
  - stage06 §2-A 同时自相矛盾地既说"用 arxiv_client.py"又说"批量运行：`scripts/verify_references.py`"。
  修复：统一改为调用 `scripts/verify_references.py`（CLI：`python scripts/verify_references.py --input refs.json [--output report.md]`，可选 `S2_API_KEY` 经环境变量）；删除 `ArxivClient`/`SemanticScholarClient` 引用。若确实想要类封装，则补建 `scripts/arxiv_client.py` 并自测。

- **P2-2 正文版本标注**
  位置：SKILL.md 226 行"*版本：v0.6 · 2026-08-23*"；README 多处 v0.6。
  修复：版本只在 frontmatter（P1-1），SKILL.md 正文末移除版本行；README 可保留"本版变更"说明但勿作正文版本标注。

- **P2-3 Hard Stop 计数不一致**
  位置：SKILL.md 27 行"检索策略、筛选标准、综述大纲三处 Hard Stop"（漏 P0）。
  修复：改为四处——P0 类型选择、P1 检索策略、P3 文献筛选、P5 综述大纲（与 README §六 及 stage00 一致）。

- **P2-4 标题编号混乱/重复**
  位置：stage01（一/二/三/三-B/四-B/四，非连续）；stage04 两个"四-B"（92 与 102 行）；stage06（四 / 四-B）。
  修复：重排为连续层级（如 一/二/三/四… 或统一用 1/2/3）；分叉用 2-A/2-B 而非"三-B/四-B"。

### P3（建议）
- **P3-1** 空 `templates/` 目录未在任何文档引用 → 删除或补用途说明。
- **P3-2** frontmatter 非标准字段 `partner`/`skill_type`/`afp_spec_target` → 上架前移除或并入 description 注释（不影响运行，但属噪音）。
- **P3-3** SKILL.md 阶段表(149-153) 只列 P4 主产物 `analysis_report.md`，漏 `gap_summary.md`；P5 漏 `references.bib` → 主表补全或加"等"。
- **P3-4** 脚本 `--api-key` 走命令行参数，密钥可能暴露于进程列表 → README 已主推 env，建议脚本 `--help`/注释再强调"优先用环境变量"。

---

## 四、未覆盖范围与后续建议

1. **未做端到端对话触发实测**：建议补 3–5 个场景（含 1–2 条 near-miss 如"帮我写篇论文"不应触发、"搜一下多智能体文献"应触发），验证意图识别与 Hard Stop 落盘。
2. **脚本网络分支未实测**：arXiv/S2 真实核验需联网（且 S2 无 key 易被 429）；建议在你本机用 3–5 条真实 DOI/arXiv ID 跑一次，确认相似度阈值 0.70 不会误杀规范标题。
3. **修复顺序建议**：先 P1-1（加 version）→ P2-1（修脚本引用，最影响可用性）→ P2-2/3/4（文档一致性）→ P3 收尾。改完跑一次 validate 即可参赛。

---

*本审查为只读评估，未修改 skill 包任何文件。修复需你确认写入计划后执行。*
