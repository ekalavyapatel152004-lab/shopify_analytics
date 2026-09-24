"""
Shopify Sales Analytics — Professional 3-Page Streamlit Dashboard
Pages: 1·Sales Analysis  2·Customer Analysis  3·Geography & Payment
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os, io

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shopify Sales Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* body */
html, body, [class*="css"] { font-family:"Segoe UI",Arial,sans-serif; }
.block-container { padding-top:1rem; padding-bottom:2rem; }
.main { background:#f0f2f6; }

/* sidebar */
section[data-testid="stSidebar"]               { background:#161d31; }
section[data-testid="stSidebar"] *             { color:#c9d1e9 !important; }
section[data-testid="stSidebar"] hr            { border-color:#2a3150; }
section[data-testid="stSidebar"] .stRadio label{ font-size:14px; padding:4px 0; }

/* page banner */
.page-banner {
    background:linear-gradient(135deg,#1a2340 0%,#1e4080 100%);
    border-radius:12px; padding:20px 28px 16px 28px;
    margin-bottom:22px; border-left:5px solid #4a90d9;
}
.page-banner h2 { color:#fff; font-size:20px; font-weight:700; margin:0 0 4px 0; }
.page-banner p  { color:#90aad0; font-size:13px; margin:0; }

/* KPI strip */
.kpi-strip { display:flex; gap:12px; flex-wrap:wrap; margin-bottom:18px; }
.kpi-box {
    flex:1; min-width:140px; background:#fff; border-radius:10px;
    padding:14px 18px; box-shadow:0 1px 6px rgba(0,0,0,.08);
    border-top:4px solid #4a90d9;
}
.kpi-box.c1{border-top-color:#4a90d9;}
.kpi-box.c2{border-top-color:#00c4a7;}
.kpi-box.c3{border-top-color:#f0934a;}
.kpi-box.c4{border-top-color:#e05580;}
.kpi-box.c5{border-top-color:#8b6fd4;}
.kpi-title { font-size:10px; color:#6b7a99; font-weight:700;
             text-transform:uppercase; letter-spacing:.6px; margin-bottom:6px; }
.kpi-val   { font-size:24px; font-weight:800; color:#1a2340; line-height:1.1; }
.kpi-note  { font-size:11px; color:#9aa3bc; margin-top:4px; }

/* section label */
.sec-lbl {
    font-size:13px; font-weight:700; color:#1a2340;
    border-left:4px solid #4a90d9; padding-left:10px;
    margin:20px 0 10px; text-transform:uppercase; letter-spacing:.4px;
}

/* filter row */
div[data-testid="stExpander"] > details > summary {
    background:#e8ecf4; border-radius:8px; font-size:13px;
    font-weight:600; color:#1a2340 !important;
}

/* download button */
.stDownloadButton button {
    background:#4a90d9!important; color:#fff!important;
    border:none!important; border-radius:8px!important;
    font-weight:600!important; padding:8px 20px!important;
}
/* reset button */
div[data-testid="stButton"] button {
    background:#e05580!important; color:#fff!important;
    border:none!important; border-radius:8px!important;
    font-weight:600!important; padding:8px 20px!important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COLOURS & CHART DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
C_BLUE   = "#4a90d9"
C_TEAL   = "#00c4a7"
C_AMBER  = "#f0934a"
C_PINK   = "#e05580"
C_PURPLE = "#8b6fd4"
C_GREEN  = "#27ae60"
C_SLATE  = "#7f8fa6"

PALETTE = [C_BLUE, C_TEAL, C_AMBER, C_PINK, C_PURPLE, C_GREEN, C_SLATE,
           "#f1c40f", "#e67e22", "#1abc9c", "#9b59b6", "#e74c3c"]

_BASE = dict(
    plot_bgcolor  = "#ffffff",
    paper_bgcolor = "#ffffff",
    font          = dict(family="Segoe UI,Arial,sans-serif", color="#333", size=12),
    hoverlabel    = dict(bgcolor="#1a2340", font_color="#fff", font_size=12),
    title_font    = dict(size=13, color="#1a2340"),
    title_x       = 0,
)

def _lay(h=360, t=44, b=50, l=60, r=30):
    """Return a layout dict with base styles, height, and margins.
    Callers pass margin edges directly — no duplicate-key conflict."""
    return dict(**_BASE, height=h, margin=dict(t=t, b=b, l=l, r=r))

STATE_ABBREV = {
    'Alabama':'AL','Alaska':'AK','Arizona':'AZ','Arkansas':'AR','California':'CA',
    'Colorado':'CO','Connecticut':'CT','Delaware':'DE','District Of Columbia':'DC',
    'Florida':'FL','Georgia':'GA','Hawaii':'HI','Idaho':'ID','Illinois':'IL',
    'Indiana':'IN','Iowa':'IA','Kansas':'KS','Kentucky':'KY','Louisiana':'LA',
    'Maine':'ME','Maryland':'MD','Massachusetts':'MA','Michigan':'MI','Minnesota':'MN',
    'Mississippi':'MS','Missouri':'MO','Montana':'MT','Nebraska':'NE','Nevada':'NV',
    'New Hampshire':'NH','New Jersey':'NJ','New Mexico':'NM','New York':'NY',
    'North Carolina':'NC','North Dakota':'ND','Ohio':'OH','Oklahoma':'OK','Oregon':'OR',
    'Pennsylvania':'PA','Rhode Island':'RI','South Carolina':'SC','South Dakota':'SD',
    'Tennessee':'TN','Texas':'TX','Utah':'UT','Vermont':'VT','Virginia':'VA',
    'Washington':'WA','West Virginia':'WV','Wisconsin':'WI','Wyoming':'WY'
}

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def fc(v):
    """Format currency."""
    if v >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if v >= 1_000:     return f"${v/1_000:.1f}K"
    return f"${v:,.0f}"

def fn(v):
    """Format number."""
    if v >= 1_000_000: return f"{v/1_000_000:.2f}M"
    if v >= 1_000:     return f"{v/1_000:.1f}K"
    return f"{int(v):,}"

def kpis(cards):
    """Render a flex row of KPI boxes. cards = [(title,val,note,cls), ...]"""
    cls_map = ["c1","c2","c3","c4","c5"]
    html = '<div class="kpi-strip">'
    for i, (title, val, note) in enumerate(cards):
        c = cls_map[i % 5]
        html += (f'<div class="kpi-box {c}">'
                 f'<div class="kpi-title">{title}</div>'
                 f'<div class="kpi-val">{val}</div>'
                 f'<div class="kpi-note">{note}</div>'
                 f'</div>')
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

def sec(t):
    st.markdown(f'<div class="sec-lbl">{t}</div>', unsafe_allow_html=True)

def show(fig, h=360):
    """Render plotly chart directly (no wrapping div — avoids Streamlit clipping)."""
    fig.update_layout(height=h)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def hbar(df_in, x_col, y_col, title, color=C_BLUE, h=400, text_fmt=None):
    """
    Horizontal bar chart.  Adds right-side padding so 'outside' labels never clip.
    Always renders labels INSIDE bars when bar is large enough, OUTSIDE when small.
    """
    df_in = df_in.sort_values(x_col)
    max_val = df_in[x_col].max()
    labels  = [text_fmt(v) if text_fmt else str(v) for v in df_in[x_col]]
    fig = go.Figure(go.Bar(
        x=df_in[x_col], y=df_in[y_col].astype(str),
        orientation="h",
        marker_color=color, marker_line_width=0,
        text=labels,
        textposition="auto",
        textfont=dict(size=11, color="#fff"),
        insidetextanchor="middle",
        hovertemplate=f"<b>%{{y}}</b><br>{title}: %{{x:,}}<extra></extra>",
        cliponaxis=False,
    ))
    fig.update_layout(**_lay(h=h, t=44, b=40, l=140, r=20), title=title,
        xaxis=dict(range=[0, max_val * 1.22], showgrid=True,
                   gridcolor="#eef1f8", tickformat=",.0f",
                   title=""),
        yaxis=dict(title="", tickfont=dict(size=11)),
    )
    return fig

def vbar(df_in, x_col, y_col, title, colors=None, h=360, text_fmt=None, xangle=0):
    """Vertical bar chart with inside-middle text."""
    labels = [text_fmt(v) if text_fmt else str(v) for v in df_in[y_col]]
    bar_colors = colors if colors else C_BLUE
    fig = go.Figure(go.Bar(
        x=df_in[x_col].astype(str), y=df_in[y_col],
        marker_color=bar_colors, marker_line_width=0,
        text=labels,
        textposition="auto",
        textfont=dict(size=11, color="#fff"),
        insidetextanchor="middle",
        hovertemplate="<b>%{x}</b><br>%{y:,}<extra></extra>",
        cliponaxis=False,
    ))
    max_val = df_in[y_col].max()
    fig.update_layout(**_lay(h=h, t=44, b=60, l=60, r=20), title=title,
        xaxis=dict(title="", tickangle=xangle),
        yaxis=dict(title="", gridcolor="#eef1f8",
                   range=[0, max_val * 1.20], tickformat=",.0f"),
    )
    return fig

def donut(labels, values, title, colors=None, center_text="", h=340):
    col = colors if colors else PALETTE[:len(labels)]
    fig = go.Figure(go.Pie(
        labels=labels, values=values,
        hole=0.56,
        marker=dict(colors=col, line=dict(color="#fff", width=2)),
        textinfo="percent+label",
        textfont=dict(size=11),
        hovertemplate="<b>%{label}</b><br>%{value:,}<br>%{percent}<extra></extra>",
        sort=False,
    ))
    ann = [dict(text=center_text, x=0.5, y=0.5, font_size=13,
                showarrow=False, font_color="#1a2340")] if center_text else []
    fig.update_layout(**_lay(h=h, t=44, b=20, l=20, r=20), title=title,
        annotations=ann,
        legend=dict(orientation="h", x=0.5, xanchor="center",
                    y=-0.08, font_size=11),
    )
    return fig

def to_csv(df):
    buf = io.BytesIO(); df.to_csv(buf, index=False); return buf.getvalue()

# ─────────────────────────────────────────────────────────────────────────────
# REGION MAP
# ─────────────────────────────────────────────────────────────────────────────
_REGION = {
    'California':'West','Oregon':'West','Washington':'West','Nevada':'West',
    'Arizona':'West','Utah':'West','Colorado':'West','Montana':'West',
    'Idaho':'West','Wyoming':'West','Alaska':'West','Hawaii':'West','New Mexico':'West',
    'Texas':'South','Florida':'South','Georgia':'South','North Carolina':'South',
    'South Carolina':'South','Virginia':'South','Tennessee':'South','Alabama':'South',
    'Mississippi':'South','Arkansas':'South','Louisiana':'South','Oklahoma':'South',
    'Kentucky':'South','West Virginia':'South','Maryland':'South',
    'District Of Columbia':'South','Delaware':'South',
    'New York':'Northeast','Pennsylvania':'Northeast','New Jersey':'Northeast',
    'Massachusetts':'Northeast','Connecticut':'Northeast','Rhode Island':'Northeast',
    'New Hampshire':'Northeast','Vermont':'Northeast','Maine':'Northeast',
    'Illinois':'Midwest','Ohio':'Midwest','Michigan':'Midwest','Indiana':'Midwest',
    'Wisconsin':'Midwest','Minnesota':'Midwest','Iowa':'Midwest','Missouri':'Midwest',
    'North Dakota':'Midwest','South Dakota':'Midwest','Nebraska':'Midwest','Kansas':'Midwest',
}

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOAD & CLEAN
# ─────────────────────────────────────────────────────────────────────────────
def _clean_raw(df_raw):
    df = df_raw.copy()
    df.columns = [
        'line_item_id','order_number','country','first_name','last_name',
        'province','zip_code','city','currency','customer_id','invoice_date',
        'gateway','product_id','product_type','variant_id','quantity',
        'subtotal_price','total_price_usd','total_tax'
    ]
    df.drop_duplicates(inplace=True)
    df['invoice_date'] = pd.to_datetime(df['invoice_date'], errors='coerce')
    for c in ['quantity','subtotal_price','total_price_usd','total_tax']:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['product_id']   = df['product_id'].astype(str).fillna('UNKNOWN')
    df['variant_id']   = df['variant_id'].astype(str).fillna('UNKNOWN')
    df['customer_id']  = df['customer_id'].astype(str)
    df['order_number'] = df['order_number'].astype(str)
    df.dropna(subset=['subtotal_price','total_price_usd','total_tax','invoice_date'], inplace=True)
    df['city']         = df['city'].str.strip().str.upper()
    df['province']     = df['province'].str.strip().str.title()
    df['country']      = df['country'].str.strip().str.title()
    df['gateway']      = df['gateway'].str.strip().str.lower()
    df['product_type'] = df['product_type'].str.strip().str.title()
    df['product_type'] = df['product_type'].replace({"Boy'S":"Boy's Shoes","Boy's":"Boy's Shoes"})
    gw = {'shopify_payments':'Shopify Payments','paypal':'PayPal',
          'amazon_payments':'Amazon Pay','gift_card':'Gift Card','manual':'Manual'}
    df['gateway'] = df['gateway'].map(gw).fillna(df['gateway'])
    df = df[(df['quantity']>=1)&(df['quantity']<=20)&(df['total_price_usd']>0)].copy()
    df['order_date']  = df['invoice_date'].dt.normalize()
    df['day_of_week'] = df['invoice_date'].dt.day_name()
    df['hour']        = df['invoice_date'].dt.hour
    df['unit_price']  = (df['subtotal_price'] / df['quantity']).round(2)
    df['tax_rate']    = (df['total_tax'] / df['subtotal_price'] * 100).round(2)
    df['customer_full_name'] = df['first_name'] + ' ' + df['last_name']
    df['region'] = df['province'].map(_REGION).fillna('Other')
    return df

@st.cache_data(show_spinner="Loading Shopify data…")
def load_data():
    base  = os.path.dirname(__file__)
    tries = [
        os.path.join(base, "data","cleaned","shopify_sales_cleaned.csv"),
        os.path.join(base, "..","data","cleaned","shopify_sales_cleaned.csv"),
        os.path.join(base, "data","raw","Shopify Sales.xlsx"),
        os.path.join(base, "..","data","raw","Shopify Sales.xlsx"),
    ]
    for p in tries:
        if not os.path.exists(p):
            continue
        df = (pd.read_csv(p, parse_dates=["invoice_date"])
              if p.endswith(".csv")
              else _clean_raw(pd.read_excel(p, sheet_name="shopify_sales")))
        df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")
        df["order_date"]   = pd.to_datetime(df["order_date"],   errors="coerce")
        df["customer_id"]  = df["customer_id"].astype(str)
        if "unit_price" not in df.columns:
            df["unit_price"] = (df["subtotal_price"] / df["quantity"]).round(2)
        if "region" not in df.columns:
            df["region"] = df["province"].map(_REGION).fillna("Other")
        return df
    st.error("Data file not found. Place 'Shopify Sales.xlsx' in data/raw/ and run generate_data.py.")
    st.stop()

RAW = load_data()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR  ── navigation + global filters
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<div style='font-size:18px;font-weight:800;color:#fff;"
        "padding:12px 4px 8px 4px;letter-spacing:.5px;'>🛍️ Shopify Analytics</div>",
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    PAGE_SALES  = "📊  Sales Analysis"
    PAGE_CUST   = "👤  Customer Analysis"
    PAGE_GEO    = "🌍  Geography & Payment"

    page = st.radio("Page", [PAGE_SALES, PAGE_CUST, PAGE_GEO],
                    label_visibility="collapsed")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Date
    st.markdown("<div style='font-size:12px;font-weight:700;color:#90aad0;"
                "text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;'>"
                "Date Range</div>", unsafe_allow_html=True)
    mn = RAW["order_date"].min().date()
    mx = RAW["order_date"].max().date()
    d_from = st.date_input("From", value=mn, min_value=mn, max_value=mx, key="gd1")
    d_to   = st.date_input("To",   value=mx, min_value=mn, max_value=mx, key="gd2")
    st.markdown("<hr>", unsafe_allow_html=True)

    # Filters
    st.markdown("<div style='font-size:12px;font-weight:700;color:#90aad0;"
                "text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;'>"
                "Filters</div>", unsafe_allow_html=True)

    all_prod  = sorted(RAW["product_type"].dropna().unique())
    sel_prod  = st.multiselect("Product Type", all_prod,  default=all_prod,  key="gp")
    all_gw    = sorted(RAW["gateway"].dropna().unique())
    sel_gw    = st.multiselect("Gateway",      all_gw,    default=all_gw,    key="gg")
    all_reg   = sorted(RAW["region"].dropna().unique())
    sel_reg   = st.multiselect("Region",       all_reg,   default=all_reg,   key="gr")

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.button("🔄  Reset Filters"):
        st.rerun()
    st.markdown(
        f"<div style='font-size:11px;color:#6070a0;margin-top:8px;'>"
        f"{len(RAW):,} records · Mar 2025</div>",
        unsafe_allow_html=True,
    )

# ── apply global filters ─────────────────────────────────────────────────────
mask = (
    (RAW["order_date"].dt.date >= d_from) &
    (RAW["order_date"].dt.date <= d_to)   &
    RAW["product_type"].isin(sel_prod)    &
    RAW["gateway"].isin(sel_gw)           &
    RAW["region"].isin(sel_reg)
)
DF = RAW[mask].copy()

if DF.empty:
    st.warning("No data for the current filters — please adjust the sidebar.")
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 1  ─  SALES ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
if page == PAGE_SALES:

    st.markdown("""<div class="page-banner">
        <h2>📊 Shopify Sales Analysis</h2>
        <p>Revenue trends · Product performance · Timing · Payment channel breakdown</p>
    </div>""", unsafe_allow_html=True)

    # ── page-level filters ────────────────────────────────────────────────────
    with st.expander("🔍  Page Filters", expanded=False):
        fx1, fx2 = st.columns(2)
        with fx1:
            DOW = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            sel_dow = st.multiselect("Day of Week", DOW, default=DOW, key="p1dow")
        with fx2:
            h0, h1 = int(DF["hour"].min()), int(DF["hour"].max())
            sel_hr  = st.slider("Hour range", h0, h1, (h0, h1), key="p1hr")
    D = DF[DF["day_of_week"].isin(sel_dow) & DF["hour"].between(sel_hr[0], sel_hr[1])]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    t_rev = D["total_price_usd"].sum()
    t_ord = D["order_number"].nunique()
    t_qty = D["quantity"].sum()
    t_aov = t_rev / t_ord if t_ord else 0
    kpis([
        ("Total Revenue",        fc(t_rev),  f"{t_ord:,} orders"),
        ("Total Orders",         fn(t_ord),  f"{d_from} → {d_to}"),
        ("Total Qty Sold",        fn(t_qty),  f"avg {t_qty/max(t_ord,1):.1f} / order"),
        ("Avg Order Value",      fc(t_aov),  "revenue ÷ orders"),
    ])

    # ── Revenue by Date ───────────────────────────────────────────────────────
    sec("Revenue by Date")
    daily = D.groupby("order_date")["total_price_usd"].sum().reset_index()
    daily.columns = ["Date","Revenue"]
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=daily["Date"], y=daily["Revenue"],
        mode="lines+markers+text",
        line=dict(color=C_BLUE, width=3),
        marker=dict(size=9, color=C_BLUE, line=dict(color="#fff", width=2)),
        text=[fc(v) for v in daily["Revenue"]],
        textposition="top center",
        textfont=dict(size=11, color=C_BLUE),
        fill="tozeroy", fillcolor="rgba(74,144,217,0.07)",
        hovertemplate="<b>%{x|%A %b %d}</b><br>Revenue: $%{y:,.0f}<extra></extra>",
    ))
    fig_line.update_layout(**_lay(h=300, t=44, b=44, l=70, r=20),
        xaxis=dict(title="", showgrid=False, tickformat="%b %d",
                   tickfont=dict(size=12)),
        yaxis=dict(title="Revenue (USD)", gridcolor="#eef1f8",
                   tickformat="$,.0f", range=[0, daily["Revenue"].max()*1.25]),
    )
    show(fig_line, 300)

    # ── Product Performance  (2 charts side by side) ─────────────────────────
    sec("Product Performance")
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        rev_pt = (D.groupby("product_type")["total_price_usd"]
                   .sum().sort_values(ascending=True).reset_index())
        fig = hbar(rev_pt, "total_price_usd", "product_type",
                   "Revenue by Product Type", color=C_BLUE, h=420, text_fmt=fc)
        show(fig, 420)

    with col2:
        top10 = (D.groupby("product_type")["total_price_usd"]
                  .sum().nlargest(10).sort_values(ascending=False).reset_index())
        cols10 = PALETTE[:len(top10)]
        fig = vbar(top10, "product_type", "total_price_usd",
                   "Top 10 Products by Revenue",
                   colors=cols10, h=420,
                   text_fmt=fc, xangle=-30)
        show(fig, 420)

    # ── Sales Timing  (2 charts side by side) ────────────────────────────────
    sec("Sales Timing")
    col3, col4 = st.columns(2, gap="medium")

    with col3:
        DOW_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
        rev_dow = (D.groupby("day_of_week")["total_price_usd"]
                    .sum().reindex(DOW_ORDER, fill_value=0).reset_index())
        rev_dow.columns = ["Day","Revenue"]
        peak_d = rev_dow.loc[rev_dow["Revenue"].idxmax(), "Day"]
        dow_colors = [C_AMBER if d == peak_d else C_BLUE for d in rev_dow["Day"]]
        fig_dow = vbar(rev_dow, "Day", "Revenue",
                       "Revenue by Day Name",
                       colors=dow_colors, h=340, text_fmt=fc)
        show(fig_dow, 340)

    with col4:
        rev_hr = (D.groupby("hour")["total_price_usd"]
                   .sum().reset_index()
                   .rename(columns={"hour":"Hour","total_price_usd":"Revenue"}))
        peak_h = rev_hr.loc[rev_hr["Revenue"].idxmax(), "Hour"]
        hr_colors = [C_PINK if h == peak_h else C_TEAL for h in rev_hr["Hour"]]
        fig_hr = vbar(rev_hr, "Hour", "Revenue",
                      "Revenue by Order Hour",
                      colors=hr_colors, h=340, text_fmt=fc)
        fig_hr.update_layout(xaxis=dict(title="Hour (24h)", dtick=2))
        show(fig_hr, 340)

    # ── Gateway & Quantity  (2 charts side by side) ───────────────────────────
    sec("Gateway & Quantity Breakdown")
    col5, col6 = st.columns(2, gap="medium")

    with col5:
        gate = (D.groupby("gateway")["total_price_usd"]
                 .sum().reset_index()
                 .sort_values("total_price_usd", ascending=False))
        total_lbl = fc(gate["total_price_usd"].sum())
        fig_d = donut(gate["gateway"].tolist(),
                      gate["total_price_usd"].tolist(),
                      "Revenue by Gateway",
                      colors=PALETTE[:len(gate)],
                      center_text=total_lbl, h=360)
        show(fig_d, 360)

    with col6:
        qty_pt = (D.groupby("product_type")["quantity"]
                   .sum().sort_values(ascending=True).reset_index())
        fig = hbar(qty_pt, "quantity", "product_type",
                   "Quantity Sold by Product Type",
                   color=C_TEAL, h=360, text_fmt=fn)
        show(fig, 360)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("⬇️  Download Sales Data (CSV)",
                       data=to_csv(D),
                       file_name="sales_analysis.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 2  ─  CUSTOMER ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
elif page == PAGE_CUST:

    st.markdown("""<div class="page-banner">
        <h2>👤 Customer Analysis</h2>
        <p>Segmentation · Repeat-purchase behaviour · RFM scoring · Top customers</p>
    </div>""", unsafe_allow_html=True)

    # ── page filters ──────────────────────────────────────────────────────────
    with st.expander("🔍  Page Filters", expanded=False):
        fx1, fx2 = st.columns(2)
        with fx1:
            sel_p2 = st.multiselect("Product Type",
                                    sorted(DF["product_type"].unique()),
                                    default=sorted(DF["product_type"].unique()),
                                    key="p2prod")
        with fx2:
            min_ord = st.number_input("Min orders per customer", 1, 20, 1, key="p2min")
    D2 = DF[DF["product_type"].isin(sel_p2)]

    # ── customer aggregates ───────────────────────────────────────────────────
    cdf = (D2.groupby("customer_id").agg(
        total_rev   = ("total_price_usd","sum"),
        order_count = ("order_number","nunique"),
        first_order = ("order_date","min"),
        last_order  = ("order_date","max"),
        full_name   = ("customer_full_name","first"),
    ).reset_index())

    ref = D2["order_date"].max()
    cdf["recency_days"] = (ref - cdf["last_order"]).dt.days

    # RFM quintile scoring
    for col, asc, lbl in [
        ("recency_days", True, "R"),("order_count", False, "F"),("total_rev", False, "M")
    ]:
        try:
            cdf[lbl] = pd.qcut(cdf[col], 5,
                                labels=[5,4,3,2,1] if asc else [1,2,3,4,5],
                                duplicates="drop").astype(float)
        except Exception:
            cdf[lbl] = 3.0
    cdf["rfm_score"] = cdf[["R","F","M"]].sum(axis=1)

    def seg(s):
        if s >= 12: return "Champions"
        if s >= 9:  return "Loyal"
        if s >= 7:  return "Potential"
        if s >= 5:  return "At Risk"
        return "Lost"
    cdf["segment"]       = cdf["rfm_score"].apply(seg)
    cdf["customer_type"] = np.where(cdf["order_count"] > 1, "Returning", "New")

    # ── KPIs ──────────────────────────────────────────────────────────────────
    n_cust  = len(cdf)
    n_new   = (cdf["customer_type"] == "New").sum()
    n_ret   = (cdf["customer_type"] == "Returning").sum()
    rep_rt  = n_ret / n_cust * 100 if n_cust else 0
    top10n  = max(1, int(n_cust * 0.10))
    top10rv = cdf.nlargest(top10n, "total_rev")["total_rev"].sum()
    top10sh = top10rv / cdf["total_rev"].sum() * 100 if cdf["total_rev"].sum() else 0

    kpis([
        ("Top 10% Revenue Share", f"{top10sh:.1f}%",  f"top {top10n} customers"),
        ("Repeat Purchase Rate",  f"{rep_rt:.1f}%",   f"{n_ret:,} repeat buyers"),
        ("New Customers",         fn(n_new),           "1 order only"),
        ("Returning Customers",   fn(n_ret),           "2+ orders"),
        ("Unique Customers",      fn(n_cust),          f"{d_from} → {d_to}"),
    ])

    # ── Row 1: Frequency + New vs Returning ───────────────────────────────────
    sec("Purchase Behaviour")
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        freq = (cdf[cdf["order_count"] >= min_ord]["order_count"]
                .value_counts().sort_index().reset_index())
        freq.columns = ["Orders","Customers"]
        fig = vbar(freq, "Orders", "Customers",
                   "Customer Order Frequency",
                   colors=C_BLUE, h=340, text_fmt=fn)
        show(fig, 340)

    with col2:
        nr = cdf["customer_type"].value_counts().reset_index()
        nr.columns = ["Type","Count"]
        fig = donut(nr["Type"].tolist(), nr["Count"].tolist(),
                    "New vs Returning Customers",
                    colors=[C_BLUE, C_AMBER],
                    center_text=fn(n_cust), h=340)
        show(fig, 340)

    # ── Row 2: RFM donut + Top 10 customers ───────────────────────────────────
    sec("RFM Segmentation & Top Customers")
    col3, col4 = st.columns(2, gap="medium")

    with col3:
        SEG_ORDER  = ["Champions","Loyal","Potential","At Risk","Lost"]
        SEG_COLORS = [C_GREEN, C_BLUE, C_TEAL, C_AMBER, C_PINK]
        sc = (cdf["segment"].value_counts()
              .reindex(SEG_ORDER, fill_value=0).reset_index())
        sc.columns = ["Segment","Count"]
        fig = donut(sc["Segment"].tolist(), sc["Count"].tolist(),
                    "RFM Customer Segments",
                    colors=SEG_COLORS,
                    center_text=f"{n_cust:,}<br>customers", h=380)
        show(fig, 380)

    with col4:
        top10c = (cdf.nlargest(10,"total_rev")
                     .sort_values("total_rev", ascending=True))
        fig = hbar(top10c, "total_rev", "full_name",
                   "Top 10 Customers by Revenue",
                   color=C_PURPLE, h=380, text_fmt=fc)
        show(fig, 380)

    # ── Row 3: Purchase gap ────────────────────────────────────────────────────
    sec("First-to-Second Purchase Gap")
    multi = cdf[cdf["order_count"] >= 2]
    if len(multi) >= 2:
        ord_d = (D2.groupby(["customer_id","order_number"])["order_date"]
                   .min().reset_index()
                   .sort_values(["customer_id","order_date"]))
        # first→second gap per customer (pandas 3-compatible)
        def _gap(g):
            dates = g["order_date"].values
            return (pd.Timestamp(dates[1]) - pd.Timestamp(dates[0])).days if len(dates) >= 2 else np.nan
        gaps = (ord_d.groupby("customer_id")[["order_date"]]
                .apply(_gap).dropna().reset_index())
        gaps.columns = ["customer_id","gap_days"]
        bins   = [0,1,2,3,4,5,6,7]
        lbls   = ["Day 0","Day 1","Day 2","Day 3","Day 4","Day 5","Day 6"]
        gaps["bucket"] = pd.cut(gaps["gap_days"], bins=bins, labels=lbls, right=False)
        gd = (gaps["bucket"].value_counts()
              .reindex(lbls, fill_value=0).reset_index())
        gd.columns = ["Gap","Count"]
        fig = vbar(gd, "Gap", "Count",
                   "Days Between 1st & 2nd Purchase",
                   colors=C_TEAL, h=300, text_fmt=fn)
        show(fig, 300)
    else:
        st.info("Not enough repeat-purchase data with current filters.")

    # ── Segment summary table ─────────────────────────────────────────────────
    sec("Customer Segment Summary")
    tbl = (cdf.groupby("segment").agg(
        Customers=("customer_id","count"),
        Total_Revenue=("total_rev","sum"),
        Avg_Orders=("order_count","mean"),
        Avg_Revenue=("total_rev","mean"),
    ).round(2).reset_index().sort_values("Total_Revenue", ascending=False))
    tbl["Total_Revenue"] = tbl["Total_Revenue"].apply(lambda x: f"${x:,.0f}")
    tbl["Avg_Revenue"]   = tbl["Avg_Revenue"].apply(lambda x: f"${x:,.0f}")
    tbl["Avg_Orders"]    = tbl["Avg_Orders"].apply(lambda x: f"{x:.1f}")
    tbl.columns          = ["Segment","Customers","Total Revenue","Avg Orders","Avg Revenue"]
    st.dataframe(tbl, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("⬇️  Download Customer Data (CSV)",
                       data=to_csv(cdf),
                       file_name="customer_analysis.csv", mime="text/csv")


# ══════════════════════════════════════════════════════════════════════════════
#  PAGE 3  ─  GEOGRAPHY & PAYMENT
# ══════════════════════════════════════════════════════════════════════════════
elif page == PAGE_GEO:

    st.markdown("""<div class="page-banner">
        <h2>🌍 Geography &amp; Payment Analysis</h2>
        <p>State &amp; city revenue · Payment gateway performance · Revenue heatmap by state × product</p>
    </div>""", unsafe_allow_html=True)

    # ── page filters ──────────────────────────────────────────────────────────
    with st.expander("🔍  Page Filters", expanded=False):
        fx1, fx2, fx3 = st.columns(3)
        with fx1:
            sel_st  = st.multiselect("State",
                                     sorted(DF["province"].dropna().unique()),
                                     default=sorted(DF["province"].dropna().unique()),
                                     key="p3st")
        with fx2:
            sel_g3  = st.multiselect("Gateway",
                                     sorted(DF["gateway"].dropna().unique()),
                                     default=sorted(DF["gateway"].dropna().unique()),
                                     key="p3gw")
        with fx3:
            top_n = st.slider("Top N Cities", 5, 25, 15, key="p3n")
    D3 = DF[DF["province"].isin(sel_st) & DF["gateway"].isin(sel_g3)]

    # ── KPIs ──────────────────────────────────────────────────────────────────
    g_rev  = D3["total_price_usd"].sum()
    g_ord  = D3["order_number"].nunique()
    g_cust = D3["customer_id"].nunique()
    g_rpc  = g_rev / g_cust if g_cust else 0
    g_aov  = g_rev / g_ord  if g_ord  else 0
    kpis([
        ("Total Revenue",        fc(g_rev),  f"{g_ord:,} orders"),
        ("Total Orders",         fn(g_ord),  f"{D3['province'].nunique()} states"),
        ("Unique Customers",     fn(g_cust), f"{D3['city'].nunique()} cities"),
        ("Revenue per Customer", fc(g_rpc),  "rev ÷ customers"),
        ("Avg Order Value",      fc(g_aov),  "rev ÷ orders"),
    ])

    # ── US Map ────────────────────────────────────────────────────────────────
    sec("Total Orders by State")
    sm = (D3.groupby("province").agg(
        Orders   = ("order_number","nunique"),
        Revenue  = ("total_price_usd","sum"),
        Customers= ("customer_id","nunique"),
    ).reset_index())
    sm["code"] = sm["province"].map(STATE_ABBREV)
    smc = sm.dropna(subset=["code"])

    fig_map = go.Figure(go.Choropleth(
        locations   = smc["code"],
        z           = smc["Orders"],
        locationmode= "USA-states",
        colorscale  = [[0,"#cce4f6"],[0.4,"#4a90d9"],[1,"#0d2e6b"]],
        zmin=0,
        colorbar=dict(title="Orders", thickness=16, len=0.75,
                      tickfont=dict(size=11)),
        customdata  = smc[["Revenue","Customers","province"]].values,
        hovertemplate=(
            "<b>%{customdata[2]}</b><br>"
            "Orders: %{z:,}<br>"
            "Revenue: $%{customdata[0]:,.0f}<br>"
            "Customers: %{customdata[1]:,}<extra></extra>"
        ),
    ))
    fig_map.update_layout(
        **_BASE, height=420,
        geo=dict(scope="usa", bgcolor="#f0f2f6",
                 lakecolor="#d6e8f7", showlakes=True,
                 landcolor="#edf0f5",
                 subunitcolor="#c0cce0", showsubunits=True),
        margin=dict(t=10, b=10, l=10, r=10),
    )
    show(fig_map, 420)

    # ── Gateway + Top Cities ──────────────────────────────────────────────────
    sec("Gateway Revenue & Top Cities")
    col1, col2 = st.columns([2, 3], gap="medium")

    with col1:
        gw_agg = (D3.groupby("gateway")["total_price_usd"]
                    .sum().sort_values(ascending=True).reset_index())
        # use distinct colours per gateway
        gw_colors = PALETTE[:len(gw_agg)]
        fig = hbar(gw_agg, "total_price_usd", "gateway",
                   "Gateway Revenue", color=C_BLUE, h=360, text_fmt=fc)
        # override bar colours to be per-bar
        fig.data[0].marker.color = gw_colors[::-1]   # reversed because hbar sorts asc
        show(fig, 360)

    with col2:
        city_agg = (D3.groupby("city")["total_price_usd"]
                      .sum().nlargest(top_n)
                      .sort_values(ascending=True).reset_index())
        fig = hbar(city_agg, "total_price_usd", "city",
                   f"Top {top_n} Cities by Revenue",
                   color=C_TEAL, h=max(360, top_n * 26), text_fmt=fc)
        show(fig, max(360, top_n * 26))

    # ── State × Product Heatmap ───────────────────────────────────────────────
    sec("Revenue Heatmap — State × Product Type")
    top_states = (D3.groupby("province")["total_price_usd"]
                    .sum().nlargest(15).index.tolist())
    top_prods  = (D3.groupby("product_type")["total_price_usd"]
                    .sum().nlargest(10).index.tolist())
    hm = (D3[D3["province"].isin(top_states) & D3["product_type"].isin(top_prods)]
            .groupby(["province","product_type"])["total_price_usd"]
            .sum().reset_index()
            .pivot(index="province", columns="product_type", values="total_price_usd")
            .fillna(0))
    hm = hm.loc[hm.sum(axis=1).sort_values(ascending=False).index]

    fig_hm = go.Figure(go.Heatmap(
        z          = hm.values,
        x          = hm.columns.tolist(),
        y          = hm.index.tolist(),
        colorscale = "Blues",
        text       = [[f"${v/1000:.0f}K" if v >= 1000 else (f"${v:.0f}" if v > 0 else "")
                        for v in row] for row in hm.values],
        texttemplate = "%{text}",
        textfont   = dict(size=10, color="#1a2340"),
        hovertemplate = "<b>%{y}</b><br><b>%{x}</b><br>$%{z:,.0f}<extra></extra>",
        colorbar   = dict(title="Revenue ($)", thickness=16, len=0.8,
                          tickformat="$,.0f", tickfont=dict(size=10)),
        xgap=2, ygap=2,
    ))
    fig_hm.update_layout(
        **_BASE, height=520,
        xaxis=dict(title="", tickangle=-35, tickfont=dict(size=11), side="bottom"),
        yaxis=dict(title="", autorange="reversed", tickfont=dict(size=11)),
        margin=dict(t=20, b=100, l=130, r=80),
    )
    show(fig_hm, 520)

    # ── State summary table ────────────────────────────────────────────────────
    sec("State Performance Summary")
    st_tbl = (D3.groupby("province").agg(
        Region        = ("region","first"),
        Revenue       = ("total_price_usd","sum"),
        Orders        = ("order_number","nunique"),
        Customers     = ("customer_id","nunique"),
        Units         = ("quantity","sum"),
        Avg_Order     = ("total_price_usd","mean"),
    ).round(2).sort_values("Revenue", ascending=False).reset_index())
    st_tbl.columns = ["State","Region","Revenue ($)","Orders","Customers",
                       "Units Sold","Avg Order ($)"]
    st_tbl["Revenue ($)"]  = st_tbl["Revenue ($)"].apply(lambda x: f"${x:,.0f}")
    st_tbl["Avg Order ($)"]= st_tbl["Avg Order ($)"].apply(lambda x: f"${x:,.0f}")
    st.dataframe(st_tbl, use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("⬇️  Download Geography Data (CSV)",
                       data=to_csv(D3),
                       file_name="geography_payment.csv", mime="text/csv")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='text-align:center;color:#9aa3bc;font-size:11px;"
    "border-top:1px solid #dde1eb;padding:16px 0 6px;margin-top:28px;'>"
    "Shopify Sales Analytics &nbsp;·&nbsp; Streamlit + Plotly + Pandas"
    " &nbsp;·&nbsp; Data: March 2025"
    "</div>",
    unsafe_allow_html=True,
)
