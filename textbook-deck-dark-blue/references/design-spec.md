# 教材课件 PPT · 设计规范与高频坑

本文件从一次 26 页全量实战沉淀。写第一页前读一遍；配色先按 §0 选一套，再照 §1–§4 写，能避开绝大多数 lint 报错。

## 目录
0. 配色方案选择（先定，全程一套到底）
1. 字体与字号
2. 画布坐标与页面骨架
3. 常用版式模板
4. 高频 lint 报错与修法（实测）
5. Windows / lark-cli 操作要点

---

## 0. 配色方案（先选一套，全程一致）

**选哪套**：用户点名风格就以用户为准；没点名时按主题选——编程/AI/机器人默认 `tech_dark_blue`；要长时间投影、护眼或浅色风选 `classroom_light`；生物/自然/科普选 `nature_green`。选定后整份 deck 只用这一套，不要中途混色。

### 方案 A · tech_dark_blue（科技深蓝，默认，深底）
| 角色 | 值 |
|---|---|
| 页面背景 | `linear-gradient(135deg,rgba(8,18,38,1) 0%,rgba(14,40,80,1) 100%)` |
| 主标题 | `rgba(255,255,255,1)` |
| 主强调（青） | `rgba(79,195,247,1)` |
| 次强调（琥珀，重点/思政） | `rgba(255,183,77,1)`；深底上文字用 `rgba(255,220,160,1)` |
| 正文 | `rgba(220,230,245,1)` / `rgba(180,196,220,1)` |
| 次要/图注 | `rgba(143,163,196,1)` |
| 成功/输出 | `rgba(120,230,160,1)` |

### 方案 B · classroom_light（教室浅底，投影护眼）
| 角色 | 值 |
|---|---|
| 页面背景 | `linear-gradient(135deg,rgba(244,246,250,1) 0%,rgba(232,238,246,1) 100%)` |
| 主标题 | `rgba(26,46,75,1)`（深靛蓝） |
| 主强调 | `rgba(37,99,235,1)`（亮蓝） |
| 次强调（重点/思政） | `rgba(232,114,12,1)`（橙） |
| 正文 | `rgba(45,55,72,1)` |
| 次要/图注 | `rgba(110,125,145,1)` |
| 成功/输出 | `rgba(22,138,78,1)` |
| 卡片底 | `rgba(255,255,255,0.8)` + 细描边 `rgba(26,46,75,0.15)` |

### 方案 C · nature_green（自然/生物科普，浅绿底）
| 角色 | 值 |
|---|---|
| 页面背景 | `linear-gradient(135deg,rgba(243,247,240,1) 0%,rgba(228,238,224,1) 100%)` |
| 主标题 | `rgba(47,74,59,1)`（深墨绿） |
| 主强调 | `rgba(46,125,80,1)` |
| 次强调（重点） | `rgba(200,164,74,1)`（土黄） |
| 正文 | `rgba(55,70,60,1)` |
| 次要/图注 | `rgba(120,135,120,1)` |
| 卡片底 | `rgba(255,255,255,0.85)` + 细描边 `rgba(47,74,59,0.15)` |

**通用约束**：无论哪套，全 deck 只用到"主标题色 + 主强调 + 次强调 + 正文 + 次要"这几个色，不要额外加色；卡片/模块底用主强调的低透明度（0.10–0.18）半透明块。

## 1. 字体与字号
- 中文一律「思源黑体」；代码/变量/符号用 `fontFamily="Roboto Mono"`。
- 标题 28–36px bold；正文 15–17px；图注/caption 12–13px。
- 文字颜色写在 `<content color="...">`（不是 fontColor）。
- 深底用 §0 深底色值；浅底把"正文/图注"换成对应深色值，强调色直接用。

## 2. 画布与页面骨架
- 画布固定 960×540；内容区左右留 80（x=80…880）。
- 页脚线在 y≈486，元素底缘不超过 y≈490。
- 标准标题区：小标签 y≈50（13px，主强调色，letterSpacing=2）→ 主标题 y≈78–80（28–32px bold）→ 导读 y≈126–136（15px）→ 主内容区从 y≈160 起。

## 3. 常用版式模板
- **纵向流程图**：开始/结束 `ellipse` w=120 h=30 居中 x=420；步骤 `round-rect` x=330 w=300 h=32；节点间竖线 `line startX=480 ... endArrow`，border width=2；关键步骤用次强调色填充高亮；右侧 x=660 放图注。
- **贴标签的盒子（变量）**：盒子 `rect`；标签 `round-rect` 压在盒子顶部**外面**。**标签底缘必须 ≤ 盒子顶缘 − 4px**（推荐：标签 y=128 h=28，盒子 y=160 h=110）。
- **三段横向流程**：三个等宽块 x=70/380/670，同一 y、h；块间横箭头连到垂直中线；中间块高亮。
- **三栏对比**：x=70/355/634，w=255，同 y/h；短标签要留够宽度。
- **控制台示意条**：`round-rect` 半透明底 + 主强调描边，等宽字体放提示语与光标 █。

## 4. 高频 lint 报错与修法（实测）
| 报错 | 原因 | 修法 |
|---|---|---|
| `bbox_overlap` | 标签压进盒子 | 标签上移，标签底缘 < 盒子顶缘（见 §3） |
| `bbox_overlap` | 中心向四角画连线穿越文字 | 不画辐射连线；改四角环绕、不连线 |
| `text_may_overflow_shape`(width) | 短文本比 shape 宽 | 缩短文案 / 加宽 shape / 单行加 `wrap="false"` |
| `sxsd_invalid_scalar: border width` | border width 写了小数 | 只能是非负整数，写 2 不写 1.5 |
| 含 `<img>` 的页提交后**末尾多一张重复页** | 图片上传吃掉多个 revision，slide 被追加两次（如 micro:bit 页出现位置18 + 末尾位置26 两张相同） | 提交后必做 `+xml-get` 核页数；用 `+delete-slide --slide-id <末尾重复页>` 删掉，保留序列中位置正确的那张 |
| `xml_not_well_formed`(line 1, col 0) | 把 `+xml-get` 的 **JSON 包裹文件**直接喂 xml_lint | 先 python 抽出 `data.xml_presentation.content` 写成纯 `.xml` 再 lint（见 §5） |
| `sparse_container_content`(warn) | 大盒子内容太少 | 缩小盒子高度或补一行说明 |
| table 高度不符 | table height ≠ 各行 tr height 之和 | 精确等于各行高之和（差 1px 也报错） |
| 全文才暴露的 id 重复 | 跨页自造 id | 元素不要写 id，留空由服务端分配 |

**硬规矩**：不写 `<?xml?>`，单页只放一个 `<slide>`；禁 emoji；语义图标先查 IconPark；`&`/`<`/`>` 转义；line 箭头必须显式 `<endArrow type="arrow"/>`。

## 5. Windows / lark-cli 操作要点
- Python 命令是 `python`（本机无 python3）。
- 每条 Bash 只跑一条命令（PowerShell 无 `&&`）。
- lark-cli 的 `--output/--file/--slide` 只接受 CWD 内相对路径；先 `Set-Location` 到工作目录。
- 不在命令行内联 JSON；传结构先 Write 成文件再 `@file`。
- 导出 pptx：`lark-cli drive +export --token "<id>" --doc-type slides --file-extension pptx --output-dir "."`。
- 复制文件用 python `shutil.copy`，不用 shell 重定向（BOM/编码）。
- **`+xml-get` 输出是 JSON 包裹**，正文在 `data.xml_presentation.content`（字符串形式的 `<presentation>...`）。**不要**直接把这个 JSON 文件喂 `xml_lint.py`（会报 `not well-formed`）。正确做法：先 python 抽出 `content` 写成纯 `.xml`，再 lint 该 `.xml`：
  ```python
  import json
  d = json.load(open('server_full.xml', encoding='utf8'))
  open('server.xml','w',encoding='utf8').write(d['data']['xml_presentation']['content'])
  ```
- **含 `<img>` 的页面提交后务必核页数**：图片上传会占用多个 revision，偶发把该页追加两次。提交完所有页后跑一次 `+xml-get`，数 `<slide>` 是否等于计划页数；多了就用 `+delete-slide --slide-id <重复页>` 删末尾那张（先 `--dry-run` 确认）。
- 本机 bash 初始 PATH 不含标准 bin，命令前加 `export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"`；python 用托管路径 `C:/Users/29206/.workbuddy/binaries/python/versions/3.13.12/python.exe`。
