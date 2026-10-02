# P8 · AFP-SPEC 合规检查（Pattern 5 版）

> AFP Skill Creator · Stage 08
> 目的：对照 AFP-SPEC v0.1 做最终逐条验收，判定 Bronze / Silver / Gold 等级，生成合规证书 AFP-SPEC-CONFORMANCE.md

---

## 一、本阶段与 P7 的关系

P7 生态集成里做过一次 AFP-SPEC **合规自检**（Step 1.3）——那是快速过筛。本阶段是**正式验收**：逐条检查、留下证据、生成证书。证书是 Committee 审议材料包的必备文件（见 P7 §5.1）。

检查执行时 Read `modules/afp-spec-checker.md` 获取完整 checklist 与检查方法。本文档只定义验收流程与判级规则。

---

## 二、四大条款逐条验收

### §5 Hard Stops（硬停止协议）

| 检查项 | 方法 |
|---|---|
| 每个 stage 结尾有统一格式确认单 | 逐个打开 stages/*.md 核对结尾确认框 |
| 有"不允许自动推进"纪律条款 | 主控或 stage 中检索该条款 |
| 方向性决策点给多方案而非单方案 | 对照 P3 确认的方案型决策点清单 |
| 通用指令表含 Next / Back / Edit | 核对主控指令表 |

### §6 Evidence Chain（证据链）

| 检查项 | 方法 |
|---|---|
| 事实性输出有来源要求 | 核对涉及引用/数据的 stage 是否写明验证动作 |
| 方法论出处真实 | 核对 P3 确认单里的出处（经典移植型必查） |
| 领域证据链标准落实 | 对照 `modules/domains/{domain}.md` 的证据类型表 |
| 无法验证的内容标 `unverified` | 检索输出 schema 中的标记规则 |

### §7 Output Structure（输出结构）

| 检查项 | 方法 |
|---|---|
| 每个 stage 有输出 schema | 逐个核对 stage 的"输出 schema"节 |
| HUD 状态骨架完整 | 主控 JSON 骨架字段核对 |
| 最终交付物结构明确 | 主控"最终交付物"清单核对 |

### §8 Multi-Agent Handoff（多 agent 交接 · Orchestrator / Gold 必查）

| 检查项 | 方法 |
|---|---|
| 分段引导话术明确指向下游 skill | 核对 orchestrator 路由表的引导话术列 |
| 状态磁盘持久化格式已定义 | 对照 `modules/continuation-protocol.md` 格式 |
| 下游 skill 触发后能读到上游状态 | 核对下游 skill 的状态读取说明 |
| Shared Primitive 有调用契约 | 核对 contract（输入/输出/状态影响/错误处理） |

---

## 三、分级判定规则

| 等级 | 门槛 | 本阶段可判定性 |
|---|---|---|
| **Bronze** | §5 + §6 全过 | ✅ 本阶段可当场判定 |
| **Silver** | Bronze + §7 全过 + 3 个真实用户案例 | 条款部分当场判定；**用户案例在 P9 完成后回填** |
| **Gold** | Silver + §8 全过 + 3 位合伙人 peer-review + 6 个月运行历史 | 条款部分当场判定；peer-review 与运行历史属**运行期义务**，证书标"目标待达成" |

**判定输出三种结果**：
- `certified`：该等级全部门槛已达成
- `provisional`：条款检查全过，但案例/历史类门槛未到期——证书标注"暂定 + 待达成项"
- `failed`：条款检查有未过项 → 按 §五回退修正

---

## 四、生成合规证书

检查全部完成后，在 skill 目录生成 `AFP-SPEC-CONFORMANCE.md`：

```markdown
# AFP-SPEC 合规证书

- skill：{name} v{version}
- partner：{partner}
- skill_type：{type}
- 检查日期：{date}
- 检查工具：afp-skill-creator P8（对照 AFP-SPEC v0.1）

## 判定结果

- 目标等级：{bronze | silver | gold}
- 判定：{certified | provisional | failed}
- 待达成项：{无 | 3 个真实用户案例（P9） | peer-review ×3 | 运行历史 6 个月}

## 逐条结果

| 条款 | 结果 | 证据/备注 |
|---|---|---|
| §5 Hard Stops | ✅/❌ | {备注} |
| §6 Evidence Chain | ✅/❌ | {备注} |
| §7 Output Structure | ✅/❌ | {备注} |
| §8 Multi-Agent Handoff | ✅/❌/不适用 | {备注} |

## 自评人声明

本证书为合伙人自评，接受 Steering Committee 复核。自评失实将按治理规则处理。

—— {partner}，{date}
```

---

## 五、不通过的回退映射

哪条不过，回哪个 stage 修：

| 未过项 | 回退到 |
|---|---|
| Hard Stop 缺失 / 格式漂移 | P6 内容撰写（补确认单） |
| 方案型决策变单方案 | P3 决策点清单 + P6 改写 |
| 方法论出处存疑 | P3 方法论来源 |
| 输出无 schema | P6（补输出 schema 节） |
| HUD 骨架缺字段 | P4 结构设计 |
| 断点续传缺失 | P6 + `modules/continuation-protocol.md` |
| 交接话术不清（orchestrator） | P4 §五 + P6 |
| frontmatter 字段问题 | P5 |

修正后**重跑本阶段**，直到 `certified` 或 `provisional`。

---

## 六、Hard Stop · 交付确认单

```
╭─ P8 AFP-SPEC 合规检查 完成 ───────────────────────╮
│ 🏅 目标等级：{bronze | silver | gold}
│ 📋 逐条结果：
│   §5 Hard Stops        [ ✅ | ❌ ]
│   §6 Evidence Chain    [ ✅ | ❌ ]
│   §7 Output Structure  [ ✅ | ❌ ]
│   §8 Multi-Agent Handoff [ ✅ | ❌ | 不适用 ]
│ ⚖️  判定：{certified | provisional | failed}
│ 📄 证书：AFP-SPEC-CONFORMANCE.md {已生成 | 未生成}
│ ⏳ 待达成项：{清单 | 无}
│ 👉 NEXT：输入 "Next" 进入 P9 测试与迭代
│         （failed → 按回退映射修正后重跑 P8）
╰──────────────────────────────────────────────╯
```

**P8 完成后必须等待用户 `Next` 确认才推进 P9。**

---

## 七、反模式警告

合规检查阶段常见错误：

- ❌ **自检当验收**：只跑 P7 的快速过筛就出证书——逐条证据缺失，Committee 复核会打回
- ❌ **证书注水**：案例没跑够就标 `certified`——自评失实是治理违规
- ❌ **为过检而补形式**：往 stage 里粘贴确认框但没有真实停顿逻辑——形合神不合，P9 走查测试会现形
- ❌ **§8 全跳过**：Independent 也可能有跨 skill 状态传递（被 orchestrator 引导时）——"不适用"要给理由
- ❌ **failed 后硬闯 P9**：条款未过就去测试——测试只会把结构性问题放大
- ❌ **证书生成后不再维护**：skill 大版本更新后旧证书失效——重大变更需重跑 P8

---

*P8 完成后，主控加载 stages/09-testing-guidance.md*
