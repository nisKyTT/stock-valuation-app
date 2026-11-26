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

# --- 券商級深色 App 風格 CSS (桌面與手機 RWD 優化) ---
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

    /* 權威新聞卡片 */
    .news-card {
        display: block;
        text-decoration: none !important;
        background: #111418;
        border-bottom: 1px solid #1e2329;
        padding: 13px 14px;
        transition: background 0.15s;
    }
    .news-card:hover { background: #181c22; }
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
        margin-bottom: 7px;
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
        if av >= 1e12: return f"{sign}\${av / 1e12:.2f}T"
        if av >= 1e9: return f"{sign}\${av / 1e9:.2f}B"
        if av >= 1e6: return f"{sign}\${av / 1e6:.2f}M"
        return f"{sign}\${av:,.2f}"
    return f"{val:.{decimals}f}"

def fmt_signed_usd(val, decimals=2):
    if val >= 0: return f"+\${val:,.{decimals}f}"
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

# --- 官方 Google Translate 免費 API (繁體中文) ---
@st.cache_data(ttl=3600, show_spinner=False)
def translate_to_zh_tw(text):
    if not text: return text
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {"client": "gtx", "sl": "auto", "tl": "zh-TW", "dt": "t", "q": text}
        req_url = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(req_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=5) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            translated = "".join([segment[0] for segment in res_json[0] if segment[0]])
            return translated if translated else text
    except Exception:
        return text

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
    html = '<div style="border:1px solid #2b3139; border-radius:10px; overflow:hidden;">'
    for n in news_items:
        sym_badge = f'<span class="us-tag">{n["symbol"]}</span>' if show_symbol else ""
        major_badge = '<span class="pill pill-red">🔥 重大影響</span>' if n["is_major"] else '<span class="pill pill-gray">市場動態</span>'
        pub_badge = f'<span class="pill pill-blue">{n["publisher"]}</span>'
        tag_html = "".join([f'<span class="pill pill-yellow">{t}</span>' for t in n["tags"]])
        html += f"""
        <a href="{n['link']}" target="_blank" class="news-card">
            <div class="news-title-zh">{sym_badge}{n['title_zh']}</div>
            <div class="news-title-en">{n['title_en']}</div>
            <div class="news-meta">
                {major_badge}
                {pub_badge}
                {tag_html}
                <span>{n['date']}</span>
            </div>
        </a>"""
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# --- 抓取美股三大指數 (含多重備援) ---
@st.cache_data(ttl=600, show_spinner=False)
def fetch_indices():
    indices = [("DIA", "道瓊 DIA"), ("SPY", "標普 SPY"), ("QQQ", "納指 QQQ")]
    out = []
    for sym, label in indices:
        price, prev = None, None
        try:
            t = yf.Ticker(sym)
            # 優先從 fast_info 取得最新即時價
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

    # 多重備援獲取股價
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
        return {"error": f"找不到 {symbol} 的有效報價數據，可能因連線頻率受限，請稍候再試。"}

    prev_close = prev_close or price
    day_chg = price - prev_close
    day_chg_pct = (day_chg / prev_close * 100) if prev_close else 0.0

    quote_type = info.get("quoteType", "EQUITY")
    name = info.get("shortName") or symbol
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
