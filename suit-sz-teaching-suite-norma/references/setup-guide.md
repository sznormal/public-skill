# 配置指南（环境准备与依赖安装）

本技能依赖三个本地 Python 包，**无外部服务、无账号、无凭据**，因此不需要登录、授权或 Token 管理。
所有安装都在受管 Python 的虚拟环境中进行，不污染系统环境。

## 一、先跑只读自检

```
<python> scripts/check_environment.py            # 人读
<python> scripts/check_environment.py --json     # 机器可读
```

输出四种状态：

| 状态 | 含义 | 下一步 |
|---|---|---|
| ready | 核心与当前所需依赖齐备 | 跳过本指南，直接用 `recommended_interpreter` 执行主流程 |
| partial | 核心可用，部分可选功能不可用 | 继续执行，只在结果中标注受影响功能 |
| needs_setup | 必需依赖缺失 | 只按下面"三、缺失项安装"补齐缺失项，然后重跑自检 |
| unavailable | 依赖存在但版本过低 | 按"四、版本不兼容"升级后重跑自检 |

自检**只读**：不安装、不登录、不授权、不修改配置、不启子进程、不访问网络。

## 二、解释器选择（最重要）

自检输出的 `recommended_interpreter` 是**能 import python-docx 的那个解释器**。
后续所有脚本都用它执行，不要用裸 `python` —— 沙箱与部分环境里 `python` 可能不在 PATH 上，
或指向未装 python-docx 的运行时。

自检会依次查找：当前解释器 → 受管默认虚拟环境 → 其它受管虚拟环境 → 受管运行时目录。
其中"受管默认虚拟环境"指：

```
~/.workbuddy/binaries/python/envs/default
├── Scripts/python.exe      # Windows
└── bin/python              # macOS / Linux
```

## 三、缺失项安装

### python-docx（必需：生成与解析 .docx）

- 官方主页：https://python-docx.readthedocs.io/
- 官方文档：https://python-docx.readthedocs.io/en/latest/
- 官方下载：https://pypi.org/project/python-docx/
- 认证方式：无需任何凭据
- 适用版本：>= 0.8.11（已验证 1.2.0）

步骤：

1. 若受管默认虚拟环境尚未创建，用受管 Python 创建它：

   ```
   ~/.workbuddy/binaries/python/versions/<版本>/python.exe -m venv ~/.workbuddy/binaries/python/envs/default
   ```

2. 在该虚拟环境中安装（不要全局安装，避免污染用户环境）：

   ```
   ~/.workbuddy/binaries/python/envs/default/Scripts/python.exe -m pip install python-docx
   ```

   macOS / Linux 把 `Scripts/python.exe` 换成 `bin/python`。

3. 最小验证：

   ```
   ~/.workbuddy/binaries/python/envs/default/Scripts/python.exe -c "import docx; print(docx.__version__)"
   ```

   更完整的验证：`<该解释器> scripts/selftest.py`，8 项全部 PASS 即环境可用。

### openpyxl（可选：读取 .xlsx 教学大纲）

- 官方主页：https://openpyxl.readthedocs.io/
- 官方文档：https://openpyxl.readthedocs.io/en/stable/
- 官方下载：https://pypi.org/project/openpyxl/
- 认证方式：无需任何凭据
- 适用版本：>= 3.0.0（已验证 3.1.5）

```
<该解释器> -m pip install openpyxl
<该解释器> -c "import openpyxl; print(openpyxl.__version__)"
```

缺失时不影响主流程：改为请用户以文本或表格截图提供模块与学时清单。

### olefile（可选：解析旧版 .doc）

- 官方主页：https://olefile.readthedocs.io/
- 官方文档：https://olefile.readthedocs.io/en/latest/
- 官方下载：https://pypi.org/project/olefile/
- 认证方式：无需任何凭据
- 适用版本：>= 0.46（已验证 0.47）

```
<该解释器> -m pip install olefile
<该解释器> -c "import olefile; print(olefile.__version__)"
```

缺失时不影响主流程：请用户把 `.doc` 另存为 `.docx` 后继续。

### 可选增强（不进依赖清单，缺失自动跳过）

- LibreOffice：docx 转 PDF 做渲染检查。
- PyMuPDF：PDF 逐页渲染成图核对。

## 四、版本不兼容

自检报告 `unavailable` 且 `reason_code=version_incompatible` 时：

1. 查看报告的实测版本，与上面的最低版本比对。
2. 升级到不高于当前 Python 支持的最新版：

   ```
   <该解释器> -m pip install --upgrade python-docx
   ```

3. 重跑自检；`ready` 后不再重复引导。

## 五、权限、存储与安全

- 全程不使用账号、Token、API Key 或 Cookie；**任何凭据都不需要用户在对话中提供**。
- 只从 PyPI 官方源安装，不使用未知镜像，不使用 `sudo` / 管理员全局安装。
- 依赖只写入受管虚拟环境目录，与系统 Python 隔离。
- 脚本对文件系统只做两件事：读取技能目录内的模板与输入文件、把产物写到用户指定输出路径；
  不删除文件、不改动用户模板（用户自带模板只读，产物一律另存新文件）。

## 六、卸载与回滚

```
<该解释器> -m pip uninstall python-docx openpyxl olefile
```

整个受管虚拟环境可直接删除目录回滚：`~/.workbuddy/binaries/python/envs/default`。
卸载后主流程降级为 Markdown 产出（见 `SKILL.md` 的降级策略），不会停工。

## 七、核验记录

| 项目 | 值 |
|---|---|
| 核验日期 | 2026-09-16 |
| 适用版本 | 技能 1.2.0 |
| 已验证环境 | Windows + 受管 Python 3.13，python-docx 1.2.0 / openpyxl 3.1.5 / olefile 0.47 |
| 未验证环境 | macOS、Linux（脚本只用标准库与 python-docx，路径按 `Path.home()` 解析，未实测） |
| 核验方式 | 本机运行 `scripts/check_environment.py`（返回 ready）与 `scripts/selftest.py`（8/8 PASS） |
