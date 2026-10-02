---
name: suit-sz-teaching-suite-norma
version: 1.2.0
display_name: 高校教学文件写作套件（课标·教案·授课计划）
display_name_en: Teaching Document Suite (Course Standard, Lesson Plan, Schedule)
category: writing
author: norma（中德机器人学院 / 深圳信息职业技术大学）
license: MIT
agent_created: true
description: 面向高校与职业院校教师的教学公文写作技能，闭环完成三类教学文档的撰写与自查：撰写《课程标准》（含课程思政融入表）、以课标为唯一输入生成教案与学期授课计划、并对三份文件做版本格式内容与时数勾稽的督导一致性检查。内置课标、教案、授课计划空白模板与确定性渲染、回读校验脚本，产出字体字号首行缩进行距均可机器校验的 docx。当用户提到课程标准、教学大纲标准、课标排版、教案、授课计划、学期教学进度、教学文件检查时使用。
description_zh: 面向高校与职业院校教师的教学公文写作技能，闭环完成《课程标准》（含课程思政融入表）、教案与学期授课计划的撰写，并对三份文件做版本、格式、内容与时数勾稽的督导一致性检查。
description_en: A teaching-document authoring skill for college and vocational-school teachers. It drafts a Course Standard with an ideological-education integration table, generates weekly lesson plans and the semester teaching schedule from that standard, and runs a supervisor consistency check across version, formatting, content and teaching-hour reconciliation. Ships blank templates plus deterministic render and read-back validation scripts. Use when the user mentions course standard, syllabus standard, lesson plan, teaching schedule, semester progress table, or teaching-document review.
---

# 高校教学文件写作套件

一次闭环完成三类教学公文：**《课程标准》**（设计总纲）→ **教案 + 学期授课计划**（落地执行件）→ **督导检查**（三份文件一致性核对）。

默认版式取自深圳信息职业技术大学（下称"深信院"）校版模板；**用户提供本校模板时，一切版式以用户模板实际提取值为准**。

## 一、能力与链路

| 代号 | 能力 | 输入 | 产物 |
|---|---|---|---|
| **P2** | 撰写《课程标准》 | 教材/大纲/课程信息（可无，允许检索补充） | `课程标准-<课程名>.docx` |
| **P3** | 撰写教案 + 学期授课计划 | **一份已写好的课标 .docx**（硬性） | `<课程名>-教案N.docx` × N + `<课程名>-课程计划.docx` |
| **P4** | 督导一致性检查 | 上述文件（≥1 份即可） | `督导检查报告-<课程名>.md` |

三条铁律，任何一条都不能绕：

1. **先课标 → 后教案/授课计划 → 最后督导。没有课标绝不写教案。** 教案的教学过程、重难点、思政点全部源自课标，凭空编造一律返工。
2. **生成新文件，绝不覆盖用户模板。** 用户常开着 Word，覆盖会损坏会话。
3. **回读校验判 PASS 才交付。** 不声称"应该没问题"。

## 二、开工三步

### 第 1 步 环境自检（只读）

```
<python> scripts/check_environment.py
```

**不要用裸 `python`**：沙箱与部分环境里 `python` 可能不在 PATH 上，或指向未装 python-docx 的解释器。
第一次用一个能跑起来的解释器执行本脚本即可，它会在自己与受管 Python 目录里查找，并输出：

- 总体状态：`ready` / `partial` / `needs_setup` / `unavailable`
- `recommended_interpreter`：**后续所有脚本都用这个解释器执行**
- `runtime_level`：L1（可出 docx）或 L2（Markdown 降级）

加 `--json` 取机器可读结果。自检不安装、不登录、不授权、不改配置、不访问网络。

### 第 2 步 按意图路由

| 用户意图信号 | 去哪 |
|---|---|
| 课标 / 大纲标准 / 课程纲要 / 课标排版 / 套模板 / 按大纲生成 | 读 `@references/workflow-course-standard.md` |
| 教案 / 授课计划 / 教学进度 / 周次表 / 根据课标生成教案 | 读 `@references/workflow-lesson-schedule.md` |
| 督导 / 检查 / 对一对 / 自查 / 一致性 / 匹配 | 读 `@references/workflow-supervisor.md` |
| 笼统"写教学文件"且未指明 | 一次提问给三选一（课标 / 教案+授课计划 / 督导），别猜 |
| 问环境、装依赖、报错排查 | 读 `@references/setup-guide.md` |

若用户要走教案或督导但**没给课标**，直接说明必须先有课标，并转去课标工作流；不要顺手编一份。

### 第 3 步 执行并自证

每个工作流都以"回读校验"收尾。改完排版后可以整体跑一遍自测确认技能本身没坏：

```
<python> scripts/selftest.py --out <产物目录>
```

8 项全 PASS 表示渲染、校验、降级产出链路正常。

## 三、降级策略（缺什么降什么，绝不整体停摆）

| 级别 | 触发条件 | 交付形态 |
|---|---|---|
| **L1 完整** | 找到可 import python-docx 的解释器 | 生成排版对齐模板的 `.docx`（首选） |
| **L2 Markdown** | 没有可用 python-docx | `scripts/export_markdown.py` 产出 `.md` 全文 + Word 版式对照表，用户粘贴进本校模板即可 |
| **L3 纯文本** | 连文件写入也受限 | 直接在对话中输出完整结构化内容 + 版式说明 |

- 缺 python-docx 且用户接受安装 → 按 `@references/setup-guide.md` 的步骤引导，装完重跑自检再看状态。
- 缺 python-docx 且用户不愿安装 → 按 L2 继续干活，**不停工等安装**，并在交付时标注"未产出 docx"。
- 缺 openpyxl / olefile → 只影响 xlsx 大纲与旧版 .doc 的自动解析，改为请用户给文本或转存 .docx。
- 逐项降级的限制、恢复与停止条件见 `skill-dependencies.json`。

## 四、参考文件（按需读取，本文件是唯一入口）

| 文件 | 什么时候读 |
|---|---|
| `@references/format-rules.md` | **涉及任何排版时必读**：字体、字号、首行缩进、行距、标题与表格顺序、python-docx 函数清单 |
| `@references/politics-integration.md` | 写教案"教学过程"或核对思政覆盖时 |
| `@references/teacher-checklist.md` | 向老师收集素材，需要逐项清单时 |
| `@references/workflow-course-standard.md` | 写课标 |
| `@references/workflow-lesson-schedule.md` | 写教案与授课计划 |
| `@references/workflow-supervisor.md` | 做督导检查 |
| `@references/setup-guide.md` | 环境缺失、安装、卸载与回滚 |

内置空白模板在 `templates/`：`课程标准.docx`、`教案模板.docx`、`课程计划-空白模板.docx`。

## 五、脚本清单

| 脚本 | 用途 | 关键参数 |
|---|---|---|
| `check_environment.py` | 只读环境自检，给四态结论与推荐解释器 | `--json` |
| `render_course_standard.py` | JSON → 排版合规的课标 docx | `--data` / `--out` / `--demo` / `--no-template` |
| `validate_docx.py` | 回读 docx 校验排版，输出位置/期望/实测 | `<docx> --profile course-standard\|lesson\|schedule` |
| `selftest.py` | 端到端自测 8 项（含反向用例） | `--out` / `--json` |
| `export_markdown.py` | L2 降级产出 Markdown + 版式对照表 | `--data` / `--type` / `--out` / `--demo` |
| `docx_helpers.py` | 公共函数：字体、缩进、单元格、标题+表格插入 | 供上面脚本与临时脚本 import |
| `doc_extract.py` | 提取旧版 .doc（OLE2）文本 | `<doc 路径>` |
| `progress_dashboard.py` | 在确认门处显示"写到哪、卡在哪" | 供工作流调用 |

## 六、停止条件

- 头部信息栏（课标）或范围与日期基准（教案/授课计划）**未经用户显式确认** → 停止，不进入生成。
- 走教案但没有课标 → 停止并转课标工作流，不臆造。
- 素材缺失且用户不允许检索 → 只产出骨架与待补清单，不编造课程内容、学时、思政案例。
- 找不到任何可用解释器且用户拒绝安装、也拒绝 Markdown 降级 → 停止并说明继续所需条件。

## 七、边界

- 默认版式仅对应深信院校版模板；其他院校请提供本校模板，本技能自动以其提取值为准。
- 不处理单页讲义、PPT、论文、报告、公函等非教学公文类文档。
- 督导环节只读检查并出报告，不自动修改任何 docx。
- 生成内容须经任课教师与教研室审核确认后使用。
