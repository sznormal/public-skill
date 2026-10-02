#!/usr/bin/env python
"""视频风格拉片 — 第3步：音频探针 + 本地转写（无 ffmpeg / 走 hf-mirror）。
用法:
  python asr_transcribe.py "<视频路径>" [模型目录]
模型目录省略时自动下载 Systran/faster-whisper-small（走 hf-mirror，禁用 xet）。
产物: 频谱诊断 JSON + 判决（旁白 or 纯音乐垫）+ asr_segments.json
"""
import os, sys, json, glob, shutil, wave
import numpy as np

os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
os.environ.setdefault("HF_HUB_DISABLE_XET", "1")        # 关键：禁用 xet 传输，否则 401
os.environ.setdefault("HF_HUB_ENABLE_HF_TRANSFER", "0")
import av
from numpy.fft import rfft, rfftfreq

def load_audio(src):
    c = av.open(src)
    st = [s for s in c.streams if s.type == "audio"]
    if not st:
        c.close(); return None, None
    sr = st[0].sample_rate
    buf = [fr.to_ndarray() for fr in c.decode(audio=0)]
    c.close()
    a = np.concatenate(buf, axis=1).astype(np.float32)
    a = a.mean(axis=0) if a.shape[0] > 1 else a[0]
    return a, sr

def probe(a, sr):
    win, hop = int(sr*0.04), int(sr*0.01)
    cents = []; bl = bm = bh = 0; env = []
    for i in range(0, len(a)-win, hop):
        seg = a[i:i+win]*np.hanning(win)
        S = np.abs(rfft(seg)); f = rfftfreq(win, 1/sr)
        if S.sum() < 1e-6: continue
        cents.append(float((f*S).sum()/S.sum()))
        bl += float(S[f < 300].sum()); bm += float(S[(f >= 300) & (f < 3400)].sum())
        bh += float(S[f >= 3400].sum()); env.append(float(np.sqrt(np.mean(seg**2))))
    env = np.array(env); tot = bl + bm + bh + 1e-9
    sylratio = None
    if len(env) > 20:
        e2 = env - env.mean()
        Ms = np.abs(rfft(e2*np.hanning(len(e2)))); mf = rfftfreq(len(e2), hop/sr)
        sylratio = float(Ms[(mf >= 2) & (mf <= 8)].sum() / (Ms[mf > 0.3].sum() + 1e-9))
    return {"spectral_centroid_Hz": round(float(np.mean(cents)), 1),
            "low_<300_pct": round(100*bl/tot, 1), "mid_300-3400_pct": round(100*bm/tot, 1),
            "high_>3400_pct": round(100*bh/tot, 1),
            "syllable_mod_2-8Hz_ratio": round(sylratio, 3) if sylratio else None,
            "env_range_dB": round(float(20*np.log10((np.percentile(env, 95)+1e-9)/(np.percentile(env, 5)+1e-9))), 1)}

def ensure_model(dst):
    if dst and os.path.isdir(dst) and os.path.exists(os.path.join(dst, "model.bin")):
        return dst
    from huggingface_hub import snapshot_download
    base = snapshot_download("Systran/faster-whisper-small")
    dst = dst or os.path.join(os.path.dirname(base), "fw-small-local")
    os.makedirs(dst, exist_ok=True)
    snap = base
    for f in ["model.bin", "config.json", "tokenizer.json", "vocabulary.txt"]:
        s = os.path.join(snap, f)
        if os.path.exists(s) and os.path.getsize(s) > 0:
            shutil.copyfile(s, os.path.join(dst, f))
    need = [f for f in ["model.bin", "config.json", "tokenizer.json", "vocabulary.txt"]
            if not (os.path.exists(os.path.join(dst, f)) and os.path.getsize(os.path.join(dst, f)) > 0)]
    if need:
        # Windows 符号链接失败：snapshot 里是 0 字节，从 blobs/ 按大小认领
        hub = os.path.join(os.path.expanduser("~/.cache/huggingface/hub"),
                           "models--Systran--faster-whisper-small")
        blobs = sorted(glob.glob(os.path.join(hub, "blobs", "*")), key=os.path.getsize, reverse=True)
        blobs = [b for b in blobs if os.path.getsize(b) > 100]
        order = ["model.bin", "tokenizer.json", "vocabulary.txt", "config.json"]  # 由大到小
        for i, f in enumerate(order):
            if f in need and i < len(blobs):
                shutil.copyfile(blobs[i], os.path.join(dst, f))
    return dst

def main():
    src = sys.argv[1]; model_dir = sys.argv[2] if len(sys.argv) > 2 else None
    a, sr = load_audio(src)
    if a is None:
        print("NO_AUDIO_STREAM -> 纯视觉/文字驱动"); return
    rms = float(np.sqrt(np.mean(a**2))); peak = float(np.abs(a).max())
    print("AUDIO rms=%.6f peak=%.4f dBFS=%.1f dur=%.2fs" % (rms, peak, 20*np.log10(rms+1e-12), len(a)/sr))
    diag = probe(a, sr)
    print("PROBE", json.dumps(diag))
    silent = rms < 1e-4
    verdict = ("静音" if silent else
               "音乐/氛围垫，无旁白" if (diag["low_<300_pct"] > 60 and (diag["syllable_mod_2-8Hz_ratio"] or 1) < 0.3)
               else "可能有语音，见转写")
    print("VERDICT:", verdict)

    # 归一化后写 wav，提高识别率
    ref = os.path.join(os.path.dirname(os.path.abspath(src)), "audio_norm.wav")
    with wave.open(ref, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(((a/(peak+1e-9)*0.9)*32767).astype(np.int16).tobytes())

    from faster_whisper import WhisperModel
    md = ensure_model(model_dir)
    m = WhisperModel(md, device="cpu", compute_type="int8", local_files_only=True)
    seg, info = m.transcribe(ref, language=None, beam_size=5, vad_filter=True)
    segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in seg]
    print("lang:", info.language, round(info.language_probability, 3))
    for s in segs: print("  [%.2f-%.2f] %s" % (s["start"], s["end"], s["text"]))
    print("SEGMENTS:", len(segs), "->", "无有效语音（确认为音乐垫）" if not segs else "有旁白")
    json.dump({"probe": diag, "verdict": verdict, "segments": segs},
              open("asr_segments.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
