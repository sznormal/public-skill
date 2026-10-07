# 教材课件 · 设计规范与高频坑

> norma-textbook-deck · Module
> 来源：第1章（26 页）+ 第10章（25 页）两次全量实战沉淀。
> 写第一页前读一遍；配色先按 §0 选一套，再照 §1–§3 写，能避开绝大多数 lint 报错。

---

## 0. 配色方案（先选一套，全程一致）

**选哪套**：用户点名就以用户为准；没点名按主题——编程/AI/机器人默认 `tech_dark_blue`；长时间投影/护眼选 `classroom_light`；生物/自然/科普选 `nature_green`。选定后整份 deck 只用这一套。

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
| 主标题 | `rgba(26,46,75,1)` |
| 主强调 | `rgba(37,99,235,1)` |
| 次强调 | `rgba(232,114,12,1)` |
| 正文 | `rgba(45,55,72,1)` |
| 次要/图注 | `rgba(110,125,145,1)` |
| 成功/输出 | `rgba(22,138,78,1)` |
| 卡片底 | `rgba(255,255,255,0.8)` + 描边 `rgba(26,46,75,0.15)` |

### 方案 C · nature_green（自然/生物科普，浅绿底）

| 角色 | 值 |
|---|---|
| 页面背景 | `linear-gradient(135deg,rgba(243,247,240,1) 0%,rgba(228,238,224,1) 100%)` |
| 主标题 | `rgba(47,74,59,1)` |
| 主强调 | `rgba(46,125,80,1)` |
| 次强调 | `rgba(200,164,74,1)` |
| 正文 | `rgba(55,70,60,1)` |
| 次要/图注 | `rgba(120,135,120,1)` |
| 卡片底 | `rgba(255,255,255,0.85)` + 描边 `rgba(47,74,59,0.15)` |

**通用约束**：全 deck 只用"主标题 + 主强调 + 次强调 + 正文 + 次要"这几个色；卡片/模块底用主强调的低透明度（0.10–0.18）半透明块。

## 1. 字体与字号

- 中文一律「思源黑体」；代码/变量/符号用 `fontFamily="Roboto Mono"`。
- 标题 28–36px bold；正文 15–17px；图注/caption 12–13px。
- 文字颜色写在 `<content color="...">`（**不是** fontColor）。
- `content` 需带 `autoFit="normal-auto-fit"` 与 `wrap="true"`；行距 `lineSpacing="multiple:1.1~1.5"`。

## 2. 画布与页面骨架

- 画布固定 960×540；内容区左右留 80（x=80…880）。
- 页脚在 y≈494，元素底缘不超过 y≈500。
- 标准标题区：小标签 y≈46（13px，主强调色）→ 主标题 y≈70（30px bold）→ 导读 y≈120（15px）→ 主内容区从 y≈156 起。
- 高度预算（内容页）：`40 上padding + 74 标题块 + 14 + 2 分隔 + 14 + C 内容区 + 48 下padding = 720` ⇒ **C ≈ 528**（按 720 高折算）。

## 3. 常用版式模板

- **纵向流程图**：开始/结束 `ellipse` w=120 h=30 居中；步骤 `rect` x=330 w=300 h=32；节点间竖线 `line startX=480 ... endArrow`，border width=2；关键步骤用次强调色填充高亮；右侧放图注。
- **贴标签的盒子（变量）**：盒子 `rect`；标签 `round-rect` 压在盒子顶部**外面**。**标签底缘必须 ≤ 盒子顶缘 − 4px**。
- **三段横向流程**：三个等宽块 x=70/380/670，同一 y、h；块间横箭头连到垂直中线；中间块高亮。
- **三栏对比**：x=70/355/634，w=255，同 y/h；短标签要留够宽度。
- **卡片网格**：2×2 或 3 卡；每卡 `rect` 半透明底 + 标题 + 说明；卡间距 ≥ 20。
- **表格（形状绘制）**：表头行高 42（主强调 0.22 底），数据行高 48–60（交替 `rgba(255,255,255,0.05)` / `0.02`），竖分隔线用 `line` + `rgba(143,163,196,0.35)`。
- **控制台示意条**：`rect` 半透明底 + 主强调描边，等宽字体放提示语与光标 █。

## 4. 配图取材（硬规矩：只搜不生成）

**禁止用 AI 生图（ImageGen）做课件配图。** 需要实拍素材（封面、硬件板卡、实验装置、场景照）时，**用网络搜索找现成图片**。

- 搜索关键词按「对象 + 型号/场景」组织（如 `micro:bit V2 board front photo`、`RK3588 development board`）。
- 优先选：白底或暗底可抠图的正视实拍图、分辨率 ≥ 1000px、无强水印。
- 下载后统一转 PNG、裁成课件该处宽高比（如 320×240 / 426×284），命名语义化（`microbit.png`、`cover.png`）。
- 引用：`<img src="@./images/xxx.png" topLeftX=".." topLeftY=".." width=".." height=".."/>`。
- **其余页面一律用 shape/line 纯图形绘制**，不额外找图；能画就不找图。
- 找不到合适实拍图 → 回退纯图形绘制（如用 5×5 点阵方块模拟 LED 屏），**绝不改用 AI 生图**。

## 5. 高频 lint 报错与修法（实测）

| 报错 | 原因 | 修法 |
|---|---|---|
| `bbox_overlap` | 标签压进盒子 | 标签上移，标签底缘 < 盒子顶缘 |
| `bbox_overlap` | 中心向四角画连线穿越文字 | 不画辐射连线；改四角环绕、不连线 |
| `text_may_overflow_shape`(width) | 短文本比 shape 宽 | 缩短文案 / 加宽 shape / 单行加 `wrap="false"` |
| `sxsd_invalid_scalar: border width` | border width 写了小数 | **只能非负整数**，写 2 不写 1.5 |
| `xml_not_well_formed`(line1 col0) | 把 `+xml-get` 的 JSON 包裹直接喂 lint | 先抽 `data.xml_presentation.content` 成纯 `.xml` 再 lint |
| `sparse_container_content`(warn) | 大盒子内容太少 | 缩小盒子高度或补一行说明 |
| 含 `<img>` 页提交后末尾多重复页 | 图片上传吃多个 revision | 回读核页数，`+delete-slide` 删末尾重复页 |
| 全文才暴露的 id 重复 | 跨页自造 id | 元素不写 id，留空由服务端分配 |

**硬规矩**：不写 `<?xml?>`，单页只放一个 `<slide>`；禁 emoji；语义图标先查 IconPark；`&`/`<`/`>` 转义；line 箭头必须显式 `<endArrow type="arrow"/>`。

## 6. Windows / lark-cli 操作要点

- python 用托管路径：`C:/Users/admin/.workbuddy/binaries/python/versions/3.13.12/python.exe`。
- 本机 bash 初始 PATH 不含标准 bin，命令前加 `export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"`。
- lark-cli 的 `--output/--file/--slide` 只接受 CWD 内相对路径；先 cd 到工作目录。
- 不在命令行内联 JSON；传结构先 Write 成文件再 `@file`。
- 导出 pptx：`lark-cli drive +export --as user --token "<id>" --doc-type slides --file-extension pptx --output-dir "."`。
- 复制文件用 python `shutil.copy`，不用 shell 重定向（BOM/编码）。
- lint 结果取法：`xml_lint.py --input x.xml > .lint.tmp.json 2>&1`，再 python 读 `summary.error_count`。
- 全文核页数：`+xml-get` 输出 JSON → 抽 `content` → 数 `<slide>` 个数。
