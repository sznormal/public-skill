---
name: office-readback-verify
description: >
  零依赖读取 Office 文件（docx/xlsx/pptx）＋ 对"写入结果"做逐格回读校验，确保委派写入没有静默失真。
  触发场景：
  (1) 需要读取 .docx / .xlsx / .pptx 内容，但 managed Python 环境没有 python-docx / openpyxl；
  (2) 委派子代理或 MCP 工具（sheetagent / tencent-docs 等）写入 Excel、Word 之后，需要验证写入是否忠实；
  (3) 交付前需要证明「表格数据 = 源数据」，做逐格比对而非只数行数；
  (4) 关键词：回读校验 / 逐格比对 / 单元格比对 / 写入验证 / 读docx / 读xlsx / 无依赖读Office /
      readback / cell-level diff / verify xlsx / no-dependency office reader。
version: 1.0.0
agent_created: true
---

# Office 文件无依赖读取 与 写入回读校验

## 为什么需要这个 skill

两条实测踩坑，靠常规做法发现不了：

1. **委派写入会静默改写标点。** 实测把 CSV 中 855 个单元格写入 xlsx，写入工具把 2 个单元格里的
   中文全角引号 `“` `”`（U+201C/U+201D）改成了半角直引号 `"`。**只数行数、只对行数列数，一个都查不出来。**
2. **managed Python 没有 Office 库。** `import docx` / `import openpyxl` 直接 ModuleNotFoundError，
   而临时装 venv 又慢又容易坏（见 `html-to-docx-on-windows`）。

OOXML 本质是 zip + XML，标准库 `zipfile` + `xml.etree` 足够，秒级可用、零安装。

## 脚本

| 脚本 | 用途 |
| --- | --- |
| `scripts/read_office.py` | 读取 docx（段落＋表格）/ xlsx（逐行逐格）/ pptx（逐页文本） |
| `scripts/verify_xlsx.py` | xlsx ↔ CSV/JSON **逐格比对**；`--structure` 只看结构不比对 |

统一用 managed Python 调用：

```bash
PY="C:/Users/29206/.workbuddy/binaries/python/versions/3.13.12/python.exe"
SK=~/.workbuddy/skills/office-readback-verify/scripts
```

### 读取

```bash
"$PY" "$SK/read_office.py" 文件.docx                 # 直接打印
"$PY" "$SK/read_office.py" 文件.docx --out out.txt   # 落盘（长文档必用，省上下文）
"$PY" "$SK/read_office.py" 表格.xlsx --out out.txt
```

- docx 表格输出为 `[TABLE]` / `[/TABLE]` 包裹，单元格以 ` | ` 分隔。
- xlsx 输出 `=== SHEET 表名 (路径) ===`、`MERGED: ...`、`ROW 3 A3='...' | B3='...'`。

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

## 硬规则

- **写入类委派一律以逐格比对收尾**，不得只凭子代理回执或行数统计验收。
- 修复偏差时**只改受影响单元格**，并要求"其余单元格保持原值、不得插行删行"；改完必须再比对一次。
- 若模板有必须保留的横幅/表头行（如合并单元格说明行），在委派指令里**明确点名"原样保留、不得改动"**。
- **不要覆盖用户的原始模板**：先 `cp` 成独立副本再写入，交付副本，原件保持不动。
- 源数据留档（CSV + 生成脚本 + 校验脚本放同一目录），便于将来重跑与版本比对。

## 已知环境坑

- **sheet-agent 的路径校验要求以 `/` 开头**：Windows 绝对路径 `D:\...` 会被拒绝。
  实际生效的 `file_id` 形如 `/BaiduSyncdisk/workbudy/.../xxx.xlsx`，`sheet_id` 通常是 `000001`。
  委派时把 Windows 路径与 file_id 两种写法都给到子代理。
- **子代理只拿到你写进指令的字面值**。所以源数据必须落成文件并传路径，不要指望它"理解上下文"。
- 长文档一律 `--out` 落盘再按需读取，避免把全文灌进上下文。

## 复用示例（本 skill 的诞生场景）

给 Excel 模板填知识图谱：57 行 × 15 列、
先用 `read_office.py` 实测模板骨架（发现第 1 行是 A1:O1 合并说明横幅、第 3–4 行是示例数据须删）、
把数据落成 `kg_rows.csv`、委派表格子代理写入、
最后 `verify_xlsx.py` 逐格比对——首轮揪出 2 处引号失真，修复后复验 exit 0。
