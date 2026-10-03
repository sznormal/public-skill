---
name: scanned-pdf-ocr
description: 读取扫描件 PDF（无文字层的图片型 PDF）并提取全文。当 Read 读 PDF 超限、pdfplumber/fitz 抽文本几乎为空、或 Read 读图片被过滤（模型不支持读图）时使用。触发场景：通知/公文/合同/教材/论文的扫描版 PDF 需要提取内容、核对表格数字、整理要点。含本地 RapidOCR 方案、表格数字的可靠性与"何时该直接问用户"的判据。
version: 1.0.0
agent_created: true
---

# 扫描件 PDF 读取（本地 OCR 方案）

## 何时触发

出现以下任一信号，说明 PDF 是**扫描件**（图片型，无文字层）：

- `Read` 直接读 PDF 报超限（页数多 / 文件大）
- 用 fitz/pdfplumber 抽文本，字符数**远小于预期**（如 41 页只出 1258 字符，且集中在个别页）
- 用 `Read` 读渲染出来的 PNG/JPG，返回 *"current model does not support images. Content filtered"*（当前模型不支持读图）
- 页面上明明是文字，但抽取结果是空白或乱码

**核心结论：扫描件的正确路径是本地 OCR，不是反复换工具读图。**

## 环境准备（一次性）

RapidOCR（PP-OCR 模型 + onnxruntime，纯 pip，无需 GPU，中文效果好）：

```bash
"C:/Users/29206/.workbuddy/binaries/python/envs/default/Scripts/pip.exe" install -q rapidocr-onnxruntime
```

常用配套（一般已装）：`pip install pymupdf opencv-python numpy`

> 不要用系统 Python / 全局 pip。固定用受管 venv：`C:/Users/29206/.workbuddy/binaries/python/envs/default/Scripts/python.exe`

## 标准流程

### 第 1 步：渲染页面为 PNG

```python
import fitz, os
doc = fitz.open(PDF)
os.makedirs(OUTDIR, exist_ok=True)
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=fitz.Matrix(140/72, 140/72))  # dpi=140 足够
    pix.save(os.path.join(OUTDIR, "p%02d.png" % (i+1)))
```

dpi 选择：**140 够用**（A4 约 1158×1638）。只有小字号表格需要更高（300+）。

### 第 2 步：全量 OCR 落盘（必须落盘，不要只打到 stdout）

```python
import os, io
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")   # 防 onnxruntime 冲突
from rapidocr_onnxruntime import RapidOCR
engine = RapidOCR()
with io.open(OUT, "w", encoding="utf-8") as fo:
    for f in sorted(files):
        result, _ = engine(os.path.join(SRC, f))
        fo.write("\n\n===== %s =====\n" % f)
        for box, text, score in (result or []):
            fo.write(text + "\n")
        fo.flush()          # 逐页 flush，中断也不丢
```

实测速度：**41 页 / 约 4 分钟**。跑在后台（`run_in_background=true`），完成后一次性 Read 全文。

### 第 3 步：带坐标重构表格（需要按行/列对齐时）

RapidOCR 返回 `[box, text, score]`，box 是四角坐标。按 y 中心聚类成行、按 x 排序成列，即可还原表格：

```python
items = [(sum(p[1] for p in box)/4, min(p[0] for p in box), text) for box, text, sc in result]
items.sort()
rows, cur, last_y = [], [], None
for y, x, t in items:
    if last_y is None or y - last_y <= 18:   # 容差按行高调
        cur.append((x, t))
    else:
        rows.append(cur); cur = [(x, t)]
    last_y = y
for r in sorted(rows, key=lambda r: r[0][0]):
    print(" | ".join("%s[x=%.0f]" % (t, x) for x, t in sorted(r)))
```

## 坑位清单

| # | 坑 | 现象 | 处置 |
|---|---|---|---|
| 1 | `cv2.imwrite` 中文路径 | **静默失败**，文件不存在 | 直接把 ndarray 传给 `engine(img_array)`；或 `cv2.imencode('.png', img)[1].tofile(path)` |
| 2 | score 是字符串 | `TypeError: type str doesn't define __round__` | `float(score)` |
| 3 | onnxruntime 冲突 | 加载模型时报 DLL 错 | 设环境变量 `KMP_DUPLICATE_LIB_OK=TRUE` |
| 4 | Bash 里 `/tmp` | 被解析成 `d:/tmp` | 临时脚本写项目 `.workbuddy/` 下，用绝对路径 |
| 5 | 表格数字漏识 | 同一行两个数字被合并成一个 token；或小字号数字整列读不出 | 数字列**裁剪 + 放大 4-5 倍**再 OCR；先做墨迹聚类定位单元格位置 |
| 6 | 竖线干扰 | 单元格数字被表格边线污染，OCR 认不出 | 先把长竖线整列涂白（ink 占比 > 0.5×行高 的列），再聚类识别 |
| 7 | `Read` 读图被过滤 | 模型不支持读图 | 不要在这条路上反复试，直接走本地 OCR |
| 8 | 数字被误读 | 面积小、笔画细的数字（1/7、3/8）易错 | 关键数字**交叉验证**：列求和 vs 总数行、多处出现的一致性 |

## 可靠性判据（重要）

**OCR 对正文可靠，对表格数字不可靠。**

- 正文段落、标题、条款：可靠，可直接引用。
- 表格中的**关键数字**（金额、名额、分数、日期）：**必须交叉验证**；若连试 2-3 种策略（裁剪放大 / 墨迹聚类 / 竖线涂白）仍读不稳，**直接问用户**。

> 实战教训：为读一页 81 行名额表的数字列，连续尝试 4 种策略（全页坐标、高清裁剪、分列条带、墨迹聚类）仍未可靠读出，最后用户一句话给出答案——**问用户比 OCR 快一个数量级**。不要为表格数字陷入长时间工具循环。

## 交付检查

- [ ] 全文落盘为具名 txt（含页码分隔符 `===== pXX.png =====`），换会话可复核
- [ ] 渲染图保留在 `<项目>/.workbuddy/<名字>_png/`，便于回溯定位
- [ ] 引用关键条款时标注**页码**，便于用户回查原文件
- [ ] 关键数字已交叉验证，或明确标注"OCR 未能可靠识别，需人工确认"

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
