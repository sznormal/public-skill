# P7 · 生态集成（Pattern 5 版）

> AFP Skill Creator · Stage 07
> 目的：帮用户走完把 skill 集成到 AFP-ecosystem 官方仓库的完整流程——命名空间审议 + 触发词冲突预检 + Steering Committee 审议 + 上架

---

## 一、生态集成的四步流程

在 P4 结构设计 + P5 Frontmatter 撰写 + P6 内容撰写完成后，进入生态集成阶段：

```
Step 1 · 本地验证
    ↓
Step 2 · 命名空间前缀验证
    ↓
Step 3 · 触发词冲突预检
    ↓
Step 4 · Steering Committee 审议 + 上架 AFP-ecosystem
```

不同 skill_type 走的路径深度不同：

| skill_type | 需要走的 Step |
|---|---|
| **Independent**（合伙人自治命名空间下） | Step 1-3；Step 4 简版（Committee 备案）|
| **Orchestrator**（合伙人自治命名空间下） | Step 1-3；Step 4 简版（Committee 备案）|
| **Shared Primitive**（`afp-shared-*`）| Step 1-4 全套（Committee 强制审议）|
| **AFP 官方**（`afp-*`）| Step 1-4 全套（Committee 强制审议）|

---

## 二、Step 1 · 本地验证

### 2.1 本地部署测试

把 skill 目录复制到 `~/.claude/skills/`：

```bash
cp -r ~/qingni-strategy/{skill-directory} ~/.claude/skills/{skill-name}/
```

**验证清单**：
- [ ] 目录结构符合 P4 设计
- [ ] SKILL.md 位于目录顶层（而非子目录）
- [ ] frontmatter 五段（name / description / partner / skill_type / afp_spec_target）完整
- [ ] `stages/` 和 `modules/` 里的子文档**无 frontmatter**
- [ ] 所有 `Read` 引用路径正确（本地路径或 shared primitive 路径）

### 2.2 触发测试

新开一个 Claude Code 对话，逐一测试：

- [ ] **用主要触发词触发** → skill 是否被加载？
- [ ] **用变体触发词触发**（不完全一致的口令） → 是否仍能触发？
- [ ] **用应触发隔离的口令**（如询问其他阶段） → skill 是否正确地**不触发**？
- [ ] **首次上手引导** → 是否输出预期话术？
- [ ] **Hard Stop 输出** → 格式是否规范？
- [ ] **状态持久化** → 完成一个 Hard Stop 后磁盘文件是否正确写入？
- [ ] **续跑** → 新对话说 `Continue {project_path}` 是否恢复状态？

### 2.3 AFP-SPEC 合规自检

对照 AFP-SPEC v0.1 走一遍合规自检：

- [ ] §5 Hard Stops：所有关键决策点是否都有 Hard Stop？
- [ ] §6 Evidence Chain：事实性主张是否都有来源？
- [ ] §7 Output Structure：输出是否有 schema？
- [ ] §8 Multi-Agent Handoff：如果是 Orchestrator，分段引导话术是否清晰？

**Bronze 门槛**：完成上面所有检查项即可
**Silver 门槛**：Bronze + 通过 3 个真实用户案例测试
**Gold 门槛**：Silver + 通过 3 位合伙人 peer-review + 至少 6 个月运行历史

---

## 三、Step 2 · 命名空间前缀验证

### 3.1 前缀合规检查

对照 P5 里定义的命名空间规则：

| 前缀 | 你的授权 |
|---|---|
| `yiping-*` | 只有一平可用 |
| `xuejun-*` | 只有学君可用 |
| `qingni-*` | 只有学术志研发团队可用 |
| `afp-shared-*` | 需 Steering Committee 授权 |
| `afp-*` | 需 Steering Committee 授权 |
| `<partner_slug>-*` | 合伙人加入时 Committee 授予 |

**验证**：
- 你的 skill 的 `name` 是否以你被授权的前缀开头？
- 你的 `partner` 字段是否与前缀一致？

### 3.2 未授权情形的处理

如果你尚未获得任何合伙人 slug：

**Option A**：加入 AFP 合伙人计划
- 走 A 文档的合伙人申请流程
- 获得 Committee 授予的 `<slug>-*` 命名空间
- 回到本 skill 的 P5 更新 frontmatter

**Option B**：Bronze 独立开发（不进入 AFP-ecosystem）
- 保持 skill 在本地使用
- 不进入 AFP-ecosystem 官方仓库
- 不享受合伙人积分分成
- 未来加入合伙人计划时再迁移

---

## 四、Step 3 · 触发词冲突预检

**这是 Pattern 5 生态集成的最关键一步**——触发词冲突会破坏整个 ecosystem 的用户体验。

### 4.1 使用触发词冲突预检工具

**在线预检工具**（由 `afp-shared-trigger-conflict-checker` 提供）：

```
输入：你的 skill 的 description 全文
输出：与 AFP-ecosystem 现有 skill 的触发词交集分析
```

### 4.2 冲突识别的三种情形

**Case 1 · 严重冲突：完全相同触发词**

```
你的触发词："帮我写文献综述"
冲突的 skill：xuejun-literature-review-journal（触发词包含"帮我写文献综述"）

处理方案：
- 你收窄触发词到细分场景（如"帮我写博士论文文献综述"）
- 或者与该合伙人协商（找 Committee 仲裁）
- 或者判断这两个 skill 是否可以合并到 Shared Primitive
```

**Case 2 · 中度冲突：语义近似**

```
你的触发词："文献综述"
冲突的 skill：qingni-framework-cn-navigator（触发词包含"研究现状梳理"）

处理方案：
- 通常不冲突（因为 navigator 是 orchestrator 层，你是 independent 层）
- 但需要在触发隔离说明里明确
```

**Case 3 · 无冲突**

```
预检通过 → 进入 Step 4
```

### 4.3 冲突调解流程

如果你和其他合伙人的触发词无法调和：

1. **发起 Committee 仲裁请求**
2. Committee 根据以下原则仲裁：
   - **精确度优先**：更精确的触发词优先获得触发权
   - **先到先得**：同精确度下，先上架的 skill 优先
   - **合伙人协商**：Committee 鼓励双方直接协商，Committee 仅在协商失败时介入
3. **仲裁结果**：败方需要调整触发词或收窄 description

### 4.4 命名规范化

Committee 通过后，若你的 skill 未来会与很多合伙人的 skill 产生潜在冲突，Committee 可能建议命名规范化：

- 加更精确的领域限定：`yiping-phd-literature-review`（明确针对博士论文）
- 加学科限定：`yiping-social-lit-review`（明确针对社会学）
- 加方法限定：`yiping-systematic-review`（明确系统综述）

---

## 五、Step 4 · Steering Committee 审议 + 上架

### 5.1 提交材料

打包提交至 AFP-ecosystem 官方仓库：

```
submission-package/
├── SKILL.md                       主入口
├── stages/                         所有 stages
├── modules/                        所有 modules
├── templates/                      所有 templates
├── README.md                       使用说明
├── AFP-SPEC-CONFORMANCE.md         合规证书自评
├── INTEGRATION-GUIDE.md            集成建议（放到 ecosystem 哪里）
├── TRIGGER-CONFLICT-REPORT.md      触发词冲突预检报告
└── PARTNER-DECLARATION.md          合伙人声明（partner slug / 授权来源 / 归属）
```

### 5.2 Committee 审议要点

**通用审议**（所有 skill 类型）：
- 命名空间前缀合规
- Frontmatter 五段完整
- 触发词冲突预检通过
- AFP-SPEC 合规目标达成
- 文档质量（README / stages 说明清晰）

**Shared Primitive 额外审议**：
- 通用性：是否真的能被跨合伙人反复复用？
- 独特性：是否与已有 primitive 重复？
- 契约清晰性：调用契约是否明确？
- Gold 级质量：是否达到 Shared Primitive 层的最低门槛？

**AFP 官方 skill 额外审议**：
- 战略意义：是否服务 AFP 生态的核心战略？
- 治理归属：是否明确归属共同体池？
- 未来演化：是否与 AFP 演进路线图一致？

### 5.3 审议结果

- **通过**：授予 AFP-ecosystem 官方前缀，上架官方仓库，开始积分记账
- **需修改**：Committee 反馈具体修改点，回到对应 stage 修正
- **拒绝**：明确拒绝理由（如通用性不足、与已有 primitive 重复等）

### 5.4 上架后事项

- **积分记账开始**：从上架次日起，你的 skill 每次触发都记入你的积分账户
- **月度结算**：每月 1 日结算上月积分，按 F 文档 §8.1 分成规则打款
- **版本演进**：你可以随时更新自己命名空间下的 skill（重大版本变更需 Committee 备案）
- **贡献者署名**：终身署名在 skill 的 README + AFP-ecosystem 贡献者名录

---

## 六、Hard Stop · 交付确认单

```
╭─ P7 生态集成 完成 ────────────────────────────────╮
│ 
│ Step 1 · 本地验证：
│   [ ✅ | ⚠️ | ❌ ] 目录结构合规
│   [ ✅ | ⚠️ | ❌ ] 触发测试通过
│   [ ✅ | ⚠️ | ❌ ] AFP-SPEC 合规自检通过（等级：{bronze/silver/gold}）
│ 
│ Step 2 · 命名空间前缀验证：
│   命名空间：{yiping-* / xuejun-* / qingni-* / afp-shared-* / afp-*}
│   [ ✅ | ❌ ] 前缀授权合规
│ 
│ Step 3 · 触发词冲突预检：
│   [ ✅ 无冲突 | ⚠️ N 项待调整 | ❌ 需 Committee 仲裁 ]
│   预检报告：TRIGGER-CONFLICT-REPORT.md
│ 
│ Step 4 · Steering Committee 审议：
│   [ ✅ 已通过 | ⏳ 待审议 | ❌ 需修改 ]
│   审议结果：{详细说明}
│ 
│ 📦 提交包路径：{submission-package-path}
│ 🎯 上架状态：{已上架 AFP-ecosystem / 待上架 / 需修改 / 拒绝}
│ 💰 积分记账：{已启用 · 从 YYYY-MM-DD 开始 | 待启用}
│ 
│ 👉 NEXT：输入 "Next" 进入 P8 AFP-SPEC 合规最终检查
╰────────────────────────────────────────────────╯
```

---

## 七、反模式警告

生态集成阶段常见错误：

- ❌ **跳过触发词冲突预检**：直接上架 → 被 Committee 打回，破坏其他合伙人体验
- ❌ **私自用受限前缀**：`afp-shared-*` / `afp-*` 未经审议就用 → 上架会被拒
- ❌ **命名空间前缀与 partner 不一致**：`name: yiping-*` 但 `partner: xuejun` → 记账混乱
- ❌ **Committee 审议前发布**：非官方渠道分发未审议的 skill → 违反 Steering Committee 治理规则
- ❌ **合伙人授权模糊**：Bronze 独立开发的 skill 突然主张进入 ecosystem → 需先走合伙人加入流程
- ❌ **Shared Primitive 提议随便**：把只有自己用的能力提交为 `afp-shared-*` → Committee 会拒
- ❌ **忽略 AFP-SPEC 合规自检**：直接提交 Committee → 会被打回补齐合规
- ❌ **冲突调解绕过 Committee**：私下与其他合伙人协商但未通报 Committee → 记账、上架状态不清

---

## 八、上架后持续义务

上架不是终点，是开始。作为 AFP-ecosystem 官方合伙人 skill，你有持续义务：

- **保持文档更新**：SKILL.md / README 与实际行为同步
- **响应用户反馈**：合理时间内回应用户 issue
- **合规性维护**：AFP-SPEC 版本升级时同步升级
- **与其他合伙人协作**：如果你的 skill 与其他 skill 有内嵌调用关系，保持契约稳定
- **贡献 Shared Primitive**：发现通用能力时主动提议共同体资产化
- **月度贡献报告**：Committee 每月发月度贡献报告，可选择性回应

**违规处理**：
- 严重违反合规 → 暂停积分记账 3 个月
- 抢占触发词恶意行为 → 撤销命名空间授权
- 私自分发未审议 skill → 通报 + 记违规

---

*P7 完成后，主控加载 stages/08-conformance-check.md*
