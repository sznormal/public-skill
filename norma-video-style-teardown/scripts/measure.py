#!/usr/bin/env python
"""视频风格拉片 — 第2步：色彩采样 + 版式测量。
用法: python measure.py "<frames目录>" [关键帧png...]
不传帧名则对目录内所有 sec_*.png 采样。
"""
import cv2, numpy as np, os, sys, json

def hexof(bgr):
    b, g, r = [int(x) for x in bgr]; return "#%02x%02x%02x" % (r, g, b)

def analyze(fn, path):
    img = cv2.imread(path)
    f = img.reshape(-1, 3).astype(np.float32)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, lab, cen = cv2.kmeans(f, 6, None, crit, 3, cv2.KMEANS_PP_CENTERS)
    counts = np.bincount(lab.flatten(), minlength=6)
    order = np.argsort(-counts)
    dom = [{"hex": hexof(cen[i]), "pct": round(100*counts[i]/len(f), 1)} for i in order]
    b, g, r = (img[:, :, i].astype(int) for i in range(3))
    warm = (r - b > 50) & (r > 120)        # 琥珀/金
    cool = (b - r > 40) & (b > 110)        # 冷蓝灰
    white = (r > 200) & (g > 200) & (b > 200)
    def mean_hex(mask):
        return hexof(img[mask].mean(axis=0)) if mask.sum() > 20 else None
    return {"file": fn, "dominant": dom,
            "accent_warm": {"hex": mean_hex(warm), "px": int(warm.sum())},
            "accent_cool": {"hex": mean_hex(cool), "px": int(cool.sum())},
            "text_white": {"hex": mean_hex(white), "px": int(white.sum())},
            "mean_lum": round(float(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()), 2)}

def bands(img, x0, x1, thr=100, minpx=3):
    g = cv2.cvtColor(img[:, x0:x1], cv2.COLOR_BGR2GRAY)
    m = (g > thr).sum(axis=1); out = []; s = None
    for y, v in enumerate(m):
        if v > minpx and s is None: s = y
        if v <= minpx and s is not None: out.append((s, y-1, y-s)); s = None
    if s is not None: out.append((s, len(m)-1, len(m)-s))
    return [b for b in out if b[2] >= 3]

def main():
    d = sys.argv[1]
    names = sys.argv[2:] or sorted(f for f in os.listdir(d) if f.startswith("sec_"))
    res = []
    for fn in names:
        p = os.path.join(d, fn)
        if not os.path.exists(p): continue
        r = analyze(fn, p); res.append(r)
        print(fn, "| dom:", [x["hex"] for x in r["dominant"][:3]])
        print("   warm", r["accent_warm"], "cool", r["accent_cool"],
              "white", r["text_white"], "lum", r["mean_lum"])
    # 行带：对每张图给出行带（字号/位置），x 区间按需修改
    for fn in names[:3]:
        p = os.path.join(d, fn)
        if not os.path.exists(p): continue
        img = cv2.imread(p)
        print("== bands", fn, "(x 40-920, thr 100):")
        for b in bands(img, 40, 920):
            print("   y %d-%d h=%d" % b)
    json.dump(res, open(os.path.join(d, "..", "colors.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
