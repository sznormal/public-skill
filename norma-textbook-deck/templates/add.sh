#!/bin/bash
# norma-textbook-deck · 单页闭环脚本：lint -> 提交
# 用法：cd chN_ppt && bash add.sh slide-NN.xml
# 依赖：环境变量或直接改下面三个路径

export PATH="/usr/bin:/bin:/usr/local/bin:$PATH"

PY="C:/Users/admin/.workbuddy/binaries/python/versions/3.13.12/python.exe"
LINT="C:/Users/admin/.workbuddy/connectors/skills/connector-feishu/lark-slides/scripts/xml_lint.py"
# 改成当前 deck 的 xml_presentation_id
PRES="${PRES:-Te2JsP5ymlbz7Hdp33vcvLIEnPf}"

F="$1"
if [ -z "$F" ]; then echo "usage: bash add.sh slide-NN.xml"; exit 1; fi

# 1) lint
"$PY" "$LINT" --input "$F" > ".lint.tmp.json" 2>&1
EC=$("$PY" -c "import json;d=json.load(open('.lint.tmp.json',encoding='utf8'));print(d['summary']['error_count'])")
WC=$("$PY" -c "import json;d=json.load(open('.lint.tmp.json',encoding='utf8'));print(d['summary']['warning_count'])")
echo "[lint] $F errors=$EC warnings=$WC"

if [ "$EC" != "0" ]; then
  echo "[abort] lint error_count != 0, 未提交。详情："
  "$PY" -c "import json;d=json.load(open('.lint.tmp.json',encoding='utf8'));print(json.dumps(d.get('slides',[])[0].get('issues',[]),ensure_ascii=False,indent=2))" 2>/dev/null
  exit 1
fi

# 2) submit
lark-cli slides +add-slide --as user --presentation "$PRES" --slide "@$F" 2>&1 | tail -12
