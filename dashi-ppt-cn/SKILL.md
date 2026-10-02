---
name: dashi-ppt-cn
description: 中文教材章节 → 可编辑 PPTX 的优化版技能。封装 dashi-ppt 引擎并固化 theme09 的三处阻塞绕过方案（maxH 校验缺陷、process/breakdown 6 条上限、comparison 导出 4N 页与 v1-v3 英文泄漏）。触发词：教材 PPT、教材章节 PPT、教材文字转可编辑 PPTX、课程 PPT、教学课件、课件制作、dashi-ppt 教材优化版。
---

# dashi-ppt-cn（教材章节 PPT 优化版）

本 skill 是 `dashi-ppt` 的**封装优化版**，专门针对「中文教材章节 → 可编辑 PPTX」场景。它不复刻渲染引擎，而是复用 `dashi-ppt` 的 `project/` 生成器，仅在流程中插入两道自动修复（maxH、v4 提取），并把教材场景的硬约束写死，使单章 PPT 产出无需逐次手工排错。

## 路径约定

- `<dashi-ppt>` = `C:/Users/29206/.workbuddy/skills/dashi-ppt`（复用的引擎根）
- `<dashi-ppt-cn>` = `C:/Users/29206/.workbuddy/skills/dashi-ppt-cn`（本 skill 根）
- `<python>` = `C:/Users/29206/.workbuddy/binaries/python/envs/default/Scripts/python.exe`（managed venv，已装 python-pptx 1.0.2）
- `<deck>` = 本次任务的 ASCII 输出目录，如 `D:/wb_ppt/p0X`（**禁止中文路径**，否则 npm/tsx 传参乱码）

## 依赖

- Node.js 20+；`tsx`（位于 `<dashi-ppt>/project/node_modules/.bin/tsx`，缺失则 `npm install tsx`）
- Python managed venv + `python-pptx`
- `dashi-ppt` 原 skill 必须存在（本 skill 仅调用其脚本，不修改其源码）

## 关键优化点（已验证的绕过方案）

1. **theme09 maxH 校验缺陷** → scaffold 之后、render 之前**必跑** `<dashi-ppt-cn>/scripts/fix_maxh.mjs`：按版式精确补/剔 `maxH` 映射，解除 `validateGoalSpec` 硬失败。
2. **process/breakdown 6 条上限** → 教材任务步骤/知识点常 >6，超出则**拆分多页**（如 7 步拆「上/下」、8 知识点拆「上/下」）；所有文案截断到 theme09 预算（标题≤28、摘要≤38、要点说明≤18、收尾语≤24）。
3. **comparison 导出 4N 页 + v1-v3 英文泄漏** → `export:pptx` 默认出 4N 页；导出后**必跑** `<dashi-ppt-cn>/scripts/extract_v4.py` 提取每组第 4 页（v4 定制版），产出干净 N 页。v1-v3 模板变体残留未填占位（`text-1`）与主题英文装饰（`ANNUAL RESEARCH REPORT` 等），不可直接交付。
4. **中文路径乱码** → `goal.json` 与输出目录一律 ASCII 路径，不经 `npm run` 传中文路径（直接 `node` 调 `.mjs`）。
5. **tsx 预装检查** → 渲染前确认 `tsx` 存在。
6. **预留图片槽** → 封面/场景/实战页预留 image slot，用户给图后用 `media:stage` 填入真实路径（不交付空槽）。

> 风格选择、是否生图、是否预留槽位，仍按 `dashi-ppt` 原规则先与用户确认（本 skill 默认「预留图片槽位」）。
> 教材/品牌故事类默认 `theme09` 深蓝杂志风；嵌入式技术类可选 `theme03` 深浅代码风。

## 工作流（教材章节专用）

1. **提炼目标**：`title / goal / audience / owner / 页数（单章约 18-24 页）/ 产物格式（默认 PPTX 可编辑）`；确认主题（默认 theme09）与图片意图（默认预留槽）。
2. **提取教材内容**：读对应项目详细设计 md，梳理每页 `role`、要点、数据。
3. **逐页 brief（遵守 6 条上限）**：写为 `briefs.json`，`role` 含 `cover/breakdown/statement/metrics/relationship/context/process/actions/risks/case/closing` 等；每页 `items ≤ 6`（超出拆页）；文案截断到预算。
4. **scaffold**（直接用 `node` 调 `.mjs`，避免中文路径）：
   ```
   node <dashi-ppt>/project/scripts/goal-scaffold.mjs --title <t> --goal <g> --theme theme09 --pages <n> --content-briefs <deck>/briefs.json --layout-variants 3 --seed <seed> --workflow-run-id <id> --chunk-size 5 --out <deck>/goal.json
   ```
5. **fix_maxh（关键修复）**：
   ```
   node <dashi-ppt-cn>/scripts/fix_maxh.mjs <deck>/goal.json
   ```
6. **props:safe**：
   ```
   node <dashi-ppt>/project/scripts/write-safe-props.mjs --goal <deck>/goal.json --write
   ```
7. **validate:goal-spec**：
   ```
   node <dashi-ppt>/project/scripts/validate-goal-spec.mjs <deck>/goal.json
   ```
8. **render（tsx）**：
   ```
   <dashi-ppt>/project/node_modules/.bin/tsx <dashi-ppt>/project/scripts/render-goal-deck.jsx <deck>/goal.json <deck>/ppt/index.html
   ```
9. **validate:swiss + validate:goal-copy**：
   ```
   node <dashi-ppt>/project/scripts/validate-swiss-deck.mjs <deck>/ppt/index.html
   node <dashi-ppt>/project/scripts/validate-goal-copy.mjs <deck>/goal.json <deck>/ppt/index.html
   ```
10. **export:pptx（comparison，4N 页）**：
    ```
    node <dashi-ppt>/project/scripts/export-pptx.mjs <deck>/ppt <deck>/<name>_all.pptx --title "<name>"
    ```
11. **extract_v4（关键修复，产出干净 N 页）**：
    ```
    "<python>" <dashi-ppt-cn>/scripts/extract_v4.py <deck>/<name>_all.pptx <deck>/<name>_N页.pptx
    ```
12. **成果验收**：检查 N 页文案完整、无英文泄漏、图片槽（若已填）、首尾页非空白。
13. **交付**：主交付物为 `<name>_N页.pptx`，附 HTML 预览 `<deck>/ppt/index.html`。

## JSON 结构（与 dashi-ppt schema v2 一致）

```json
{
  "schemaVersion": 2,
  "title": "项目一：嵌入式开发工程师入职上手",
  "goal": "面向职业本科学生建立嵌入式 Linux 开发环境认知与上手能力",
  "audience": "职业本科 嵌入式班学生",
  "owner": "授课教师",
  "themePack": "theme09",
  "variantOutputMode": "comparison",
  "slides": [
    {
      "id": "s1",
      "content": {
        "presentation": {
          "title": "嵌入式开发工程师入职上手",
          "summary": "搭建环境 · 命令行 · Shell 脚本三大上手任务",
          "takeaway": "先搭环境，再练命令，最后用脚本提效",
          "items": []
        }
      },
      "selectedVariant": "v1",
      "variants": [
        {"id": "v1", "kind": "template", "layout": "theme09_page001", "props": {}, "contentMap": {"kicker": "meta.panelTitle", "title": "presentation.title", "subtitle": "presentation.summary", "lead": "presentation.takeaway"}},
        {"id": "v2", "kind": "template", "layout": "theme09_page005", "props": {}, "contentMap": {"kicker": "meta.panelTitle", "title": "presentation.title", "subtitle": "presentation.summary"}},
        {"id": "v3", "kind": "template", "layout": "theme09_page031", "props": {}, "contentMap": {"title": "presentation.title", "summary": "presentation.summary"}},
        {"id": "v4", "kind": "bespoke", "adjustable": false, "composition": {"designIntent": {"compositionFamily": "hero", "objective": "封面定调"}, "background": "dark", "elements": [{"id": "title", "type": "text", "grid": {"column": 1, "row": 1, "width": 10, "height": 2}, "role": "title", "text": ""}]}, "contentMap": {"elements[0].text": "presentation.title"}}
      ]
    }
  ]
}
```

> `presentation.maxH` 字段**不要手填**——由 `fix_maxh.mjs` 在第 5 步按版式自动注入。brief 阶段只需保证 `items` 数量与文案长度在预算内。

## 坑位参考

详见 `references/theme09_pitfalls.md`（含 maxH 缺陷根因、6 条上限拆页示例、v4 提取原理、中文路径乱码、tsx 预装，及可复用的验证命令）。

## 安全说明

本 skill 仅封装 `dashi-ppt` 引擎调用 + 自带两个修复脚本，**未修改任何引擎源码**，可与 `dashi-ppt` 升级共存。删除本 skill 不影响原 skill 与其历史产物。
