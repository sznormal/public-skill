---
name: bibagent
version: 1.0.0
agent_created: true
description: |
  BibAgent是一个用于检测科学文献中错误引用(miscitation)的智能体框架。
  使用场景包括：(1) 检查论文引用是否正确 (2) 识别五类引用错误 (3) 验证付费墙后的文献引用 (4) 
  生成可追踪的引用完整性报告。核心技术包括：五类错误分类法、Evidence Committee机制、
  文档解析与引用映射、Accessible和Paywalled双分支验证。
---

# BibAgent: 错误引用检测框架

## 概述

BibAgent是一个端到端的科学文献错误引用(miscitation)检测智能体，能够：
- 同时处理可访问(full-text accessible)和付费墙后的(paywalled)文献来源
- 发出带可追踪证据的明确错误代码
- 支持论文级引用完整性摘要生成

## 五类错误分类法

### 1. Citation Validity Errors (引用有效性错误)
- 引用指向不存在的文献、无效DOI或无法解析的参考
- 示例：幽灵引用、无法解析的参考文献

### 2. Content Misrepresentation Errors (内容误传错误)
- 错误地描述被引文献的实际内容或结论
- 示例：将被引文献未声明的观点归因于它

### 3. Scope Extrapolation Errors (范围外推错误)
- 将正确理解的结论应用到其确立的人群、设置、任务或方法论范围之外
- 示例：将特定实验条件的结论推广到不适用场景

### 4. Evidence Characterization Errors (证据特征错误)
- 对证据的逻辑类型或强度进行错误陈述
- 示例：将相关性发现提升为"因果关系"、将边缘效应定义为确定性效应

### 5. Attribution & Traceability Errors (归属与可追踪性错误)
- 破坏性元数据链接：幽灵引用、无法解析的参考或错误归属 authorship
- 阻止读者可靠地定位和归因原始来源

## 依赖优先级规则

实际验证工作流应遵循：
1. 首先检查引用是否可以追踪
2. 然后检查来源是否有效
3. 然后检查内容是否被忠实呈现
4. 最后检查范围和证据强度声明

每个错误引用实例应接收一个主要类别，对应于实际引用检查工作流中的第一个失败点。

## 核心工作流

### 1. 文档解析与引用映射
- 解析输入文档，提取所有in-text citations
- 映射每个引用到其 bibliography entry

### 2. 来源分类
- 区分可访问来源和付费墙来源
- 可访问来源：直接获取并分析全文
- 付费墙来源：使用Evidence Committee机制

### 3. 双分支验证

**Accessible分支(可访问来源)**:
- 使用NLI(自然语言推理)模型验证引用的内容与声称是否一致
- 在长文本中定位决定性证据

**Paywalled分支(付费墙来源)**:
- 使用Evidence Committee机制
- 通过下游引用重建社区共识
- 应用field-normalized影响力分数
- 支持可靠性感知的弃权(abstention)

### 4. 错误代码输出
- 返回 taxonomy-aligned 错误代码
- 附带 traceable evidence bundles

## 使用示例

### 基本引用检查
当用户请求检查论文中的引用是否正确时，使用此skill：
1. 解析用户提供的论文文档
2. 提取所有引用
3. 对每个引用应用五类错误分类验证
4. 报告检测到的错误及证据

### 付费墙文献验证
当需要验证无法直接访问的文献引用时：
1. 识别付费墙来源
2. 使用Evidence Committee通过下游引用重建共识
3. 应用field-normalized影响力评分
4. 决定是否需要abstain(放弃判断)

### 引用完整性报告
生成论文级引用完整性摘要：
1. 聚合所有检测到的错误
2. 按错误类别分类
3. 提供每个错误的详细证据
4. 指出最需要人工干预的位置

## 实施考虑

### 跨学科适用性
- taxonomy在证据关系层面定义，不依赖特定学科术语
- 可扩展到多语言语料库

### 非文本证据扩展
- 可附加结构化证据对象到引用(如链接到 figure 中的特定面板)
- 可扩展到reason over figures、tables和code

### 局限性
- 继承backbone和引用图中的系统性偏见
- 长文档解析在格式极端情况下可能失败
- 存在被游戏(gaming)的风险
