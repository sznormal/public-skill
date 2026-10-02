#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract text from legacy Word .doc (OLE2 binary) files via the piece table.
Pure-python, depends only on `olefile`. UTF-16 / CP1252 pieces handled.
"""
import olefile
import struct
import sys


def _u16(b, o):
    return struct.unpack_from("<H", b, o)[0]


def _u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def doc_to_text(path):
    ole = olefile.OleFileIO(path)
    if not ole.exists("WordDocument"):
        raise RuntimeError("No WordDocument stream (not a Word .doc?)")
    word = ole.openstream("WordDocument").read()

    # FIB offsets (standard Word Binary Format)
    # fcMin at 0x18 ; ccpText at 0x4C ; fcClx at 0x01A2 ; lcbClx at 0x01A6
    fc_min = _u32(word, 0x18)
    ccp_text = _u32(word, 0x4C)
    fc_clx = _u32(word, 0x01A2)
    lcb_clx = _u32(word, 0x01A6)

    # fWhichTblStm at 0x0A bit 0x01 -> 1Table else 0Table
    flags = word[0x0A]
    tbl_name = "1Table" if (flags & 0x01) else "0Table"
    if not ole.exists(tbl_name):
        tbl_name = "0Table" if tbl_name == "1Table" else "1Table"
    table = ole.openstream(tbl_name).read()

    clx = table[fc_clx: fc_clx + lcb_clx]

    # Walk CLX: optional Prc(0x01) entries then a single Pcdt(0x02)
    pos = 0
    pcdt = None
    while pos < len(clx):
        tag = clx[pos]
        if tag == 0x02:
            lcb = _u32(clx, pos + 1)
            pcdt = clx[pos + 5: pos + 5 + lcb]
            break
        elif tag == 0x01:
            cb = _u16(clx, pos + 1)
            pos += 3 + cb
        else:
            break

    if pcdt is None:
        raise RuntimeError("Pcdt not found in CLX")

    n = (len(pcdt) - 4) // 8  # number of pieces
    cp_fmt = "<" + ("I" * (n + 1))
    cps = struct.unpack_from(cp_fmt, pcdt, 0)
    pcd_base = 4 * (n + 1)  # CP array (n+1 x 4B) then PCD array (n x 8B)

    out = []
    for i in range(n):
        pcd = pcdt[pcd_base + i * 8: pcd_base + i * 8 + 8]
        fc = _u32(pcd, 2)
        f_compressed = bool(fc & 0x40000000)
        fc_off = fc & 0x3FFFFFFF
        if f_compressed:
            start = fc_off >> 1
            length = cps[i + 1] - cps[i]  # 1 byte per char
            chunk = word[start: start + length]
            try:
                out.append(chunk.decode("cp1252", "replace"))
            except Exception:
                out.append(chunk.decode("latin-1", "replace"))
        else:
            start = fc_off
            length = (cps[i + 1] - cps[i]) * 2  # 2 bytes per char
            chunk = word[start: start + length]
            out.append(chunk.decode("utf-16-le", "replace"))

    ole.close()
    return "".join(out)


if __name__ == "__main__":
    print(doc_to_text(sys.argv[1]))
