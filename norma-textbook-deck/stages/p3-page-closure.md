# P3 · 逐页闭环（write / lint / submit）

> norma-textbook-deck · Stage 03
> 目的：一页一页把课件做出来。**每一页都必须走完"写→校验→提交→记录"四步**，禁止攒批。

---

## 一、单页闭环四步（每页重复）

```
① 写 slide-NN.xml        （按 modules/design-spec.md 骨架填空）
② lint 到 0 错           xml_lint.py --input slide-NN.xml
③ 提交                    lark-cli slides +add-slide --presentation "<id>" --slide "@slide-NN.xml"
④ 记录                   确认 ok==true，记下 slide_id 写入 deck-state.json
```

**纪律**：
- lint 的 `error_count` 必须为 0 才能提交；warning 可接受（见 `modules/pitfalls.md`）。
- 提交后**不要**立刻写下一页就忘了记录 slide_id——它是后续核对/删除的唯一依据。
- 一页的 note（讲稿）必须写 3–5 句，供教师上课直接念。

**一键脚本**：`templates/add.sh` 把 lint + 提交封装成一条命令，工作目录下 `bash add.sh slide-NN.xml`。

## 二、代码怎么图表化（核心手法）

PPT 正文**一个字符都不贴整段代码**。讲代码时，只画它的"语义角色"：

| 代码元素 | 图表化方式 |
|---|---|
| `print` / `input` | 控制台条（等宽字体 + 光标 █）或"嘴巴/耳朵"比喻 |
| 变量 | "贴标签的盒子"（盒子 rect + 标签 round-rect 压顶） |
| 多变量拼接 | 并排盒子 + 逗号拼接箭头 |
| 分支结构 | 横向分叉节点 |
| 循环 | 环形箭头 / 回环 |
| 列表 | 分格抽屉 |
| 字典 | 键值对卡片 |
| 异常处理 | "保险丝/兜底网"图形 |
| 字符串方法 | 输入 → 动作 → 输出 三段横向流程 |

## 三、版式与坐标（照 `modules/design-spec.md` 填空）

- 画布固定 960×540；内容区 x=80…880。
- 标准标题区：小标签 y≈46（13px）→ 主标题 y≈70（30px bold）→ 导读 y≈120（15px）→ 内容区 y≈156 起。
- 页脚 y≈494（caption 11px），左侧"第N章 · 章名"，右侧页码。
- 每页 `<style>` 必须有深蓝渐变底色；`<data>` 内所有元素；`<note>` 写讲稿。
- **硬规矩**：不写 `<?xml?>`；单页只放一个 `<slide>`；禁 emoji；不写元素 id（交服务端分配）；`&`/`<`/`>` 转义；line 箭头必须 `<endArrow type="arrow"/>`；`border width` 只能整数。

## 四、含 `<img>` 的页面（特殊注意）

- 图片用 `<img src="@./images/xxx.png" .../>`，`@` 前缀让服务端自动上传。
- **提交后必须回读核页数**：图片上传会占用多个 revision，偶发在末尾多出一张重复页。
  - 发现重复 → 用 `lark-cli slides +delete-slide --slide-id <末尾重复页>` 删除（先 `--dry-run`）。
  - 保留序列中**位置正确**的那张，删掉末尾多出来的。

## 五、输出 schema

```json
{
  "deck": { "submitted_pages": 25, "revision_id": 27 },
  "stages": { "P3_pages": ["pPP","pPY","...","pPN"] }
}
```

中间产物落盘：`chN_ppt/slide-01.xml` … `chN_ppt/slide-NN.xml`。

## 六、Hard Stop · 确认单（分批）

由于页数较多，每完成 **5–8 页**给一次进度确认单（不必每页都停）：

```
╭─ P3 逐页制作 · 进度 ─────────────────────────╮
│ 📊 已提交：{N}/{planned} 页
│ 📄 本轮：slide-{a}…slide-{b}
│ 🖼  配图页：{状态}
│ ⚠️  页数核对：{正常 | 发现重复页已删}
│ 🔗 预览：{url}
│ 👉 继续制作下一页 / 或说 "暂停"
╰──────────────────────────────────────────╯
```

**硬停点**：全部页面提交完成后，进入 P4 前必须停一次；中途若需删除/覆盖已提交页面，必须先确认。

**等用户确认才推进**：本阶段不得自动进入 P4，也不得在未确认的情况下执行删除/覆盖类破坏性操作。
