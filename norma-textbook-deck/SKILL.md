---
name: norma-textbook-deck
description: >
  把教材（Markdown）某一章稳定复现地做成教学课件：飞书在线幻灯片 + 导出的 .pptx + 章节代码外置 txt。
  固化「Python 机器人基础编程」课程课件的风格规律与制作流程——先反推既有 PPT 的抽取规律，
  再规划大纲、逐页闭环、三重验收、搜图配图。默认「科技深蓝风」，可按主题切换教室浅底/自然绿。
  硬性要求：一页一点、尽量用流程/图示/表格/对比呈现、PPT 正文不贴代码、代码单独抽成 txt、配图只搜不生成。
  符合 AFP-SPEC Bronze 合规。
  【触发词覆盖】：把第X章做PPT / 教材转课件 / 教材做幻灯片 / 这一章做成课件 /
                科技风课件 / 深蓝课件 / 浅色课件 / 代码别贴在PPT里 /
                Python机器人基础编程 课件 / 智能机器人编程 课件 / 帮教材生成 PPT /
                把教材某章生成幻灯片 / 章节课件模板
  【触发隔离】：只处理「教材 Markdown → 教学课件（PPT/幻灯片）」这一单点任务。
              用户要做的是普通商业演示、汇报 PPT、数据看板、产品发布 deck 时，本 skill 不触发——
              那些走通用 ppt 制作能力。用户只想要教案 / 课程标准 / 习题 / 试卷等教学文书时，
              本 skill 也不触发（那走教学文书类 skill）。用户还在挑选/比较不同 PPT 工具时，
              本 skill 不触发。
  【触发冲突预检】：与本机 `dashi-ppt-cn`（教材章节 → 可编辑 PPTX）触发词存在部分重叠。
              分工规则——**产出飞书在线幻灯片 + 深蓝教学风 + 代码外置三件套 → 本 skill**；
              **产出纯本地可编辑 PPTX（dashi 引擎、theme09）→ dashi-ppt-cn**。
              用户明确点名 dashi / 可编辑 pptx 时，让位给 dashi-ppt-cn。
              与前身 `textbook-deck-dark-blue` 为同一课程体系的新旧两版，本 skill 为 AFP 化正式版。
version: 1.0.0
agent_created: true
partner: norma
skill_type: independent
afp_spec_target: bronze
---

# norma-textbook-deck · 教材 → 教学课件（可复现版）

把一章 Markdown 教材做成 20–30 页、可直接上课的飞书幻灯片，并导出 pptx 与代码 txt。
**本 skill 是 `textbook-deck-dark-blue` 的 AFP 化正式版**，把「Python 机器人基础编程」课程课件的风格规律与制作流程固化为可复用资产。

## 一、核心设计理念

1. **先反推规律，再动手**——不凭感觉排版。先解析既有同级 PPT，归纳"抽哪些点、怎么排"的规律（`modules/extraction-rules.md`），新章照此复刻，风格天然一致。
2. **落盘思维**——每一页、每一份计划、每一次验收都要落成具名文件。判据：换个全新对话，只凭 `chN_ppt/` 里的文件能不能接着干。
3. **逐页闭环，禁止攒批**——写一页 → lint 到 0 错 → 立即提交 → 记 slide_id。攒批会一次报一堆错、难定位。
4. **代码零外贴**——PPT 正文一个字符都不贴整段代码，只画它的"语义角色"；代码抽到 `<章名>_实例代码.txt`。
5. **搜图不生成**——配图一律用网络搜索找现成实拍图，**禁止 AI 生图**；找不到就回退纯图形绘制。

## 二、全局状态管理（HUD）

每章开工时在 `chN_ppt/.lark-slides/plan/chN/` 落盘 `deck-state.json`：

```json
{
  "meta": { "chapter": "第N章", "chapter_title": "", "source_md": "", "current_stage": "P1", "scheme": "tech_dark_blue" },
  "deck": { "xml_presentation_id": "", "url": "", "planned_pages": 0, "submitted_pages": 0, "revision_id": 0 },
  "artifacts": { "plan_json": "", "code_txt": "", "slides_dir": "chN_ppt/", "images": [] },
  "stages": { "P1_source": false, "P2_outline": false, "P3_pages": [], "P4_acceptance": false },
  "history": { "completed": [], "pending": [] }
}
```

## 三、阶段路由表

| 阶段 | 名称 | 加载文档 | 硬停输出 |
|---|---|---|---|
| **P1** | 读源文 + 抽代码 + 反推规律 | `stages/p1-source-extraction.md` | 源文清单 + 代码 txt + 规律确认单 |
| **P2** | 定页面大纲 + 建空白 deck | `stages/p2-outline-planning.md` | `slide_plan.json` + 在线空白 deck + 开工通知 |
| **P3** | 逐页闭环（write/lint/submit） | `stages/p3-page-closure.md` | 每页 slide-NN.xml + slide_id |
| **P4** | 三重验收 + 导出 + 交付 | `stages/p4-acceptance-delivery.md` | pptx + 代码 txt + 在线链接 + 验收单 |

**起始动作**：识别到触发词后 → Read `stages/p1-source-extraction.md`，同时 Read `modules/extraction-rules.md`。
**新指令/改稿**：回到「阶段路由表」重新定位当前阶段。

## 四、按需模块（Read on demand）

| 用户说 / 场景 | 加载文档 |
|---|---|
| "抽哪些点" / "怎么排" / "教学弧线" | `modules/extraction-rules.md`（七条抽取规律） |
| 配色 / 坐标 / 版式模板 | `modules/design-spec.md`（写第一页前必读） |
| 报错 / lint 不过 / 页面重复 | `modules/pitfalls.md`（实测踩坑与修法） |
| 换配色方案 | `modules/design-spec.md` §0（A 深蓝 / B 教室浅底 / C 自然绿） |
| "配图从哪来" | `modules/design-spec.md` §4（只搜不生成） |

## 五、外部能力复用清单

本 skill 不自造底层轮子，复用以下既有能力：

| 能力 | 来源 | 用途 |
|---|---|---|
| 飞书幻灯片 XML 读写 | `lark-slides` 连接器 skill | `+create` / `+add-slide` / `+xml-get` / `+delete-slide` |
| XML 合法性校验 | `lark-slides/scripts/xml_lint.py` | 每页提交前 lint，error_count 必须 0 |
| 导出 pptx | `lark-cli drive +export` | 最终交付本地 pptx |
| 网络找图 | WebSearch + 下载 | 配图取材（禁止 AI 生图） |

> 本 skill 为 Independent 类型，不读取 `afp-shared-*` primitive；中间产物直接落盘于 `chN_ppt/`，无需跨 skill 状态传递。

## 六、首次上手引导

```
你好！我来把这一章教材做成教学课件（飞书在线幻灯片 + pptx + 代码 txt）。

默认用「科技深蓝风」，和你们现有课程的 PPT 同一套视觉。
三件交付物：
  1. 飞书在线幻灯片链接
  2. 导出的本地 .pptx
  3. <章名>_实例代码.txt（正文不贴代码，代码都在这里）

请确认三件事：
  ① 要处理哪一章？（给 md 文件名）
  ② 配色用默认深蓝，还是换教室浅底 / 自然绿？
  ③ 有没有可参照的既有 PPT？（没有就按本课程既有规律做）

确认后我从 P1 开始。
```

## 七、通用指令表

| 指令 | 功能 |
|---|---|
| `Next` | 确认当前阶段完成，进入下一步 |
| `Back` | 回到上一阶段修改 |
| `Edit <字段>=<新值>` | 修改状态字段 |
| `Skip` | 跳过可选阶段（如硬件增强页） |
| `Status` | 输出当前 HUD 状态 |
| `Continue {chN_ppt}` | 跨对话续跑（从磁盘恢复状态） |
| `校验` | 立即对已提交页面重跑 lint + 页数核对 |
| `导出` | 跳过验收，直接导出 pptx |

## 八、断点续传（跨对话抗压缩）

- 每阶段完成后写入 `chN_ppt/.lark-slides/plan/chN/deck-state.json`
- 用户新对话说 `Continue {chN_ppt路径}` → 从磁盘恢复 `current_stage` 与 `submitted_pages` 续跑
- 长对话中每 5 轮 auto-checkpoint

## 九、Hard Stop 输出规范

每阶段完成后输出：

```
╭─ norma-textbook-deck · P{N} 完成 ────────────╮
│ 📖 章节：第{N}章 {章名}
│ 🎨 配色：{tech_dark_blue | classroom_light | nature_green}
│ 📊 进度：{submitted_pages}/{planned_pages} 页
│ 📁 已落盘：{files}
│ 📍 下一步：P{N+1} - {next_stage_name}
│ 👉 NEXT：Next 继续 / Back 回退 / Edit 修改
╰──────────────────────────────────────────╯
```

**硬停纪律**：P1/P2/P3 阶段切换、配色选定、以及「删除/覆盖已提交页面」等破坏性操作前，必须停下来等用户确认，不允许自动推进。

## 十、输出结构（§7 Output Structure）

每章交付固定三件套（落盘到教材 md 同目录）：

| # | 交付物 | 文件名 | 说明 |
|---|---|---|---|
| 1 | 飞书在线幻灯片 | — | `+create` 返回的 url |
| 2 | 本地 pptx | `第N章_<章名>.pptx` | `drive +export` 导出后复制 |
| 3 | 代码外置 | `第N章_<章名>_实例代码.txt` | 按小节归档，保留缩进注释 |

中间产物落盘：`chN_ppt/slide-NN.xml`、`chN_ppt/.lark-slides/plan/chN/slide_plan.json`、`chN_ppt/images/`、`chN_ppt/add.sh`。

## 十一、证据链（§6 Evidence Chain）

- 教材内容全部来自用户指定的源 md，**不编造**；PPT 上出现的每个知识点都能在源 md 里找到出处。
- 配色/字体/坐标以 `modules/design-spec.md` 的实测值为准；lint 报错以 `xml_lint.py` 实际输出为准。
- 配图须来自网络搜索的**真实素材**，记录来源关键词；找不到合适素材时如实说明并回退纯图形绘制。
- 涉及"第1章 PPT 规律"等结论时，以实际解析 pptx 的结果为证，不凭印象。

## 十二、反模式警告（内嵌 10 条）

- ❌ **不反推规律直接排**——导致每章风格漂移，失去"模板"意义
- ❌ **PPT 正文贴整段代码**——违反核心约束，代码必须外置
- ❌ **攒批提交**——一次写 10 页再统一 lint，报错难定位
- ❌ **跳过 lint 直接提交**——服务端报错更难查
- ❌ **含 img 页面提交后不回读核页数**——图片上传会多出重复页
- ❌ **用 AI 生图做配图**——失实、风格漂移、耗积分；必须网络搜图
- ❌ **直接 lint `+xml-get` 的 JSON 包裹文件**——会被判 not well-formed
- ❌ **破坏性操作不硬停**——删除/覆盖已提交页面前必须确认
- ❌ **中间产物只留在对话里**——换对话即丢失，必须落盘
- ❌ **交付不等价于"页数对"**——必须跑完整三重验收（页数 + 全文 lint + pptx 完整性）

## 十三、用户核查清单

流程型 skill 标配，随附 `templates/用户核查清单.md`：每个阶段一行"skill 应完成的动作 + 你怎么核查 + 应见哪个落盘文件"，供用户勾选监督。

## 十四、维护者与版本

- 维护者：norma
- 版本：v1.0.0（2026-09-16 · 由 afp-skill-creator 9 阶段流程产出）
- 前身：`textbook-deck-dark-blue`（保留，向后兼容）
- AFP-SPEC：Bronze（见 `AFP-SPEC-CONFORMANCE.md`）
- 测试状态：**provisional**（已在第 10 章 25 页课件上完成 1 次端到端验证；满 3 个真实用户案例后升 certified）

## 十五、沉淀案例台账（P9 迭代用）

每完成一章课件，在此追加一行。这是把 provisional 升为 certified 的证据。

| # | 日期 | 章节 | 页数 | 配色 | 验证结论 / 偏差修正 |
|---|---|---|---|---|---|
| 1 | 2026-09-16 | 第10章 综合项目：虚拟机器人指令解析 | 25 | tech_dark_blue | 端到端跑通。偏差 3 处已回写 `modules/pitfalls.md`：①`border width` 须整数；②含 `<img>` 页提交后末尾多出重复页，需 `+xml-get` 核页数并 `+delete-slide` 删除；③`+xml-get` 输出是 JSON 包裹，须抽 `data.xml_presentation.content` 成纯 xml 再 lint。 |

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
