import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

STATE_PATH = Path("radar_state.json")

st.set_page_config(
    page_title="A+ Live Radar",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
:root {
  --bg: #05080C;
  --panel: #091119;
  --line: #23303A;
  --green: #78FF2E;
  --yellow: #FFD93D;
  --red: #FF4D4D;
  --blue: #35A7FF;
  --purple: #BF65FF;
  --muted: #9AA6B2;
}
.stApp { background: radial-gradient(circle at top left, #0D1720 0%, #05080C 42%, #030507 100%); color: white; }
.block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px; }
[data-testid="stMetricValue"] { color: var(--green); }
.radar-header {
  border: 1px solid var(--line); border-radius: 18px; padding: 22px 26px;
  background: linear-gradient(135deg, rgba(9,17,25,.96), rgba(3,6,9,.96));
  box-shadow: 0 0 30px rgba(120,255,46,.08);
}
.title { font-size: 48px; line-height: 1; font-weight: 900; letter-spacing: -1px; }
.sub { color: var(--green); font-weight: 800; letter-spacing: .7px; margin-top: 6px; }
.state-box { border: 1px solid var(--line); border-radius: 16px; padding: 18px; background: #05080C; text-align: center; }
.state-label { font-size: 14px; color: white; font-weight: 800; }
.state-value { font-size: 42px; font-weight: 900; margin-top: 5px; }
.card {
  border: 1px solid var(--line); border-radius: 18px; padding: 18px;
  background: rgba(9,17,25,.92); box-shadow: 0 0 20px rgba(0,0,0,.25);
  min-height: 520px;
}
.rank { font-size: 26px; font-weight: 900; border: 2px solid var(--green); border-radius: 12px; padding: 4px 13px; display:inline-block; margin-right: 10px; }
.coin { font-size: 38px; font-weight: 900; letter-spacing: 1px; }
.tag { font-size: 14px; font-weight: 900; border-radius: 8px; padding: 5px 10px; display:inline-block; margin-top: 7px; }
.tag-pre { color: var(--yellow); border: 1px solid var(--yellow); }
.tag-bull { color: var(--green); border: 1px solid var(--green); }
.tag-sharp { color: var(--red); border: 1px solid var(--red); }
.caption { color: #D7DEE6; font-size: 15px; margin-top: 10px; min-height: 42px; }
.readbox { margin-top: 10px; border: 1px solid #1C2832; border-radius: 12px; padding: 10px; background: #071017; }
.readline { color: white; font-size: 14px; margin: 2px 0; }
.timing { font-weight: 900; font-size: 18px; }
.footer-note { color: var(--muted); font-size: 13px; }
.small-panel { border: 1px solid var(--line); border-radius: 16px; padding: 16px; background: rgba(9,17,25,.88); }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def sample_state():
    now = datetime.now().isoformat(timespec="seconds")
    return {
        "generated_at": now,
        "cycle_number": 0,
        "active_pairs": 0,
        "market_state": "WAITING",
        "regime_name": "WAITING",
        "btc": {"reason": "Start the scanner to populate radar_state.json", "rsi_15m": 0, "rsi_60m": 0, "above_vwap_15m": False, "above_vwap_60m": False},
        "sector_counts": {},
        "state_counts": {},
        "top_setups": [],
    }


def load_state(path: Path):
    if not path.exists():
        return sample_state(), False, f"Waiting for {path.name}. Start the scanner first."
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f), True, "OK"
    except Exception as e:
        return sample_state(), False, f"Could not read {path.name}: {e}"


def state_color(state: str):
    if state == "BULL":
        return "#78FF2E"
    if state in {"PREBULL", "WATCH", "WAITING"}:
        return "#FFD93D"
    return "#FF4D4D"


def tag_class(tag: str):
    tag = (tag or "").upper()
    if tag == "BULL":
        return "tag tag-bull"
    if tag == "SHARPSHOOTER":
        return "tag tag-sharp"
    return "tag tag-pre"


def timing_color(timing: str):
    t = (timing or "").upper()
    if t == "ON TIME":
        return "#78FF2E"
    if t in {"EARLY", "WATCH", "WAIT"}:
        return "#FFD93D"
    return "#FF4D4D"


def line_chart(values, title, accent="#78FF2E"):
    vals = [float(v) for v in (values or []) if v is not None]
    fig = go.Figure()
    if len(vals) >= 2:
        fig.add_trace(go.Scatter(y=vals, mode="lines", line=dict(width=3, color=accent), fill="tozeroy", fillcolor="rgba(120,255,46,0.05)"))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=accent)),
        height=170,
        margin=dict(l=8, r=8, t=34, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#071017",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


def setup_card(setup, accent="#78FF2E"):
    rank = setup.get("rank", "-")
    coin = setup.get("coin") or setup.get("pair", "NO SETUP")
    tag = setup.get("tag", "WATCH")
    cr = setup.get("chart_read", {}) or {}
    timing = cr.get("timing", "WATCH")
    caption = setup.get("caption", "")
    tscore = setup.get("trigger_score", 0)
    trscore = setup.get("trade_score", 0)
    cscore = setup.get("confidence", 0)

    st.markdown(f"""
    <div class="card" style="border-color:{accent};">
      <div><span class="rank" style="border-color:{accent};">{rank}</span><span class="coin">{coin}</span></div>
      <div class="{tag_class(tag)}">{tag}</div>
      <div class="caption">{caption}</div>
      <div style="display:flex; gap:14px; margin-top:12px;">
        <div><div style="color:#9AA6B2;font-size:12px;">TRIGGER</div><div style="font-size:34px;font-weight:900;color:#78FF2E;">{tscore}</div></div>
        <div><div style="color:#9AA6B2;font-size:12px;">TRADE</div><div style="font-size:34px;font-weight:900;color:#BF65FF;">{trscore}</div></div>
        <div><div style="color:#9AA6B2;font-size:12px;">CONF</div><div style="font-size:34px;font-weight:900;color:#35A7FF;">{cscore}</div></div>
      </div>
      <div class="readbox">
        <div class="readline"><b>30M:</b> {cr.get('read_30m', 'No read')}</div>
        <div class="readline"><b>1H:</b> {cr.get('read_1h', 'No read')}</div>
        <div class="timing" style="color:{timing_color(timing)};">Timing: {timing}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(line_chart(setup.get("close_30m", []), "30M MOVEMENT", accent), use_container_width=True, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(line_chart(setup.get("close_1h", []), "1H MOVEMENT", accent), use_container_width=True, config={"displayModeBar": False})


state, ok, msg = load_state(STATE_PATH)
market = state.get("market_state", "WAITING")
color = state_color(market)

# Auto-refresh using browser refresh. Keeps dependencies minimal.
refresh_seconds = st.sidebar.slider("Refresh seconds", 5, 120, 15)
st.sidebar.caption("Keep the scanner running in another PowerShell window.")
st.components.v1.html(f"<script>setTimeout(function(){{window.parent.location.reload();}}, {refresh_seconds * 1000});</script>", height=0)

h1, h2 = st.columns([2.2, 1])
with h1:
    st.markdown(f"""
    <div class="radar-header">
      <div class="title"><span style="color:#78FF2E;">A+</span> LIVE RADAR APP</div>
      <div class="sub">VISUAL MARKET COMMAND CENTER</div>
      <div style="margin-top:16px;color:#D7DEE6;">Last update: <b>{state.get('generated_at','')}</b> &nbsp; | &nbsp; Cycle: <b>{state.get('cycle_number',0)}</b> &nbsp; | &nbsp; Active pairs: <b style="color:#78FF2E;">{state.get('active_pairs',0)}</b></div>
    </div>
    """, unsafe_allow_html=True)
with h2:
    st.markdown(f"""
    <div class="state-box">
      <div class="state-label">MARKET STATE</div>
      <div class="state-value" style="color:{color};">{market}</div>
      <div style="color:#D7DEE6;">{state.get('btc',{}).get('reason','')}</div>
    </div>
    """, unsafe_allow_html=True)

if not ok:
    st.warning(msg)

m1, m2, m3, m4 = st.columns(4)
btc = state.get("btc", {}) or {}
with m1:
    st.metric("BTC 15M RSI", btc.get("rsi_15m", 0))
with m2:
    st.metric("BTC 1H RSI", btc.get("rsi_60m", 0))
with m3:
    st.metric("Above 15M VWAP", "YES" if btc.get("above_vwap_15m") else "NO")
with m4:
    st.metric("Above 1H VWAP", "YES" if btc.get("above_vwap_60m") else "NO")

st.markdown("### 🎯 Top Radar Setups")
setups = state.get("top_setups", []) or []
accents = ["#78FF2E", "#FF8A3D", "#35A7FF"]
if not setups:
    st.info("No live setups yet. Start the scanner and wait for the next cycle.")
else:
    cols = st.columns(3)
    for i, col in enumerate(cols):
        with col:
            if i < len(setups):
                setup_card(setups[i], accents[i])
            else:
                st.markdown('<div class="card"><div class="coin">NO SETUP</div><div class="caption">Cash is a position.</div></div>', unsafe_allow_html=True)

st.markdown("### 🌊 Market Flow")
f1, f2 = st.columns([1, 1])
with f1:
    st.markdown('<div class="small-panel"><b>Sector Flow</b></div>', unsafe_allow_html=True)
    sectors = state.get("sector_counts", {}) or {}
    if sectors:
        df = pd.DataFrame([{"Sector": k, "Count": v} for k, v in sorted(sectors.items(), key=lambda x: x[1], reverse=True)])
        st.bar_chart(df.set_index("Sector"))
    else:
        st.caption("No sector flow yet.")
with f2:
    st.markdown('<div class="small-panel"><b>Scanner State Counts</b></div>', unsafe_allow_html=True)
    counts = state.get("state_counts", {}) or {}
    if counts:
        df2 = pd.DataFrame([{"State": k, "Count": v} for k, v in counts.items()])
        st.bar_chart(df2.set_index("State"))
    else:
        st.caption("No state counts yet.")

st.markdown("---")
st.markdown('<div class="footer-note">Not financial advice. This app reads your local radar_state.json generated by the scanner. Keep the scanner running for live updates.</div>', unsafe_allow_html=True)
