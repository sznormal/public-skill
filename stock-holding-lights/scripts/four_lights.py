#!/usr/bin/env python3
"""
个股持仓四灯信号监控工具 v1.0
吸取 etf-three-lights 分层架构 + 多维数据 + 操作语义

用法1：传入已查询的数据
  python four_lights.py --data holdings_data.json

用法2：指定持仓列表（脚本自动调用neodata查询）
  python four_lights.py --holdings "300059:17.22:金融,600276:50:医药,603605:0:消费"

参数格式：代码:止损价:持仓类型
持仓类型：金融/医药/消费/科技/周期/港股
"""

import sys
import glob
import json
import os
import subprocess

# ============================================================
# 配置
# ============================================================

def _wb_home(*parts):
    """WorkBuddy 用户目录，按本机 HOME 推导，不写死用户名。"""
    return os.path.join(os.path.expanduser("~"), ".workbuddy", *parts)


# neodata 脚本路径候选列表（按本机 ~/.workbuddy 自动发现 + 环境变量覆盖）
NEODATA_SCRIPT_PATHS = [
    os.environ.get("NEODATA_SCRIPT", ""),
    *sorted(glob.glob(_wb_home("plugins", "**", "neodata-financial-search", "scripts", "query.py"), recursive=True)),
    *sorted(glob.glob(_wb_home("resources", "builtin-skills", "neodata-financial-search", "scripts", "query.py"))),
    "D:/workbudy/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/neodata-financial-search/scripts/query.py",
]

# Python 路径候选列表（按本机 ~/.workbuddy 自动发现版本）
PYTHON_PATHS = [
    os.environ.get("PYTHON_BIN", ""),
    *sorted(glob.glob(_wb_home("binaries", "python", "versions", "*", "python.exe")), reverse=True),
    *sorted(glob.glob(_wb_home("binaries", "python", "envs", "*", "Scripts", "python.exe")), reverse=True),
    "D:/miniconda/python.exe",
]

# 持仓类型对应的板块指数配置
MARKET_INDEX_CONFIG = {
    "金融": {
        "indices": ["上证", "证券板块"],
        "extra_relief": None,
    },
    "医药": {
        "indices": ["上证", "医药板块"],
        "extra_relief": None,
    },
    "消费": {
        "indices": ["上证", "消费板块"],
        "extra_relief": None,
    },
    "科技": {
        "indices": ["上证", "创业板", "科创50"],
        "extra_relief": {"name": "科创50", "condition": "连续3日无单日跌幅>3%"},
    },
    "周期": {
        "indices": ["上证", "资源板块"],
        "extra_relief": None,
    },
    "港股": {
        "indices": ["上证", "创业板"],
        "extra_relief": None,
    },
}


def find_python():
    """查找可用的 Python 路径"""
    for path in PYTHON_PATHS:
        if os.path.exists(path):
            return path
    return sys.executable


def find_neodata_script():
    """查找 neodata 查询脚本路径"""
    for path in NEODATA_SCRIPT_PATHS:
        if os.path.exists(path):
            return path
    return None


def query_neodata(query, python_path=None, script_path=None):
    """调用 neodata 查询数据"""
    if python_path is None:
        python_path = find_python()
    if script_path is None:
        script_path = find_neodata_script()
    if script_path is None:
        return {"error": "neodata 脚本未找到"}

    try:
        result = subprocess.run(
            [python_path, script_path, "--query", query],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return {"error": result.stderr[:500]}
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# 第一灯：资金灯（任一触发）
# ============================================================

def judge_capital_light(data):
    """资金灯判定：主力资金3日净流向+委比+量比"""
    main_flow_3d = data.get("main_flow_3d", 0)
    bid_ratio = data.get("bid_ratio", 0)
    volume_ratio = data.get("volume_ratio", 1)
    sector_3d_underperform = data.get("sector_3d_underperform", 0)
    main_flow_today = data.get("main_flow_today", 0)
    dist_to_stop = data.get("dist_to_stop", 100)

    # 红灯（任一）
    red_reasons = []
    if main_flow_3d < -50000000:  # 3日累计流出>5000万
        red_reasons.append(f"主力3日累计流出{main_flow_3d/10000:.0f}万")
    if bid_ratio < -50 and volume_ratio > 1.5:
        red_reasons.append(f"委比{bid_ratio:.1f}%+量比{volume_ratio:.2f}放量偏卖")
    if sector_3d_underperform > 5:
        red_reasons.append(f"板块3日跑输大盘{sector_3d_underperform:.1f}pct")
    if red_reasons:
        return {"status": "红", "reason": "；".join(red_reasons),
                "main_flow_3d": main_flow_3d, "bid_ratio": bid_ratio, "volume_ratio": volume_ratio}

    # 黄灯（任一）
    yellow_reasons = []
    if main_flow_today < -10000000:  # 单日流出>1000万
        yellow_reasons.append(f"主力单日流出{main_flow_today/10000:.0f}万")
    if bid_ratio < -30 and volume_ratio < 1:
        yellow_reasons.append(f"委比{bid_ratio:.1f}%缩量偏卖")
    if dist_to_stop < 10:
        yellow_reasons.append(f"距止损线仅{dist_to_stop:.1f}%")
    if yellow_reasons:
        return {"status": "黄", "reason": "；".join(yellow_reasons),
                "main_flow_3d": main_flow_3d, "bid_ratio": bid_ratio, "volume_ratio": volume_ratio}

    # 绿灯（全部）
    if main_flow_3d >= 0 and bid_ratio > 0 and volume_ratio < 1:
        return {"status": "绿", "reason": f"主力3日净流入{main_flow_3d/10000:.0f}万，委比{bid_ratio:.1f}%偏买缩量",
                "main_flow_3d": main_flow_3d, "bid_ratio": bid_ratio, "volume_ratio": volume_ratio}

    # 蓝灯（全部）
    main_flow_2d_positive = data.get("main_flow_2d_positive", False)
    if main_flow_2d_positive and bid_ratio > 50 and volume_ratio > 1.0:
        return {"status": "蓝", "reason": f"主力连续2日净流入，委比{bid_ratio:.1f}%强烈偏买",
                "main_flow_3d": main_flow_3d, "bid_ratio": bid_ratio, "volume_ratio": volume_ratio}

    # 默认黄灯（信号不明确）
    return {"status": "黄", "reason": "资金信号不明确",
            "main_flow_3d": main_flow_3d, "bid_ratio": bid_ratio, "volume_ratio": volume_ratio}


# ============================================================
# 第二灯：估值灯（全量判定）
# ============================================================

def judge_valuation_light(data):
    """估值灯判定：PE/PB 5年分位+ROE+安全边际"""
    pe_percentile = data.get("pe_percentile", 50)
    pb_percentile = data.get("pb_percentile", 50)
    roe = data.get("roe", 0)
    safety_margin = data.get("safety_margin", 0)

    # 红灯
    if pe_percentile > 90:
        return {"status": "红", "reason": f"PE 5年分位{pe_percentile:.1f}%极度高估",
                "pe_percentile": pe_percentile, "pb_percentile": pb_percentile, "roe": roe}

    # 黄灯
    if pe_percentile > 75:
        return {"status": "黄", "reason": f"PE 5年分位{pe_percentile:.1f}%偏贵",
                "pe_percentile": pe_percentile, "pb_percentile": pb_percentile, "roe": roe}

    # 绿灯（全部）
    if 25 <= pe_percentile <= 75 and roe > 15:
        return {"status": "绿", "reason": f"PE分位{pe_percentile:.1f}%合理，ROE {roe:.1f}%达标",
                "pe_percentile": pe_percentile, "pb_percentile": pb_percentile, "roe": roe}

    # 蓝灯（全部）
    if pe_percentile < 10 and roe > 20 and safety_margin > 30:
        return {"status": "蓝", "reason": f"PE分位{pe_percentile:.1f}%极低估，ROE {roe:.1f}%，安全边际{safety_margin:.0f}%",
                "pe_percentile": pe_percentile, "pb_percentile": pb_percentile, "roe": roe, "safety_margin": safety_margin}

    # PE低但ROE不达标 → 黄灯
    if pe_percentile < 25:
        return {"status": "黄", "reason": f"PE分位{pe_percentile:.1f}%偏低但ROE {roe:.1f}%未达标",
                "pe_percentile": pe_percentile, "pb_percentile": pb_percentile, "roe": roe}

    return {"status": "黄", "reason": "估值信号不明确",
            "pe_percentile": pe_percentile, "pb_percentile": pb_percentile, "roe": roe}


# ============================================================
# 第三灯：技术灯（混合触发）
# ============================================================

def judge_technical_light(data):
    """技术灯判定：MA20方向+RSI+距止损线"""
    ma20_direction = data.get("ma20_direction", "unknown")
    price_above_ma20 = data.get("price_above_ma20", False)
    rsi = data.get("rsi", 50)
    dist_to_stop = data.get("dist_to_stop", 100)
    ma5_cross_ma10 = data.get("ma5_cross_ma10", False)
    volume_support = data.get("volume_support", False)

    # 红灯（任一）
    red_reasons = []
    if dist_to_stop <= 0:
        red_reasons.append("已跌破止损线")
    if ma20_direction == "down" and not price_above_ma20:
        red_reasons.append("MA20向下且收盘在下方")
    if red_reasons:
        return {"status": "红", "reason": "；".join(red_reasons),
                "ma20_direction": ma20_direction, "rsi": rsi, "dist_to_stop": dist_to_stop}

    # 黄灯（任一）
    yellow_reasons = []
    if rsi < 30 or rsi > 70:
        yellow_reasons.append(f"RSI {rsi:.1f}超卖或超买")
    if dist_to_stop < 5:
        yellow_reasons.append(f"距止损线仅{dist_to_stop:.1f}%")
    if ma20_direction == "flat" and not price_above_ma20:
        yellow_reasons.append("MA20走平且价格在下方")
    if yellow_reasons:
        return {"status": "黄", "reason": "；".join(yellow_reasons),
                "ma20_direction": ma20_direction, "rsi": rsi, "dist_to_stop": dist_to_stop}

    # 绿灯（全部）
    if ma20_direction == "up" and price_above_ma20 and 40 <= rsi <= 60:
        return {"status": "绿", "reason": f"MA20向上，收盘在上方，RSI {rsi:.1f}正常",
                "ma20_direction": ma20_direction, "rsi": rsi, "dist_to_stop": dist_to_stop}

    # 蓝灯（全部）
    if 30 <= rsi <= 40 and ma5_cross_ma10 and volume_support:
        return {"status": "蓝", "reason": f"RSI {rsi:.1f}超卖回升+MA5金叉MA10+量能配合",
                "ma20_direction": ma20_direction, "rsi": rsi, "dist_to_stop": dist_to_stop}

    return {"status": "黄", "reason": "技术信号不明确",
            "ma20_direction": ma20_direction, "rsi": rsi, "dist_to_stop": dist_to_stop}


# ============================================================
# 第四灯：市场环境灯（分流检查+计时器）
# ============================================================

def judge_market_light(holding_type, market_data):
    """市场环境灯判定：按持仓类型分流检查"""
    config = MARKET_INDEX_CONFIG.get(holding_type, MARKET_INDEX_CONFIG["金融"])

    if not config["indices"]:
        return {"status": "N/A", "reason": "不适用第四灯", "applicable": False}

    index_results = market_data.get("index_results", [])
    has_red = False
    has_yellow = False

    for idx in index_results:
        if idx.get("status") == "红":
            has_red = True
        elif idx.get("status") == "黄":
            has_yellow = True

    if has_red:
        overall = "红"
        reason = "存在红色触发的指数"
    elif has_yellow:
        overall = "黄"
        reason = "存在黄色触发的指数"
    else:
        overall = "绿"
        reason = "所有检查指数均正常"

    # 红灯时计算解除进度
    relief = None
    if overall == "红":
        relief = {
            "条件1_上证3日>=MA120": market_data.get("sh_above_ma120_3d", {"progress": "0/3", "achieved": False}),
            "条件2_创业板3日无暴跌": market_data.get("cyb_no_crash_3d", {"progress": "0/3", "achieved": False}),
            "条件3_主力3日净流入": market_data.get("main_inflow_3d", {"progress": "需查询确认", "achieved": False}),
        }
        if config.get("extra_relief"):
            relief["条件4_科创50_3日无暴跌"] = market_data.get("kc50_no_crash_3d", {"progress": "0/3", "achieved": False})

    return {
        "status": overall,
        "reason": reason,
        "applicable": True,
        "holding_type": holding_type,
        "index_details": index_results,
        "relief_progress": relief,
    }


# ============================================================
# 综合分析
# ============================================================

LIGHT_PRIORITY = {"红": 0, "黄": 1, "绿": 2, "蓝": 3}
LIGHT_NAMES = {"红": "红灯", "黄": "黄灯", "绿": "绿灯", "蓝": "蓝灯"}


def analyze_holding(code, name, stop_loss, holding_type, stock_data, market_data):
    """分析单只持仓的四灯状态"""
    stock_data["dist_to_stop"] = ((stock_data.get("price", 0) - stop_loss) / stock_data["price"] * 100) if stop_loss > 0 and stock_data.get("price", 0) > 0 else 100

    capital = judge_capital_light(stock_data)
    valuation = judge_valuation_light(stock_data)
    technical = judge_technical_light(stock_data)
    market = judge_market_light(holding_type, market_data)

    lights = [capital["status"], valuation["status"], technical["status"]]
    market_status = market["status"]

    # 绿灯计数（绿+蓝都算正面信号，N/A不算）
    green_count = sum(1 for s in lights if s in ("绿", "蓝"))
    if market_status in ("绿", "蓝"):
        green_count += 1

    # 冲突规则：就高不就低（仅前三灯参与，第四灯是计时器不参与冲突判定）
    conflict_light = min(lights, key=lambda x: LIGHT_PRIORITY.get(x, 1)) if lights else "黄"

    # 分级建议
    if conflict_light == "红":
        advice = "红灯：立即减仓，卖涨不卖跌"
    elif conflict_light == "黄":
        advice = "黄灯：不操作，密切监控"
    elif conflict_light == "绿":
        if green_count == 4:
            advice = "四灯全绿：可考虑加仓/持有"
        elif green_count == 3:
            advice = "三灯绿：继续持有，观望"
        elif green_count == 2:
            advice = "两灯绿：谨慎持有"
        else:
            advice = "绿灯但亮灯不足：观望"
    elif conflict_light == "蓝":
        advice = "蓝灯：可分批建仓，3-4笔，每笔间隔2-3日"
    else:
        advice = "信号不明确，观望"

    # 第四灯计时器提醒
    if market_status == "红":
        advice += " | 第四灯红灯：禁止新建仓（卖出不受限），只微调时机±1-2天"
    elif market_status == "黄":
        advice += " | 第四灯黄灯：市场偏弱，谨慎操作"

    return {
        "code": code,
        "name": name,
        "holding_type": holding_type,
        "latest_price": stock_data.get("price", 0),
        "stop_loss_price": stop_loss,
        "capital_light": capital,
        "valuation_light": valuation,
        "technical_light": technical,
        "market_light": market,
        "green_count": green_count,
        "conflict_light": LIGHT_NAMES.get(conflict_light, conflict_light),
        "advice": advice,
    }


# ============================================================
# 主函数
# ============================================================

def parse_holdings(holdings_str):
    """解析持仓参数：代码:止损价:类型"""
    holdings = []
    for item in holdings_str.split(","):
        parts = item.strip().split(":")
        if len(parts) >= 3:
            code = parts[0].strip()
            stop_loss = float(parts[1])
            holding_type = parts[2].strip()
            holdings.append({"code": code, "stop_loss": stop_loss, "holding_type": holding_type})
    return holdings


def main():
    import argparse
    parser = argparse.ArgumentParser(description="个股持仓四灯信号监控工具")
    parser.add_argument("--data", help="已查询的持仓数据JSON文件路径")
    parser.add_argument("--holdings", help='持仓列表，格式：代码:止损价:类型，如 "300059:17.22:金融,600276:50:医药"')
    args = parser.parse_args()

    if args.data:
        # 从JSON文件加载数据
        with open(args.data, "r", encoding="utf-8") as f:
            all_data = json.load(f)
        results = []
        for h in all_data.get("holdings", []):
            result = analyze_holding(
                h["code"], h.get("name", ""), h.get("stop_loss", 0),
                h.get("holding_type", "金融"), h.get("stock_data", {}), h.get("market_data", {})
            )
            results.append(result)
        print(json.dumps(results, ensure_ascii=False, indent=2))
    elif args.holdings:
        # 解析持仓列表
        holdings = parse_holdings(args.holdings)
        python_path = find_python()
        script_path = find_neodata_script()

        if not script_path:
            print(json.dumps({"error": "未找到 neodata 查询脚本，请确认 skill 已安装"}, ensure_ascii=False))
            sys.exit(1)

        results = []
        for h in holdings:
            # 查询每只股票的数据
            query = f'{h["code"]}今日实时行情价格涨跌幅主力资金净流向委比量比PE估值PB ROE'
            raw = query_neodata(query, python_path, script_path)

            # 构造stock_data（简化版，实际需要从neodata返回中解析）
            stock_data = {
                "price": 0, "main_flow_3d": 0, "bid_ratio": 0,
                "volume_ratio": 1, "pe_percentile": 50, "roe": 10,
                "rsi": 50, "ma20_direction": "unknown",
                "price_above_ma20": False,
            }
            market_data = {"index_results": []}

            result = analyze_holding(h["code"], "", h["stop_loss"], h["holding_type"], stock_data, market_data)
            result["_neodata_raw"] = raw[:500] if isinstance(raw, str) else str(raw)[:500]
            results.append(result)

        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({
            "error": "请传入 --data 或 --holdings 参数",
            "usage": 'python four_lights.py --holdings "300059:17.22:金融,600276:50:医药,603605:0:消费"',
            "usage2": "python four_lights.py --data holdings_data.json"
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
