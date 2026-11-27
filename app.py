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
    page_title="美股看盤與估值 App (雙引擎版)",
    page_icon="📈",
    layout="wide"
)

# --- 安全讀取 Finnhub API Key ---
def get_finnhub_key():
    try:
        return st.secrets.get("FINNHUB_API_KEY", "").strip()
    except Exception:
        return ""

FINNHUB_KEY = get_finnhub_key()

# --- 高可讀性券商級深色 App 風格 CSS ---
st.markdown("""
<style>
    .stApp { background-color: #0b0e11; color: #f1f5f9; }
    .block-container {
        padding-top: 3.6rem !important;
        padding-bottom: 6rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 980px;
    }

    /* 分頁導覽列 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        border-bottom: 1px solid #262d38;
        justify-content: space-around;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1; height: 46px; font-size: 15px; font-weight: 600;
        color: #94a3b8; background: transparent;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom: 2px solid #ef4444 !important;
    }

    /* 頂部大盤指數三欄並排網格 */
    .idx-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 14px; }
    .idx-card { border-radius: 12px; padding: 12px 8px; text-align: center; color: #ffffff; }
    .idx-up { background: linear-gradient(180deg, #15803d, #14532d); border: 1px solid #22c55e; }
    .idx-down { background: linear-gradient(180deg, #b91c1c, #7f1d1d); border: 1px solid #ef4444; }
    .idx-flat { background: #1a2029; border: 1px solid #2d3748; }
    .idx-name { font-size: 13px; font-weight: 700; opacity: 0.95; }
    .idx-price { font-size: 21px; font-weight: 800; margin: 3px 0; letter-spacing: 0.3px; }
    .idx-chg { font-size: 13px; font-weight: 600; white-space: nowrap; }

    /* 庫存損益雙欄總覽卡 */
    .pnl-box {
        background-color: #14181f; border: 1px solid #262d38; border-radius: 12px;
        display: flex; justify-content: space-around; padding: 16px 10px; margin: 12px 0 16px 0;
    }
    .pnl-col { text-align: center; flex: 1; }
    .pnl-divider { width: 1px; background-color: #262d38; }
    .pnl-val { font-size: 24px; font-weight: 800; }
    .pnl-lbl { font-size: 13.5px; color: #cbd5e1; margin-top: 5px; font-weight: 500; }

    /* 合理價三欄卡片 */
    .fv-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 16px; }
    .fv-card {
        background: #14181f; border: 1px solid #262d38; border-radius: 12px;
        padding: 13px 10px; text-align: center;
    }
    .fv-lbl { font-size: 13px; color: #cbd5e1; font-weight: 600; }
    .fv-val { font-size: 20px; font-weight: 800; color: #ffffff; margin-top: 5px; }

    /* 現代化個股 / 庫存卡片 (高可讀性雙層設計) */
    .stock-card {
        background-color: #14181f;
        border: 1px solid #262d38;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        transition: border-color 0.2s, background 0.15s;
    }
    .stock-card:hover {
        background-color: #191f28;
        border-color: #3b4759;
    }
    .sc-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        flex-wrap: wrap;
    }
    .sc-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
    .sc-right-group { display: flex; align-items: center; gap: 22px; margin-left: auto; }
    .sc-price-block { text-align: right; }
    .sc-pnl-block { text-align: right; min-width: 96px; }

    .us-tag {
        display: inline-block; background-color: #dc2626; color: #ffffff;
        font-size: 11px; font-weight: 800; padding: 2px 6px; border-radius: 4px;
        vertical-align: middle; letter-spacing: 0.5px;
    }
    .rank-tag {
        display: inline-block; background-color: #1e293b; color: #e2e8f0;
        font-size: 12px; font-weight: 700; padding: 2px 7px; border-radius: 5px;
        border: 1px solid #334155;
    }
    .sym-text { font-size: 18px; font-weight: 800; color: #ffffff; vertical-align: middle; }
    .name-sub { font-size: 13px; color: #cbd5e1; margin-left: 2px; }
    .price-text { font-size: 19px; font-weight: 800; line-height: 1.2; }
    .chg-text { font-size: 13.5px; font-weight: 600; margin-top: 3px; white-space: nowrap; }

    /* 底部圖示資訊晶片列 (取代難讀灰色小字) */
    .sc-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
        padding-top: 10px;
        border-top: 1px solid #222934;
    }
    .info-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        background-color: #1c222d;
        border: 1px solid #2c3544;
        border-radius: 7px;
        padding: 4px 10px;
        font-size: 13px;
        color: #e2e8f0;
        line-height: 1.3;
    }
    .chip-lbl { color: #94a3b8; font-weight: 500; }
    .chip-val { color: #f8fafc; font-weight: 700; }

    .up { color: #4ade80; }
    .down { color: #f87171; }
    .warn-text { color: #fbbf24; }
    .neutral { color: #cbd5e1; }

    /* 評級與指令標籤 */
    .pill { display: inline-block; padding: 3px 9px; border-radius: 6px; font-size: 12.5px; font-weight: 700; }
    .pill-green { background: rgba(34,197,94,0.18); color: #4ade80; border: 1px solid rgba(34,197,94,0.45); }
    .pill-yellow { background: rgba(245,158,11,0.18); color: #fbbf24; border: 1px solid rgba(245,158,11,0.45); }
    .pill-blue { background: rgba(59,130,246,0.18); color: #60a5fa; border: 1px solid rgba(59,130,246,0.45); }
    .pill-gray { background: rgba(148,163,184,0.18); color: #e2e8f0; border: 1px solid rgba(148,163,184,0.4); }
    .pill-red { background: rgba(239,68,68,0.18); color: #f87171; border: 1px solid rgba(239,68,68,0.45); }

    /* 個股體檢：雙欄圖示指標卡片網格 */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-top: 6px;
    }
    .metric-card {
        background: #14181f;
        border: 1px solid #262d38;
        border-radius: 12px;
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        gap: 8px;
        transition: border-color 0.2s;
    }
    .metric-card:hover { border-color: #3b4759; }
    .mc-head {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
    }
    .mc-title-wrap { display: flex; align-items: center; gap: 10px; }
    .mc-icon {
        width: 34px; height: 34px;
        border-radius: 9px;
        background: #1e2633;
        border: 1px solid #2e394a;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 17px;
        flex-shrink: 0;
    }
    .mc-title { font-size: 14.5px; font-weight: 700; color: #f1f5f9; line-height: 1.25; }
    .mc-val { font-size: 19px; font-weight: 800; color: #ffffff; text-align: right; white-space: nowrap; }
    .mc-hint {
        font-size: 13px;
        color: #cbd5e1;
        line-height: 1.45;
        background: #10141a;
        border-radius: 7px;
        padding: 7px 10px;
        border-left: 3px solid #334155;
    }

    /* 權威新聞可點擊卡片 (直連原文) */
    .news-link-card {
        display: block; text-decoration: none !important; background: #14181f;
        border: 1px solid #262d38; border-radius: 12px; padding: 14px 16px;
        margin-bottom: 10px; transition: border-color 0.2s, background 0.15s;
    }
    .news-link-card:hover { background: #191f28; border-color: #3b82f6; }
    .news-title-zh { font-size: 16px; font-weight: 700; color: #f8fafc; line-height: 1.45; margin-bottom: 5px; }
    .news-title-en { font-size: 13px; color: #94a3b8; line-height: 1.4; margin-bottom: 9px; }
    .news-meta { font-size: 12.5px; color: #cbd5e1; display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }

    @media (max-width: 680px) {
        .block-container { padding-top: 4.2rem !important; padding-left: 0.65rem !important; padding-right: 0.65rem !important; }
        .metric-grid { grid-template-columns: 1fr; }
        .fv-grid { grid-template-columns: 1fr; gap: 8px; }
        .idx-price { font-size: 17px; }
        .idx-chg { font-size: 11.5px; }
        .pnl-val { font-size: 20px; }
        .sc-right-group { gap: 14px; }
        .price-text { font-size: 16px; }
        .sym-text { font-size: 16px; }
        .info-chip { font-size: 12.5px; padding: 4px 8px; }
        .mc-val { font-size: 17px; }
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
    return f"+${val:,.{decimals}f}" if val >= 0 else f"-${abs(val):,.{decimals}f}"

def get_action_pill(action_text):
    if "黃金坑" in action_text or "甜美買入" in action_text:
        return f'<span class="pill pill-green">{action_text}</span>'
    if "超買" in action_text or "停利" in action_text:
        return f'<span class="pill pill-yellow">{action_text}</span>'
    if "迴避" in action_text or "偏貴" in action_text:
        return f'<span class="pill pill-red">{action_text}</span>'
    return f'<span class="pill pill-gray">{action_text}</span>'

def render_gauge_svg(score, action_text):
    pct = max(0, min(100, score))
    dash = int(pct * 2.51)
    color = "#4ade80" if score >= 75 else ("#fbbf24" if score >= 60 else ("#94a3b8" if score >= 45 else "#f87171"))
    return f"""
<div style="text-align:center; background:#14181f; border:1px solid #262d38; border-radius:12px; padding:16px 12px; margin-bottom:14px;">
<svg viewBox="0 0 200 115" width="215" height="122">
<path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#262d38" stroke-width="16" stroke-linecap="round"/>
<path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="{color}" stroke-width="16" stroke-linecap="round" stroke-dasharray="{dash} 252"/>
<text x="100" y="80" text-anchor="middle" fill="#ffffff" font-size="31" font-weight="800">{score}</text>
<text x="100" y="102" text-anchor="middle" fill="#cbd5e1" font-size="12.5">估值綜合評分 / 100</text>
</svg>
<div style="margin-top:6px;">{get_action_pill(action_text)}</div>
</div>
"""

def render_metric_grid(items):
    """將指標渲染為高可讀性的圖示雙欄卡片網格
    items: list of (icon, title, value, hint, val_class)
    """
    cards_html = '<div class="metric-grid">'
    for icon, title, val, hint, val_cls in items:
        border_accent = "#22c55e" if val_cls == "up" else ("#ef4444" if val_cls == "down" else ("#f59e0b" if val_cls == "warn-text" else "#3b82f6"))
        cards_html += (
            f'<div class="metric-card">'
            f'<div class="mc-head">'
            f'<div class="mc-title-wrap"><span class="mc-icon">{icon}</span><div class="mc-title">{title}</div></div>'
            f'<div class="mc-val {val_cls}">{val}</div>'
            f'</div>'
            f'<div class="mc-hint" style="border-left-color:{border_accent};">{hint}</div>'
            f'</div>'
        )
    cards_html += '</div>'
    st.markdown(cards_html, unsafe_allow_html=True)

# --- Finnhub 官方 API 請求工具 ---
def finnhub_get(endpoint, params):
    if not FINNHUB_KEY:
        return None
    try:
        params["token"] = FINNHUB_KEY
        url = f"https://finnhub.io/api/v1/{endpoint}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None

# --- 雙通道繁體中文翻譯引擎 ---
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
        req = urllib.request.Request(f"{url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            translated = "".join([seg[0] for seg in res_json[0] if seg and seg[0]])
            if translated: return translated
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
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
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
            try: date_str = parsedate_to_datetime(pub_date_raw).strftime("%Y-%m-%d")
            except Exception: date_str = ""
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
        sym_badge = f'<span class="us-tag" style="margin-right:6px;">{n["symbol"]}</span>' if show_symbol else ""
        major_badge = '<span class="pill pill-red">🔥 重大影響</span>' if n["is_major"] else '<span class="pill pill-gray">📰 市場動態</span>'
        pub_badge = f'<span class="pill pill-blue">{n["publisher"]}</span>'
        tag_html = "".join([f'<span class="pill pill-yellow">{t}</span>' for t in n["tags"]])
        st.markdown(
            f'<a href="{n["link"]}" target="_blank" class="news-link-card">'
            f'<div class="news-title-zh">{sym_badge}{n["title_zh"]} <span style="font-size:12.5px; color:#60a5fa; font-weight:600;">[原文 ↗]</span></div>'
            f'<div class="news-title-en">{n["title_en"]}</div>'
            f'<div class="news-meta">{major_badge}{pub_badge}{tag_html}<span>📅 {n["date"]}</span></div>'
            f'</a>',
            unsafe_allow_html=True
        )

# --- 抓取美股三大指數 (Finnhub 優先 + yfinance 備援) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_indices():
    indices = [("DIA", "道瓊 DIA"), ("SPY", "標普 SPY"), ("QQQ", "納指 QQQ")]
    out = []
    for sym, label in indices:
        price, prev, chg, chg_pct = None, None, 0.0, 0.0
        fq = finnhub_get("quote", {"symbol": sym})
        if fq and fq.get("c"):
            price = float(fq["c"])
            prev = float(fq.get("pc") or price)
            chg = float(fq.get("d") or (price - prev))
            chg_pct = float(fq.get("dp") or 0.0)
        else:
            try:
                t = yf.Ticker(sym)
                df = t.history(period="5d")
                if not df.empty:
                    price = float(df["Close"].iloc[-1])
                    prev = float(df["Close"].iloc[-2]) if len(df) > 1 else price
                    chg = price - prev
                    chg_pct = (chg / prev * 100) if prev else 0.0
            except Exception:
                pass
        out.append({"label": label, "price": price, "chg": chg, "chg_pct": chg_pct})
    return out

# --- 核心分析引擎：Finnhub 官方比率 + yfinance 技術面 (RSI / 200 SMA) + 合理價測算 ---
@st.cache_data(ttl=1800, show_spinner=False)
def analyze_stock_data(ticker_symbol):
    symbol = ticker_symbol.strip().upper()
    source_tag = "yfinance"

    fq = finnhub_get("quote", {"symbol": symbol})
    fm_raw = finnhub_get("stock/metric", {"symbol": symbol, "metric": "all"})
    fm = (fm_raw.get("metric") or {}) if isinstance(fm_raw, dict) else {}
    if fq and fq.get("c"):
        source_tag = "Finnhub + yfinance"

    stock = yf.Ticker(symbol)
    try:
        info = stock.info or {}
    except Exception:
        info = {}

    rsi_14, sma_200, hist_price, hist_prev = None, None, None, None
    try:
        hist = stock.history(period="1y")
        if not hist.empty and len(hist) >= 15:
            closes = hist["Close"]
            hist_price = float(closes.iloc[-1])
            hist_prev = float(closes.iloc[-2]) if len(closes) > 1 else hist_price
            sma_200 = float(closes.rolling(window=min(200, len(closes))).mean().iloc[-1])
            delta = closes.diff()
            gain = delta.clip(lower=0).rolling(window=14).mean()
            loss = (-delta.clip(upper=0)).rolling(window=14).mean()
            rs = gain / loss.replace(0, pd.NA)
            rsi_val = (100 - (100 / (1 + rs))).iloc[-1]
            if pd.notna(rsi_val):
                rsi_14 = float(rsi_val)
    except Exception:
        pass

    price = (float(fq["c"]) if (fq and fq.get("c")) else None) or info.get("currentPrice") or info.get("regularMarketPrice") or hist_price
    prev_close = (float(fq["pc"]) if (fq and fq.get("pc")) else None) or info.get("previousClose") or hist_prev or price
    if price is None:
        return {"error": f"找不到 {symbol} 的有效報價數據，請稍候再試。"}

    day_chg = price - prev_close
    day_chg_pct = (day_chg / prev_close * 100) if prev_close else 0.0

    quote_type = info.get("quoteType", "EQUITY")
    name = info.get("shortName") or symbol
    sector = info.get("sector", "Unknown")
    mcap = info.get("marketCap")

    high_52w = fm.get("52WeekHigh") or info.get("fiftyTwoWeekHigh")
    low_52w = fm.get("52WeekLow") or info.get("fiftyTwoWeekLow")
    pct_from_high = ((price - high_52w) / high_52w) if (price and high_52w) else None

    pe_ttm = fm.get("peTTM") or fm.get("peExclExtraTTM") or info.get("trailingPE")
    pe_fwd = info.get("forwardPE")
    peg = info.get("pegRatio") or info.get("trailingPegRatio")
    pb = fm.get("pbQuarterly") or fm.get("pbAnnual") or info.get("priceToBook")
    ev_ebitda = info.get("enterpriseToEbitda")
    p_fcf = fm.get("pfcfShareTTM") or ((mcap / info["freeCashflow"]) if (mcap and info.get("freeCashflow") and info["freeCashflow"] > 0) else None)
    p_ocf = (mcap / info["operatingCashflow"]) if (mcap and info.get("operatingCashflow") and info["operatingCashflow"] > 0) else None

    roe = (fm["roeTTM"] / 100.0) if fm.get("roeTTM") is not None else info.get("returnOnEquity")
    roa = (fm["roaTTM"] / 100.0) if fm.get("roaTTM") is not None else info.get("returnOnAssets")
    rev_growth = (fm["revenueGrowthTTMYoy"] / 100.0) if fm.get("revenueGrowthTTMYoy") is not None else info.get("revenueGrowth")
    div_yield = (fm["dividendYieldIndicatedAnnual"] / 100.0) if fm.get("dividendYieldIndicatedAnnual") is not None else info.get("trailingAnnualDividendYield")
    beta = fm.get("beta") or info.get("beta")

    revenue = info.get("totalRevenue")
    fcf = info.get("freeCashflow")
    fcf_margin = (fcf / revenue) if (fcf is not None and revenue) else None
    eps_ttm = fm.get("epsTTM") or info.get("trailingEps")
    eps_fwd = info.get("forwardEps")
    net_income = info.get("netIncomeToCommon")

    if quote_type == "ETF": model_type = "ETF"
    elif sector == "Financial Services": model_type = "金融 / 銀行"
    elif sector == "Real Estate": model_type = "REITs / 房地產"
    elif sector in ["Healthcare", "Consumer Defensive", "Utilities", "Industrials", "Energy"]: model_type = "防禦 / 價值股"
    else: model_type = "科技 / 成長股"

    # 內在合理價值推導
    fair_value = None
    eps_base = eps_fwd if (eps_fwd and eps_fwd > 0) else (eps_ttm if (eps_ttm and eps_ttm > 0) else None)
    if model_type == "科技 / 成長股" and eps_base:
        g_factor = min(0.30, max(0.0, rev_growth or 0.10))
        fair_pe = min(30.0, max(18.0, 16.0 + g_factor * 45.0))
        fair_value = eps_base * fair_pe
    elif model_type == "金融 / 銀行" and eps_base:
        fair_value = eps_base * 13.5
    elif model_type == "防禦 / 價值股" and eps_base:
        fair_value = eps_base * 18.0
    elif model_type == "REITs / 房地產" and div_yield and div_yield > 0:
        fair_value = (price * div_yield) / 0.048

    buy_price = (fair_value * 0.85) if fair_value else None
    sell_price = (fair_value * 1.15) if fair_value else None

    # 綜合評分引擎
    score, reasons, warnings = 0, [], []
    if model_type == "ETF":
        score = 50
        warnings.append("ETF 標的，財報估值模型不適用")
    elif model_type == "金融 / 銀行":
        if pb and pb > 0:
            if pb < 1.3: score += 25; reasons.append(f"P/B ({pb:.2f}x) 低估")
            elif pb < 2.0: score += 18; reasons.append(f"P/B ({pb:.2f}x) 合理")
            elif pb < 3.0: score += 10
            else: score += 4; warnings.append(f"金融股 P/B ({pb:.2f}x) 偏高")
        if pe_fwd and pe_fwd > 0:
            if pe_fwd < 12: score += 20; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 便宜")
            elif pe_fwd < 16: score += 14
            else: score += 6
        if roe is not None:
            if roe > 0.14: score += 25; reasons.append(f"ROE 高達 {roe*100:.1f}%")
            elif roe > 0.10: score += 18
            else: score += 8
        if roa is not None: score += 10 if roa > 0.012 else (6 if roa > 0.008 else 2)
        if div_yield and div_yield > 0.025: score += 10; reasons.append(f"股息率 {div_yield*100:.2f}%")
        elif div_yield and div_yield > 0.01: score += 5
        score += (10 if beta < 1.15 else 5) if beta else 5

    elif model_type == "REITs / 房地產":
        if div_yield:
            if div_yield >= 0.05: score += 35; reasons.append(f"股息率達 {div_yield*100:.2f}%，收息吸引")
            elif div_yield >= 0.035: score += 25; reasons.append(f"股息率 {div_yield*100:.2f}% 穩健")
            else: score += 10; warnings.append("REITs 股息率偏低")
        if p_ocf:
            if p_ocf < 15: score += 25; reasons.append(f"P/OCF ({p_ocf:.1f}x) 具安全邊際")
            elif p_ocf < 20: score += 16
            else: score += 6
        if pb and pb > 0: score += 20 if pb < 1.5 else (12 if pb < 2.2 else 5)
        score += (20 if (beta and beta < 1.0) else 10)

    elif model_type == "防禦 / 價值股":
        if pe_fwd and pe_fwd > 0:
            if pe_fwd < 16: score += 25; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 具安全邊際")
            elif pe_fwd < 22: score += 16
            else: score += 6; warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 偏高")
        if fcf_margin is not None:
            if fcf_margin > 0.12: score += 20; reasons.append(f"FCF Margin {fcf_margin*100:.1f}% 造血穩健")
            elif fcf_margin > 0.05: score += 12
        if roe is not None: score += 20 if roe > 0.15 else (12 if roe > 0.08 else 4)
        if div_yield and div_yield >= 0.03: score += 20; reasons.append(f"股息率 {div_yield*100:.2f}%")
        elif div_yield and div_yield >= 0.015: score += 10
        score += (15 if (beta and beta < 0.95) else 8)

    else:
        if pe_fwd and pe_fwd > 0:
            if pe_fwd < 20: score += 18; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 具吸引力")
            elif pe_fwd < 28: score += 12; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 合理")
            elif pe_fwd < 38: score += 6
            else: warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 偏高")
        else: warnings.append("缺乏正向預測盈利")

        if peg and 0 < peg < 1.3 and (rev_growth or 0) > 0.10:
            score += 15; reasons.append(f"PEG ({peg:.2f}) 搭配高營收成長，性價比優異")
        elif peg and 0 < peg < 2.2:
            score += 8
        else:
            score += 4

        if fcf_margin is not None:
            if fcf_margin > 0.15: score += 18; reasons.append(f"FCF Margin {fcf_margin*100:.1f}% 造血力極強")
            elif fcf_margin > 0.05: score += 10
            else: warnings.append("自由現金流利潤率偏低")
        if roa is not None:
            if roa > 0.10: score += 14; reasons.append(f"ROA {roa*100:.1f}% 資產效率極高")
            elif roa > 0.05: score += 8
        if rev_growth is not None:
            if rev_growth > 0.15: score += 15; reasons.append(f"營收高速增長 {rev_growth*100:.1f}%")
            elif rev_growth > 0.05: score += 9
            elif rev_growth < 0: warnings.append(f"營收負增長 ({rev_growth*100:.1f}%)")
        if net_income is not None and net_income > 0: score += 10
        else: warnings.append("淨利潤數據異常或虧損")
        score += (10 if (beta and beta < 1.2) else 5)

    score = min(100, max(0, score))

    if rsi_14 is not None and rsi_14 > 72:
        warnings.append(f"RSI(14) 達 {rsi_14:.1f}，短線過熱超買，切勿追高")
    if sma_200 is not None and price < sma_200:
        warnings.append(f"現價低於 200 日線 (${sma_200:.2f})，處於中線空頭，建議分批限價低接")

    if model_type == "ETF":
        action_badge = "📦 ETF 配置"
    elif rsi_14 is not None and rsi_14 > 75:
        action_badge = "⚠️ 短線超買勿追"
    elif score >= 70 and buy_price and price <= buy_price and (rsi_14 is None or rsi_14 < 42):
        action_badge = "🔥 超跌黃金坑"
    elif score >= 65 and fair_value and price <= fair_value:
        action_badge = "🟢 甜美買入區"
    elif sell_price and price >= sell_price:
        action_badge = "🎯 進入停利區"
    elif score < 45:
        action_badge = "🔴 偏貴 / 迴避"
    else:
        action_badge = "🟡 持有觀望"

    return {
        "symbol": symbol, "name": name, "model_type": model_type, "source_tag": source_tag,
        "price": price, "day_chg": day_chg, "day_chg_pct": day_chg_pct,
        "high_52w": high_52w, "low_52w": low_52w, "pct_from_high": pct_from_high,
        "pe_ttm": pe_ttm, "pe_fwd": pe_fwd, "peg": peg, "pb": pb, "ev_ebitda": ev_ebitda,
        "p_fcf": p_fcf, "p_ocf": p_ocf, "revenue": revenue, "rev_growth": rev_growth,
        "eps_ttm": eps_ttm, "eps_fwd": eps_fwd, "fcf": fcf, "fcf_margin": fcf_margin,
        "roa": roa, "roe": roe, "div_yield": div_yield, "beta": beta,
        "rsi_14": rsi_14, "sma_200": sma_200,
        "fair_value": fair_value, "buy_price": buy_price, "sell_price": sell_price,
        "score": score, "action_badge": action_badge, "reasons": reasons, "warnings": warnings
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
        idx_html += (
            f'<div class="idx-card {cls}">'
            f'<div class="idx-name">{item["label"]}</div>'
            f'<div class="idx-price">{item["price"]:.2f}</div>'
            f'<div class="idx-chg">{arrow}{abs(item["chg"]):.2f} ({item["chg_pct"]:+.2f}%)</div>'
            f'</div>'
        )
idx_html += '</div>'
st.markdown(idx_html, unsafe_allow_html=True)

if FINNHUB_KEY:
    st.markdown('<div style="font-size:13px; color:#94a3b8; margin-bottom:8px;">🟢 雙引擎已啟動：Finnhub 官方財報 API + yfinance 技術面日線</div>', unsafe_allow_html=True)
else:
    st.markdown('<div style="font-size:13px; color:#fbbf24; margin-bottom:8px;">🟡 目前為 yfinance 單引擎模式（請至 Secrets 填入 FINNHUB_API_KEY）</div>', unsafe_allow_html=True)

# ==========================================
# 主分頁導覽
# ==========================================
tab_watch, tab_detail, tab_port = st.tabs(["📊 自選排行", "🔍 個股體檢", "🔒 私人庫存"])

# ==========================================
# Tab 1: 自選組合批次排行 (圖示卡片版)
# ==========================================
with tab_watch:
    groups = {
        "全部自選 (20檔)": "GOOG, TSM, NVDA, MSFT, AMZN, META, AAPL, ASML, AMD, AVGO, VRT, V, MA, AXP, JPM, O, ABBV, TGT, MMM, VZ",
        "科技與AI核心": "GOOG, TSM, NVDA, MSFT, AMZN, META, AAPL, ASML, AMD, AVGO, VRT",
        "金融與防禦收息": "V, MA, AXP, JPM, O, ABBV, TGT, MMM, VZ"
    }
    selected_group = st.radio("選擇自選分類", list(groups.keys()), horizontal=True, label_visibility="collapsed")
    watchlist_input = st.text_input("自選代號清單（可直接增減）", value=groups[selected_group])

    if st.button("🚀 掃描並計算合理價與買賣訊號", type="primary", use_container_width=True):
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
            st.markdown(f'<div style="font-size:13.5px; color:#cbd5e1; margin:8px 0 10px 0;">已完成 <b>{len(results)}</b> 檔掃描，依綜合估值評分由高至低排列：</div>', unsafe_allow_html=True)

            for idx, r in enumerate(results, 1):
                d_cls = "up" if r["day_chg"] >= 0 else "down"
                d_arrow = "▲" if r["day_chg"] >= 0 else "▼"
                fv_str = f"${r['fair_value']:.0f}" if r["fair_value"] else "N/A"
                rsi_str = f"{r['rsi_14']:.0f}" if r["rsi_14"] else "N/A"
                rsi_cls = "up" if (r["rsi_14"] and r["rsi_14"] < 35) else ("warn-text" if (r["rsi_14"] and r["rsi_14"] > 72) else "chip-val")

                st.markdown(
                    f'<div class="stock-card">'
                    f'<div class="sc-top">'
                    f'<div class="sc-left">'
                    f'<span class="rank-tag">#{idx}</span>'
                    f'<span class="us-tag">US</span>'
                    f'<span class="sym-text">{r["symbol"]}</span>'
                    f'<span class="name-sub">{r["name"]}</span>'
                    f'</div>'
                    f'<div class="sc-right-group">'
                    f'<div class="sc-price-block">'
                    f'<div class="price-text {d_cls}">${r["price"]:.2f}</div>'
                    f'<div class="chg-text {d_cls}">{d_arrow} {abs(r["day_chg"]):.2f} ({r["day_chg_pct"]:+.2f}%)</div>'
                    f'</div>'
                    f'<div>{get_action_pill(r["action_badge"])}</div>'
                    f'</div>'
                    f'</div>'
                    f'<div class="sc-chips">'
                    f'<span class="info-chip">⭐ <span class="chip-lbl">評分</span> <span class="chip-val">{r["score"]} 分</span></span>'
                    f'<span class="info-chip">⚖️ <span class="chip-lbl">合理價</span> <span class="chip-val">{fv_str}</span></span>'
                    f'<span class="info-chip">⚡ <span class="chip-lbl">RSI</span> <span class="{rsi_cls}" style="font-weight:700;">{rsi_str}</span></span>'
                    f'<span class="info-chip">🏷️ <span class="chip-val">{r["model_type"]}</span></span>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

# ==========================================
# Tab 2: 個股深度體檢 (雙欄圖示卡片版)
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

            st.markdown(
                f'<div style="display:flex; justify-content:space-between; align-items:center; background:#14181f; border:1px solid #262d38; border-radius:12px; padding:16px 18px; margin-bottom:14px;">'
                f'<div>'
                f'<div><span class="us-tag" style="margin-right:8px;">US</span><span style="font-size:22px; font-weight:800; color:#fff;">{r["symbol"]}</span></div>'
                f'<div style="font-size:13.5px; color:#cbd5e1; margin-top:4px;">{r["name"]} · 🏷️ {r["model_type"]} ({r["source_tag"]})</div>'
                f'</div>'
                f'<div style="text-align:right;">'
                f'<div style="font-size:24px; font-weight:800;" class="{d_cls}">${r["price"]:.2f}</div>'
                f'<div class="chg-text {d_cls}">{d_arrow} {abs(r["day_chg"]):.2f} ({r["day_chg_pct"]:+.2f}%)</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

            # 內在合理價與安全邊際三欄卡
            if r["fair_value"]:
                st.markdown(
                    f'<div class="fv-grid">'
                    f'<div class="fv-card"><div class="fv-lbl">🛡️ 安全邊際買入價 (85折)</div><div class="fv-val up">${r["buy_price"]:.2f}</div></div>'
                    f'<div class="fv-card"><div class="fv-lbl">⚖️ 推導內在合理價</div><div class="fv-val">${r["fair_value"]:.2f}</div></div>'
                    f'<div class="fv-card"><div class="fv-lbl">🎯 建議分批停利價 (115折)</div><div class="fv-val warn-text">${r["sell_price"]:.2f}</div></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )

            g_col, info_col = st.columns([1, 1.4])
            with g_col:
                st.markdown(render_gauge_svg(r["score"], r["action_badge"]), unsafe_allow_html=True)
            with info_col:
                if r["reasons"]:
                    st.success("**✅ 核心優勢**\n\n" + "\n".join([f"- {x}" for x in r["reasons"]]))
                if r["warnings"]:
                    st.warning("**⚠️ 風險與技術提示**\n\n" + "\n".join([f"- {x}" for x in r["warnings"]]))
                elif not r["reasons"]:
                    st.info("各項數據表現均衡，暫無極端優勢或警示。")

            t_news, t_tech, t_val, t_prof = st.tabs(["📰 重大新聞", "📊 技術動量", "💰 估值倍數", "🏦 獲利與風險"])

            with t_news:
                st.markdown('<div style="font-size:13px; color:#cbd5e1; margin-bottom:10px;">直連全球 7 大權威外媒（標題已譯為繁體中文，點擊卡片直連英文原文）：</div>', unsafe_allow_html=True)
                with st.spinner("正在抓取權威外媒..."):
                    render_news_list(fetch_authoritative_news(r["symbol"], max_items=6), show_symbol=False)

            with t_tech:
                rsi_cls = "up" if (r["rsi_14"] and r["rsi_14"] < 35) else ("warn-text" if (r["rsi_14"] and r["rsi_14"] > 72) else "")
                sma_above = bool(r["sma_200"] and r["price"] >= r["sma_200"])
                sma_status = "🟢 站上牛熊線（中線多頭格局）" if sma_above else "🟠 跌破牛熊線（偏弱 / 築底區）"
                sma_cls = "up" if sma_above else "warn-text"
                beta_cls = "warn-text" if (r["beta"] and r["beta"] > 1.4) else ("up" if (r["beta"] and r["beta"] < 1.0) else "")

                render_metric_grid([
                    ("⚡", "RSI (14日相對強弱)", fmt_num(r["rsi_14"], decimals=1), "低於 35 為超賣黃金坑；高於 72 屬短線過熱，切勿追高。", rsi_cls),
                    ("📈", "200 日均線 (牛熊分界)", fmt_num(r["sma_200"], is_currency=True), f"目前趨勢：{sma_status}", sma_cls),
                    ("📏", "52 週價格區間", f"{fmt_num(r['low_52w'], is_currency=True)} - {fmt_num(r['high_52w'], is_currency=True)}", f"目前距離 52 週最高點：{fmt_num(r['pct_from_high'], is_pct=True)}", ""),
                    ("🌊", "Beta (波動係數)", fmt_num(r["beta"]), "小於 1.0 較抗跌；大於 1.4 波動劇烈，建議分批掛限價單。", beta_cls),
                ])

            with t_val:
                pe_cls = "up" if (r["pe_fwd"] and r["pe_fwd"] < 22) else ("warn-text" if (r["pe_fwd"] and r["pe_fwd"] > 35) else "")
                peg_cls = "up" if (r["peg"] and 0 < r["peg"] < 1.2) else ("warn-text" if (r["peg"] and r["peg"] > 2.2) else "")
                pfcf_cls = "up" if (r["p_fcf"] and r["p_fcf"] < 20) else ""

                render_metric_grid([
                    ("🔭", "Forward P/E (預測本益比)", fmt_num(r["pe_fwd"]), "一般科技股低於 25 倍屬合理區間；銀行股低於 12 倍為優。", pe_cls),
                    ("🧾", "Trailing P/E (TTM)", fmt_num(r["pe_ttm"]), "過去 12 個月真實盈利本益比（優先取自 Finnhub 數據）。", ""),
                    ("🚀", "PEG Ratio (成長性價比)", fmt_num(r["peg"]), "低於 1.2 且搭配高營收增長時，通常具備較高爆發力。", peg_cls),
                    ("💵", "Price / FCF (市現率)", fmt_num(r["p_fcf"]), "總市值 ÷ 自由現金流；低於 20 倍代表現金回報優異。", pfcf_cls),
                    ("🏛️", "Price / Book (市淨率)", fmt_num(r["pb"]), "銀行與 REITs 核心估值指標；低於 1.5 倍代表貼近資產淨值。", ""),
                ])

            with t_prof:
                fcf_cls = "up" if (r["fcf_margin"] and r["fcf_margin"] > 0.15) else ""
                rev_cls = "up" if (r["rev_growth"] and r["rev_growth"] > 0.15) else ("down" if (r["rev_growth"] and r["rev_growth"] < 0) else "")
                div_cls = "up" if (r["div_yield"] and r["div_yield"] >= 0.03) else ""

                render_metric_grid([
                    ("💧", "Levered FCF Margin", fmt_num(r["fcf_margin"], is_pct=True), "自由現金流佔總營收比例；高於 15% 代表企業造血力極強。", fcf_cls),
                    ("⚙️", "ROA / ROE (獲利效率)", f"{fmt_num(r['roa'], is_pct=True)} / {fmt_num(r['roe'], is_pct=True)}", "一般企業 ROA > 8%（銀行 > 1%）、ROE > 15% 表現優異。", ""),
                    ("📊", "總營收 & 年增率", f"{fmt_num(r['revenue'], is_currency=True)} ({fmt_num(r['rev_growth'], is_pct=True)})", "科技與成長型企業年增率高於 15% 屬於高速擴張期。", rev_cls),
                    ("💎", "EPS (TTM / Forward)", f"{fmt_num(r['eps_ttm'])} / {fmt_num(r['eps_fwd'])}", "預測 Forward EPS 高於過去 TTM，代表市場預期盈利持續增長。", ""),
                    ("🎁", "股息率 (Dividend Yield)", fmt_num(r["div_yield"], is_pct=True), "防禦型收息股 > 3%、REITs > 5% 較具現金流吸引力。", div_cls),
                ])

# ==========================================
# Tab 3: 🔒 私人庫存 (雙層圖示卡片版)
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
            "sym": sym, "price": price, "day_chg": res["day_chg"], "day_chg_pct": res["day_chg_pct"],
            "shares": shares, "avg_cost": avg_cost, "market_val": market_val,
            "pnl_usd": pnl_usd, "pnl_pct": pnl_pct, "target": target, "dist_pct": dist_pct,
            "score": res["score"], "action_badge": res["action_badge"]
        })

    if positions:
        total_pnl = total_value - total_cost
        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0.0
        pnl_cls = "up" if total_pnl >= 0 else "down"

        if hide_amounts:
            st.markdown(f'<div style="font-size:13.5px; color:#cbd5e1; margin-top:4px;">💼 共 <b>{len(positions)}</b> 檔美股 ｜ 🙈 隱私遮罩已開啟</div>', unsafe_allow_html=True)
            pnl_display = "****"
        else:
            st.markdown(f'<div style="font-size:13.5px; color:#cbd5e1; margin-top:4px;">💼 共 <b>{len(positions)}</b> 檔美股 ｜ 總成本 <b>USD ${total_cost:,.2f}</b> ｜ 現值 <b>USD ${total_value:,.2f}</b></div>', unsafe_allow_html=True)
            pnl_display = fmt_signed_usd(total_pnl, 2)

        st.markdown(
            f'<div class="pnl-box">'
            f'<div class="pnl-col"><div class="pnl-val {pnl_cls}">{pnl_display}</div><div class="pnl-lbl">未實現損益 (USD)</div></div>'
            f'<div class="pnl-divider"></div>'
            f'<div class="pnl-col"><div class="pnl-val {pnl_cls}">{total_pnl_pct:+.2f}%</div><div class="pnl-lbl">總報酬率</div></div>'
            f'</div>',
            unsafe_allow_html=True
        )

        for p in positions:
            weight_pct = (p["market_val"] / total_value * 100) if total_value > 0 else 0.0
            d_cls = "up" if p["day_chg"] >= 0 else "down"
            d_arrow = "▲" if p["day_chg"] >= 0 else "▼"
            p_cls = "up" if p["pnl_usd"] >= 0 else "down"

            cost_val_str = "****" if hide_amounts else f"${p['avg_cost']:.2f}"
            share_val_str = "** 股" if hide_amounts else f"{p['shares']:.2f} 股"
            pnl_right = "****" if hide_amounts else fmt_signed_usd(p["pnl_usd"], 1)
            target_chip = f'🎯 <span class="chip-lbl">目標</span> <span class="chip-val">${p["target"]:.0f} ({p["dist_pct"]:+.1f}%)</span>' if p["dist_pct"] is not None else '🎯 <span class="chip-lbl">無目標價</span>'

            warn_tag = '<span class="pill pill-yellow">⚠️ 集中度過高</span>' if weight_pct > 40 else ""
            tp_tag = '<span class="pill pill-green">🎯 逼近停利</span>' if (p["target"] > 0 and p["price"] >= p["target"] * 0.92) else ""

            st.markdown(
                f'<div class="stock-card">'
                f'<div class="sc-top">'
                f'<div class="sc-left">'
                f'<span class="us-tag">US</span>'
                f'<span class="sym-text">{p["sym"]}</span>'
                f'{warn_tag}{tp_tag}'
                f'</div>'
                f'<div class="sc-right-group">'
                f'<div class="sc-price-block">'
                f'<div class="price-text {d_cls}">${p["price"]:.2f}</div>'
                f'<div class="chg-text {d_cls}">{d_arrow} {abs(p["day_chg"]):.2f} ({p["day_chg_pct"]:+.2f}%)</div>'
                f'</div>'
                f'<div class="sc-pnl-block">'
                f'<div class="price-text {p_cls}">{pnl_right}</div>'
                f'<div class="chg-text {p_cls}">{p["pnl_pct"]:+.2f}%</div>'
                f'</div>'
                f'</div>'
                f'</div>'
                f'<div class="sc-chips">'
                f'<span class="info-chip">⚖️ <span class="chip-lbl">佔比</span> <span class="chip-val">{weight_pct:.0f}%</span></span>'
                f'<span class="info-chip">🏷️ <span class="chip-lbl">均價</span> <span class="chip-val">{cost_val_str}</span></span>'
                f'<span class="info-chip">📦 <span class="chip-lbl">持股</span> <span class="chip-val">{share_val_str}</span></span>'
                f'<span class="info-chip">{target_chip}</span>'
                f'<span class="info-chip">⭐ <span class="chip-lbl">估值</span> <span class="chip-val">{p["score"]} 分</span></span>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.write("")
        with st.expander("🔥 查看影響目前持倉的權威外媒重大新聞（繁體中文）", expanded=False):
            with st.spinner("正在抓取權威外媒..."):
                port_news = []
                for p in positions:
                    port_news.extend(fetch_authoritative_news(p["sym"], max_items=3))
                port_news.sort(key=lambda x: (x["is_major"], x["date"]), reverse=True)
                render_news_list(port_news[:6], show_symbol=True)
