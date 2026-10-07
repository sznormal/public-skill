# AFP-SPEC 合规证书

- skill：norma-vocational-course-framework v1.0.0
- partner：norma
- skill_type：independent
- 检查日期：2026-10-07（D 轮复核）
- 检查工具：afp-skill-creator P8（对照 AFP-SPEC v0.1）

## 判定结果

- 目标等级：silver
- 判定：**provisional**（条款检查全过；"3 个真实用户案例"属运行期门槛，待 P9 回填）
- 本轮新增达成：命名空间前缀（norma-*）、触发词隔离三段式、薄路由化

## 逐条结果

| 条款 | 结果 | 证据/备注 |
|---|---|---|
| §5 Hard Stops | ✅ | 六阶段 + 每阶段与用户确认；已补 ╭─ 确认单格式（C 主体）+ 显式"不允许自动推进"纪律框 |
| §6 Evidence Chain | ✅ | 政策依据命名引用、不编造、产出落盘为具名文件 |
| §7 Output Structure | ✅ | 三层目录结构 + 写作规范 + 模板 reference + 薄路由表 |
| §8 Multi-Agent Handoff | 不适用 | Independent 单点任务，无下游交接 |

## 反模式自检（D 轮新增）

| 反模式 | 结果 | 备注 |
|---|---|---|
| 命名空间前缀缺失 | ✅ 已修复 | 已由 `vocational-course-framework` 改名 `norma-vocational-course-framework` |
| 触发词未隔离 | ✅ 已修复 | description 升级为【覆盖/隔离/关系】三段式 |
| 主控过厚（违反渐进披露） | ✅ 已修复 | 六阶段内联正文压为路由表，主文件进入薄路由区间；详情延迟 Read 到 `references/` |

## 自评人声明

本证书为合伙人自评，接受 Steering Committee 复核。自评失实将按治理规则处理。

—— norma，2026-10-07
