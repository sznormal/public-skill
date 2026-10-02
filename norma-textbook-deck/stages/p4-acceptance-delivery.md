# P4 · 三重验收 + 导出 + 交付

> norma-textbook-deck · Stage 04
> 目的：交付前把整份 deck 验一遍，导出 pptx，把三件套落到教材目录。

---

## 一、三重验收（缺一不可）

### 验收 1 · 服务端页数 + 顺序

```
lark-cli slides +xml-get --as user --presentation "<id>" > server_full.xml
```

用 python 解析，核对：
- `<slide>` 数量 == `planned_pages`（多了就是重复页，删掉）
- 每页标题顺序与 `slide_plan.json` 一致

### 验收 2 · 全文 lint = 0 错

**关键**：`+xml-get` 的输出是 **JSON 包裹**，正文在 `data.xml_presentation.content`。
**不能**直接把 JSON 文件喂 `xml_lint.py`（会报 `not well-formed`）。先抽出纯 xml：

```python
import json
d = json.load(open('server_full.xml', encoding='utf8'))
open('server.xml','w',encoding='utf8').write(d['data']['xml_presentation']['content'])
```

再 `xml_lint.py --input server.xml`，确认 `error_count=0`（warning 可接受）。

### 验收 3 · pptx 完整性

导出后用 zipfile 三重确认：
- `testzip()` 返回 `None`（无损坏）
- `ppt/slides/slide*.xml` 数量 == 计划页数
- `ppt/media/` 数量 == 配图数量

## 二、导出 pptx

```
lark-cli drive +export --as user --token "<id>" --doc-type slides --file-extension pptx \
  --output-dir "." --file-name "第N章_<章名>" --overwrite
```

再用 python `shutil.copy` 把 pptx 复制到教材 md 同目录（不用 shell 重定向，避免编码问题）。

## 三、交付三件套

| # | 交付物 | 位置 |
|---|---|---|
| 1 | 飞书在线幻灯片链接 | `+create` 返回的 url |
| 2 | `第N章_<章名>.pptx` | 教材目录 |
| 3 | `第N章_<章名>_实例代码.txt` | 教材目录 |

## 四、输出 schema

```json
{
  "deck": { "submitted_pages": 25, "revision_id": 28 },
  "acceptance": { "page_count_ok": true, "full_lint_errors": 0, "pptx_integrity": true },
  "artifacts": { "pptx": "第N章_xxx.pptx", "code_txt": "第N章_xxx_实例代码.txt", "url": "" },
  "stages": { "P4_acceptance": true }
}
```

同时更新 `deck-state.json` 与项目 memory。

## 五、Hard Stop · 交付确认单

```
╭─ P4 验收 + 交付 完成 ────────────────────────╮
│ ✅ 验收 1 页数顺序：{N}/{N} 页，无重复
│ ✅ 验收 2 全文 lint：0 错（{W} warn）
│ ✅ 验收 3 pptx：zip 正常 / {N} 页 / {M} 图
│ 📦 交付三件套：
│    1. 在线：{url}
│    2. pptx：{文件名}（{大小}）
│    3. 代码：{文件名}
│ 📁 教材目录已更新
│ 👉 还需要改哪页？说页码即可；否则本章完成。
╰──────────────────────────────────────────╯
```

最后用 **present_files** 一次性交付：在线链接 + pptx + 代码 txt。

**等用户确认才推进**：本阶段为流程终点；若用户在验收中发现需改的页面，回退 P3 修改后重跑本阶段验收，不得跳过验收直接交付。
