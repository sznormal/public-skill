# AFP-SPEC 合规证书

- skill：norma-textbook-deck v1.0.0
- partner：norma
- skill_type：independent
- 检查日期：2026-09-16
- 检查工具：afp-skill-creator P8（对照 AFP-SPEC v0.1）

## 判定结果

- 目标等级：bronze
- 判定：**provisional**（条款检查全过；"3 个真实用户案例"属运行期门槛，待 P9 回填）
- 待达成项：3 个真实用户案例（P9 完成后回填）
- 当前案例数：**1 / 3**（2026-09-16 第10章 25 页端到端验证；案例台账见 `SKILL.md` §十五）

### 案例 1 回填（2026-09-16 · 第10章）

验证方式：以本 skill 前身流程实际制作《第10章 综合项目：虚拟机器人指令解析》25 页课件，跑完 P1→P4。

| 环节 | 结果 |
|---|---|
| P1 抽代码 | 代码块成功外置为 `_实例代码.txt`（4 个代码块），正文零贴码 ✅ |
| P2 建 deck + 大纲 | `slide_plan.json` 25 页，配色/字体/坐标直接复用 design-spec ✅ |
| P3 逐页闭环 | 25 页逐页 lint 提交；实测 3 个坑（见下）✅ |
| P4 三重验收 | 全文 lint 0 error/13 warning；pptx zip testzip=None、25 slide xml + 2 media ✅ |

发现的偏差（已全部回写 `modules/pitfalls.md`）：
1. `<border width="1.5">` 被 SXSD 拒（须整数）→ 写入 pitfalls G2。
2. 含 `<img>` 页面提交后**末尾多出重复页**（图片上传吃 revision）→ 写入 pitfalls G1，修法为 `+xml-get` 核页数后 `+delete-slide`。
3. `+xml-get` 输出为 JSON 包裹，直接 lint 判 not well-formed → 写入 pitfalls G3，修法为抽 `data.xml_presentation.content`。

## 逐条结果

| 条款 | 结果 | 证据/备注 |
|---|---|---|
| §5 Hard Stops | ✅ | 4 个 stage 结尾均有统一格式确认单；主控 §九 + P1–P4 均含"等用户确认才推进/不得自动推进"纪律条款；配色选定、删除/覆盖已提交页面等破坏性操作均设硬停；主控 §七 通用指令表含 `Next / Back / Edit / Skip / Status / Continue` |
| §6 Evidence Chain | ✅ | 主控 §十一 明确：教材内容全部来自用户指定源 md、不编造；配色/坐标为实测值；lint 以 `xml_lint.py` 实际输出为准；配图须为网络搜索的真实素材并记录关键词；"第1章规律"以实际 pptx 解析为证 |
| §7 Output Structure | ✅ | 4 个 stage 均有"输出 schema"节；主控 §二 有完整 HUD JSON 骨架；主控 §十 明确最终三件套交付物（在线链接 + pptx + 代码 txt）；流程型配《用户核查清单》，`templates/用户核查清单.md` 含 4 阶段共 15 行核查项，每行含"应完成动作 / 怎么核查 / 应见落盘文件"，并附 5 条一票否决项 |
| §8 Multi-Agent Handoff | 不适用 | 本 skill 为 Independent 单点任务，内部 4 个 stage 属同一任务的工序，不产生跨 skill 交接；中间产物直接落盘 `chN_ppt/`，无需 `afp-shared-continuation`。理由已记入主控 §五 |

## 反模式自查（对照通用 20 条）

| 反模式 | 自查 | 说明 |
|---|---|---|
| 命名空间前缀缺失 | ✅ 已避免 | `norma-` 前缀 |
| partner 与 name 前缀不匹配 | ✅ 一致 | `name: norma-textbook-deck` / `partner: norma` |
| 主控塞满内容（违反渐进披露） | ✅ 已避免 | SKILL.md 为薄路由，细节在 stages/modules |
| 触发词未隔离 | ✅ 已做 | description 段 3 明确"不触发"商业演示/教学文书/工具选型 |
| 触发词太宽/太窄 | ✅ 已收窄 | 收窄到"教材→课件"单点场景 |
| 关键步骤产物不落盘 | ✅ 已避免 | slide-NN.xml / slide_plan.json / deck-state.json / images/ 全落盘 |
| 决策点未 Hard Stop | ✅ 已设 | 配色、页序、破坏性操作、阶段切换均硬停 |
| 输出无结构 | ✅ 已定义 | §十 三件套 + 各 stage 输出 schema |
| 子文档写 frontmatter | ✅ 已避免 | stages/modules/templates 均为纯 markdown |
| 状态传递不用磁盘持久化 | ✅ 已避免 | `deck-state.json` + `Continue` 断点续传 |

## 自评人声明

本证书为合伙人自评，接受 Steering Committee 复核。自评失实将按治理规则处理。

—— norma，2026-09-16
