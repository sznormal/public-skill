# draw.io XML 规范

生成代码、排查导入失败时加载本文件。

## 最小可用骨架

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="Electron" type="device">
  <diagram id="roadmap" name="技术路线图">
    <mxGraphModel dx="1100" dy="700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="826" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="2" value="阶段一" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#4f46e5;fontColor=#ffffff;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fontFamily=Microsoft YaHei;" vertex="1" parent="1">
          <mxGeometry x="80" y="80" width="200" height="50" as="geometry" />
        </mxCell>
        <mxCell id="3" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#64748b;" edge="1" parent="1" source="2" target="4">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

规则：

- `id="0"` 与 `id="1"` 必须存在，`id="1"` 的 `parent="0"`。
- 其余节点 `id` 从 `2` 起连续编号，全局唯一。
- 所有业务节点 `parent="1"`。
- 未压缩明文，禁止 `compressed="true"`。

## 转义规则

| 原文 | 必须写成 |
|---|---|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&apos;` |

换行（配合 `html=1`）写成 `&lt;br&gt;`。示例：

```xml
<mxCell id="5" value="数据采集&lt;br&gt;与预处理" style="rounded=1;whiteSpace=wrap;html=1;fontFamily=Microsoft YaHei;" vertex="1" parent="1">
  <mxGeometry x="80" y="160" width="200" height="60" as="geometry" />
</mxCell>
```

## 样式速查表

所有样式默认带 `fontFamily=Microsoft YaHei`，中文不使用 Helvetica。

| 用途 | style 值 |
|---|---|
| 主标题条 | `rounded=0;whiteSpace=wrap;html=1;fillColor=#4f46e5;fontColor=#ffffff;strokeColor=#3730a3;fontSize=16;fontStyle=1;align=center;verticalAlign=middle;fontFamily=Microsoft YaHei;` |
| 阶段分区（泳道） | `swimlane;html=1;startSize=40;fillColor=#f8fafc;strokeColor=#cbd5e1;fontSize=14;fontStyle=1;align=center;verticalAlign=middle;fontFamily=Microsoft YaHei;` |
| 普通卡片 | `rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#eef2ff;strokeColor=#4f46e5;fontColor=#1f2937;fontSize=12;align=center;verticalAlign=middle;fontFamily=Microsoft YaHei;` |
| 强调卡片 | `rounded=1;arcSize=8;whiteSpace=wrap;html=1;fillColor=#f59e0b;strokeColor=#b45309;fontColor=#ffffff;fontSize=12;fontStyle=1;align=center;verticalAlign=middle;fontFamily=Microsoft YaHei;` |
| 中性说明框 | `rounded=0;whiteSpace=wrap;html=1;fillColor=#f1f5f9;strokeColor=#94a3b8;fontColor=#334155;fontSize=11;align=left;verticalAlign=middle;spacingLeft=8;fontFamily=Microsoft YaHei;` |
| 虚线分组框 | `rounded=1;dashed=1;dashPattern=8 4;html=1;fillColor=none;strokeColor=#94a3b8;fontColor=#475569;fontSize=12;fontFamily=Microsoft YaHei;verticalAlign=top;` |
| 主流程连线 | `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#64748b;` |
| 强调连线 | `edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#4f46e5;` |
| 反馈虚线 | `edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;dashed=1;endArrow=block;endFill=1;strokeWidth=2;strokeColor=#f59e0b;` |
| 无向关联线 | `endArrow=none;html=1;dashed=1;strokeColor=#94a3b8;strokeWidth=1;` |

## 几何与坐标

- `gridSize="10"`，`x / y / width / height` 取 10 的倍数。
- 顶点写 `<mxGeometry x=".." y=".." width=".." height=".." as="geometry" />`。
- 连线写 `<mxGeometry relative="1" as="geometry" />`。
- 子节点（放入泳道或分组框）的坐标相对父容器左上角。
- 需要固定连线走向时，在连线的 `mxGeometry` 内加 `<Array as="points"><mxPoint x=".." y=".." /></Array>`。

## 中文与字体

- 一律 `fontFamily=Microsoft YaHei`；标题加 `fontStyle=1`，正文不加。
- 标题 `fontSize=14—16`，分区标题 `14`，卡片正文 `11—12`。
- 卡片内长文本使用 `align=left;spacingLeft=8`，居中短文本使用 `align=center`。

## 落盘位置

- XML 落在 `drawio-projects/<图名>/<图名>.drawio`，由 S5 阶段写入。
- 同一项目的版式规格、内容结构、坐标布局落在同目录的 `01-版式规格.md`、`02-内容结构.md`、`03-坐标布局.md`。
- 落盘后运行 `python scripts/validate_drawio.py <文件路径>`，把 `errors`、`warnings` 条数写回 `manifest.json` 的 `validation` 字段。
- 文件重名时追加 `-2`、`-3` 序号，不覆盖已有文件。

## 导入方式

1. 打开 diagrams.net 或 draw.io 桌面版。
2. 菜单 `Extras` → `Edit Diagram`（中文界面：其他 → 编辑绘图）。
3. 全选原有内容并删除，粘贴完整 XML，点击 `Apply`（应用）。
4. 或用 `File` → `Import from` → `Advanced` → `Edit XML...`，同样粘贴后应用。

## 自检清单

- [ ] XML 声明为 `<?xml version="1.0" encoding="UTF-8"?>`，文件保存为 UTF-8。
- [ ] 根元素为 `mxfile`，逐级含 `diagram` → `mxGraphModel` → `root`。
- [ ] 存在 `id="0"` 与 `id="1"`。
- [ ] 所有 `mxCell id` 唯一；连线 `source` 与 `target` 均指向已存在的 id。
- [ ] 每条连线带 `edge="1"` 且 `parent="1"`。
- [ ] 每个顶点带 `vertex="1"`、`parent="1"` 和 `mxGeometry as="geometry"`。
- [ ] `&`、`<`、`>` 已转义；`value` 内换行写 `&lt;br&gt;`。
- [ ] 无 `compressed="true"`，无 base64 负载。

## 常见导入失败原因

| 现象 | 原因 | 处理 |
|---|---|---|
| 提示 XML 解析错误 | 裸 `&`、`<`、`>` 未转义 | 按转义表替换 |
| 粘贴后一片空白 | 缺少 `mxfile` 或 `diagram` 外层 | 补齐外层结构 |
| 连线不显示 | 缺 `edge="1"` 或 `source`/`target` 无效 | 补齐属性和有效 id |
| 中文方框或乱码 | 字体未指定中文字体或文件非 UTF-8 | 加 `fontFamily=Microsoft YaHei`，改存 UTF-8 |
| 节点全部堆在左上角 | 缺 `mxGeometry as="geometry"` | 补齐几何节点 |
| 内容为压缩串 | 误用 `compressed="true"` | 输出未压缩明文 |
