---
name: library-doc-to-pptx
description: 把 WorkBuddy 资料库（/space/d/ 或 *.workbuddy.link/p/ 链接）里的在线文档正文提取出来，自动生成一份可编辑 PPTX。解决四个高频卡点：资料库 doc 的 XML 体正文如何转成干净 Markdown、Git Bash 下 slidep 命令因 cygpath 路径映射失败无法运行、slidep 中 flex 行内 Box 不给显式宽度会导致文字按最窄列换行从而溢出、slidep lint 输出被日志淹没如何取结果。触发词：把这篇资料库文档做成 PPT / 读取资料库文档生成幻灯片 / space 链接转 PPT / 资料库导出 ppt。
version: 1.0.0
author: 小妮
agent_created: true
---

# 资料库在线文档 → 可编辑 PPTX

## 适用场景

用户给出一个资料库节点链接（`https://www.workbuddy.cn/space/d/<id>` 或 `*.workbuddy.link/p/<id>`），要求"读取正文，生成 PPT"。

本 skill 只负责**取正文 + 落盘成 Markdown**这一段，以及**生成 PPT 时必踩的四个坑**。PPT 的叙事与视觉设计仍走 `tencent-pptx` skill。

## 第一步：读取资料库文档正文

先按资料库 skill（`资料库`，SKILL.md 在 `plugins/workbuddy-builtin/skills/library/`）的规定走：

1. `python "${SKILL_DIR}/runtime_context.py"` → 得到 `mode=sandbox|client`。
2. `mode=client` 时：`ToolSearch(tool_names=["connect_open_platform"])` → `DeferExecuteTool(connect_open_platform, {skill_id:"library"})` 取 token。
3. 归一化 nodeId（从 URL 里提取 `{id}`），`space.workspace.node-info` 确认 `kind`。
4. `kind=doc` → 在 `library/doc/` 下执行：

```bash
printf '%s' "<token>" | python get_doc_reviews.py --page-id <nodeId> --token-stdin > raw.txt
```

**关键：一定要重定向到文件**。正文常达 10 万字符，直接读会被截断（中间丢 6 万字节），必须落盘后再转换。

## 第二步：XML 体正文 → 干净 Markdown

资料库 doc 的返回是 WorkBuddy 组件 XML（`<Heading>` / `<Paragraph>` / `<BulletedList>` / `<Table>` / `<Mark bold>`），不是 Markdown。用 `scripts/doc_xml_to_md.py` 转换：

```bash
python scripts/doc_xml_to_md.py raw.txt out.md
```

转换器已处理三个易错点：
- `<Mark bold>...</Mark>` 必须转成 `**...**`，且在 **Mark 开始标签处不能丢弃前面已缓冲的文本**（否则"本报告依据 DACUM…对以下三个岗位中"这类前导文字会整段消失，只剩加粗部分）。
- `<Table>` 的 `<TableCell>` 内嵌 `<Paragraph>`，单元格文本要按 cell 缓冲，`</Table>` 时再统一输出 GFM 表格。
- 结尾 `KS_DOC_REVIEWS\t...` 行要剥掉。

**自检**：转完后 `grep -n "^#" out.md` 看标题层级是否与原文一致；重点抽查带 `<Mark bold>` 的段落，确认加粗前的文字还在。

## 第三步：走 tencent-pptx 生成 PPT

按 `tencent-pptx` skill 的标准流程（STORY.md → 风格 → 逐页 lint + upsert-dsl）执行。以下是本机实测的四个卡点与解法。

### 卡点 1：Git Bash 下 `slidep` 命令跑不起来

`slidep` 是 npm shim，内部用 `cygpath -w` 把路径转成 `D:\program\cygwin\c\Users\...`，导致 `Cannot find module ...@tencent\slidep\dist\index.js`。

**解法**：绕过 shim，直接用托管 node 调 dist/index.js。建议先落一个包装脚本：

```bash
#!/bin/sh
NODE="C:/Users/<user>/.workbuddy/binaries/node/versions/<ver>/node.exe"
SLIDEP="C:/Users/<user>/.workbuddy/binaries/node/versions/<ver>/node_modules/@tencent/slidep/dist/index.js"
exec "$NODE" "$SLIDEP" "$@"
```

托管 node 版本目录可用 `which slidep` 反推（shim 就在 node 版本目录里）。

### 卡点 2：flex 行内的 Box 不给宽度 → 文字按最窄列换行 → 溢出

`slidep` 的 Box 在 `flexDirection: 'row'` 的父容器里没有 `flex` 也没有 `width` 时，宽度按内容收缩而非撑满，正文会被折成 3–4 行，lint 报 `child-containment ... bottom+Npx`。

**解法**：给行内的文本容器显式 `width`，按 `容器宽 - padding*2 - 兄弟元素宽 - gap` 算出可用值后再留 2% 余量。

### 卡点 3：lint 的结果 JSON 被日志淹没

lint/upsert 会先打一堆 `couldn't load font` 与 `[NodeImageLoadService]` 日志。用

```bash
sh sp.sh lint file.pptx --dsl-file slides/01.slide 2>&1 | grep -o '{"ok".*'
```

拿结果。`{"ok":true,...,"diagnostics":[]}` 才算通过；`ok:false` 时 `diagnostics[].message` 里会带行号和 `bottom+Npx` 数值，据此做高度收缩（减小 padding / lineHeight / 字号，或删掉次要文本行）。

**注意**：本机 lint 用 Sans 回退字体量文本，比"微软雅黑"更宽，所以 lint 通过 ⇒ 实际渲染一定通过；反过来 lint 报溢出时，若只超 3–8px，实际渲染可能没问题——但按规则仍要改到通过。

### 卡点 4：`slidep screenshot` 在本机不可用

报 `render failed: The argument 'filename' must be a file URL...`，依赖未配置好的本地 editor SDK。

**解法**：不要在这上面反复试。以 `slidep lint` 的溢出诊断作为唯一自动校验手段，并靠"上 padding + 标题块 + 内容区 + 各 gap + 下 padding ≤ 720"的高度预算表人工把关。

## 高度预算模板（1280×720 内容页）

```
上 padding 40 + 标题块 74 + gap 14 + 分隔线 2 + gap 14 + 内容区 C + 下 padding 48 = 720
⇒ C = 528
```

页脚用 `position: 'absolute', left: 40, right: 40, bottom: 18`，不参与上述预算。封面 / 目录 / 章节扉页 / 结束页可省略 A（标题块）与 D（页脚），改用 `padding '48px 64px'` + `justifyContent: 'space-between'`。

## 页面视觉类型的选择（高置信度素材场景）

素材是"岗位能力标准 / JD 分析 / 财务数据"这类**不能编造**的内容时：
- 全篇 **L1 主视觉统一用内联结构图**（Box + Text + FAIcon 绘制流程 / 分层 / 双端结构），不用 AI 生图——保证每张图都能追溯到原文表格。
- 数据用 Table 组件（`cells` 二维数组 + `cellStyle.background` 做斑马纹与表头深底）。
- 图标只用 FAIcon 文档里列出的名字（`chart-line` / `eye` / `cog` / `briefcase` / `file-text` / `check-circle` / `info-circle` / `arrow-down` / `arrow-right` / `folder` / `copy` / `wrench` / `share` / `chart-bar` 等）；**编造图标名会导致构建出空白图形**。

## 字体落地的默认取舍

预设学术风要求"思源黑体"，但 Windows + Office/WPS 环境不保证安装。**默认改用「微软雅黑」**并在交付说明里写明这是落地微调（字体家族仍控制在 2 套以内：微软雅黑 + 封面英文 Times New Roman）。

## 交付前自检清单

- [ ] `python -c "zipfile" ` 数一下 `ppt/slides/slide*.xml` 数量 = 计划页数
- [ ] `presentation.xml` 的 `sldId` 顺序与 `presentation.xml.rels` 映射后 = slide1..slideN（页序正确）
- [ ] `zip.testzip()` 为 None（文件没损坏）
- [ ] 每页 `.slide` 都过了 lint 且 `ok:true`
- [ ] 目录声明的章节数 = `type: section` 扉页数，编号 01..N 连续且与目录条目文字逐字一致
- [ ] 用脚本扫一遍各页 hex：只出现预设色板内的颜色，没有自创色

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
