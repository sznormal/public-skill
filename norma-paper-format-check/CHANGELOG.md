# CHANGELOG · 论文排版与投稿前检查（norma-paper-format-check）

> 本文件记录本 skill 在 AFP-SPEC 优化过程中的每一次修改留痕（机制建立于 2026-10-07）。
> 总台账与逐批次详情见 `afp-selfbuilt-skills-audit.md`。

## 2026-10-07 · C 主体（AFP-SPEC 语义强化）
- 类型：确认纪律显式化 + 确认点 ╭─ 化
- 改动 1：在交互/工作流开头插入统一「分阶段确认纪律（硬停总纲 · 不允许自动推进）」╭─ 框，显式声明凡正文标注「确认点 / Gate / Hard Stop / 必须等用户确认」的节点，AI 一律不允许自动推进，须用户明确确认后方可进入后续阶段。
- 改动 2：将 3 处硬停（S1 目标刊与交付格式 / S2 约束清单 / S3 检查交付） 就地升级为 ╭─ 代码块框，便于 Committee 用 `grep ╭─` 复核全部确认点。
- 未改动：各确认点的语义与原有叙述内容保持不变（仅增 ╭─ 视觉框）。
- 校验：本文件所属 SKILL.md 的 ╭─ 计数与代码块围栏均通过平衡校验。

## 历史批次（汇总，详情见审计报告第 VI 节）
- A 批：补 partner / skill_type / afp_spec_target / agent_created 四字段 + 落盘 AFP-SPEC-CONFORMANCE.md（provisional）。
- B 批：修硬编码个人路径（本机可用性修复）。
- C 安全子集：补【触发隔离】段（norma-video-style-teardown / school-news-oa-writer）。
