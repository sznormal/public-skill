# 技能整改报告 · suit-sz-teaching-suite-norma

- 送审技能：`suit-sz-teaching-suite-norma`
- 原版本 / 新版本：1.1.0 → **1.2.0**
- 审核反馈：沙箱评测未达标准，评级"低质量"，审核时间 2026-09-14
- 整改依据：https://open.workbuddy.cn/docs/skill 的技能结构与 frontmatter 字段规范
- 整改日期：2026-09-16
- 整改方式：先复现、再定位、后修改，全程以平台校验器的机器结论作为通过判据

---

## 一、根因定位（先复现，不猜）

用平台侧 `skill_ops.py validate` 对原包做基线体检，得到 **19 项 error**；`preflight` 得到 **14 项 high**。
两类问题叠加，正是"沙箱评测未达标准"的直接技术原因。

### 根因 1（致命）：frontmatter 用了 YAML 折行块标量，平台解析直接失败

平台解析器只支持**顶层 `key: value`**，不支持 `>` 折行续行。原 SKILL.md 的 `description_zh`、
`description_en`、`description` 三个字段全部写成折行块标量，导致：

- 17 处 `frontmatter_invalid`（第 7–17 行等，续行被当成非法字段行）
- `description` 无法解析 → 报"description 必须是 20—1024 字符完整描述"

**触发词依赖 name 与 description，description 解析不出来，技能在平台上等于没有触发描述**，
这是评审判"低质量"最可能的一击。

### 根因 2（致命）：依赖型 Skill 缺 `references/setup-guide.md`

平台规则要求依赖型 Skill 必须同时具备 `skill-dependencies.json` + `scripts/check_environment.py`
+ `references/setup-guide.md` 三件套。原包只有前两件，报 `dependency_guide`："依赖型 Skill 必须包含配置指南"。

### 根因 3（功能性）：评测环境里 `python` 命令不存在，脚本却按裸 `python` 调用

原 SKILL.md 第一步写着"开工前运行 `python <SKILL_DIR>/scripts/check_environment.py`"。
实测在干净环境里该命令直接失败（`python: command not found`）；即便存在，
受管解释器也未安装 python-docx，而**真正可用的解释器在 `~/.workbuddy/binaries/python/envs/default`**
（python-docx 1.2.0 已就位）。原自检只用 `sys.executable` 判断，看不到这个环境，
于是必然把运行级别误判为 L2，整条链路降级成 Markdown 产出——技能最核心的 docx 能力在评测中根本没跑起来。

### 根因 4（正确性）：文档引用了一批并不存在的函数

`stages/02`、`stages/03`、`modules/sziit-format.md`、`references/format-spec.md` 反复要求调用
`insert_heading_table_before()`、`strip_cell()`、`append_cell()`、`write_cell()`，
但 `scripts/docx_helpers.py` 里**一个都没有**。照着技能做，代码必然 `AttributeError`。

### 根因 5（规范与洁净度）

- 非规范产物：根目录 `README.md`、`AFP-SPEC-CONFORMANCE.md`（自评"Silver"证书，且版本停在 1.0.0）、
  `skill-dependencies.json` 之外的自定义依赖说明；`scripts/__pycache__/` 下 7 个 `.pyc` 二进制
  （预检直接判 `unsupported_script` high ×8，导致 `static_scan_status: blocked`）。
- 目录结构：`stages/`、`modules/` 不在平台三目录（`references/`、`scripts/`、`templates/`）之内，
  且存在 **reference 互相加载**（`modules/politics-integration.md` 指向 `stages/04`，
  `modules/sziit-format.md` 被 `stages/02`、`stages/03` 引用），违反"加载式引用只由顶层 SKILL.md 发起"。
- 内容重复：同一张排版规则表在 SKILL.md、`modules/sziit-format.md`、`references/format-spec.md` 出现三遍。
- 历史残留：`stages/03` 里留着"旧 teaching-docs-writer/references/course-plan.md 逻辑（已并入本套件）"这类变更记录。
- SKILL.md 正文 260 行，把路由与全部细则混在一起，渐进式披露不成立。

---

## 二、整改对照表

| # | 问题 | 修法 | 复验证据 |
|---|---|---|---|
| 1 | frontmatter 折行块标量致解析失败（17 error） | 三个 description 字段改写为**单行 `key: value`**；补齐平台字段 `category: writing`；保留 `version`、`agent_created: true` | `validate` → `ok=true, issues=0` |
| 2 | 缺配置指南 | 新增 `references/setup-guide.md`（146 行）：四态说明、解释器选择、三依赖安装与验证、权限与存储、卸载回滚、核验记录；清单内全部官方 URL 在指南中逐字出现 | `dependency_guide` 相关 3 类 issue 全部消失 |
| 3 | 裸 `python` 不可用 + 误判运行级别 | 重写 `check_environment.py`：**只读**、无子进程、无网络；在当前解释器与受管 Python/虚拟环境目录中查找可 import python-docx 的解释器，输出 `recommended_interpreter` 与 L1/L2；SKILL.md 明确"不要用裸 python，后续都用推荐解释器" | 用**未装 docx 的受管解释器**执行自检，仍返回 `ready` + 正确推荐解释器（见下"四、关键证据"） |
| 4 | 引用不存在的函数 | 在 `docx_helpers.py` 中真正实现 `insert_heading_table_before`、`strip_cell`、`write_cell`、`append_cell`、`set_first_line_chars`、`set_exact_line_spacing`、`clear_runs`、`drop_element`、`add_header_para`；删除 `reset_para` 误用导致的 `TypeError` | 自测第 3/4/5 项 PASS |
| 5 | 缺确定性产出与验收手段 | 新增 `render_course_standard.py`（JSON → 合规 docx，模板作外壳、清空正文重建）、`validate_docx.py`（回读 XML，逐项输出位置/期望/实测，判 PASS/FAIL）、`selftest.py`（8 项端到端自测，含反向用例） | 自测 8/8 PASS；反向用例确认校验器真能抓错 |
| 6 | 非规范产物与二进制垃圾 | 删除 `README.md`、`AFP-SPEC-CONFORMANCE.md`、`scripts/__pycache__/`、`inspect_full.py`、`inspect_header.py`、`test_helper.py`（后三者已被 `validate_docx.py` 取代） | `preflight`：high 由 14 → **0**，`static_scan_status: pass`，`scan_complete: true` |
| 7 | 目录结构不合规、reference 互相加载 | `stages/02~04` → `references/workflow-*.md`；`modules/*` → `references/format-rules.md`、`references/politics-integration.md`；`stages/01-intent.md` 的路由逻辑上收到 SKILL.md；删除被合并的 `references/format-spec.md`；清除全部跨 reference 指向 | 全文扫描 `stages/`、`modules/`、`format-spec` 零残留；`validate` 无 `nested_reference` / `dead_reference` |
| 8 | 同一规则三处重复维护 | `format-rules.md` 成为排版唯一权威来源（合并原 `modules/sziit-format.md` + `references/format-spec.md`）；SKILL.md 只留路由与三条流程铁律，不再复制字体字号表 | SKILL.md 由 260 行 → **126 行**（平台上限 500 行） |
| 9 | 历史记录与状态标注 | 删除"旧 teaching-docs-writer 已并入""（已实测）""七·补/七·再补"等变更痕迹，章节重新编号 | `validate` 无 `state_marker` / `history_section` |
| 10 | 依赖清单与实际不符 | `olefile` 由 required 改 false；补 `markdown-export`、`format-validate` 两项能力与对应降级；三项依赖的降级矩阵与技能实际 L1/L2/L3 策略对齐 | `validate` 无 `dependency_*` 类 issue |

---

## 三、复验结果

| 检查 | 命令 | 整改前 | 整改后 |
|---|---|---|---|
| 结构校验 | `skill_ops.py validate` | `ok=false`，19 error | **`ok=true`，0 issue** |
| 安全预检 | `skill_ops.py preflight` | `blocked`，14 high + 3 medium，`scan_complete=false` | **`pass`，0 high + 7 medium**（7 项均为产出文档所必需的写文件操作，中危） |
| 端到端自测 | `scripts/selftest.py` | 无此能力 | **8/8 PASS** |
| 环境自检（干净解释器） | `check_environment.py` | 误判 L2 | **`ready`，L1，推荐解释器正确** |
| 四态降级 | 同上（隐藏受管目录） | 无四态 | **`needs_setup`，退出码 1，只列缺失项** |
| 渲染→回读 | `render_course_standard.py` + `validate_docx.py` | 无此能力 | **PASS** |
| frontmatter 可解析性 | 单行 key: value | 解析失败 | **description 等字段均可解析，长度在 20–1024 内** |

## 四、关键证据

**证据 1 · 环境自检不再被"裸 python 不存在"卡死**（用未装 python-docx 的解释器执行）：

```
[OK  ] python-docx   python-docx 1.2.0（来源：受管默认虚拟环境（...\envs\default\Scripts\python.exe））
总体状态：ready
推荐解释器：...\envs\default\Scripts\python.exe
运行级别：L1
```

**证据 2 · 端到端自测 8/8**：

```
[PASS] 1 环境自检 —— status=ready 解释器=...envs\default\Scripts\python.exe
[PASS] 2 环境状态机四态 —— 实测=['ready','partial','needs_setup','unavailable']
[PASS] 3 缩进与节点删除 —— firstLineChars=200 删除后仍挂树=False
[PASS] 4 标题在表格上方 —— body 顺序=['p','tbl','sectPr']，表格数=1
[PASS] 5 单元格先裁剪再写 —— 写入5行 实得5行 末行=第5行内容
[PASS] 6 渲染并回读校验 —— 段落=14 表格=2 失败=0
[PASS] 7 反向用例能被抓住 —— 注入1处破坏 → 校验报错3项（字体族 期望仿宋系 / 实测 微软雅黑）
[PASS] 8 Markdown 降级产出 —— 含版式对照表
```

第 4 项对应"标题必须在表格上方"这条历史返工点；第 5 项对应"先写后裁剪会把末行顶出单元格"这条坑；
第 7 项是校验器的**反向用例**——证明它不是一个只输出 PASS 的橡皮图章。

**证据 3 · 缺依赖时只展示缺失项**（隐藏受管 Python 目录模拟干净机器）：

```
[MISS] python-docx / openpyxl / olefile
总体状态：needs_setup      退出码 1
下一步：只展示缺失必需项的配置步骤，配置完成后重新检查
```

## 五、本次交付物

- 整改后的技能目录：`~/.workbuddy/skills/suit-sz-teaching-suite-norma/`（v1.2.0）
- 可直接提交的打包件：`suit-sz-teaching-suite-norma-v1.2.0.zip`（20 个文件，98,871 字节，含顶层技能目录）
- 整改前完整备份：工作区 `_audit/skill-backup-before/`

最终目录结构：

```
suit-sz-teaching-suite-norma/
├── SKILL.md                              126 行，仅路由 + 铁律 + 索引
├── skill-dependencies.json               6 能力 / 3 依赖 / 6 项功能降级
├── references/
│   ├── format-rules.md                   排版唯一权威来源
│   ├── workflow-course-standard.md       写课标
│   ├── workflow-lesson-schedule.md       写教案 + 授课计划
│   ├── workflow-supervisor.md            督导一致性检查
│   ├── politics-integration.md           思政点映射
│   ├── teacher-checklist.md              素材收集清单
│   └── setup-guide.md                    配置指南（平台必备件）
├── scripts/
│   ├── check_environment.py              只读四态自检
│   ├── render_course_standard.py         JSON → 合规 docx
│   ├── validate_docx.py                  回读校验（验收标准）
│   ├── selftest.py                       8 项端到端自测
│   ├── docx_helpers.py                   公共排版函数（补齐缺失函数）
│   ├── export_markdown.py                L2 降级产出
│   ├── doc_extract.py                    旧版 .doc 提取
│   └── progress_dashboard.py             进度仪表盘
└── templates/                            3 个校版空白模板
```

## 六、未覆盖与已知限制

- **教案 / 授课计划模板的填充脚本未脚本化**：目前仍由工作流指导模型用 `docx_helpers.py` 组装，
  `render_course_standard.py` 只覆盖课标。原因是两份模板的合并单元格结构差异大，
  强行抽象成通用脚本反而更易出错；已用 `validate_docx.py --profile lesson|schedule` 兜住验收。
- **未在 macOS / Linux 实测**：脚本只用标准库与 python-docx，路径按 `Path.home()` 解析，
  但未在真实 mac/Linux 上跑过，`setup-guide.md` 已如实标注。
- **xlsx 大纲与旧版 .doc 两个降级分支未用真实样本验证**，清单中 `evidence_label` 标为"未验证"。
- **中危预检 7 项**为写文件与创建目录，是本类"产出文档"技能的必要行为，非风险项；
  平台 `manual_review_required` 恒为 true 属其固定策略，不代表存在问题。
