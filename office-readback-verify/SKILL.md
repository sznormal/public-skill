---
name: office-readback-verify
description: >
  零依赖读取 Office 文件（docx/xlsx/pptx）与 PDF（含 LaTeX 排版产物）＋ 对"写入/构建结果"做逐格、逐字段回读校验，
  确保委派写入或模板渲染没有静默失真。
  触发场景：
  (1) 需要读取 .docx / .xlsx / .pptx 内容，但 managed Python 环境没有 python-docx / openpyxl；
  (2) 委派子代理或 MCP 工具（sheetagent / tencent-docs 等）写入 Excel、Word 之后，需要验证写入是否忠实；
  (3) 交付前需要证明「表格数据 = 源数据」，做逐格比对而非只数行数；
  (4) 编译出 PDF（pdflatex/journal 模板/HTML 打印）后，需要证明「页面上真的渲染出了作者栏、邮箱、关键字段」，
      而本机没有 pdftotext / poppler；
  (5) 关键词：回读校验 / 逐格比对 / 单元格比对 / 写入验证 / 读docx / 读xlsx / 读pptx / 读PDF /
      无依赖读Office / 读PDF文字层 / PDF文本提取 / 校验PDF渲染 / pdftotext 替代 /
      readback / cell-level diff / verify xlsx / verify pdf text layer / no-dependency office reader。
version: 1.1.0
agent_created: true
---

# Office 文件无依赖读取 与 写入回读校验

## 为什么需要这个 skill

三条实测踩坑，靠常规做法发现不了：

1. **委派写入会静默改写标点。** 实测把 CSV 中 855 个单元格写入 xlsx，写入工具把 2 个单元格里的
   中文全角引号 `“` `”`（U+201C/U+201D）改成了半角直引号 `"`。**只数行数、只对行数列数，一个都查不出来。**
2. **managed Python 没有 Office 库。** `import docx` / `import openpyxl` 直接 ModuleNotFoundError，
   而临时装 venv 又慢又容易坏（见 `html-to-docx-on-windows`）。
3. **PDF 构建"成功"不等于渲染正确。** 日志里 `Output written` 正常、零 fatal，但页面上的作者栏/
   邮箱/脚注可能仍是占位符或排版错位；而本机往往**没有 pdftotext**（poppler 不在 TinyTeX 里）。

OOXML 本质是 zip + XML，PDF 内容流是 zlib 压缩的文本算子流——标准库 `zipfile` / `xml.etree` /
`re` / `zlib` 足够，秒级可用、零安装。

## 脚本

| 脚本 | 用途 |
| --- | --- |
| `scripts/read_office.py` | 读取 docx（段落＋表格）/ xlsx（逐行逐格）/ pptx（逐页文本） |
| `scripts/verify_xlsx.py` | xlsx ↔ CSV/JSON **逐格比对**；`--structure` 只看结构不比对 |
| `scripts/read_pdf.py` | 读取 **PDF 文本层**（无 pdftotext 时的替代），支持 `--find` / `--grep` |

统一用 managed Python 调用：

```bash
PY="$HOME/.workbuddy/binaries/python/versions/3.13.12/python.exe"   # Git Bash；Windows 原生 shell 写完整盘符路径
SK=~/.workbuddy/skills/office-readback-verify/scripts
```

（旧版此处写死过某个具体用户名下的绝对路径，换机即失效；用 `$HOME` 可跨机复用。）

### 读取

```bash
"$PY" "$SK/read_office.py" 文件.docx                 # 直接打印
"$PY" "$SK/read_office.py" 文件.docx --out out.txt   # 落盘（长文档必用，省上下文）
"$PY" "$SK/read_office.py" 表格.xlsx --out out.txt
```

- docx 表格输出为 `[TABLE]` / `[/TABLE]` 包裹，单元格以 ` | ` 分隔。
- xlsx 输出 `=== SHEET 表名 (路径) ===`、`MERGED: ...`、`ROW 3 A3='...' | B3='...'`。

### 读取 PDF 文本层（构建产物回读）

编译出 PDF 之后，**用它证明页面上真的渲染出了该有的内容**（作者栏、邮箱、单位、脚注、页眉短名）：

```bash
"$PY" "$SK/read_pdf.py" 论文.pdf                      # 全部文本
"$PY" "$SK/read_pdf.py" 论文.pdf --grep "邮箱" "姓名" "单位"   # 命中报告（OK/MISSING）
"$PY" "$SK/read_pdf.py" 论文.pdf --find "关键词"        # 打印关键词周边 900 字上下文
```

原理：抽 `stream…endstream` → `zlib.decompress` → 解析内容流里的 `(...)` 字面串与 `<hex>` 串，
把 `Td/TD/T*/ET` 当换行。`--grep` / `--find` 匹配前**统一去除所有空白**，以抵抗字距与连字造成的假阴性。

**必须知道的读取假象（都是提取器的锅，不是 PDF 的错）：**

- **字距会拆词**：`Sino-GermanRoboticsSchool`、`Hongying Zheng` 可能变成 `HongyingZheng`。
- **ff/fi 连字会吞字符**：`scientific` 显示为 `scientic`、`verifiability` 显示为 `veri"ability`，
  `set off` 显示为 `set o`。按这些字符串 grep 计数会得到 0——**别据此判定"内容缺失"**。
- 结论：**要用"去空白后子串匹配"判断有无**，不要用原样 `grep -c`。

### 结构探测（写入前先做，确认模板骨架）

```bash
"$PY" "$SK/verify_xlsx.py" 目标.xlsx --structure --start-row 3 --ncols 15
```

输出：工作表名、**合并单元格**、最大行号、数据行数、表头行、首数据行、末行、**中间空行**。
先看合并单元格（例如说明横幅 `A1:O1` 不能丢）、再看中间有没有空行（模板常要求"中间不可为空/不可跳级"）。

### 逐格比对（写入后必做）

```bash
"$PY" "$SK/verify_xlsx.py" 目标.xlsx 源数据.csv --start-row 3 --ncols 15
```

- 源 CSV 首行若与表头行一致会自动跳过；也可传 JSON 二维数组。
- 输出差异格清单（行/列/期望/实际）＋差异格数。
- **退出码 0 = 零差异；1 = 有差异。** 可直接用于流程判定。
- 差异格会逐字符显示，全角/半角、空格、全角逗号等肉眼难辨的失真一目了然。
- 附加能力：行数不一致时会先报 `⚠️ 行数不一致：源 N 行 vs 表 M 行`。

## 标准工作流

1. **先摸清目标文件骨架** → `--structure`：记住合并区、表头行号、示例数据行号、列数。
2. **准备源数据在文件里**（CSV/JSON，不要只放在上下文里）：这样源数据可复现、可比对。
3. **写入**（委派子代理或 MCP 工具）。
4. **逐格回读比对** → 有差异就精确修复受影响单元格，再比对一次，直至 **exit 0**。
5. **不要在没跑第 4 步的情况下宣称"写入完成"。** 子代理的自我报告描述的是它的意图，不等于磁盘事实。

**构建/渲染类产物（PDF）走同一条纪律：**

1. 改**生成器源头**（如 `md2jair.py` 的 PREAMBLE），不要只改产物 `.tex`——改产物下次重跑就被覆盖。
2. 重跑生成器 → 编译（`pdflatex → biber → pdflatex ×2`）。
3. 查日志：`grep -c '^!'`（fatal）、`undefined`、`Output written on … (N pages)`、`.bbl` 条目数。
4. **回读页面**：`read_pdf.py --grep` 点名要验证的字段（姓名、邮箱、单位、脚注标记）。
5. 顺带扫生成物里 `TODO-` / `example.edu` / 旧机构名等**占位残留计数必须为 0**。
6. 只有第 4、5 步都过，才说"渲染正确"。

## 硬规则

- **写入类委派一律以逐格比对收尾**，不得只凭子代理回执或行数统计验收。
- **排版/编译类产物一律以"页面文本层回读"收尾**，不得只凭编译日志无报错就宣称渲染正确。
- 修复偏差时**只改受影响单元格**，并要求"其余单元格保持原值、不得插行删行"；改完必须再比对一次。
- 若模板有必须保留的横幅/表头行（如合并单元格说明行），在委派指令里**明确点名"原样保留、不得改动"**。
- **不要覆盖用户的原始模板**：先 `cp` 成独立副本再写入，交付副本，原件保持不动。
- 源数据留档（CSV + 生成脚本 + 校验脚本放同一目录），便于将来重跑与版本比对。

## 已知环境坑

- **`pdftotext` / poppler 通常不存在**，TinyTeX 里也没有。不要为了读 PDF 文本去装 poppler，直接用 `read_pdf.py`。
- **模板默认值 ≠ 未填的占位符**。看到页脚出现 `Vol. 4, Article 6`、`Insert <AE Name>`、`10.1613/jair.1.xxxxx`
  这类"像占位符"的字符串，**先回查官方模板原文**再判定。实测 JAIR 模板第 25–30 行就是这几个值，
  由编辑部排版时赋值，作者不需要改——**判据是模板逐行同源，不是"看起来像"**。
- **邮箱里的下划线不用转义**：acmart 的 `\email` 内部走 `\nolinkurl`（见 `acmart.cls`），
  `2013100896@suit-sz.edu.cn` 直接写在 `\email{}` 里即可，写 `\_` 反而错。
- **sheet-agent 的路径校验要求以 `/` 开头**：Windows 绝对路径 `D:\...` 会被拒绝。
  实际生效的 `file_id` 形如 `/BaiduSyncdisk/workbudy/.../xxx.xlsx`，`sheet_id` 通常是 `000001`。
  委派时把 Windows 路径与 file_id 两种写法都给到子代理。
- **子代理只拿到你写进指令的字面值**。所以源数据必须落成文件并传路径，不要指望它"理解上下文"。
- 长文档一律 `--out` 落盘再按需读取，避免把全文灌进上下文。
- **同步盘目录下"个别文件写不进去、同目录其他文件正常"**：先查有没有 `*.baiduyun.uploading.cfg` 伴随文件，
  直接 `taskkill //F //IM baidunetdiskhost.exe`（只杀上传工作进程，主程序不受影响），等 3–5 秒句柄释放后重试。
  诊断用 `ctypes` 调 `CreateFileW(path, GENERIC_WRITE, dwShareMode=0, …)` 取错误码：
  `ERROR_SHARING_VIOLATION(32)` = 有进程占句柄；`ERROR_ACCESS_DENIED(5)` = 权限/ACL；`ERROR_FILE_NOT_FOUND(2)` = 路径错。
  别浪费时间查 ACL——本次四个文件 ACL 完全一致却只有一个写不进。先写 `.new` 再 `os.replace` 的绕法**同样无效**。

## 复用示例

**例 1（写入类，本 skill 的诞生场景）** 给 Excel 模板填知识图谱：57 行 × 15 列、
先用 `read_office.py` 实测模板骨架（发现第 1 行是 A1:O1 合并说明横幅、第 3–4 行是示例数据须删）、
把数据落成 `kg_rows.csv`、委派表格子代理写入、
最后 `verify_xlsx.py` 逐格比对——首轮揪出 2 处引号失真，修复后复验 exit 0。

**例 2（构建类）** 期刊投稿 PDF 的作者栏落盘：把三位作者与邮箱写进 `md2jair.py` 的 PREAMBLE（源头）→
重跑生成器 → `pdflatex → biber → pdflatex ×2`（29 页 / fatal=0 / undefined=0）→
`read_pdf.py --grep` 点名验证 `hyzheng@126.com`、`2013100896@suit-sz.edu.cn`、`Corresponding Author`、
单位串与页眉短名，全部 OK，并确认生成物里占位符与旧机构名计数为 0。
期间正是用 `--find` 读到页脚上下文，才发现 `Vol. 4, Article 6` 一类"像占位符"的值其实是模板默认值——
**回查模板原文才避免误报**。
