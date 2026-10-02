# AFP-SPEC 合规检查器（v0.1 checklist 版）

> AFP Skill Creator · Module
> 触发：用户说 "AFP-SPEC 是什么" / "怎么合规"；或 P8 合规检查阶段由主控 Read
> 定位：AFP-SPEC v0.1 四大条款的完整 checklist + 逐项检查方法。判级流程与证书模板见 stages/08-conformance-check.md

---

## 一、AFP-SPEC v0.1 是什么

AFP-SPEC 是 AFP 行动派共同体的 **skill 质量协议层**——跨领域通用，不管你做学术、咨询还是法律 skill，都用同一套条款验收。核心四条款：

| 条款 | 一句话 | 防的是什么 |
|---|---|---|
| **§5 Hard Stops** | 关键决策点必须硬停止等用户确认 | agent 越权自主推进 |
| **§6 Evidence Chain** | 事实性主张必须可溯源 | 幻觉与虚构 |
| **§7 Output Structure** | 输出必须有结构 schema | 产出不稳定、不可交接 |
| **§8 Multi-Agent Handoff** | 跨 skill 交接必须走显式协议 | 状态丢失、流程断裂 |

分级：**Bronze**（§5+§6）→ **Silver**（+§7 + 3 用户案例）→ **Gold**（+§8 + peer-review + 6 个月运行）。

---

## 二、§5 Hard Stops · 完整 checklist

- [ ] **H1** 每个 stage 结尾有交付确认单（统一格式框）
- [ ] **H2** 确认单含 `👉 NEXT` 行，明确下一步口令
- [ ] **H3** 存在"即使结果明确也不允许自动推进"纪律条款
- [ ] **H4** 通用指令表含 Next / Back / Edit 三件套（Skip / Export / Status 可选）
- [ ] **H5** 方向性决策点输出多方案（2-3 个，各带优势/代价），不替用户拍板
- [ ] **H6** `Back` 有明确的状态回滚语义（回到哪、哪些字段还原）
- [ ] **H7** 乱序请求有防御（用户越阶要求时引导回当前阶段）

**检查方法**：`grep -l "╭─" stages/*.md` 快扫确认单覆盖率；逐文件核对 H3 条款文字；对照 P3 决策点清单核对 H5。

## 三、§6 Evidence Chain · 完整 checklist

- [ ] **E1** 方法论出处真实（经典移植型：书/论文可查证；原创型：3 个实践案例）
- [ ] **E2** 涉及引用/文献的 stage 写明验证动作（用哪个工具/primitive 验证）
- [ ] **E3** 领域证据链标准落实（对照 `modules/domains/{domain}.md` 的证据类型表）
- [ ] **E4** 无法验证的输出有 `unverified` 标记规则
- [ ] **E5** 话术不承诺 skill 做不到的能力（能力主张也是事实性主张）
- [ ] **E6** 数据类输出要求来源 + 时间（防止过期数据当现状）

**检查方法**：检索 stage 中的"验证 / 校验 / 来源"关键词；抽查 3 条方法论引用的真实性。

## 四、§7 Output Structure · 完整 checklist

- [ ] **O1** 主控有 HUD JSON 骨架，字段覆盖 meta / stages 状态 / history
- [ ] **O2** 每个 stage 有"输出 schema"节（字段 / 章节 / 格式定义）
- [ ] **O3** 最终交付物清单明确（用户走完全流程拿到什么）
- [ ] **O4** 确认单格式全 skill 统一（不同 stage 不漂移）
- [ ] **O5** **每一步实质产物落盘为具名文件**（表 / 稿 / 脚本 / 图 / 数据 / 交接包，路径如 `{project_path}/stage-outputs/` 或等价）——不只是"路径约定"，而是每个产出实质内容的阶段都显式规定落哪个具名文件；对话会压缩、会结束，磁盘不会。**判据一句话：换一个全新对话、只凭磁盘上这些文件，能不能接着往下干？能，才算真落盘。** ⚠️ 落盘是工程化命门（见主控理念 6；与"状态续传"是两回事：状态为断点恢复、产物落盘为成资产）；虽列于 §7，**强烈建议 Bronze 级即纳入必查，不必等 Silver**。

**检查方法**：核对主控 JSON 骨架；逐 stage 找"输出 schema"节；比对任意两个 stage 的确认单格式；**逐 stage 核 O5——每个产出实质内容的阶段是否都写明"落盘为哪个具名文件"，并用"换新对话能否接着干"复核**。

## 五、§8 Multi-Agent Handoff · 完整 checklist

（Orchestrator 必查；Shared Primitive 必查契约部分；Independent 若参与被引导流程也要查）

- [ ] **M1** 分段引导话术明确（"请对我说 XX 触发下一步"，指向真实存在的 skill）
- [ ] **M2** 状态磁盘持久化格式已定义（对照 `modules/continuation-protocol.md`）
- [ ] **M3** 下游 skill 有状态读取说明（触发时先 Read 全局状态文件）
- [ ] **M4** Orchestrator 不含下游业务逻辑（只路由 + 状态 + 话术）
- [ ] **M5** Shared Primitive 有完整调用契约（输入 / 输出 / 状态影响 / 错误处理四节）
- [ ] **M6** 契约有版本号（防 breaking change）

**检查方法**：核对 orchestrator 路由表；打开契约文件核对四节齐全。

---

## 六、快速自检命令

在 skill 目录下跑：

```bash
# 确认单覆盖率（应等于 stage 数）
grep -l "╭─" stages/*.md | wc -l && ls stages/*.md | wc -l

# 子文档是否误加 frontmatter（应为 0）
grep -l "^---$" stages/*.md modules/*.md 2>/dev/null | xargs -I{} head -1 {} | grep -c "^---$"

# frontmatter 五字段齐全（主控）
grep -E "^(name|partner|skill_type|afp_spec_target|agent_created):" SKILL.md

# 路由脚注断链检查（脚注里提到的文件是否都存在）
grep -h "主控加载 stages/" stages/*.md
```

命令只能查形式合规；**语义合规（H5 多方案、M4 不越权等）必须人工逐条核对**。

---

## 七、检查结果输出格式

```
╭─ AFP-SPEC 合规检查报告 ──────────────────────────╮
│ skill：{name} · 目标等级：{target}
│ §5 Hard Stops：       {7/7} [ ✅ | ❌ 未过：H3, H5 ]
│ §6 Evidence Chain：   {6/6} [ ✅ | ❌ 未过：… ]
│ §7 Output Structure： {5/5} [ ✅ | ❌ 未过：… ]
│ §8 Handoff：          {6/6 | 部分适用 | 不适用（理由）}
│ 综合：{可判 certified/provisional | failed → 见 stages/08 §五回退映射}
╰──────────────────────────────────────────────╯
```

---

*本模块对应 AFP-SPEC v0.1。SPEC 版本升级时本 checklist 同步升级，已上架 skill 需按 stages/07 §八运行期义务跟进。*
