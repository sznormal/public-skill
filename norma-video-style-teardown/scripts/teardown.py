#!/usr/bin/env python
"""视频风格拉片 — 第1步：元数据 + 运动能量 + 抽帧 + 拼图。
用法: python teardown.py "<视频路径>" "<输出目录>"
无 ffmpeg 依赖，用 OpenCV 自带解码。
"""
import cv2, numpy as np, os, sys, json

def grid(frames, cols, tw, th, out_path, base=20):
    rows = (len(frames) + cols - 1) // cols
    sheet = np.zeros((rows * th, cols * tw, 3), np.uint8) + base
    for k, im in enumerate(frames):
        im = cv2.resize(im, (tw, th))
        r, c = divmod(k, cols)
        sheet[r*th:(r+1)*th, c*tw:(c+1)*tw] = im
    cv2.imwrite(out_path, sheet)
    return sheet.shape

def main(src, out):
    frames_dir = os.path.join(out, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    cap = cv2.VideoCapture(src)
    if not cap.isOpened():
        print("ERROR: cannot open", src); sys.exit(1)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
    codec = "".join(chr((fourcc >> (8*i)) & 0xFF) for i in range(4))
    dur = n / fps if fps else 0
    size = os.path.getsize(src)
    meta = {"fps": round(fps, 3), "width": w, "height": h, "frames": n,
            "duration_sec": round(dur, 2), "codec": codec,
            "size_mb": round(size/1e6, 2), "bitrate_mbps": round(size*8/dur/1e6, 2) if dur else None}
    print("META", json.dumps(meta, ensure_ascii=False))

    # ---- per-frame motion (mean abs diff on downscaled gray) ----
    per = []; prev = None; idx = 0
    while True:
        ret, fr = cap.read()
        if not ret: break
        g = cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (320, 180)).astype(np.int16)
        if prev is not None:
            per.append((idx, float(np.mean(np.abs(g - prev)))))
        prev = g; idx += 1
    arr = np.array([d for _, d in per]) if per else np.zeros(1)
    peaks = [i for i in range(2, len(arr)-2)
             if arr[i] > arr[i-1] and arr[i] >= arr[i+1] and arr[i] > arr.max()*0.25]
    merged = []
    for p in peaks:
        if merged and p - merged[-1][-1] <= 8: merged[-1].append(p)
        else: merged.append([p])
    moments = [(round(m[0]/fps, 2), round(m[-1]/fps, 2), round(float(arr[m].max()), 3)) for m in merged]
    motion = {
        "per_frame_mean": round(float(arr.mean()), 3),
        "p95": round(float(np.percentile(arr, 95)), 3),
        "max": round(float(arr.max()), 3),
        "hard_cut_threshold_est": 10.0,
        "verdict": "无硬切（全渐变溶解）" if arr.max() < 10 else "存在硬切",
        "action_moments": moments,
        "per_second": {s: {"max": round(float(arr[s*int(fps):(s+1)*int(fps)].max()), 3),
                           "mean": round(float(arr[s*int(fps):(s+1)*int(fps)].mean()), 3)}
                       for s in range(max(1, int(dur))) if len(arr[s*int(fps):(s+1)*int(fps)])},
    }
    print("MOTION", json.dumps({k: motion[k] for k in ["per_frame_mean", "max", "verdict"]}, ensure_ascii=False))
    print("ACTION_MOMENTS:", moments)
    json.dump(motion, open(os.path.join(out, "motion.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    # ---- 1fps frames + contact sheet ----
    step = max(1, int(fps)); saved = []; metrics = []
    for fi in range(0, n, step):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, fr = cap.read()
        if not ret: break
        t = round(fi/fps, 2)
        sm = cv2.resize(fr, (240, 135))
        lab = cv2.cvtColor(sm, cv2.COLOR_BGR2LAB)
        hsv = cv2.cvtColor(sm, cv2.COLOR_BGR2HSV)
        name = "sec_%05.2f.png" % t
        cv2.imwrite(os.path.join(frames_dir, name), cv2.resize(fr, (960, 540)))
        saved.append((t, name))
        metrics.append({"time": t, "file": name,
                        "brightness": round(float(lab[:, :, 0].mean()), 1),
                        "saturation": round(float(hsv[:, :, 1].mean()), 1)})
    cap.release()

    thumbs = [cv2.imread(os.path.join(frames_dir, f)) for _, f in saved]
    print("contact_sheet", grid(thumbs, 5, 480, 270, os.path.join(frames_dir, "contact_sheet.png"), 235))

    # ---- caption strip (bottom band of each 1s frame) ----
    y0, y1 = int(0.78*540), int(0.92*540)          # 需按实际字幕位置微调
    rows = []
    for t, f in saved:
        im = cv2.imread(os.path.join(frames_dir, f))
        band = im[y0:y1, 0:960]
        lab = np.zeros((band.shape[0], 110, 3), np.uint8)
        cv2.putText(lab, "%.0fs" % t, (8, band.shape[0]//2+6), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 255), 2)
        rows.append(np.hstack([lab, band]))
        rows.append(np.zeros((6, 1070, 3), np.uint8))
    cv2.imwrite(os.path.join(frames_dir, "caption_strip.png"), np.vstack(rows))
    print("caption_strip done（y 区间 %.2f-%.2f，若字幕没框住请调整 y0/y1）" % (0.78, 0.92))

    # ---- transition strips around action moments ----
    for i, (a, b, _) in enumerate(moments):
        a2, b2 = max(0, a - 0.7), min(dur, b + 0.8)
        fs = []; stepf = max(1, int((b2 - a2) * fps / 12))
        for fi in range(int(a2*fps), int(b2*fps), stepf):
            cap2 = cv2.VideoCapture(src); cap2.set(cv2.CAP_PROP_POS_FRAMES, fi)
            r, f = cap2.read(); cap2.release()
            if r: fs.append(f)
        if fs:
            grid(fs, 4, 480, 270, os.path.join(frames_dir, "trans_T%d_%.1f-%.1fs.png" % (i, a2, b2)))

    json.dump({"meta": meta, "per_second_metrics": metrics},
              open(os.path.join(out, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("DONE ->", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "video-teardown")
