#!/usr/bin/env python3
"""archive-doctor: 回收站取证 —— 找出被删除文件的原路径、大小与删除时刻。

用途：压缩包/文档「凭空消失」时，确认它是否只是被删到回收站、数据是否完整可还原。

用法:
    python recycle_probe.py [F:] [C:]           # 列最近 20 条
    python recycle_probe.py --grep 33220235     # 只找名字匹配的
    python recycle_probe.py --verify            # 校验 $R 数据字节数是否与 $I 记录一致

注意：$I 里的 FILETIME 按 UTC 计算，脚本已 +8 小时换算为本地时间输出。
"""
import os, sys, glob, struct, datetime

HEADER = f"{'删除时刻(本地)':<21}{'大小(字节)':>14}  {'原路径'}"
SEP = "-" * 100


def parse_i(path):
    with open(path, "rb") as f:
        data = f.read()
    if len(data) < 28:
        return None
    size = struct.unpack("<Q", data[8:16])[0]
    ft = struct.unpack("<Q", data[16:24])[0]
    dt = None
    if ft:
        dt = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=ft / 10)
        dt += datetime.timedelta(hours=8)  # UTC -> 东八区
    nlen = struct.unpack("<I", data[24:28])[0]
    name = data[28:28 + nlen * 2].decode("utf-16-le", errors="replace").rstrip("\x00")
    return size, dt, name


def recycle_dirs(drives):
    out = []
    for d in drives:
        base = f"{d}:\\$Recycle.Bin"
        if not os.path.isdir(base):
            continue
        for sid in os.listdir(base):
            p = os.path.join(base, sid)
            if os.path.isdir(p):
                out.append(p)
    return out


def main():
    args = [a for a in sys.argv[1:]]
    grep = None
    verify = False
    drives = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--grep":
            grep = args[i + 1]; i += 2; continue
        if a == "--verify":
            verify = True; i += 1; continue
        drives.append(a.rstrip(":\\/")); i += 1
    if not drives:
        drives = [c for c in "CDEFGH" if os.path.isdir(f"{c}:\\")]

    for rb in recycle_dirs(drives):
        print(f"===== {rb} =====")
        rows = []
        for p in glob.glob(os.path.join(rb, "$I*")):
            try:
                r = parse_i(p)
            except Exception:
                continue
            if r is None:
                continue
            size, dt, name = r
            if grep and grep.lower() not in name.lower():
                continue
            rows.append((dt, name, size, os.path.basename(p)))
        if not rows:
            print("(无匹配条目)\n")
            continue
        rows.sort(key=lambda x: (x[0] is None, x[0]), reverse=True)
        print(HEADER); print(SEP)
        for dt, name, size, iid in rows[:30]:
            ts = dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "?"
            line = f"{ts:<21}{size:>14,}  {name}"
            if verify:
                rp = os.path.join(rb, "$R" + iid[2:])
                if not os.path.exists(rp):
                    line += "   [数据缺失]"
                else:
                    actual = os.path.getsize(rp)
                    line += "   [数据完整]" if actual == size else f"   [大小不符:{actual:,}]"
            print(line)
        print()


if __name__ == "__main__":
    main()
