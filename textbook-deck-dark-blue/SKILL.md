---
name: textbook-deck-dark-blue
description: 把教材（Markdown）某一章做成教学课件飞书幻灯片，默认"科技深蓝风"，也可按用户要求或主题切换为教室浅底/自然绿等配色。硬性要求：尽量用流程/图示/表格/对比呈现、PPT 正文不贴代码、章节代码用内置脚本单独抽成 txt；交付在线幻灯片 + 导出的 .pptx + 代码 txt。适用于 K12/中学编程、AI 素养、机器人/信息技术教材章节课件；当用户说"把第X章做PPT""教材转课件""科技风/深蓝/浅色课件""代码别贴在PPT里"时使用。本 skill 是 ppt（飞书幻灯片）skill 的教材课件预设，底层走 lark-cli slides。
version: 1.0.0
---

# 教材课件 PPT（多配色预设 + 代码外置）

把一章 Markdown 教材做成 20–30 页、可直接上课的飞书幻灯片。**底层是飞书 slides；本 skill 固定教材课件三件事：多套配色可切换、图表化叙事、代码外置。**

## 0. 动手前必读（强制）
本 skill 不替代底层 ppt skill。开始前按顺序重读：
- **占位符说明**：`<ppt>` = 底层 `lark-slides` 连接器 skill，本机绝对路径 `C:\Users\29206\.workbuddy\connectors\skills\connector-feishu\lark-slides\`；`<本skill>` = 本 skill 目录 `textbook-deck-dark-blue\`。
- 开始前按顺序重读：
1. `<ppt>/SKILL.md`（主流程）
2. `<ppt>/references/workflow/slides-editing.md`、`<ppt>/references/workflow/error-handling.md`（本机 Windows / lark-cli 操作要点）
3. `<ppt>/references/xml/xml-schema-quick-ref.md`（元素属性）

> 新指令/改稿时回到第 1 步重读 `<ppt>/SKILL.md`。

## 1. 配色方案（先定，全程一套）
按 `references/design-spec.md` §0 选一套，整份 deck 只用这一套：
- **tech_dark_blue**：科技深蓝深底，默认，编程/AI/机器人主题。
- **classroom_light**：浅色投影底，护眼/浅色风需求。
- **nature_green**：浅绿底，生物/自然科普。
用户点名就以用户为准；没点名按主题默认 tech_dark_blue。选好后，标题/正文/强调色全部从该方案取值，不要混。

## 2. 输入物与三件交付物
- **输入**：一章教材 `.md`（同目录的 `_冲突文件_admin_*.md` 等备份一律忽略）。
- **交付**（与教材 md 同目录）：
  1. 飞书在线幻灯片链接（`+create` 的 `url`）
  2. 导出的本地 `.pptx`
  3. `<章名>_实例代码.txt`

## 3. 工作流（按序）
### 3.1 读源文 + 抽代码
- 完整 Read 源 md（代码块、mermaid、表格、思政时间线、课后题都要读到）。
- **用内置脚本抽代码**（不要手抄）：
  ```
  python <本skill>/scripts/extract_code.py "<章.md>" "<章名>_实例代码.txt" --lang python
  ```
  脚本自动按"代码块上方最近的小节标题"归档、保留缩进与注释。抽完打开 txt 抽查节名是否正确。
- **PPT 正文一个字符都不贴整段代码**；要讲代码时只画它的"语义角色"（见 3.4）。

### 3.2 定页面大纲
教学弧：封面→目录→引题→学习目标→背景/为什么学→核心概念（每个工具一页）→实践项目（流程图+逐行解析+报错）→拓展→小结→下章预告/寄语。一页一个点；教材里的 mermaid 用节点+箭头重绘，不贴 mermaid。

### 3.3 建空白幻灯片 + 开工通知
工作目录 `chN_ppt/` 下 `lark-cli slides +create --title "<章名>"`，记下 `xml_presentation_id` 与 `url`；立刻 present_files 发开工卡片，正文告诉用户可边做边看进度。

### 3.4 逐页闭环（一页一页来，禁止攒批）
每页重复：写 `slide-NN.xml` → `python <ppt>/scripts/xml_lint.py --input slide-NN.xml`（error_count 必须 0）→ `lark-cli slides +add-slide --presentation "<id>" --slide "@slide-NN.xml"`（确认 `.ok==true` 并记 slide_id）→ note 写 3–5 句讲稿。
**代码怎么图表化**：print/input 画控制台条或"嘴巴/耳朵"比喻；变量画"贴标签的盒子"；多变量画并排盒子+逗号拼接箭头；流程用纵向节点箭头；对比用三栏"症状→药方"。

### 3.5 全文验收 + 导出交付
1. `lark-cli slides +xml-get --presentation "<id>" --output ./full.xml`
2. `python <ppt>/scripts/xml_lint.py --input full.xml`，全文 error_count=0。
3. 导出 pptx：`lark-cli drive +export --token "<id>" --doc-type slides --file-extension pptx --output-dir "."`，用 python `shutil.copy` 复制到教材目录。
4. present_files 交付：在线链接 + pptx（可同一次）+ 代码 txt（单独一次）。

## 4. 配图取材（硬规矩：只搜不生成）
**禁止用 AI 生图（ImageGen）做课件配图。** 需要实拍素材（封面、硬件板卡、实验装置、场景照等）时，**用网络搜索找现成图片**，下载后落到 `chN_ppt/images/`，再用 `<img src="@./images/xxx.png">` 引用。理由：生成的图容易失实、风格漂移，且消耗积分；教材课件要的是真实、可信的素材。

- 搜索关键词按"对象 + 型号/场景"组织（如 `micro:bit V2 board front photo`、`RK3588 development board`）。
- 优先选：白底或暗底可抠图的正视实拍图、分辨率 ≥ 1000px、无强水印。
- 下载后统一转 PNG、裁成课件该处宽高比（如 320×240 / 426×284），命名语义化（`microbit.png`、`cover.png`）。
- **其余页面一律用 shape/line 纯图形绘制**，不额外找图；能画就不找图。
- 若找不到合适实拍图，回退到纯图形绘制（如用 5×5 点阵方块模拟 LED 屏），**绝不改用 AI 生图**。

## 5. 设计规范与高频坑
配色取值、坐标模板、本机实测的 lint 报错修法，全在 **`references/design-spec.md`**，写第一页前必读。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
