import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from pytrends.request import TrendReq
from datetime import datetime, timedelta
import os
import base64
from pathlib import Path

# ── PAGE CONFIG ──────────────────────────────────────────────
def load_logo(path="logo.png"):
    p = Path(path)
    if p.exists():
        with open(p, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        ext = p.suffix.replace(".", "")
        return f"data:image/{ext};base64,{data}"
    return None

# Load logo untuk favicon
_logo_path = Path("logo.png")
_favicon = _logo_path if _logo_path.exists() else "📊"

st.set_page_config(
    page_title="IHSG Fear & Greed Index",
    page_icon=_favicon,        # ← pakai logo.png kalau ada
    layout="wide"
)

# ── CUSTOM CSS (desktop + mobile responsive) ─────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

:root {
    --bg     : #0d1117;
    --card   : #161b22;
    --border : #30363d;
    --text   : #e6edf3;
    --muted  : #8b949e;
}

html, body, [class*="css"] {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', sans-serif;
}

/* DESKTOP */
.block-container { padding: 2rem 3rem !important; }

.metric-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
}

.badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: 'Space Mono', monospace;
}

.section-title {
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 0.6rem;
    margin-top: 1rem;
}

.desc-box {
    background: var(--card);
    border: 1px solid var(--border);
    border-left: 3px solid #f6c90e;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-top: 1rem;
}

.desc-box h4 {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    color: #f6c90e;
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.desc-box p {
    font-size: 0.82rem;
    color: var(--muted);
    line-height: 1.6;
    margin: 0;
}

.footer {
    text-align: center;
    color: var(--muted);
    font-size: 0.72rem;
    padding: 1.5rem 0 0.5rem;
    border-top: 1px solid var(--border);
    margin-top: 2rem;
}

div[data-testid="stMetric"] {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem 1rem;
}

div[data-testid="stMetricValue"] { color: var(--text) !important; }

/* MOBILE (<768px) */
@media (max-width: 768px) {
    .block-container { padding: 0.8rem 0.8rem !important; }

    /* Stack semua kolom jadi vertikal */
    div[data-testid="stHorizontalBlock"] {
        flex-direction: column !important;
        gap: 0 !important;
    }
    div[data-testid="stHorizontalBlock"] > div {
        width: 100% !important;
        min-width: 100% !important;
        flex: unset !important;
    }

    /* Metric cards lebih compact */
    .metric-card { padding: 0.7rem 0.9rem; margin-bottom: 0.4rem; }

    /* Badge lebih kecil */
    .badge { font-size: 0.68rem; padding: 2px 7px; }

    /* Section title lebih kecil */
    .section-title { font-size: 0.85rem; }

    /* Desc box */
    .desc-box { padding: 0.9rem 1rem; }
    .desc-box p { font-size: 0.78rem; }

    /* Metric value */
    div[data-testid="stMetricValue"] { font-size: 1.1rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 0.75rem !important; }

    /* Sembunyikan scrollbar horizontal */
    .main .block-container { overflow-x: hidden; }

    /* Tab lebih compact */
    button[data-baseweb="tab"] { font-size: 0.78rem !important; padding: 6px 10px !important; }
}
</style>
""", unsafe_allow_html=True)

# ── HELPERS ──────────────────────────────────────────────────
def warna_skor(skor):
    if skor >= 75: return "#38a169"
    if skor >= 55: return "#68d391"
    if skor >= 45: return "#ecc94b"
    if skor >= 25: return "#ed8936"
    return "#e53e3e"

def label_skor(skor):
    if skor >= 75: return "Extreme Greed"
    if skor >= 55: return "Greed"
    if skor >= 45: return "Neutral"
    if skor >= 25: return "Fear"
    return "Extreme Fear"

def hitung_rsi(data, period=14):
    delta     = data.diff()
    naik      = delta.clip(lower=0)
    turun     = -delta.clip(upper=0)
    avg_naik  = naik.ewm(com=period-1, adjust=False).mean()
    avg_turun = turun.ewm(com=period-1, adjust=False).mean()
    rs        = avg_naik / avg_turun
    return 100 - (100 / (1 + rs))

def normalisasi(series, window=90):
    recent  = series.dropna().tail(window)
    min_val = float(recent.min())
    max_val = float(recent.max())
    nilai   = float(series.dropna().iloc[-1])
    if max_val == min_val:
        return 50.0
    return round((nilai - min_val) / (max_val - min_val) * 100, 1)

def filter_hari(df, hari):
    if hari >= 9999:
        return df
    cutoff = df.index[-1] - timedelta(days=hari)
    return df[df.index >= cutoff]

# ── LOAD DATA ────────────────────────────────────────────────
@st.cache_data(ttl=900)
def load_data():
    ihsg = yf.download("^JKSE", period="5y", progress=False)
    idr  = yf.download("IDR=X", period="5y", progress=False)["Close"].squeeze()
    pytrends = TrendReq(hl='id-ID', tz=420)
    pytrends.build_payload(
        ["IHSG","rupiah","saham","investasi","bursa"],
        timeframe='today 5-y', geo='ID'
    )
    trends_data = pytrends.interest_over_time()
    if 'isPartial' in trends_data.columns:
        trends_data = trends_data.drop(columns=['isPartial'])
    return ihsg, idr, trends_data

@st.cache_data(ttl=900)
def hitung_semua(ihsg, idr, trends_data):
    close    = ihsg["Close"].squeeze()
    volume   = ihsg["Volume"].squeeze()
    idr_ch   = idr.pct_change(10)
    bobot_kw = {"IHSG":0.30,"rupiah":0.30,"saham":0.20,"investasi":0.15,"bursa":0.05}
    tr_skor  = sum(trends_data[kw]*b for kw,b in bobot_kw.items())
    tr_daily = tr_skor.resample("D").ffill()
    tr_align = tr_daily.reindex(close.index, method="ffill")
    ma50     = close.rolling(50).mean()
    momentum = (close - ma50) / ma50 * 100
    rsi      = hitung_rsi(close)
    vol_r    = volume.rolling(5).mean() / volume.rolling(90).mean()
    idr_inv  = -idr_ch
    s_mom = normalisasi(momentum)
    s_rsi = normalisasi(rsi)
    s_vol = normalisasi(vol_r)
    s_idr = normalisasi(idr_inv)
    s_tr  = normalisasi(tr_align)
    skor_hari_ini = round(s_mom*0.25 + s_rsi*0.20 + s_vol*0.20 + s_idr*0.20 + s_tr*0.15, 1)
    csv_path = "data/historis.csv"
    if os.path.exists(csv_path):
        df_hist = pd.read_csv(csv_path, index_col="date", parse_dates=True)
    else:
        df_hist = pd.DataFrame(columns=["skor","close"])
    return skor_hari_ini, s_mom, s_rsi, s_vol, s_idr, s_tr, df_hist, float(close.iloc[-1]), float(idr.iloc[-1])

# ── LOAD ─────────────────────────────────────────────────────
with st.spinner("Mengambil data terbaru..."):
    ihsg, idr, trends_data = load_data()
    skor, s_mom, s_rsi, s_vol, s_idr, s_tr, df_hist, harga_ihsg, kurs_idr = hitung_semua(ihsg, idr, trends_data)

# ── HEADER ───────────────────────────────────────────────────
logo_src  = load_logo("logo.png")
logo_html = f'<img src="{logo_src}" style="width:110px;height:110px;object-fit:contain;border-radius:12px;display:block;margin-left:auto;">' if logo_src else '<div style="width:110px;height:110px;border:1px dashed #30363d;border-radius:12px;display:flex;align-items:center;justify-content:center;color:#8b949e;font-size:0.65rem;margin-left:auto;">LOGO</div>'

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:0.5rem 0 0.5rem;flex-wrap:wrap;gap:8px;">
    <div>
        <div style="font-family:'Space Mono',monospace;font-size:clamp(1rem,3vw,1.4rem);font-weight:700;color:#e6edf3;line-height:1.3;">
            IHSG Fear &amp; Greed Index
        </div>
        <div style="color:#8b949e;font-size:clamp(0.7rem,2vw,0.83rem);margin-top:4px;">
            Indeks sentimen pasar saham Indonesia &nbsp;·&nbsp; Update harian setelah market tutup 15.30 WIB
        </div>
    </div>
    {logo_html}
</div>
""", unsafe_allow_html=True)

st.divider()

# ── MAIN LAYOUT ──────────────────────────────────────────────
col_kiri, col_kanan = st.columns([1, 2], gap="large")

# ── KOLOM KIRI ───────────────────────────────────────────────
with col_kiri:
    warna = warna_skor(skor)
    label = label_skor(skor)

    fig_gauge = go.Figure(go.Indicator(
        mode   = "gauge+number",
        value  = skor,
        number = {"font": {"size": 52, "color": warna, "family": "Space Mono"}},
        gauge  = {
            "axis"       : {"range": [0,100], "tickcolor": "#8b949e", "tickfont": {"color": "#8b949e", "size": 10}},
            "bar"        : {"color": warna, "thickness": 0.25},
            "bgcolor"    : "#161b22",
            "bordercolor": "#30363d",
            "steps"      : [
                {"range": [0,  25], "color": "#2d1515"},
                {"range": [25, 45], "color": "#2d1e0f"},
                {"range": [45, 55], "color": "#2d2a0f"},
                {"range": [55, 75], "color": "#0f2d1a"},
                {"range": [75,100], "color": "#0a2318"},
            ],
            "threshold": {"line": {"color": warna, "width": 4}, "value": skor}
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        height=240,
        margin=dict(t=20, b=0, l=10, r=10)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.markdown(f'<div style="text-align:center;margin-top:-1rem;margin-bottom:1.2rem;"><span class="badge" style="background:{warna}22;color:{warna};border:1px solid {warna}55;font-size:1rem;padding:6px 24px;">{label}</span></div>', unsafe_allow_html=True)

    # Historical Values
    st.markdown('<p class="section-title">Historical Values</p>', unsafe_allow_html=True)
    if len(df_hist) > 0:
        def get_hist(days):
            target = df_hist.index[-1] - timedelta(days=days)
            row    = df_hist.iloc[(df_hist.index - target).abs().argsort()[0]]
            return float(row["skor"])
        for period_label, days in [("Yesterday", 1), ("Last Week", 7), ("Last Month", 30)]:
            try:
                s = get_hist(days)
                w = warna_skor(s); l = label_skor(s)
                st.markdown(f'<div class="metric-card" style="display:flex;justify-content:space-between;align-items:center;"><span style="color:#8b949e;font-size:0.83rem;">{period_label}</span><span class="badge" style="background:{w}22;color:{w};border:1px solid {w}55;">{l} &mdash; {s}</span></div>', unsafe_allow_html=True)
            except Exception:
                pass
    else:
        st.markdown('<p style="color:#8b949e;font-size:0.82rem;">Data historis belum tersedia</p>', unsafe_allow_html=True)

    # Yearly High & Low
    st.markdown('<p class="section-title">Yearly High & Low</p>', unsafe_allow_html=True)
    if len(df_hist) > 0:
        df_year  = filter_hari(df_hist, 365)
        idx_high = df_year["skor"].idxmax()
        idx_low  = df_year["skor"].idxmin()
        for lbl, s_val, idx in [("Yearly High", float(df_year["skor"].max()), idx_high), ("Yearly Low", float(df_year["skor"].min()), idx_low)]:
            w = warna_skor(s_val); l = label_skor(s_val)
            tgl = pd.Timestamp(idx).strftime("%b %d, %Y")
            st.markdown(f'<div class="metric-card" style="display:flex;justify-content:space-between;align-items:center;"><span style="color:#8b949e;font-size:0.83rem;">{lbl}<br><span style="font-size:0.72rem;">({tgl})</span></span><span class="badge" style="background:{w}22;color:{w};border:1px solid {w}55;">{l} &mdash; {s_val}</span></div>', unsafe_allow_html=True)

    # Deskripsi
    st.markdown("""
    <div class="desc-box">
        <h4>Tentang Indeks Ini</h4>
        <p>
            IHSG Fear &amp; Greed Index mengukur sentimen pasar saham Indonesia menggunakan
            5 indikator: momentum harga (MA50), RSI, volume perdagangan, pergerakan kurs
            rupiah, dan tren pencarian publik via Google Trends.<br><br>
            <b style="color:#e53e3e;">0–24</b> Extreme Fear &nbsp;·&nbsp;
            <b style="color:#ed8936;">25–44</b> Fear &nbsp;·&nbsp;
            <b style="color:#ecc94b;">45–54</b> Neutral &nbsp;·&nbsp;
            <b style="color:#68d391;">55–74</b> Greed &nbsp;·&nbsp;
            <b style="color:#38a169;">75–100</b> Extreme Greed<br><br>
            Bukan rekomendasi investasi.
        </p>
    </div>
    """, unsafe_allow_html=True)

# ── KOLOM KANAN ──────────────────────────────────────────────
with col_kanan:
    m1, m2, m3 = st.columns(3)
    m1.metric("IHSG", f"{harga_ihsg:,.2f}")
    m2.metric("USD/IDR", f"{kurs_idr:,.0f}")
    m3.metric("Update", datetime.now().strftime("%d %b %Y %H:%M"))

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📈 Chart Historis", "🔍 Breakdown Indikator"])

    with tab1:
        periode  = st.selectbox("Periode", ["30 Hari", "90 Hari", "1 Tahun", "Semua"], index=2)
        hari_map = {"30 Hari": 30, "90 Hari": 90, "1 Tahun": 365, "Semua": 9999}
        df_plot  = filter_hari(df_hist, hari_map[periode])

        fig = go.Figure()
        for y0, y1, color in [(0,25,"rgba(229,62,62,0.08)"),(25,45,"rgba(237,137,54,0.06)"),(45,55,"rgba(236,201,75,0.06)"),(55,75,"rgba(104,211,145,0.06)"),(75,100,"rgba(56,161,105,0.08)")]:
            fig.add_hrect(y0=y0, y1=y1, fillcolor=color, line_width=0)

        fig.add_trace(go.Scatter(
            x=df_plot.index, y=df_plot["skor"],
            name="Fear & Greed",
            line=dict(width=2.5, color="#f6c90e"),
            fill="tozeroy", fillcolor="rgba(246,201,14,0.06)"
        ))
        fig.add_trace(go.Scatter(
            x=df_plot.index, y=df_plot["close"],
            name="IHSG", yaxis="y2",
            line=dict(width=1.5, color="#8b949e", dash="dot"),
        ))
        for y, txt in [(12,"Extreme Fear"),(35,"Fear"),(50,"Neutral"),(65,"Greed"),(87,"Extreme Greed")]:
            fig.add_annotation(x=df_plot.index[-1], y=y, text=txt, showarrow=False, xanchor="right", font=dict(size=9, color="#8b949e"))

        fig.update_layout(
            paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
            font_color="#e6edf3",
            height=420,
            margin=dict(t=10, b=20, l=0, r=50),
            legend=dict(
                bgcolor="#161b22", bordercolor="#30363d", borderwidth=1,
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            xaxis=dict(gridcolor="#21262d", fixedrange=False),
            yaxis=dict(gridcolor="#21262d", range=[0,100], title="Skor F&G", fixedrange=False),
            yaxis2=dict(overlaying="y", side="right", showgrid=False, title="IHSG", fixedrange=False),
            hovermode="x unified",
            dragmode="pan"
        )
        st.plotly_chart(fig, use_container_width=True, config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d","lasso2d"],
            "responsive": True
        })

    with tab2:
        st.markdown("<br>", unsafe_allow_html=True)
        indikator = [
            ("Momentum (MA50)", s_mom, 0.25, "Jarak IHSG dari MA50 — di bawah MA = fear"),
            ("RSI 14 Hari",     s_rsi, 0.20, "RSI < 30 oversold (fear), > 70 overbought (greed)"),
            ("Volume Pasar",    s_vol, 0.20, "Volume 5 hari vs 90 hari — volume rendah = lesu"),
            ("Kurs Rupiah",     s_idr, 0.20, "Rupiah melemah = investor asing cabut = fear"),
            ("Sentimen Publik", s_tr,  0.15, "Google Trends: IHSG, rupiah, saham, investasi, bursa"),
        ]
        for nama, skor_i, bbt, desc in indikator:
            w = warna_skor(skor_i); lb = label_skor(skor_i)
            st.markdown(f"""
            <div class="metric-card">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;flex-wrap:wrap;gap:4px;">
                    <span style="font-weight:500;font-size:0.9rem;">{nama}</span>
                    <div>
                        <span class="badge" style="background:{w}22;color:{w};border:1px solid {w}55;margin-right:4px;">{lb}</span>
                        <span style="font-family:'Space Mono',monospace;font-size:0.9rem;color:{w};">{skor_i}</span>
                    </div>
                </div>
                <div style="background:#21262d;border-radius:4px;height:6px;margin-bottom:6px;">
                    <div style="background:{w};width:{int(skor_i)}%;height:6px;border-radius:4px;"></div>
                </div>
                <span style="font-size:0.75rem;color:#8b949e;">Bobot {int(bbt*100)}% &nbsp;·&nbsp; {desc}</span>
            </div>""", unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
    <p>© {datetime.now().year} IHSG Fear & Greed Index &nbsp;·&nbsp; Data bersifat indikatif, bukan rekomendasi investasi &nbsp;·&nbsp;
    <a href="mailto:mugenworklabs@gmail.com" style="color:#8b949e;text-decoration:none;">mugenworklabs@gmail.com</a></p>
</div>
""", unsafe_allow_html=True)