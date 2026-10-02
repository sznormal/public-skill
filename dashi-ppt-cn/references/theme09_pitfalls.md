# theme09（深蓝杂志风）坑位与绕过方案

本文档记录在 dashi-ppt theme09 上制作中文教材 PPT 时遇到的已验证阻塞点，及对应的绕过方案。所有方案均已在「项目一：嵌入式开发工程师入职上手」22 页 PPT 制作中实测通过。

---

## 坑位 1：maxH 校验缺陷（最耗时，约占总工时 50%）

### 现象
`render-goal-deck.jsx` 在渲染前调用 `validateGoalSpec`，对 `maxH`（版式最大高度，数字属性）校验自相矛盾：
- 不映射 `maxH` → 报 `slide X variant Y ... requires N available 1/1`（必须映射的可见属性缺失）；
- 映射 `maxH` 到字符串字段（如 `presentation.title`）→ 报 `maxH 不是有效数字`；
- 在不支持 `maxH` 的版式上映射 → 报 `unknown prop for this layout`。

### 根因
theme09 的 111 个版式中，**只有 `theme09_page075` / `theme09_page110` 两种版式真正支持 `maxH`**，且默认值为数字（`page075 = 520`、`page110 = 560`）；其余版式根本无此属性。校验器却对「支持 maxH 的版式」强制要求映射。

### 绕过（已固化到 `scripts/fix_maxh.mjs`）
对每个 variant：
- 用 `getLayoutRecord(layout)` + `unknownPropKeys(rec, {maxH:540})` 判断该版式是否支持 maxH（返回空数组即支持）；
- 支持 → 在 `slide.content.presentation` 写入数值 `maxH`（取 `defaultProps.maxH`，兜底 540），并将 `contentMap.maxH` 映射为 `"presentation.maxH"`；
- 不支持 → 剔除 `contentMap.maxH`。

验证命令：
```bash
node <dashi-ppt-cn>/scripts/fix_maxh.mjs <deck>/goal.json
# 输出: 支持 maxH 的 variant: 13 | 不支持(已剔除 maxH): 75
#        新增 presentation.maxH: 13 | 映射 contentMap.maxH: 13 | 剔除多余 maxH: 0
node <dashi-ppt>/project/scripts/validate-goal-spec.mjs <deck>/goal.json   # 应通过
```

---

## 坑位 2：process / breakdown 6 条上限（约 25%）

### 现象
`goal:scaffold` 对 `process`（步骤流）/ `breakdown`（要点清单）角色设定 **item-count 上限 6**。教材任务常超此数（如任务1 有 7 步、8 知识点），scaffold 直接失败：`Insufficient compatible layouts in theme09: slide X process requires 3 available 0/0`。

### 绕过（已写进 SKILL.md 工作流）
- 超出 6 条即**拆分多页**：7 步拆「七步上 / 七步下」，8 知识点拆「知识点上 / 知识点下」；
- 所有文案截断到 theme09 预算：标题≤28、摘要≤38、要点说明≤18、收尾语≤24；
- 拆分后单章页数会略增（项目一由 ~20 页增至 22 页），属正常。

---

## 坑位 3：comparison 导出 4N 页 + v1-v3 英文泄漏（约 20%）

### 现象
`export:pptx` 在 `variantOutputMode:"comparison"` 下每逻辑页导出 4 个变体（v1/v2/v3 模板 + v4 定制），单章得 4N 页（如 88 页）。即使把 `variantOutputMode` 改为 `selected-only`，导出引擎仍遍历全部变体。

进一步排查：v1-v3 模板变体在中文内容上出现**未填占位**（`text-1`/`text-2`）与**主题自带英文装饰泄漏**（`ANNUAL RESEARCH REPORT`、`FEATURED COMPANIES`、`CONTACT SHEET` 等）；仅 **v4（定制版）** 内容完整、无泄漏。

### 绕过（已固化到 `scripts/extract_v4.py`）
`export:pptx` 后仍产出 4N 页备份，再用 `extract_v4.py` 提取每组第 4 页（v4）成干净 N 页，并扫描泄漏词告警。

验证命令：
```bash
node <dashi-ppt>/project/scripts/export-pptx.mjs <deck>/ppt <deck>/<name>_all.pptx --title "<name>"
"<python>" <dashi-ppt-cn>/scripts/extract_v4.py <deck>/<name>_all.pptx <deck>/<name>_N页.pptx
# 输出: 输入 88 页 -> 提取 22 页，输出: ..._N页.pptx
#        未检测到英文泄漏/占位，提取干净
```

> 若希望改用统一的「锁模板」风格（v1-v3），需先回填 v1-v3 文案并覆盖那批英文默认词，再单独导出——不在本 skill 默认流程内。

---

## 坑位 4：中文路径乱码（约 5%，但反复打断）

### 现象
中文项目路径（含「嵌入式linux…」）经 `npm run` 传递时被编码成乱码（mojibake，如 `宓屽叆寮弆inux…`），导致脚本找不到文件。

### 绕过
- 所有 `goal.json` 与输出目录使用 **ASCII 路径**（如 `D:/wb_ppt/p0X/`）；
- 渲染/校验脚本直接用 `node` 调 `.mjs`，不经 `npm run`。

---

## 坑位 5：tsx 缺失

### 现象
`render-goal-deck.jsx` 是 TS/JSX，需 `tsx` 运行；原 skill 未预装时 `tsx: command not found`。

### 绕过
```
cd <dashi-ppt>/project && npm install tsx
# 渲染用 <dashi-ppt>/project/node_modules/.bin/tsx <dashi-ppt>/project/scripts/render-goal-deck.jsx ...
```

---

## 可复用验证清单（单章制作完成后）

```bash
# 1. maxH 修复（scaffold 后）
node <dashi-ppt-cn>/scripts/fix_maxh.mjs <deck>/goal.json
# 2. 规格校验
node <dashi-ppt>/project/scripts/validate-goal-spec.mjs <deck>/goal.json
# 3. 渲染
<dashi-ppt>/project/node_modules/.bin/tsx <dashi-ppt>/project/scripts/render-goal-deck.jsx <deck>/goal.json <deck>/ppt/index.html
# 4. 非浏览器校验
node <dashi-ppt>/project/scripts/validate-swiss-deck.mjs <deck>/ppt/index.html
node <dashi-ppt>/project/scripts/validate-goal-copy.mjs <deck>/goal.json <deck>/ppt/index.html
# 5. 导出 + 提取干净 v4
node <dashi-ppt>/project/scripts/export-pptx.mjs <deck>/ppt <deck>/<name>_all.pptx --title "<name>"
"<python>" <dashi-ppt-cn>/scripts/extract_v4.py <deck>/<name>_all.pptx <deck>/<name>_N页.pptx
```
