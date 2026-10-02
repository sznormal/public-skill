# 排版规范（唯一权威来源）

本文件是本技能所有文档类型的排版基线，`SKILL.md` 与各工作流文件只引用本文件，不重复维护同一条规则。
下表为**默认值**（取自深圳信息职业技术大学校版模板）；用户提供本校模板时，一切以模板实际提取值为准。

## 一、《课程标准》

| 元素 | 字体 | 字号 | 对齐 | 首行缩进 |
|---|---|---|---|---|
| 标题《XXX》课程标准 | 黑体 | 22pt（二号） | 居中 | 顶格 |
| 一级（一、二、…八、） | 黑体 | 16pt（三号） | 左 | **顶格** |
| 二级（（一）（二）、教材使用等） | 楷体 | 16pt（三号） | 左 | **2 字符** |
| 正文 / 编号子标题(1.x) / 表格 | 仿宋 | 16pt（三号） | 左 | **2 字符** |
| 头部信息栏 | 标签=仿宋三号**加黑**；值=仿宋三号**不加黑** | 16pt | 左 | 顶格 |
| 表格标题（学时分配表等） | 仿宋 | 16pt | 居中 | 顶格 |

行距固定值 28 磅（EXACTLY），段前段后 0。

## 二、教案 / 授课计划

| 区域 | 字体 | 字号 | 其他 |
|---|---|---|---|
| 封面标题 | 方正公文小标宋 / 华文中宋 | 22–26pt | 居中 |
| 封面填写值 | 楷体_GB2312 | 15pt（小三） | 加下划线，居中 |
| 教案表头标签 | 黑体 | 14pt | 左 |
| 教案"教学目的及要求"等小标题 | 楷体 | 14pt | 左 |
| 教案表格填写值 | 仿宋_GB2312 | 14pt（四号） | 首行缩进 2 字符，单倍行距 |
| 授课计划 表格0 填写值 | 楷体_GB2312 | 12pt | 左对齐 |
| 授课计划 周次表填写值 | 仿宋_GB2312 | 10pt | 日期/课型/时数/平台居中；内容/作业左对齐 |

## 三、字号与字体族对照

| 字号名 | pt | 字体族 | 用途 |
|---|---|---|---|
| 二号 | 22 | 黑体 | 课标标题（22pt）、一级标题与教案表头标签（14pt） |
| 小二 | 18 | 楷体 / 楷体_GB2312 | 课标二级标题、教案小标题、封面填写值、授课计划表格0 |
| 三号 | 16 | 仿宋 / 仿宋_GB2312 | 课标正文与表格、教案表格填写值、周次表填写值 |
| 小三 | 15 | 方正公文小标宋 / 华文中宋 | 教案与授课计划封面标题 |
| 四号 | 14 | | |
| 小四 | 12 | | |
| 五号 | 10.5 | | |

## 四、字重与编号体例

**字重规则**：黑体/楷体/仿宋靠字体名本身区分层级，生成时一律 `bold=False`；
**唯一例外——头部信息栏标签显式 `bold=True`**（仿宋加黑）。

编号体例：

- 教学目标段：`#1、素质目标` / `（1）（2）（3）`（行首 `#` 表示该行顶格，渲染时必须剥离 `#`）
- 重点 / 难点：`1、2、3、`
- 教学过程：`第X学时（40分钟）：` → `一、二、三`（标分钟数）→ `1. 2. 3.`
- 周次表内容提要：`讲解：1.…；2.…。` + 换行 + `实验：…`

## 五、跨文档硬规则

1. **首行缩进最易漏**：一级顶格、其余 2 字符，必须显式设置。用 `w:firstLineChars="200"`（随字号自适应），**勿用固定 twips**。
2. **生成新文件，绝不覆盖用户模板**：用户常开着 Word，覆盖会损坏会话。
3. **标题必须在表格上方**：插入"标题+表格"块时先放标题再放表格，调用 `scripts/docx_helpers.py` 的 `insert_heading_table_before()`，生成后回读核对顺序。
4. **往 body 追加表格不能用 `body.append()`**：`w:sectPr` 是 body 末元素，`append()` 会把表格插到它之后（无效位置）。用 `body.find(qn('w:sectPr')).addprevious(tbl)`；`doc.add_table()` 已内部处理，可放心用。
5. **合并单元格取值去重**：python-docx 的 `row.cells` 会重复返回合并格，用 `value_cell(row)` 按去重文本取"标签格之后的值格"。
6. **中文字体必须设 `w:rFonts/@w:eastAsia`**：`run.font.name` 只改西文，对中文无效。
7. **写入单元格先裁剪再写**：先删 `cell.paragraphs[1:]`，再用第 0 段写首行、其余 `add_paragraph()`。若"先写后按行数裁剪"，模板遗留空段会把最后一行正文顶出范围而被删掉。
8. **模板里藏有括号提示文字**：模板正文含"（需包括但不限于以下内容：）""（采用的教学模式特别是…）"等提示，生成前必须逐条删除。
9. **带标签行与空值格的处理方式不同**：带标签的单元格（教学目的、重点、难点、教具、课后作业、线上作业）保留标签行只写值行；空单元格（教学单元值、周次/时数/班级、资源、在线环节、答疑）整体覆盖。
10. **不擅自改写领域术语**：软件名、书名、型号以用户原文为准。

## 六、先从模板提取实际规范（不要假设）

```python
from docx import Document
from docx.oxml.ns import qn

doc = Document(template_path)

for i, p in enumerate(doc.paragraphs):                       # 段落格式
    if p.text.strip():
        runs = [(r.text, r.font.name, r.font.size.pt if r.font.size else None,
                 r.font.bold, r.font.underline) for r in p.runs]
        print(i, repr(p.text[:30]), p.alignment, runs)

for ti, tb in enumerate(doc.tables):                         # 表格结构（合并格去重）
    print('TABLE', ti, len(tb.rows), 'x', len(tb.columns))
    for ri, row in enumerate(tb.rows):
        uniq = []
        for c in row.cells:
            t = c.text.strip().replace('\n', '/')
            if not uniq or uniq[-1] != t:
                uniq.append(t)
        print(ri, '|', ' || '.join(uniq)[:120])

rPr = run._element.get_or_add_rPr()                          # 中文字体在 eastAsia
print(rPr.get_or_add_rFonts().get(qn('w:eastAsia')))
```

旧版 `.doc`（OLE2 二进制）先用 `scripts/doc_extract.py` 提取文本再比对。

## 七、python-docx 操作函数（`scripts/docx_helpers.py`）

| 函数 | 用途 |
|---|---|
| `set_run_font(run, name, size, bold, underline)` | 设中文字体（eastAsia）+ 字号 + 字重 + 下划线 |
| `set_first_line_chars(p, chars, size_pt)` | 首行缩进 N 字符（写 `w:firstLineChars`，随字号自适应） |
| `set_exact_line_spacing(p, pt)` | 固定行距（课标正文用 28 磅） |
| `clear_cell(cell)` | 清空单元格多余段落与 run，返回可写首段 |
| `value_cell(row)` | 合并单元格按去重文本取"标签格之后的值格" |
| `strip_cell(cell, keep_label)` | 删除模板占位段；`keep_label=True` 时保留带标签首段 |
| `write_cell(cell, lines, **kw)` | 覆盖式写入（空值格用） |
| `append_cell(cell, lines, **kw)` | 追加式写入（带标签格用，保留标签行） |
| `insert_heading_table_before(doc, anchor, title, rows, ...)` | 插入"标题+表格"块，标题恒在表格上方 |
| `drop_element(el)` | 从 XML 树移除元素 |
| `dump_tables(doc)` | 打印全部表格结构，动手前定位行/列 |

## 八、渲染验证

```python
import pymupdf                       # 可选：PDF 逐页渲染成图逐页看
doc = pymupdf.open(pdf_path)
for i in range(doc.page_count):
    doc[i].get_pixmap(dpi=100).save(f'page_{i+1}.png')
```

LibreOffice 转 PDF 时指定可写 profile：
`soffice -env:UserInstallation=file:///<可写目录>/lo_profile --headless --convert-to pdf --outdir <输出目录> <docx>`

逐页检查：字体是否生效（楷体/仿宋）、下划线、缩进、表格列宽与内容截断、跨页断行。
格式检查的确定性做法是用 `scripts/validate_docx.py` 回读 XML，逐项比对字体族、字号、首行缩进与行距。
