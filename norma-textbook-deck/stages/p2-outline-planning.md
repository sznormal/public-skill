# P2 · 定页面大纲 + 建空白 deck

> norma-textbook-deck · Stage 02
> 目的：把"要做哪些页、每页讲什么"先定死，再建在线空白 deck 开工。写 XML 时就是"填空"而非"创作"。

---

## 一、先定页面大纲（`slide_plan.json`）

按 `modules/extraction-rules.md` 的**标准教学弧线**排页，落盘
`chN_ppt/.lark-slides/plan/chN/slide_plan.json`（模板见 `templates/slide-plan.json`）。

每页至少定义：

| 字段 | 含义 |
|---|---|
| `n` | 页码 |
| `layout_type` | 版式：title-cover / grid / two-column / flow / diagram / concept / table / compare / timeline / conclusion |
| `visual_focus` | 视觉主体：img / numbered-cards / icon-cards / horizontal-3step / vertical-flow / before-after / symbol-cure / quote … |
| `text_density` | low / mid / high |
| `key_message` | 这一页唯一要传达的一句话 |
| `uses_image` | 是否用配图（并登记 `assets.images` 的 `used_on`） |

同时把 `design`（配色取值 / 字体 / 画布 / 骨架）与 `assets`（图片清单 + 缺失回退策略）写进 plan。

**页数**：一般 20–30 页。**一页一个点**，不堆砌。

## 二、建空白幻灯片 + 开工通知

在工作目录 `chN_ppt/` 下：

```
lark-cli slides +create --as user --title "第N章 <章名>"
```

记下返回的 `xml_presentation_id` 与 `url`，写入 `deck-state.json`。

**立刻 present_files** 把 url 发给用户作开工卡片，正文说明"可边做边看进度"。

## 三、配图取材（只搜不生成 · 硬规矩）

按 `modules/design-spec.md` §4：

1. 只对 `uses_image=true` 的页找图（通常 1–2 页：封面、硬件/实物页）。
2. **用网络搜索找现成实拍图**，关键词按「对象 + 型号/场景」组织。
3. 选图标准：正视实拍、分辨率 ≥1000px、无强水印、易抠背景。
4. 下载 → 转 PNG → 裁成目标宽高比 → 语义化命名，落到 `chN_ppt/images/`。
5. **禁止 AI 生图**。找不到合适素材 → 回退纯图形绘制（如用 5×5 点阵方块模拟 LED 屏）。
6. 其余页面**一律用 shape/line 纯图形绘制**，能画就不找图。

## 四、输出 schema

```json
{
  "deck": { "xml_presentation_id": "", "url": "", "planned_pages": 25, "submitted_pages": 0 },
  "artifacts": { "plan_json": "chN_ppt/.lark-slides/plan/chN/slide_plan.json", "images": ["images/cover.png"] },
  "stages": { "P2_outline": true }
}
```

## 五、Hard Stop · 确认单

```
╭─ P2 页面大纲 + 空白 deck 完成 ────────────────╮
│ 📊 计划页数：{N} 页（教学弧线：封面→…→预告）
│ 🎨 配色 / 字体：{scheme} / 思源黑体
│ 🖼  配图页：{N} 页（{图片文件名}），其余纯图形
│ 🔗 在线空白 deck：{url}
│ 📄 plan 落盘：{slide_plan.json}
│ ⚠️  请先看大纲：页序 / 每页要点是否要调整？
│ 👉 NEXT：输入 "Next" 开始 P3 逐页制作
╰──────────────────────────────────────────╯
```

**等用户 `Next` 才推进 P3。** 用户若要调整页序或增删页，先改 `slide_plan.json` 再确认。
