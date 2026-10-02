#!/bin/bash
# archive-doctor: 批量诊断压缩包是「损坏」还是「加密」
# 用法: bash diagnose.sh <目录> [ID...]
#   目录可用 POSIX(/f/download) 或 Windows(F:\download) 形式，脚本内部用 cygpath 归一化
export PATH="/usr/bin:/bin:/c/Windows/System32:/c/Program Files/7-Zip:$PATH"
SZ="/c/Program Files/7-Zip/7z"
DIR="${1:?用法: diagnose.sh <目录> [ID...]}"
shift
LOG="${TMPDIR:-/tmp}/archive-doctor-diag.log"
TLOG="${TMPDIR:-/tmp}/archive-doctor-t.log"
: > "$LOG"

# 关键：Git Bash 会把 F:\download 这类参数改写成 F://download，必须用 cygpath 归一化
WIN_DIR=$(cygpath -w "$DIR" 2>/dev/null) || WIN_DIR="$DIR"
case "$WIN_DIR" in *\\) WIN_DIR="${WIN_DIR%\\}" ;; esac

sniff() { od -A n -t x1 -N 8 "$1" 2>/dev/null | tr -d ' \n'; }

report() {
  local id="$1"
  local WF="$WIN_DIR\\$id"
  local PF
  PF=$(cygpath -u "$WF" 2>/dev/null) || PF="$WF"

  echo "================================================" >> "$LOG"
  echo "FILE: $WF" >> "$LOG"

  # ① 先确认文件真的存在 —— 绝不能把「找不到文件」报告成「损坏」
  if [ ! -e "$PF" ]; then
    echo "VERDICT: [MISSING] 文件不存在（已删除/已移动/盘符未挂载）—— 先去回收站或原路径找回，不要谈修复" >> "$LOG"
    echo "VERDICT: [MISSING] $WF"
    return
  fi

  # ② 文件头判型
  local hdr
  hdr=$(sniff "$PF")
  case "$hdr" in
    526172211a070100) echo "FORMAT: RAR5" >> "$LOG" ;;
    526172211a0700)   echo "FORMAT: RAR4" >> "$LOG" ;;
    504b0304*)        echo "FORMAT: ZIP"  >> "$LOG" ;;
    377abcaf271c*)    echo "FORMAT: 7Z"   >> "$LOG" ;;
    *)                echo "FORMAT: UNKNOWN (hdr=${hdr:-空})" >> "$LOG" ;;
  esac

  # ③ 实测：区分损坏 / 加密
  : > "$TLOG"
  "$SZ" t "$WF" > "$TLOG" 2>&1 </dev/null
  local rc=$?
  cat "$TLOG" >> "$LOG"

  local v
  if [ $rc -eq 0 ]; then
    v="[OK] 未加密或密码已知，可正常解压"
  elif grep -qi "wrong password\|Enter password\|password" "$TLOG"; then
    v="[ENCRYPTED] 加密，缺密码 —— 不是损坏，修复无意义"
  elif grep -qi "CRC\|Data Error\|Data error\|Unexpected end" "$TLOG"; then
    v="[DAMAGED] 出现 CRC/数据错误 —— 这个才需要谈修复"
  else
    v="[UNKNOWN] 退出码 $rc，未匹配已知特征，需人工看日志"
  fi
  echo "VERDICT: $v" >> "$LOG"
  echo "VERDICT: $v  <-  $WF"

  # ④ 列内容（含注释区，常藏发布者线索）
  "$SZ" l -slt "$WF" >> "$LOG" 2>&1 </dev/null
}

if [ $# -gt 0 ]; then
  for id in "$@"; do report "$id.rar"; done
else
  PF_DIR=$(cygpath -u "$WIN_DIR" 2>/dev/null) || PF_DIR="$DIR"
  found=0
  for f in "$PF_DIR"/*.rar "$PF_DIR"/*.zip; do
    [ -f "$f" ] || continue
    found=1
    report "$(basename "$f")"
  done
  [ $found -eq 0 ] && echo "目录内未找到 rar/zip: $WIN_DIR"
fi

echo "---- 明细日志: $LOG ----"
