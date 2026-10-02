# 一句话定位卡片规范

## 句式（一字不能改）

> 我凭借______，服务______，在______情境下解决______问题，通过______交付。

五槽映射：
- 凭借 = 第四问优势证据
- 服务 = 第六问目标客户
- 情境下解决 = 第七问客户问题 + 场景
- 通过 = 第二问变现载体

## 方式 A：对话内 Visualizer（show_widget）

五要素填实后调用 `show_widget`。`title` 设为「一句话商业定位卡片」；`loading_messages` 用 `["正在生成定位卡片","渲染排版中","马上就好"]`。

```svg
<svg role="img" width="100%" viewBox="0 0 680 420" xmlns="http://www.w3.org/2000/svg">
  <title>一句话商业定位卡片</title>
  <desc>一人公司商业定位</desc>
  <rect x="64" y="50" width="6" height="280" rx="3" fill="#D4537E"/>
  <text x="104" y="95" font-size="32" font-family="Georgia, serif" fill="#D4537E" opacity="0.25" font-style="italic">"</text>
  <text x="130" y="120" font-size="16" font-family="var(--font-sans)" fill="#444441">
    <tspan font-weight="400" fill="#888780">我凭借 </tspan>
    <tspan font-weight="500" fill="#2C2C2A">【凭借】</tspan>
    <tspan font-weight="400" fill="#888780">，服务 </tspan>
    <tspan font-weight="500" fill="#2C2C2A">【服务】</tspan>
    <tspan font-weight="400" fill="#888780">，</tspan>
  </text>
  <text x="130" y="156" font-size="16" font-family="var(--font-sans)" fill="#444441">
    <tspan font-weight="400" fill="#888780">在 </tspan>
    <tspan font-weight="500" fill="#2C2C2A">【情境】</tspan>
    <tspan font-weight="400" fill="#888780">的情境下解决 </tspan>
    <tspan font-weight="500" fill="#2C2C2A">【问题】</tspan>
    <tspan font-weight="400" fill="#888780">的问题，</tspan>
  </text>
  <text x="130" y="192" font-size="16" font-family="var(--font-sans)" fill="#444441">
    <tspan font-weight="400" fill="#888780">通过 </tspan>
    <tspan font-weight="500" fill="#2C2C2A">【交付】</tspan>
    <tspan font-weight="400" fill="#888780">交付。</tspan>
  </text>
  <text x="600" y="220" font-size="32" font-family="Georgia, serif" fill="#D4537E" opacity="0.25" font-style="italic">"</text>
  <line x1="104" y1="275" x2="620" y2="275" stroke="#D3D1C7" stroke-width="0.5"/>
  <text x="104" y="318" font-size="13" font-family="var(--font-sans)" font-weight="400" fill="#5F5E5A">
    商业象限：<tspan font-weight="500" fill="#2C2C2A">Q【编号】 第【X】象限 【虚拟/实体】</tspan>
  </text>
  <text x="104" y="340" font-size="13" font-family="var(--font-sans)" font-weight="400" fill="#888780">
    主原力：【XX】型
  </text>
  <text x="104" y="362" font-size="13" font-family="var(--font-sans)" font-weight="400" fill="#5F5E5A">
    💰 定价：【结构】｜首单【区间】
  </text>
  <text x="104" y="384" font-size="13" font-family="var(--font-sans)" font-weight="400" fill="#5F5E5A">
    🔥 差异化：【锚点】——不像【同类】的是【关键不同】
  </text>
  <text x="620" y="325" text-anchor="end" font-size="13" font-family="var(--font-sans)" font-weight="400" fill="#888780">
    一人公司商业定位专家 · 孔知位
  </text>
</svg>
```

## 方式 B：HTML 文件保存（Write + present_files）

写入 `outputs/一句话商业定位卡片.html`，再用 `present_files` 展示。

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>一句话商业定位卡片</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    display: flex; justify-content: center; align-items: center;
    min-height: 100vh; background: #09090B;
    font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', -apple-system, sans-serif;
  }
</style>
</head>
<body>
<svg role="img" width="800" height="420" viewBox="0 0 800 420" xmlns="http://www.w3.org/2000/svg">
  <title>一句话商业定位卡片</title>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#FAFAF9"/>
      <stop offset="100%" stop-color="#F5F5F4"/>
    </linearGradient>
    <linearGradient id="accentLine" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#F43F5E"/>
      <stop offset="100%" stop-color="#EC4899"/>
    </linearGradient>
    <filter id="cardShadow" x="-2%" y="-2%" width="104%" height="106%">
      <feDropShadow dx="0" dy="2" stdDeviation="20" flood-color="#000" flood-opacity="0.06"/>
    </filter>
  </defs>

  <rect x="40" y="30" width="720" height="360" rx="24" fill="url(#bg)" filter="url(#cardShadow)"/>
  <rect x="40" y="30" width="6" height="360" rx="3" fill="url(#accentLine)"/>
  <text x="80" y="80" font-size="40" font-family="Georgia, serif" fill="#F43F5E" opacity="0.25" font-style="italic">"</text>

  <g font-size="18" fill="#292524">
    <text x="110" y="115" dominant-baseline="central" letter-spacing="1">
      <tspan font-weight="400" fill="#78716C">我凭借 </tspan>
      <tspan font-weight="600" fill="#1C1917">【凭借】</tspan>
      <tspan font-weight="400" fill="#78716C">，服务 </tspan>
      <tspan font-weight="600" fill="#1C1917">【服务】</tspan>
      <tspan font-weight="400" fill="#78716C">，</tspan>
    </text>
    <text x="110" y="155" dominant-baseline="central" letter-spacing="1">
      <tspan font-weight="400" fill="#78716C">在 </tspan>
      <tspan font-weight="600" fill="#1C1917">【情境】</tspan>
      <tspan font-weight="400" fill="#78716C">的情境下解决 </tspan>
      <tspan font-weight="600" fill="#1C1917">【问题】</tspan>
      <tspan font-weight="400" fill="#78716C">的问题，</tspan>
    </text>
    <text x="110" y="195" dominant-baseline="central" letter-spacing="1">
      <tspan font-weight="400" fill="#78716C">通过 </tspan>
      <tspan font-weight="600" fill="#1C1917">【交付】</tspan>
      <tspan font-weight="400" fill="#78716C">交付。</tspan>
    </text>
  </g>

  <text x="700" y="230" font-size="40" font-family="Georgia, serif" fill="#F43F5E" opacity="0.25" font-style="italic">"</text>
  <line x1="80" y1="280" x2="720" y2="280" stroke="#E7E5E4" stroke-width="0.5"/>

  <g font-size="13">
    <text x="80" y="325" dominant-baseline="central" font-weight="500" fill="#78716C">
      商业象限：<tspan font-weight="600" fill="#1C1917">Q【编号】 第【X】象限 【虚拟/实体】</tspan>
    </text>
    <text x="80" y="355" dominant-baseline="central" font-weight="400" fill="#A8A29E">
      主原力：【XX】型
    </text>
    <text x="80" y="378" dominant-baseline="central" font-weight="400" fill="#78716C">
      💰 定价：【结构】｜首单【区间】
    </text>
    <text x="80" y="400" dominant-baseline="central" font-weight="400" fill="#78716C">
      🔥 差异化：【锚点】——不像【同类】的是【关键不同】
    </text>
    <text x="680" y="340" text-anchor="end" dominant-baseline="central" font-weight="400" fill="#A8A29E" letter-spacing="1">
      一人公司商业定位专家 · 孔知位
    </text>
  </g>
</svg>
</body>
</html>
```

## 纯文本复制版

紧随 Visualizer 之后输出代码块：

```
我凭借【凭借】，服务【服务】，在【情境】的情境下解决【问题】的问题，通过【交付】交付。

📍 Q【编号】 第【X】象限 【虚拟/实体】 | ⚡ 主原力：【XX】型
💰 定价结构：【结构】｜首单价格带：【区间】
🔥 差异化：【锚点】——不像【同类】的是【关键不同】
```
