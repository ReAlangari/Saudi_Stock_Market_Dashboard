import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="تحليل أساسي ",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ───────────────────────────────────────────────────────────────
API_BASE = "https://app.sahmk.sa/api/v1"
API_KEY = os.getenv("SAHMK_API_KEY") or st.secrets.get("SAHMK_API_KEY", "")
HEADERS = {"X-API-Key": API_KEY}

# ─── Plotly Shared Theme ─────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", family="IBM Plex Sans Arabic, Tajawal, sans-serif"),
    hoverlabel=dict(bgcolor="#1A1F2E", font_size=13, font_color="#E2E8F0", bordercolor="#4A5568"),
    margin=dict(l=20, r=20, t=20, b=20),
)

# ─── Fundamental Data (loaded from CSV) ──────────────────────────────────────
# Source: Tadawul disclosures, company annual reports, Argaam
FUNDAMENTALS = pd.read_csv(os.path.join(os.path.dirname(__file__), "data", "saudi_stocks_fundamentals.csv"))
FUNDAMENTALS["symbol"] = FUNDAMENTALS["symbol"].astype(str)

# Shariah compliance threshold
SHARIAH_MAX_DEBT_RATIO = 33.0


# ─── API Helpers ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def api_get(endpoint, params=None):
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"خطأ في الاتصال: {e}")
        return None


def get_market_summary():
    return api_get("/market/summary/")


def get_quotes(symbols):
    return api_get("/quotes/", {"symbols": symbols})


def get_sectors():
    return api_get("/market/sectors/")


def fmt_number(n, prefix="", suffix=""):
    if n is None:
        return "N/A"
    abs_n = abs(n)
    if abs_n >= 1_000_000_000:
        return f"{prefix}{n / 1_000_000_000:,.2f}B{suffix}"
    if abs_n >= 1_000_000:
        return f"{prefix}{n / 1_000_000:,.2f}M{suffix}"
    if abs_n >= 1_000:
        return f"{prefix}{n / 1_000:,.1f}K{suffix}"
    return f"{prefix}{n:,.2f}{suffix}"


MOOD_CONFIG = {
    "very_bullish":       ("صعود قوي",   "#00C853", "🟢"),
    "bullish":            ("صعود",        "#66BB6A", "🟢"),
    "moderately_bullish": ("صعود معتدل", "#A5D6A7", "🟡"),
    "neutral":            ("محايد",        "#FFD54F", "🟡"),
    "moderately_bearish": ("هبوط معتدل", "#FF8A65", "🟠"),
    "bearish":            ("هبوط",        "#EF5350", "🔴"),
    "very_bearish":       ("هبوط حاد",   "#C62828", "🔴"),
}

SECTOR_NAMES = {
    "TENI": "الطاقة", "TMTI": "المواد الأساسية", "TCPI": "السلع الرأسمالية",
    "TCSI": "الخدمات التجارية", "TTSI": "النقل", "TCGI": "السلع المعمرة",
    "TSSI": "الخدمات الاستهلاكية", "TMDI": "الإعلام والترفيه", "TRLI": "التجزئة",
    "TFSI": "الأغذية والمواد الغذائية", "TFBI": "إنتاج الأغذية", "THEI": "المعدات الصحية",
    "TPBI": "الأدوية", "TBNI": "البنوك", "TDFI": "الخدمات المالية",
    "TISI": "التأمين", "TRTI": "إدارة العقارات", "TUTI": "المرافق العامة",
    "TRMI": "صناديق الريت", "TDAI": "البرمجيات والخدمات",
}


# ─── Styled Metric Card ─────────────────────────────────────────────────────
def styled_metric(label, value, delta=None, border_color="#4A5568"):
    """Bloomberg-style metric card with colored border and monospace value."""
    delta_html = ""
    if delta is not None:
        delta_str = str(delta)
        if delta_str.startswith("+") or (delta_str.replace("%", "").replace(",", "").replace(" ", "").replace(".", "").lstrip("-").isdigit() and not delta_str.startswith("-")):
            arrow, d_color = "▲", "#00C853"
        elif delta_str.startswith("-"):
            arrow, d_color = "▼", "#FF1744"
        else:
            arrow, d_color = "", "#A0AEC0"
        delta_html = f'<div style="font-size:0.8rem;color:{d_color};margin-top:4px;">{arrow} {delta_str}</div>'

    st.markdown(f"""
    <div class="metric-card" style="border-right:3px solid {border_color};">
        <div style="color:#A0AEC0;font-size:0.78rem;margin-bottom:4px;">{label}</div>
        <div style="font-family:'IBM Plex Mono',monospace;font-size:1.45rem;font-weight:700;color:#FAFAFA;direction:ltr;unicode-bidi:isolate;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Arabic:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;700&family=Tajawal:wght@400;500;700&display=swap');

    /* Global typography */
    html, body, .main, .stMarkdown, .stSelectbox, .stRadio {
        font-family: 'IBM Plex Sans Arabic', 'Tajawal', sans-serif !important;
    }

    /* RTL Support */
    .main .block-container, .stMarkdown {
        direction: rtl;
        text-align: right;
    }

    /* Metric card */
    .metric-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 18px 16px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.35);
    }

    /* Section header */
    .section-header {
        border-right: 4px solid #00C853;
        padding-right: 14px;
        margin: 24px 0 12px 0;
        font-size: 1.15rem;
        font-weight: 600;
        color: #E2E8F0;
        direction: rtl;
        text-align: right;
        font-family: 'IBM Plex Sans Arabic', 'Tajawal', sans-serif;
    }

    /* Shariah badges */
    .shariah-pass {
        background: linear-gradient(135deg, #1B5E20, #2E7D32);
        color: #FAFAFA;
        padding: 5px 14px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }
    .shariah-fail {
        background: linear-gradient(135deg, #B71C1C, #C62828);
        color: #FAFAFA;
        padding: 5px 14px;
        border-radius: 14px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Glassmorphism sidebar */
    section[data-testid="stSidebar"] > div:first-child {
        background: linear-gradient(180deg, rgba(26,31,46,0.92) 0%, rgba(37,43,59,0.95) 100%) !important;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-left: 1px solid rgba(255,255,255,0.06);
    }

    /* Sidebar radio hover */
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
        transition: background 0.2s ease;
    }

    /* Pulse animation for API status */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(0,200,83,0.5); }
        70% { box-shadow: 0 0 0 8px rgba(0,200,83,0); }
        100% { box-shadow: 0 0 0 0 rgba(0,200,83,0); }
    }
    .status-dot {
        display: inline-block;
        width: 9px; height: 9px;
        border-radius: 50%;
        margin-left: 6px;
        vertical-align: middle;
    }
    .status-dot.online {
        background: #00C853;
        animation: pulse 2s infinite;
    }
    .status-dot.offline {
        background: #FF1744;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Saudi_Arabia.svg/320px-Flag_of_Saudi_Arabia.svg.png", width=50)
    st.title("التحليل الأساسي")
    st.caption("  | تحليل مالي للسوق السعودي")
    st.divider()

    page = st.radio(
        "التنقل",
        ["ملخص السوق", "مكررات القيمة", "الملاءة والتوافق الشرعي", "الكفاءة والربحية", "تحليل سهم"],
        index=0,
    )

    st.divider()
    if st.button("تحديث البيانات", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("بيانات لحظية: [SAHMK API](https://app.sahmk.sa)")
    st.caption("بيانات مالية: القوائم المالية السنوية")
    st.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: merge live prices into fundamentals
# ═══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def get_enriched_fundamentals():
    """Merge live price data with fundamental dataset (batched — API max 50 per call)."""
    all_symbols = FUNDAMENTALS["symbol"].tolist()
    BATCH_SIZE = 50
    all_quotes = []

    for i in range(0, len(all_symbols), BATCH_SIZE):
        batch = all_symbols[i:i + BATCH_SIZE]
        result = get_quotes(",".join(batch))
        if result and result.get("quotes"):
            all_quotes.extend(result["quotes"])

    df = FUNDAMENTALS.copy()

    if all_quotes:
        live_df = pd.DataFrame(all_quotes)[["symbol", "price", "change", "change_percent", "volume"]]
        live_df["symbol"] = live_df["symbol"].astype(str)
        df = df.merge(live_df, on="symbol", how="left")
    else:
        df["price"] = None
        df["change"] = None
        df["change_percent"] = None
        df["volume"] = None

    return df


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: Market Summary + Dividends
# ═══════════════════════════════════════════════════════════════════════════════
if page == "ملخص السوق":
    summary = get_market_summary()

    if summary:
        st.markdown("## ملخص السوق والتوزيعات")
        st.caption(f"تاسي — مؤشر السوق الرئيسي  |  التحديث: {summary.get('timestamp', 'N/A')}")

        # ── Market Header ──
        col1, col2, col3, col4 = st.columns(4)
        idx_val = summary.get("index_value", 0)
        idx_chg = summary.get("index_change", 0)
        idx_pct = summary.get("index_change_percent", 0)
        mood_raw = summary.get("market_mood", "neutral")
        mood_label, mood_color, mood_icon = MOOD_CONFIG.get(mood_raw, ("غير معروف", "#999", "⚪"))

        with col1:
            st.metric("مؤشر تاسي", f"{idx_val:,.2f}", f"{idx_chg:+.2f} ({idx_pct:+.1f}%)")
        with col2:
            st.metric("مزاج السوق", f"{mood_icon} {mood_label}")
        with col3:
            st.metric("إجمالي الكمية", fmt_number(summary.get("total_volume", 0)))
        with col4:
            total_value = summary.get("total_value", 0)
            st.metric("إجمالي القيمة", fmt_number(total_value, suffix=" ر.س"))

        st.divider()

        # ── Top Dividend Yielders ──
        st.markdown('<div class="section-header">أعلى 10 أسهم توزيعاً للأرباح (عائد التوزيعات %)</div>',
                    unsafe_allow_html=True)

        df = get_enriched_fundamentals()
        top_div = df[df["dividend_yield"] > 0].nlargest(10, "dividend_yield")

        fig_div = px.bar(
            top_div, x="dividend_yield", y="name", orientation="h",
            color="dividend_yield",
            color_continuous_scale=["#A5D6A7", "#00C853", "#1B5E20"],
            text=top_div["dividend_yield"].apply(lambda x: f"{x:.1f}%"),
            labels={"dividend_yield": "عائد التوزيعات %", "name": "الشركة"},
        )
        fig_div.update_layout(
            height=420,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            yaxis=dict(showgrid=False, autorange="reversed"),
            xaxis=dict(showgrid=True, gridcolor="#2D3748"),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        fig_div.update_traces(textposition="outside")
        st.plotly_chart(fig_div, use_container_width=True)

        st.info("**عائد التوزيعات** = (التوزيعات النقدية السنوية ÷ سعر السهم الحالي) × 100. "
                "كلما ارتفعت النسبة، زاد الدخل النقدي للمستثمر. هذا المؤشر جوهري لشركات الكابيتال.")

        # ── Sector ROE Heatmap ──
        st.divider()
        st.markdown('<div class="section-header">متوسط العائد على حقوق المساهمين حسب القطاع (ROE %)</div>',
                    unsafe_allow_html=True)

        sector_roe = df.groupby("sector").agg(
            avg_roe=("roe", "mean"),
            count=("symbol", "count"),
        ).reset_index().sort_values("avg_roe", ascending=True)

        fig_roe = px.bar(
            sector_roe, x="avg_roe", y="sector", orientation="h",
            color="avg_roe",
            color_continuous_scale=["#FF8A80", "#FAFAFA", "#A5D6A7", "#00C853", "#1B5E20"],
            color_continuous_midpoint=10,
            text=sector_roe["avg_roe"].apply(lambda x: f"{x:.1f}%"),
            labels={"avg_roe": "ROE %", "sector": "القطاع"},
        )
        fig_roe.update_layout(
            height=380,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            yaxis=dict(showgrid=False),
            xaxis=dict(showgrid=True, gridcolor="#2D3748"),
            coloraxis_showscale=False,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        fig_roe.update_traces(textposition="outside")
        st.plotly_chart(fig_roe, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: Valuation Multiples
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "مكررات القيمة":
    st.markdown("## مكررات القيمة (Valuation Multiples)")
    st.caption("تحليل مقارن لمكررات الربحية والقيمة الدفترية وعائد التوزيعات")

    df = get_enriched_fundamentals()
    # Filter out negative/zero P/E for scatter
    df_val = df[df["pe"] > 0].copy()

    # ── P/E vs P/B Scatter ──
    st.markdown('<div class="section-header">مخطط التشتت: مكرر الربحية (P/E) مقابل القيمة الدفترية (P/B)</div>',
                unsafe_allow_html=True)

    fig_scatter = px.scatter(
        df_val, x="pe", y="pb",
        size="dividend_yield",
        color="roe",
        color_continuous_scale=["#FF1744", "#FFD54F", "#00C853"],
        hover_name="name",
        hover_data={"pe": ":.1f", "pb": ":.1f", "roe": ":.1f", "dividend_yield": ":.1f", "sector": True},
        labels={"pe": "مكرر الربحية (P/E)", "pb": "مكرر القيمة الدفترية (P/B)",
                "roe": "ROE %", "dividend_yield": "عائد التوزيعات %"},
        text="symbol",
    )
    fig_scatter.update_traces(textposition="top center", textfont=dict(size=10))

    # Add quadrant lines
    median_pe = df_val["pe"].median()
    median_pb = df_val["pb"].median()
    fig_scatter.add_hline(y=median_pb, line_dash="dash", line_color="#555", annotation_text="متوسط P/B")
    fig_scatter.add_vline(x=median_pe, line_dash="dash", line_color="#555", annotation_text="متوسط P/E")

    fig_scatter.update_layout(
        height=520,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        xaxis=dict(showgrid=True, gridcolor="#2D3748"),
        yaxis=dict(showgrid=True, gridcolor="#2D3748"),
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.success("**الربع السفلي الأيسر** (P/E منخفض + P/B منخفض) = أسهم قد تكون **مقومة بأقل من قيمتها** — فرصة استثمارية محتملة")
    with col_info2:
        st.warning("**الربع العلوي الأيمن** (P/E مرتفع + P/B مرتفع) = أسهم قد تكون **مبالغ في تقييمها** — تحتاج تحليل أعمق")

    st.divider()

    # ── Comparative Table ──
    st.markdown('<div class="section-header">جدول مقارنة المكررات</div>', unsafe_allow_html=True)

    display_df = df[["symbol", "name", "sector", "pe", "pb", "dividend_yield", "roe"]].copy()
    display_df["pe"] = display_df["pe"].apply(lambda x: f"{x:.1f}" if x > 0 else "خسارة")

    st.dataframe(
        display_df.rename(columns={
            "symbol": "الرمز", "name": "الشركة", "sector": "القطاع",
            "pe": "مكرر الربحية", "pb": "القيمة الدفترية",
            "dividend_yield": "عائد التوزيعات %", "roe": "ROE %",
        }).sort_values("عائد التوزيعات %", ascending=False),
        use_container_width=True, hide_index=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: Solvency & Shariah Screening
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "الملاءة والتوافق الشرعي":
    st.markdown("## الملاءة المالية والتوافق الشرعي")
    st.caption("فحص نسب الديون والتوافق مع معايير الاستثمار الشرعي")

    df = get_enriched_fundamentals()

    # ── Shariah Screening Overview ──
    st.markdown('<div class="section-header">فحص التوافق الشرعي (نسبة الديون الربوية &lt; 33%)</div>',
                unsafe_allow_html=True)

    compliant_count = df["shariah_compliant"].sum()
    non_compliant_count = len(df) - compliant_count

    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        st.metric("إجمالي الأسهم", len(df))
    with col_s2:
        st.metric("متوافقة شرعياً", f"{compliant_count}", delta=f"{compliant_count/len(df)*100:.0f}%")
    with col_s3:
        st.metric("غير متوافقة", f"{non_compliant_count}", delta=f"-{non_compliant_count/len(df)*100:.0f}%")

    st.divider()

    # ── Shariah Debt Ratio Bar ──
    df_shariah = df.sort_values("shariah_debt_ratio", ascending=True).copy()
    df_shariah["status"] = df_shariah["shariah_debt_ratio"].apply(
        lambda x: "متوافق ✅" if x < SHARIAH_MAX_DEBT_RATIO else "غير متوافق ❌"
    )
    colors = ["#00C853" if x < SHARIAH_MAX_DEBT_RATIO else "#FF1744" for x in df_shariah["shariah_debt_ratio"]]

    fig_shariah = go.Figure(go.Bar(
        x=df_shariah["shariah_debt_ratio"],
        y=df_shariah["name"],
        orientation="h",
        marker_color=colors,
        text=df_shariah["shariah_debt_ratio"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
    ))
    fig_shariah.add_vline(x=33, line_dash="dash", line_color="#FF1744", line_width=2,
                          annotation_text="الحد الشرعي 33%", annotation_font_color="#FF1744")
    fig_shariah.update_layout(
        height=520,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        xaxis=dict(title="نسبة الديون الربوية إلى الأصول %", showgrid=True, gridcolor="#2D3748"),
        yaxis=dict(showgrid=False),
        margin=dict(l=20, r=40, t=20, b=20),
    )
    st.plotly_chart(fig_shariah, use_container_width=True)

    st.info("**معيار التوافق الشرعي:** نسبة الديون الربوية يجب ألا تتجاوز **33%** من إجمالي الأصول. "
            "البنوك التقليدية عادةً لا تتوافق بسبب طبيعة أعمالها. بنك الراجحي وبنك الإنماء يعملان وفق الشريعة بالكامل.")

    st.divider()

    # ── Debt-to-Equity Comparison ──
    st.markdown('<div class="section-header">نسبة الدين إلى حقوق المساهمين (Debt-to-Equity)</div>',
                unsafe_allow_html=True)

    # Exclude banks (their D/E is naturally very high)
    df_non_bank = df[~df["sector"].isin(["البنوك"])].sort_values("debt_equity", ascending=True)

    fig_de = px.bar(
        df_non_bank, x="debt_equity", y="name", orientation="h",
        color="debt_equity",
        color_continuous_scale=["#00C853", "#FFD54F", "#FF1744"],
        text=df_non_bank["debt_equity"].apply(lambda x: f"{x:.2f}"),
        labels={"debt_equity": "الدين / حقوق المساهمين", "name": "الشركة"},
    )
    fig_de.add_vline(x=1.0, line_dash="dash", line_color="#FFD54F",
                     annotation_text="حد الخطر 1.0", annotation_font_color="#FFD54F")
    fig_de.update_layout(
        height=450,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        xaxis=dict(showgrid=True, gridcolor="#2D3748"),
        yaxis=dict(showgrid=False),
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    fig_de.update_traces(textposition="outside")
    st.plotly_chart(fig_de, use_container_width=True)

    st.caption("**ملاحظة:** تم استثناء البنوك من هذا الرسم لأن نسبة الدين مرتفعة بطبيعة أعمالها.")

    # ── Current Ratio ──
    st.divider()
    st.markdown('<div class="section-header">نسبة التداول (Current Ratio) — القدرة على سداد الالتزامات</div>',
                unsafe_allow_html=True)

    df_cr = df.sort_values("current_ratio", ascending=True)
    cr_colors = ["#FF1744" if x < 1.0 else "#FFD54F" if x < 1.5 else "#00C853" for x in df_cr["current_ratio"]]

    fig_cr = go.Figure(go.Bar(
        x=df_cr["current_ratio"],
        y=df_cr["name"],
        orientation="h",
        marker_color=cr_colors,
        text=df_cr["current_ratio"].apply(lambda x: f"{x:.2f}"),
        textposition="outside",
    ))
    fig_cr.add_vline(x=1.0, line_dash="dash", line_color="#FF1744",
                     annotation_text="الحد الأدنى 1.0", annotation_font_color="#FF1744")
    fig_cr.update_layout(
        height=520,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        xaxis=dict(title="نسبة التداول (أصول جارية ÷ خصوم جارية)", showgrid=True, gridcolor="#2D3748"),
        yaxis=dict(showgrid=False),
        margin=dict(l=20, r=40, t=20, b=20),
    )
    st.plotly_chart(fig_cr, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: Efficiency & Profitability
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "الكفاءة والربحية":
    st.markdown("## الكفاءة والربحية")
    st.caption("هل الإدارة تستخدم أموال المستثمرين بذكاء؟")

    df = get_enriched_fundamentals()

    # ── ROE Comparison ──
    st.markdown('<div class="section-header">العائد على حقوق المساهمين (ROE %)</div>',
                unsafe_allow_html=True)

    df_roe = df.sort_values("roe", ascending=True)
    roe_colors = ["#FF1744" if x < 0 else "#FFD54F" if x < 10 else "#00C853" for x in df_roe["roe"]]

    fig_roe = go.Figure(go.Bar(
        x=df_roe["roe"],
        y=df_roe["name"],
        orientation="h",
        marker_color=roe_colors,
        text=df_roe["roe"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
    ))
    fig_roe.add_vline(x=15, line_dash="dash", line_color="#00C853",
                      annotation_text="ممتاز > 15%", annotation_font_color="#00C853")
    fig_roe.update_layout(
        height=520,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        xaxis=dict(title="ROE %", showgrid=True, gridcolor="#2D3748",
                   zeroline=True, zerolinecolor="#FAFAFA"),
        yaxis=dict(showgrid=False),
        margin=dict(l=20, r=40, t=20, b=20),
    )
    st.plotly_chart(fig_roe, use_container_width=True)

    st.info("**ROE > 15%** يعتبر ممتازاً ويعني أن الشركة تحقق عوائد جيدة للمساهمين. "
            "**ROE سلبي** يعني أن الشركة تخسر أموال المستثمرين.")

    st.divider()

    # ── Net Margin Comparison ──
    st.markdown('<div class="section-header">هامش صافي الربح (Net Profit Margin %)</div>',
                unsafe_allow_html=True)

    df_margin = df.sort_values("net_margin", ascending=True)
    margin_colors = ["#FF1744" if x < 0 else "#FFD54F" if x < 10 else "#00C853" for x in df_margin["net_margin"]]

    fig_margin = go.Figure(go.Bar(
        x=df_margin["net_margin"],
        y=df_margin["name"],
        orientation="h",
        marker_color=margin_colors,
        text=df_margin["net_margin"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
    ))
    fig_margin.update_layout(
        height=520,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        xaxis=dict(title="هامش صافي الربح %", showgrid=True, gridcolor="#2D3748",
                   zeroline=True, zerolinecolor="#FAFAFA"),
        yaxis=dict(showgrid=False),
        margin=dict(l=20, r=40, t=20, b=20),
    )
    st.plotly_chart(fig_margin, use_container_width=True)

    st.divider()

    # ── Revenue vs Net Income ──
    st.markdown('<div class="section-header">الإيرادات مقابل صافي الربح (مليار ر.س)</div>',
                unsafe_allow_html=True)

    df_rev = df.sort_values("revenue_b", ascending=False).head(12)

    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(
        name="الإيرادات", y=df_rev["name"], x=df_rev["revenue_b"],
        orientation="h", marker_color="#2196F3",
        text=df_rev["revenue_b"].apply(lambda x: f"{x:.1f}B"), textposition="auto",
    ))
    fig_rev.add_trace(go.Bar(
        name="صافي الربح", y=df_rev["name"], x=df_rev["net_income_b"],
        orientation="h", marker_color="#00C853",
        text=df_rev["net_income_b"].apply(lambda x: f"{x:.1f}B"), textposition="auto",
    ))
    fig_rev.update_layout(
        barmode="group", height=480,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA"),
        xaxis=dict(title="مليار ر.س", showgrid=True, gridcolor="#2D3748"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig_rev, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: Stock Deep Dive
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "تحليل سهم":
    st.markdown("## تحليل سهم تفصيلي")

    df = get_enriched_fundamentals()

    # Stock selector
    stock_options = {f"{row['symbol']} — {row['name']}": row["symbol"] for _, row in df.iterrows()}
    selected = st.selectbox("اختر السهم", options=list(stock_options.keys()))
    symbol = stock_options[selected]

    stock = df[df["symbol"] == symbol].iloc[0]

    # ── Header ──
    st.markdown(f"### {stock['symbol']} — {stock['name']}")

    shariah_tag = ('<span class="shariah-pass">متوافق شرعياً ✅</span>'
                   if stock["shariah_compliant"]
                   else '<span class="shariah-fail">غير متوافق شرعياً ❌</span>')
    st.markdown(f"**القطاع:** {stock['sector']} &nbsp; | &nbsp; {shariah_tag}", unsafe_allow_html=True)

    st.divider()

    # ── Live Price ──
    if stock.get("price"):
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        with col_p1:
            chg_pct = stock.get("change_percent", 0) or 0
            st.metric("السعر الحالي", f"{stock['price']} ر.س", f"{chg_pct:+.2f}%")
        with col_p2:
            st.metric("الكمية", fmt_number(stock.get("volume", 0) or 0))
        with col_p3:
            pe_display = f"{stock['pe']:.1f}" if stock["pe"] > 0 else "خسارة"
            st.metric("مكرر الربحية (P/E)", pe_display)
        with col_p4:
            st.metric("عائد التوزيعات", f"{stock['dividend_yield']:.1f}%")

    st.divider()

    # ── Fundamental KPIs ──
    st.markdown('<div class="section-header">المؤشرات المالية الأساسية</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        pe_display = f"{stock['pe']:.1f}" if stock["pe"] > 0 else "خسارة"
        st.metric("مكرر الربحية (P/E)", pe_display)
    with col2:
        st.metric("القيمة الدفترية (P/B)", f"{stock['pb']:.1f}")
    with col3:
        st.metric("ROE", f"{stock['roe']:.1f}%")
    with col4:
        st.metric("هامش الربح", f"{stock['net_margin']:.1f}%")
    with col5:
        st.metric("الدين/حقوق المساهمين", f"{stock['debt_equity']:.2f}")
    with col6:
        st.metric("نسبة التداول", f"{stock['current_ratio']:.2f}")

    st.divider()

    # ── Radar Chart ──
    st.markdown('<div class="section-header">ملف المخاطر والعوائد</div>', unsafe_allow_html=True)

    # Normalize metrics for radar (0-100 scale)
    def norm(val, min_v, max_v):
        return max(0, min(100, (val - min_v) / (max_v - min_v) * 100)) if max_v != min_v else 50

    radar_data = {
        "الربحية (ROE)": norm(stock["roe"], -5, 65),
        "عائد التوزيعات": norm(stock["dividend_yield"], 0, 8),
        "الملاءة المالية": norm(2 - stock["debt_equity"], 0, 2),  # inverse: lower debt = better
        "السيولة": norm(stock["current_ratio"], 0.5, 3.5),
        "هامش الربح": norm(stock["net_margin"], -10, 55),
        "التوافق الشرعي": norm(33 - stock["shariah_debt_ratio"], 0, 33),
    }

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=list(radar_data.values()),
        theta=list(radar_data.keys()),
        fill="toself",
        fillcolor="rgba(0, 200, 83, 0.2)",
        line=dict(color="#00C853", width=2),
        name=stock["name"],
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#2D3748", linecolor="#2D3748"),
            angularaxis=dict(gridcolor="#2D3748", linecolor="#2D3748"),
        ),
        height=420,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#FAFAFA", size=12),
        showlegend=False,
        margin=dict(l=60, r=60, t=40, b=40),
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    st.divider()

    # ── Financial Summary ──
    st.markdown('<div class="section-header">ملخص القوائم المالية (مليار ر.س)</div>', unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)

    with col_f1:
        fig_fs = go.Figure()
        fig_fs.add_trace(go.Bar(
            name="الإيرادات", x=["الإيرادات"], y=[stock["revenue_b"]],
            marker_color="#2196F3", text=[f"{stock['revenue_b']:.1f}B"], textposition="auto",
        ))
        fig_fs.add_trace(go.Bar(
            name="صافي الربح", x=["صافي الربح"], y=[stock["net_income_b"]],
            marker_color="#00C853" if stock["net_income_b"] > 0 else "#FF1744",
            text=[f"{stock['net_income_b']:.1f}B"], textposition="auto",
        ))
        fig_fs.update_layout(
            title="الدخل", height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            showlegend=False,
            yaxis=dict(showgrid=True, gridcolor="#2D3748"),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_fs, use_container_width=True)

    with col_f2:
        fig_bs = go.Figure()
        fig_bs.add_trace(go.Bar(
            name="الأصول", x=["الأصول"], y=[stock["total_assets_b"]],
            marker_color="#2196F3", text=[f"{stock['total_assets_b']:.1f}B"], textposition="auto",
        ))
        fig_bs.add_trace(go.Bar(
            name="الديون", x=["الديون"], y=[stock["total_debt_b"]],
            marker_color="#FF1744", text=[f"{stock['total_debt_b']:.1f}B"], textposition="auto",
        ))
        equity = stock["total_assets_b"] - stock["total_debt_b"]
        fig_bs.add_trace(go.Bar(
            name="حقوق المساهمين", x=["حقوق المساهمين"], y=[equity],
            marker_color="#00C853", text=[f"{equity:.1f}B"], textposition="auto",
        ))
        fig_bs.update_layout(
            title="الميزانية", height=300,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            showlegend=False,
            yaxis=dict(showgrid=True, gridcolor="#2D3748"),
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_bs, use_container_width=True)

    # ── Comparative Position ──
    st.divider()
    st.markdown('<div class="section-header">الموقع مقارنة بالقطاع</div>', unsafe_allow_html=True)

    sector_peers = df[df["sector"] == stock["sector"]]
    if len(sector_peers) > 1:
        metrics_compare = ["pe", "pb", "roe", "dividend_yield", "debt_equity"]
        labels_compare = ["مكرر الربحية", "القيمة الدفترية", "ROE %", "عائد التوزيعات %", "الدين/حقوق المساهمين"]

        comparison = []
        for m, l in zip(metrics_compare, labels_compare):
            comparison.append({
                "المؤشر": l,
                stock["name"]: f"{stock[m]:.1f}" if stock[m] != 0 else "خسارة",
                f"متوسط {stock['sector']}": f"{sector_peers[m].mean():.1f}",
            })

        st.dataframe(pd.DataFrame(comparison), use_container_width=True, hide_index=True)
    else:
        st.caption("لا توجد شركات أخرى في نفس القطاع للمقارنة.")
