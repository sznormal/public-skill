# -*- coding: utf-8 -*-
"""
机器人编程基础 —— 章节 Markdown → 带封面/水印的 PDF

用法:
    python build_chapter.py "<md文件路径>" "<输出目录>"

流程:
    1. Markdown → HTML（含封面页、正文页、水印层）
    2. Playwright + 本机 Chrome 打印为 PDF
       - 第 1 次调用: 只保留封面(page margin=0, 无页脚) → cover.pdf
       - 第 2 次调用: 只保留正文(正常页边距, 带页脚页码) → body.pdf
    3. pypdf 合并 → 最终 PDF
"""
import io
import os
import re
import sys
import html as html_mod
import shutil
import tempfile
from pathlib import Path

import markdown

# ---------------------------------------------------------------- 常量
BASE = Path(__file__).resolve().parent
ASSETS = BASE / "assets"
BUILD = BASE / "build"

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]

# 封面 / 水印配置（可由命令行覆盖）
CFG = {
    "book": "机器人编程基础",           # 封面主标题（书名）
    "school": "深圳信息职业技术大学",   # 单位名称（封面 + 页脚 + 水印默认值）
    "author": "郑洪英",                 # 编著者
    "badge": "学生版",                  # 封面徽标
    "watermark": "",                    # 水印文字，留空则用 school
}

# 品牌色
INDIGO = "#4f46e5"
INDIGO_DARK = "#312e81"
GOLD = "#f59e0b"

WM_COUNT = 12  # 每页水印文字个数

# mermaid 图可用绘制区（px @96dpi）
#   A4 210mm - 左右各 18mm = 174mm ≈ 658px
#   A4 297mm - 上 16mm - 下 18mm = 263mm ≈ 994px（再留出图注空间）
MAX_W = 640
MAX_H = 850


def wm_text() -> str:
    return CFG["watermark"] or CFG["school"]


# ---------------------------------------------------------------- 工具
def find_browser() -> str:
    for p in CHROME_CANDIDATES:
        if os.path.exists(p):
            return p
    raise RuntimeError("未找到可用的 Chrome / Edge 浏览器")


MERMAID_URLS = [
    "https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js",
    "https://unpkg.com/mermaid@10.9.1/dist/mermaid.min.js",
]


def ensure_mermaid() -> Path:
    """确保本地存在 mermaid.min.js（缺失时下载一次，之后离线可用）。"""
    ASSETS.mkdir(parents=True, exist_ok=True)
    dst = ASSETS / "mermaid.min.js"
    if dst.exists() and dst.stat().st_size > 100_000:
        return dst
    import urllib.request

    for url in MERMAID_URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=90).read()
            if len(data) > 100_000:
                dst.write_bytes(data)
                return dst
        except Exception:
            continue
    raise RuntimeError(
        f"无法下载 mermaid.min.js，请手动保存到 {dst}（来源：{MERMAID_URLS[0]}）"
    )


def prepare_build_dir() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    src = ensure_mermaid()
    dst = BUILD / "mermaid.min.js"
    if not dst.exists() or dst.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dst)


# ---------------------------------------------------------------- Markdown 预处理
MERMAID_RE = re.compile(r"^```mermaid\s*\n(.*?)^```\s*$", re.S | re.M)


def extract_mermaid(text: str):
    """把 ```mermaid 代码块抽出来，替换为占位符。"""
    blocks = []

    def repl(m):
        blocks.append(m.group(1).rstrip())
        return f"\n\n@@MERMAID_{len(blocks) - 1}@@\n\n"

    text = MERMAID_RE.sub(repl, text)
    return text, blocks


def md_to_html(text: str) -> str:
    md = markdown.Markdown(
        extensions=[
            "extra",            # tables / fenced_code / attr_list / md_in_html ...
            "sane_lists",
            "admonition",
        ],
        output_format="html5",
    )
    return md.convert(text)


def restore_mermaid(html_text: str, blocks) -> str:
    """把占位符还原为 mermaid 容器。"""
    for i, code in enumerate(blocks):
        block = '<div class="mermaid">\n' + html_mod.escape(code) + "\n</div>"
        # 占位符通常被包在 <p> 里
        html_text = re.sub(
            r"<p>\s*@@MERMAID_%d@@\s*</p>" % i, lambda m: block, html_text
        )
        html_text = html_text.replace("@@MERMAID_%d@@" % i, block)
    # 兜底：fenced_code 万一没被抽走
    html_text = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        lambda m: '<div class="mermaid">' + m.group(1) + "</div>",
        html_text,
        flags=re.S,
    )
    return html_text


HEAD1_RE = re.compile(r"^\s*#\s+(.+?)\s*#*\s*$", re.M)


def split_title(text: str):
    """取出首个一级标题作为章节标题，并从正文中移除。"""
    m = HEAD1_RE.search(text)
    title = m.group(1).strip() if m else "未命名章节"
    if m:
        text = text[: m.start()] + text[m.end():]
    return title, text.lstrip()


CHAPTER_NO_RE = re.compile(r"^第\s*([0-9]+|[一二三四五六七八九十]+)\s*章")


def chapter_number(title: str) -> str:
    m = CHAPTER_NO_RE.match(title)
    return m.group(1) if m else ""


def chapter_name(title: str) -> str:
    """去掉开头的『第N章』，留章节名。"""
    return CHAPTER_NO_RE.sub("", title).strip()


# ---------------------------------------------------------------- CSS
BASE_CSS = f"""
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{
  font-family: "SimSun", "宋体", "Microsoft YaHei", serif;
  font-size: 11pt;
  line-height: 1.85;
  color: #1f2937;
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}}

/* ---------------- 水印 ---------------- */
.wm {{
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 900;
  overflow: hidden;
  pointer-events: none;
}}
.wm-grid {{
  width: 100%; height: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-auto-rows: 1fr;
  place-items: center;
}}
.wm-grid span {{
  transform: rotate(-30deg);
  white-space: nowrap;
  font-family: "Microsoft YaHei", sans-serif;
  font-weight: 700;
  font-size: 26px;
  letter-spacing: 8px;
  color: rgba(79, 70, 229, 0.11);
}}

/* ---------------- 正文 ---------------- */
.content {{
  position: relative;
  z-index: 1;
}}
h1, h2, h3, h4, h5, h6 {{
  font-family: "Microsoft YaHei", "黑体", sans-serif;
  color: {INDIGO_DARK};
  line-height: 1.5;
  break-after: avoid-page;
  page-break-after: avoid;
}}
h1 {{ font-size: 20pt; }}
h2 {{
  font-size: 15pt;
  margin: 26px 0 12px;
  padding: 6px 0 6px 14px;
  border-left: 6px solid {INDIGO};
  background: linear-gradient(90deg, rgba(79,70,229,0.085), rgba(79,70,229,0));
  border-radius: 3px;
}}
h3 {{
  font-size: 13pt;
  margin: 20px 0 9px;
  padding-left: 10px;
  border-left: 3px solid {GOLD};
}}
h4 {{ font-size: 11.5pt; margin: 16px 0 7px; color: #4338ca; }}
p {{ margin: 9px 0; text-align: justify; }}

strong {{ font-weight: 700; color: #111827; }}

a {{ color: {INDIGO}; text-decoration: none; }}

/* 列表 */
ul, ol {{ margin: 9px 0 9px 0; padding-left: 26px; }}
li {{ margin: 4px 0; }}
li > p {{ margin: 3px 0; }}

/* 行内代码 */
code {{
  font-family: Consolas, "Courier New", "Microsoft YaHei", monospace;
  font-size: 9.5pt;
  background: #eef1f8;
  color: #b91c1c;
  padding: 1px 5px;
  border-radius: 3px;
  word-break: break-word;
}}

/* 代码块 */
pre {{
  background: #f7f8fc;
  border: 1px solid #e0e4f0;
  border-left: 4px solid {INDIGO};
  border-radius: 4px;
  padding: 10px 14px;
  margin: 12px 0;
  font-size: 9.5pt;
  line-height: 1.62;
  white-space: pre-wrap;
  word-break: break-all;
  break-inside: avoid;
  page-break-inside: avoid;
  overflow: visible;
}}
pre code {{
  background: none;
  color: #1e293b;
  padding: 0;
  font-size: 9.5pt;
  white-space: pre-wrap;
  word-break: break-all;
}}

/* 表格 */
table {{
  border-collapse: collapse;
  width: 100%;
  margin: 14px 0;
  font-family: "Microsoft YaHei", sans-serif;
  font-size: 9.5pt;
  break-inside: avoid;
  page-break-inside: avoid;
}}
th {{
  background: #eef2ff;
  color: {INDIGO_DARK};
  font-weight: 700;
  border: 1px solid #c7d2fe;
  padding: 7px 9px;
  text-align: left;
}}
td {{
  border: 1px solid #dbe0f0;
  padding: 6px 9px;
  vertical-align: top;
}}
tbody tr:nth-child(even) td {{ background: #fafbff; }}

/* 引用 */
blockquote {{
  margin: 12px 0;
  padding: 9px 16px;
  border-left: 4px solid {GOLD};
  background: #fffbeb;
  color: #78350f;
  border-radius: 0 4px 4px 0;
  break-inside: avoid;
}}
blockquote p {{ margin: 4px 0; }}

/* 分隔线 */
hr {{
  border: none;
  border-top: 1px dashed #cbd5e1;
  margin: 18px 0;
}}

/* 图片 */
img {{ max-width: 100%; height: auto; }}

/* mermaid 图 */
.mermaid {{
  margin: 16px 0;
  text-align: center;
  break-inside: avoid;
  page-break-inside: avoid;
}}
.mermaid svg {{
  max-width: 100% !important;
}}

/* 居中图注 */
div[align="center"] {{
  text-align: center;
  font-family: "Microsoft YaHei", sans-serif;
  font-size: 9.5pt;
  color: #64748b;
  margin: 4px 0 16px;
}}
"""

COVER_CSS = f"""
.cover {{
  position: relative;
  z-index: 1;
  width: 210mm;
  height: 296mm;
  overflow: hidden;
  background: #ffffff;
}}
.cover-inner {{
  position: relative;
  height: 100%;
  padding: 0 22mm;
  display: flex;
  flex-direction: column;
}}
.cover-band {{
  height: 16mm;
  background: {INDIGO};
  margin: 0 -22mm;
}}
.cover-band-gold {{
  height: 3mm;
  background: {GOLD};
  margin: 0 -22mm;
}}
.cover-school {{
  margin-top: 12mm;
  font-family: "Microsoft YaHei", sans-serif;
  font-size: 13pt;
  letter-spacing: 7px;
  color: {INDIGO};
  font-weight: 700;
}}
.cover-school-en {{
  margin-top: 3mm;
  font-family: Arial, Helvetica, sans-serif;
  font-size: 8pt;
  letter-spacing: 2.4px;
  color: #94a3b8;
  text-transform: uppercase;
}}
.cover-body {{
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}}
.cover-title {{
  font-family: "Microsoft YaHei", "黑体", sans-serif;
  font-size: 40pt;
  font-weight: 700;
  letter-spacing: 10px;
  color: #1e1b4b;
  margin: 0;
  line-height: 1.3;
}}
.cover-rule {{
  width: 34mm;
  height: 3px;
  background: {GOLD};
  margin: 8mm 0;
}}
.cover-badge {{
  display: inline-block;
  font-family: "Microsoft YaHei", sans-serif;
  font-size: 9pt;
  letter-spacing: 4px;
  color: {INDIGO};
  border: 1px solid {INDIGO};
  border-radius: 20px;
  padding: 2px 14px;
  margin-bottom: 16mm;
}}
.cover-chapno {{
  font-family: "Microsoft YaHei", sans-serif;
  font-size: 12pt;
  letter-spacing: 5px;
  color: {GOLD};
  font-weight: 700;
  margin-bottom: 4mm;
}}
.cover-chapname {{
  font-family: "Microsoft YaHei", "黑体", sans-serif;
  font-size: 21pt;
  font-weight: 700;
  color: {INDIGO};
  line-height: 1.5;
  max-width: 150mm;
}}
.cover-meta {{
  border-top: 1px solid #e2e8f0;
  padding: 7mm 0 10mm;
  text-align: center;
}}
.cover-meta p {{
  margin: 2mm 0;
  font-family: "Microsoft YaHei", sans-serif;
  font-size: 12pt;
  color: #475569;
  letter-spacing: 2px;
  text-align: center;
}}
.cover-band-bottom {{
  height: 4mm;
  background: {GOLD};
  margin: 0 -22mm;
}}
.cover-band-bottom2 {{
  height: 8mm;
  background: {INDIGO};
  margin: 0 -22mm;
}}
"""


def build_html(title: str, body_html: str) -> str:
    no = chapter_number(title)
    name = chapter_name(title)
    chap_label = f"第 {no} 章" if no else ""

    wm = "".join(f"<span>{wm_text()}</span>" for _ in range(WM_COUNT))

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{html_mod.escape(title)}</title>
<style>
{BASE_CSS}
{COVER_CSS}
</style>
</head>
<body>
<div class="wm"><div class="wm-grid">{wm}</div></div>

<section class="cover">
  <div class="cover-inner">
    <div class="cover-band"></div>
    <div class="cover-band-gold"></div>

    <div class="cover-school">{CFG['school']}</div>
    <div class="cover-school-en">Shenzhen Institute of Information Technology</div>

    <div class="cover-body">
      <div class="cover-title">{CFG['book']}</div>
      <div class="cover-rule"></div>
      <div class="cover-badge">{CFG['badge']}</div>
      <div class="cover-chapno">{chap_label}</div>
      <div class="cover-chapname">{html_mod.escape(name)}</div>
    </div>

    <div class="cover-meta">
      <p>编著：{CFG['author']}</p>
      <p>单位：{CFG['school']}</p>
    </div>

    <div class="cover-band-bottom"></div>
    <div class="cover-band-bottom2"></div>
  </div>
</section>

<div class="content">
{body_html}
</div>

<script src="./mermaid.min.js"></script>
<script>
(function () {{
  // 打印区域的可用像素尺寸（A4 - 页边距），按需等比缩小 mermaid 图
  var MAXW = {MAX_W}, MAXH = {MAX_H};

  function fitSvgs() {{
    var n = 0;
    document.querySelectorAll('.mermaid svg').forEach(function (s) {{
      var vb = s.viewBox && s.viewBox.baseVal;
      var w = (vb && vb.width) ? vb.width : 0;
      var h = (vb && vb.height) ? vb.height : 0;
      if (!w || !h) {{
        var r = s.getBoundingClientRect();
        w = r.width; h = r.height;
      }}
      if (!w || !h) return;
      var k = Math.min(MAXW / w, MAXH / h, 1);
      s.removeAttribute('style');
      s.setAttribute('width', (w * k).toFixed(1));
      s.setAttribute('height', (h * k).toFixed(1));
      s.style.maxWidth = '100%';
      s.style.display = 'block';
      s.style.margin = '0 auto';
      s.setAttribute('data-fit-scale', k.toFixed(3));
      n++;
    }});
    window.__fitCount = n;
    return n;
  }}

  try {{
    mermaid.initialize({{
      startOnLoad: false,
      theme: 'base',
      fontFamily: '"Microsoft YaHei", sans-serif',
      themeVariables: {{
        primaryColor: '#eef2ff',
        primaryTextColor: '#1e1b4b',
        primaryBorderColor: '#4f46e5',
        lineColor: '#4f46e5',
        secondaryColor: '#fffbeb',
        tertiaryColor: '#f8fafc',
        fontSize: '15px'
      }},
      flowchart: {{ useMaxWidth: false, htmlLabels: true, curve: 'basis', nodeSpacing: 40, rankSpacing: 42 }}
    }});
    var task = mermaid.run({{ querySelector: '.mermaid' }});
    Promise.resolve(task).then(function () {{
      fitSvgs();
      window.__mermaidDone = true;
    }}).catch(function () {{
      fitSvgs();
      window.__mermaidDone = true;
    }});
  }} catch (e) {{
    window.__mermaidError = String(e);
    window.__mermaidDone = true;
  }}
}})();
</script>
</body>
</html>
"""


def footer_template() -> str:
    return f"""
<div style="width:100%;font-family:'Microsoft YaHei',sans-serif;font-size:8px;color:#94a3b8;
            padding:0 18mm;">
  <div style="border-top:0.5px solid #e2e8f0;padding-top:4px;
              display:flex;justify-content:space-between;">
    <span>{CFG['book']} · {CFG['badge']}</span>
    <span>{CFG['school']}　第 <span class="pageNumber"></span> 页</span>
  </div>
</div>
"""


FOOTER_TMPL = footer_template()


MM = 1.0 / 25.4  # 毫米 → 英寸


def render_pdf(md_path: Path, out_path: Path, cdp=None) -> dict:
    import time
    from pypdf import PdfWriter, PdfReader
    from cdp_print import ChromeCDP

    raw = md_path.read_text(encoding="utf-8")
    title, body_md = split_title(raw)
    body_md, mer_blocks = extract_mermaid(body_md)
    body_html = md_to_html(body_md)
    body_html = restore_mermaid(body_html, mer_blocks)

    html_doc = build_html(title, body_html)
    BUILD.mkdir(parents=True, exist_ok=True)
    tmp_html = BUILD / (md_path.stem + ".html")
    tmp_html.write_text(html_doc, encoding="utf-8")

    cover_pdf = BUILD / (md_path.stem + "__cover.pdf")
    body_pdf = BUILD / (md_path.stem + "__body.pdf")

    own_browser = cdp is None
    if own_browser:
        cdp = ChromeCDP(find_browser())

    m_err, m_cnt = "", 0
    try:
        cdp.open_page(tmp_html.as_uri())
        cdp.wait_for("document.readyState === 'complete'", timeout=90)
        # 等待 mermaid 渲染完成
        cdp.wait_for(
            "window.__mermaidDone === true && "
            f"document.querySelectorAll('.mermaid svg').length >= {len(mer_blocks)}",
            timeout=120,
        )
        time.sleep(1.2)

        m_err = cdp.evaluate("window.__mermaidError || ''") or ""
        m_cnt = cdp.evaluate("document.querySelectorAll('.mermaid svg').length") or 0
        m_scales = cdp.evaluate(
            "Array.from(document.querySelectorAll('.mermaid svg'))"
            ".map(function(s){return s.getAttribute('data-fit-scale');})"
        ) or []

        # ---- 封面（满页出血、无页眉页脚）----
        # 注意：不要隐藏 .content —— 隐藏/恢复会打乱已渲染 mermaid SVG 的尺寸，
        # 只需用 pageRanges="1" 取第 1 页（封面）即可。
        time.sleep(0.3)
        cdp.print_pdf(str(cover_pdf), margins=(0, 0, 0, 0), page_ranges="1")

        # ---- 正文（正常页边距 + 页脚页码）----
        cdp.evaluate("document.querySelector('.cover').style.display='none';")
        time.sleep(0.6)
        cdp.print_pdf(
            str(body_pdf),
            margins=(16 * MM, 18 * MM, 18 * MM, 18 * MM),
            footer=footer_template(),
        )
    finally:
        if own_browser:
            cdp.close()

    # ---- 合并封面 + 正文 ----
    writer = PdfWriter()
    for f in (cover_pdf, body_pdf):
        for pg in PdfReader(str(f)).pages:
            writer.add_page(pg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fh:
        writer.write(fh)
    writer.close()

    return {
        "title": title,
        "cover_pages": len(PdfReader(str(cover_pdf)).pages),
        "body_pages": len(PdfReader(str(body_pdf)).pages),
        "mermaid_rendered": m_cnt,
        "mermaid_scales": m_scales,
        "mermaid_error": m_err,
        "total_pages": len(PdfReader(str(out_path)).pages),
    }


def main():
    import argparse

    ap = argparse.ArgumentParser(description="Markdown → 带封面与水印的 PDF")
    ap.add_argument("md", help="Markdown 文件路径")
    ap.add_argument("out_dir", help="输出目录")
    ap.add_argument("--book", default=CFG["book"], help="封面主标题（书名）")
    ap.add_argument("--school", default=CFG["school"], help="单位名称（封面/页脚）")
    ap.add_argument("--author", default=CFG["author"], help="编著者姓名")
    ap.add_argument("--badge", default=CFG["badge"], help="封面徽标，如：学生版")
    ap.add_argument("--watermark", default=CFG["watermark"], help="水印文字（默认同单位）")
    args = ap.parse_args()

    CFG.update(
        book=args.book,
        school=args.school,
        author=args.author,
        badge=args.badge,
        watermark=args.watermark,
    )

    md_path = Path(args.md).resolve()
    out_dir = Path(args.out_dir).resolve()
    prepare_build_dir()
    info = render_pdf(md_path, out_dir / (md_path.stem + ".pdf"))
    print(
        f"[OK] {md_path.name} -> {md_path.stem}.pdf | "
        f"封面 {info['cover_pages']} 页 + 正文 {info['body_pages']} 页 "
        f"= 共 {info['total_pages']} 页 | mermaid {info['mermaid_rendered']} 个"
        + (f" | ERR: {info['mermaid_error']}" if info["mermaid_error"] else "")
    )


if __name__ == "__main__":
    main()
