---
name: school-news-oa-writer
description: 按学校 OA 投稿规范，把一次校园活动/培训/竞赛/会议信息生成可直接复制进 OA 的 Word 新闻稿。内置字数分级（默认一般新闻≤200字/配图1张）、Word 排版（小四宋体、行距固定值24磅、段前段后0）、norma 行文偏好（中德机器人学院前置、点明嵌入式技术专业教师、用具体日期、落款无逗号版）与 python-docx 生成+自检模板。适用于用户说"写学校新闻稿""OA发稿""培训新闻""学校新闻报道""新闻通稿""帮我写个培训报道"等场景。
【触发隔离】：只处理「校园活动/培训/竞赛/会议 → OA 投稿 Word 新闻稿」这一单点任务。用户要做的是公众号推文/自媒体文案、学术论文/报告、或纯新闻素材整理而不投稿 OA 时，本 skill 不触发——那走通用写作能力。
version: 1.0.0
agent_created: true
partner: norma
skill_type: independent
afp_spec_target: bronze
---

# 学校新闻 OA 发稿

把一次校园活动信息，按学校 OA 投稿规范，产出一份格式合规、可直接复制进 OA 的 Word 新闻稿（.docx）。产出为本地文件 + 字数/格式自检报告。

## 一、硬性约束（来自学校 OA 规范，必须遵守）

### 1. 字数 / 配图分级（先判定类型，默认「一般新闻」）
| 类型 | 字数 | 配图 |
|---|---|---|
| **一般新闻（默认）** | **≤200字** | **1张** |
| 重要新闻 | ≤300字 | 2张 |
| 重大新闻（校级） | ≤500字 | 3张 |
| 图说报道 | 大型活动图≤5张 / 单位新闻图≤3张，每图图说≤50字 | — |

- 流程：先用 Word 调格式 → 复制到 OA。标题只粘到 OA 标题栏，**正文不要带标题**。
- 判断技巧：用户没说类型时，默认按「一般新闻 200字/1图」起草，并提示可升档。

### 2. Word 排版（用 python-docx 实现，见第四节）
- 正文：小四号（12pt）宋体，行距 = 固定值 24 磅，段前 0 / 段后 0，首行缩进 2 字符（24pt）。
- 图说（如有）：五号（10.5pt）宋体，行距固定值 24 磅，段前 0 / 段后 0。
- 标题：Word 内仅作审阅，字号 16pt 居中；**复制进 OA 时标题只进标题栏、不进正文区**。
- 落款：文末 `（文/中德机器人学院；图/XXX）`（norma 终版无逗号；若用户要求严格贴合 OA 原文规范则用 `（文/，中德机器人学院；图/XXX）`）。

### 3. 行文偏好（norma 定稿版，写学校新闻默认遵循）
1. 标题与联合主办方**前置突出「中德机器人学院」**（我校中德机器人学院联合…）
2. 授课须点明**「嵌入式技术专业教师」**
3. 能用具体日期就不用"近日"（例：8月23日）
4. 正文可压到 2 段、不必铺课程模块
5. 落款 `（文/中德机器人学院；图/深圳市南山区华必达培训学校）`

### 4. 底线
政治性、准确性、真实性；政策背景 / 人名 / 职务 / 数据 / 活动名称 / 规范性表述须无误。

## 二、五段式骨架（按类型裁剪）
- 标题（我校/中德机器人学院 + 核心事件 + 成果/动作）
- 导语（5W1H：具体日期·主办方·地点·规模·核心成果，数字具体）
- 主体（展开放法：方式·内容·师资·实训，多项并列）
- 升华（价值拔高：人才·产业·品牌，套路词 筑牢/助力/凸显）
- 落款（文/图署名）
- 一般新闻（≤200字）：压成 1–2 段，保留导语+升华即可，不必铺课程模块。

## 三、工作流程
1. **收集要素**：新闻类型(一般/重要/重大)、具体日期、主办方(我校中德机器人学院 + 其他)、活动全称、期次、规模(人数/天数)、授课方、图片来源、文/图署名。缺要素先问用户，不要编造。
2. **起草**：套五段式骨架 + 行文偏好，控制字数到对应档位。
3. **生成 Word**：用第四节 python-docx 模板输出 `.docx`（managed venv 已装 python-docx）。
4. **自检**：回读字数分级 + 字体/行距，输出合规报告（✅/⚠️）。
5. **交付提示**：提醒用户标题只进 OA 标题栏、图片上传后宽度改 600、单张 2–10MB。

## 四、python-docx 生成模板（参考）
```python
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_LINE_SPACING
from docx.oxml.ns import qn

def set_run_font(run, font_name='宋体', font_size=12, bold=False):
    run.font.name = font_name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)
    run.font.size = Pt(font_size)
    run.font.bold = bold

def set_pf(p, line_spacing=24, space_before=0, space_after=0, first_indent=24):
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(line_spacing)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.first_line_indent = Pt(first_indent)

def build(title, body_paras, credit):
    doc = Document()
    pt = doc.add_paragraph(); r = pt.add_run(title)
    set_run_font(r, '宋体', 16, True); pt.alignment = 1
    set_pf(pt, space_after=12, first_indent=0)
    for t in body_paras:
        p = doc.add_paragraph(); set_run_font(p.add_run(t), '宋体', 12, False)
        set_pf(p, first_indent=24)
    pa = doc.add_paragraph(); set_run_font(pa.add_run(credit), '宋体', 12, False)
    set_pf(pa, space_before=0, first_indent=0)
    return doc

# 运行环境（managed venv，已含 python-docx；按本机 HOME 推导，勿写死用户名）：
# Windows:      ~/.workbuddy/binaries/python/envs/default/Scripts/python.exe gen.py
# macOS/Linux:  ~/.workbuddy/binaries/python/envs/default/bin/python gen.py
```
- 写脚本用 `Write` 落盘到工作区 `outputs/`，再用 managed venv 的 python 执行。
- 自检：重新 `Document(path)` 读取，校验每段字号/字体/行距（EXACTLY 规则下 `line_spacing` 为 EMU，需 ÷12700 得磅）/段前段后。

## 五、注意
- 图片由用户另提供，Skill 不生成图片；仅提醒 OA 上传规范（单张不拼图、2–10MB、上传后宽度改 600）。
- 标题段 16pt 仅为 Word 审阅美观，不计入正文字数，也不进 OA 正文区。
- 若用户终版与 OA 原文落款逗号不一致，以用户终版为准，但提示差异。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
