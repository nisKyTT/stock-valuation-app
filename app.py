import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

# --- 網頁基礎設定 ---
st.set_page_config(
    page_title="美股看盤與估值 App",
    page_icon="📈",
    layout="wide"
)

# --- 券商級深色 App 風格 CSS ---
st.markdown("""
<style>
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

    /* 分頁導覽列 */
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

    /* 頂部大盤指數三欄並排網格 */
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

    .up { color: #22c55e; }
    .down { color: #ef4444; }
    .neutral { color: #9ca3af; }

    /* 評級與新聞標籤 */
    .pill {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }
    .pill-green { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(34,197,94,0.4); }
    .pill-yellow { background: rgba(245,158,11,0.18); color: #fbbf24; border: 1px solid rgba(245,158,11,0.4); }
    .pill-blue { background: rgba(59,130,246,0.18); color: #60a5fa; border: 1px solid rgba(59,130,246,0.4); }
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

    /* 權威新聞可點擊卡片 (直連原文) */
    .news-link-card {
        display: block;
        text-decoration: none !important;
        background: #111418;
        border: 1px solid #1e2329;
        border-radius: 10px;
        padding: 13px 14px;
        margin-bottom: 10px;
        transition: border-color 0.2s, background 0.15s;
    }
    .news-link-card:hover {
        background: #181c22;
        border-color: #3b82f6;
    }
    .news-title-zh {
        font-size: 15px;
        font-weight: 700;
        color: #f9fafb;
        line-height: 1.45;
        margin-bottom: 4px;
    }
    .news-title-en {
        font-size: 11px;
        color: #848e9c;
        line-height: 1.35;
        margin-bottom: 8px;
    }
    .news-meta {
        font-size: 11px;
        color: #9ca3af;
        display: flex;
        align-items: center;
        gap: 6px;
        flex-wrap: wrap;
    }

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
        if av >= 1e12: return f"{sign}${av / 1e12:.2f}T"
        if av >= 1e9: return f"{sign}${av / 1e9:.2f}B"
        if av >= 1e6: return f"{sign}${av / 1e6:.2f}M"
        return f"{sign}${av:,.2f}"
    return f"{val:.{decimals}f}"

def fmt_signed_usd(val, decimals=2):
    if val >= 0: return f"+${val:,.{decimals}f}"
    return f"-${abs(val):,.{decimals}f}"

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

# --- 雙通道穩定繁體中文翻譯引擎 ---
@st.cache_data(ttl=86400, show_spinner=False)
def translate_to_zh_tw(text):
    if not text: return text
    clean_text = text.strip()

    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(clean_text)}&langpair=en|zh-TW"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            res_txt = data.get("responseData", {}).get("translatedText", "")
            if res_txt and not res_txt.startswith("MYMEMORY WARNING"):
                return res_txt
    except Exception:
        pass

    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "en", "tl": "zh-TW", "dt": "t", "q": clean_text}
        req_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(req_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://translate.google.com/"
        })
        with urllib.request.urlopen(req, timeout=4) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            translated = "".join([seg[0] for seg in res_json[0] if seg and seg[0]])
            if translated:
                return translated
    except Exception:
        pass

    return clean_text

# --- 全球 7 大權威財經媒體抓取 ---
HIGH_IMPACT_KEYWORDS = {
    "財報/業績": ["earnings", "revenue", "guidance", "quarter", "q1", "q2", "q3", "q4", "profit", "beat", "miss", "forecast", "outlook", "sales"],
    "政策/監管": ["tariff", "trump", "fed", "rate", "antitrust", "doj", "lawsuit", "china", "export", "ban", "sanction", "chips act", "regulation", "sec"],
    "評級/目標價": ["upgrade", "downgrade", "price target", "buy rating", "sell rating", "analyst", "wall street", "overweight"],
    "AI/重大業務": ["ai", "chip", "2nm", "cloud", "nvidia", "openai", "datacenter", "capex", "acquisition", "merger", "deal", "partnership", "dividend", "buyback"]
}

@st.cache_data(ttl=900, show_spinner=False)
def fetch_authoritative_news(ticker_symbol, max_items=6):
    symbol = ticker_symbol.strip().upper()
    parsed = []
    sites = "(site:reuters.com OR site:bloomberg.com OR site:cnbc.com OR site:wsj.com OR site:ft.com OR site:barrons.com OR site:marketwatch.com)"
    query = urllib.parse.quote(f'"{symbol}" stock {sites} when:14d')
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

    try:
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        for item in root.findall(".//item")[:15]:
            raw_title = item.findtext("title", "")
            link = item.findtext("link", "#")
            pub_date_raw = item.findtext("pubDate", "")
            source_el = item.find("source")
            publisher = source_el.text if (source_el is not None and source_el.text) else "權威外媒"

            title_en = raw_title.rsplit(" - ", 1)[0].strip() if " - " in raw_title else raw_title.strip()
            try:
                date_str = parsedate_to_datetime(pub_date_raw).strftime("%Y-%m-%d")
            except Exception:
                date_str = ""

            if not title_en: continue
            t_lower = title_en.lower()
            matched_tags = [tag for tag, kws in HIGH_IMPACT_KEYWORDS.items() if any(kw in t_lower for kw in kws)]
            parsed.append({
                "symbol": symbol, "title_en": title_en, "publisher": publisher,
                "link": link, "date": date_str, "is_major": len(matched_tags) > 0, "tags": matched_tags[:2]
            })
    except Exception:
        pass

    if not parsed:
        try:
            for item in (yf.Ticker(symbol).news or [])[:8]:
                if isinstance(item, dict) and isinstance(item.get("content"), dict):
                    c = item["content"]
                    title_en = c.get("title", "")
                    publisher = (c.get("provider") or {}).get("displayName", "Yahoo Finance")
                    link = (c.get("canonicalUrl") or {}).get("url") or "#"
                    date_str = c.get("pubDate", "")[:10]
                else:
                    title_en = item.get("title", "")
                    publisher = item.get("publisher", "Yahoo Finance")
                    link = item.get("link", "#")
                    ts = item.get("providerPublishTime")
                    date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d") if ts else ""
                if not title_en: continue
                t_lower = title_en.lower()
                matched_tags = [tag for tag, kws in HIGH_IMPACT_KEYWORDS.items() if any(kw in t_lower for kw in kws)]
                parsed.append({
                    "symbol": symbol, "title_en": title_en, "publisher": publisher,
                    "link": link, "date": date_str, "is_major": len(matched_tags) > 0, "tags": matched_tags[:2]
                })
        except Exception:
            pass

    parsed.sort(key=lambda x: (x["is_major"], len(x["tags"]), x["date"]), reverse=True)
    top_news = parsed[:max_items]
    for n in top_news:
        n["title_zh"] = translate_to_zh_tw(n["title_en"])
    return top_news

def render_news_list(news_items, show_symbol=False):
    if not news_items:
        st.info("近 14 天內暫無權威財經媒體相關報導。")
        return

    for n in news_items:
        sym_badge = f'<span class="us-tag">{n["symbol"]}</span>' if show_symbol else ""
        major_badge = '<span class="pill pill-red">🔥 重大影響</span>' if n["is_major"] else '<span class="pill pill-gray">市場動態</span>'
        pub_badge = f'<span class="pill pill-blue">{n["publisher"]}</span>'
        tag_html = "".join([f'<span class="pill pill-yellow">{t}</span>' for t in n["tags"]])

        st.markdown(f"""
        <a href="{n['link']}" target="_blank" class="news-link-card">
            <div class="news-title-zh">{sym_badge}{n['title_zh']} <span style="font-size:11px; color:#60a5fa; font-weight:normal;">[外媒原文 ↗]</span></div>
            <div class="news-title-en">{n['title_en']}</div>
            <div class="news-meta">
                {major_badge}
                {pub_badge}
                {tag_html}
                <span>{n['date']}</span>
            </div>
        </a>
        """, unsafe_allow_html=True)

# --- 抓取美股三大指數 (含多重備援) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_indices():
    indices = [("DIA", "道瓊 DIA"), ("SPY", "標普 SPY"), ("QQQ", "納指 QQQ")]
    out = []
    for sym, label in indices:
        price, prev = None, None
        try:
            t = yf.Ticker(sym)
            if hasattr(t, "fast_info"):
                price = getattr(t.fast_info, "last_price", None)
                prev = getattr(t.fast_info, "previous_close", None)
            if price is None:
                info = t.info or {}
                price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
                prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
            if price is None:
                df = t.history(period="5d")
                if not df.empty:
                    price = float(df["Close"].iloc[-1])
                    prev = float(df["Close"].iloc[-2]) if len(df) > 1 else price
            chg = (price - prev) if (price and prev) else 0.0
            chg_pct = (chg / prev * 100) if (prev and prev > 0) else 0.0
            out.append({"label": label, "price": price, "chg": chg, "chg_pct": chg_pct})
        except Exception:
            out.append({"label": label, "price": None, "chg": 0.0, "chg_pct": 0.0})
    return out

# --- 核心分析引擎 (含多重防崩潰備援機制) ---
@st.cache_data(ttl=1800, show_spinner=False)
def analyze_stock_data(ticker_symbol):
    symbol = ticker_symbol.strip().upper()
    try:
        stock = yf.Ticker(symbol)
        info = stock.info or {}
    except Exception as e:
        return {"error": f"抓取 {symbol} 時發生錯誤: {e}"}

    price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("navPrice")
    prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")

    if price is None and hasattr(stock, "fast_info"):
        try:
            price = getattr(stock.fast_info, "last_price", None)
            if prev_close is None:
                prev_close = getattr(stock.fast_info, "previous_close", None)
        except Exception:
            pass

    if price is None:
        try:
            df = stock.history(period="5d")
            if not df.empty:
                price = float(df["Close"].iloc[-1])
                if prev_close is None and len(df) > 1:
                    prev_close = float(df["Close"].iloc[-2])
        except Exception:
            pass

    if price is None:
        return {"error": f"找不到 {symbol} 的有效報價數據，請稍候再試。"}

    prev_close = prev_close or price
    day_chg = price - prev_close
    day_chg_pct = (day_chg / prev_close * 100) if prev_close else 0.0

    quote_type = info.get("quoteType", "EQUITY")
    name = info.get("shortName") or symbol
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
        else: warnings.append("ROA 為負數")
        if net_income is not None and net_income > 0: score += 7
        else: warnings.append("處於淨虧損 (Net Loss)")
        if op_income is not None and op_income > 0: score += 6
        else: warnings.append("本業營業虧損 (Operating Loss)")
        if rev_growth is not None:
            if rev_growth > 0.15: score += 8; reasons.append(f"營收高速增長 {rev_growth*100:.1f}%")
            elif rev_growth > 0.05: score += 5
            elif rev_growth > 0: score += 2
            else: warnings.append(f"營收負增長 ({rev_growth*100:.1f}%)")
        if eps_fwd is not None and eps_ttm is not None and eps_ttm > 0:
            if eps_fwd > eps_ttm * 1.1: score += 7; reasons.append("預期未來 EPS 增長 > 10%")
            elif eps_fwd > eps_ttm: score += 4
        score += (10 if beta < 1.1 else (6 if beta < 1.5 else 2)) if beta is not None else 5

    if model_type == "ETF": verdict = "ETF 標的"
    elif score >= 75: verdict = "強力買入"
    elif score >= 60: verdict = "偏向買入"
    elif score >= 45: verdict = "持有觀望"
    else: verdict = "賣出迴避"

    return {
        "symbol": symbol, "name": name, "sector": sector, "industry": industry,
        "model_type": model_type, "price": price, "day_chg": day_chg, "day_chg_pct": day_chg_pct,
        "mcap": mcap, "high_52w": high_52w, "low_52w": low_52w, "pct_from_high": pct_from_high,
        "pe_ttm": pe_ttm, "pe_fwd": pe_fwd, "peg": peg, "ps_ttm": ps_ttm, "pb": pb,
        "ev_sales": ev_sales, "ev_ebitda": ev_ebitda, "p_fcf": p_fcf, "p_ocf": p_ocf,
        "revenue": revenue, "rev_growth": rev_growth, "op_income": op_income,
        "net_income": net_income, "eps_ttm": eps_ttm, "eps_fwd": eps_fwd,
        "fcf": fcf, "ocf": ocf, "capex": capex, "fcf_margin": fcf_margin,
        "gross_margin": gross_margin, "op_margin": op_margin, "profit_margin": profit_margin,
        "roa": roa, "roe": roe, "div_yield": div_yield, "payout_ratio": payout_ratio,
        "debt_to_equity": debt_to_equity, "current_ratio": current_ratio, "beta": beta,
        "score": score, "verdict": verdict, "reasons": reasons, "warnings": warnings
    }

# ==========================================
# 頂部：美股三大指數色塊
# ==========================================
idx_data = fetch_indices()
idx_html = '<div class="idx-grid">'
for item in idx_data:
    if item["price"] is not None:
        cls = "idx-up" if item["chg"] > 0 else ("idx-down" if item["chg"] < 0 else "idx-flat")
        arrow = "▲" if item["chg"] > 0 else ("▼" if item["chg"] < 0 else "")
        idx_html += f"""
        <div class="idx-card {cls}">
            <div class="idx-name">{item['label']}</div>
            <div class="idx-price">{item['price']:.2f}</div>
            <div class="idx-chg">{arrow}{abs(item['chg']):.2f} ({item['chg_pct']:+.2f}%)</div>
        </div>"""
idx_html += '</div>'
st.markdown(idx_html, unsafe_allow_html=True)

# ==========================================
# 主分頁導覽
# ==========================================
tab_watch, tab_detail, tab_port = st.tabs(["自選排行", "個股體檢", "🔒 私人庫存"])

# ==========================================
# Tab 1: 自選組合批次排行
# ==========================================
with tab_watch:
    groups = {
        "全部自選 (20檔)": "GOOG, TSM, NVDA, MSFT, AMZN, META, AAPL, ASML, AMD, AVGO, VRT, V, MA, AXP, JPM, O, ABBV, TGT, MMM, VZ",
        "科技與AI核心": "GOOG, TSM, NVDA, MSFT, AMZN, META, AAPL, ASML, AMD, AVGO, VRT",
        "金融與防禦收息": "V, MA, AXP, JPM, O, ABBV, TGT, MMM, VZ"
    }
    selected_group = st.radio("選擇自選分類", list(groups.keys()), horizontal=True, label_visibility="collapsed")
    watchlist_input = st.text_input("自選代號清單（可直接增減）", value=groups[selected_group])

    if st.button("🚀 掃描並依估值評分排序", type="primary", use_container_width=True):
        raw_tickers = watchlist_input.replace(" ", ",").split(",")
        tickers = list(dict.fromkeys([t.strip().upper() for t in raw_tickers if t.strip()]))
        results = []
        prog = st.progress(0)
        for i, t in enumerate(tickers):
            res = analyze_stock_data(t)
            if "error" not in res:
                results.append(res)
            prog.progress((i + 1) / len(tickers))
        prog.empty()

        if results:
            results.sort(key=lambda x: x["score"], reverse=True)
            st.caption(f"已完成 {len(results)} 檔掃描，依綜合估值評分由高至低排列：")

            for idx, r in enumerate(results, 1):
                d_cls = "up" if r["day_chg"] >= 0 else "down"
                d_arrow = "▲" if r["day_chg"] >= 0 else "▼"
                pe_str = f"PE {r['pe_fwd']:.1f}" if r["pe_fwd"] else "PE N/A"
                st.markdown(f"""
                <div class="stock-row">
                    <div class="row-left">
                        <div><span style="color:#848e9c; font-size:11px; margin-right:5px;">#{idx}</span><span class="us-tag">US</span><span class="sym-text">{r['symbol']}</span></div>
                        <div class="sub-text">{r['name']} · {r['model_type']}</div>
                    </div>
                    <div class="row-mid">
                        <div class="price-text {d_cls}">${r['price']:.2f}</div>
                        <div class="chg-text {d_cls}">{d_arrow}{abs(r['day_chg']):.2f} ({r['day_chg_pct']:+.2f}%)</div>
                    </div>
                    <div class="row-right">
                        <div><span style="font-size:14px; font-weight:800; color:#fff; margin-right:5px;">{r['score']}分</span>{get_pill_html(r['verdict'])}</div>
                        <div class="sub-text">{pe_str} · 距高點 {fmt_num(r['pct_from_high'], is_pct=True)}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# Tab 2: 個股深度體檢
# ==========================================
with tab_detail:
    c_in, c_btn = st.columns([4, 1])
    with c_in:
        single_ticker = st.text_input("輸入美股代號", value="TSM", label_visibility="collapsed", placeholder="輸入美股代號，例如 GOOG, TSM, JPM, O")
    with c_btn:
        st.button("🔍 查詢", type="primary", use_container_width=True)

    if single_ticker:
        r = analyze_stock_data(single_ticker)
        if "error" in r:
            st.error(r["error"])
        else:
            d_cls = "up" if r["day_chg"] >= 0 else "down"
            d_arrow = "▲" if r["day_chg"] >= 0 else "▼"

            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center; background:#161a1e; border:1px solid #2b3139; border-radius:10px; padding:14px 16px; margin-bottom:14px;">
                <div>
                    <div><span class="us-tag">US</span><span style="font-size:20px; font-weight:800; color:#fff;">{r['symbol']}</span></div>
                    <div class="sub-text">{r['name']} · {r['model_type']}</div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:22px; font-weight:800;" class="{d_cls}">${r['price']:.2f}</div>
                    <div class="chg-text {d_cls}">{d_arrow} {abs(r['day_chg']):.2f} ({r['day_chg_pct']:+.2f}%)</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            g_col, info_col = st.columns([1, 1.4])
            with g_col:
                st.markdown(render_gauge_svg(r["score"], r["verdict"]), unsafe_allow_html=True)
            with info_col:
                if r["reasons"]:
                    st.success("**✅ 核心優勢**\n\n" + "\n".join([f"- {x}" for x in r["reasons"]]))
                if r["warnings"]:
                    st.warning("**⚠️ 風險提示**\n\n" + "\n".join([f"- {x}" for x in r["warnings"]]))
                elif not r["reasons"]:
                    st.info("各項財務數據表現均衡，暫無極端優勢或紅旗警示。")

            t_news, t_val, t_prof, t_risk = st.tabs(["📰 重大新聞 (繁中)", "估值倍數", "獲利與現金流", "股息與風險"])

            def render_kv_list(items):
                html = '<div style="border:1px solid #2b3139; border-radius:10px; overflow:hidden;">'
                for k, v, hint in items:
                    html += f"""
                    <div class="kv-row">
                        <div>
                            <div class="kv-key">{k}</div>
                            <div class="kv-hint">{hint}</div>
                        </div>
                        <div class="kv-val">{v}</div>
                    </div>"""
                html += '</div>'
                st.markdown(html, unsafe_allow_html=True)

            with t_news:
                st.caption("直連全球 7 大權威外媒（已翻譯為繁體中文，點擊卡片直接直連英文原文）：")
                with st.spinner("正在抓取權威外媒並直譯為繁體中文..."):
                    news_items = fetch_authoritative_news(r["symbol"], max_items=6)
                render_news_list(news_items, show_symbol=False)

            with t_val:
                render_kv_list([
                    ("Forward P/E (預測本益比)", fmt_num(r["pe_fwd"]), "越低越安全；一般 < 20 便宜，銀行 < 12 為優"),
                    ("Trailing P/E (TTM)", fmt_num(r["pe_ttm"]), "過去12個月本益比；< 20 偏低估，> 35 偏貴"),
                    ("PEG Ratio", fmt_num(r["peg"]), "本益比 ÷ 盈利增速；< 1.2 低估，1.2–2.0 合理"),
                    ("Price / FCF (市現率)", fmt_num(r["p_fcf"]), "市值 ÷ 自由現金流；< 20 優異，檢驗真實含金量"),
                    ("EV / EBITDA", fmt_num(r["ev_ebitda"]), "企業價值倍數；< 15 便宜，適合重資產與半導體"),
                    ("Price / Book (市淨率)", fmt_num(r["pb"]), "銀行與 REITs 核心指標；< 1.5 貼近資產淨值"),
                    ("Price / OCF (REITs參考)", fmt_num(r["p_ocf"]), "營運現金流倍數 (近似 P/FFO)；REITs < 15 便宜"),
                ])

            with t_prof:
                render_kv_list([
                    ("Levered FCF Margin", fmt_num(r["fcf_margin"], is_pct=True), "自由現金流佔營收比；> 15% 造血極強"),
                    ("ROA / ROE", f"{fmt_num(r['roa'], is_pct=True)} / {fmt_num(r['roe'], is_pct=True)}", "ROA > 8%（銀行 > 1%）、ROE > 15% 為優"),
                    ("總營收 & 年增率", f"{fmt_num(r['revenue'], is_currency=True)} ({fmt_num(r['rev_growth'], is_pct=True)})", "成長股年增 > 15% 為高速增長"),
                    ("EPS (TTM / Forward)", f"{fmt_num(r['eps_ttm'])} / {fmt_num(r['eps_fwd'])}", "Forward EPS 高於 TTM 代表預期盈利成長"),
                    ("自由現金流 (FCF)", fmt_num(r["fcf"], is_currency=True), "扣除資本開支後真正可支配的現金"),
                    ("資本開支 (CapEx)", fmt_num(r["capex"], is_currency=True), "廠房與設備投入（負數代表現金流出）"),
                ])

            with t_risk:
                render_kv_list([
                    ("Beta (波動係數)", fmt_num(r["beta"]), "< 1.0 抗跌；> 1.5 波動劇烈需提高安全邊際"),
                    ("股息率 (Dividend Yield)", fmt_num(r["div_yield"], is_pct=True), "防禦股 > 3%、REITs > 5% 具吸引力"),
                    ("派息比率 (Payout Ratio)", fmt_num(r["payout_ratio"], is_pct=True), "< 70% 較安全，> 90% 須留意減息風險"),
                    ("負債權益比 (Debt/Equity)", fmt_num(r["debt_to_equity"]), "< 100% 財務穩健，> 150% 對利率敏感"),
                    ("52 週價格區間", f"{fmt_num(r['low_52w'], is_currency=True)} - {fmt_num(r['high_52w'], is_currency=True)}", f"目前距 52 週高點 {fmt_num(r['pct_from_high'], is_pct=True)}"),
                ])

# ==========================================
# Tab 3: 🔒 私人庫存
# ==========================================
with tab_port:
    default_portfolio = pd.DataFrame([
        {"股票代號": "GOOG", "持倉股數": 28.5177, "成本均價(USD)": 280.55, "目標價(USD)": 350.00},
        {"股票代號": "TSM",  "持倉股數": 4.2200,  "成本均價(USD)": 379.38, "目標價(USD)": 455.00},
    ])

    ctrl1, ctrl2 = st.columns([2, 1])
    with ctrl1:
        hide_amounts = st.toggle("🙈 隱私遮罩（隱藏金額與股數）", value=False)
    with ctrl2:
        if st.button("🔄 刷新報價", use_container_width=True):
            st.cache_data.clear()

    with st.expander("⚙️ 編輯庫存股數 / 新增試算標的", expanded=False):
        edited_df = st.data_editor(
            default_portfolio, num_rows="dynamic", use_container_width=True, hide_index=True,
            column_config={
                "股票代號": st.column_config.TextColumn("代號", required=True),
                "持倉股數": st.column_config.NumberColumn("股數", min_value=0.0, format="%.4f", required=True),
                "成本均價(USD)": st.column_config.NumberColumn("均價", min_value=0.0, format="$%.2f", required=True),
                "目標價(USD)": st.column_config.NumberColumn("目標價", min_value=0.0, format="$%.2f", required=True),
            }
        )

    positions, total_cost, total_value = [], 0.0, 0.0
    for _, row in edited_df.iterrows():
        sym = str(row["股票代號"]).strip().upper()
        shares = float(row["持倉股數"] or 0)
        avg_cost = float(row["成本均價(USD)"] or 0)
        target = float(row["目標價(USD)"] or 0)
        if not sym or shares <= 0: continue
        res = analyze_stock_data(sym)
        if "error" in res: continue

        price = float(res["price"])
        cost_basis = shares * avg_cost
        market_val = shares * price
        pnl_usd = market_val - cost_basis
        pnl_pct = (pnl_usd / cost_basis * 100) if cost_basis > 0 else 0.0
        dist_pct = ((target - price) / price * 100) if (target > 0 and price > 0) else None

        total_cost += cost_basis
        total_value += market_val
        positions.append({
            "sym": sym, "name": res["name"], "price": price, "day_chg": res["day_chg"],
            "day_chg_pct": res["day_chg_pct"], "shares": shares, "avg_cost": avg_cost,
            "pnl_usd": pnl_usd, "pnl_pct": pnl_pct, "target": target, "dist_pct": dist_pct,
            "score": res["score"], "verdict": res["verdict"]
        })

    if positions:
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
        pnl_cls = "up" if total_pnl >= 0 else "down"

        if hide_amounts:
            st.caption(f"共 {len(positions)} 檔美股 ｜ 隱私遮罩已開啟")
            pnl_display = "****"
        else:
            st.caption(f"共 {len(positions)} 檔美股，總成本 USD ${total_cost:,.2f} ｜ 現值 USD ${total_value:,.2f}")
            pnl_display = fmt_signed_usd(total_pnl, 2)

        st.markdown(f"""
        <div class="pnl-box">
            <div class="pnl-col">
                <div class="pnl-val {pnl_cls}">{pnl_display}</div>
                <div class="pnl-lbl">未實現損益 (USD)</div>
            </div>
            <div class="pnl-divider"></div>
            <div class="pnl-col">
                <div class="pnl-val {pnl_cls}">{total_pnl_pct:+.2f}%</div>
                <div class="pnl-lbl">總報酬率</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        for p in positions:
            d_cls = "up" if p["day_chg"] >= 0 else "down"
            d_arrow = "▲" if p["day_chg"] >= 0 else "▼"
            p_cls = "up" if p["pnl_usd"] >= 0 else "down"
            target_str = f"目標 ${p['target']:.0f} ({p['dist_pct']:+.1f}%)" if p["dist_pct"] is not None else "無目標價"
            sub_left = "均價 **** · **股" if hide_amounts else f"均價 ${p['avg_cost']:.2f} · {p['shares']:.2f}股"
            pnl_right = "****" if hide_amounts else fmt_signed_usd(p["pnl_usd"], 1)

            st.markdown(f"""
            <div class="stock-row">
                <div class="row-left">
                    <div><span class="us-tag">US</span><span class="sym-text">{p['sym']}</span></div>
                    <div class="sub-text">{sub_left}</div>
                </div>
                <div class="row-mid">
                    <div class="price-text {d_cls}">${p['price']:.2f}</div>
                    <div class="chg-text {d_cls}">{d_arrow}{abs(p['day_chg']):.2f} ({p['day_chg_pct']:+.2f}%)</div>
                </div>
                <div class="row-right">
                    <div class="price-text {p_cls}">{pnl_right}</div>
                    <div class="sub-text">{target_str} · {p['score']}分</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        with st.expander("🔥 查看影響目前持倉的權威外媒重大新聞（繁體中文）", expanded=False):
            with st.spinner("正在抓取 Reuters / Bloomberg / CNBC 等權威報導並翻譯..."):
                port_news = []
                for p in positions:
                    port_news.extend(fetch_authoritative_news(p["sym"], max_items=3))
                port_news.sort(key=lambda x: (x["is_major"], x["date"]), reverse=True)
                render_news_list(port_news[:6], show_symbol=True)
