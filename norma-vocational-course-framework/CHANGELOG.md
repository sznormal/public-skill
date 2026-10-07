# CHANGELOG · 职教课程框架生成（norma-vocational-course-framework）

> 本文件记录本 skill 在 AFP-SPEC 优化过程中的每一次修改留痕（机制建立于 2026-10-07）。
> 总台账与逐批次详情见 `afp-selfbuilt-skills-audit.md`。

## 2026-10-07 · D 轮（命名空间前缀 + AFP 薄路由/触发词隔离改造）
- 类型：命名空间前缀补齐 + 触发词隔离标准化 + 薄路由化（AFP-SPEC 实质性改造）
- 改动 1（改名）：目录由 `vocational-course-framework` 重命名为 `norma-vocational-course-framework`（AFP 反模式"命名空间前缀缺失"的核心修复）。`git mv` 保留历史。
- 改动 2（frontmatter）：`name` 字段同步改为 `norma-vocational-course-framework`；`description` 升级为 AFP 标准三段式——【触发词覆盖】/【触发词隔离】/【与其他 skill 的关系】，显式声明不触发场景（教学文件专家团 / 单知识点 / 纯 PPT 排版）与下游 skill 关系。
- 改动 3（薄路由化）：删除原 107 行"六阶段建设流程"内联正文与三层目录代码块，压缩为一张「六阶段路由表」（阶段/目标/关键动作/详情 Read），详情延迟加载到 `references/`。主文件由 4224 字符压至薄路由区间（约 2400 字符）。
- 改动 4（保留）：C 主体已加的两处 ╭─ 框（分阶段确认纪律 + 阶段确认点）原样保留，未改动语义。
- 未改动：`references/` 7 个明细文档、`partner/skill_type/afp_spec_target/agent_created/version` 字段值、版权与许可声明。
- 校验：改名后目录内无残留旧名字符串；SKILL.md 字符数进入薄路由区间；触发词三段式齐备。

## 2026-10-07 · C 主体（AFP-SPEC 语义强化）
- 类型：确认纪律显式化 + 确认点 ╭─ 化
- 改动 1：在交互/工作流开头插入统一「分阶段确认纪律（硬停总纲 · 不允许自动推进）」╭─ 框，显式声明凡正文标注「确认点 / Gate / Hard Stop / 必须等用户确认」的节点，AI 一律不允许自动推进，须用户明确确认后方可进入后续阶段。
- 改动 2：将「六阶段每阶段完成后与用户确认」升级为显式阶段确认点 ╭─ 框 就地升级为 ╭─ 代码块框，便于 Committee 用 `grep ╭─` 复核全部确认点。
- 未改动：各确认点的语义与原有叙述内容保持不变（仅增 ╭─ 视觉框）。
- 校验：本文件所属 SKILL.md 的 ╭─ 计数与代码块围栏均通过平衡校验。

## 历史批次（汇总，详情见审计报告第 VI 节）
- A 批：补 partner / skill_type / afp_spec_target / agent_created 四字段 + 落盘 AFP-SPEC-CONFORMANCE.md（provisional）。
- B 批：修硬编码个人路径（本机可用性修复，本 skill 无残留路径 bug）。
- C 安全子集：补【触发隔离】段（norma-video-style-teardown / school-news-oa-writer）。
