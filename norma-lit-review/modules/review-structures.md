# 理工科综述结构设计指南

> Norma理工科文献综述 · Module
> 加载条件：P5 阶段用户需要选择综述结构，或主动问"综述怎么组织"

---

## 一、五种综述类型结构对比

| 维度 | T1 叙述/SoTA | T2 系统综述 | T3 范围综述 | T4 文献计量 | T5 批判/观点 |
|------|-------------|-----------|-----------|-----------|------------|
| 核心目标 | 讲清现状与趋势 | 严谨回答证据问题 | 摸清全貌与空白 | 量化演进 | 提出立场 |
| 是否 PRISMA | 否 | 是(2020) | 是(ScR) | 否 | 否 |
| 章节骨架 | 引言+主题章+范式+缺口 | 方法+PRISMA+结果+讨论 | 方法+证据地图+空白 | 数据方法+图+演进 | 立场+批判+主张 |
| 篇幅 | 2-6 页 | 长（最严谨） | 中 | 中（图表多） | 短（洞察） |
| 引用数 | 15-40 篇 | 30-100+ | 30-80 | 不限（计量） | 10-30 篇 |
| 适用 | 相关工作/开题 | 方法对比/学位论文 | 新兴交叉/基金 | 趋势报告 | 顶刊邀稿 |

> 类型由 P0 锁定；各类型写作要素细节见 `modules/review-types.md`。

---

## 二、常见理工科综述组织逻辑

### 逻辑一：按技术路线（最适合 CS/EE）

```
Introduction
├── Traditional Methods（传统方法）
├── Deep Learning-based Methods（深度学习方法）
│   ├── CNN-based approaches
│   ├── Transformer-based approaches
│   └── Lightweight models
├── Hybrid Approaches（混合方法）
└── Summary & Gaps
```

### 逻辑二：按应用场景（最适合交叉学科）

```
Introduction
├── Application Scenario A
│   ├── Method X in scenario A
│   └── Method Y in scenario A
├── Application Scenario B
│   └── ...
└── Cross-scenario comparison
```

### 逻辑三：按问题维度（最适合信号处理/控制）

```
Introduction
├── Problem Formulation（问题定义）
├── Solution Approaches（解决思路）
│   ├── Approach 1: ...
│   └── Approach 2: ...
├── Evaluation Metrics（评价方法）
└── Open Challenges（待解决问题）
```

### 逻辑四：时间线演进（适合有明确技术代际的领域）

```
2015-2018: Era of Traditional Methods
2018-2021: CNN Revolution
2021-2023: Transformer Dominance
2024-present: Lightweight + Edge Deployment
```

---

## 三、理工科综述的黄金比例

```
引言/背景：   15%
方法综述：   50%（主体）
对比分析：   15%
缺口/展望：   20%
```

**关键是方法综述占一半篇幅**——这是理工科综述与文科综述最大的不同。文科综述重在理论流派梳理，理工科综述重在技术路线的对比分析。

---

## 四、好综述 vs 烂综述

| 烂综述 | 好综述 |
|--------|--------|
| "A 提出了 X，B 提出了 Y，C 提出了 Z..." | "为解决 Q 问题，已有三种技术路线：A 的 X 从硬件层面...，B 的 Y 从算法层面...，C 的 Z 则另辟蹊径..." |
| 罗列文献，没有对比 | 横向对比 + 纵向演进 |
| 每篇文献一句带过 | 核心文献展开讨论，次要文献列表汇总 |
| 结论是"还需要进一步研究" | 结论明确指出"现有方法在 XX 场景下的 YY 指标仍有 ZZ 的改进空间" |
