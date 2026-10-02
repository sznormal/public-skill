# 云上仙宫视频生成（xian-gong-video）

> 把任意建筑 / 风景照，转译成「云上仙宫 / 中式天庭」风格的 AI 生图提示词，并延伸出国风视频。

## 一句话简介

内容创作者做国风仙宫视频的提示词规则库：图片是命门、模型比提示词重要、巨物感靠人物占比钉死 1%–2%、并内置**反同质化铁律**避免画面雷同。

## 核心能力

- **万能公式**：主体明确 + 空间关系清楚 + 人物极小（1%–2%）+ 光影明确 + 材质真实 + 镜头质感 + 负面约束
- **五步工作流**：定场景 → 选模型/比例 → 写生图提示词 → 图生视频四段式 → 剪映剪辑交付
- **变量矩阵**：机位 / 场景主体 / 框景 / 时段 / 人物行为 / 情绪 六维度组合，批量产出差异化仙宫图
- **反同质化铁律**：强制轮换机位与人物姿态、风格加成每次最多挑 1–2 项、相邻图至少换 3 个变量、模型混用破同款感
- **多模型适配**：即梦 5 Pro / Image 2.0、豆包 Seedream 5.0 Pro、Midjourney、GPT-image2、Z-Image Turbo（中文长描述式）
- **图生视频四段式**：保留主体 + 动态效果 + 运镜方式 + 风格氛围

## 触发词

仙宫图 / 云上天宫 / 天庭视频 / 中式仙宫 / 国风仙宫视频 / 仙宫提示词 / 一套提示词出多张仙宫 / 仙宫图单一 / 仙宫画面同质化

## 使用步骤

1. 上传一张建筑或风景图（或描述想要的仙宫场景）
2. 按变量矩阵选 6 个维度组合（相邻图至少换 3 个维度）
3. 套用生图提示词模板，比例锁 21:9，接负面约束
4. 把提示词复制到即梦 / 豆包 / MJ 等模型出图
5. 选图后用四段式提示词做图生视频，剪映拼接 + 古风 BGM

## 示例（生图提示词 · 英文）

```
Extremely low-angle shot looking up, a colossal dark bronze celestial bull-horn gate rising from a sea of clouds, two massive curved horns forming the arch of the gate, a long white jade staircase ascending through the gate into mist, a single tiny figure in grey Hanfu climbing the stairs with back to camera, figure only 1%-2% of frame height, sunrise rays breaking through the gate creating strong god rays and rim light, cool blue-gray shadows on the clouds, 21mm ultra-wide angle cinematic low angle, photorealistic bronze jade stone and cloud textures, vast sacred overwhelming atmosphere, UE5 photorealistic rendering. no text, no watermark, no black bars, no neon, no glow effects, no 3D render, no CGI
```

## 适用场景

- 国风仙宫 / 天庭短视频批量生产
- 把现实地标（塔、门、雕塑、山）仙宫化二次创作
- 教师节 / 节日国风视频素材生成
- 四平台（视频号 / 抖音 / 小红书 / B站）差异化分发前的素材生产

## 目录结构

```
xian-gong-video/
├── SKILL.md              # 核心规则 + 工作流 + 反同质化铁律
├── references/
│   └── prompts.md        # 可直抄的提示词范例库
├── manifest.yaml         # 市场发布清单（slug/版本/分类/触发词/标签）
├── README.md             # 本文件
└── icon.png              # 512×512 市场图标
```

## 许可证

MIT © gumiho
