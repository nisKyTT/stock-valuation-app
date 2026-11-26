import streamlit as st
import yfinance as yf
import pandas as pd

# --- 網頁基礎設定 ---
st.set_page_config(
    page_title="全行業美股估值自動分析系統",
    page_icon="📊",
    layout="wide"
)

# --- 輔助格式化函式 ---
def fmt_num(val, is_pct=False, is_currency=False, decimals=2):
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val = float(val)
    except (ValueError, TypeError):
        return "N/A"
    if is_pct:
        return f"{val * 100:.{decimals}f}%"
    if is_currency:
        if abs(val) >= 1e12:
            return f"${val / 1e12:.2f}T"
        elif abs(val) >= 1e9:
            return f"${val / 1e9:.2f}B"
        elif abs(val) >= 1e6:
            return f"${val / 1e6:.2f}M"
        return f"${val:,.2f}"
    return f"{val:.{decimals}f}"

# --- 核心分析引擎 (加入快取 30 分鐘避免重複請求) ---
@st.cache_data(ttl=1800, show_spinner=False)
def analyze_stock_data(ticker_symbol):
    symbol = ticker_symbol.strip().upper()
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        if not info or (info.get("currentPrice") is None and info.get("regularMarketPrice") is None):
            return {"error": f"找不到 {symbol} 的有效報價數據（請確認代號是否為個股）"}
    except Exception as e:
        return {"error": f"抓取 {symbol} 時發生錯誤: {e}"}

    quote_type = info.get("quoteType", "EQUITY")
    name = info.get("shortName", symbol)
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
    price = info.get("currentPrice") or info.get("regularMarketPrice")
    mcap = info.get("marketCap")

    # 52 週區間位置
    high_52w = info.get("fiftyTwoWeekHigh")
    low_52w = info.get("fiftyTwoWeekLow")
    pct_from_high = ((price - high_52w) / high_52w) if (price and high_52w) else None

    # 基礎估值倍數
    pe_ttm = info.get("trailingPE")
    pe_fwd = info.get("forwardPE")
    peg = info.get("pegRatio") or info.get("trailingPegRatio")
    ps_ttm = info.get("priceToSalesTrailing12Months")
    pb = info.get("priceToBook")
    ev_sales = info.get("enterpriseToRevenue")
    ev_ebitda = info.get("enterpriseToEbitda")

    # 獲利、現金流與成長
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

    # 股息與財務健康
    div_rate = info.get("dividendRate")
    div_yield = (div_rate / price) if (div_rate and price) else info.get("trailingAnnualDividendYield")
    payout_ratio = info.get("payoutRatio")
    debt_to_equity = info.get("debtToEquity")  # yfinance 回傳為百分比，如 120 代表 1.2x
    current_ratio = info.get("currentRatio")
    beta = info.get("beta")

    # 衍生指標
    fcf_margin = (fcf / revenue) if (fcf is not None and revenue) else None
    p_fcf = (mcap / fcf) if (mcap and fcf and fcf > 0) else None
    p_ocf = (mcap / ocf) if (mcap and ocf and ocf > 0) else None

    # 嘗試抓取最新 CapEx
    capex = None
    try:
        cf = stock.cashflow
        if cf is not None and not cf.empty and "Capital Expenditure" in cf.index:
            capex = float(cf.loc["Capital Expenditure"].iloc[0])
    except Exception:
        pass

    # --- 判斷所屬估值模型 ---
    if quote_type == "ETF":
        model_type = "ETF (僅供數據參考)"
    elif sector == "Financial Services":
        model_type = "金融 / 銀行模型"
    elif sector == "Real Estate":
        model_type = "REITs / 房地產模型"
    elif sector in ["Healthcare", "Consumer Defensive", "Utilities", "Industrials", "Energy"]:
        model_type = "防禦 / 價值股模型"
    else:
        model_type = "科技 / 成長股模型"

    # --- 多行業動態評分引擎 (滿分 100) ---
    score = 0
    reasons = []
    warnings = []

    if model_type == "ETF (僅供數據參考)":
        score = 50
        warnings.append("此標的為 ETF，財報估值模型不適用，請改看成分股與費用率")

    elif model_type == "金融 / 銀行模型":
        # 1. P/B 估值 (25分)
        if pb is not None and pb > 0:
            if pb < 1.3:
                score += 25; reasons.append(f"市淨率 P/B ({pb:.2f}x) 處於低估區間")
            elif pb < 2.0:
                score += 18; reasons.append(f"市淨率 P/B ({pb:.2f}x) 合理")
            elif pb < 3.0:
                score += 10
            else:
                score += 4; warnings.append(f"金融股 P/B ({pb:.2f}x) 偏高")
        # 2. Forward P/E (20分)
        if pe_fwd is not None and pe_fwd > 0:
            if pe_fwd < 12:
                score += 20; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 具吸引力")
            elif pe_fwd < 16:
                score += 14
            elif pe_fwd < 22:
                score += 8
            else:
                score += 3; warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 高於金融業平均")
        # 3. ROE 獲利效率 (25分)
        if roe is not None:
            if roe > 0.14:
                score += 25; reasons.append(f"ROE 高達 {roe*100:.1f}%，資本回報極佳")
            elif roe > 0.10:
                score += 18
            elif roe > 0.06:
                score += 10
            else:
                warnings.append(f"ROE 偏低 ({roe*100:.1f}%)")
        # 4. ROA (10分)
        if roa is not None:
            if roa > 0.012:
                score += 10; reasons.append(f"金融業 ROA ({roa*100:.2f}%) 表現優異")
            elif roa > 0.008:
                score += 6
            else:
                score += 2
        # 5. 股息與派息安全 (10分)
        if div_yield is not None and div_yield > 0.025:
            score += 6; reasons.append(f"股息率 {div_yield*100:.2f}% 提供良好下檔保護")
        elif div_yield is not None and div_yield > 0.01:
            score += 3
        if payout_ratio is not None and 0 < payout_ratio < 0.60:
            score += 4
        elif payout_ratio is not None and payout_ratio >= 0.75:
            warnings.append(f"派息比率偏高 ({payout_ratio*100:.0f}%)")
        # 6. 風險 Beta (10分)
        if beta is not None:
            score += 10 if beta < 1.15 else (6 if beta < 1.4 else 2)
        else:
            score += 5

    elif model_type == "REITs / 房地產模型":
        # 1. 股息率 (30分)
        if div_yield is not None:
            if div_yield >= 0.05:
                score += 30; reasons.append(f"股息率達 {div_yield*100:.2f}%，收息回報吸引")
            elif div_yield >= 0.035:
                score += 22; reasons.append(f"股息率 {div_yield*100:.2f}% 處於穩健區間")
            elif div_yield >= 0.02:
                score += 12
            else:
                score += 4; warnings.append("作為 REITs，股息率偏低")
        # 2. P/OCF 近似 P/FFO (25分)
        if p_ocf is not None:
            if p_ocf < 14:
                score += 25; reasons.append(f"營運現金流倍數 P/OCF ({p_ocf:.1f}x) 估值便宜")
            elif p_ocf < 18:
                score += 18
            elif p_ocf < 24:
                score += 10
            else:
                score += 4; warnings.append(f"P/OCF ({p_ocf:.1f}x) 估值偏貴")
        else:
            warnings.append("營運現金流數據不足或為負")
        # 3. P/B (15分)
        if pb is not None and pb > 0:
            if pb < 1.5:
                score += 15; reasons.append(f"P/B ({pb:.2f}x) 貼近資產淨值")
            elif pb < 2.2:
                score += 10
            else:
                score += 4
        # 4. 營業利潤率 (10分)
        if op_margin is not None and op_margin > 0.25:
            score += 10
        elif op_margin is not None and op_margin > 0.15:
            score += 6
        else:
            warnings.append("房地產本業利潤率偏低")
        # 5. 負債控管 D/E (10分)
        if debt_to_equity is not None:
            if debt_to_equity < 100:
                score += 10; reasons.append(f"負債比率 ({debt_to_equity:.0f}%) 控管穩健")
            elif debt_to_equity < 160:
                score += 6
            else:
                score += 2; warnings.append(f"負債比率較高 ({debt_to_equity:.0f}%)，對利率敏感")
        else:
            score += 5
        # 6. 波動 Beta (10分)
        if beta is not None:
            score += 10 if beta < 0.95 else (6 if beta < 1.2 else 2)
        else:
            score += 5

    elif model_type == "防禦 / 價值股模型":
        # 1. Forward P/E (20分)
        if pe_fwd is not None and pe_fwd > 0:
            if pe_fwd < 16:
                score += 20; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 估值具安全邊際")
            elif pe_fwd < 22:
                score += 14
            elif pe_fwd < 28:
                score += 7
            else:
                score += 2; warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 對價值股偏高")
        else:
            warnings.append("缺乏正向預測盈利")
        # 2. EV/EBITDA & P/FCF (20分)
        if ev_ebitda is not None and ev_ebitda > 0:
            score += 10 if ev_ebitda < 13 else (6 if ev_ebitda < 18 else 2)
        if p_fcf is not None:
            if p_fcf < 18:
                score += 10; reasons.append(f"Price/FCF ({p_fcf:.1f}x) 現金流回報優異")
            elif p_fcf < 25:
                score += 6
            else:
                score += 2
        else:
            warnings.append("自由現金流為負數")
        # 3. 獲利能力 FCF Margin & ROE (25分)
        if fcf_margin is not None:
            if fcf_margin > 0.12:
                score += 13; reasons.append(f"FCF Margin ({fcf_margin*100:.1f}%) 造血穩定")
            elif fcf_margin > 0.05:
                score += 8
            elif fcf_margin > 0:
                score += 3
            else:
                warnings.append("自由現金流利潤率為負")
        if roe is not None and roe > 0.15:
            score += 12
        elif roe is not None and roe > 0.08:
            score += 7
        elif roe is not None and roe <= 0:
            warnings.append("ROE 為負數")
        # 4. 股息與派息 (15分)
        if div_yield is not None and div_yield >= 0.03:
            score += 10; reasons.append(f"股息率 {div_yield*100:.2f}% 具備防禦收益")
        elif div_yield is not None and div_yield >= 0.015:
            score += 6
        if payout_ratio is not None and 0 < payout_ratio < 0.75:
            score += 5
        elif payout_ratio is not None and payout_ratio >= 0.90:
            warnings.append(f"派息比率過高 ({payout_ratio*100:.0f}%)，須留意減息風險")
        # 5. 成長與盈虧檢查 (10分)
        if rev_growth is not None and rev_growth > 0.03:
            score += 5
        elif rev_growth is not None and rev_growth < 0:
            warnings.append(f"營收呈現衰退 ({rev_growth*100:.1f}%)")
        if net_income is not None and net_income > 0:
            score += 5
        else:
            warnings.append("處於淨虧損狀態")
        # 6. 低波動加分 Beta (10分)
        if beta is not None:
            if beta < 0.9:
                score += 10; reasons.append(f"Beta ({beta:.2f}) 低波動，抗跌力強")
            elif beta < 1.2:
                score += 6
            else:
                score += 2
        else:
            score += 5

    else:
        # 科技 / 成長股模型
        # [A] 估值維度 (40分)
        if pe_fwd is not None and pe_fwd > 0:
            if pe_fwd < 18:
                score += 12; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 極具吸引力")
            elif pe_fwd < 25:
                score += 8; reasons.append(f"Forward P/E ({pe_fwd:.1f}x) 處於合理區間")
            elif pe_fwd < 35:
                score += 4
            else:
                warnings.append(f"Forward P/E ({pe_fwd:.1f}x) 偏高，存在殺估值風險")
        else:
            warnings.append("缺乏正向預測盈利 (Forward P/E 無效)")

        if peg is not None and peg > 0:
            if peg < 1.2:
                score += 10; reasons.append(f"PEG ({peg:.2f}) 顯示成長性被低估")
            elif peg < 2.0:
                score += 6
            else:
                score += 2; warnings.append(f"PEG ({peg:.2f}) 偏高，成長溢價較貴")
        else:
            score += 4

        if ev_ebitda is not None and ev_ebitda > 0:
            score += 9 if ev_ebitda < 15 else (5 if ev_ebitda < 25 else 1)

        if p_fcf is not None:
            if p_fcf < 20:
                score += 9; reasons.append(f"Price/FCF ({p_fcf:.1f}x) 現金流回報優異")
            elif p_fcf < 30:
                score += 5
            else:
                score += 2
        else:
            warnings.append("自由現金流為負數，無法計算正向 Price/FCF")

        # [B] 獲利與現金流 (35分)
        if fcf_margin is not None:
            if fcf_margin > 0.15:
                score += 12; reasons.append(f"Levered FCF Margin 高達 {fcf_margin*100:.1f}%，造血力極強")
            elif fcf_margin > 0.05:
                score += 7
            elif fcf_margin > 0:
                score += 3
            else:
                warnings.append(f"自由現金流利潤率為負 ({fcf_margin*100:.1f}%)")

        if roa is not None:
            if roa > 0.10:
                score += 10; reasons.append(f"ROA ({roa*100:.1f}%) 資產效率極高")
            elif roa > 0.05:
                score += 6
            elif roa > 0:
                score += 2
            else:
                warnings.append("ROA 為負數")

        if net_income is not None and net_income > 0:
            score += 7
        else:
            warnings.append("公司目前處於淨虧損 (Net Loss)")

        if op_income is not None and op_income > 0:
            score += 6
        else:
            warnings.append("本業處於營業虧損 (Operating Loss)")

        # [C] 成長動能 (15分)
        if rev_growth is not None:
            if rev_growth > 0.15:
                score += 8; reasons.append(f"營收高速增長 ({rev_growth*100:.1f}%)")
            elif rev_growth > 0.05:
                score += 5
            elif rev_growth > 0:
                score += 2
            else:
                warnings.append(f"營收負增長 ({rev_growth*100:.1f}%)")

        if eps_fwd is not None and eps_ttm is not None and eps_ttm > 0:
            if eps_fwd > eps_ttm * 1.1:
                score += 7; reasons.append("預期未來 EPS 增長超過 10%")
            elif eps_fwd > eps_ttm:
                score += 4
            else:
                warnings.append("預期未來 EPS 衰退")

        # [D] 風險 Beta (10分)
        if beta is not None:
            if beta < 1.1:
                score += 10
            elif beta < 1.5:
                score += 6
            else:
                score += 2; warnings.append(f"Beta ({beta:.2f}) 偏高，波動劇烈")
        else:
            score += 5

    # --- 買賣建議判定 ---
    if model_type == "ETF (僅供數據參考)":
        verdict = "⚪ ETF 標的"
    elif score >= 75:
        verdict = "🟢 強力買入 (Strong Buy)"
    elif score >= 60:
        verdict = "🟡 偏向買入 (Accumulate)"
    elif score >= 45:
        verdict = "⚪ 持有觀望 (Hold)"
    else:
        verdict = "🔴 賣出 / 迴避 (Avoid)"

    return {
        "symbol": symbol, "name": name, "sector": sector, "industry": industry,
        "model_type": model_type, "price": price, "mcap": mcap,
        "high_52w": high_52w, "low_52w": low_52w, "pct_from_high": pct_from_high,
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
# 前端網頁介面 (UI)
# ==========================================
st.title("📊 全行業美股估值與自選股排名系統")
st.caption("支援自動識別科技、銀行金融、REITs 與防禦型股票，動態切換估值指標並生成量化買賣建議。")

tab1, tab2 = st.tabs(["🏆 批次掃描自選股並自動排名", "🔍 單一股票深度體檢"])

# --- Tab 1: 批次掃描與自動排名 ---
with tab1:
    st.subheader("自選股清單批次掃描")
    default_watchlist = "GOOG, TSM, NVDA, MSFT, AMZN, META, AAPL, ASML, AMD, AVGO, VRT, V, MA, AXP, JPM, O, ABBV, TGT, MMM, VZ"
    watchlist_input = st.text_area(
        "請輸入美股代號（以逗號或空格分隔，已預設您的自選清單）：",
        value=default_watchlist,
        height=80
    )

    if st.button("🚀 開始批次掃描並排名", type="primary"):
        raw_tickers = watchlist_input.replace("\n", ",").replace(" ", ",").split(",")
        tickers = list(dict.fromkeys([t.strip().upper() for t in raw_tickers if t.strip()]))

        if not tickers:
            st.warning("請至少輸入一個股票代號。")
        else:
            results = []
            errors = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, t in enumerate(tickers):
                status_text.text(f"正在分析 ({i+1}/{len(tickers)}): {t} ...")
                res = analyze_stock_data(t)
                if "error" in res:
                    errors.append(res["error"])
                else:
                    results.append(res)
                progress_bar.progress((i + 1) / len(tickers))

            status_text.empty()
            progress_bar.empty()

            if errors:
                with st.expander(f"⚠️ 有 {len(errors)} 筆代號無法讀取"):
                    for err in errors:
                        st.write(f"- {err}")

            if results:
                # 依綜合評分由高到低排序
                results.sort(key=lambda x: x["score"], reverse=True)

                df_summary = pd.DataFrame([{
                    "排名": idx + 1,
                    "代號": r["symbol"],
                    "名稱": r["name"],
                    "估值模型": r["model_type"],
                    "綜合評分": r["score"],
                    "買賣建議": r["verdict"],
                    "最新股價": fmt_num(r["price"], is_currency=True),
                    "距52週高點": fmt_num(r["pct_from_high"], is_pct=True),
                    "Fwd P/E": fmt_num(r["pe_fwd"]),
                    "PEG": fmt_num(r["peg"]),
                    "P/B": fmt_num(r["pb"]),
                    "FCF Margin": fmt_num(r["fcf_margin"], is_pct=True),
                    "ROE": fmt_num(r["roe"], is_pct=True),
                    "股息率": fmt_num(r["div_yield"], is_pct=True),
                    "Beta": fmt_num(r["beta"]),
                } for idx, r in enumerate(results)])

                st.success(f"✅ 掃描完成！共分析 {len(results)} 檔美股，已依綜合估值評分由高至低排序。")
                st.dataframe(df_summary, use_container_width=True, hide_index=True)

                # 下載 CSV 報告
                csv = df_summary.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 下載排名結果 (CSV / Excel 可開)",
                    data=csv,
                    file_name="us_stock_valuation_ranking.csv",
                    mime="text/csv"
                )

                # 快速摘要前 3 名亮點
                st.markdown("### 🌟 本次掃描評分前三名")
                top_cols = st.columns(min(3, len(results)))
                for col, r in zip(top_cols, results[:3]):
                    with col:
                        st.info(f"**{r['symbol']} ({r['name']})**\n\n"
                                f"🏆 評分：**{r['score']} / 100** | {r['verdict']}\n\n"
                                f"📌 模型：{r['model_type']}\n\n"
                                f"✅ 亮點：{r['reasons'][0] if r['reasons'] else '各項數據均衡'}")

# --- Tab 2: 單一股票深度體檢 ---
with tab2:
    col_in, col_btn = st.columns([3, 1])
    with col_in:
        single_ticker = st.text_input("輸入單一美股代號（例如：GOOG, TSM, JPM, O, ABBV）：", value="TSM")
    with col_btn:
        st.write("")
        st.write("")
        run_single = st.button("🔍 深度分析", type="primary", use_container_width=True)

    if run_single and single_ticker:
        with st.spinner(f"正在抓取 {single_ticker.upper()} 財務報表與估值數據..."):
            r = analyze_stock_data(single_ticker)

        if "error" in r:
            st.error(r["error"])
        else:
            st.markdown(f"## {r['name']} ({r['symbol']})")
            st.caption(f"所屬板塊：{r['sector']} / {r['industry']}  |  套用引擎：**{r['model_type']}**")

            # 頂部關鍵指標卡片
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("最新股價", fmt_num(r["price"], is_currency=True), f"距52週高點 {fmt_num(r['pct_from_high'], is_pct=True)}")
            m2.metric("總市值", fmt_num(r["mcap"], is_currency=True))
            m3.metric("系統綜合評分", f"{r['score']} / 100")
            m4.metric("操作建議", r["verdict"])

            # 優劣勢摘要
            c_pro, c_con = st.columns(2)
            with c_pro:
                st.success("**✅ 核心優勢**\n\n" + ("\n".join([f"- {x}" for x in r["reasons"]]) if r["reasons"] else "- 暫無顯著超額亮點"))
            with c_con:
                st.warning("**⚠️ 風險提示**\n\n" + ("\n".join([f"- {x}" for x in r["warnings"]]) if r["warnings"] else "- 財報面未見明顯紅旗警示"))

            st.divider()

            # 詳細四大數據表
            d1, d2 = st.columns(2)
            with d1:
                st.markdown("#### 1. 核心估值倍數")
                val_df = pd.DataFrame({
                    "指標": ["Trailing P/E (TTM)", "Forward P/E", "PEG Ratio", "Price / Book (P/B)",
                           "Price / Sales (P/S)", "EV / Sales", "EV / EBITDA", "Price / FCF", "Price / OCF (REITs參考)"],
                    "數值": [fmt_num(r["pe_ttm"]), fmt_num(r["pe_fwd"]), fmt_num(r["peg"]), fmt_num(r["pb"]),
                           fmt_num(r["ps_ttm"]), fmt_num(r["ev_sales"]), fmt_num(r["ev_ebitda"]), fmt_num(r["p_fcf"]), fmt_num(r["p_ocf"])]
                })
                st.dataframe(val_df, use_container_width=True, hide_index=True)

                st.markdown("#### 3. 股息、負債與風險")
                risk_df = pd.DataFrame({
                    "指標": ["股息率 (Dividend Yield)", "派息比率 (Payout Ratio)", "負債權益比 (Debt/Equity %)",
                           "流動比率 (Current Ratio)", "Beta (波動係數)", "52週低點 / 高點"],
                    "數值": [fmt_num(r["div_yield"], is_pct=True), fmt_num(r["payout_ratio"], is_pct=True),
                           fmt_num(r["debt_to_equity"]), fmt_num(r["current_ratio"]), fmt_num(r["beta"]),
                           f"{fmt_num(r['low_52w'], is_currency=True)} / {fmt_num(r['high_52w'], is_currency=True)}"]
                })
                st.dataframe(risk_df, use_container_width=True, hide_index=True)

            with d2:
                st.markdown("#### 2. 獲利能力與現金流 (TTM)")
                prof_df = pd.DataFrame({
                    "指標": ["總營收 (Revenue)", "營收年增率 (YoY)", "營業利潤 / 虧損", "淨利潤 / 虧損",
                           "EPS (TTM / Forward)", "營運現金流 (OCF)", "自由現金流 (FCF)", "資本開支 (CapEx)",
                           "Levered FCF Margin", "毛利率 / 營業利潤率 / 淨利率", "ROA (資產報酬率)", "ROE (股東權益報酬率)"],
                    "數值": [fmt_num(r["revenue"], is_currency=True), fmt_num(r["rev_growth"], is_pct=True),
                           fmt_num(r["op_income"], is_currency=True), fmt_num(r["net_income"], is_currency=True),
                           f"{fmt_num(r['eps_ttm'])} / {fmt_num(r['eps_fwd'])}",
                           fmt_num(r["ocf"], is_currency=True), fmt_num(r["fcf"], is_currency=True),
                           fmt_num(r["capex"], is_currency=True), fmt_num(r["fcf_margin"], is_pct=True),
                           f"{fmt_num(r['gross_margin'], is_pct=True)} / {fmt_num(r['op_margin'], is_pct=True)} / {fmt_num(r['profit_margin'], is_pct=True)}",
                           fmt_num(r["roa"], is_pct=True), fmt_num(r["roe"], is_pct=True)]
                })
                st.dataframe(prof_df, use_container_width=True, hide_index=True)
