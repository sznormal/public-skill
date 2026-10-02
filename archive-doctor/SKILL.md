---
name: archive-doctor
version: 1.1.0
display_name: 压缩包诊断与解压
display_name_en: Archive Doctor - Diagnose & Extract
category: engineering
author: Norma
agent_created: true
license: MIT
description: 诊断压缩包到底是「损坏」还是「加密/缺密码」，并批量解压。先用文件头+7z测试区分损坏与加密，再读包内注释找发布者线索、列出加密标志，然后做有限次试密（编号本身/编号变体/常见弱口令/同系列交叉），产出状态表与结论；拿到密码后用一条命令批量解压并校验。含文件"消失"时的回收站取证（$I/$R 元数据解析与还原）。内置本机 Windows 环境避坑（Bash PATH 重置、cygpath 路径归一化、PowerShell 无 stdout）。当用户说"帮我修复这个压缩包""解压失败""压缩包打不开""提示密码错误""rar损坏了""文件不见了/被删了""批量解压这些包"时使用。
description_zh: 诊断压缩包是损坏还是加密/缺密码，并批量解压。含文件头判型、7z 测试、注释取证、有限试密、状态表输出、批量解压校验，以及文件"消失"时的回收站元数据取证与还原；内置本机 Windows 环境避坑。
description_en: Diagnose whether an archive is corrupted or merely encrypted/password-locked, then batch-extract. Covers header sniffing, 7z testing, comment forensics, bounded password probing, status-table reporting, batch extraction with verification, and Recycle Bin forensics when files vanish.
---

# 压缩包诊断与解压（archive-doctor）

## 核心判断：**「解压失败」99% 不是损坏**

WinRAR / 7-Zip 在密码错误时也会弹「错误」「CRC 失败」，用户极易误判为文件损坏，
从而去找「修复工具」——**方向完全错误**。第一件事永远是：

> 用 `7z t` 测一遍。有 CRC 错误 → 真损坏；只报 `Wrong password` → 是加密。

## 触发词

帮我修复压缩包 / 解压失败 / 压缩包打不开 / 提示密码错误 / rar 损坏了 / 批量解压 / 解压码

---

## Step 0 · 环境前置（本机 Windows 必做）

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Program Files/7-Zip:$PATH"
```

| 坑 | 现象 | 解法 |
|---|---|---|
| Bash PATH 损坏 | `ls`/`head`/`dirname` 全 `command not found`，退出码 127 | 每条 Bash 命令开头重置 PATH（shell 状态不跨调用保留） |
| PowerShell 无输出 | exit code 0 但 stdout 为空 | 改用 Bash，输出重定向到文件 → 用 Read 工具读 |
| 原生 exe 拒收路径 | `/f/download/x.rar` 报「系统找不到指定的路径」 | 传 Windows 形式。**但注意下一行** |
| **参数被 MSYS 改写** | 传入 `F:\download`，脚本里收到的是 `F://download` | **用 `cygpath -w` 归一化**再交给 7z；`cygpath` 对 `/f/x`、`F:/x`、`F:\x` 三种形式都能正确转成 `F:\x` |
| `[ -f ]` 误判 | 文件确实存在却判定不存在 | 先确认是不是文件真没了（见 Step 0.5）；`cygpath -u` 转出的 POSIX 路径做存在性判断最稳 |

工具位置：`C:\Program Files\7-Zip\7z.exe`（本机无 WinRAR / unrar）。

## Step 0.5 · 先确认文件真的存在（血的教训）

**绝不能把「文件不存在」报告成「损坏」。** 二者的处置方向完全相反：
找不到文件 → 去回收站/移动盘/原路径找回；损坏 → 才谈修复。

```bash
PF=$(cygpath -u "$(cygpath -w "$DIR")/$id.rar")
[ -e "$PF" ] || echo "MISSING: 文件不存在"
```

**文件「凭空消失」时的取证流程**：
1. `ls -la <目录>` 看目录 mtime —— 若等于最近的时刻，说明刚有增删
2. 查回收站：`F:\$Recycle.Bin\<SID>` 与 `C:\$Recycle.Bin\<SID>`（`SID` 形如 `S-1-5-21-...-1003`）
3. 解析 `$I*` 元数据（v2 格式：8B 版本 | 8B 大小 | 8B FILETIME | 4B 文件名长度 | UTF-16LE 原路径），配对 `$R*` 才是真实数据
4. 比对 `$R` 文件实际字节数 == `$I` 记录的大小 → 数据完整、可完整还原
5. **报告时把「原路径 + 删除时刻 + 可还原」写清楚**，是否还原交给用户决定（属个人文件，需确认）

> ⚠️ 本机实测：`$I` 里的 FILETIME 按 **UTC** 呈现，报告给用户前要 **+8 小时**换算成东八区。
> 本机还有个特性：`rm` 会被 shim 转成「移入回收站」，所以被删的东西多数能捞回来。

---

## Step 1 · 文件头判型

```bash
od -A d -t x1 -N 16 "F:\\path\\archive.rar"
```

| 头部 hex | 格式 | 可列目录 |
|---|---|---|
| `52 61 72 21 1A 07 00` | RAR4 | 视压缩选项 |
| `52 61 72 21 1A 07 01 00` | RAR5（AES-256 常见） | 若 `Encrypted = -` 可列 |
| `50 4B 03 04` | ZIP | — |
| `37 7A BC AF 27 1C` | 7z | — |

## Step 2 · 测试区分「损坏 vs 加密」

```bash
"/c/Program Files/7-Zip/7z" t "F:\\path\\archive.rar" > /tmp/t.log 2>&1; echo $?
```

判读要点（`-slt` 列表模式同样适用）：

| 输出特征 | 结论 |
|---|---|
| `ERROR: Wrong password` | **加密，缺密码**。不要提修复 |
| `CRC Failed` / `Data Error` | 真损坏，才谈修复（`7z r` / RAR 有 recovery record 时可能救回） |
| `Method = ... AES:15:3` + `Encrypted = +` | AES-256 加密（RAR5 默认 PBKDF2 风格 KDF，暴力效率极低） |
| `Encrypted = -`（顶层） | 文件头未加密 → 目录仍可列出，能拿到文件名与原始大小 |

## Step 3 · 读包内注释取证

RAR/ZIP 的注释区常写着发布者说明，是**最省力的线索**（`7z l -slt` 会打印 `Comment = { ... }`）。

实战见到的典型套路：注释里只写「文件编码为：<编号>」+「付费获取解压码：淘宝/拼多多搜索『压缩包密码解除』」。
→ 说明**密码在卖家手里，不在包里**。此时应直接告知用户，不要陪着找修复工具。

## Step 4 · 列出内容

```bash
"/c/Program Files/7-Zip/7z" l -slt "F:\\path\\archive.rar" > /tmp/l.log 2>&1
```

记录：包内文件名、原始 Size、`Encrypted`、`Modified` 时间、`Method`。
多包同源时**比对注释与内文件命名规律**，判断是否同一发布者的系列包。

## Step 5 · 有限次试密（有边界！）

优先级顺序（本机约 0.3–1 秒/次，几十次完全可接受）：

1. **编号本身** —— 包名 `<ID>.rar`、内文件 `<ID>.pdf`，密码极可能就是 `<ID>`
2. **编号变体** —— `<ID>.pdf`、`<ID>a`、`a<ID>`、`qq<ID>`、`www.<ID>`、`<ID>_`、尾随空格
3. **常见弱口令** —— `123456` `12345678` `888888` `666666` `qwerty` `admin` `password` `20220826`（按文件 Modified 日期）
4. **同系列交叉** —— 把同目录其他同源包的编号逐个当密码试（验证是否共用密码）

把结果写进日志再读回（PowerShell 无 stdout 时尤其必要）。

**边界（不可越）**：
- ❌ 不下载密码字典 / 破解软件
- ❌ 不跑长时间暴力枚举（RAR5 + AES 下没意义）
- ✅ 只做**有限次**试密，然后如实告知「密码只能在卖家手里 / 需用户提供」

## Step 6 · 输出（Norma 老师格式）

**结论先行 + 状态表 + 三句话 + 行动项**。

状态表字段：压缩包（含大小）｜包内文件（含大小）｜状态。
状态用色：加密待密码 = 红；未加密可解压 = 绿。

拿到密码后的解压命令：

```bash
"/c/Program Files/7-Zip/7z" x -p"PASSWORD" "F:\\path\\archive.rar" -o"F:\\path\\<输出目录>"
```

批量（循环 + 逐包校验退出码）：

```bash
bash scripts/extract.sh "F:\\download" "PASSWORD" 33220235 30667467 32835492
```

## Step 7 · 收尾

- 临时目录用 `rm -rf` 清掉，不留垃圾
- 用户未提供密码时，**明确列出阻塞项**，不要含糊成「已尽力」
- 免费来源可正常解压时，主动指出对比（例：同名 ZIP 未加密、PDF 已解出），帮用户省掉一次付费
- **诊断跑完后不要假设文件还在**：如果中途用户可能动过文件，交付前回读一次确认

## 脚本（已实测）

| 脚本 | 用途 |
|---|---|
| `scripts/diagnose.sh <目录> [ID...]` | 批量判型 + 判损坏/加密/缺失，明细写入 `%TEMP%\archive-doctor-diag.log` |
| `scripts/extract.sh <目录> <密码> [ID...] [--out <目录>]` | 批量解压 + 逐包校验，有失败则退出码 1 |

```bash
export PATH="/usr/bin:/bin:/c/Windows/System32:$PATH"
bash scripts/diagnose.sh /f/download 33220235 30667467   # 指定编号
bash scripts/diagnose.sh /f/download                     # 扫整个目录
bash scripts/extract.sh /f/download 'PASSWORD' 33220235 30667467
```

回归用例（改脚本后必跑）：

| 场景 | 期望 |
|---|---|
| 目录内普通 ZIP | `[OK]` |
| 不存在的文件 | `[MISSING]` ← **绝不能是 `[DAMAGED]`** |
| 真实加密 RAR | `[ENCRYPTED]` |
| 解压密码错误 | `[FAIL] 退出码 2`，脚本退出码 1 |

## 反模式

| 别做 | 为什么 |
|---|---|
| 一上来推荐「RAR 修复工具」 | 加密包没有东西可修，纯浪费时间 |
| 把「密码错误」报成「文件损坏」 | 误导用户去走错误路径 |
| **把「文件不存在」报成「损坏」** | 最危险的误报：文件可能只是被删/被移，去回收站就能完整捞回，却让人去修一个不存在的文件 |
| 声称「无法解压」就结束 | 应给出唯一可行路径：索要密码 |
| 编造一个密码或猜测结果 | 违反不编造原则 |
| 靠 `[ -e ]` 单点判断就下结论 | 先排除「盘符未挂载 / 参数被 MSYS 改写」这两类假阴性 |
