# WikiSkill 架构原理

> 来源：*WikiSkill: Compiling Agent Experience into Persistent Knowledge for Skill Evolution*
> (arXiv:2608.27454，Google，2026-08-27)

## 1. 问题形式化

- 数据集 $\mathcal{D}$ 划分为互斥的 train / val / test
- Agent $\pi$ 配备工具集 $\mathcal{U}$ 与技能集 $S$；执行任务 $x_i$ 产生轨迹
  $\tau_i = (o_1, a_1, \dots, o_T, a_T)$
- 评分 $f(\hat{y}_i, y_i) \in [0,1]$，split 性能 $\mathcal{R}$ 为平均分
- **系统状态是二元组 $(S_k, W_k)$** —— 技能集 + 持久化 Wiki

目标：从 $(S_0, W_0) = (\emptyset, \emptyset)$ 出发，用训练 rollout 与验证门控，
最大化未见测试集上的表现。

**关键点**：把 $W$（知识）显式提升为与 $S$（技能）并列的一等状态，
这是 WikiSkill 与 EvoSkill / Trace2Skill / SkillOpt 的根本区别。

## 2. 现有方法的共性缺陷

| 方法 | 保存经验的方式 | 缺陷 |
|---|---|---|
| EvoSkill | 累积 prior proposals 与评分结果 | 流水账，非知识结构 |
| Trace2Skill | 从轨迹蒸馏 trajectory-local lessons | 局部教训，跨迭代不复用 |
| SkillOpt | rejected-edit 反馈 + epoch-wise meta guidance | 反馈只服务当轮决策 |

论文原话：这些方法**没有把学到的东西维护成一个独立的、不断演化的知识表示**，
洞察散落在优化历史中，限制了跨迭代的系统性复用。

## 3. 三层的职责与生命周期

| 层 | 职责 | 生命周期策略 | 为什么 |
|---|---|---|---|
| Raw `raw/` | 保存逐步交互全量信息 | 不可变、只追加 | 保留原始事实，供后续重新解读 |
| **Wiki `wiki/`** | 编译后的失败模式、成功策略、提案审计 | **永不回滚** | 失败也是资产；清零即失忆 |
| Skills `skills/` | 可执行程序知识 | 可回滚（快照） | 改动是假设，假设可被证伪 |

### Wiki 的三个文件各解决什么问题

| 文件 | 解决的问题 |
|---|---|
| `patterns/*.md` | 同类失败模式的根因与处置，跨迭代累积证据 |
| `logs.md` | 提供跨迭代的长期历史感知 |
| `skill-impact.md` | **记录被否决提案的 diff**，防止后续迭代重犯 |
| `index.md` | 供 Skill Proposer 检索入口（无需加载全文） |

`skill-impact.md` 是本框架最容易被低估、但论文消融证明价值最大的组件。

## 4. 四组件与公式

| 组件 | 公式 | 关键约束 |
|---|---|---|
| Inference Agent | $\tau_i \sim \pi(x_i; S_{k-1})$ | **训练时禁止访问 Wiki** |
| Wiki Maintainer | $W'_k \leftarrow \mathcal{M}_{WM}(W_{k-1}, \mathcal{T}_{sample,k})$ | 采样轨迹；patch-based 增量编辑 |
| Skill Proposer | $P_k \leftarrow \mathcal{M}_P(W'_k, S_{k-1}, \mathcal{T}_{train,k})$ | ReAct；`read_file` 按需检索；原子提案 |
| Gating | $\mathcal{R}(\mathcal{T}_{val,k}) > \mathcal{R}_{best}$ ? | 拒绝则 $S_k \leftarrow S_{k-1}$，**Wiki 不动** |

门控后由外层 harness 追加审计：
$W_k \leftarrow \text{Update}(W'_k, P_k, \mathcal{R}(\mathcal{T}_{val,k}), a_k)$

## 5. 关键实验数据（5 基准 × 5 模型，3 次独立运行平均）

基准：LiveMath（数学）、SealQA（网页搜索）、SpreadsheetBench（表格）、
OfficeQA（长文档 QA）、ALFWorld（具身任务）
模型：Gemini-3.5-Flash、Qwen-3.5-4B/9B、Qwen-3.6-27B、Gemma-4-31B

| 结论 | 数据 |
|---|---|
| 全面领先 | 5 个模型上平均性能均超所有基线方法，相对最强对手 +3.3 ~ +12.0 |
| 增益随模型规模放大 | Qwen 家族相对无技能：4B +12.3、9B +17.5、27B +23.9 |
| **技能补偿模型规模** | Qwen-3.5-9B + WikiSkill (47.4) > Qwen-3.6-27B 无技能 (39.4) |
| 单任务跃迁 | Gemini-3.5-Flash：LiveMath 33.0 → 72.6；SpreadSheet 50.5 → 76.6 |
| 跨模型迁移可超自进化 | Qwen-3.6-27B 技能使 Gemma-4-31B 的 LiveMath 33.9 → 73.7（自进化仅 56.7） |
| 存在负迁移 | Qwen-3.5-4B 技能使 Gemini 的 SpreadSheet 50.5 → 18.1 |
| **消融：Wiki 的价值** | Proposer 持 Wiki：48.7 → 63.7（**+15.0**） |
| **消融：训练时给 Wiki 反而有害** | 63.7 → 60.9（LiveMath 72.6 → 64.8） |

### 消融的机制解释

**为什么训练时让 Inference Agent 看 Wiki 会降分？**
论文假设：解题知识会直接来自 wiki 而非 skills，使产出的轨迹对技能开发
**信息量更低**——agent 靠"查资料"做对了题，技能本身的缺陷就被掩盖了，
Wiki Maintainer 看到的失败样本随之减少。

**为什么持久化知识值 +15 分？**
没有跨迭代积累时，Skill Proposer 难以解决 intricate failure modes，
且会重复提出已被否决的改动。

## 6. 一个完整案例（Qwen-3.6-27B on ALFWorld）

| 迭代 | Wiki 侧 | Skills 侧 | 结果 |
|---|---|---|---|
| 0 | 识别循环行为 → `take-examine-move-loop.md` | 提出 `goal-directed-action` | 拒绝（diff 与结论留档） |
| 1 | 审计轨迹提示该方向已试过 | 新建 `break-repetition-loop`，含规则 *Never Return an Item to Its Origin Location* | 接受 |
| 4 | 出现新循环变体 → `multi-operation-loop.md` 累积证据 | 细化技能，新增 *Each Operation Type ONCE Per Item* | 接受 |

体现的是：**不是一次想对，而是每轮都在上一轮的知识上叠加。**

## 7. 论文自述的局限

1. 技能**全量注入** prompt，未评估 retrieval / triggering
2. 门控**过严**（必须涨分），排除中性提案
3. **Wiki 无自动剪枝**，长程运行会膨胀
4. 未覆盖**极长周期任务**（数百动作 / 数小时）

> 本 skill 在局限 3 上做了补强：提供 `prune` 命令清理 raw 与快照。
> 局限 1、2、4 仍需使用者自行权衡。
