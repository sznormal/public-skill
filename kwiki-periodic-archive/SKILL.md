---
name: kwiki-periodic-archive
description: >-
  WPS 知识库（kwiki-cli）周期性归档：把 N 天以前的内容归纳成一篇摘要文档写回知识库，再删除原文。
  适用于「每日AI新闻」「资讯收录」这类按日期累积的网页剪藏库。含三重护栏：原文完整备份落盘 → 摘要写回并回读校验 → 校验通过才删除。
  触发词：知识库归档、定期整理知识库、清理旧内容、7天归档、kwiki archive。
version: 1.0.0
---

# WPS 知识库周期性归档

## 适用场景

知识库内容按日期持续累积（如 `AI 收录/YYYY-MM-DD 0819/` 结构），需要定期把 N 天前的旧内容压缩成一篇可检索的摘要，再清理原文，避免库无限膨胀。

## 目标知识库

| 知识库 | kuid | drive_id | 归档周期 |
|---|---|---|---|
| 每日AI新闻（持续更新） | `0s_3159273167` | `3159273167` | 7 天 |

## 调用前置（必做）

```bash
export PATH="$PATH:/d/program/node/node_global"
export X_KWIKI_AUTH="<token>"   # WorkBuddy 的 bash 非交互，不读 ~/.bashrc
```

- CLI：`D:\program\node\node_global\kwiki-cli.cmd`
- pandoc：`C:\Users\29206\AppData\Local\Pandoc\pandoc`

## 三阶段流程（护栏不可跳过）

### 阶段 1：扫描 + 备份（只读，绝对安全）

```bash
python scripts/scan.py --kuid 0s_3159273167 --days 7 --outdir "<归档目录>"
```

产出：
- `tree.json` — 全量文件树（递归）
- `old_contents.jsonl` — **旧文件完整正文备份**（护栏 1：删除前必须存在，逐条校验非空）
- `digest.txt` — 每篇标题 + 420 字摘录，供Agent 归纳
- `plan.json` — 待删清单（能整文件夹删的整删，否则逐个删）
- 控制台输出：文件数、日期分布、主题分布

若旧文件数为 0 → 直接退出，不做任何写操作。

### 阶段 2：归纳 + 写回（Agent 完成）

Agent 读 `digest.txt` 撰写摘要 Markdown，须包含：
1. 归档说明（范围/文件数/字数/归档时间）
2. 内容整体画像（主题分布表 + **来源质量提示**：营销软文占比、重复收录）
3. 核心结论（5~8 条，带数据）
4. 分主题详述
5. 关键事件时间线表
6. **数据存疑提示**（不同来源口径冲突时必须标注）
7. 原文索引（按日期分组）

**写回必须用 docx 路线，不要用 file-convert**（见下方踩坑）：

```bash
pandoc "摘要.md" -f markdown -t docx -o "摘要.docx"
kwiki-cli kwiki file-upload --drive-id <drive_id> --file "./摘要.docx"
```

上传后用 `file-content` 回读，**确认正文长度 > 1000** 才视为成功（护栏 2）。

### 阶段 3：删除（护栏校验通过后）

```bash
python scripts/delete.py --plan "<归档目录>/plan.json" \
                         --require-kuid <新摘要文档kuid> \
                         --min-len 1000
```

脚本会先校验：
1. `old_contents.jsonl` 存在，条数 == 计划删除文件数，且每条正文非空
2. 新摘要文档 kuid 可回读且正文长度 ≥ `--min-len`
3. 待删清单中**不包含**新摘要文档自身

任一不满足 → **直接退出，不删除任何东西**。
通过后每批 ≤10 个执行，每批后回读根目录，最后输出汇总。

## 已知踩坑（重要）

| 坑 | 表现 | 正解 |
|---|---|---|
| `file-convert` md→otl | 正文异步同步失效，回读只剩标题（28 字符测试也一样） | 用 pandoc 转 docx 再 `file-upload` |
| 直接上传 `.md` | 存为 `doc_type=md`，`file-content` 报 `200365000`，**不可被问答索引** | 同上，走 docx |
| `file-list` 不递归 | 只返回当前层 | 用 `scripts/scan.py` 递归遍历 |
| WorkBuddy bash 无 token | `no token in keyring` | 每次调用前 `export X_KWIKI_AUTH` |
| `.workbuddy/settings.json` 的 env | 需重启 WorkBuddy 才生效 | 脚本内显式注入或重启 |

## 删除的安全性

- ⚠️ **测试 delete.py 时绝对不能用真实 plan.json**：护栏通过即会真删。测试护栏应使用"摘要 kuid 填一个不存在的 kuid（如 `0ltest_not_exist`）"或"临时把 plan.json 的 files/folders 置空"，切勿用真实摘要文档 kuid 验证。
- 2026-09-10 事故记录：用真实 plan + 真实摘要 kuid 做"护栏自测"，三道护栏全部通过导致误删 1 个文件夹（7 个文件）。幸有 `old_contents.jsonl` 备份，已从备份完整恢复（docx 路线 + file-rename 还原标题）。
- 恢复方法参考：`D:\BaiduSyncdisk\output\kwiki_archive\selftest\restore.py`（从备份 jsonl 重建文件：pandoc→docx→file-upload→file-rename）。
- 删除进回收站，保留期内可从 https://www.kdocs.cn/enttrash/0 恢复
- 原文正文已完整备份在 `old_contents.jsonl`（本地），删除后内容仍可追溯
- 摘要文档独立成文，删除原文不影响摘要

## 中间产物约定

归档目录：`D:\BaiduSyncdisk\output\kwiki_archive\<YYYY-MM-DD>\`
