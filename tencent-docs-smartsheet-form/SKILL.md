---
name: tencent-docs-smartsheet-form
description: 用腾讯文档（docs.qq.com）把一份题目清单做成**可在线填报的问卷**——走「智能表格 + 表单视图」路线，自动建字段（题目）、选项、表单视图并校验。触发场景：用户要把测评/问卷/报名表/收集表做成腾讯文档在线问卷、要"在线收集答题数据"、要把一份 xlsx 题库挂到腾讯文档让学生填。触发词：腾讯文档在线问卷、腾讯文档表单、智能表格表单、把题目做成在线问卷、在线收集答卷。注意：腾讯文档「收集表」(form) 无法用 API 写入题目，本 skill 给出唯一可行路径与其全部坑位。
version: 1.0.0
agent_created: true
---

# 腾讯文档在线问卷：智能表格 + 表单视图

## 第一原则（先看这条，能省一小时）

**腾讯文档「收集表」(`file_type:"form"`) 用 API 建不出带题目的表单。**

`manage.create_file` 确实支持 `file_type:"form"`，但服务端**没有对应的表单内容编辑工具**（无 `form.add_question` 之类），只能建出一个空表。

**唯一可编程落地的在线问卷形态 = 智能表格（smartsheet）+ 表单视图（`view_type:"form"`）。**
学生打开表单填写提交 → 每条答卷自动落成智能表格的一行 → 可直接导出分析。效果与收集表等价。

```
manage.create_file(file_type="smartsheet")   → 建文档
smartsheet.list_tables                       → 拿 sheet_id
smartsheet.list_fields / update_fields       → 改主字段名、删示例字段
smartsheet.add_fields                        → 建字段（= 题目）
smartsheet.add_view(view_type="form")        → 建表单视图
```

---

## 调用方式

腾讯文档能力分散在 4 个 MCP endpoint 上，**smartsheet 走主服务 `tencent-docs`**。
skill 目录（`tencentdocs.py` 所在）：

```
C:/Users/{user}/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docs-plugin/<ver>/skills/tencent-docs
```

**调用前必做**：`python tencentdocs.py tdoc_init` → 期望 `READY`；查参数用 `tdoc_schema <service> <tool>`，**不要凭记忆拼参数**。

**数据量大时不要用 CLI**：`tencentdocs.py tdoc_call` 只接受命令行 JSON 字符串，Windows 约 32KB 上限。
改为在脚本里直接复用其内部函数：

```python
import sys, json
sys.path.insert(0, SKILL_DIR)
import tencentdocs as td

def call(tool, args, service="tencent-docs"):
    url = td._resolve_url(service)
    tokens = td._require_tokens()
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": tool, "arguments": args}}
    rsp = td._post_jsonrpc(url, payload, tokens[0], tokens[1], False, 120)
    obj = json.loads(rsp)
    if obj.get("error"):
        raise RuntimeError(obj["error"])
    for c in obj["result"].get("content", []):
        if c.get("type") == "text":
            return json.loads(c["text"])
```

---

## 字段映射（从题目清单派生字段）

若题目来源是「题号 | 模块 | 题型 | 题干 | 选项」结构的表，按此映射：

| 题型 | `field_type` | 备注 |
|---|---|---|
| 填空题 / 开放题 | `text` | 无选项 |
| 多选题 | `select` | `property_select.options` |
| 单选题 / 情境判断 / 量表题 | `singleSelect` | `property_single_select.options` |

- 选项分隔符：**表意空格 U+3000**（`\u3000`），切分后去空白。
- 选项**保留 `A.` / `1 完全不同意` 原始前缀**——便于答卷回填到答案串。
- 「模块说明」「说明」这类非题目行**跳过**（不能做字段）。
- 字段名建议 `Q{题号} {题干}`（换行转空格），便于与原卷对照。
- **首个主字段建议放 `学号`**（主字段不可删，须复用）。

字段对象：
```json
{"field_title": "Q1 题干……", "field_type": "singleSelect",
 "property_single_select": {"options": [{"text": "A.选项一"}, {"text": "B.选项二"}]}}
```

---

## 坑位（全部为实测，不是推测）

### 坑 1 · 字段标题禁止 ASCII 直引号 `"`
报错 `400001 invalid field title: contains illegal characters`。
**实测仅此一个字符非法**；`、，。？：（）[]→×≥%…` 与 U+3000 全部合法。
写入前**必须**把直引号成对转中文引号：

```python
def fix_quotes(s):
    out, open_q = [], True
    for ch in s:
        if ch == '"':
            out.append('\u201c' if open_q else '\u201d'); open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)
```

### 坑 2 · 同表字段标题不可重复
报错 `400001 字段标题 "X" 已存在`。
**标题是续跑的锚点**：重跑前先 `list_fields` 取已有标题集合，只提交差集。

### 坑 3 · 腾讯 WAF 限流（最耗时，务必按此纪律执行）

- **现象**：请求打到 `waf-captcha.cloud.tencent.com`，返回 **HTTP 501 HTML 拦截页**。
  在 `tencentdocs.py` 里表现为 `_post_jsonrpc` 返回 `None` → 上层只报 `XXX 无响应`，
  **错误信息里看不到 501**，极易误诊为网络抖动。**看到 `无响应` 先怀疑限流。**
- **规律**：
  - **读**操作（`list_*`）基本能通；**写**操作被拦。
  - 静默后可放行 3~5 个请求，随即再被拦 → 惩罚窗口内**配额极少**。
  - **请求体越大越易被拦**：单请求整体建表（7.5KB）被拦；占位短标题 8 个字段能过；真实内容 4 个字段以上大概率被拦。
  - **换通道无用**：走宿主 MCP（DeferExecuteTool）同样 501，因为**出口 IP 相同**。
  - **惩罚期 > 1 小时**：曾以每 3 分钟 1 个请求的极低强度连续跑 1 小时，写入仍零进展。
  - 配额是**累计消耗型**：同一会话早期可连续成功 15 个请求，不存在固定阈值。
- **纪律（最重要的一条）**：
  > **重试会延长惩罚。** 不要用「失败 → 立即重试 → 加长退避」去撞它，实测会把惩罚期越拖越长。
  > 正确做法是 **长时间静默**，恢复后**一次性用中等批次写完**。
- **开工前先发单字段探针**确认放行，再进入批量：

```python
call("smartsheet.add_fields", {"file_id": FID, "sheet_id": SID,
     "fields": [{"field_title": "恢复探针", "field_type": "text"}]})
```
被拦 → **当天不要再碰**，隔更久再来。

### 坑 4 · 新建智能表格自带 5 个示例字段
`文本 / 数字 / 单选 / 日期 / 图片`。**主字段（`文本`）不可删**：
用 `update_fields` 改名复用（如改成「学号」），其余 4 个用 `delete_fields` 删除。

```python
call("smartsheet.update_fields", {"file_id": FID, "sheet_id": SID, "fields": [
    {"field_id": primary_id, "field_title": "学号", "field_type": primary_type}]})
```

### 坑 5 · 分享链接与权限
- API **不返回**表单视图的公开分享 URL → 需在 UI 里对表单视图点「分享」。**不要臆造链接。**
- **不要用 `set_privilege(policy=2)`**：那是**文档级**「全员可读」，会把**已回收的答卷数据（含学号等个人信息）一并公开**。表单分享走表单自身的设置。

### 坑 6 · WorkBuddy 的 Bash 里 `/tmp` 会被解析成 `d:\tmp`
临时脚本一律写到项目 `.workbuddy/` 下，再用**绝对路径**执行。

---

## 标准流程

1. **确认鉴权**：`tdoc_init` → `READY`
2. **建文档**：`manage.create_file(title=…, file_type="smartsheet")` → 记录 `file_id` / `url`
3. **拿 sheet_id**：`smartsheet.list_tables`
4. **改造主字段 + 删示例字段**：`list_fields` → `update_fields` → `delete_fields`
5. **探针**：单字段 `add_fields`，确认未被限流
6. **写字段**：自适应批次（8→4→2→1），按标题去重续跑；被拦就停、静默、隔久再来
7. **建表单视图**：`smartsheet.add_view(view_type="form", view_title="填写问卷")`
8. **校验**：`list_fields` 的 `total` 应等于设计字段数；`list_views` 应含 `form`
9. **交付**：把文档 URL 给用户，并**明确告知表单分享链接需在 UI 获取**、权限不要开全员可读

---

## 交付时必须说明的三件事

1. 走的是**智能表格表单视图**，不是原生「收集表」——以及为什么（接口限制）。
2. **表单分享链接需用户自行在 UI 获取**（API 未返回）。
3. **未擅自开放文档权限**，并说明开放的风险（答卷含个人信息会被公开）。
