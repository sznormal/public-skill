#!/usr/bin/env python3
"""
ETF定投回测分析脚本
优先通过 westock-data（腾讯自选股）获取 ETF 日 K 线，备选东方财富 push2his API，
模拟定期定额（定投）与一次性投入的收益对比，输出回测指标与走势序列。

用法:
    python etf_dca_backtest.py <ETF代码> [--freq weekly|monthly] [--amount 1000] \
        [--period 2y] [--fq qfq] [--output json|table]

示例:
    python etf_dca_backtest.py 510300
    python etf_dca_backtest.py 159915 --freq monthly --amount 2000 --period 3y
    python etf_dca_backtest.py 588000 --freq weekly --amount 500 --period 5y
"""

import sys
import os
import glob
import json
import argparse
import subprocess
from datetime import datetime, timedelta


# ---- 路径解析（自动适配不同机器上的运行时与 westock-data 安装位置）----
def _wb_home(*parts):
    """WorkBuddy 用户目录，按本机 HOME 推导，不写死用户名。"""
    return os.path.join(os.path.expanduser("~"), ".workbuddy", *parts)


def find_node():
    candidates = [os.environ.get("NODE_BIN", "")]
    candidates += sorted(glob.glob(_wb_home("binaries", "node", "versions", "*", "node.exe")), reverse=True)
    candidates += [
        r"D:/Program Files/nodejs/node.exe",
        r"C:/Program Files/nodejs/node.exe",
        "/usr/local/bin/node",
        "/usr/bin/node",
    ]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return "node"


def find_westock_cli():
    if os.environ.get("WESTOCK_CLI"):
        return os.environ["WESTOCK_CLI"]
    candidates = []
    for pattern in (
        ("plugins", "**", "westock-tool", "scripts", "index.js"),
        ("plugins", "**", "westock-data", "scripts", "index.js"),
        ("resources", "builtin-skills", "westock-data", "scripts", "index.js"),
    ):
        candidates += sorted(glob.glob(_wb_home(*pattern), recursive=True))
    candidates += [
        r"D:/workbudy/WorkBuddy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js",
        r"D:/workbudy/resources/app.asar.unpacked/resources/builtin-skills/westock-data/scripts/index.js",
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0] if candidates else ""


WESTOCK_CLI = find_westock_cli()
NODE_BIN = find_node()


def parse_args():
    parser = argparse.ArgumentParser(description='ETF定投回测分析')
    parser.add_argument('fund_code', type=str, help='ETF代码(6位数字)')
    parser.add_argument('--freq', type=str, default='weekly',
                        choices=['weekly', 'monthly'],
                        help='定投频率: weekly(周定投) / monthly(月定投) (默认weekly)')
    parser.add_argument('--amount', type=float, default=1000.0,
                        help='每期定投金额(元) (默认1000)')
    parser.add_argument('--period', type=str, default='2y',
                        choices=['1y', '2y', '3y', '5y', 'all'],
                        help='回测周期 (默认2y)')
    parser.add_argument('--fq', type=str, default='qfq',
                        choices=['qfq', 'hfq', 'none'],
                        help='复权方式: qfq(前复权)/hfq(后复权)/none(不复权) (默认qfq)')
    parser.add_argument('--output', type=str, default='json',
                        choices=['json', 'table'],
                        help='输出格式 (默认json)')
    return parser.parse_args()


def get_offset(period):
    return {'1y': 250, '2y': 500, '3y': 750, '5y': 1250, 'all': 2500}.get(period, 500)


def get_westock_code(code):
    if code.lower().startswith(('sh', 'sz')):
        return code.lower()
    if code.startswith(('5', '6', '9')):
        return f"sh{code}"
    return f"sz{code}"


# ---------------- K线获取 ----------------
def get_klines_westock(symbol, offset=500, fq='qfq'):
    """通过 westock-data CLI 获取日 K 线（主数据源）"""
    ws_code = get_westock_code(symbol)
    try:
        result = subprocess.run(
            [NODE_BIN, WESTOCK_CLI, "kline", ws_code,
             "--period", "day", "--limit", str(offset), "--fq", fq],
            capture_output=True, text=True, timeout=60, encoding='utf-8'
        )
        if result.returncode != 0 and not result.stdout:
            return []
        output = result.stdout
    except Exception as e:
        print(f"[WARN] westock-data kline 调用失败({symbol}): {e}", file=sys.stderr)
        return []

    klines = []
    lines = output.strip().split('\n')
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith('|') and '---' in line:
            in_table = True
            continue
        if not in_table or not line.startswith('|'):
            continue
        cells = [c.strip() for c in line.split('|')[1:-1]]
        if not cells:
            continue
        # 表头: | date | open | last | high | low | ...
        if cells[0].lower() in ('date', '时间', '日期') or 'date' in cells[0].lower():
            continue
        if len(cells) < 5:
            continue
        try:
            date_str = cells[0]
            if len(date_str) == 8 and date_str.isdigit():
                date_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            klines.append({
                'date': date_str,
                'open': float(cells[1]),
                'close': float(cells[2]),   # 该列实际名为 last（收盘价）
                'high': float(cells[3]),
                'low': float(cells[4]),
            })
        except (ValueError, IndexError):
            continue

    klines.sort(key=lambda x: x['date'])
    if len(klines) > offset:
        klines = klines[-offset:]
    return klines


def get_klines_eastmoney(symbol, offset=500, fq='qfq'):
    """东方财富历史 K 线 API（备选数据源）"""
    import requests
    import time as _time

    market = 1 if symbol.startswith(('5', '6', '9')) else 0
    secid = f"{market}.{symbol}"
    fqt = {'qfq': '1', 'hfq': '2', 'none': '0'}[fq]
    start_date = (datetime.now() - timedelta(days=int(offset * 1.6))).strftime("%Y%m%d")

    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    params = {
        "secid": secid, "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58",
        "klt": "101", "fqt": fqt, "beg": start_date, "end": "20500101",
        "lmt": str(offset + 20),
    }
    headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"}

    for attempt in range(3):
        try:
            _time.sleep(0.5 + attempt * 0.5)
            resp = requests.get(url, params=params, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            if attempt < 2:
                print(f"[WARN] 东财K线请求失败({symbol})第{attempt+1}次: {e}", file=sys.stderr)
                _time.sleep(1 + attempt)
            else:
                print(f"[WARN] 东财K线请求失败({symbol}): {e}", file=sys.stderr)
                return []

    klines_raw = data.get("data", {}).get("klines", [])
    klines = []
    for line in klines_raw:
        parts = line.split(",")
        if len(parts) < 7:
            continue
        try:
            klines.append({
                'date': parts[0],
                'open': float(parts[1]), 'close': float(parts[2]),
                'high': float(parts[3]), 'low': float(parts[4]),
            })
        except (ValueError, IndexError):
            continue
    klines.sort(key=lambda x: x['date'])
    if len(klines) > offset:
        klines = klines[-offset:]
    return klines


def get_klines(symbol, offset=500, fq='qfq'):
    klines = get_klines_westock(symbol, offset=offset, fq=fq)
    if klines:
        return klines
    return get_klines_eastmoney(symbol, offset=offset, fq=fq)


# ---------------- 定投回测 ----------------
def select_invest_dates(klines, freq):
    """按日历对齐选择定投日：周定投=每周第一个交易日，月定投=每月第一个交易日。"""
    invest_idx = []
    last_key = None
    for i, k in enumerate(klines):
        d = datetime.strptime(k['date'], '%Y-%m-%d')
        if freq == 'weekly':
            key = d.isocalendar()[:2]          # (year, week)
        else:
            key = (d.year, d.month)
        if key != last_key:
            invest_idx.append(i)
            last_key = key
    return invest_idx


def irr_per_period(cashflows):
    """用二分法求解每期内部收益率（cashflows 为各期末净现金流，期末含终值）。
    采用反向递推计算 NPV，避免大幂次导致的上溢/下溢与除零。"""
    def npv(r):
        # NPV = sum cf_i/(1+r)^i，反向递推避免 (1+r)^i 溢出
        acc = 0.0
        for cf in reversed(cashflows):
            acc = acc / (1 + r) + cf
        return acc

    lo, hi = -0.9999, 1000.0
    nlo, nhi = npv(lo), npv(hi)
    if nlo == nhi or (nlo > 0) == (nhi > 0):
        # 区间内未变号（含无穷/边界情形），返回近似
        return None
    for _ in range(300):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def max_drawdown(prices):
    mdd = 0.0
    peak = prices[0] if prices else 0
    for p in prices:
        if p > peak:
            peak = p
        if peak > 0:
            dd = (p / peak - 1)
            if dd < mdd:
                mdd = dd
    return mdd * 100


def run_dca(klines, freq, amount):
    n = len(klines)
    periods_per_year = 52 if freq == 'weekly' else 12
    idx = select_invest_dates(klines, freq)
    if not idx:
        return None

    total_invested = 0.0
    shares = 0.0
    series = []          # 每个定投日的累计投入与组合市值
    cashflows = []       # 用于 IRR

    for j, i in enumerate(idx):
        price = klines[i]['close']
        if price <= 0:
            continue
        buy_shares = amount / price
        shares += buy_shares
        total_invested += amount
        cashflows.append(-amount)
        series.append({
            'date': klines[i]['date'],
            'invested': round(total_invested, 2),
            'value': round(shares * price, 2),
            'price': price,
        })

    if total_invested <= 0:
        return None

    last_price = klines[-1]['close']
    final_value = shares * last_price

    # 终值计入最后一期现金流
    cashflows[-1] += final_value

    per_r = irr_per_period(cashflows)
    if per_r is not None and per_r > -0.9999:
        annualized = ((1 + per_r) ** periods_per_year - 1) * 100
    else:
        annualized = None

    dca_return = (final_value / total_invested - 1) * 100

    # 一次性投入对比：首期一次性投入等额资金
    first_price = klines[idx[0]]['close']
    lump_shares = total_invested / first_price
    lump_value = lump_shares * last_price
    lump_return = (lump_value / total_invested - 1) * 100
    days_span = (datetime.strptime(klines[-1]['date'], '%Y-%m-%d') -
                 datetime.strptime(klines[idx[0]]['date'], '%Y-%m-%d')).days
    years = max(days_span / 365.0, 1e-9)
    lump_annualized = ((lump_value / total_invested) ** (1 / years) - 1) * 100 if lump_value > 0 else 0

    # 价格序列最大回撤（基于回测窗口）
    prices = [k['close'] for k in klines]
    mdd = max_drawdown(prices)

    return {
        'freq': freq,
        'amount': amount,
        'installments': len(idx),
        'first_date': klines[idx[0]]['date'],
        'last_date': klines[-1]['date'],
        'total_invested': round(total_invested, 2),
        'final_value': round(final_value, 2),
        'shares': round(shares, 4),
        'last_price': last_price,
        'dca_return_pct': round(dca_return, 2),
        'dca_annualized_pct': round(annualized, 2) if annualized is not None else None,
        'lump_value': round(lump_value, 2),
        'lump_return_pct': round(lump_return, 2),
        'lump_annualized_pct': round(lump_annualized, 2),
        'max_drawdown_pct': round(mdd, 2),
        'excess_return_pct': round(dca_return - lump_return, 2),
        'series': series,
    }


def get_etf_name(fund_code):
    """通过腾讯财经行情获取 ETF 名称（轻量、无需 node）。"""
    import urllib.request
    prefix = 'sh' if fund_code.startswith(('5', '6', '9')) else 'sz'
    url = f"https://qt.gtimg.cn/q={prefix}{fund_code}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=10).read().decode("gbk")
        vals = data.split('"')[1].split("~")
        if len(vals) >= 53:
            return vals[1]
    except Exception:
        pass
    return fund_code


def main():
    args = parse_args()
    if len(args.fund_code) != 6 or not args.fund_code.isdigit():
        print(f"[ERROR] ETF代码应为6位数字, 当前: {args.fund_code}", file=sys.stderr)
        sys.exit(1)

    offset = get_offset(args.period)
    print(f"[INFO] 获取 ETF {args.fund_code} 日K线({offset}根)...", file=sys.stderr)
    klines = get_klines(args.fund_code, offset=offset, fq=args.fq)
    if not klines:
        print("[ERROR] 获取K线失败", file=sys.stderr)
        sys.exit(1)

    print(f"[INFO] 共 {len(klines)} 个交易日，运行定投回测({args.freq}, 每期{args.amount}元)...", file=sys.stderr)
    result = run_dca(klines, args.freq, args.amount)
    if not result:
        print("[ERROR] 定投回测失败（无有效数据）", file=sys.stderr)
        sys.exit(1)

    fund_name = get_etf_name(args.fund_code)
    output = {
        'fund_code': args.fund_code,
        'fund_name': fund_name,
        'analysis_period': args.period,
        'fq': args.fq,
        'report_date': datetime.now().strftime('%Y-%m-%d'),
        'metrics': result,
    }

    if args.output == 'table':
        print_table(output)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))


def print_table(output):
    m = output['metrics']
    print(f"\n{'='*64}")
    print(f"  ETF定投回测: {output['fund_name']}({output['fund_code']})")
    print(f"  频率: {m['freq']} | 每期: {m['amount']:.0f}元 | 周期: {output['analysis_period']}")
    print(f"  区间: {m['first_date']} ~ {m['last_date']} | 期数: {m['installments']}")
    print(f"{'='*64}")
    print(f"  {'指标':<22}{'定投(DCA)':>18}{'一次性投入':>18}")
    print(f"  {'-'*58}")
    print(f"  {'总投入(元)':<20}{m['total_invested']:>18}{m['total_invested']:>18}")
    print(f"  {'期末市值(元)':<20}{m['final_value']:>18.2f}{m['lump_value']:>18.2f}")
    print(f"  {'累计收益率':<20}{m['dca_return_pct']:>17.2f}%{m['lump_return_pct']:>17.2f}%")
    ann = f"{m['dca_annualized_pct']:.2f}%" if m['dca_annualized_pct'] is not None else 'N/A'
    print(f"  {'年化收益率':<20}{ann:>18}{m['lump_annualized_pct']:>17.2f}%")
    print(f"  {'区间最大回撤':<20}{m['max_drawdown_pct']:>17.2f}%{m['max_drawdown_pct']:>17.2f}%")
    print(f"  {'超额收益(定投-一次性)':<20}{m['excess_return_pct']:>16.2f}%")
    print(f"{'='*64}\n")


if __name__ == "__main__":
    main()
