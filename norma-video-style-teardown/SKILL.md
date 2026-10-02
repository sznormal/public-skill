---
name: norma-video-style-teardown
description: 拆解一支参考视频的「结构 / 风格 / 渲染 / 动画转场 / 文案」，产出可直接套拍的复刻规格。当用户上传或指向一个视频文件（.mp4/.mov/.mkv 等）并说「分析这个视频的风格」「拆解结构」「我要套用这个风格做视频」「拉片」时使用。不依赖 ffmpeg——用 OpenCV(自带解码)抽帧、PyAV 取音频、faster-whisper 本地转写。
agent_created: true
---

# 视频风格拉片（Video Style Teardown）

把一支参考视频拆成**可复刻的规格**，而不是写观后感。产出物：分镜时间轴、色板 HEX、字号/版式测量、转场清单、文案结构、复刻规格卡。

## 前置：环境（一次性）

本机 **没有 ffmpeg**，且 Git Bash 缺 `head/tail/which/ls` 等命令（不要用管道）。走托管 Python：

```bash
PY=C:/Users/29206/.workbuddy/binaries/python/versions/3.13.12/python.exe
$PY -m venv C:/Users/29206/.workbuddy/binaries/python/envs/video-analysis
VPY=C:/Users/29206/.workbuddy/binaries/python/envs/video-analysis/Scripts/python.exe
$VPY -m pip install opencv-python-headless numpy av faster-whisper
```

> 坑：pip 输出重定向别接 `| tail`，会 `command not found`。直接 `... 2>&1`。

## 步骤

### 1. 元数据 + 运动能量 + 抽帧
`python scripts/teardown.py "<视频路径>" "<输出目录>"`

一次性产出：
- 元数据：fps / 分辨率 / 帧数 / 时长 / 编码 / 码率
- **逐帧差分时间轴**（运动能量）→ 判断有无硬切
- 1fps 抽帧 + `contact_sheet.png`（总览）
- `caption_strip.png`（把每帧底部字幕条裁出纵向拼接 → 一张图读完所有字幕）

### 2. 转场与细节（按需）
用 `scripts/teardown.py` 里的 `grid()` 对**转场窗口**抽密帧（每 0.1s 一帧，4 列拼图），逐个转场看"怎么变的"。窗口由第 1 步的 action_moments 决定。

### 3. 色彩与版式
`scripts/measure.py`：k-means 主色 + 阈值掩膜取纯强调色；行带/包围盒量字号与位置。

### 4. 音频与文案
`python scripts/asr_transcribe.py "<视频路径>" "<模型目录>"`

- 先用 PyAV 解音频，报 RMS/峰值/频谱重心/低频占比/2–8Hz 音节调制比 → **判定是旁白还是纯音乐垫**
- 再跑 faster-whisper 转写

### 5. 读图分析（关键）
脚本只出图，**必须用 Read 工具亲自看图**（多模态）：读 contact_sheet 拿总览，读 caption_strip 拿全部字幕，读 zoom_* 拿字体/插画细节。所有"画面上写了什么字"都以此为准，不要脑补。

### 6. 产出交付物
- Markdown 报告（结构/风格/渲染/动画/文案 + 复刻规格卡 + 分镜模板）
- HTML 活样本：**用被测视频的色板/字体/动效来做报告本身**，用户可直接照抄 CSS
- 内联 SVG 时间轴（结构 + 运动能量）

## 判定规则（重要经验）

| 现象 | 结论 |
|------|------|
| 逐帧平均绝对差最大值 ≪ 10（0–255 标度） | **无硬切**，全靠交叉溶解。硬切会在单帧产生 >10 的尖峰 |
| 逐帧差均值 < 0.5 | 极慢节奏；"动的是光/透明度，不是形" |
| 低频(<300Hz)能量占比 >60% + 2–8Hz 音节调制比 <0.3 + ASR 0 条 | 音频是**音乐垫，无旁白**；文案载体是画面文字 |
| 整体平均亮度 L < 20/255 | 深色电影感基调，亮部仅占小面积 |

## 高频坑

1. **HuggingFace 模型下载失败**（xet 401 / `model.bin is incomplete`）：
   ```python
   os.environ["HF_ENDPOINT"]="https://hf-mirror.com"
   os.environ["HF_HUB_DISABLE_XET"]="1"       # 关键：禁用 xet 传输协议
   os.environ["HF_HUB_ENABLE_HF_TRANSFER"]="0"
   ```
   若 snapshot 里 `model.bin` 是 0 字节（Windows 符号链接失败），**从 `blobs/` 里按文件大小认领**再拷成 `model.bin`/`config.json`/`tokenizer.json`/`vocabulary.txt`，然后 `WhisperModel(本地目录, local_files_only=True)`。
2. **不要用 `import scipy`** 做重采样，环境里可能没有；PyAV/faster-whisper 自带解码与重采样。
3. `cv2.imread` 读中文路径正常；但**构造拼接图时各图高度必须对齐**，`np.hstack` 会因高度不等直接抛错。
4. 字幕带裁剪的 y 区间要先从全帧看清位置；不同片子的字幕基线不同，别照抄数字。
5. 图像读取会占上下文，**优先拼图**（一张 sheet 顶十几张单图）。

## 产物目录约定

```
<输出目录>/
  frames/contact_sheet.png  caption_strip.png  trans_*.png  zoom_*.png
  meta.json  motion.json  colors.json  geometry.json  asr_segments.json
  GPT-6_Astra_风格拆解报告.md          # 报告
  GPT-6_Astra_风格拆解_复刻演示.html    # 活样本
```
