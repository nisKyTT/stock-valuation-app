import streamlit as st
import yfinance as yf
import pandas as pd

# --- 網頁基礎設定 ---
st.set_page_config(
    page_title="美股看盤與估值 App",
    page_icon="📈",
    layout="wide"
)

# --- 券商級深色 App 風格 CSS (已修正桌面與手機版 RWD) ---
st.markdown("""
<style>
    /* 全局深邃暗黑背景與安全邊距 (避免被頂部工具列與底部浮動鈕遮擋) */
    .stApp {
        background-color: #0b0e11;
        color: #eaecef;
    }
    .block-container {
        padding-top: 3.8rem !important;
        padding-bottom: 6rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 960px;
    }

    /* 分頁導覽列 (仿券商 App 紅底線分頁) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        border-bottom: 1px solid #2b3139;
        justify-content: space-around;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        height: 44px;
        font-size: 15px;
        font-weight: 600;
        color: #848e9c;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #ef4444 !important;
    }

    /* 頂部大盤指數三欄並排網格 (手機版也保持橫向並排，不垂直堆疊) */
    .idx-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        margin-bottom: 14px;
    }
    .idx-card {
        border-radius: 10px;
        padding: 10px 6px;
        text-align: center;
        color: #ffffff;
    }
    .idx-up { background: linear-gradient(180deg, #15803d, #166534); border: 1px solid #22c55e; }
    .idx-down { background: linear-gradient(180deg, #b91c1c, #991b1b); border: 1px solid #ef4444; }
    .idx-flat { background: #1e2329; border: 1px solid #2b3139; }
    .idx-name { font-size: 12px; font-weight: 600; opacity: 0.9; }
    .idx-price { font-size: 19px; font-weight: 800; margin: 2px 0; }
    .idx-chg { font-size: 11px; font-weight: 600; white-space: nowrap; }

    /* 庫存損益雙欄總覽卡 */
    .pnl-box {
        background-color: #161a1e;
        border: 1px solid #2b3139;
        border-radius: 10px;
        display: flex;
        justify-content: space-around;
        padding: 14px 8px;
        margin: 10px 0 14px 0;
    }
    .pnl-col { text-align: center; flex: 1; }
    .pnl-divider { width: 1px; background-color: #2b3139; }
    .pnl-val { font-size: 22px; font-weight: 800; }
    .pnl-lbl { font-size: 12px; color: #848e9c; margin-top: 4px; }

    /* 券商標準三欄條列式清單 */
    .stock-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 13px 10px;
        border-bottom: 1px solid #1e2329;
        background-color: #111418;
        transition: background 0.15s;
    }
    .stock-row:hover { background-color: #181c22; }
    .row-left { flex: 1.2; min-width: 0; }
    .row-mid { flex: 1; text-align: right; padding-right: 10px; }
    .row-right { flex: 1.15; text-align: right; }

    .us-tag {
        display: inline-block;
        background-color: #dc2626;
        color: #ffffff;
        font-size: 10px;
        font-weight: 800;
        padding: 1px 4px;
        border-radius: 3px;
        margin-right: 5px;
        vertical-align: middle;
    }
    .sym-text { font-size: 15px; font-weight: 700; color: #ffffff; vertical-align: middle; }
    .sub-text { font-size: 11px; color: #848e9c; margin-top: 3px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .price-text { font-size: 16px; font-weight: 700; }
    .chg-text { font-size: 11px; font-weight: 600; margin-top: 2px; white-space: nowrap; }

    /* 美股習慣：綠漲紅跌 */
    .up { color: #22c55e; }
    .down { color: #ef4444; }
    .neutral { color: #9ca3af; }

    /* 評級小標籤 */
    .pill {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
    .pill-green { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(34,197,94,0.4); }
    .pill-yellow { background: rgba(245,158,11,0.18); color: #fbbf24; border: 1px solid rgba(245,158,11,0.4); }
    .pill-gray { background: rgba(156,163,175,0.18); color: #d1d5db; border: 1px solid rgba(156,163,175,0.4); }
    .pill-red { background: rgba(239,68,68,0.18); color: #f87171; border: 1px solid rgba(239,68,68,0.4); }

    /* 數據明細列 */
    .kv-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 12px;
        border-bottom: 1px solid #1e2329;
        background: #111418;
    }
    .kv-key { font-size: 13px; color: #eaecef; font-weight: 600; }
    .kv-hint { font-size: 11px; color: #848e9c; margin-top: 2px; }
    .kv-val { font-size: 14px; font-weight: 700; color: #ffffff; text-align: right; white-space: nowrap; margin-left: 10px; }

    /* 手機窄螢幕專屬微調 */
    @media (max-width: 640px) {
        .block-container {
            padding-top: 4.2rem !important;
            padding-left: 0.6rem !important;
            padding-right: 0.6rem !important;
        }
        .idx-price { font-size: 16px; }
        .idx-chg { font-size: 10px; }
        .pnl-val { font-size: 19px; }
        .price-text { font-size: 14px; }
        .sym-text { font-size: 14px; }
        .sub-text { font-size: 10px; }
        .stock-row { padding: 11px 6px; }
    }
</style>
""", unsafe_allow_html=True)

# --- 輔助函式 ---
def fmt_num(val, is_pct=False, is_currency=False, decimals=2):
    if val is None or pd.isna(val): return "N/A"
    try: val = float(val)
    except (ValueError, TypeError): return "N/A"
    if is_pct: return f"{val * 100:.{decimals}f}%"
    if is_currency:
        sign = "-" if val < 0 else ""
        av = abs(val)
        if av >= 1e12: return f"{sign}\${av / 1e12:.2f}T"
        if av >= 1e9: return f"{sign}\${av / 1e9:.2f}B"
        if av >= 1e6: return f"{sign}\${av / 1e6:.2f}M"
        return f"{sign}\${av:,.2f}"
    return f"{val:.{decimals}f}"

def fmt_signed_usd(val, decimals=2):
    if val >= 0:
        return f"+\${val:,.{decimals}f}"
    return f"-\${abs(val):,.{decimals}f}"

def get_pill_html(verdict):
    if "強力買入" in verdict: return f'<span class="pill pill-green">{verdict}</span>'
    if "偏向買入" in verdict: return f'<span class="pill pill-yellow">{verdict}</span>'
    if "賣出" in verdict or "迴避" in verdict: return f'<span class="pill pill-red">{verdict}</span>'
    return f'<span class="pill pill-gray">{verdict}</span>'

def render_gauge_svg(score, verdict):
    pct = max(0, min(100, score))
    dash = int(pct * 2.51)
    color = "#22c55e" if score >= 75 else ("#fbbf24" if score >= 60 else ("#9ca3af" if score >= 45 else "#ef4444"))
    return f"""
    <div style="text-align:center; background:#161a1e; border:1px solid #2b3139; border-radius:12px; padding:16px 12px; margin-bottom:14px;">
        <svg viewBox="0 0 200 115" width="210" height="120">
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#2b3139" stroke-width="16" stroke-linecap="round"/>
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round"
                  stroke-dasharray="{dash} 252"/>
            <text x="100" y="80" text-anchor="middle" fill="#ffffff" font-size="30" font-weight="800">{score}</text>
            <text x="100" y="100" text-anchor="middle" fill="#848e9c" font-size="12">估值綜合評分 / 100</text>
        </svg>
        <div style="margin-top:4px;">{get_pill_html(verdict)}</div>
    </div>
    """

# --- 抓取美股三大指數 (快取 10 分鐘) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_indices():
    indices = [("DIA", "道瓊 DIA"), ("SPY", "標普 SPY"), ("QQQ", "納指 QQQ")]
    out = []
    for sym, label in indices:
        try:
            t = yf.Ticker(sym)
            info = t.info
            price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
            prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
            chg = (price - prev) if (price and prev) else 0.0
            chg_pct = (chg / prev * 100) if (prev and prev > 0) else 0.0
            out.append({"label": label, "price": price, "chg": chg, "chg_pct": chg_pct})
        except Exception:
            out.append({"label": label, "price": None, "chg": 0.0, "chg_pct": 0.0})
    return out

# --- 核心分析引擎 (快取 30 分鐘) ---
@st.cache_data(ttl=1800, show_spinner=False)
def analyze_stock_data(ticker_symbol):
    symbol = ticker_symbol.strip().upper()
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
        if not info or price is None:
            return {"error": f"找不到 {symbol} 的有效報價數據"}
    except Exception as e:
        return {"error": f"抓取 {symbol} 時發生錯誤: {e}"}

    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose") or price
    day_chg = price - prev_close
    day_chg_pct = (day_chg / prev_close * 100) if prev_close else 0.0

    quote_type = info.get("quoteType", "EQUITY")
    name = info.get("shortName", symbol)
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
    mcap = info.get("marketCap")

    high_52w = info.get("fiftyTwoWeekHigh")
    low_52w = info.get("fiftyTwoWeekLow")
    pct_from_high = ((price - high_52w) / high_52w) if (price and high_52w) else None

    pe_ttm = info.get("trailingPE")
    pe_fwd = info.get("forwardPE")
    peg = info.get("pegRatio") or info.get("trailingPegRatio")
    ps_ttm = info.get("priceToSalesTrailing12Months")
    pb = info.get("priceToBook")
    ev_sales = info.get("enterpriseToRevenue")
    ev_ebitda = info.get("enterpriseToEbitda")

    revenue = info.get("totalRevenue")
    net_income = info.get("netIncomeToCommon")
    op_margin = info.get("operatingMargins")
    gross_margin = info.get("grossMargins")
    profit_margin = info.get("profitMargins")
    op_income = (revenue * op_margin) if (revenue and op_margin is not None) else None
    eps_ttm = info.get("trailingEps")
    eps_fwd = info.get("forwardEps")
    fcf = info.get("freeCashflow")
    ocf = info.get("operatingCashflow")
    roa = info.get("returnOnAssets")
    roe = info.get("returnOnEquity")
    rev_growth = info.get("revenueGrowth")

    div_rate = info.get("dividendRate")
    div_yield = (div_rate / price) if (div_rate and price) else info.get("trailingAnnualDividendYield")
    payout_ratio = info.get("payoutRatio")
    debt_to_equity = info.get("debtToEquity")
    current_ratio = info.get("currentRatio")
    beta = info.get("beta")

    fcf_margin = (fcf / revenue) if (fcf is not None and revenue) else None
    p_fcf = (mcap / fcf) if (mcap and fcf and fcf > 0) else None
    p_ocf = (mcap / ocf) if (mcap and ocf and ocf > 0) else None

    capex = None
    try:
        cf = stock.cashflow
        if cf is not None and not cf.empty and "Capital Expenditure" in cf.index:
            capex = float(cf.loc["Capital Expenditure"].iloc[0])
    except Exception:
        pass

    if quote_type == "ETF": model_type = "ETF"
    elif sector == "Financial Services": model_type = "金融 / 銀行"
    elif sector == "Real Estate": model_type = "REITs / 房地產"
    elif sector in ["Healthcare", "Consumer Defensive", "Utilities", "Industrials", "Energy"]: model_type = "防禦 / 價值股"
    else: model_type = "科技 / 成長股"

    score, reasons, warnings = 0, [], []

    if model_type == "ETF":
        score = 50
        warnings.append("ETF 標的，財報估值模型不適用")
    elif model_type == "金融 / 銀行":
        if pb is not None and pb > 0:
            if pb < 1.3: score += 25; reasons.append(f"市淨率 P/B ({pb:.2f}x) 低估")
            elif pb < 2.0: score += 18; reasons.append(f"市淨率 P/B ({pb:.2f}x) 合理")
            elif pb < 3.0: score += 10
            else: score += 4; warnings.append(f"金融股 P/B ({pb:.2f}x) 偏高")
        if pe_fwd is not None and pe_fwd > 0:
            if pe_fwd < 12: score += 20; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 具吸引力")
            elif pe_fwd < 16: score += 14
            elif pe_fwd < 22: score += 8
            else: score += 3; warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 偏高")
        if roe is not None:
            if roe > 0.14: score += 25; reasons.append(f"ROE 高達 {roe*100:.1f}%")
            elif roe > 0.10: score += 18
            elif roe > 0.06: score += 10
            else: warnings.append(f"ROE 偏低 ({roe*100:.1f}%)")
        if roa is not None:
            score += 10 if roa > 0.012 else (6 if roa > 0.008 else 2)
        if div_yield is not None and div_yield > 0.025: score += 6; reasons.append(f"股息率 {div_yield*100:.2f}%")
        elif div_yield is not None and div_yield > 0.01: score += 3
        if payout_ratio is not None and 0 < payout_ratio < 0.60: score += 4
        elif payout_ratio is not None and payout_ratio >= 0.75: warnings.append(f"派息比率偏高 ({payout_ratio*100:.0f}%)")
        score += (10 if beta < 1.15 else (6 if beta < 1.4 else 2)) if beta is not None else 5

    elif model_type == "REITs / 房地產":
        if div_yield is not None:
            if div_yield >= 0.05: score += 30; reasons.append(f"股息率達 {div_yield*100:.2f}%，收息吸引")
            elif div_yield >= 0.035: score += 22; reasons.append(f"股息率 {div_yield*100:.2f}% 穩健")
            elif div_yield >= 0.02: score += 12
            else: score += 4; warnings.append("REITs 股息率偏低")
        if p_ocf is not None:
            if p_ocf < 14: score += 25; reasons.append(f"P/OCF ({p_ocf:.1f}x) 便宜")
            elif p_ocf < 18: score += 18
            elif p_ocf < 24: score += 10
            else: score += 4; warnings.append(f"P/OCF ({p_ocf:.1f}x) 偏貴")
        if pb is not None and pb > 0:
            score += 15 if pb < 1.5 else (10 if pb < 2.2 else 4)
        if op_margin is not None and op_margin > 0.25: score += 10
        elif op_margin is not None and op_margin > 0.15: score += 6
        if debt_to_equity is not None:
            if debt_to_equity < 100: score += 10
            elif debt_to_equity < 160: score += 6
            else: score += 2; warnings.append(f"負債比偏高 ({debt_to_equity:.0f}%)")
        else: score += 5
        score += (10 if beta < 0.95 else (6 if beta < 1.2 else 2)) if beta is not None else 5

    elif model_type == "防禦 / 價值股":
        if pe_fwd is not None and pe_fwd > 0:
            if pe_fwd < 16: score += 20; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 具安全邊際")
            elif pe_fwd < 22: score += 14
            elif pe_fwd < 28: score += 7
            else: score += 2; warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 偏高")
        if ev_ebitda is not None and ev_ebitda > 0:
            score += 10 if ev_ebitda < 13 else (6 if ev_ebitda < 18 else 2)
        if p_fcf is not None:
            score += 10 if p_fcf < 18 else (6 if p_fcf < 25 else 2)
        if fcf_margin is not None:
            if fcf_margin > 0.12: score += 13; reasons.append(f"FCF Margin {fcf_margin*100:.1f}% 造血穩健")
            elif fcf_margin > 0.05: score += 8
            elif fcf_margin > 0: score += 3
            else: warnings.append("自由現金流利潤率為負")
        if roe is not None:
            score += 12 if roe > 0.15 else (7 if roe > 0.08 else 0)
        if div_yield is not None and div_yield >= 0.03: score += 10; reasons.append(f"股息率 {div_yield*100:.2f}%")
        elif div_yield is not None and div_yield >= 0.015: score += 6
        if payout_ratio is not None and 0 < payout_ratio < 0.75: score += 5
        elif payout_ratio is not None and payout_ratio >= 0.90: warnings.append("派息比率過高，留意減息風險")
        if rev_growth is not None and rev_growth > 0.03: score += 5
        if net_income is not None and net_income > 0: score += 5
        score += (10 if beta < 0.9 else (6 if beta < 1.2 else 2)) if beta is not None else 5

    else:
        if pe_fwd is not None and pe_fwd > 0:
            if pe_fwd < 18: score += 12; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 極具吸引力")
            elif pe_fwd < 25: score += 8; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 合理")
            elif pe_fwd < 35: score += 4
            else: warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 偏高")
        else: warnings.append("缺乏正向預測盈利")
        if peg is not None and peg > 0:
            if peg < 1.2: score += 10; reasons.append(f"PEG ({peg:.2f}) 成長性被低估")
            elif peg < 2.0: score += 6
            else: score += 2; warnings.append(f"PEG ({peg:.2f}) 成長溢價偏貴")
        else: score += 4
        if ev_ebitda is not None and ev_ebitda > 0:
            score += 9 if ev_ebitda < 15 else (5 if ev_ebitda < 25 else 1)
        if p_fcf is not None:
            if p_fcf < 20: score += 9; reasons.append(f"Price/FCF ({p_fcf:.1f}x) 現金流回報優異")
            elif p_fcf < 30: score += 5
            else: score += 2
        else: warnings.append("自由現金流為負數")
        if fcf_margin is not None:
            if fcf_margin > 0.15: score += 12; reasons.append(f"FCF Margin {fcf_margin*100:.1f}% 造血力極強")
            elif fcf_margin > 0.05: score += 7
            elif fcf_margin > 0: score += 3
            else: warnings.append("自由現金流利潤率為負")
        if roa is not None:
            if roa > 0.10: score += 10; reasons.append(f"ROA {roa*100:.1f}% 資產效率極高")
            elif roa > 0.05: score += 6
            elif roa > 0: score += 2
        if net_income is not None and net_
