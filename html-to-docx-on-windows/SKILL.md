---
name: html-to-docx-on-windows
description: 在 Windows 上让 tencent-docx 插件的 HTML→DOCX 转换跑通。当 setup-html-to-docx.sh 报 exit=2、提示 "Installing html-to-docx dependencies" 后失败，或 $HOME/.venv-html-to-docx 建完就消失、被建到 D:\c\Users\... 时使用。触发场景：调用 html_to_docx convert、S3 doc-converter、导出 Word 版交付物、tencent-docx 流水线在 Windows 卡在环境准备。
version: 1.0.0
agent_created: true
---

# HTML → DOCX 转换：Windows 环境修复

## 症状

`bash <plugin_root>/scripts/wb/local/setup-html-to-docx.sh` 在 Windows + Git Bash 下必然失败：

```
✓ Python 3.12 available
▶ Creating venv at /c/Users/<user>/.venv-html-to-docx
✓ venv ready: /c/Users/<user>/.venv-html-to-docx
▶ Installing html-to-docx dependencies (only-binary wheels)   ← 到此 exit=2
```

且此后 `$HOME/.venv-html-to-docx` **不存在**，反而多出一个 `D:\c\Users\<user>\.venv-html-to-docx`。

## 根因（两个独立缺陷，都在脚本里）

1. **路径翻译**：`uv` 是 Windows 原生程序，收到 POSIX 路径 `/c/Users/...` 不会像 curl/git 那样自动转换为 `C:\Users\...`，而是当作「D 盘下的相对/绝对路径」处理 → 实际建到 `D:\c\Users\...`。所以脚本自己 `ls $VENV_DIR/bin/python` 永远找不到刚建好的 venv。
2. **目录布局**：脚本按 Unix 布局取解释器 `$VENV_DIR/bin/python`，但 `uv venv` 在 Windows 上产出的是 `$VENV_DIR/Scripts/python.exe`。于是第 4 步 `uv pip install --python "$VENV_DIR/bin/python"` 必然失败（exit 2）。

> 结论：**不要试图改脚本或反复重跑**。直接跳过脚本，手工两步建环境。

## 修复步骤

```bash
export PATH="$HOME/.local/bin:$PATH"          # uv 若已装在 ~/.local/bin
PLUGIN="<plugin_root>"                        # 形如 .../tencent-docx/<ver>/，务必先探测（见下）
REQ="$PLUGIN/skills/html-to-docx/scripts/requirements.txt"
HTMLDOCX_DIR="$PLUGIN/skills/html-to-docx/scripts"
PY="C:/Users/<user>/.venv-html-to-docx/Scripts/python.exe"

# 0. 清掉可能被建到错位置的残留
rm -rf "D:/c/Users/<user>/.venv-html-to-docx"

# 1. 用 Windows 风格路径建 venv（关键：C:/... 而不是 /c/...）
uv venv --python 3.12 "C:/Users/<user>/.venv-html-to-docx"

# 2. 用 Scripts/python.exe 装依赖
uv pip install --python "$PY" --only-binary=:all: -r "$REQ"
```

依赖清单（requirements.txt）：`python-docx` `html-for-docx` `beautifulsoup4` `lxml` `httpx` `Pillow` `click` `pytest`。

`--only-binary=:all:` 必须保留：`lxml` 在新 Python 上无 wheel 时会走源码编译，Windows 下缺 libxml2/libxslt 必挂。要求 **Python 3.12**。

## ⚠️ 每次转换前必做的两项探测（环境会自己坏掉）

实测该环境**会在会话之间被破坏**，两种形态都遇到过：

1. **`site-packages` 被清空**——解释器 `Scripts/python.exe` 还在，但 `import docx` 报 ModuleNotFoundError。
2. **插件缓存目录短暂不可用／版本号变更**——`cd <plugin>/skills/html-to-docx/scripts` 报 No such file or directory，但几秒后 `find` 又能找到；或路径里出现新的版本目录。

所以**不要复用上次记下的路径**，每次转换先跑：

```bash
# 探测 1：定位当前插件版本目录（不要写死）
ls -d "$HOME/.workbuddy/plugins/cache/workbuddy-builtin/tencent-docx/"*/
# 选最新的 5.x 那个，赋给 PLUGIN

# 探测 2：依赖是否还在
"$PY" -c "import docx,bs4,lxml,httpx,PIL,click; print('deps OK')"
# 报错则重装（不必重建 venv，解释器在就行）
uv pip install --python "$PY" --only-binary=:all: -r "$PLUGIN/skills/html-to-docx/scripts/requirements.txt"
```

venv 本身若连 `Scripts/python.exe` 都没了，才走完整「修复步骤」。

其他易踩点：

- **包名 ≠ 模块名**：`html-for-docx` 装出来的模块名不是 `html_for_docx`。别用它做探测，直接 `import html_to_docx`（配合 `PYTHONPATH`）更可靠。
- 转换前务必 `cd` 到 `<plugin>/skills/html-to-docx/scripts`，否则报 `No module named html_to_docx`。

## 转换

```bash
cd "$HTMLDOCX_DIR"          # cwd 设为 scripts/，让 html_to_docx 包可导入
"$PY" -m html_to_docx convert "<input.html>" -o "<output.docx>"
```

成功时 stdout 是 JSON：`{"success": true, "docx_path": "...", "warnings": [], "fields": [...]}`。

冒烟测试（可选）：

```bash
PYTHONPATH="$HTMLDOCX_DIR" "$PY" -c "import sys;sys.path.insert(0,'$HTMLDOCX_DIR');import html_to_docx;print('OK')"
```

## 关于输出里的 `fields`

`fields` 里的 `auto_N` 是**自动识别的中文表单空位**，会在 DOCX 里生成 `w:bookmarkStart/bookmarkEnd` 书签（不是 `fldChar` 域）。表现：

- **不可见、不影响打印**，正常打开无异常。
- 来源是表格里**内容为空的单元格**（代码判定 `cell.get_text(strip=True)` 为空），把左侧单元格文字当作 label。
- 若一行里**连续多个空单元格**，第 2 个之后的 label 会退化成上一个单元格的令牌文本 `__DOCXFIELD_<hex>__` —— 只是书签名难看，**无视觉影响**。
- 想彻底避免：别留纯空单元格，填入 `—`、`（授课后填写）` 之类占位文字。`&nbsp;` 无效（`\xa0.strip()` 仍为空串）。
- 无法用 `data-docx-field` 抑制：`cell.find(attrs=...)` 只搜后代，空单元格没有后代。

## 环境事实

- **沙箱不会回滚 `$HOME` 写入**（已实测：沙箱内 `$HOME` 建文件，下一次调用仍在）。venv 消失纯粹是上面的路径翻译问题，**无需 `dangerouslyDisableSandbox`**。
- ~~环境可长期复用~~ **更正**：实测该环境**跨会话会被破坏**（`site-packages` 被清空、插件版本目录变更），因此**每次都要做前两项探测**，不要默认它还好着。
- **切勿再跑 `setup-html-to-docx.sh`**——它会 `rm -rf` 掉可用环境、再建到错误位置，一步就把好环境弄坏。
- 验证产物完整性：用 venv 里的 python + `python-docx` 读段落/标题/表格数，并解包 `word/document.xml` 检查 `sectPr`（封面节无 footerReference、正文节含 PAGE/NUMPAGES 与 `w:pgNumType w:start`）。

## 交付约定

转换成功即视为流水线终点。若任务要求「强制打开预览」，转换后立刻把 `.docx` 交给 `present_files`。

---

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
