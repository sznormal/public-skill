# AFP Skill 架构学：从 Bundle 到 Pattern 5

> AFP Skill Creator · Module
> 触发：用户说 "什么是 Bundle vs Primitive" / "架构学" / 读旧文档遇到 Bundle 概念不理解时
> 理论基础：F 文档《AFP Skill 架构学》v2.0

---

## 一、这个模块解决什么

AFP 体系的架构经历了五代演化，v0.3 起定型为 **Pattern 5 · Orchestrated Independent Collection**。但早期文档、模板和一平/学君的存量 skill 里还留着 "Bundle""AFP-shared-primitives 目录" 等旧概念。本模块讲清：

1. 五代架构各是什么、为什么被淘汰（§二）
2. 新旧术语对照——读旧文档时怎么换算（§三）
3. Pattern 5 为什么是终局形态（§四）

---

## 二、五代架构简史

### Pattern 1 · 单体巨石（Monolith）

一个 SKILL.md 塞下全部方法论 + 流程 + 模板。

- **死因**：主控动辄上万 token，每次触发全量加载；改一处怕动全身；违反渐进披露

### Pattern 2 · 主控 + 子文档（Progressive Disclosure）

SKILL.md 变薄，业务下沉到 stages/ 和 modules/，按需 Read。

- **贡献**：确立薄路由 + 按需加载两大铁律（沿用至今）
- **死因**：单个 skill 内部解决了，但 skill 之间各自为政——通用能力（检索、审查、格式化）每家重复造轮子

### Pattern 3 · Federated Bundle（联邦制打包）

按业务域打大包（Bundle）：`phd-master/`、`cn-journal-master/`……跨 Bundle 共享的能力抽到 `AFP-shared-primitives/` 子目录。

- **贡献**：第一次出现"共享 primitive"概念；`templates/bundle-master-template.md` 即此代产物
- **死因**：两个硬伤——
  1. **Claude Code 只扫描 skills 目录顶层一层**，Bundle 内部的子能力无法独立触发，用户必须从 Bundle 大门进
  2. **积分记不清**：合伙人共建一个 Bundle 时，调用记在 Bundle 头上，贡献者的子能力贡献不可见

### Pattern 4 · 中央调度（Central Dispatcher）

一个全局总控 skill 统一接管所有触发，再内部分发。

- **死因**：总控成为单点瓶颈 + 触发词黑洞（什么口令都往它那儿吸）；任何合伙人上新能力都要改总控——治理噩梦

### Pattern 5 · Orchestrated Independent Collection（定型 · 2026-07）

三个角色，全部平铺在 skills 目录顶层，人人 first-class：

| 角色 | 干什么 | 记账 |
|---|---|---|
| **Independent** | 单点任务，可直接触发 | 触发 1 点 |
| **Orchestrator** | 只做引导 + 状态传递，不干业务 | 触发 1 点 |
| **Shared Primitive**（`afp-shared-*`） | 共同体资产，被其他 skill 内嵌 Read | 复用 2 点 / 直触 1 点 |

配套四机制：命名空间前缀（合伙人自治）、触发词精确度分级 + 冲突预检、磁盘状态传递、Committee 治理。

---

## 三、新旧术语对照表（读旧文档必备）

| 旧概念（Pattern 3 语境） | Pattern 5 换算 |
|---|---|
| Bundle | **Orchestrator + 一组 Independent**（拆开平铺，不再打包） |
| Bundle 主控 | Orchestrator 的 SKILL.md |
| Bundle 内子 stage（业务性的） | 各自升格为顶层 Independent skill |
| `AFP-shared-primitives/` 子目录 | `afp-shared-*` 顶层 skill（Committee 审议上架） |
| `../AFP-shared-primitives/xxx.md` 相对路径 Read | Read `~/.claude/skills/afp-shared-xxx/SKILL.md` |
| Federated Bundle（架构学最优形态） | 已被 Pattern 5 取代；"引用 shared primitive"的精神保留 |
| Bundle 命名（`phd-master`） | `<partner>-<domain>-orchestrator`（如 `yiping-phd-orchestrator`） |

**读旧文档的原则**：方法论内容（怎么写综述、怎么做审查）照用；**架构指令（目录结构、路径、命名）一律按 Pattern 5 换算**。

---

## 四、Pattern 5 为什么是终局

四条硬理由：

1. **平台约束对齐**：Claude Code 只扫顶层——平铺是唯一让每个能力都可独立触发的结构，不是品味选择是物理约束
2. **积分可精确记账**：每次调用落到唯一 skill ID，`GROUP BY partner` 即出月度积分——MPC 分配机制的技术地基
3. **合伙人自治**：命名空间前缀让每人在自己地盘自由迭代，Committee 只管边界（shared 层 + 冲突仲裁）——治理成本最低
4. **演化开放**：Independent 可升级 Shared Primitive、成组后可加 Orchestrator（见 stages/02 §六）——架构不锁死成长路径

**存量迁移**：一平博论家族、学君论文实操 V2、青泥家族等 Pattern 2/3 存量 skill，按"先新增后迁移"原则逐步过渡——新 skill 一律 Pattern 5，旧 skill 大版本迭代时顺带迁移，不搞休克式重构。

---

## 五、常见问题

**Q：我就想做个"一条龙"，为什么不让我做 Bundle？**
A：一条龙体验用 Orchestrator 实现——用户感受一样（一个口令走全程），但每个环节仍可被单独触发、单独记账。Bundle 给的它都给，Bundle 的两个硬伤它没有。

**Q：Shared Primitive 和放自己 modules/ 里有什么区别？**
A：modules/ 是私有的、不记复用分；`afp-shared-*` 是共同体的、被 Read 一次记 2 点。判断标准见 stages/04 §4.3——3+ 合伙人可能用才提议 shared。

**Q：旧模板 `bundle-master-template.md` 还能用吗？**
A：已保留为历史参考。新建 skill 请用 `templates/independent-skill-template.md` / `orchestrator-template.md` / `shared-primitive-template.md`。

---

*本模块 v1.0 · 对应 F 文档《AFP Skill 架构学》v2.0 · Pattern 5 定型版*
