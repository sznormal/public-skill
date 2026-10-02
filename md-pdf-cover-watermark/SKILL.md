---
name: md-pdf-cover-watermark
description: 把 Markdown 批量转成「带封面 + 全页水印 + 页码」的 A4 PDF（中文教材/讲义/报告场景）。当用户提出"给这几章 md 加封面导出 PDF""PDF 要加水印""第 X-Y 章做成 PDF""每章配一个封面"等需求时使用。内含纯标准库 CDP 打印方案（不依赖 playwright/puppeteer）、mermaid 图自动渲染与缩放、封面/水印模板，以及交付验收脚本。
agent_created: true
---

# Markdown → 带封面与水印的 PDF

把一组 Markdown 章节转成 A4 PDF：每份 PDF 第 1 页是**独立封面**（书名 / 章节号 / 章节名 /
编著 / 单位），正文每页覆盖**斜向水印**，页脚带**连续页码**，Markdown 里的 **mermaid 流程图
自动渲染为矢量图**。

## 何时用它

- 教材 / 讲义 / 培训手册：一章一个 md，需要导出成带封面、带防伪水印的 PDF 发学生
- 学校 / 单位内部材料：需要"XX学校"水印 + 统一封面
- 任何"md → 排版精美的 PDF"且**要求中文排版、表格、代码块、mermaid 都正常**的场景

配套能力：`build_all.py` 支持章号区间批量处理，自动跳过网盘冲突文件（`*冲突文件*`、`*副本*`）。

## 环境准备（一次性）

用 WorkBuddy 托管 Python 环境，装三个纯 Python 包即可（**不需要 playwright**）：

```bash
# WorkBuddy 托管 venv 的 python（按本机 HOME 推导，勿写死用户名）
PY="$HOME/.workbuddy/binaries/python/envs/default/Scripts/python.exe"   # Windows
# PY="$HOME/.workbuddy/binaries/python/envs/default/bin/python"          # macOS / Linux
"$PY" -m pip install markdown pypdf pymupdf
```

- `markdown` —— Markdown → HTML
- `pypdf` —— 合并「封面 PDF + 正文 PDF」
- `pymupdf` —— 质检时把 PDF 页渲染成 PNG（仅验收用，可省）

浏览器：脚本自动探测
`C:\Program Files\Google\Chrome\Application\chrome.exe`，
回退 `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`。

mermaid 渲染库 `assets/mermaid.min.js`（v10.9.1）**首次运行会自动下载**，之后离线可用。

## 用法

### 单章

```bash
"$PY" scripts/build_chapter.py "<章节.md>" "<输出目录>" \
  --book "机器人编程基础" --school "深圳信息职业技术大学" \
  --author "郑洪英" --badge "学生版"
```

### 批量（章号区间）

```bash
"$PY" scripts/build_all.py "<md所在目录>" -o "<输出目录>" --from 1 --to 10 \
  --book "机器人编程基础" --school "深圳信息职业技术大学" \
  --author "郑洪英" --badge "学生版"
```

输出文件名 = 源 md 文件名换扩展名（便于对照）。默认输出目录为
`<md所在目录>/第A-B章_PDF`。10 章约 100 秒。

### 交付前验收（必做）

```bash
"$PY" scripts/verify_pdfs.py "<输出目录>" \
  --school "深圳信息职业技术大学" --author "郑洪英" --book "机器人编程基础"
```

逐份检查：A4 尺寸（595.28×841.89pt）、封面三段文字、**每页水印出现次数 ≥10**、
正文页码连续、无 Chrome 默认日期页眉、无空白页。有异常时退出码为 1。

### 需要目视确认时

```bash
"$PY" scripts/qa_pdf.py "<某个.pdf>" ch1 1 2 9   # 把第 1/2/9 页导出 PNG
```

再用 Read 工具看图核对（封面构图、mermaid 是否跨页、页脚大小）。

## 实现要点（改动前请先读）

1. **Markdown → HTML**：python-markdown，扩展 `extra`（含 tables/fenced_code/md_in_html）
   + `sane_lists`。首个 `#` 一级标题抽出来做封面章节名，正文里删掉避免重复。
2. **mermaid**：` ```mermaid ` 代码块先抽成占位符，转完 HTML 再还原成
   `<div class="mermaid">`，由本地 mermaid.js 渲染；渲染完成后按
   `MAX_W=640 / MAX_H=850`（px@96dpi）**等比缩小**兜底，防止高图跨页。
3. **打印**：`scripts/cdp_print.py` 是自写的 **CDP over WebSocket 客户端（纯标准库）**，
   启动 `chrome --headless=new --remote-debugging-port=0`，读 `DevToolsActivePort` 拿端口，
   用 `Target.createTarget` + `attachToTarget(flatten)` 开页，再发 `Page.printToPDF`。
   支持 `printBackground / displayHeaderFooter / footerTemplate / pageRanges / 页边距(inch)`。
4. **两趟打印 + 合并**：封面趟 `margins=0` + `pageRanges="1"`（满页出血、无页脚）；
   正文趟隐藏 `.cover` + 常规页边距 + `footerTemplate`（`<span class="pageNumber">` 自动填页码，
   从 1 起算）。最后 pypdf 合并。

## 踩过的坑（重要，别再犯）

| # | 现象 | 根因 | 正确做法 |
|---|------|------|----------|
| 1 | 页眉被打印出「日期 + 文档标题」 | CDP 里 `displayHeaderFooter=True` 但只给了 `footerTemplate`，Chrome 用默认页眉补齐 | 设置 `displayHeaderFooter` 时**同时**给 `headerTemplate`（可传 `<div></div>`） |
| 2 | 水印看不见（封面） | 水印层 `.wm{z-index:0}`，封面 `z-index:1` 且 `background:#fff`，被白底盖住 | 水印层 `z-index:900`，叠在内容之上（透明度 ~0.11 不影响阅读） |
| 3 | mermaid 图被拉得极长、跨页断裂（页数虚高） | 打印前先把 `.content` 设 `display:none` 再恢复，**已渲染的 SVG 尺寸失效被撑开** | **只隐藏 `.cover`**；封面改用 `pageRanges="1"` 取第一页，全程不动 `.content` |
| 4 | 图或代码块跨页断裂 | 长元素未做分页约束 | CSS：`pre/table/blockquote/.mermaid { break-inside: avoid }`，`h2~h4 { break-after: avoid }` |
| 5 | 代码块长行溢出页面 | 未换行 | `pre{white-space:pre-wrap; word-break:break-all}` |
| 6 | 以为 CLI `--print-to-pdf` 不能打印背景色 | 旧版 headless 的传闻 | 实测 Chrome 153 的 CLI 与 CDP **都能**打印背景（可用 zlib 解压 PDF 流搜 `rg` 填充色验证）；但 CLI 无法设 A4 / 自定义页脚，所以仍走 CDP |
| 7 | `pip install playwright` 卡住 | 轮子约 40MB，慢网下会长时间无响应 | 本方案**不需要** playwright；CDP 自写 100 行即可 |

## 目录结构

```
scripts/
  cdp_print.py       # 纯标准库 CDP/WebSocket 客户端 + print_pdf()
  build_chapter.py   # 单章：md→HTML→封面/正文两趟打印→合并；含封面/水印/正文全部 CSS
  build_all.py       # 批量（章号区间、复用同一 Chrome）
  verify_pdfs.py     # 交付验收（逐份逐页断言）
  qa_pdf.py          # PDF 页转 PNG，供目视核对
  make_html_dev.py   # 导出中间 HTML，便于用浏览器截图调版式
assets/              # mermaid.min.js（自动下载）
build/               # 中间产物：每章 HTML + 封面/正文 PDF
```

## 版式参数（改样式改哪里）

全部在 `build_chapter.py`：

- 品牌色：`INDIGO = #4f46e5`、`GOLD = #f59e0b`（靛蓝 + 琥珀金）
- 正文字体：宋体 11pt / 行距 1.85；标题：微软雅黑；代码：Consolas
- h2 左边框 6px 靛蓝 + 淡靛蓝渐变底；h3 左边框 3px 琥珀金
- 表格：表头淡靛蓝底（`#eef2ff`）+ 深靛蓝字，隔行 `#fafbff` —— **刻意用浅底深字**，
  万一背景打印被关掉也仍可读
- 水印：`WM_COUNT=12` 个，2 列网格，`rotate(-30deg)`，`rgba(79,70,229,.11)`
- 页边距：上 16mm / 下左右各 18mm

封面/水印文案统一走 `CFG` 字典，命令行 `--book/--school/--author/--badge/--watermark` 覆盖。

## 一句话总结

**python-markdown 转 HTML → 自写 CDP 客户端让 Chrome 打印两趟（封面满页 + 正文带页脚）→ pypdf 合并 → 自写断言脚本验收。**
不需要 playwright，不需要 LaTeX，不需要 LibreOffice。
