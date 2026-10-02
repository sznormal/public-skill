---
name: skill-to-expert-team
version: 1.4.0
display_name: Skill 改造成专家团
display_name_en: Convert a Skill into an Expert Team
category: engineering
author: Norma
agent_created: true
license: MIT
description: 把一个已有的 WorkBuddy skill 改造为多角色协作的专家团（expertType=team）：先核对三处信息源（官方规范 / expert-manager 内置 references / 现网同类包惯例）再动手，设计只做编排的团长、按分析域拆分成员、把原 skill 整份内嵌为共享工具箱、生成并压缩头像、校验注册打包；也覆盖「专家团已上线后追加一类新职责」的扩装路径。含并发编辑覆盖、members 字段名、头像压缩与 AI 水印、运行环境 PATH、静态扫描高危模式、审核类误报调试等实战坑位。当用户要求"把某个 skill 改成专家团""这个技能应该多角色协作""skill 转专家团""给这个专家团再加个审校能力"时使用。
description_zh: 把已有 WorkBuddy skill 改造为多角色协作专家团：先核对三处信息源再动手，团长只编排、成员按域拆分、原 skill 内嵌为共享工具箱，并完成校验注册打包；含上线后扩装新能力的路径与实战坑位。
description_en: Convert an existing WorkBuddy skill into a multi-role expert team (expertType=team) - verify three information sources first, then an orchestrator-only lead, members split by analysis domain, the original skill embedded as a shared toolkit, plus validation, registration, packaging, and the path for adding a new capability to a live team.
---

# Skill 改造成专家团

适用于：用户已有一个能用的 skill，现在要求把它变成**多角色协作的专家团**。

> 从零创建专家团请直接用内置 skill `expert-manager`（场景 A 交互模式）。本 skill 只补它没覆盖的「已有 skill → 专家团」改造路径，以及「团队上线后扩装」路径。

## 〇、开工前：三处信息源 + 运行环境

**不要凭记忆写专家包**。花 20 分钟读完这三处，能省掉后续大量返工：

| 信息源 | 位置 | 拿到什么 |
|---|---|---|
| ① 官方规范 | `open.workbuddy.cn/docs/expert-team` | 基础结构、members 语义、团长职责 |
| ② expert-manager 内置规范 | `workbuddy-builtin/skills/expert-manager/references/`：`team-spec.md`、`plugin-json-spec.md`、`agent-md-spec.md`、`avatar-spec.md` | 字段级硬约束（比官网更细，是校验器的判据来源） |
| ③ 现网同类包惯例 | `~/.workbuddy/plugins/marketplaces/experts/plugins/*/.codebuddy-plugin/plugin.json` | 真实在跑的 team 包怎么填（如 `members[]` 用 `name` 还是 `displayName`） |

**抢先读校验器源码**：`expert-manager/scripts/validate_expert.py`。它把硬约束写死在代码里（tags 恰好 3 个、profession 必须等于 displayName、displayDescription.zh 字数区间…）。**先读它再写文件**，比写完跑一遍再改快得多。

### 运行环境（Windows / 沙箱）

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32"   # 不先设，find/head/grep 全部不可用
```

**Python 解释器是分层的**——这是最容易让"验证通过"变成假象的地方：

- 受管解释器（`~/.workbuddy/binaries/python/versions/*`）：干净，**通常没有 python-docx**
- 项目 venv（`~/.workbuddy/binaries/python/envs/default`）：装过依赖，**跑脚本用这个**
- 内嵌 skill 的 `check_environment.py` **不能只看 `sys.executable`**，必须主动发现带依赖的解释器（否则会把能力误判为不可用，降级路径被错误触发）

## 一、先判断该不该拆

改造前先回答：**拆出来的每个成员，有没有用户会直接问它的问题？**（这是"能独立成 agent"的唯一标准）

- 有 → 独立成 agent
- 没有 → 归入相邻成员，不要为拆而拆

典型拆分维度是**流程阶段**（提取 → 撰写 A → 撰写 B → 校验），因为阶段之间有真实的数据依赖，天然是独立职责边界。

**必问用户的三个决策点**（问一次即可，别来回问）：
1. 成员构成（用户列的成员之外，是否保留原 skill 的某个能力作为独立角色）
2. 署名（校内资产 / 个人 IP，两者署名不同）
3. 团队与成员的命名偏好（不给就用谐音花名，见第三节）

## 二、标准改造流程

```
0. 核对三处信息源 + 读校验器源码 + 修 PATH
1. init_expert.py 初始化 team 型骨架
2. 清理 init 占位文件 → 写 N 个 agents/*.md
3. 写 plugin.json（含 teamInfo / members / 展示字段）
4. 写 settings.json（agent = agentName）
5. 原 skill 整份复制进 skills/<name>/，按团队视角重写其 SKILL.md
6. 补齐成员真正需要的脚本（原 skill 缺的能力在这里补）
7. 生成 N+1 张头像并压到 512×512 / ≤500KB
8. 写 README.md
9. validate → register → package
```

初始化命令（专家**必须**生成在该目录，否则平台检测不到）：

```bash
python init_expert.py <name> --type team \
  --path "$WORKBUDDY_CONFIG_DIR/plugins/marketplaces/my-experts/plugins"
```

脚本位置：`workbuddy-builtin/skills/expert-manager/scripts/`

## 三、成员与团长设计

### 命名（team-spec 要求）
- 每成员三字花名，**像人名**，谐音或拆字暗含职能，但**不与 profession 重复**，中英文都自然
- 禁止：叠字谐音（领码码）、单字名、纯职能词、张三/John Doe
- 主理人 `profession` **不能用通用 title**（团长 / Team Lead），要体现业务定位，如"教学文件总编""交付总监"
- **英文 name 用拼音姓氏**（Wen Siqi / Fan Shizhen），不要用 Agent ID

### 团长 prompt 的写法
团长是**编排器**，正文里必须写清三件事：

1. **它不做什么**——"你自己不撰写任何教学文件正文"，并把每个专业产出点名列出
2. **SOP 分 Phase**——每 Phase 写：调谁、输入从哪来、产出是什么
3. **依赖链与阻断规则**——哪个阶段缺前置必须停下并转回，而不是"顺手编一个顶上"

必须包含（平台规范要求）：
- **4 条协作铁律**：TeamCreate → 调度成员 → 消息中转 → 成员结论为准
- **5 条严禁行为**：跳过 TeamCreate / 代写成员产出 / 跳阶段 / 成员直连 / spawn 自己
- **单 Agent 直调路由表**：什么问法直接调谁
- **成员能力速查**：Agent ID + 擅长点 + 典型问法
- **确认门不可代签**：需要真实用户答复的环节（如头部信息栏、范围确认），团长只中转，不得自行假定

### 成员的 Prompt 必备结构
1. 角色定义（一句话：你是谁）
2. 硬性前置条件（有的话写在最前面，如"没有 X 绝不作业"）
3. 核心能力 3–5 点
4. 工作流程（分 Step，含确认门位置）
5. 输出规范（产物文件名、格式来源）
6. **SendMessage 回传要求**——必须给出**模板化回传格式**，并明令禁止只回传状态句

## 四、plugin.json 关键字段

| 字段 | 要点 |
|---|---|
| `expertType` | `"team"` |
| `agentName` | 主理人 ID，**必须有业务语义**，不能是 `team-lead` |
| `teamInfo` | `{leadAgent, memberAgents}`，**memberAgents 不含主理人** |
| `members` | **含主理人**，role=`lead`；成员用 `name` 字段（**不是** init 模板里的 `displayName`） |
| `profession` | Team 型**必须与 displayName 完全一致**（校验器会报错） |
| `tags` / `quickPrompts` | **各恰好 3 个**，多一个少一个都报错 |
| `defaultInitPrompt` | 必须与 `quickPrompts[0]` 一致 |
| `displayDescription.zh` | **40–50 字**（中文按字符数计，标点也算） |
| `categoryId` | 按**主要输出物**和**服务对象**选，不按直觉 |
| `skills` | `["./skills/<name>"]`，指向内嵌工具箱 |

`settings.json`：`{"agent": "<agentName>"}`，值必须与 plugin.json 的 agentName 一致。

主理人 MD 文件名必须带团队前缀，**不可用通用 `team-lead.md`**。

**agents/*.md 的 frontmatter 禁止 `tools` 字段**（工具权限由系统分配）。

**追加成员时三处同步**：`agents/` 新增文件 + `members[]` 增条目 + `teamInfo.memberAgents` 增 ID，少一处则成员不可见或路由失败。

## 五、原 skill 内嵌为共享工具箱

- 整份复制到 `skills/<name>/`（排除 `__pycache__`、`*.pyc`）
- **重写内嵌 SKILL.md**：不要沿用原 skill 的"按意图路由"（那是给单 agent 的）。改成**团队工具箱手册**——「谁用哪一部分」的映射表 + 脚本清单 + 参考文件清单 + 降级策略 + 铁律
- 内嵌 SKILL.md 的 `name` 必须与目录名一致
- 成员的 MD 里写清"读哪份 reference、跑哪个脚本"，避免成员迷路

**改造时的实质增量往往在这里**：借"拆角色"的机会把原 skill 缺的能力补成确定性脚本。例如新增一个"提取"脚本把原本靠模型临场判断的步骤变成可复跑、可反证的工具。

## 六、头像生成

```python
# ImageGen: size="1024x1024", output_dir=avatars/
```

- 同一团队**风格锚定**：每个 prompt 用相同前缀与后缀；背景色调按 categoryId 映射
- prompt 必须**从对应 MD 描述中提取角色特征**，不要用通用模板
- 生成后**必须压缩**：原图约 1–1.8MB，远超 500KB 上限
  1. resize 到 512×512（LANCZOS）
  2. 存 PNG `optimize=True`
  3. 仍 >500KB 才降级 JPEG（`quality=88, progressive=True`）
- 生成的文件名是 prompt 派生的长名，**需重命名为 plugin.json 里声明的名字**
- 删掉 `avatars/.gitkeep`

**生成图右下角通常带 "AI 生成" 水印，无法通过参数去除**——这是平台策略，不要反复重试参数。交付时**主动告知用户**：如需无水印，请自行替换 `avatars/` 下的文件（512×512、PNG/JPG、≤500KB）。

## 七、实战坑位清单

| 坑 | 后果 | 对策 |
|---|---|---|
| **同一文件的两个 Edit 放同一消息并发** | 后写覆盖先写，**首次修改被静默吞掉** | 同文件的多次编辑**串行**；改完用 `grep -c` 数关键词出现次数核对 |
| `members[]` 用 `displayName` | 与现网 team 包惯例不符 | 用 `name`（可查现网包：`~/.workbuddy/plugins/marketplaces/experts/plugins/*/.codebuddy-plugin/plugin.json`） |
| 头像直接放原图 | 超 500KB 上限 | 见第六节压缩 |
| 默认期望字典缺字体族归一字段 | 同族字体（仿宋 vs 仿宋_GB2312）误报一片 | 比对时用 `want_family = exp.get("font_family") or font_family(want_font)` |
| 角色格式按「整条记录取众数」聚合 | 离群段污染整类（表标题混进正文 → 正文被读成"居中顶格"） | **逐维度取众数**，并输出 confidence |
| 内嵌 skill 后忘了同步 | 两份副本各自漂移 | **默认只保留内嵌副本为真相源**：原独立 skill 先打包备份，再整目录移出 `~/.workbuddy/skills/`。用户级 skill **没有启用开关**（不像插件有 `settings.json > enabledPlugins`），生效与否只取决于目录是否存在，所以"下线"= 移出该目录，用 `mv` 不用删，可秒恢复 |
| 改了内嵌脚本的公开行为 | 原 skill 的 selftest 回归失败 | 每次改脚本后**先跑 selftest 回归**，再继续 |
| 脚本里出现 `obj.remove(x)` / `del ...copy` 之类写法 | 平台**静态安全扫描误判为文件删除高危**，`preflight` 直接 blocked | 改用不会命中删除模式等价写法；**改完必须重跑 `preflight` 确认 high=0**（medium=写文件属必要行为，可接受） |
| 只看结构合规就交付 | 结构全绿但团队跑不起来 | 见第八节：结构校验之外还要跑内嵌脚本自测与反向用例 |
| 专家团主理人（`role: "lead"`）配了 `avatar` | 走「测试 / 试用」时输入框整块崩成 `identity.profession?.trim is not a function` | **主理人不要配头像**即可绕开（其余成员头像照留），见第十一节 |

> 详细的现象 / 根因 / 修法 / 证据记录见 `references/pitfalls.md`。

## 八、交付前的验收清单

```
1. validate_expert.py <dir>        → 0 error（warning 也要清掉）
2. register_expert.py <dir>        → 写入 marketplace.json（回读确认条目在）
3. 内嵌 skill 的 selftest           → 全 PASS（回归）
4. 新增脚本的反向用例               → 故意做坏输入，确认脚本能抓到（不是橡皮图章）
5. 引用完整性扫描                    → agents/ 与 skill 里提到的每个文件都真实存在
6. 残留扫描                         → 无未完成标记、无失效路径（原 skill 的旧目录名等）
7. 健壮性                           → 喂最脏的真实输入（如未填写的空白模板）不崩
8. package_expert.py <dir> <out>   → 产出 zip，列出文件数确认无遗漏
```

**第 4 条最容易被跳过，也最重要**：只跑"正常输入 → PASS"不能证明工具有效，必须构造"坏输入 → 应该报错"的用例。

**注意验收工具是分层的**：
- **skill 层**（含内嵌 skill 的脚本质量）→ `skill-crafting/scripts/skill_ops.py validate|preflight`
- **专家包层**（结构、字段、头像规格）→ `expert-manager/scripts/validate_expert.py`
- 两层都要过，别只跑一层就宣布完成。

## 九、交付话术要点

- 列出团队结构表（Agent ID / 花名 / 职业头衔 / 关键约束）
- 说明**本次相对原 skill 的实质增量**，而不是只罗列文件
- 给出可复现的验收证据（校验输出、selftest 结果、反向用例结果）
- 如实说明未验证的部分（未实测的平台、未覆盖的场景）
- 提醒头像可手动替换（512×512，PNG/JPG，≤500KB），并说明 AI 水印情况
- **给出口入口径 + 主理人无头像这条规约**：三个入口现在都可用；但要主动告诉用户"主理人为什么不带头像"，否则对方会以为是漏配而"补回去"，一补就复崩（原因见第十一节）

**"如实说明"是硬要求**：专家团的**团长真实编排、跨成员消息往返无法在沙箱内实测**（沙箱里跑不出 TeamCreate）。这类结构性缺口必须主动写出来，不能因为"结构校验全绿"就暗示已经端到端验证过。

## 十、给已有专家团后加能力（团队已上线，要新增一类职责）

触发：用户说"这个专家团还得能审 / 能查 / 能算 XX"，而不是"从零建团"。**不要重建团队**，在既有结构上扩。

```
1. 先读现状：agents/ 下各成员定义 + 内嵌 skill 的 SKILL.md + 内嵌 skill 工作流参考文档
   —— 确认现有成员覆盖到哪里、缺的是什么（往往 prompt 已写但缺确定性工具）
2. 判断是"新成员"还是"现有成员的新能力"
   — 有独立提问入口 → 新成员（plugin.json 的 agents / members / teamInfo 三处同步 + 一张头像）
   — 只是让现有成员更强 → 只改那个成员 + 补脚本
3. 把能力落成确定性脚本（不要只写进 prompt）
4. 给脚本造"合规样本 + 注入缺陷样本"，写进 selftest 做反向用例
5. 成员 MD 里把"临场写代码"改成"调脚本"，写清各结论级别的处理方式
6. 新能力若对应新场景 → 团长 SOP 加一条工作流分支 + 客观判断依据
7. 同步更新：README / plugin.json（description、tags、quickPrompts、version）/ skill-dependencies.json
8. validate → register → package（版本号 +0.1）
```

**关键经验**：

- **判断依据要写成客观条件，不是动词**。区分"撰写"与"审核"应依据"**用户手上有没有文件**"——"帮我看看课标对不对"（有文件）与"帮我出份课标"（没文件）动词相近、场景相反。
- **新能力不能被老规则误阻断**。加了审核链路后，必须回头把团长里"没有 X 不写 Y"这类硬规则**限定为只约束撰写链路**，否则用户拿着已有文件会被拦下来。
- **审核类能力保留三级别结论**：FAIL（必须改）/ WARN（建议改）/ UNVERIFIED（未判定转人工）。**"没查成"绝不能写成"不合规"**。脚本用**非零退出码**表达"存在 FAIL"，便于上层流程直接消费。
- **只读纪律写进成员 prompt**：审核成员不得改输入文件，问题只出报告；返工由主笔做，且**改一次、复检一次**。
- **启发式结论必须自曝**：凡关键词匹配、数字集合命中得出的结论，在使用处标"启发式"，并要求人工抽 3~5 条回原文复核。
- **教学/公文类文档普遍用字间距排版**（「周　次」「教 学 内 容」），关键词匹配前**必须去掉空白**，否则"找不到"的误报会直接进用户报告。
- **数字类勾稽别用"数字集合命中"**：集合命中会把同表里的其他数字（如某列写着"讲授48/实验16"里的 48）当成目标值，造成**漏报**。应按表头**定位到具体列**再取值。
- **关键词定位表格要防撞车**：同一份文档里"实践教学安排表"与"学时分配表（含实践列）"会互相命中，定位条件要收紧到表头组合特征。
- **选填列不算空缺**：备注、说明类列留空是正常的，统计空单元格率前要按表头豁免，否则误报一片"表格未填完整"。
- **字段值比对要容忍补充说明**：「嵌入式技术（职业本科）」vs「嵌入式技术」不是实质不一致，比对前做归一化（去括号补充、统一全半角）。
- **新增检查本身也要反向验证**：加了"审定日期不得早于编写日期"后，要**造一个日期倒置的样本**确认真的会报错。
- **审核报告是建议性证据，不是结论性背书**：报告中要写明"送审前仍需责任人确认"。

## 十一、已知平台缺陷：本地包被选进输入框时 chip 崩溃（交付必读）

**现象**：专家中心点「测试 / 试用」→ 会话输入框整块变成红色报错卡片
`输入框遇到错误 / identity.profession?.trim is not a function`，点「重试」无效。

**根因（平台侧缺陷 + 包侧可规避，2026-09-21 定论）**：
- `toI18nText()` 会把**字符串也包成 `{zh, en}` 对象**（`toI18n()` 同理），所以主理人挂上来的
  `assistantDisplayName` / `assistantProfession` 必为对象；只有
  `assistantAvatarUrl = resolveExpertAvatarUrl(leader.avatar)` **是字符串**。
- chip 的 `resolveExpertChipAvatar()` 三分支判定里，`hasText()` **只认字符串** →
  三个字段中只有 `assistantAvatarUrl` 能为真 → **团队分支被 avatarUrl 单独触发** →
  转头拿两个**对象**去 `resolveAvatarFallbackSeed()` 里 `.trim()` → `TypeError`。
- 这也解释了为何崩在团队分支（59177）而不是顶层 `profession`（59246）：顶层字段已被本地化成字符串。

**包侧规避（已实测有效，写进包规约）**：
> **`members[]` 中 `role: "lead"` 的主理人成员，不要配 `avatar`。**

主理人无头像 → `resolveExpertAvatarUrl(undefined)` → `assistantAvatarUrl` 整个键**不存在** →
三个 `hasText` 全假 → chip 退回安全分支，用顶层**已本地化的字符串** `profession` 取色。
其余成员头像、团队卡片 `avatar` 全部保留；代价仅"主理人消息头像退化为首字色块"。
**注意只改 `profession` / `name` 无用**（字符串同样被 `toI18n` 包成对象，会继续崩在 `name?.trim()`）——
逃生口令是"主理人不带头像"，别改错字段。

**交付/验收动作**：
- 三个入口（新建任务 `+` → 专家 / 专家中心「开始对话」/ 专家中心「测试」）现在都可以用；
  改了 `members` 结构后**务必至少走一遍「测试」按钮**——它是唯一会暴露此类 chip 缺陷的入口；
- 若首页已卡在报错卡片：**先完全退出并重启应用**（`[DocumentSelectionHook] step=reset_for_session_change`
  只是切会话，**不是重启**；用 `AppStartup.log` 的 `uptimeSec` 确认）；
- 重启后仍崩，说明还有旧副本带回了坏字符串——**两处状态 + 一处包体**都要查：
  ① `storage/device/scoped/<scope>/newTaskExpert.json`；② `storage/user-<uid>-personal/global/expert.json`
  的 `recents[]`（4MB 级单文件，最易漏）；③ **`plugins/cache/<marketplace>/<plugin>/<version>/` 安装快照**（见下）。
  已备一键脚本 `_diag/clean_expert_chip_state.py`（默认预演，`--apply` 才写且自动备份+复检）；
- 判断"包侧能否规避"**不要靠推理**：把平台源码逐字抄进最小 Node 脚本、喂真实 plugin.json 与落盘快照，
  跑"正向现行文件必须 ok／反向人为还原触发条件必须崩"的**双向断言**，见 `references/pitfalls.md` §8.2。

### 11.1 致命误区：改的是"源目录"，跑的却是"安装快照"

**现象**：改完 `plugins/marketplaces/my-experts/plugins/<pkg>/` 并重新注册打包（版本号也涨了），
用户仍报**完全一样**的错——因为运行时根本没用这份文件。

**真相**：平台插件目录分两层（官方源码注释原文）：

```
plugins/marketplaces/<marketplace>            ← 可更新的 marketplace source（你编辑的地方）
plugins/cache/<marketplace>/<plugin>/<ver>/   ← 不可变安装快照（运行时实际加载的地方）
daemon 托管的 plugin 只能从 installed_plugins.json 记录的安装快照加载
```

`~/.workbuddy/plugins/installed_plugins.json` 是**唯一真相源**：

```json
"plugins": { "suit-sz-teaching-team@my-experts": [ {
  "installPath": "<USER_HOME>\\.workbuddy\\plugins\\cache\\my-experts\\suit-sz-teaching-team\\1.1.1",
  "version": "1.1.1", "installedAt": "…", "lastUpdated": "…" } ] }
```

**三件套判据（10 秒确认真相源）**：
1. `installed_plugins.json` → `installPath`：运行时读哪个目录；
2. `.in_use/<pid>` 的 `procStart`：**哪个进程**在什么时候加载了这份快照
   （本次 `procStart=2026-09-21T12:18:03Z` 与崩溃时刻 `12:17:53/12:18:24Z` 完全咬合 → 铁证）；
3. 两棵树的哈希比对：本次只差 `plugin.json` / `README.md` / `settings.json` 三个文件，
   而旧快照的 `plugin.json` 里 `members[0]` **仍带 avatar**。

**修法**：把快照同步为已修版本（先整目录备份 → 覆盖差异文件 → `plugin.json` 的 `version`
保持与**目录名 / `installed_plugins.json`** 一致，避免自相矛盾），或让应用走一次正式 install/update 重建快照。
注意 `expert-manager/scripts/register_expert.py` **只写 marketplace.json，完全不碰缓存快照与安装记录**
——"注册成功 ≠ 运行时生效"。

**通用教训**：在带缓存/快照层的平台里，定位到"文件写对了"只是中点；
必须再确认"**运行时读的是不是这个文件**"。判据优先级：安装记录 → 进程加载标记 → 文件内容。
同类场景（skill、MCP、插件）一律先查这一层，别在源目录上反复改。


**报告平台时的最小修法**：`resolveAvatarFallbackSeed` 内加 `typeof === "string"` 判定，或让 chip 入口统一走 `localizedExpertText()`；顺带对齐 `handleExpertTest`（detail-panel-expert-test）与 summon 链路的数据形状（前者 `...targetExpert` 原样展开，`assistant*` 保持对象）。
