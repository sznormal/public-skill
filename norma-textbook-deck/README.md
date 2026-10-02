# norma-textbook-deck · 使用说明

> 教材 Markdown → 教学课件（飞书在线幻灯片 + pptx + 代码 txt）
> AFP-SPEC Bronze · Independent skill · partner: norma

---

## 这个 skill 做什么

把一章教材（Markdown）稳定复现地做成 20–30 页教学课件。它固化了
《Python 机器人基础编程（AI素质版）》课程课件的**风格规律与制作流程**：

- **先反推规律**：解析既有同级 PPT，归纳"抽哪些点、怎么排"（七条抽取规律）
- **规划大纲**：`slide_plan.json` 把页序、每页要点、配色、配图先定死
- **逐页闭环**：写一页 → lint 到 0 错 → 立即提交 → 记 slide_id
- **三重验收**：服务端页数 + 全文 lint + pptx 完整性
- **搜图不生成**：配图一律网络搜图，禁止 AI 生图

交付三件套：**在线幻灯片链接 + .pptx + `_实例代码.txt`**（正文不贴代码）。

---

## 怎么用

在对话里说：

```
把第10章做PPT
教材转课件
把这一章做成课件
```

skill 会先问三件事：哪一章、用什么配色（默认科技深蓝）、有没有参照 PPT。
确认后从 P1 走完 P4。

---

## 目录结构

```
norma-textbook-deck/
├── SKILL.md                    ← 主入口（薄路由 + AFP frontmatter）
├── stages/                     ← 四个阶段（顺序推进，各有 Hard Stop）
│   ├── p1-source-extraction.md
│   ├── p2-outline-planning.md
│   ├── p3-page-closure.md
│   └── p4-acceptance-delivery.md
├── modules/                    ← 按需加载
│   ├── extraction-rules.md     ← 七条抽取规律 + 教学弧线
│   ├── design-spec.md          ← 配色/坐标/版式/高频坑/配图规矩
│   └── pitfalls.md             ← 实测踩坑（反面样例）
├── templates/
│   ├── slide-plan.json         ← 大纲计划模板
│   ├── slide-xx.xml            ← 页面 XML 骨架
│   ├── add.sh                  ← lint+提交一键脚本
│   └── 用户核查清单.md          ← 用户监督用
├── scripts/
│   └── extract_code.py         ← 代码外置抽取
├── AFP-SPEC-CONFORMANCE.md     ← 合规证书
└── README.md                   ← 本文件
```

---

## 快速上手（单章制作）

```bash
# 0) 准备工作目录
mkdir chN_ppt && cd chN_ppt

# 1) 抽代码（在教材目录执行）
<python> <skill>/scripts/extract_code.py "第N章_xxx.md" "第N章_xxx_实例代码.txt" --lang python

# 2) 建空白 deck
lark-cli slides +create --as user --title "第N章 <章名>"

# 3) 逐页闭环（改 add.sh 里的 PRES 为实际 id）
bash add.sh slide-01.xml

# 4) 验收 + 导出
lark-cli slides +xml-get --as user --presentation "<id>" > server_full.xml
# 抽 content 成 server.xml 后 lint
lark-cli drive +export --as user --token "<id>" --doc-type slides --file-extension pptx --output-dir "."
```

---

## 关键纪律（三条）

1. **逐页闭环**：一页一 lint 一提交，lint error_count 必须 0。
2. **只搜不生成**：配图用网络搜索的真实素材；找不到回退纯图形，绝不用 AI 生图。
3. **步步落盘**：`slide-NN.xml`、`slide_plan.json`、`deck-state.json`、`images/` 都要落盘——换个对话只凭这些文件能接着干。

---

## 常见问题

| 问题 | 处理 |
|---|---|
| 页数比计划多 | 含 img 页提交多出的重复页，`+delete-slide` 删末尾那张 |
| lint 报 `not well-formed` | 直接把 `+xml-get` 的 JSON 喂了 lint——先抽 `content` 成纯 xml |
| lint 报 `border width` | 改成整数，写 2 不写 1.5 |
| 想换配色 | 改 `slide_plan.json` 的 `design.scheme`，按 `design-spec.md` §0 取值 |
| 想做别的课程 | 先按 `modules/extraction-rules.md` 反推新课程的规律，再照本流程执行 |

---

## 与前身 skill 的关系

本 skill 是 `textbook-deck-dark-blue` 的 AFP 化正式版：
- 前者保留（向后兼容），触发词较宽
- 本 skill 用 `norma-` 命名空间前缀，触发词收窄到"教材→课件"单点任务
- 底层能力（`lark-slides` 连接器）两者共用

---

*维护者：norma · v1.0.0 · 2026-09-16*
