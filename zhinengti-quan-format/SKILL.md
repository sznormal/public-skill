---
name: zhinengti-quan-format
description: 当用户要求撰写或修改"智能体圈深度教程"系列飞书云文档时触发。严格按照 H1→H2→H3→H4 的中文编号格式规范处理文档标题层级，使用 lark-cli 操作飞书文档。触发词：用户说"智能体圈深度教程"。
version: 1.0.0
agent_created: true
partner: norma
skill_type: independent
afp_spec_target: bronze
---

# 智能体圈深度教程 — 飞书云文档格式规范

本 skill 定义"智能体圈深度教程"系列飞书云文档的标题层级格式标准。当用户要求撰写、修改或检查此类文档时，严格遵循以下规范。

## 标题层级编号格式

| 层级 | 编号格式 | 示例 |
|------|---------|------|
| H1 | 一、二、三... | `一、认识新版扣子` |
| H2 | （一）（二）（三）... | `（一）快速起步` |
| H3 | 1. 2. 3. ... | `1. 注册与登录` |
| H4 | ①②③④⑤⑥... | `① 自动模式 vs 手动切换` |

## 核心约束

1. **层级不可跳跃**：必须 H1 → H2 → H3 → H4 逐级递进，禁止 H1 直接跳到 H3
2. **H3 编号重置**：每个 H2 下的 H3 从 `1.` 重新开始编号，不延续上一个 H2 的编号
3. **H4 编号重置**：每个 H3 下的 H4 从 `①` 重新开始编号，不延续上一个 H3 的编号
4. **H1 编号连续**：全文 H1 从"一、"开始连续编号，不受 H2/H3 分组影响

## 使用 lark-cli 操作飞书文档

### 获取文档结构

```
lark-cli docs +fetch --api-version v2 --doc "<url>" --scope outline --max-depth 4
```

获取带 block-id 的完整目录结构，用于后续定位。

### 修改标题内容（block_replace）

当标题文字或编号需要修正时：

```
lark-cli docs +update --api-version v2 --doc "<url>" \
  --command block_replace \
  --block-id "<block-id>" \
  --content "<h3>1. 新的标题文字</h3>"
```

支持 h1/h2/h3/h4 四种标签。

### 插入缺失层级（block_insert_after）

当发现层级跳跃（如 H1 直接下有 H3，缺少 H2）时，在合适的 H3 前插入 H2：

```
lark-cli docs +update --api-version v2 --doc "<url>" \
  --command block_insert_after \
  --block-id "<前一个同级block-id>" \
  --content "<h2>（一）分组标题文字</h2>"
```

**关键规则**：若目标位置下方的 H3 含有 H4 子级，必须在**最后一个 H4** 之后插入 H2，否则 H4 会与父级 H3 分离。

### 批量操作策略

- 同一章节的多个同类修改（如多个 H3 编号修正）可在一条 Bash 命令中用 `&&` 串联
- 每批次不超过 10 个 block_replace/block_insert 操作，避免超时
- 每次批量操作后验证文档结构

## 标准章节结构模板

"智能体圈深度教程"文档通常包含以下章节：

```
一、[章节标题]          ← H1
  （一）[分组标题]      ← H2
    1. [小节标题]      ← H3
      ① [子项标题]     ← H4
      ② [子项标题]
    2. [小节标题]
  （二）[分组标题]
    3. [小节标题]
二、[章节标题]          ← H1（编号连续）
```

## 常见问题与处理

### 问题 1：H3 编号跨 H2 未重置

**现象**：（一）下有 1. 2. 3.，（二）下从 4. 开始而非 1.

**处理**：对每个 H2 下的 H3 重新编号，使用 block_replace 逐个修正。

### 问题 2：插入 H2 后 H4 归属错误

**现象**：在 H3 后面插入 H2，导致该 H3 下的 H4 被归到新 H2 下。

**处理**：插入 H2 时，先检查下方 H3 是否有 H4 子级。若有，在最后一个 H4 的 block-id 后插入，而非在 H3 后插入。

### 问题 3：H1 被错误标记为 H2

**现象**：第三章及之后的章节用了 `<h2>` 而非 `<h1>`。

**处理**：使用 block_replace 将错误的 H2 改为 H1，同时更新编号前缀（如"四、"而非"（四）"）。

## 验证步骤

每次修改后必须执行：

```
lark-cli docs +fetch --api-version v2 --doc "<url>" --scope outline --max-depth 4
```

检查：
- 无 H1→H3 跳跃（每个 H1→H2→H3 完整）
- 每个 H2 下 H3 编号从 1 开始
- 每个 H3 下 H4 编号从 ① 开始
- H1 编号全局连续

## 封面图与跨栏图片插入规则

"智能体圈深度教程"系列文档要求：

1. **封面图**：文档开头（第一个 H1 之前）必须有一张封面横幅图片，全宽居中
2. **跨栏图片**：每个 H1 章节标题之前（即前一章内容的末尾）必须有一张跨栏分隔图片，全宽居中

### 图片规范

以下两张图片为固定资源，**不重新生成、不替换、不修改**，直接引用本地文件路径：

| 类型 | 固定路径 | 用途 | 对齐 |
|------|---------|------|------|
| 封面图 | `assets/AI智能体创富圈头图.png` | 文档开头唯一一张 | center, width=980 |
| 跨栏图片 | `assets/跨栏图片.PNG` | 每章之间分隔 | center, width=980 |

**注意**：封面图只在第一个 H1 前放一次；跨栏图片在第二~最后一个 H1（含附录）前各放一次。

### 插入流程（4 步）

#### 步骤 1：准备图片文件

将固定路径的封面图和跨栏图片复制到当前工作目录（lark-cli 要求文件位于工作目录下）：

```bash
cp "assets/AI智能体创富圈头图.png" "<工作目录>/AI智能体创富圈头图.png"
cp "assets/跨栏图片.PNG" "<工作目录>/跨栏图片.PNG"
```

**这些图片路径是固定的，不要使用其他图片或尝试重新生成。**

#### 步骤 2：上传图片到文档末尾

使用 `docs +media-insert` 将两张图片追加到文档末尾，生成对应的图片 block：

```bash
lark-cli docs +media-insert \
  --doc "<文档URL>" \
  --file "./跨栏图片.PNG" \
  --width 980 --align center

lark-cli docs +media-insert \
  --doc "<文档URL>" \
  --file "./AI智能体创富圈头图.png" \
  --width 980 --align center
```

**关键**：`--file` 参数只接受相对路径（相对于工作目录），不接受绝对路径。务必先 `cd` 到文件所在目录或复制文件到工作目录。

上传后记录返回的 block_id，如：
- 跨栏图片 block_id: `doxcnXXXX001`
- 封面图 block_id: `doxcnXXXX002`

#### 步骤 3：批量复制跨栏图片到各章末尾

使用 `block_copy_insert_after` 在每章最后一块后面复制跨栏图片实例。**注意**：是在前 H1 那一章的最后一块后面插入，而非在目标 H1 之前——因为之后紧跟着的就是下一章的 H1。

命令语法：

```bash
lark-cli docs +update --api-version v2 --doc "<文档URL>" \
  --command block_copy_insert_after \
  --src-block-ids "<跨栏图片block-id>" \
  --block-id "<目标H1那章的最后一块block-id>"
```

**需要确认各章最后一块 block-id**。通过 `docs +fetch --max-depth 4` 获取完整目录，找到每个 H1 下属最后一个子块（通常是最深的 H3 或 H4 的 block-id），或使用获取带 block-id 的详细结构来定位。

批量执行示例（以多个 `&&` 串联）：

```bash
# H1一末尾: block-id "doxcn_last_of_ch1"
# H1二末尾: block-id "doxcn_last_of_ch2"
# ...依此类推
lark-cli docs +update <...> --command block_copy_insert_after \
  --src-block-ids "doxcn_跨栏_img" --block-id "doxcn_last_of_ch1" \
  && \
lark-cli docs +update <...> --command block_copy_insert_after \
  --src-block-ids "doxcn_跨栏_img" --block-id "doxcn_last_of_ch2" \
  && ...
```

**覆盖范围**：第二~第十二章及附录（共 11~12 张），不包括第一章（封面图单独处理）。

#### 步骤 4：移动封面图到文档最开头

封面图上传后位于文档末尾，需要通过两步 `block_move_after` 交换到文档开头：

```bash
# 步骤 4a：将封面图移到 H1一 后面
lark-cli docs +update --api-version v2 --doc "<文档URL>" \
  --command block_move_after \
  --src-block-ids "<封面图block-id>" \
  --block-id "<H1一的block-id>"

# 步骤 4b：将 H1一 移到封面图后面（封面图在文档最前）
lark-cli docs +update --api-version v2 --doc "<文档URL>" \
  --command block_move_after \
  --src-block-ids "<H1一的block-id>" \
  --block-id "<封面图block-id>"
```

**原理**：两次移动交换了两个块的先后顺序，使封面图跑到了 H1 之上（即文档最开头）。

### 移动/复制块操作参考

| 命令 | 用途 | 语法关键点 |
|------|------|-----------|
| `block_move_after` | 移动已有块到指定块之后 | `--src-block-ids "src" --block-id "target"` → src 移到 target 后面 |
| `block_copy_insert_after` | 复制块并插入到指定块之后 | `--src-block-ids "src" --block-id "target"` → src 的副本出现在 target 后面 |

### 关键技术发现

1. **飞书云盘 URL 不可用于 `<img href>` 插入**：云空间文件 URL 需要鉴权，不能直接在 `block_insert_after` 的 `--content '<img href="..."/>'` 中使用。必须通过 `docs +media-insert` 先上传生成图片 block，再用 `block_copy_insert_after` 或 `block_move_after` 调整位置
2. **`docs +media-insert` 只能追加到文档末尾**：图片 block 创建时不支持指定位置，需要后续用移动/复制命令调整
3. **`block_copy_insert_after` 可复制图片 block**：图片 block 复制后保留原图引用（不为空）
4. **封面图的"交换法"**：两步 `block_move_after` 可以使任意 A B 交换顺序

## 修订版本记录

每次修改后在内存记录中更新修订版本号（rev 号），便于追踪变更历史。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
