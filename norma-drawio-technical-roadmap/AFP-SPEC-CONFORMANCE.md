# AFP-SPEC 合规证书

| 项目 | 内容 |
|---|---|
| skill | norma-drawio-technical-roadmap |
| 版本 | 2.0.0 |
| 类型 | Independent（Pattern 5） |
| 领域 | 学术研究 / 教育培训（科研与教改项目制图） |
| 目标等级 | Bronze |
| 判定 | certified（含 1 项已记录偏差） |
| 判定日期 | 2026-09-07 |

## 判级结果

```
╭─ AFP-SPEC 合规检查报告 ───────────────────────────╮
│ skill：norma-drawio-technical-roadmap · 目标：bronze
│ §5 Hard Stops：       6/7   ⚠️ 偏差：H1（已记录，见下）
│ §6 Evidence Chain：   6/6   ✅
│ §7 Output Structure： 5/5   ✅（O6 登记为不适用）
│ §8 Handoff：          2/2   ✅（Independent，仅查适用项）
│ 综合：Bronze certified
╰──────────────────────────────────────────────────╯
```

## §5 Hard Stops

| 项 | 结果 | 依据 |
|---|---|---|
| H1 每 stage 结尾有交付确认单 | ⚠️ 偏差 | 采用条件 Hard Stop，只在三种信号命中时输出确认单，非每阶段必停 |
| H2 确认单含 NEXT 行 | ✅ | 确认单模板含 `👉 NEXT：回复 A / B / Back 重来` |
| H3 不允许自动推进的纪律条款 | ✅ | 明确「不替用户拍板，不合并成一次最终确认」 |
| H4 Next / Back / Edit 三件套 | ✅ | 通用指令表含三件套，另加 Status / Continue / Export |
| H5 方向性决策点多方案 | ✅ | 确认单要求列 2—3 个选项，各带优势与代价 |
| H6 Back 回滚语义 | ✅ | 「回退上一阶段，该阶段落盘文件作废重做，其余保留」 |
| H7 乱序请求防御 | ✅ | 越阶要求须先补齐前置阶段并落盘 |

**H1 偏差说明**：本 skill 的核心场景是「给图给资料、一句话出图」，用户明确要求产出不带解释文字。每阶段硬停会直接破坏该体验，因此改为条件触发式 Hard Stop——歧义、缺项、版式认不出三种信号必停，其余一路推到底，同时用步步落盘保证用户事后可核查。此取舍已记录，升级 Silver 时需重新评估。

## §6 Evidence Chain

| 项 | 结果 | 依据 |
|---|---|---|
| E1 方法论出处真实 | ✅ | 判为工程实践型而非经典移植型：版式库与 XML 规范源自 draw.io 官方导入格式与制图工程实践，非文献引用 |
| E2 涉及引用的 stage 写明验证动作 | ✅ | S3 逐节点填来源列（资料名 + 章节/页码/行号） |
| E3 领域证据链标准落实 | ✅ | `references/evidence-and-terms.md` 落实学术领域的溯源要求 |
| E4 unverified 标记规则 | ✅ | 三态判定 verified / unverified / 待补充 |
| E5 不承诺做不到的能力 | ✅ | 硬规则「只归纳不编造」，停止条件明确 |
| E6 数据类输出要求来源 + 时间 | ✅ | 指标类内容来源列追加采集或统计时间 |

## §7 Output Structure

| 项 | 结果 | 依据 |
|---|---|---|
| O1 HUD JSON 骨架 | ✅ | `manifest.json` schema 含 inputs / stage_status / artifacts / validation |
| O2 每个 stage 有输出 schema | ✅ | 阶段路由表含落盘列；`02-内容结构.md` 有六列 schema |
| O3 最终交付物清单明确 | ✅ | 主控「交付物」节列明 5 个文件 |
| O4 确认单格式统一 | ✅ | 单一模板，全 skill 不漂移 |
| O5 步步落盘为具名文件 | ✅ | `01-版式规格.md`、`02-内容结构.md`、`03-坐标布局.md`、`<图名>.drawio`、`manifest.json` |
| O6 用户核查清单 | N/A | 登记为工具型（单程产出、无多阶段人工决策），Bronze 免配 |

**O5 落盘判据复核**：换个全新对话，只凭 `drawio-projects/<图名>/` 下的文件能否接着改图——能。`manifest.json` 记录阶段状态与产物路径，`03-坐标布局.md` 记录节点 id 与坐标，`01-版式规格.md` 记录配色与字体，无需重读参考图。

## §8 Multi-Agent Handoff

Independent skill，仅查适用项。

| 项 | 结果 | 依据 |
|---|---|---|
| M2 状态磁盘持久化格式 | ✅ | `manifest.json` 由 `scripts/init_project.py` 生成 |
| M3 下游有状态读取说明 | ✅ | `Continue <项目路径>` 指令读取 manifest 续跑 |

M1、M4—M6 属 Orchestrator 与 Shared Primitive 范畴，不适用。

## 已查的协作项

- **触发冲突预检**：本机仅 `llm-wiki-ingest` 出现「流程图」字样，其领域为知识库摄入，不构成本 skill 的触发冲突。附带效应：本 skill 落盘的 `.drawio` 会被其自动摄入知识库，属协作而非冲突。
- **Shared Primitives 复用**：本机 AFP 生态内无可复用的 primitive，登记为不适用。

## 升级路径

升 Silver 需补：§7 输出 schema 全套（每个阶段的结构化字段定义）、《用户核查清单》、3 个真实用户案例记录，并重新评估 H1 偏差。
