# P1 · 读源文 + 抽代码 + 反推规律

> norma-textbook-deck · Stage 01
> 目的：把这一章的"原料"备齐——完整读懂源文、把代码抽成独立 txt、确认本课程的课件抽取规律。

---

## 一、读源文（完整读，不跳读）

1. 定位源 md：用户指定的 `第N章_<章名>_学生版.md`。
   - **忽略**同目录的 `_冲突文件_admin_*.md` 等备份文件（那是网盘冲突副本）。
2. 用 Read **完整读一遍**源 md，逐项确认以下元素是否齐全、各出现在哪里：
   - [ ] 章节引言/背景
   - [ ] 学习目标（语法 / 硬件 / 价值三类）
   - [ ] 核心概念（含 `mermaid` 图，需重绘）
   - [ ] 项目实战（含代码块、逐行解析、硬件增强版）
   - [ ] 表格（指令词典、测试用例等）
   - [ ] 课程思政小知识 / 思政寄语
   - [ ] AI 透视窗 / 素养贴士 / 工程视角
   - [ ] 术语解析
   - [ ] 常见报错与调试（Debugging Corner）
   - [ ] 本章小结
   - [ ] 课后习题（选择题/填空/简答/实践/思政思考）
   - [ ] 下章预告

## 二、抽代码（用脚本，不手抄）

在教材 md 同目录执行：

```
<managed_python> "<skill>/scripts/extract_code.py" "<第N章_xxx.md>" "第N章_xxx_实例代码.txt" --lang python
```

- 脚本自动按"代码块上方最近的小节标题"归档，保留缩进与注释。
- 抽完**打开 txt 抽查**：小节标题是否对应正确、代码块数量是否与源 md 一致、缩进有无丢失。
- **PPT 正文一个字符都不贴整段代码**——代码只进 txt，PPT 上只画它的"语义角色"（见 `stages/p3-page-closure.md`）。
- 把代码块的"语义角色清单"记下来（如：文件操作 / 循环 / 字典查找 / try-except），P3 排版时逐块转成图形。

## 三、反推规律（本 skill 的方法论锚点）

**若用户提供了可参照的既有 PPT**（如第1章 pptx）→ 解析它，归纳抽取规律：

1. 用零依赖脚本解析 pptx（zipfile + ElementTree）：按页输出 shape 类型 / 文本 / 图片 / 备注。
2. 归纳并核对 `modules/extraction-rules.md` 里的**七条规律**，确认是否仍然成立、有无新增规律。
3. 若发现与 `extraction-rules.md` 不一致之处，**当场更新该模块**（这是本 skill 的自我进化点）。

**若用户未提供参照 PPT** → 直接采用 `modules/extraction-rules.md` 的既有七条规律（它就是本课程固化的模板）。

## 四、配色确认（硬停）

按 `modules/design-spec.md` §0 让用户确认配色，整份 deck 只用这一套：

| 方案 | 适用 |
|---|---|
| `tech_dark_blue`（默认） | 编程 / AI / 机器人主题 |
| `classroom_light` | 长时间投影、护眼、浅色风 |
| `nature_green` | 生物 / 自然科普 |

用户不指定 → 默认 `tech_dark_blue`。**选后全程不混色。**

## 五、输出 schema

落盘 `chN_ppt/.lark-slides/plan/chN/deck-state.json` 的 P1 部分：

```json
{
  "meta": { "chapter": "第N章", "chapter_title": "", "source_md": "", "scheme": "tech_dark_blue", "current_stage": "P2" },
  "artifacts": { "code_txt": "第N章_xxx_实例代码.txt", "code_blocks": 4, "semantic_roles": [] },
  "stages": { "P1_source": true }
}
```

同时产出：
- `第N章_<章名>_实例代码.txt`（教材目录）
- 一份"源文元素清单"（对话中呈现，确认哪些板块本章存在、哪些不存在）

## 六、Hard Stop · 确认单

```
╭─ P1 读源文 + 抽代码 + 反推规律 完成 ──────────╮
│ 📖 章节：第{N}章 {章名}
│ 🎨 配色：{scheme}
│ 📄 源文元素：{齐全项} / {缺项}
│ 💻 代码块：{N} 个 → {code_txt}
│ 🔁 语义角色：{列表}
│ 🧩 规律核对：{与 extraction-rules 一致 | 已更新 N 条}
│ 💾 已落盘：{files}
│ 👉 NEXT：输入 "Next" 进入 P2 页面大纲规划
╰──────────────────────────────────────────╯
```

**等用户 `Next` 才推进 P2。**
