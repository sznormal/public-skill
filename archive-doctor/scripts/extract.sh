#!/bin/bash
# archive-doctor: 用已知密码批量解压 + 逐包校验
# 用法: bash extract.sh <目录> <密码> [ID...] [--out <输出目录>]
#   例:  bash extract.sh /f/download 'PASSWORD' 33220235 30667467
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Program Files/7-Zip:$PATH"
SZ="/c/Program Files/7-Zip/7z"
DIR="${1:?用法: extract.sh <目录> <密码> [ID...] [--out <输出目录>]}"
PW="${2:?缺少密码}"
shift 2

OUT=""
if [ "$1" = "--out" ]; then OUT="$2"; shift 2; fi

WIN_DIR=$(cygpath -w "$DIR" 2>/dev/null) || WIN_DIR="$DIR"
case "$WIN_DIR" in *\\) WIN_DIR="${WIN_DIR%\\}" ;; esac
PF_DIR=$(cygpath -u "$WIN_DIR" 2>/dev/null) || PF_DIR="$DIR"

ok=0; bad=0; failed=""

expand() {
  local base="$1"
  local src="$PF_DIR/$base"
  if [ ! -f "$src" ]; then echo "[SKIP] $base 不存在"; bad=$((bad+1)); failed="$failed $base"; return; fi

  local wsrc="$WIN_DIR\\$base"
  local wdst
  if [ -n "$OUT" ]; then wdst=$(cygpath -w "$OUT" 2>/dev/null || echo "$OUT")
  else wdst="$WIN_DIR\\${base%.*}"; fi
  case "$wdst" in *\\) wdst="${wdst%\\}" ;; esac
  mkdir -p "$wdst" 2>/dev/null

  "$SZ" x -y -p"$PW" "$wsrc" -o"$wdst" >/dev/null 2>&1 </dev/null
  local rc=$?
  if [ $rc -eq 0 ]; then
    local n
    n=$(find "$wdst" -type f 2>/dev/null | wc -l)
    echo "[OK]   $base -> $wdst  ($n 个文件)"
    ok=$((ok+1))
  else
    echo "[FAIL] $base  (退出码 $rc：2=密码错误/参数错, 255=致命错误)"
    bad=$((bad+1)); failed="$failed $base"
  fi
}

if [ $# -gt 0 ]; then
  for id in "$@"; do expand "$id.rar"; done
else
  for f in "$PF_DIR"/*.rar; do
    [ -f "$f" ] || continue
    expand "$(basename "$f")"
  done
fi

echo "---- 成功 $ok / 失败 $bad ----"
[ -n "$failed" ] && echo "失败列表:$failed"
[ $bad -gt 0 ] && exit 1
exit 0
