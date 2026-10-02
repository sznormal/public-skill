# 实战坑位与调试记录

本文件记录把 `suit-sz-teaching-suite-norma`（课程标准 + 教案 + 授课计划写作 skill）改造为
`suit-sz-teaching-team` 专家团（v1.0.0 建团 → v1.1.0 加装审核能力）过程中**真实踩到并有证据**的坑。
每条格式：现象 → 根因 → 修法 → 证据。

---

## 一、前置：skill 本体先达标，否则专家包里嵌的是坏件

### 1.1 frontmatter 用 YAML 折行块标量，平台解析直接失败

- **现象**：平台校验 `ok=false`，共 **19 个 issue**，其中 **17 个是 `frontmatter_invalid`**；`description` 解析为空 → 触发词失效 → 被判"低质量"。
- **根因**：`description_zh` / `description_en` / `description` 三字段写成 `>` 折行 + 缩进续行。平台的 frontmatter 解析器**只认顶层单行 `key: value`**。
- **修法**：全部改为单行标量，描述再长也不折行。
- **证据**：改造后 `skill_ops.py validate` → `ok=true, issues=0`；`preflight` 由 `blocked`（14 high）变为 `pass`（0 high）。

> 教训：**"内容质量不够"往往先表现为"根本解析不了"**。拿到低质量评级，第一步永远是跑平台校验器拿机器判据，不要先去改内容。

### 1.2 依赖型 skill 缺平台必备件

- **现象**：报 `dependency_guide` / `dependency_error` 类 issue。
- **根因**：技能声明了外部依赖（python-docx 等），但缺 `references/setup-guide.md`，且 `skill-dependencies.json` 的 `required` 标记、降级矩阵与功能清单三处对不上。
- **修法**：补 `setup-guide.md`；依赖清单里每个 `functional_degradations` 条目写全 8 个键——`capability` / `trigger` / `fallback` / `user_input` / `limitations` / `evidence_label` / `recovery` / `stop_condition`。
- **证据**：脚本化校验"每个条目字段完整"，输出 `所有 functional 条目字段完整 ✓`。

### 1.3 文档要求调用不存在的函数

- **现象**：SKILL.md 与 references 多轮要求调用 `insert_heading_table_before` / `strip_cell` / `append_cell` / `write_cell`，而 `docx_helpers.py` 里**一个都没有**——照做必然 `AttributeError`。
- **根因**：文档先行、实现缺失，属于典型的"纸面能力"。
- **修法**：要么补实现，要么从文档里删掉。本次全部补齐为真实函数，并把"让模型临场拼 python-docx 代码"的段落统一替换为**调确定性脚本**。
- **教训**：**文档里出现的每个函数名/脚本名/文件路径，都要能被 grep 到实体**。这是第八节"引用完整性扫描"存在的原因。

---

## 二、运行环境

### 2.1 bash 工具默认 PATH 不全

- **现象**：`find` / `head` / `grep` 等命令报 not found，脚本无法准备。
- **修法**：每条命令前显式 `export PATH="/usr/bin:/bin:/c/Windows/System32"`。
- **注意**：这是环境特性，不是脚本 bug——不要因此去改脚本。

### 2.2 Python 解释器分层，导致"能力误判"

- **现象**：skill 第一步写"运行 `python scripts/check_environment.py`"，但**干净环境里根本没有 `python` 命令**；真正带 python-docx 的解释器在 venv（`~/.workbuddy/binaries/python/envs/default`）。原自检只看 `sys.executable`，看不到 venv → **把运行级别误判为 L2**，核心 docx 能力在评测里从未被执行。
- **根因**：混淆了"受管运行时"（干净、无三方依赖）与"项目 venv"（装过依赖）。
- **修法**：`check_environment.py` 重写为**主动发现**带目标模块的解释器并回传其绝对路径，四态输出（ready / partial / needs_setup / unavailable），且**只读、不用 subprocess**。
- **证据**：用无 docx 的受管解释器调用时输出 `needs_setup` 并给出正确解释器路径；用 venv 解释器调用输出 `ready`。

### 2.3 目录里混入缓存与自评文件

- **现象**：提交包含 `__pycache__/`（7 个 `.pyc`）、`README.md`、自评"Silver"的 `AFP-SPEC-CONFORMANCE.md`。
- **修法**：全部删除；打包时排除 `__pycache__` / `*.pyc`。
- **教训**：**自评证书类文件在平台审核里是负分项**，不要放进技能包。

---

## 三、专家包结构

### 3.1 同文件两个 Edit 并发 → 首次修改被静默吞掉

- **现象**：`skill-dependencies.json` 里补的 `template-extract` 降级条目消失，`grep -c` 计数与预期不符。
- **根因**：**同一文件的两次 Edit 放在同一条消息里并发执行**，后写基于旧内容覆盖了先写。
- **修法**：同文件的多次编辑**必须串行**（等上一次返回再发下一次）；改完用 `grep -c "关键词" <file>` 核对出现次数。
- **证据**：改为串行后条目落位，脚本校验输出 `python-docx caps` 含 `template-extract`。

### 3.2 `members[]` 字段名不是 init 模板给的那个

- **现象**：init 生成的模板用 `displayName`，与现网 team 包不一致。
- **修法**：先查现网同类包（`investment-masters-team` / `stock-partner-team` / `a-share-analysis`）的 `plugin.json`，确认惯例是 **`name`**。同时确认 `author.email` 可留空（有先例）。
- **教训**：**模板 ≠ 惯例**。init 脚本生成的是骨架，字段语义以现网在跑 + 校验器为准。

### 3.3 init 会留下占位 agent

- **现象**：`agents/` 下有 `member-placeholder.md` 与 `<team>-team-lead.md` 两个占位文件。
- **修法**：写真实成员前先删掉，并把主理人文件改成**带业务语义的名字**（如 `teaching-doc-team-lead.md`），platform 不接受通用 `team-lead.md`。

### 3.4 头像生成与规格

| 项 | 记录 |
|---|---|
| 张数 | N+1（团队 1 张 + 成员 N 张） |
| 原始体积 | 约 **1–1.8 MB**，远超 500 KB 上限 |
| 压缩链 | 512×512（LANCZOS）→ PNG `optimize=True`；仍超限才降 JPEG `quality=88, progressive=True` |
| 实测结果 | 6 张压到 **289–492 KB**，全部合规 |
| 文件名 | 生成名是 prompt 派生长名（`Professional_cartoon_style_ill_2026-...png`），**必须重命名**为 plugin.json 声明的名字 |
| `.gitkeep` | 需删除 |
| **水印** | 生成图右下角带 **"AI 生成" 水印**，**无法通过参数去除**（平台策略，不要反复重试）。交付时主动告知用户可自行替换 |

### 3.5 主理人 prompt 只做编排，必须显式禁止代写

- **现象**：初版团长 prompt 没有明确"我不写正文"，模型容易越界直接产出课标内容，团队的其余成员形同虚设。
- **修法**：正文里写清"你自己不撰写任何 XX 正文"，并**点名列出**每个专业产出（不写课标、不写教案、不出督导结论），再配"5 条严禁行为"。

---

## 四、工具链（内嵌 skill 的脚本）

### 4.1 角色格式：整条记录取众数 → 离群段污染整类

- **现象**：版式提取把 `body`（正文）读成"居中 + 顶格"，与真实不符。
- **根因**：按"整条记录"聚合取众数时，**表标题段落**（居中、无缩进）混进正文角色，把整类带偏。
- **修法**：改为**逐维度取众数**（字体、字号、对齐、缩进、行距各自独立统计），并输出 `sample_count` / confidence。
- **证据**：修复后 `body` 正确读出 `仿宋 / 16pt / 左对齐 / 缩进 2 字符`，表标题被独立识别为 `caption` 角色。

### 4.2 期望值字典缺字段 → 同族字体误报

- **现象**：加了"按基线校验"后，selftest 回归失败 14 项。
- **根因**：无基线时回退的默认期望字典**缺少 `font_family` 归一字段**，导致 `仿宋` 与 `仿宋_GB2312` 被判为不一致。
- **修法**：`want_family = exp.get("font_family") or font_family(want_font)`，即缺字段时按期望字体名现场推导族。
- **证据**：修复后 selftest 恢复 8/8（后扩至 10/10）。

### 4.3 静态安全扫描会把等价写法误判为高危

- **现象**：`preflight` 报 `blocked`，命中 high 级 `file_delete` 类规则。
- **根因**：脚本里存在 `obj.remove(x)` 这类**文本模式**，被扫描器判为文件删除操作；实际只是操作 XML 元素。
- **修法**：改写为不命中删除模式的等价逻辑；改完**必须重跑 preflight 确认 high=0**。
- **判据约定**：`high = 0` 是硬要求；`medium`（写文件）属必要行为，可接受。**不要把 medium 也当成错误去"修"**，那会把脚本改成干不了活的样子。

### 4.4 基线必须被下游消费，否则是摆设

- **现象**：模板提取产出了版式基线 JSON，但 `validate_docx.py` 仍硬编码规范——提取结果无处使用，等于白提。
- **修法**：给校验器加 `--baseline <json>`，形成 **提取 → 渲染 → 校验** 的单一真相源；不传时回退内置默认规范（向后兼容）。
- **证据**：
  - 用**内置基线**校验正常文档 → PASS
  - 用**被改坏的基线**校验同一文档 → **FAIL 45 项**，逐条给出期望/实测
  - 证明基线真的在生效，不是装饰。

---

## 五、内嵌副本的治理

- **现象**：原独立 skill 与专家团内嵌副本各存一份，改版式规则要动两处，必然漂移。
- **核对**：全目录 grep 原 skill 名 → **专家团内零引用**（确认是自包含复制，不是软链/路径依赖）。
- **结论**：**默认只保留内嵌副本为真相源**。
- **下线操作**（用户级 skill **没有启用开关**，不像插件有 `settings.json > enabledPlugins`）：
  1. 先打包备份：`~/.workbuddy/backups/<name>-v<ver>-offline-backup-<date>.zip`
  2. 再整目录 `mv` 到 `~/.workbuddy/backups/offline-skills/<name>/`
  3. **用 `mv` 不用 `rm`**，可秒恢复；恢复即把目录移回 `~/.workbuddy/skills/`
  4. 下线后**复跑内嵌 skill 的 selftest** 证明能力没被带走
- **证据**：下线后专家团内嵌 skill selftest `10/10 PASS`，环境自检 `status=ready`。

---

## 六、给团队加装"审核"能力（v1.1.0）

新场景：用户**已有**教学文件，要审一致性、必备项目、表格填写完整度。
**不是从零建团**，而是给现有的 `doc-supervisor` 配一把确定性工具 + 给团长加一条分支。

### 6.1 新链路被老规则误阻断（最容易犯的设计错）

- **现象**：团长里"没有课标绝不写教案"这类硬规则，会让"用户拿着已有文件来审核"的请求被拦下。
- **修法**：把依赖链硬规则**显式限定为只约束撰写链路**，审核链路独立成 Workflow B。
- **关键**：判断依据要写成**客观条件**——"**用户手上有没有文件**"，而不是动词（"帮我看看课标对不对" vs "帮我出份课标"，动词相近、场景相反）。

### 6.2 学时勾稽漏报（最严重的一处）

- **现象**：缺陷样本注入了"课标 48 学时 vs 授课计划 64 学时"，审核却报**一致**。
- **根因**：判定逻辑是"课标总学时 ∈ 授课计划的数字集合"，而授课计划里有"讲授 48 / 实验 16"这类**学时分解**，那个 `48` 混进数字池，恰好命中。
- **修法**：改成按表头**定位到具体列**（"本学期计划教学时数 / 总时数"列）再取值。
- **证据**：修复后精确报出 `课标 48（表1 第4行「学时总计」）｜授课计划 64（表1 第2行「本学期计划教学时数」列）`。

> 教训：**数字类勾稽绝不能用"集合命中"**，那是假通过的温床。

### 6.3 表头字间距导致"找不到表"

- **现象**：课程计划模板的表头是「周　次」（中间有全角空格），脚本报"未找到周次表"，但它其实找到了。
- **修法**：关键词匹配前**必须去掉所有空白**。
- **同类**：中文公文模板普遍存在字间距排版（「教 学 内 容」）。

### 6.4 关键词撞车

- **现象**：`实践教学安排表` 被定位成"表1"——因为 `学时分配表` 表头里也有"实践"列。
- **修法**：定位条件收紧到表头组合特征（多个关键词同时命中），而非单关键词。

### 6.5 选填列被当成空缺

- **现象**：合规样本报"空单元格率过高"。
- **根因**：`备注` 列留空被计入空缺统计。
- **修法**：按表头建立**豁免列清单**（备注、说明等），统计前剔除。

### 6.6 字段值比对过严

- **现象**：「嵌入式技术（职业本科）」vs「嵌入式技术」被判为实质不一致。
- **修法**：比对前归一化——去括号补充说明、统一全半角。

### 6.7 新增检查未反向验证

- **做法**：加了"审定日期不得早于编写日期"后，**专门造一个日期倒置的样本**（审定 9/1、编写 9/10）确认会报错。
- **证据**：✅ 命中，报出日期逻辑违规。

---

## 七、方法论沉淀

### 7.1 反向用例是"工具有效"的唯一证明

只跑"正常输入 → PASS"**不能证明任何事**——一个永远返回 PASS 的橡皮图章也能过。必须构造：

| 做坏方式 | 期望 |
|---|---|
| 内置课标模板改成微软雅黑 / 12pt / 清掉首行缩进 | 差异比对报出 **17 项 high**（含最难的缩进项） |
| 用被改坏的基线去校验正常文档 | **FAIL 45 项** |
| 样本注入 6 处已知缺陷（思政表空、学时不符、周次断档、课程名不一致、教学过程空、占位符残留） | 全部命中，退出码非零 |
| 审定日期早于编写日期 | 日期逻辑 ❌ |

### 7.2 最脏的输入也要跑得动

- 直接对**未填写的空白模板**整目录跑审核：不崩，正确报"大量未填"。
- 用**无依赖的解释器**跑脚本：友好报错并指向环境自检，而不是抛裸异常。

### 7.3 结构合规 ≠ 能跑起来

- 平台结构校验（`validate_expert.py`）全绿，只能证明包**格式对**。
- 还要跑：内嵌 skill 的 `selftest`、新增脚本的反向用例、引用完整性扫描、健壮性输入。
- **仍无法验证的**：团长真实编排、跨成员 `SendMessage` 往返——沙箱里跑不出 `TeamCreate`。这类缺口要在交付说明里**主动写出来**，不能因为结构全绿就暗示端到端验证过。

### 7.4 审核类能力的结论分级

| 级别 | 含义 | 处理 |
|---|---|---|
| FAIL | 必须改 | 脚本以非零退出码表达"存在 FAIL" |
| WARN | 建议改 | 报告列出，交责任人判断 |
| UNVERIFIED | 未判定 | **转人工，绝不写成"不合规"** |

- 关键词匹配、启发式结论**必须在使用处自曝**，并要求人工抽 3~5 条回原文复核。
- 审核报告是**建议性证据，不是结论性背书**——报告中写明"送审前仍需责任人确认"。
- 审核成员**只读**：不改输入文件，问题只出报告；返工由主笔做，且**改一次、复检一次**。

## 八、平台 UI 层缺陷（不是包的问题，但会砸在包头上）

### 8.1 本地包一被选进输入框就崩在 `identity.profession?.trim`

**现象**：专家中心点「测试 / 试用」后，会话输入框整块变成红色报错卡片
`输入框遇到错误 / identity.profession?.trim is not a function`，点「重试」反复复现。

**根因（2026-09-21 已彻底定位，此前"包侧无解"的判断是错的）**：chip 的**分支选择**踩到了
"团队 + 主理人有头像"这一组合。

```ts
// .../status-chips/expert-chip/expert-chip.tsx —— 分支在这里被选中
function hasText(value) { return typeof value === "string" && Boolean(value.trim()); }
function resolveExpertChipAvatar(selection) {
  if (selection.expertType === "team" &&
      (hasText(selection.assistantDisplayName) || hasText(selection.assistantProfession) ||
       hasText(selection.assistantAvatarUrl)))          // ← 只可能由 assistantAvatarUrl 命中
    return { avatarUrl: ..., seed: resolveAvatarFallbackSeed({
      id: selection.id,
      name: selection.assistantDisplayName,             // {zh,en} 对象
      profession: selection.assistantProfession }) };   // {zh,en} 对象
  return { avatarUrl: selection.avatarUrl, seed: resolveAvatarFallbackSeed(selection) };  // ← 安全分支
}
// packages/conversation-render/src/shared/get-avatar-fallback-background.ts —— 崩在这里
function resolveAvatarFallbackSeed(identity) {
  const profession = identity.profession?.trim();       // 对对象调 .trim() → TypeError
```

链条：`attachExpertAssistantIdentity()` 经 `toI18nText()` 给主理人挂身份时，**字符串也会被包成
`{zh, en}` 对象**（`assistantDisplayName` / `assistantProfession` 必为对象），而
`assistantAvatarUrl = resolveExpertAvatarUrl(leader.avatar)` **是字符串**。
三个 `hasText` 里只有 avatarUrl 能为真 → 团队分支被选中 → 拿两个对象去 `.trim()`。
`handleExpertTest`（`source: "detail-panel-expert-test"`）把 `...targetExpert` 原样展开成
chip 的 selection，`assistant*` 保持对象、顶层 `name`/`profession` 已被 `i18nToString()` 本地化成
字符串——这也解释了为什么崩在 59177（团队分支）而不是 59246（顶层 profession）。

**修法（包侧，已验证有效）**：**主理人成员（`members[]` 里 `role: "lead"` 的那位）不要配 `avatar`。**

```jsonc
// ✓ 安全：lead 不带头像 → assistantAvatarUrl 整个键不存在 → 三个 hasText 全假 → 走安全分支
"members": [
  { "id": "…-team-lead", "name": {"en":"…","zh":"…"}, "profession": {"en":"…","zh":"…"}, "role": "lead" },
  { "id": "member-a", "name": {…}, "profession": {…}, "avatar": "avatars/member-a.png", "role": "member" }
]
```
其余成员头像、团队卡片 `avatar` 都照常保留。代价仅一项：主理人的**消息头像**退化为首字色块
（花名/职称不受影响，`resolveExpertAssistantIdentity()` 仍会把 `assistantDisplayName` 本地化后显示）。
平台修掉该缺陷后把 `"avatar"` 加回 `members[0]` 即可（图片文件不必删）。

**注意**：只改 `profession` / `name` 是没用的（`toI18n`/`toI18nText` 对字符串同样包对象，改完会崩在
`name?.trim()`）；**逃生口令是"主理人不带头像"**，因为 `hasText` 只认字符串，只有 avatarUrl 这一项
能被字符串命中。

**崩溃的充要条件（三个必须同时成立）**：把两个函数连起来看，触发条件是"形状混合"，不是"专家包写错"：

| # | 条件 | 说明 |
|---|------|------|
| ① | `selection.expertType === "team"` | 只有团队走这条分支 |
| ② | 三个 `assistant*` 里**至少一个是非空字符串** | `assistantDisplayName` / `assistantProfession` 由 `toI18nText()` 产出，**恒为对象** → `hasText` 永假；**唯一能点亮的是 `assistantAvatarUrl`**（来自主理人 `avatar`，是字符串） |
| ③ | `assistantProfession` 是**对象** | 恒成立（`toI18nText()` 产出） |

→ 所以判据可以简化成一句话：**只要 `assistantAvatarUrl` 是个非空字符串，就必然崩**；它不是字符串就一定不崩（`hasText` 全假 → 走安全分支，那里只对已本地化成字符串的顶层 `profession` 调 `.trim()`）。

**为什么必须同时清持久化副本（第一版漏了这一层）**：chip 的 selection 不是只来自 `plugin.json`，而是
"新鲜 DTO ＋ 历史持久化记录"的归并产物，平台里有两处方向相反的归并，**任一处残留旧字符串都会重新点亮 ②**：

```ts
// (a) 展示用叠加：谁有值用谁（current 优先）——旧记录里的字符串会压住新 DTO 的对象
function overlayMissingExpertDisplayFields(current, overlay) {
  return { ...current,
    assistantDisplayName: current.assistantDisplayName || overlay.assistantDisplayName,
    assistantProfession : current.assistantProfession  || overlay.assistantProfession,
    assistantAvatarUrl  : current.assistantAvatarUrl   || overlay.assistantAvatarUrl };
}
// (b) 写回用：把 selection 的 assistant* 原样落盘 —— 内存里有坏字符串就会被写回去
function toRecentExpertRecord(expert, applicationId) {
  return { ..., assistantDisplayName: expert.assistantDisplayName,
                assistantProfession : expert.assistantProfession,
                assistantAvatarUrl  : expert.assistantAvatarUrl };
}
```

**穷举四种归并组合**（说明包侧修好后为什么彻底安全）：

| 组合 | `assistantAvatarUrl` | `assistantProfession` | 结果 |
|------|----------------------|------------------------|------|
| 纯 DTO（lead 无头像） | 缺键 | 对象 | ✅ 不进团队分支 |
| 纯历史记录（旧字符串） | 字符串 | **字符串** | ✅ 进了分支也对字符串调 `.trim()` |
| DTO 在后归并（DTO 覆盖） | 缺键（DTO 没有） | 对象 | ✅ 不进团队分支 |
| 记录在后归并（记录优先） | 字符串 | **字符串** | ✅ 进了分支也安全 |

→ **只有"DTO 自己提供了 `assistantAvatarUrl` 字符串 ＋ 对象形态的 `assistantProfession`"这一种混合才会崩**，
而这正是"主理人配了头像"造成的。去掉主理人头像后，**没有任何归并顺序能凑出 ②＋③ 的混合**。

**修法（动作侧）**：
- 首页已卡死时**先完全退出并重启应用**（内存里的坏引用随之清掉）；重启后请按下节 8.3 确认"新进程真的读到了新文件"；
- 若重启后仍崩，说明旧副本把字符串带回来了，**两个文件都要清**（只清一个不够）：
  1. `~/.workbuddy/storage/device/scoped/<scope>/newTaskExpert.json`（首页输入框恢复用的专家快照）；
  2. `~/.workbuddy/storage/user-<uid>-personal/global/expert.json` 的 `recents[]`（最近使用列表，**最容易漏**，因为它是 4MB 级的单文件）；
  每处只摘掉该专家记录的 `assistantAvatarUrl` 与 `members[lead].avatar`，**不要整文件清空**（写 `{}` 会连"已选专家"和最近列表一起丢）。已备好一键脚本：本 skill 场景下的
  `_diag/clean_expert_chip_state.py`（默认预演，`--apply` 才写入且自动备份、写后复检）。

**影响面判定**：`logs/renderer.old.log` 里历史出现的专家全是云端专家（`DeepResearchExpert`/`KiddContentExpert`/`ex_…`），**0 次同类崩溃**；换成本地专家立刻复现 → 可判定与"是否 team 类型""members 是否写错"无关，纯属平台缺陷。

**证据（两次排查）**：
- 2026-09-17（首次，WorkBuddy Desktop 5.5.6）`~/.workbuddy/logs/renderer.log:14333` 完整栈：
  `resolveAvatarFallbackSeed:54995 ← resolveExpertChipAvatar:59177 ← ExpertChip:59249 ← StatusChipsImpl ← InputToolbarImpl ← HomeInput`；
- 2026-09-21 复现同一报错，并用**保真复现脚本**（下节）钉死分支条件，四个场景全部对得上：
  ① 现行包 + 试用路径 = `TypeError: identity.profession?.trim is not a function`（与用户截图逐字一致）；
  ② 去掉 lead 头像 + 试用路径 = 渲染成功；③ 落盘恢复路径 = 本来就不崩（对照组）；
  ④ 修复后落盘恢复路径 = 仍不崩（防回归）。

### 8.2 验证"平台缺陷的包侧规避"要用保真复现，不要靠推理

**现象**：判断"这个改法到底能不能绕开平台 bug"时，很容易在推理里绕圈
（改 A 崩 B、改 B 崩 C），得出"无解"的过度结论（8.1 第一版就是如此）。

**修法**：把平台源码**逐字抄**进一个最小 Node 脚本，只替换掉无关的 IO 函数，然后喂真实数据跑。

1. 从 `app.asar` 按字节偏移取出涉及的函数原文（`grep -a -o -b "<函数名>" app.asar` + Python 切片）；
2. 抄进 `.js`，逐字保留（含 `?.`、`typeof` 判定、三分支顺序），只 stub 掉拼 URL / 读文件这类函数；
3. 数据用**真实来源**：直接 readFile 平台的 `plugin.json` 与落盘快照 `newTaskExpert.json`，
   而不是手搓一个"理想形状"；
4. 设计四类场景：**改前（复现）／改后（生效）／未改动路径（对照组，必须仍 OK）／改后未改动路径（防回归）**；
5. 退出码 0/1 表达结论，让"修法有效"成为可复跑的断言而不是说法。

**收益**：这是唯一能在"改不了平台二进制"的前提下，对规避方案给出硬证据的办法；
本次 4 个场景一次跑通，才敢把 README 里"不要用测试按钮"改成"✅ 可用（v1.1.2 起）"。

**排查方法论（可复用）**：遇到渲染层 `xxx is not a function`，不要靠猜——
1. `grep -n "is not a function" ~/.workbuddy/logs/renderer.log` 拿完整栈与组件栈；
2. 栈里给出的是 `<asset>.js:<行>`，对 `app.asar` 用
   `grep -a -o -b "<函数名>" app.asar` 拿字节偏移，再用 Python 按偏移把这几十 KB 源码读出来（asar 内是未压缩源码，含内嵌 sourcemap 注释，能看到原始 TS 路径）；
3. 顺着调用链反查入参对象的**真实形状**（读平台自己的 DTO 构建代码 + 读落盘快照文件），而不是推测。

### 8.3 「改了文件」≠「已修复」——先证伪"应用真的重载了吗"

**现象**：改完 `plugin.json` 并清完落盘副本后，用户再贴一次同样的报错。第一反应是"我的修法又错了"，
于是推翻自己重查一遍因果链——**但如果应用根本没重启，改的文件从未被读取，重查就是白干。**

**判据（两条命令，10 秒出结论）**：
```bash
# ① 崩溃时间戳 vs 修改时间戳：报错发生在修改之前，还是之后？
python -c "import json,glob;[print(json.loads(l)['timestamp']) for p in glob.glob(r'~/.workbuddy/logs/renderer*.log') for l in open(p,encoding='utf-8',errors='ignore') if 'identity.profession?.trim is not a function' in l]"
# ② 进程龄：uptimeSec 是把"日志文件在动"与"进程重启过"区分开的唯一硬证据
grep -o 'uptimeSec=[0-9]*' ~/.workbuddy/logs/AppStartup.log | tail -1
```
本次实测：崩溃只有 `12:17:53Z`、`12:18:24Z` 两次（= 本地 20:17/20:18），而所有修改都发生在其后；
`AppStartup.log` 最后一条 `uptimeSec=1715` 且 `renderer.log` 仍在实时追加 → **进程从未重启**，
`[DocumentSelectionHook] ... step=reset_for_session_change` 只是切换会话，**不是重启**。
结论：报错是修复前那一次的残留显示，不是新的失败。

**为什么容易误判**：日志文件 mtime 一直在更新（渲染层持续写日志），看起来"应用很新鲜"；
`logs/<date>/` 目录、会话切换、`[home-wrapper-reset]` 之类的日志都发生在**同一个进程内**。
只有 `uptimeSec`（或 `installer.log`/进程启动时间）能证明重启。

**动作**：向用户要一次「完全退出 + 重启」再验收；在重启完成前，**不要**基于"仍报错"去改第二版方案。
若重启后 `renderer.log` 出现**新的**崩溃时间戳，才说明修法不足，此时再进 8.2 的保真复现流程。

### 8.4 改的是"源目录"，跑的却是"安装快照"（排查平台类问题最贵的一个坑）

**现象**：改完 `plugins/marketplaces/my-experts/plugins/<pkg>/` 的 `plugin.json`、跑过 `validate_expert`
与 `register_expert`、版本号也涨了，用户重启后**仍报一模一样的错**。此时很容易怀疑"修法本身是错的"，
于是把已经正确的因果链推翻重查一遍——白花几十分钟。

**真相**：平台插件目录是**两层**（源码注释原文）：

```
plugins/marketplaces/<marketplace>             ← 可更新的 marketplace source（你编辑的地方）
plugins/cache/<marketplace>/<plugin>/<ver>/    ← 不可变安装快照（运行时实际加载的地方）
daemon 托管的 plugin 只能从 installed_plugins.json 记录的安装快照加载
```

- `~/.workbuddy/plugins/installed_plugins.json` → `plugins["<id>@<marketplace>"][0].installPath`
  指向的才是运行时目录；
- `register_expert.py` **只写 `marketplace.json`**，完全不碰缓存快照与安装记录
  → "注册成功 ≠ 运行时生效"；
- `.in_use/<pid>` 里的 `procStart` 能把"哪个进程在何时加载了这份快照"钉死。

**本次铁证**：
- `installed_plugins.json` → `installPath = …\plugins\cache\my-experts\suit-sz-teaching-team\1.1.1`；
- `.in_use/29172` → `procStart = 2026-09-21T12:18:03.538Z`，与崩溃时刻 `12:17:53Z / 12:18:24Z` 咬合；
- 两棵树哈希比对：37 vs 38 个文件，**只有 `plugin.json` / `README.md` / `settings.json` 三个不同**，
  而旧快照的 `plugin.json` 里 `members[0]` 仍带 `avatar` → 它必然复现崩溃；
- 把旧快照喂进 §8.2 的保真复现脚本：**场景1 = crash**（逐字复现用户报错）；
  同步修好后同一脚本对**快照**与**源目录**跑，均 4/4 通过、退出码 0。

**修法**：
1. 整目录备份快照（`.in_use` 可跳过）→ 覆盖差异文件；
2. 快照内 `plugin.json` 的 `version` 与**目录名 / `installed_plugins.json` 的 `version`** 三者保持一致，
   不要出现"路径写着 1.1.1、文件写着 1.1.2"的自相矛盾；
3. 或让应用走一次正式 install/update 重建快照；
4. 复检：源目录与快照的 `members[lead]` 都不得带 `avatar`。

**通用教训（可迁移到 skill / MCP / 任何带缓存层的平台）**：
定位到"文件写对了"只是**中点**，必须再确认**运行时读的是不是这个文件**。
判据优先级：**安装记录（`installed_plugins.json`） → 进程加载标记（`.in_use/<pid>` 的 `procStart`）→ 文件内容哈希比对**。
凡是"改了没用、且日志看不到新失败"的情况，先查这一层，再怀疑修法。

