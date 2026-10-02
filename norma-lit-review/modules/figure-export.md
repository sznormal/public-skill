# 图稿矢量导出（SVG → PDF / EPS）

> 适用场景：综述定稿后、按目标刊投稿前，把 `figures/*.svg` 导出为期刊接受的矢量格式。
> 三大目标刊（JAIR / Springer AIRC / Elsevier KBS）均接受 **PDF 或 EPS** 矢量图。
> 现成脚本：`outputs/lit-review/figures/export_svg_to_pdf.py`（PDF）与
> `export_svg_to_eps.py`（EPS），可整目录复用。

## 通道一：SVG → PDF（首选，保真度最高）

- 工具链：**Playwright + Chromium**（`pip install playwright && playwright install chromium`，约 115 MB）。
- 原理：SVG 内嵌进 `@page { size: <viewBox宽>pt <viewBox高>pt; margin:0 }` 的 HTML，
  `page.pdf(prefer_css_page_size=True)` 输出**页面尺寸=图幅**的矢量 PDF，字体内嵌子集。
- **禁止用 cairosvg**：Windows 无 `libcairo-2.dll`，pip 装上也必然 `OSError` 导入失败（实测）。
- Playwright API 三个坑（实测）：`margin` 四项必须是**字符串** `"0"`；`device_scale_factor`
  是 `new_context()` 参数、不是 `screenshot()` 参数；校验截图含视口留白，**不代表 PDF 页面**。
- 校验闭环：PyMuPDF（`pip install pymupdf`）打开 PDF → 打印页面尺寸（应=图幅 pt）与
  内嵌字体表 → `get_pixmap(dpi=110)` 渲染 PNG 肉眼验收。

## 通道二：SVG → EPS（svglib + reportlab，纯 Python）

- 工具链：`pip install svglib reportlab`；`svg2rlg → renderPS.drawToFile` 出 EPSF-3.0。
- 尺寸换算：svglib 按 96dpi→72pt 把 viewBox 680px 映射为 **510pt** 宽，纵横比不变，期刊排版无影响。
- **svglib 不支持 `<marker>`**：箭头会整体消失。修复法（见脚本 `arrow_polygons()`）：
  逐条 `marker-end` 线段按 marker 几何（`M0,0 L7,3 L0,6`，`markerUnits=strokeWidth`，
  refX=7 使 **tip 落在线段终点**）× 线宽展开为显式 `<polygon>`，插入 `</svg>` 前。
  轴对齐（竖直向下/水平向右）以外方向需人工处理。
- **中文字体两个坑**：
  1. svglib **无逐字回退**：`font-family="'Segoe UI','Microsoft YaHei',sans-serif"` 中
     Segoe UI 无 CJK，中文文本元素必须在 EPS 变体里把字体族改写为单一 CJK 字体
     （reportlab 侧 `register_font("Microsoft YaHei", C:/Windows/Fonts/simhei.ttf)`）。
  2. **双名注册**：svglib 会按 TTF 内部名（SimHei）引用，`renderPS` 保存时按内部名
     `getFont`，故 `Microsoft YaHei` 与 `SimHei` 两个名字都要在 pdfmetrics 注册，否则
     `KeyError: 'SimHei'`。SimHei 单字重，EPS 变体需去掉 `font-weight="700"` 防黑方块。
- **注册 CJK 会污染全局回退**：一旦注册，svglib 对英文图未解析字体的回退从 Helvetica
  变成等宽字体，文字撑出框。**必须先零注册跑英文图、最后注册 CJK 跑中文图**。
- 英文图回退 Helvetica 是可接受甚至优选（期刊标准字体）；校验时重点看文字是否溢出框。

## 纪律

- **原始 SVG 一律不改**：箭头展开、字体族改写、去粗体都写进 `*_epssrc.svg` 变体。
- 每张 EPS/PDF 必须**渲染成 PNG 肉眼验收**后才算交付（结构校验 BoundingBox 只是底线）。
- 百度同步盘会短暂锁文件（EBUSY/Permission denied）：校验产物写子目录（如 `eps_check/`），
  遇锁换文件名重试即可。
- 已知图源问题：`trend.svg`（中文图1）四个阶段标签为白字但 y 坐标在色柱上方外侧（白底白字
  不可见）；英文变体 `trend_en.svg` 已把标签放柱内修正，**中文原件待 Norma 老师确认后再修**。
