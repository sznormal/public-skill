# legacy — suit-sz-teaching-suite-norma 历史版本归档

本目录保存 `suit-sz-teaching-suite-norma` 的历史包与相关文档。**当前主版本为 1.2.0（即上级目录内容）。**

## 版本包

| 文件 | 版本 | 归档日期 | 原始位置 | 大小 |
|---|---|---|---|---|
| `suit-sz-teaching-suite-norma-v1.0.0.zip` | 1.0.0 | 2026-09-03 | `workspace/2026-09-03-22-39-47/` | 78.6 KB |
| `suit-sz-teaching-suite-norma-v1.1.0.zip` | 1.1.0 | 2026-09-03 | `workspace/2026-09-03-22-39-47/` | 89.1 KB |
| `suit-sz-teaching-team.zip` | 团队 1.1.2 | 2026-09-16 | `workspace/2026-09-16-18-52-31/` | 2,533.3 KB |

## docs/

| 文件 | 说明 |
|---|---|
| `技能整改报告-suit-sz-teaching-suite-norma.md` | 2026-09-16 的技能整改记录 |

## 说明

### 与 teaching-docs-writer 的关系

`suit-sz-teaching-suite-norma` 是教学文件写作技能（课程标准 / 教案 / 学期授课计划）的**打包分发形态**，其源技能为 `teaching-docs-writer`（位于 `teachrwork/职教文件/.trae/skills/`）。两者 `name` 字段不同，但触发词（课程标准、教案、授课计划）高度重叠。

### 关于 suit-sz-teaching-team.zip

这不是普通 skill 包，而是**专家团（expert team）形态**的插件包，含：

- `.codebuddy-plugin/plugin.json`（name=`suit-sz-teaching-team`，version=`1.1.2`）
- `agents/`：5 个角色（team-lead、course-standard-writer、lesson-plan-writer、doc-supervisor、template-extractor）
- `avatars/`：6 个 PNG 头像，合计约 2.4 MB（**占了整个包的 95%**）
- `skills/suit-teaching-suite/`：内嵌的共享工具箱

该版本与 `~/.workbuddy/plugins/marketplaces/my-experts/` 下已安装的插件同为 1.1.2。若日后觉得仓库体积吃紧，此包是首个可考虑移出的对象。

### 版本脉络

| 阶段 | 版本 | 形态 |
|---|---|---|
| 初始 | 1.0.0 | skill（modules/ + stages/ 结构） |
| 迭代 | 1.1.0 | skill（references/ + scripts/ 结构，引入 docx 模板） |
| 当前 | 1.2.0 | skill（references/ + scripts/ + templates/，含督导校验脚本） |
| 专家团 | 1.1.2 | plugin（agents/ + avatars/ + 内嵌 skill） |
