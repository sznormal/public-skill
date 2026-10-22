# public-skill

Norma 公开的 6 个科研类 WorkBuddy Skill 集合。

每个 skill 独立目录，MIT License 授权允许商业使用。

---

## Skill 清单

| Skill | 版本 | 说明 |
|---|---|---|
| `norma-lit-review` | 0.27.0 | 理工科文献综述全流程：检索策略 → 多库检索 → 筛选分类 → 研究缺口 → 结构化综述 |
| `norma-topic-selection` | 1.1.0 | 理工科选题助手：证据矩阵 → 六重门验伪 → Gap Statement → 8 维评分卡 → MVP 止损 |
| `norma-sci-journal-selection` | 1.6.0 | SCI 选刊七阶段：论文画像 → 候选池 → 硬排雷 → 匹配打分 → 冲/稳/保 |
| `norma-ssci-journal-selector` | 1.5.0 | SSCI 选刊 6 步证据流：论文指纹 → 3D 匹配打分 → 投稿序列 |
| `norma-cn-core-journal-selection` | 1.1.0 | 中文核心期刊选刊七阶段：四大目录体系 + 假刊/套刊/代发识别 + 时效 20% 权重 |
| `norma-paper-format-check` | 1.3.0 | 论文排版与投稿前检查：参考文献格式校验 + 著者-年份制四式引用修正 + 编号制零孤儿脚本门禁 |

## 快速安装

```bash
dsh plugin add github:sznormal/public-skill
```

或手动 clone 到 `~/.workbuddy/skills/`：

```bash
git clone https://github.com/sznormal/public-skill.git ~/.workbuddy/skills/public-skill-temp
# 将各 skill 子目录移入 ~/.workbuddy/skills/
```

## 目录结构

```
public-skill/
├── norma-lit-review/
│   ├── SKILL.md
│   ├── modules/
│   ├── scripts/
│   └── stages/
├── norma-topic-selection/
│   ├── SKILL.md
│   ├── modules/
│   ├── stages/
│   └── templates/
├── norma-sci-journal-selection/
│   ├── SKILL.md
│   └── references/
├── norma-ssci-journal-selector/
│   ├── SKILL.md
│   ├── references/
│   └── scripts/
├── norma-cn-core-journal-selection/
│   ├── SKILL.md
│   └── references/
├── norma-paper-format-check/
│   ├── SKILL.md
│   ├── modules/
│   ├── scripts/
│   └── templates/
├── LICENSE
└── README.md
```

## 版权与许可

全部 skill 统一适用 **MIT License**（允许商业使用）。

> © 2026 Norma
