#!/usr/bin/env python3
"""
四盏灯ETF趋势判断工具 v6.0
数据源：新浪财经（ETF K线）+ 东方财富（指数K线）
v6.0 新增：量价四象限 / 滚动累计跌幅 / ADX趋势强度 / 金叉确认期 / 条件3改进
"""
# pylint: disable=all

import sys
import json
from coze_workload_identity import requests

# ============================================================
# ETF类型注册表
# ============================================================
ETF_TYPE_REGISTRY = {
    # A股科技
    "159599": "A股科技", "159516": "A股科技", "159530": "A股科技",
    "159801": "A股科技", "512480": "A股科技", "512760": "A股科技",
    "515050": "A股科技", "515790": "A股科技", "516160": "A股科技",
    "588000": "A股科技", "588200": "A股科技", "159995": "A股科技",
    "515000": "A股科技", "159825": "A股科技", "562500": "A股科技",
    # A股宽基
    "510300": "A股宽基", "510050": "A股宽基", "510500": "A股宽基",
    "159919": "A股宽基", "512100": "A股宽基",
    "159901": "A股宽基", "510310": "A股宽基",
    # A股医药
    "159992": "A股医药", "512010": "A股医药", "512170": "A股医药",
    "159938": "A股医药", "516060": "A股医药", "159828": "A股医药",
    # 港股
    "513180": "港股", "513050": "港股", "513130": "港股",
    "513100": "港股", "159920": "港股", "513060": "港股",
    # 债券
    "161119": "债券", "511010": "债券", "511260": "债券",
    "159972": "债券", "511220": "债券", "511020": "债券",
}

# ETF名称关键词映射（v6.0 新增：增强动态检测）
ETF_NAME_KEYWORDS = {
    "A股科技": ["科技", "芯片", "半导体", "人工智能", "AI", "5G", "通信", "计算机",
                 "软件", "电子", "新能源车", "光伏", "科创", "创新"],
    "A股医药": ["医药", "医疗", "生物", "创新药", "中药", "健康", "养老"],
    "港股": ["恒生", "港股", "香港", "H股"],
    "债券": ["债券", "国债", "转债", "可转债", "信用债", "地方政府债"],
}

# ============================================================
# 第四灯配置：按ETF类型分流（v6.0 新增滚动累计跌幅阈值）
# ============================================================
FOURTH_LIGHT_CONFIG = {
    "A股科技": {
        "indices": [
            {"name": "上证指数", "secid": "1.000001", "check_ma120": True, "check_ma20": True,
             "crash_red": 3.0, "crash_yellow": 1.5,
             "cum3_red": 5.0, "cum3_yellow": 3.0,
             "cum5_red": 7.0, "cum5_yellow": 5.0},
            {"name": "创业板指", "secid": "0.399006", "check_ma120": False, "check_ma20": False,
             "crash_red": 5.0, "crash_yellow": 3.0,
             "cum3_red": 8.0, "cum3_yellow": 5.0,
             "cum5_red": 10.0, "cum5_yellow": 7.0},
            {"name": "科创50",  "secid": "1.000688", "check_ma120": True, "check_ma20": False,
             "crash_red": 5.0, "crash_yellow": 3.0,
             "cum3_red": 8.0, "cum3_yellow": 5.0,
             "cum5_red": 10.0, "cum5_yellow": 7.0},
        ],
        "extra_relief": {"name": "科创50", "secid": "1.000688", "condition": "连续3日无单日跌幅>3%"},
    },
    "A股宽基": {
        "indices": [
            {"name": "上证指数", "secid": "1.000001", "check_ma120": True, "check_ma20": True,
             "crash_red": 3.0, "crash_yellow": 1.5,
             "cum3_red": 5.0, "cum3_yellow": 3.0,
             "cum5_red": 7.0, "cum5_yellow": 5.0},
            {"name": "创业板指", "secid": "0.399006", "check_ma120": False, "check_ma20": False,
             "crash_red": 5.0, "crash_yellow": 3.0,
             "cum3_red": 8.0, "cum3_yellow": 5.0,
             "cum5_red": 10.0, "cum5_yellow": 7.0},
        ],
        "extra_relief": None,
    },
    "A股医药": {
        "indices": [
            {"name": "上证指数", "secid": "1.000001", "check_ma120": True, "check_ma20": True,
             "crash_red": 3.0, "crash_yellow": 1.5,
             "cum3_red": 5.0, "cum3_yellow": 3.0,
             "cum5_red": 7.0, "cum5_yellow": 5.0},
            {"name": "创业板指", "secid": "0.399006", "check_ma120": False, "check_ma20": False,
             "crash_red": 5.0, "crash_yellow": 3.0,
             "cum3_red": 8.0, "cum3_yellow": 5.0,
             "cum5_red": 10.0, "cum5_yellow": 7.0},
        ],
        "extra_relief": None,
    },
    "���股": {
        "indices": [
            {"name": "上证指数", "secid": "1.000001", "check_ma120": True, "check_ma20": True,
             "crash_red": 3.0, "crash_yellow": 1.5,
             "cum3_red": 5.0, "cum3_yellow": 3.0,
             "cum5_red": 7.0, "cum5_yellow": 5.0},
            {"name": "创业板指", "secid": "0.399006", "check_ma120": False, "check_ma20": False,
             "crash_red": 5.0, "crash_yellow": 3.0,
             "cum3_red": 8.0, "cum3_yellow": 5.0,
             "cum5_red": 10.0, "cum5_yellow": 7.0},
        ],
        "extra_relief": None,
    },
    "债券": {
        "indices": [],
        "extra_relief": None,
    },
}

# ============================================================
# 数据获取：ETF K线（新浪）+ 指数K线（东方财富）
# ============================================================

def get_sina_symbol(code: str) -> str:
    """根据ETF代码判断新浪符号前缀。上海=sh，深圳=sz"""
    code = code.strip()
    if code.startswith(('51', '52', '56', '58')):
        return f"sh{code}"
    elif code.startswith(('15', '16')):
        return f"sz{code}"
    else:
        return f"sh{code}"

def fetch_klines(code: str, datalen: int = 120) -> list:
    """从新浪财经拉取ETF日K数据"""
    symbol = get_sina_symbol(code)
    url = "https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    params = {
        "symbol": symbol,
        "scale": "240",
        "datalen": str(datalen),
    }
    resp = requests.get(url, params=params, timeout=15)
    if resp.status_code != 200:
        raise ValueError(f"请求失败: HTTP {resp.status_code}")

    try:
        raw = resp.json()
    except Exception:
        raise ValueError(f"解析JSON失败，可能ETF代码 {code} 不正确")

    if not raw or not isinstance(raw, list):
        raise ValueError(f"未获取到ETF {code} 的K线数据，请检查代码")

    klines = []
    for item in raw:
        klines.append({
            "date": item["day"],
            "open": float(item["open"]),
            "close": float(item["close"]),
            "high": float(item["high"]),
            "low": float(item["low"]),
            "volume": float(item["volume"]),
        })
    return klines

# 指数K线缓存
_index_cache = {}

def fetch_index_klines(secid: str, count: int = 130) -> list:
    """从东方财富拉取指数日K数据，带缓存"""
    if secid in _index_cache:
        return _index_cache[secid]

    url = "http://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid,
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "klt": "101",
        "fqt": "1",
        "end": "20500101",
        "lmt": str(count),
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if not data or not data.get("data") or not data["data"].get("klines"):
            return []
        klines = []
        for line in data["data"]["klines"]:
            parts = line.split(",")
            klines.append({
                "date": parts[0],
                "open": float(parts[1]),
                "close": float(parts[2]),
                "high": float(parts[3]),
                "low": float(parts[4]),
                "volume": float(parts[5]),
            })
        _index_cache[secid] = klines
        return klines
    except Exception:
        return []

# ============================================================
# 均线计算
# ============================================================

def calc_ma(values: list, period: int) -> list:
    """计算移动平均线"""
    mas = [None] * len(values)
    for i in range(period - 1, len(values)):
        mas[i] = sum(values[i - period + 1: i + 1]) / period
    return mas

# ============================================================
# ADX 趋势强度计算（v6.0 新增）
# ============================================================

def calc_adx(klines: list, period: int = 14) -> dict:
    """计算ADX（平均趋向指数）趋势强度"""
    n = len(klines)
    if n < period + 1:
        return {"adx": None, "plus_di": None, "minus_di": None, "strength": "数据不足"}

    # 计算 True Range 和 ±DM
    tr_list = [0.0] * n
    plus_dm_list = [0.0] * n
    minus_dm_list = [0.0] * n

    for i in range(1, n):
        high = klines[i]["high"]
        low = klines[i]["low"]
        close_prev = klines[i - 1]["close"]

        # True Range
        tr_list[i] = max(
            high - low,
            abs(high - close_prev),
            abs(low - close_prev)
        )

        # +DM / -DM
        up_move = high - klines[i - 1]["high"]
        down_move = klines[i - 1]["low"] - low

        if up_move > down_move and up_move > 0:
            plus_dm_list[i] = up_move
        else:
            plus_dm_list[i] = 0.0

        if down_move > up_move and down_move > 0:
            minus_dm_list[i] = down_move
        else:
            minus_dm_list[i] = 0.0

    # Wilder's smoothing for first value (simple average)
    start_idx = period  # element at index `period` uses data from 1..period

    tr_smooth = sum(tr_list[1:period + 1])
    plus_dm_smooth = sum(plus_dm_list[1:period + 1])
    minus_dm_smooth = sum(minus_dm_list[1:period + 1])

    dx_list = [None] * n
    tr_first = tr_smooth

    # Calculate first DX
    if tr_first > 0:
        plus_di = 100.0 * plus_dm_smooth / tr_first
        minus_di = 100.0 * minus_dm_smooth / tr_first
        dx_val = 100.0 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0.0
        dx_list[period] = dx_val

    # Wilder's smoothing for remaining values
    for i in range(period + 1, n):
        tr_smooth = tr_smooth - tr_smooth / period + tr_list[i]
        plus_dm_smooth = plus_dm_smooth - plus_dm_smooth / period + plus_dm_list[i]
        minus_dm_smooth = minus_dm_smooth - minus_dm_smooth / period + minus_dm_list[i]

        if tr_smooth > 0:
            plus_di = 100.0 * plus_dm_smooth / tr_smooth
            minus_di = 100.0 * minus_dm_smooth / tr_smooth
            dx_val = 100.0 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0.0
            dx_list[i] = dx_val
        else:
            dx_list[i] = 0.0

    # Calculate ADX (smoothed DX)
    # First ADX at index = period + period - 1 = 2*period - 1
    adx_start = 2 * period - 1
    adx_list = [None] * n
    if adx_start < n:
        valid_dx = [d for d in dx_list[period:adx_start + 1] if d is not None]
        if len(valid_dx) == period:
            adx_list[adx_start] = sum(valid_dx) / period
            # Wilder's smoothing for ADX
            for i in range(adx_start + 1, n):
                if dx_list[i] is not None:
                    adx_list[i] = (adx_list[i - 1] * (period - 1) + dx_list[i]) / period

    latest_adx = adx_list[n - 1]

    if latest_adx is None:
        return {"adx": None, "plus_di": None, "minus_di": None, "strength": "数据不足"}

    if latest_adx >= 25:
        strength = "强趋势"
        strength_note = "趋势明确，信号可信度较高"
    elif latest_adx >= 20:
        strength = "中等趋势"
        strength_note = "趋势尚可，正常参考信号"
    else:
        strength = "弱趋势/震荡"
        strength_note = "趋势偏弱，建议谨慎操作，缩小仓位"

    # 计算最新 ±DI
    if tr_smooth > 0:
        latest_plus_di = round(100.0 * plus_dm_smooth / tr_smooth, 2)
        latest_minus_di = round(100.0 * minus_dm_smooth / tr_smooth, 2)
    else:
        latest_plus_di = None
        latest_minus_di = None

    return {
        "adx": round(latest_adx, 2),
        "plus_di": latest_plus_di,
        "minus_di": latest_minus_di,
        "strength": strength,
        "strength_note": strength_note,
    }

# ============================================================
# 第一灯：顺风灯（v6.0 新增ADX趋势强度备注）
# ============================================================

def judge_tailwind_light(klines: list, ma20: list, adx_info: dict = None) -> dict:
    """顺风灯：MA20方向向上 + 收盘价在MA20上方"""
    n = len(klines)
    if ma20[n - 1] is None or n < 26 or ma20[n - 6] is None:
        return {"status": "🔴", "reason": "数据不足，无法计算MA20"}

    ma20_now = ma20[n - 1]
    ma20_5d_ago = ma20[n - 6]
    close_now = klines[n - 1]["close"]
    direction_up = ma20_now > ma20_5d_ago
    price_above = close_now > ma20_now
    green = direction_up and price_above

    reason = f"MA20={ma20_now:.4f}，{'向上' if direction_up else '向下'}；收盘价{close_now:.4f}在MA20{'上方' if price_above else '下方'}"

    # v6.0: 附加ADX趋势强度备注
    if adx_info and adx_info.get("adx") is not None:
        reason += f"；ADX={adx_info['adx']:.1f}（{adx_info['strength']}）"

    return {
        "status": "🟢" if green else "🔴",
        "ma20": round(ma20_now, 4),
        "direction": "向上" if direction_up else "向下",
        "close": round(close_now, 4),
        "price_position": "上方" if price_above else "下方",
        "reason": reason,
    }

# ============================================================
# 第二灯：风力灯（v6.0 量价四象限细分）
# ============================================================

def judge_wind_power_light(klines: list) -> dict:
    """风力灯：量价配合分析 — 放量上涨/放量下跌/缩量上涨/缩量下跌"""
    n = len(klines)
    if n < 25:
        return {"status": "🔴", "reason": "数据不足"}

    vol_5d = sum(k["volume"] for k in klines[n-5:]) / 5
    vol_20d = sum(k["volume"] for k in klines[n-25:n-5]) / 20
    vol_ratio = vol_5d / vol_20d if vol_20d > 0 else 0
    is_expanding = vol_ratio > 1.0

    close_5d_ago = klines[n - 6]["close"]
    close_now = klines[n - 1]["close"]
    return_5d = (close_now - close_5d_ago) / close_5d_ago * 100
    is_positive = return_5d > 0
    green = is_expanding and is_positive

    # v6.0: 量价四象限分类
    if is_expanding and is_positive:
        quadrant = "放量上涨"
        quadrant_strength = "强烈看多"
    elif is_expanding and not is_positive:
        quadrant = "放量下跌"
        quadrant_strength = "强烈看空（放量出逃）"
    elif not is_expanding and is_positive:
        quadrant = "缩量上涨"
        quadrant_strength = "较弱看多（上涨缺量）"
    else:
        quadrant = "缩量下跌"
        quadrant_strength = "较弱看空（弱市阴跌）"

    return {
        "status": "🟢" if green else "🔴",
        "vol_ratio": round(vol_ratio, 2),
        "volume_trend": "放量" if is_expanding else "缩量",
        "return_5d": round(return_5d, 2),
        "momentum": "向上" if is_positive else "向下",
        "quadrant": quadrant,
        "quadrant_strength": quadrant_strength,
        "reason": f"量价={quadrant}；5日均量/20日均量={vol_ratio:.2f}x，5日涨跌幅={return_5d:.2f}%",
    }

# ============================================================
# 第三灯：起锚灯（v6.0 新增金叉确认期）
# ============================================================

def judge_anchor_light(klines: list, ma5: list, ma10: list) -> dict:
    """起锚灯：MA5上穿MA10（或持续在上方）+ 量能配合 + 金叉确认期"""
    n = len(klines)
    if ma5[n - 1] is None or ma10[n - 1] is None:
        return {"status": "🔴", "reason": "数据不足"}

    ma5_now = ma5[n - 1]
    ma10_now = ma10[n - 1]
    ma5_above = ma5_now > ma10_now

    cross_day_idx = None
    cross_type = "MA5持续在MA10下方"
    cross_confirmation = None  # v6.0: 金叉确认状态

    if ma5_above:
        for i in range(n - 1, max(n - 30, 10), -1):
            if ma5[i] is not None and ma10[i] is not None and ma5[i-1] is not None and ma10[i-1] is not None:
                if ma5[i] > ma10[i] and ma5[i-1] <= ma10[i-1]:
                    cross_day_idx = i
                    cross_type = "金叉"

                    # v6.0: 金叉确认期
                    days_since_cross = n - 1 - cross_day_idx
                    if days_since_cross <= 2:
                        cross_confirmation = "待确认（金叉发生仅{}日）".format(days_since_cross + 1)
                    else:
                        cross_confirmation = "已确认（金叉发生{}日）".format(days_since_cross + 1)
                    break

        if cross_day_idx is None:
            cross_type = "MA5持续在MA10上方"
            for i in range(n - 1, max(n - 30, 10), -1):
                if ma5[i] is not None and ma10[i] is not None:
                    if ma5[i] <= ma10[i]:
                        cross_day_idx = i + 1
                        days_since_cross = n - 1 - cross_day_idx
                        cross_confirmation = "已确认（持续在MA10上方{}日）".format(days_since_cross + 1)
                        break
            if cross_day_idx is None:
                cross_day_idx = 10
                cross_confirmation = "已确认（长期在上方）"
    else:
        for i in range(n - 1, max(n - 30, 10), -1):
            if ma5[i] is not None and ma10[i] is not None and ma5[i-1] is not None and ma10[i-1] is not None:
                if ma5[i] < ma10[i] and ma5[i-1] >= ma10[i-1]:
                    cross_day_idx = i
                    cross_type = "死叉"
                    break
        if cross_day_idx is None:
            cross_type = "MA5持续在MA10下方"

    has_volume_support = False
    vol_info = ""
    check_idx = cross_day_idx if cross_day_idx is not None else n - 1

    if check_idx is not None and check_idx < n and check_idx >= 20:
        check_vol = klines[check_idx]["volume"]
        pre_20d_avg = sum(k["volume"] for k in klines[check_idx - 20:check_idx]) / 20
        has_volume_support = check_vol > pre_20d_avg
        vol_ratio = check_vol / pre_20d_avg if pre_20d_avg > 0 else 0
        vol_info = f"量比20日均量={vol_ratio:.2f}x，{'有量配合' if has_volume_support else '量能不足'}"
    else:
        if n >= 21:
            recent_vol = klines[n-1]["volume"]
            pre_20d_avg = sum(k["volume"] for k in klines[n-21:n-1]) / 20
            has_volume_support = recent_vol > pre_20d_avg
            vol_ratio = recent_vol / pre_20d_avg if pre_20d_avg > 0 else 0
            vol_info = f"最新日量比20日均量={vol_ratio:.2f}x，{'有量配合' if has_volume_support else '量能不足'}"
        else:
            has_volume_support = True
            vol_info = "数据不足，跳过量能检查"

    green = ma5_above and has_volume_support

    # v6.0: 构建增强版reason
    reason = f"MA5={ma5_now:.4f}/MA10={ma10_now:.4f}，{cross_type}"
    if cross_confirmation:
        reason += f"（{cross_confirmation}）"
    reason += f"；{vol_info}"

    return {
        "status": "🟢" if green else "🔴",
        "ma5": round(ma5_now, 4),
        "ma10": round(ma10_now, 4),
        "cross_type": cross_type,
        "cross_confirmation": cross_confirmation,
        "volume_support": has_volume_support,
        "reason": reason,
    }

# ============================================================
# 第四灯：市场环境灯（v6.0 新增滚动累计跌幅）
# ============================================================

def detect_etf_type(code: str) -> str:
    """检测ETF类型：注册表 → 代码前缀推断 → 默认A股宽基"""
    code = code.strip()
    if code in ETF_TYPE_REGISTRY:
        return ETF_TYPE_REGISTRY[code]
    # 前缀推断
    if code.startswith('51') or code.startswith('52') or code.startswith('56') or code.startswith('58'):
        if code.startswith('513'):
            return "港股"
        elif code.startswith('511'):
            return "债券"
        else:
            return "A股宽基"
    elif code.startswith('15') or code.startswith('16'):
        if code.startswith('161'):
            return "债券"
        else:
            return "A股宽基"
    else:
        return "A股宽基"

def calc_daily_change(klines: list) -> float:
    """计算最新交易日涨跌幅(%)"""
    n = len(klines)
    if n < 2:
        return 0.0
    prev_close = klines[n-2]["close"]
    curr_close = klines[n-1]["close"]
    if prev_close == 0:
        return 0.0
    return (curr_close - prev_close) / prev_close * 100

def calc_cumulative_decline(klines: list, days: int) -> float:
    """计算N日滚动累计涨跌幅(%)。负数表示累计下跌。"""
    n = len(klines)
    if n < days + 1:
        return None
    start_close = klines[n - 1 - days]["close"]
    end_close = klines[n - 1]["close"]
    if start_close == 0:
        return None
    return (end_close - start_close) / start_close * 100

def check_consecutive_above_ma(klines: list, ma_list: list, ma_period: int, required_days: int = 3) -> dict:
    """检查连续N日收盘≥MA的进度"""
    n = len(klines)
    count = 0
    for i in range(n - 1, -1, -1):
        if ma_list[i] is not None and klines[i]["close"] >= ma_list[i]:
            count += 1
        else:
            break
    return {
        "progress": f"{count}/{required_days}",
        "achieved": count >= required_days,
        "ma_value": round(ma_list[n-1], 2) if ma_list[n-1] else None,
        "latest_close": round(klines[n-1]["close"], 2),
        "gap_pct": round((klines[n-1]["close"] - ma_list[n-1]) / ma_list[n-1] * 100, 2) if ma_list[n-1] else None,
    }

def check_consecutive_no_crash(klines: list, threshold: float, required_days: int = 3) -> dict:
    """检查连续N日无单日跌幅>threshold的进度"""
    n = len(klines)
    count = 0
    for i in range(n - 1, 0, -1):
        change = (klines[i]["close"] - klines[i-1]["close"]) / klines[i-1]["close"] * 100
        if change > -threshold:
            count += 1
        else:
            break
    return {
        "progress": f"{count}/{required_days}",
        "achieved": count >= required_days,
        "threshold": f"-{threshold}%",
    }

def check_market_environment(etf_type: str) -> dict:
    """第四灯核心：检查市场环境，按ETF类型分流（v6.0 新增滚动累计跌幅）"""
    config = FOURTH_LIGHT_CONFIG.get(etf_type, FOURTH_LIGHT_CONFIG["A股宽基"])

    if not config["indices"]:
        # 债券ETF跳过第四灯
        return {
            "status": "N/A",
            "reason": "债券ETF不适用第四灯（债券与股票走势经常相反）",
            "applicable": False,
        }

    index_results = []
    has_red = False
    has_yellow = False

    for idx_config in config["indices"]:
        idx_klines = fetch_index_klines(idx_config["secid"])
        if not idx_klines or len(idx_klines) < 2:
            index_results.append({
                "name": idx_config["name"],
                "status": "❓",
                "reason": "数据获取失败",
            })
            has_red = True  # 数据失败按红灯处理
            continue

        n_idx = len(idx_klines)
        daily_change = calc_daily_change(idx_klines)
        latest_close = idx_klines[n_idx-1]["close"]

        # v6.0: 计算滚动累计跌幅
        cum3_change = calc_cumulative_decline(idx_klines, 3)
        cum5_change = calc_cumulative_decline(idx_klines, 5)

        # 检查MA120
        ma120_val = None
        below_ma120 = False
        if idx_config["check_ma120"]:
            ma120 = calc_ma([k["close"] for k in idx_klines], 120)
            if ma120[n_idx-1] is not None:
                ma120_val = ma120[n_idx-1]
                below_ma120 = latest_close < ma120_val

        # 检查MA20
        below_ma20 = False
        ma20_val = None
        if idx_config["check_ma20"]:
            ma20 = calc_ma([k["close"] for k in idx_klines], 20)
            if ma20[n_idx-1] is not None:
                ma20_val = ma20[n_idx-1]
                below_ma20 = latest_close < ma20_val and (not below_ma120)

        # 判定红黄绿
        is_red = False
        is_yellow = False
        reasons = []

        # MA条件
        if below_ma120:
            is_red = True
            reasons.append(f"收盘{latest_close:.2f}<MA120({ma120_val:.2f})")

        # 单日跌幅
        if abs(daily_change) > idx_config["crash_red"] and daily_change < 0:
            is_red = True
            reasons.append(f"单日跌幅{daily_change:.2f}%>{idx_config['crash_red']}%")
        elif abs(daily_change) > idx_config["crash_yellow"] and daily_change < 0:
            is_yellow = True
            reasons.append(f"单日跌幅{daily_change:.2f}%>{idx_config['crash_yellow']}%")

        # v6.0: 滚动累计跌幅检查
        if "cum3_red" in idx_config and cum3_change is not None:
            if cum3_change < -idx_config["cum3_red"]:
                is_red = True
                reasons.append(f"3日累计跌幅{cum3_change:.2f}%，超过{idx_config['cum3_red']}%红阈值")
            elif cum3_change < -idx_config["cum3_yellow"]:
                if not is_red:
                    is_yellow = True
                reasons.append(f"3日累计跌幅{cum3_change:.2f}%，超过{idx_config['cum3_yellow']}%黄阈值")

        if "cum5_red" in idx_config and cum5_change is not None:
            if cum5_change < -idx_config["cum5_red"]:
                is_red = True
                reasons.append(f"5日累计跌幅{cum5_change:.2f}%，超过{idx_config['cum5_red']}%红阈值")
            elif cum5_change < -idx_config["cum5_yellow"]:
                if not is_red:
                    is_yellow = True
                reasons.append(f"5日累计跌幅{cum5_change:.2f}%，超过{idx_config['cum5_yellow']}%黄阈值")

        # MA20条件（仅在非红时）
        if below_ma20 and not is_red:
            is_yellow = True
            reasons.append(f"收盘<MA20({ma20_val:.2f})但≥MA120")

        if is_red:
            status = "🔴"
            has_red = True
        elif is_yellow:
            status = "🟡"
            has_yellow = True
        else:
            status = "🟢"

        index_results.append({
            "name": idx_config["name"],
            "status": status,
            "latest_close": round(latest_close, 2),
            "ma120": round(ma120_val, 2) if ma120_val else None,
            "ma20": round(ma20_val, 2) if ma20_val else None,
            "daily_change": round(daily_change, 2),
            "cum3_change": round(cum3_change, 2) if cum3_change is not None else None,
            "cum5_change": round(cum5_change, 2) if cum5_change is not None else None,
            "reason": "；".join(reasons) if reasons else "各项指标正常",
        })

    # 汇总：任一指数红→红，任一黄→黄（无红时），全绿→绿
    if has_red:
        overall_status = "🔴"
        overall_reason = "存在红色触发的指数"
    elif has_yellow:
        overall_status = "🟡"
        overall_reason = "存在黄色触发的指数"
    else:
        overall_status = "🟢"
        overall_reason = "所有检查指数均正常"

    # 红灯时计算解除进度
    relief_progress = None
    if overall_status == "🔴":
        relief_progress = _check_relief_progress(config)

    return {
        "status": overall_status,
        "reason": overall_reason,
        "applicable": True,
        "etf_type": etf_type,
        "index_details": index_results,
        "relief_progress": relief_progress,
    }

def _check_relief_progress(config: dict) -> dict:
    """计算红灯解除条件进度（v6.0 条件3不再硬编码false）"""
    progress = {}

    # 条件1：上证连续3日收盘≥MA120
    sh_klines = fetch_index_klines("1.000001")
    if sh_klines and len(sh_klines) >= 120:
        sh_ma120 = calc_ma([k["close"] for k in sh_klines], 120)
        cond1 = check_consecutive_above_ma(sh_klines, sh_ma120, 120, 3)
        progress["条件1_上证3日≥MA120"] = cond1
    else:
        progress["条件1_上证3日≥MA120"] = {"progress": "0/3", "achieved": False, "reason": "数据不足"}

    # 条件2：创业板连续3日无单日跌幅>3%
    cyb_klines = fetch_index_klines("0.399006")
    if cyb_klines and len(cyb_klines) >= 2:
        cond2 = check_consecutive_no_crash(cyb_klines, 3.0, 3)
        progress["条件2_创业板3日无暴跌"] = cond2
    else:
        progress["条件2_创业板3日无暴跌"] = {"progress": "0/3", "achieved": False, "reason": "数据不足"}

    # v6.0: 条件3改进 — 不再硬编码false，标记为需确认
    progress["条件3_主力3日净流入"] = {
        "progress": "需盘后确认",
        "achieved": None,  # None = 未知，不再硬编码 False
        "note": "脚本无法获取主力资金数据。在WorkBuddy对话中可通过neodata-financial-search自动判断",
    }

    # 条件4（科技ETF额外）：科创50连续3日无单日跌幅>3%
    if config.get("extra_relief"):
        extra = config["extra_relief"]
        kc50_klines = fetch_index_klines(extra["secid"])
        if kc50_klines and len(kc50_klines) >= 2:
            cond4 = check_consecutive_no_crash(kc50_klines, 3.0, 3)
            progress["条件4_科创50_3日无暴跌（科技ETF额外）"] = cond4
        else:
            progress["条件4_科创50_3日无暴跌（科技ETF额外）"] = {"progress": "0/3", "achieved": False, "reason": "数据不足"}

    # 汇总：仅统计可自动检查的条件（排除条件3）
    auto_conditions = [k for k in progress if "条件3" not in k]
    auto_all_met = all(progress[k].get("achieved", False) for k in auto_conditions)

    return {
        "conditions": progress,
        "auto_conditions_all_met": auto_all_met,
        "note": "条件3（主力资金净流入）需通过neodata或盘后确认，其余条件脚本自动检查",
    }

# ============================================================
# 综合分析（v6.0 集成ADX）
# ============================================================

def analyze_etf(code: str) -> dict:
    """分析单只ETF的四盏灯状态"""
    klines = fetch_klines(code, datalen=120)

    if len(klines) < 25:
        return {"code": code, "error": f"K线数据不足({len(klines)}根)，需至少25根"}

    closes = [k["close"] for k in klines]
    ma5 = calc_ma(closes, 5)
    ma10 = calc_ma(closes, 10)
    ma20 = calc_ma(closes, 20)

    # v6.0: 计算ADX
    adx_info = calc_adx(klines)

    tailwind = judge_tailwind_light(klines, ma20, adx_info)
    wind_power = judge_wind_power_light(klines)
    anchor = judge_anchor_light(klines, ma5, ma10)

    # 第四灯：按ETF类型分流
    etf_type = detect_etf_type(code)
    fourth_light = check_market_environment(etf_type)

    # all_green逻辑修复：n/a不算green
    light4_status = fourth_light["status"]
    light4_green = (light4_status == "🟢")
    light4_na = (light4_status == "N/A")
    light4_red = (light4_status == "🔴")
    light4_yellow = (light4_status == "🟡")

    first_three_green = (tailwind["status"] == "🟢" and
                         wind_power["status"] == "🟢" and
                         anchor["status"] == "🟢")

    if light4_na:
        all_green = first_three_green  # 债券ETF只看前三灯
    else:
        all_green = first_three_green and light4_green

    green_count = sum(1 for x in [tailwind["status"], wind_power["status"], anchor["status"]] if x == "🟢")
    if light4_green:
        green_count += 1

    # v6.0: ADX调整advice
    adx_note = ""
    if adx_info and adx_info.get("adx") is not None and adx_info["adx"] < 20:
        adx_note = "（注意：ADX={}，趋势偏弱，建议谨慎）".format(adx_info["adx"])

    # advice判断顺序：红灯 > 黄灯 > 不适用 > 全绿 > 其他
    if light4_red:
        advice = "第四灯红灯，市场环境恶劣，禁止新建仓（卖出不受限）" + adx_note
    elif light4_yellow:
        advice = "第四灯黄灯，市场环境偏弱，谨慎操作，建议观望" + adx_note
    elif light4_na:
        if first_three_green:
            advice = "前三灯全绿（第四灯不适用于债券ETF），可考虑进场或持有" + adx_note
        elif green_count == 2:
            advice = "两灯亮一灯灭，趋势尚未完全确认，建议观望" + adx_note
        elif green_count == 1:
            advice = "仅一灯亮，趋势不明朗，建议继续观望" + adx_note
        else:
            advice = "三灯全灭，趋势走弱，持有者考虑减仓/离场" + adx_note
    elif all_green:
        advice = "四灯全绿，趋势+资金+短线+市场环境四重确认，可考虑进场或持有" + adx_note
    elif green_count == 3:
        advice = "三灯亮一灯灭，趋势基本确认但尚有不足，建议观望等待第四灯" + adx_note
    elif green_count == 2:
        advice = "两灯亮，趋势尚未完全确认，建议观望" + adx_note
    elif green_count == 1:
        advice = "仅一灯亮，趋势不明朗，建议继续观望" + adx_note
    else:
        advice = "灯全灭，趋势走弱，持有者考虑减仓/离场，空仓者继续等待" + adx_note

    result = {
        "code": code,
        "etf_type": etf_type,
        "data_date": klines[-1]["date"],
        "latest_close": round(closes[-1], 4),
        "kline_count": len(klines),
        "tailwind_light": tailwind,
        "wind_power_light": wind_power,
        "anchor_light": anchor,
        "fourth_light": fourth_light,
        "all_green": all_green,
        "green_count": green_count,
        "advice": advice,
    }

    # v6.0: 顶层ADX信息
    if adx_info and adx_info.get("adx") is not None:
        result["adx"] = {
            "value": adx_info["adx"],
            "plus_di": adx_info["plus_di"],
            "minus_di": adx_info["minus_di"],
            "strength": adx_info["strength"],
            "note": adx_info["strength_note"],
        }

    return result

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "请传入ETF代码，如: python three_lights.py 159599 159992 510300"}, ensure_ascii=False))
        sys.exit(1)

    codes = []
    for arg in sys.argv[1:]:
        for code in arg.replace(",", " ").split():
            code = code.strip()
            if len(code) == 6 and code.isdigit():
                codes.append(code)

    if not codes:
        print(json.dumps({"error": "未识别到有效的6位ETF代码"}, ensure_ascii=False))
        sys.exit(1)

    results = []
    for code in codes:
        try:
            result = analyze_etf(code)
            results.append(result)
        except Exception as e:
            results.append({"code": code, "error": str(e)})

    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
