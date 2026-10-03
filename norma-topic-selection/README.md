# norma-topic-selection · 理工科选题助手

> 从"已完成文献综述"到"可开题的选题与研究计划"的八阶段交互流。
> 方法论由 AFP 流程构建，内容综合四版方案评估（V1 六步法 / V2 双轴定位 / V3 闭环模块 / V4 机理深度）。

## 解决什么问题

| 常见困境 | 本 skill 的机制 |
|---|---|
| 综述读完了，不知道空白在哪 | 证据矩阵 12 字段 + 五条矿脉（limitations 高频抱怨 / 应用域×方法空格 / 矛盾格 / 孤证区 / 时间拐点） |
| 把"没人做"当成好选题 | 双轴分离：先定竞争地形（四区），再判空白性质（8 类） |
| 假空白（检索没覆盖到） | 六重门验伪：3 组检索式 + 预印本 + 最近邻反证 + 真人 + 撞题 + 可行机理 |
| 评分被总分掩盖 | 一票否决：任一维 <50 否决、真实性 <70 否决、师生分歧 >20 强制重议 |
| 做半年才发现投不进去 | P0 逆向定标：Day 1 就锁定目标刊与撞题风险表 |
| 题目太大做不完 | MVP 最小验证 + 事前固定止损规则 + 退路设计 |

## 八阶段

| 阶段 | 名称 | 产出物 |
|---|---|---|
| P0 | 方向与出口锁定 | `scope_lock.md` |
| P1 | 证据矩阵 | `evidence_matrix.md`（≥40 行） |
| P2 | 空白扫描与双轴定位 | `gap_candidates.md`（8–10 个） |
| P3 | 六重门验伪 | `gate_record.md` |
| P4 | 选题定型 | `gap_statement.md` |
| P5 | 可发表性评分 | `scorecard.md` + `scorecard.json` |
| P6 | MVP 与止损 | `mvp_plan.md` |
| P7 | 研究计划与投稿策略 | `research_plan.md` |

## 目录结构

```
norma-topic-selection/
├── SKILL.md                     薄路由主控（HUD + 阶段表 + 触发隔离）
├── stages/                      8 个阶段文档（主控按需 Read）
│   ├── 00-scope-lock.md         逆向定标：先看出口
│   ├── 01-evidence-matrix.md    12 字段矩阵 + 三个挖掘动作
│   ├── 02-gap-scan.md           双轴定位 + 五条矿脉 + 三问闸
│   ├── 03-verification-gates.md 六重门 + 最近邻表 + 反证清单
│   ├── 04-topic-finalize.md     Gap Statement / RQ / 假设
│   ├── 05-scorecard.md          8 维评分 + 否决规则
│   ├── 06-mvp-stoploss.md       MVP 六要素 + 止损规则
│   └── 07-research-plan.md      七节计划 + 时间表 + 投稿策略
├── modules/                     按需加载的方法论细则
│   ├── gap-taxonomy.md          8 类空白 + 消歧三问 + 机理相容铁律
│   ├── verification-protocol.md 六重门可执行动作与留档格式
│   ├── scoring-and-veto.md      评分锚点与否决规则说明
│   ├── topic-templates.md       填空模板库
│   └── norma-topic-antipatterns.md  16 条理工科选题反模式
├── templates/                   7 份交付物模板
└── scripts/                     纯标准库，无需 pip
    ├── matrix_lint.py           证据矩阵体检
    └── score_topic.py           评分卡计算 + 否决 + 双人分歧检测
```

## 脚本

```bash
# P1 收尾：矩阵体检（行数/必需列/稀疏列/矛盾/孤证）
python scripts/matrix_lint.py outputs/topic-selection/evidence_matrix.md

# P5 收尾：评分卡核对（加权总分 + 一票否决 + 师生分歧）
python scripts/score_topic.py outputs/topic-selection/scorecard.json
```

两个脚本只做机械统计与规则判定，**不判断空白是否成立、不给改进建议**。

## 使用边界

- ❌ 不写文献综述正文 → 走 `norma-lit-review`
- ❌ 不选具体期刊 → 走 `norma-sci-journal-selection` / `norma-ssci-journal-selector` / `norma-cn-core-journal-selection`
- ❌ 不代填文献、DOI、性能数值 → 未核实信息一律标 `[待核]`
- ❌ 不代做实验、不替用户做导师判断

## 版本与版权

v1.0.0（2026-10-03）· AFP 流程构建 · 维护者 Norma（郑洪英）

© 2026 Norma（郑洪英）· 深圳信息职业技术大学 · 中德机器人学院
依据 **PolyForm Noncommercial License v1.0.0** 授权（完整条款见仓库根目录 `LICENSE`）· 可公开、可修改、可再分发，**禁止商业使用**；教育机构教学使用属许可用途。
版本许可说明：**自初始版本起**适用本协议。
