---
name: norma-drawio-technical-roadmap
description: "把参考图的版式与资料内容合成一份可直接粘贴进 draw.io（diagrams.net）的未压缩 XML，用于绘制科研课题、教改项目、工程项目的技术路线图。触发场景：用户提供一张参考图或版式样例，并配合 PDF、Word、Markdown 或文本要点，说「参考这张图重画」「照这个风格出图」「画张技术路线图」「生成 draw.io XML」「输出 mxfile 代码」「把申报书做成图」「按这个版式换成我的内容」「出张能在 draw.io 里改的图」「仿这张图的排版重排」等。不触发：用户要 Mermaid、PPT、PNG 图片、Visio 文件、思维导图层级大纲，或只是问 draw.io 怎么用、要讲解某张图的含义、要润色图上的文字——这些不属于本 skill。"
version: 2.0.0
agent_created: true
skill_type: independent
afp_spec_target: bronze
partner: norma
---

# 定位

把「一张参考图 + 若干资料」变成一份可直接粘贴进 draw.io 的未压缩 XML 绘图代码。参考图只提供版式，内容一律来自资料，每个节点可溯源。

# 核心设计理念

1. **版式归版式，内容归内容**——参考图决定长什么样，资料决定写什么，两者不互相污染。
2. **步步落盘**——版式规格、内容结构、坐标布局都是具名文件，换个新对话只凭磁盘就能接着改。
3. **条件停下，不打扰**——默认一次出图，只在真的拿不准时才问。
4. **可溯源**——每个节点标出处，查无实据就标 `unverified`，不拿常识填空。

# 状态骨架

每次出图在 `drawio-projects/<图名>/manifest.json` 维护：

```json
{
  "skill": "norma-drawio-technical-roadmap",
  "diagram_name": "",
  "inputs": {"reference_image": "", "sources": []},
  "stage_status": {"s1": "pending", "s2": "pending", "s3": "pending", "s4": "pending", "s5": "pending", "s6": "pending"},
  "artifacts": {"spec": "01-版式规格.md", "content": "02-内容结构.md", "layout": "03-坐标布局.md", "drawio": ""},
  "validation": {"ran": false, "errors": 0, "warnings": 0},
  "notes": ""
}
```

# 阶段路由表

| 阶段 | 做什么 | 加载 | 落盘 |
|---|---|---|---|
| S1 立项 | 建项目目录与状态文件 | `scripts/init_project.py` | `manifest.json` |
| S2 解版式 | 拆参考图的骨架、配色、字体、组件 | `@references/layout-patterns.md` | `01-版式规格.md` |
| S3 提内容 | 提炼资料，建节点清单与术语表 | `@references/evidence-and-terms.md` | `02-内容结构.md` |
| S4 排坐标 | 按网格排出节点与连线坐标 | `@references/layout-patterns.md` | `03-坐标布局.md` |
| S5 出图 | 生成未压缩 XML | `@references/drawio-xml-spec.md` | `<图名>.drawio` |
| S6 自检 | 校验结构并把结果写回状态 | `scripts/validate_drawio.py` | 更新 `manifest.json` |
| S7 交付 | 输出 XML 代码块与文件路径 | — | — |

无参考图时，S2 直接采用 `@references/layout-patterns.md` 的默认版式，并在 `01-版式规格.md` 注明「未提供参考图，采用默认版式 X」。

# 条件 Hard Stop

默认一路推到底。**只有命中以下任一信号才停下**，停下时输出确认单并等回复：

| 信号 | 表现 | 停下来的动作 |
|---|---|---|
| 阶段划分有歧义 | 资料的研究阶段能读出两种以上分法 | 列出 2—3 种分法，各带优劣，让用户选 |
| 关键事实缺失 | 阶段名、方法名、成果名、指标数据缺项 | 列出缺项清单，问是留 `待补充` 还是由用户补 |
| 版式认不出来 | 参考图模糊，骨架或配色判不准 | 说明判不准的点，问是换默认版式还是用户指定 |

确认单格式：

```
╭─ S{n} 需你定夺 ──────────────────╮
│ 问题：{一句话}
│ 选项 A：{…} 优势{…} 代价{…}
│ 选项 B：{…} 优势{…} 代价{…}
│ 已落盘：{文件路径}
│ 👉 NEXT：回复 A / B / Back 重来
╰────────────────────────────────╯
```

不替用户拍板，不合并成一次「最终确认」。

# 通用指令

| 指令 | 含义 |
|---|---|
| `Next` | 当前阶段通过，进入下一阶段 |
| `Back` | 回退上一阶段，该阶段落盘文件作废重做，其余保留 |
| `Edit <字段>=<值>` | 修改状态字段或图上的某项内容 |
| `Status` | 输出当前 `manifest.json` 摘要 |
| `Continue <项目路径>` | 新对话里读 `manifest.json` 接着改图 |
| `Export` | 列出本次全部落盘文件 |

用户越阶要求（例如项目尚未立项就索要 XML，或跳过内容提炼直接要坐标）时，先补齐前置阶段并落盘，再响应；任何情况下不跳过落盘环节。

# 输出纪律

- S7 只输出一个 XML 代码块，加一行 `已保存：<绝对路径>`，代码前后不写解释、分析或客套话。
- 中途不向用户汇报版式分析、内容提炼过程。
- XML 必须未压缩明文，禁止 `compressed="true"` 与 base64。

# 硬规则

- `&`、`<`、`>`、`"`、`'` 必须转义；`value` 内换行写 `&lt;br&gt;`。
- 节点 `id` 从 `2` 起唯一编号；连线 `source`、`target` 必须指向真实存在的 id。
- 中文一律 `fontFamily=Microsoft YaHei`。
- 坐标为 10 的倍数，同层节点尺寸一致。
- 只归纳不编造；资料没写的写 `待补充` 或标 `unverified`。
- 不修改用户提供的原始资料文件。

# 停止条件

- 资料自相矛盾：按最新或最正式来源出图，并在 `02-内容结构.md` 记录冲突点。
- 用户要求「缺什么就留空」：不再追问，直接出图。
- 校验脚本 `errors` 非空：修到空为止再交付；脚本不可用时手工核对 `@references/drawio-xml-spec.md` 的自检清单，并在 `manifest.json` 的 `notes` 标注「未运行脚本自检」。

# 参考资料

- `@references/layout-patterns.md`：5 种版式、默认配色、字体层级、坐标骨架。S2 与 S4 加载。
- `@references/evidence-and-terms.md`：来源标注、`unverified` 规则、术语一致性表。S3 加载。
- `@references/drawio-xml-spec.md`：XML 骨架、转义、样式速查、自检清单、导入失败对照表。S5 与 S6 加载。

# 交付物

一次完整出图后，`drawio-projects/<图名>/` 下应有：`manifest.json`、`01-版式规格.md`、`02-内容结构.md`、`03-坐标布局.md`、`<图名>.drawio`。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
