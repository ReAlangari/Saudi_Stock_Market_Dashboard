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
    page_title="لوحة السوق السعودي | تاسي مباشر",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Constants ───────────────────────────────────────────────────────────────
API_BASE = "https://app.sahmk.sa/api/v1"
API_KEY = os.getenv("SAHMK_API_KEY") or st.secrets.get("SAHMK_API_KEY", "")

HEADERS = {"X-API-Key": API_KEY}

SECTOR_NAMES = {
    "TENI": "الطاقة",
    "TMTI": "المواد الأساسية",
    "TCPI": "السلع الرأسمالية",
    "TCSI": "الخدمات التجارية",
    "TTSI": "النقل",
    "TCGI": "السلع المعمرة",
    "TSSI": "الخدمات الاستهلاكية",
    "TMDI": "الإعلام والترفيه",
    "TRLI": "التجزئة",
    "TFSI": "الأغذية والمواد الغذائية",
    "TFBI": "إنتاج الأغذية",
    "THEI": "المعدات الصحية",
    "TPBI": "الأدوية",
    "TBNI": "البنوك",
    "TDFI": "الخدمات المالية",
    "TISI": "التأمين",
    "TRTI": "إدارة العقارات",
    "TUTI": "المرافق العامة",
    "TRMI": "صناديق الريت",
    "TDAI": "البرمجيات والخدمات",
}

MOOD_CONFIG = {
    "very_bullish":       ("صعود قوي",       "#00C853", "🟢"),
    "bullish":            ("صعود",            "#66BB6A", "🟢"),
    "moderately_bullish": ("صعود معتدل",     "#A5D6A7", "🟡"),
    "neutral":            ("محايد",            "#FFD54F", "🟡"),
    "moderately_bearish": ("هبوط معتدل",     "#FF8A65", "🟠"),
    "bearish":            ("هبوط",            "#EF5350", "🔴"),
    "very_bearish":       ("هبوط حاد",       "#C62828", "🔴"),
}

# Key TASI stocks for the watchlist
WATCHLIST_SYMBOLS = "2222,1120,2010,7010,2350,1180,2280,4200,8210,3010"


# ─── API Helpers ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def api_get(endpoint, params=None):
    """Make a cached GET request to SAHMK API."""
    try:
        resp = requests.get(f"{API_BASE}{endpoint}", headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None


def get_market_summary():
    return api_get("/market/summary/")


def get_gainers(limit=10):
    return api_get("/market/gainers/", {"limit": limit})


def get_losers(limit=10):
    return api_get("/market/losers/", {"limit": limit})


def get_volume_leaders(limit=10):
    return api_get("/market/volume/", {"limit": limit})


def get_value_leaders(limit=10):
    return api_get("/market/value/", {"limit": limit})


def get_sectors():
    return api_get("/market/sectors/")


def get_quote(symbol):
    return api_get(f"/quote/{symbol}/")


def get_quotes(symbols):
    return api_get("/quotes/", {"symbols": symbols})


def get_company(symbol):
    return api_get(f"/company/{symbol}/")


# ─── Helper: format numbers ─────────────────────────────────────────────────
def fmt_number(n, prefix="", suffix=""):
    """Format large numbers with K/M/B suffixes."""
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


def color_change(val):
    """Return green/red color based on positive/negative value."""
    if val > 0:
        return "#00C853"
    elif val < 0:
        return "#FF1744"
    return "#FFD54F"


# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* RTL Support */
    .main .block-container, .stMarkdown, .stMetric {
        direction: rtl;
        text-align: right;
    }
    /* Keep numbers LTR inside RTL context */
    [data-testid="stMetricValue"], [data-testid="stMetricDelta"] {
        direction: ltr;
        unicode-bidi: isolate;
    }

    /* Main metric cards */
    .metric-card {
        background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); }
    .metric-label { color: #A0AEC0; font-size: 0.85rem; margin-bottom: 4px; }
    .metric-value { font-size: 1.8rem; font-weight: 700; color: #FAFAFA; }
    .metric-delta-up { color: #00C853; font-size: 0.95rem; }
    .metric-delta-down { color: #FF1744; font-size: 0.95rem; }
    .metric-delta-neutral { color: #FFD54F; font-size: 0.95rem; }

    /* Mood badge */
    .mood-badge {
        display: inline-block;
        padding: 6px 18px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 1.1rem;
    }

    /* Section headers */
    .section-header {
        border-right: 4px solid #1B5E20;
        padding-right: 12px;
        margin: 20px 0 10px 0;
        font-size: 1.2rem;
        font-weight: 600;
        direction: rtl;
        text-align: right;
    }

    /* Liquidity bar */
    .liq-bar {
        height: 24px;
        border-radius: 4px;
        display: flex;
        overflow: hidden;
        margin: 4px 0;
    }
    .liq-inflow { background: #00C853; height: 100%; }
    .liq-outflow { background: #FF1744; height: 100%; }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1A1F2E 0%, #252B3B 100%);
        border: 1px solid #2D3748;
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Flag_of_Saudi_Arabia.svg/320px-Flag_of_Saudi_Arabia.svg.png", width=50)
    st.title("لوحة تاسي")
    st.caption("بيانات السوق السعودي لحظياً")
    st.divider()

    page = st.radio(
        "التنقل",
        ["نظرة عامة", "الأكثر تحركاً", "أداء القطاعات", "بحث سهم", "قائمة المتابعة"],
        index=0,
    )

    st.divider()
    if st.button("تحديث البيانات", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.caption("مصدر البيانات: [SAHMK API](https://app.sahmk.sa)")
    st.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 1: Market Overview
# ═══════════════════════════════════════════════════════════════════════════════
if page == "نظرة عامة":
    summary = get_market_summary()

    if summary:
        # ── Header Row ──
        st.markdown("## نظرة عامة على السوق")
        st.caption(f"تاسي — مؤشر السوق الرئيسي  |  التحديث: {summary.get('timestamp', 'N/A')}")

        # ── Key Metrics ──
        col1, col2, col3, col4, col5 = st.columns(5)

        idx_val = summary.get("index_value", 0)
        idx_chg = summary.get("index_change", 0)
        idx_pct = summary.get("index_change_percent", 0)
        mood_raw = summary.get("market_mood", "neutral")

        with col1:
            st.metric("مؤشر تاسي", f"{idx_val:,.2f}", f"{idx_chg:+.2f} ({idx_pct:+.1f}%)")
        with col2:
            mood_label, mood_color, mood_icon = MOOD_CONFIG.get(mood_raw, ("غير معروف", "#999", "⚪"))
            st.metric("مزاج السوق", f"{mood_icon} {mood_label}")
        with col3:
            st.metric("إجمالي الكمية", fmt_number(summary.get("total_volume", 0)))
        with col4:
            st.metric("الأسهم الرابحة", f"{summary.get('advancing', 0)}", delta=None)
        with col5:
            st.metric("الأسهم الخاسرة", f"{summary.get('declining', 0)}", delta=None)

        st.divider()

        # ── Advancing vs Declining Gauge ──
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown('<div class="section-header">اتساع السوق</div>', unsafe_allow_html=True)
            adv = summary.get("advancing", 0)
            dec = summary.get("declining", 0)
            unch = summary.get("unchanged", 0)
            total = adv + dec + unch

            fig_breadth = go.Figure(go.Pie(
                labels=["رابحة", "خاسرة", "دون تغيير"],
                values=[adv, dec, unch],
                hole=0.55,
                marker=dict(colors=["#00C853", "#FF1744", "#FFD54F"]),
                textinfo="label+value",
                textfont=dict(size=13),
            ))
            fig_breadth.update_layout(
                height=320,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                showlegend=False,
                annotations=[dict(
                    text=f"<b>{total}</b><br>سهم",
                    x=0.5, y=0.5, font_size=18, showarrow=False,
                    font=dict(color="#FAFAFA"),
                )],
            )
            st.plotly_chart(fig_breadth, use_container_width=True)

        with col_right:
            st.markdown('<div class="section-header">مقياس مزاج السوق</div>', unsafe_allow_html=True)

            mood_scores = {
                "very_bearish": 0, "bearish": 1, "moderately_bearish": 2,
                "neutral": 3, "moderately_bullish": 4, "bullish": 5, "very_bullish": 6,
            }
            score = mood_scores.get(mood_raw, 3)

            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": f"  {mood_label}", "font": {"size": 20, "color": mood_color}},
                gauge=dict(
                    axis=dict(range=[0, 6], tickvals=[0, 1, 2, 3, 4, 5, 6],
                              ticktext=["هبوط\nحاد", "هبوط", "هبوط\nمعتدل", "محايد",
                                        "صعود\nمعتدل", "صعود", "صعود\nقوي"],
                              tickfont=dict(size=9)),
                    bar=dict(color=mood_color, thickness=0.3),
                    bgcolor="#1A1F2E",
                    steps=[
                        dict(range=[0, 2], color="#3E2723"),
                        dict(range=[2, 4], color="#3E3E1A"),
                        dict(range=[4, 6], color="#1B3E23"),
                    ],
                    threshold=dict(line=dict(color=mood_color, width=3), thickness=0.8, value=score),
                ),
            ))
            fig_gauge.update_layout(
                height=320,
                margin=dict(t=40, b=20, l=40, r=40),
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

        # ── Quick Gainers / Losers Preview ──
        st.divider()
        col_g, col_l = st.columns(2)

        gainers = get_gainers(5)
        losers = get_losers(5)

        with col_g:
            st.markdown('<div class="section-header">أعلى 5 رابحة</div>', unsafe_allow_html=True)
            if gainers:
                for s in gainers.get("gainers", []):
                    name = s.get("name_en") or s.get("name", "")
                    st.markdown(
                        f"**{s['symbol']}** — {name}  \n"
                        f"<span style='color:#00C853;font-weight:600'>"
                        f"+{s['change_percent']:.2f}%</span> &nbsp; SAR {s['price']}",
                        unsafe_allow_html=True,
                    )

        with col_l:
            st.markdown('<div class="section-header">أعلى 5 خاسرة</div>', unsafe_allow_html=True)
            if losers:
                for s in losers.get("losers", []):
                    name = s.get("name_en") or s.get("name", "")
                    st.markdown(
                        f"**{s['symbol']}** — {name}  \n"
                        f"<span style='color:#FF1744;font-weight:600'>"
                        f"{s['change_percent']:.2f}%</span> &nbsp; SAR {s['price']}",
                        unsafe_allow_html=True,
                    )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 2: Top Movers
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "الأكثر تحركاً":
    st.markdown("## الأكثر تحركاً")

    tab1, tab2, tab3, tab4 = st.tabs(["الرابحة", "الخاسرة", "الأعلى كمية", "الأعلى قيمة"])

    limit = st.sidebar.slider("عدد النتائج", 5, 50, 15)

    # ── Gainers Tab ──
    with tab1:
        data = get_gainers(limit)
        if data and data.get("gainers"):
            df = pd.DataFrame(data["gainers"])
            df["display_name"] = df.apply(lambda r: r["name_en"] if r["name_en"] else r["name"], axis=1)

            fig = px.bar(
                df, x="symbol", y="change_percent",
                color="change_percent",
                color_continuous_scale=["#A5D6A7", "#00C853", "#1B5E20"],
                hover_data=["display_name", "price", "volume"],
                labels={"change_percent": "نسبة التغير %", "symbol": "الرمز"},
                title="أعلى الرابحة حسب نسبة التغير",
            )
            fig.update_layout(
                height=450,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#2D3748"),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                df[["symbol", "display_name", "price", "change", "change_percent", "volume"]].rename(
                    columns={"display_name": "الاسم", "price": "السعر (ر.س)", "change": "التغير",
                             "change_percent": "التغير %", "volume": "الكمية", "symbol": "الرمز"}
                ),
                use_container_width=True, hide_index=True,
            )

    # ── Losers Tab ──
    with tab2:
        data = get_losers(limit)
        if data and data.get("losers"):
            df = pd.DataFrame(data["losers"])
            df["display_name"] = df.apply(lambda r: r["name_en"] if r["name_en"] else r["name"], axis=1)

            fig = px.bar(
                df, x="symbol", y="change_percent",
                color="change_percent",
                color_continuous_scale=["#B71C1C", "#FF1744", "#FF8A80"],
                hover_data=["display_name", "price", "volume"],
                labels={"change_percent": "نسبة التغير %", "symbol": "الرمز"},
                title="أعلى الخاسرة حسب نسبة التغير",
            )
            fig.update_layout(
                height=450,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#2D3748"),
                coloraxis_showscale=False,
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                df[["symbol", "display_name", "price", "change", "change_percent", "volume"]].rename(
                    columns={"display_name": "الاسم", "price": "السعر (ر.س)", "change": "التغير",
                             "change_percent": "التغير %", "volume": "الكمية", "symbol": "الرمز"}
                ),
                use_container_width=True, hide_index=True,
            )

    # ── Volume Leaders Tab ──
    with tab3:
        data = get_volume_leaders(limit)
        if data and data.get("stocks"):
            df = pd.DataFrame(data["stocks"])
            df["display_name"] = df.apply(lambda r: r.get("name_en") or r["name"], axis=1)

            fig = px.bar(
                df, x="symbol", y="volume",
                color="change_percent",
                color_continuous_scale=["#FF1744", "#FFD54F", "#00C853"],
                color_continuous_midpoint=0,
                hover_data=["display_name", "price", "change_percent"],
                labels={"volume": "الكمية", "symbol": "الرمز"},
                title="الأسهم الأعلى كمية تداول",
            )
            fig.update_layout(
                height=450,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#2D3748"),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Value Leaders Tab ──
    with tab4:
        data = get_value_leaders(limit)
        if data and data.get("stocks"):
            df = pd.DataFrame(data["stocks"])
            df["display_name"] = df.apply(lambda r: r.get("name_en") or r["name"], axis=1)
            df["value_m"] = df["value"] / 1_000_000

            fig = px.bar(
                df, x="symbol", y="value_m",
                color="change_percent",
                color_continuous_scale=["#FF1744", "#FFD54F", "#00C853"],
                color_continuous_midpoint=0,
                hover_data=["display_name", "price"],
                labels={"value_m": "القيمة (مليون ر.س)", "symbol": "الرمز"},
                title="الأسهم الأعلى قيمة تداول (ر.س)",
            )
            fig.update_layout(
                height=450,
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#2D3748"),
            )
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 3: Sector Performance
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "أداء القطاعات":
    st.markdown("## أداء القطاعات")

    sectors_data = get_sectors()
    if sectors_data and sectors_data.get("sectors"):
        df = pd.DataFrame(sectors_data["sectors"])
        df["sector_name"] = df["id"].map(SECTOR_NAMES).fillna(df["id"])
        df["avg_pct"] = df["avg_change_percent"] * 100  # convert to percentage
        df["direction"] = df["avg_pct"].apply(lambda x: "إيجابي" if x > 0 else ("سلبي" if x < 0 else "مستقر"))

        # ── Treemap ──
        st.markdown('<div class="section-header">خريطة حرارية للقطاعات</div>', unsafe_allow_html=True)

        df["abs_volume"] = df["volume"].clip(lower=1)
        df["display_pct"] = df["avg_pct"].apply(lambda x: f"{x:+.2f}%")

        fig_tree = px.treemap(
            df,
            path=["sector_name"],
            values="abs_volume",
            color="avg_pct",
            color_continuous_scale=["#B71C1C", "#FF1744", "#FF8A80", "#FAFAFA", "#A5D6A7", "#00C853", "#1B5E20"],
            color_continuous_midpoint=0,
            hover_data={"avg_pct": ":.3f", "volume": ":,", "num_stocks": True},
            custom_data=["display_pct", "num_stocks"],
        )
        fig_tree.update_traces(
            texttemplate="<b>%{label}</b><br>%{customdata[0]}<br>%{customdata[1]} سهم",
            textfont=dict(size=13),
        )
        fig_tree.update_layout(
            height=500,
            margin=dict(t=30, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            coloraxis_colorbar=dict(title="متوسط التغير %"),
        )
        st.plotly_chart(fig_tree, use_container_width=True)

        # ── Horizontal Bar ──
        st.markdown('<div class="section-header">متوسط تغير القطاعات</div>', unsafe_allow_html=True)

        df_sorted = df.sort_values("avg_pct", ascending=True)

        fig_bar = px.bar(
            df_sorted, x="avg_pct", y="sector_name",
            orientation="h",
            color="avg_pct",
            color_continuous_scale=["#B71C1C", "#FF8A80", "#FAFAFA", "#A5D6A7", "#1B5E20"],
            color_continuous_midpoint=0,
            labels={"avg_pct": "متوسط التغير %", "sector_name": "القطاع"},
            hover_data={"volume": ":,", "num_stocks": True},
        )
        fig_bar.update_layout(
            height=600,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#FAFAFA"),
            yaxis=dict(showgrid=False),
            xaxis=dict(showgrid=True, gridcolor="#2D3748", zeroline=True, zerolinecolor="#FAFAFA", zerolinewidth=1),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # ── Summary Table ──
        st.markdown('<div class="section-header">تفاصيل القطاعات</div>', unsafe_allow_html=True)
        st.dataframe(
            df[["sector_name", "avg_pct", "volume", "num_stocks"]].sort_values("avg_pct", ascending=False).rename(
                columns={"sector_name": "القطاع", "avg_pct": "متوسط التغير %",
                         "volume": "الكمية", "num_stocks": "عدد الأسهم"}
            ),
            use_container_width=True, hide_index=True,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 4: Stock Lookup
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "بحث سهم":
    st.markdown("## بحث سهم وتحليل السيولة")

    symbol = st.text_input("أدخل رمز السهم", value="2222", placeholder="مثال: 2222 لأرامكو")

    if symbol:
        quote = get_quote(symbol)
        company = get_company(symbol)

        if quote:
            # ── Company Header ──
            name_en = quote.get("name_en") or quote.get("name", "")
            name_ar = quote.get("name", "")
            st.markdown(f"### {symbol} — {name_en}")
            if name_ar != name_en:
                st.caption(name_ar)

            # ── Price Metrics ──
            col1, col2, col3, col4 = st.columns(4)
            chg_pct = quote.get("change_percent", 0)
            delta_color = "normal"

            with col1:
                st.metric("السعر", f"{quote['price']} ر.س", f"{quote.get('change', 0):+.2f} ({chg_pct:+.2f}%)")
            with col2:
                st.metric("الافتتاح", f"{quote.get('open', 'N/A')} ر.س")
            with col3:
                st.metric("النطاق اليومي", f"{quote.get('low', 'N/A')} — {quote.get('high', 'N/A')}")
            with col4:
                st.metric("الإغلاق السابق", f"{quote.get('previous_close', 'N/A')} ر.س")

            col5, col6, col7, col8 = st.columns(4)
            with col5:
                st.metric("الكمية", fmt_number(quote.get("volume", 0)))
            with col6:
                st.metric("القيمة", fmt_number(quote.get("value", 0), suffix=" ر.س"))
            with col7:
                st.metric("أفضل طلب", f"{quote.get('bid', 'N/A')} ر.س")
            with col8:
                st.metric("أفضل عرض", f"{quote.get('ask', 'N/A')} ر.س")

            st.divider()

            # ── Liquidity Analysis ──
            liq = quote.get("liquidity")
            if liq:
                st.markdown('<div class="section-header">تحليل تدفق السيولة</div>', unsafe_allow_html=True)

                inflow = liq.get("inflow_value", 0)
                outflow = liq.get("outflow_value", 0)
                net = liq.get("net_value", 0)
                total_flow = inflow + outflow

                col_l1, col_l2, col_l3 = st.columns(3)
                with col_l1:
                    st.metric("التدفق الداخل", fmt_number(inflow, suffix=" ر.س"))
                with col_l2:
                    st.metric("التدفق الخارج", fmt_number(outflow, suffix=" ر.س"))
                with col_l3:
                    st.metric("صافي التدفق", fmt_number(net, suffix=" ر.س"),
                              delta=f"ضغط {'شراء' if net > 0 else 'بيع'}")

                # Liquidity Donut
                col_chart1, col_chart2 = st.columns(2)

                with col_chart1:
                    fig_liq = go.Figure(go.Pie(
                        labels=["تدفق داخل (شراء)", "تدفق خارج (بيع)"],
                        values=[inflow, outflow],
                        hole=0.6,
                        marker=dict(colors=["#00C853", "#FF1744"]),
                        textinfo="label+percent",
                        textfont=dict(size=12),
                    ))
                    fig_liq.update_layout(
                        title="توزيع تدفق الأموال",
                        height=350,
                        margin=dict(t=40, b=20, l=20, r=20),
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#FAFAFA"),
                        showlegend=False,
                        annotations=[dict(
                            text=f"<b>{'صافي +' if net > 0 else 'صافي'}<br>{fmt_number(net)}</b>",
                            x=0.5, y=0.5, font_size=14, showarrow=False,
                            font=dict(color="#00C853" if net > 0 else "#FF1744"),
                        )],
                    )
                    st.plotly_chart(fig_liq, use_container_width=True)

                with col_chart2:
                    # Trades comparison
                    fig_trades = go.Figure()
                    fig_trades.add_trace(go.Bar(
                        name="صفقات شراء", x=["الصفقات"], y=[liq.get("inflow_trades", 0)],
                        marker_color="#00C853", text=[liq.get("inflow_trades", 0)], textposition="auto",
                    ))
                    fig_trades.add_trace(go.Bar(
                        name="صفقات بيع", x=["الصفقات"], y=[liq.get("outflow_trades", 0)],
                        marker_color="#FF1744", text=[liq.get("outflow_trades", 0)], textposition="auto",
                    ))
                    fig_trades.add_trace(go.Bar(
                        name="كمية شراء", x=["الكمية"], y=[liq.get("inflow_volume", 0)],
                        marker_color="#00C853",
                        text=[fmt_number(liq.get("inflow_volume", 0))], textposition="auto",
                    ))
                    fig_trades.add_trace(go.Bar(
                        name="كمية بيع", x=["الكمية"], y=[liq.get("outflow_volume", 0)],
                        marker_color="#FF1744",
                        text=[fmt_number(liq.get("outflow_volume", 0))], textposition="auto",
                    ))
                    fig_trades.update_layout(
                        title="شراء مقابل بيع: الصفقات والكمية",
                        barmode="group", height=350,
                        margin=dict(t=40, b=20, l=20, r=20),
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#FAFAFA"),
                        xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor="#2D3748"),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_trades, use_container_width=True)

            # ── Company Info ──
            if company:
                st.divider()
                st.markdown('<div class="section-header">معلومات الشركة</div>', unsafe_allow_html=True)
                col_i1, col_i2 = st.columns([1, 2])
                with col_i1:
                    st.markdown(f"**القطاع:** {company.get('sector', 'N/A')}")
                    st.markdown(f"**الصناعة:** {company.get('industry', 'N/A')}")
                    st.markdown(f"**العملة:** {company.get('currency', 'SAR')}")
                    website = company.get("website")
                    if website:
                        st.markdown(f"**الموقع:** [{website}]({website})")
                with col_i2:
                    desc = company.get("description", "")
                    if desc:
                        with st.expander("وصف الشركة", expanded=False):
                            st.write(desc)
        else:
            st.warning(f"لم يتم العثور على سهم بالرمز **{symbol}**. يرجى التحقق من الرمز والمحاولة مرة أخرى.")


# ═══════════════════════════════════════════════════════════════════════════════
# PAGE 5: Watchlist
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "قائمة المتابعة":
    st.markdown("## قائمة الأسهم القيادية")
    st.caption("أسهم تاسي الرئيسية — أسعار لحظية مع صافي تدفق السيولة")

    data = get_quotes(WATCHLIST_SYMBOLS)

    if data and data.get("quotes"):
        df = pd.DataFrame(data["quotes"])
        df["display_name"] = df.apply(lambda r: r.get("name_en") or r["name"], axis=1)

        # ── Summary Cards ──
        cols = st.columns(5)
        for i, row in df.head(5).iterrows():
            with cols[i]:
                chg = row.get("change_percent", 0)
                delta_str = f"{chg:+.2f}%"
                st.metric(
                    label=f"{row['symbol']} — {row['display_name'][:20]}",
                    value=f"SAR {row['price']}",
                    delta=delta_str,
                )

        if len(df) > 5:
            cols2 = st.columns(5)
            for i, row in df.iloc[5:10].iterrows():
                with cols2[i - 5]:
                    chg = row.get("change_percent", 0)
                    delta_str = f"{chg:+.2f}%"
                    st.metric(
                        label=f"{row['symbol']} — {row['display_name'][:20]}",
                        value=f"SAR {row['price']}",
                        delta=delta_str,
                    )

        st.divider()

        # ── Net Liquidity Chart ──
        st.markdown('<div class="section-header">صافي تدفق السيولة (ضغط الشراء مقابل البيع)</div>',
                    unsafe_allow_html=True)

        if "net_liquidity" in df.columns:
            df["net_liq_m"] = df["net_liquidity"] / 1_000_000
            df_sorted = df.sort_values("net_liq_m", ascending=True)

            colors = ["#00C853" if x > 0 else "#FF1744" for x in df_sorted["net_liq_m"]]

            fig_liq = go.Figure(go.Bar(
                x=df_sorted["net_liq_m"],
                y=df_sorted["display_name"],
                orientation="h",
                marker_color=colors,
                text=df_sorted["net_liq_m"].apply(lambda x: f"{x:+.2f} م.ر.س"),
                textposition="auto",
                textfont=dict(size=12),
            ))
            fig_liq.update_layout(
                height=450,
                margin=dict(t=20, b=20, l=20, r=20),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#FAFAFA"),
                xaxis=dict(title="صافي السيولة (مليون ر.س)", showgrid=True, gridcolor="#2D3748",
                           zeroline=True, zerolinecolor="#FAFAFA", zerolinewidth=1),
                yaxis=dict(showgrid=False),
            )
            st.plotly_chart(fig_liq, use_container_width=True)

            st.info(
                "**كيف تقرأ هذا الرسم:** الأعمدة الخضراء = ضغط شراء صافي (أموال تدخل أكثر). "
                "الأعمدة الحمراء = ضغط بيع صافي (أموال تخرج أكثر). "
                "هذا مؤشر مؤسسي رئيسي يوضح اتجاه الأموال الذكية."
            )

        # ── Full Table ──
        st.divider()
        st.markdown('<div class="section-header">تفاصيل قائمة المتابعة</div>', unsafe_allow_html=True)

        display_cols = ["symbol", "display_name", "price", "change", "change_percent", "volume"]
        if "net_liquidity" in df.columns:
            df["net_liquidity_fmt"] = df["net_liquidity"].apply(lambda x: f"{x / 1e6:+.2f} م.ر.س")
            display_cols.append("net_liquidity_fmt")

        st.dataframe(
            df[display_cols].rename(columns={
                "symbol": "الرمز", "display_name": "الاسم", "price": "السعر (ر.س)", "change": "التغير",
                "change_percent": "التغير %", "volume": "الكمية", "net_liquidity_fmt": "صافي السيولة",
            }),
            use_container_width=True, hide_index=True,
        )
