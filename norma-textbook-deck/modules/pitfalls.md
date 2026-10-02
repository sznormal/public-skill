# 实测踩坑清单（反面样例）

> norma-textbook-deck · Module
> 来源：2026-09-16 第10章 25 页制作全过程实测。每条都带**症状 → 根因 → 修法**，照单规避。

---

## ❌ G1. 含 `<img>` 的页面提交后末尾多出重复页

**症状**：micro:bit 页在位置 18 正确，又在末尾（位置 26）多出一张一模一样的页；全文页数 26 ≠ 计划 25。

**根因**：`<img>` 的 `@./images/...` 占位符触发服务端上传图片，一次提交占用多个 revision，偶发把该页追加两次。

**修法**：
1. 所有页面提交完后，`+xml-get` 抽 `content`，数 `<slide>` 个数与计划对比。
2. 多了 → `lark-cli slides +delete-slide --as user --presentation "<id>" --slide-id <末尾重复页>`（先 `--dry-run` 确认）。
3. 保留序列中位置正确的那张。

**预防**：含图页面提交后立即回读核页数，不要等全部做完才发现。

---

## ❌ G2. `<border width="1.5">` 报 sxsd_invalid_scalar

**症状**：`invalid SXSD value '1.5' for attribute "width" on <border>`，lint 报错、页面被 block。

**根因**：SXSD schema 的 border width 只接受**非负整数**。

**修法**：全部改成整数 `width="2"`。批量修：读所有 slide-*.xml，`replace('width="1.5"','width="2"')`。

---

## ❌ G3. 直接 lint `+xml-get` 的输出报 not well-formed

**症状**：`XML is not well-formed: not well-formed (invalid token): line 1, column 0`，明明是刚取回的 deck。

**根因**：`+xml-get` 输出的是 **JSON**（`{"ok":true,"data":{"xml_presentation":{"content":"<presentation>..."}}}`），不是裸 XML。JSON 第一字符是 `{`，当然不是 well-formed XML。

**修法**：
```python
import json
d = json.load(open('server_full.xml', encoding='utf8'))
open('server.xml','w',encoding='utf8').write(d['data']['xml_presentation']['content'])
```
再 lint `server.xml`。

---

## ❌ G4. bash 报 `dirname: command not found` / `cd: null directory`

**症状**：每条命令前都刷这两行 stderr。

**根因**：本机 Git Bash 初始 PATH 不含标准 bin，shim 脚本调不到 dirname。

**修法**：每条命令前缀 `export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"`。这是无害噪音，但会让输出变脏——加上就不刷了。

---

## ❌ G5. `python` / `python3` 不可用

**症状**：`python: command not found` 或调用的 python 里没有 pptx 模块。

**根因**：本机无 `python3`，且系统 python 未装 python-pptx。

**修法**：统一用托管路径
`C:/Users/29206/.workbuddy/binaries/python/versions/3.13.12/python.exe`。
解析 pptx 用**零依赖**脚本（`zipfile` + `xml.etree.ElementTree`），不依赖 python-pptx。

---

## ❌ G6. 攒批提交，报错难定位

**症状**：一次写 8 页再统一 lint，一屏报错分不清哪页哪元素。

**根因**：违反"逐页闭环"纪律。

**修法**：一页一 lint 一提交。lint 0 错才提交。用 `templates/add.sh` 把三步压成一条命令。

---

## ❌ G7. PPT 正文贴了整段代码

**症状**：页面被代码块占满，学生看不清、投影效果差，且违反本课程课件规范。

**根因**：图省事直接把教材代码块搬上 PPT。

**修法**：代码抽到 `<章名>_实例代码.txt`；PPT 只画代码的"语义角色"（盒子/箭头/流程/控制台条）。

---

## ❌ G8. 用 AI 生图做配图

**症状**：生成的硬件图细节失实（接口位置、屏幕纹理不对），风格与实拍不一致，且消耗积分。

**根因**：图省事走了生图路径。

**修法**：**一律网络搜索找现成实拍图**（见 `design-spec.md` §4）。找不到合适素材 → 回退纯图形绘制，**绝不改用 AI 生图**。

---

## ❌ G9. 把 `+xml-get` 的 JSON 存成 full.xml 后忘记它是 JSON

**症状**：后续脚本直接把它当 XML 解析，报各种奇怪的解析错。

**根因**：文件名叫 `full.xml`，误导把它当 XML 用。

**修法**：命名区分——`server_full.xml`（JSON 原文）vs `server.xml`（抽出的纯 XML）。见 G3 的转换代码。

---

## ❌ G10. 中间产物只留在对话里

**症状**：对话被压缩后，`slide_plan.json` 的页码/配色决定、每页 key_message 全丢了，只能重做。

**根因**：违反落盘思维。

**修法**：所有实质产物落盘——`slide-NN.xml`、`slide_plan.json`、`deck-state.json`、`images/`、`add.sh`。判据：换个全新对话，只凭 `chN_ppt/` 里的文件能不能接着干。
