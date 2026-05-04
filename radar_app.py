import base64
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
import plotly.graph_objects as go

STATE_PATH = Path("radar_state.json")
DEFAULT_GITHUB_RADAR_REPO = "Trans3/a-plus-live-radar"
DEFAULT_GITHUB_RADAR_BRANCH = "main"
DEFAULT_GITHUB_RADAR_PATH = "radar_state.json"

st.set_page_config(
    page_title="A+ Scanner Report",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
:root{
  --bg:#05080C; --panel:#091119; --panel2:#071017; --line:#22303A;
  --green:#78FF2E; --yellow:#FFD93D; --red:#FF4D4D; --orange:#FF8A3D;
  --blue:#35A7FF; --purple:#BF65FF; --white:#F5F7FA; --muted:#9AA6B2;
}
.stApp{background:radial-gradient(circle at top left,#0f1a20 0%,#05080C 36%,#020407 100%);color:var(--white);} 
.block-container{max-width:1180px;padding-top:.8rem;padding-bottom:1.5rem;}
[data-testid="stSidebar"]{background:#14171f;}
#MainMenu, footer, header{visibility:hidden;}
.report-shell{border:1px solid var(--line);border-radius:18px;background:rgba(3,6,9,.92);padding:18px 20px;box-shadow:0 0 36px rgba(120,255,46,.08);} 
.header{display:grid;grid-template-columns:1.7fr .65fr;gap:18px;align-items:stretch;margin-bottom:14px;}
.header-left{border:1px solid var(--line);border-radius:14px;background:linear-gradient(135deg,#04090d,#08121a);padding:20px 24px;}
.brand{display:flex;gap:18px;align-items:center;}
.logo{width:84px;height:84px;border:2px solid var(--green);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--green);font-size:40px;font-weight:1000;box-shadow:0 0 18px rgba(120,255,46,.25);} 
.title{font-size:52px;font-weight:1000;line-height:.95;letter-spacing:-1.5px;color:white;text-transform:uppercase;}
.title span{color:var(--green);} .subtitle{margin-top:8px;color:var(--green);font-weight:900;letter-spacing:1px;text-transform:uppercase;}
.meta{display:flex;gap:24px;margin-top:18px;color:var(--white);font-weight:700;font-size:14px;flex-wrap:wrap;} .meta b{color:var(--green);}
.state-box{border:1px solid var(--line);border-radius:14px;background:#05080C;padding:18px;text-align:center;}
.state-label{font-size:14px;font-weight:900;color:white;text-transform:uppercase;letter-spacing:.8px;}
.state-value{font-size:44px;font-weight:1000;margin:10px 0 6px;text-transform:uppercase;}
.state-sub{font-size:15px;font-weight:900;text-transform:uppercase;}.state-reason{font-size:13px;color:white;margin-top:6px;line-height:1.35;}
.section-title{display:flex;align-items:center;gap:18px;justify-content:center;margin:15px 0 12px;}.section-title:before,.section-title:after{content:"";height:3px;background:var(--green);flex:1;box-shadow:0 0 8px rgba(120,255,46,.5);} .section-title span{font-size:28px;font-weight:1000;text-transform:uppercase;letter-spacing:1px;}
.setup-row{display:grid;grid-template-columns:90px 270px 230px 1fr;gap:18px;align-items:center;border:1px solid var(--line);border-radius:14px;background:rgba(9,17,25,.96);padding:18px;margin-bottom:12px;min-height:188px;} 
.rank-badge{height:148px;border:3px solid var(--green);border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:54px;font-weight:1000;color:white;background:#05080C;}
.coin-title{font-size:46px;font-weight:1000;letter-spacing:1px;line-height:1;color:white;}.pair-small{color:var(--muted);font-size:13px;font-weight:700;margin-top:4px;}
.tag{display:inline-block;border-radius:6px;padding:5px 12px;margin-top:9px;font-size:18px;font-weight:1000;text-transform:uppercase;background:#080A0E;}.tag-pre{border:2px solid var(--yellow);color:var(--yellow);}.tag-bull{border:2px solid var(--green);color:var(--green);}.tag-sharp{border:2px solid var(--red);color:var(--red);}.tag-watch{border:2px solid var(--blue);color:var(--blue);} 
.bullets{margin-top:10px;color:white;font-size:15px;font-weight:700;line-height:1.55;}.bullets div:before{content:"›";color:var(--green);font-weight:1000;margin-right:8px;}.accent-orange .bullets div:before{color:var(--orange);} .accent-blue .bullets div:before{color:var(--blue);} 
.scores{border-left:1px solid var(--line);border-right:1px solid var(--line);padding:0 20px;}.score-line{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding:8px 0;}.score-line:last-child{border-bottom:0}.score-label{font-size:13px;font-weight:900;color:white;text-transform:uppercase;line-height:1.05;}.score-num{font-size:42px;font-weight:1000;line-height:1;}.score-trigger{color:var(--green)}.score-trade{color:var(--purple)}.score-conf{color:var(--blue)}
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px;}.chart-card{border:1px solid var(--line);border-radius:10px;background:#071017;padding:8px;}.chart-caption{text-align:center;font-size:14px;font-weight:1000;margin-top:4px;text-transform:uppercase;}.timing-pill{margin-top:8px;border-radius:8px;border:2px solid;padding:6px 8px;text-align:center;font-weight:1000;text-transform:uppercase;font-size:15px;background:#05080C;}
.bottom-grid{display:grid;grid-template-columns:1.1fr 1fr 1.25fr;gap:14px;margin-top:14px;}.bottom-panel{border:1px solid var(--line);border-radius:14px;background:rgba(9,17,25,.92);padding:16px;min-height:178px;}.panel-title{color:var(--green);font-size:18px;font-weight:1000;text-transform:uppercase;text-align:center;margin-bottom:12px;}.btc-big{font-size:32px;font-weight:1000;text-transform:uppercase;}.metric-row{display:flex;justify-content:space-between;border-top:1px solid #17232D;padding:8px 0;color:white;font-size:14px;}.sector-row{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #17232D;padding:6px 0;font-size:17px;font-weight:900;}.read-row{display:grid;grid-template-columns:130px 1fr;gap:8px;border-bottom:1px solid #17232D;padding:9px 0;}.read-key{font-weight:1000;text-transform:uppercase;}.read-desc{color:white;}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:16px;border-top:1px solid var(--line);padding-top:14px;color:white;font-weight:800;}.footer .left{color:var(--green);font-size:18px}.small{font-size:13px;color:var(--muted);font-weight:500;}
.notice{border:1px solid #3b3f14;background:rgba(255,217,61,.18);border-radius:10px;padding:10px 14px;color:#fff3a3;margin:10px 0 14px;font-weight:700;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def secret_or_env(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, os.getenv(name, default))).strip()
    except Exception:
        return str(os.getenv(name, default)).strip()


def settings():
    return {
        "repo": secret_or_env("GITHUB_RADAR_REPO", DEFAULT_GITHUB_RADAR_REPO),
        "branch": secret_or_env("GITHUB_RADAR_BRANCH", DEFAULT_GITHUB_RADAR_BRANCH),
        "path": secret_or_env("GITHUB_RADAR_PATH", DEFAULT_GITHUB_RADAR_PATH),
        "token": secret_or_env("GITHUB_RADAR_TOKEN", ""),
    }


def sample_state():
    return {
        "generated_at": "",
        "cycle_number": 0,
        "active_pairs": 0,
        "market_state": "WAITING",
        "regime_name": "WAITING",
        "btc": {"reason": "Start the scanner to populate radar_state.json", "rsi_15m": 0, "rsi_60m": 0, "above_vwap_15m": False, "above_vwap_60m": False},
        "sector_counts": {},
        "state_counts": {},
        "top_setups": [],
    }


@st.cache_data(ttl=8, show_spinner=False)
def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8")), True, "local"
        except Exception as e:
            return sample_state(), False, f"local read error: {e}"
    cfg = settings()
    url = f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg['path']}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "a-plus-radar-app", "X-GitHub-Api-Version": "2022-11-28"}
    if cfg["token"]:
        headers["Authorization"] = f"Bearer {cfg['token']}"
    try:
        r = requests.get(url, headers=headers, params={"ref": cfg["branch"], "_": time.time()}, timeout=10)
        if r.status_code != 200:
            return sample_state(), False, f"GitHub {r.status_code}: {r.text[:120]}"
        raw = base64.b64decode((r.json() or {}).get("content", "")).decode("utf-8")
        return json.loads(raw), True, "cloud"
    except Exception as e:
        return sample_state(), False, f"cloud read error: {e}"


def state_color(state):
    state = (state or "").upper()
    if state == "BULL": return "#78FF2E"
    if state in {"PREBULL", "WATCH", "WAITING"}: return "#FFD93D"
    return "#FF4D4D"


def tag_class(tag):
    tag = (tag or "").upper()
    if tag == "BULL": return "tag tag-bull"
    if tag == "SHARPSHOOTER": return "tag tag-sharp"
    if tag == "WATCHLIST": return "tag tag-watch"
    return "tag tag-pre"


def timing_color(t):
    t = (t or "").upper()
    if t == "ON TIME": return "#78FF2E"
    if t in {"EARLY", "WATCH", "WAIT"}: return "#FFD93D"
    return "#FF4D4D"


def spark(values, title, accent="#78FF2E"):
    vals = [float(v) for v in (values or []) if v is not None]
    fig = go.Figure()
    if len(vals) >= 2:
        colors = [accent if vals[i] >= vals[i-1] else "#FF5A4D" for i in range(1, len(vals))]
        fig.add_trace(go.Scatter(y=vals, mode="lines", line=dict(width=3, color=accent), fill="tozeroy", fillcolor="rgba(120,255,46,0.05)"))
    else:
        fig.add_trace(go.Scatter(y=[0,0], mode="lines", line=dict(width=2, color="#23303A")))
    fig.update_layout(height=118, margin=dict(l=0,r=0,t=24,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#071017", title=dict(text=title, font=dict(size=13,color=accent)), xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False)
    return fig


def bullets_for(s):
    cr = s.get("chart_read", {}) or {}
    flags = s.get("flags", {}) or {}
    items = []
    if flags.get("acceleration"): items.append("Momentum increasing")
    elif flags.get("impulse"): items.append("Strong move")
    else: items.append("Momentum building")
    items.append(cr.get("read_30m", "Chart forming"))
    if flags.get("vwap_accept"): items.append("Buyers holding control")
    else: items.append("Needs VWAP proof")
    return items[:3]


def render_setup_row(setup, idx):
    accents = ["#78FF2E", "#FF8A3D", "#35A7FF"]
    accent = accents[(idx-1) % 3]
    accent_class = "accent-orange" if idx == 2 else "accent-blue" if idx == 3 else ""
    coin = setup.get("coin") or str(setup.get("pair", "NONE")).split("/")[0]
    pair = setup.get("pair", "")
    tag = setup.get("tag", "WATCH")
    cr = setup.get("chart_read", {}) or {}
    timing = cr.get("timing", setup.get("entry_readiness_label", "WATCH"))
    b = bullets_for(setup)
    bullet_html = "".join([f"<div>{x}</div>" for x in b])
    t = int(setup.get("trigger_score", 0) or 0)
    tr = int(setup.get("trade_score", 0) or 0)
    c = int(setup.get("confidence", 0) or 0)
    st.markdown(f"""
    <div class="setup-row {accent_class}">
      <div class="rank-badge" style="border-color:{accent};">{idx}</div>
      <div>
        <div class="coin-title">{coin}</div>
        <div class="pair-small">{pair}</div>
        <div class="{tag_class(tag)}">{tag}</div>
        <div class="bullets">{bullet_html}</div>
      </div>
      <div class="scores">
        <div class="score-line"><div class="score-label">Trigger<br/>Score</div><div class="score-num score-trigger">{t}</div></div>
        <div class="score-line"><div class="score-label">Trade<br/>Score</div><div class="score-num score-trade">{tr}</div></div>
        <div class="score-line"><div class="score-label">Confidence<br/>Score</div><div class="score-num score-conf">{c}</div></div>
      </div>
      <div>
    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1: st.plotly_chart(spark(setup.get("close_30m", []), "30M MOVEMENT", accent), width="stretch", config={"displayModeBar": False})
    with col2: st.plotly_chart(spark(setup.get("close_1h", []), "1H MOVEMENT", accent), width="stretch", config={"displayModeBar": False})
    st.markdown(f"""
        <div class="timing-pill" style="border-color:{timing_color(timing)};color:{timing_color(timing)};">Timing: {timing}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def fires(n):
    try: n = int(n)
    except Exception: n = 0
    return "🔥" * min(max(n,0),3) if n else "—"


with st.sidebar:
    st.markdown("### Radar Controls")
    refresh = st.slider("Refresh seconds", 8, 60, 20)
    auto = st.toggle("Auto refresh", value=True)
    manual = st.button("Refresh now")
    st.caption("Scanner → GitHub JSON → Streamlit report")

state, ok, source = load_state()
if manual:
    st.cache_data.clear()
    st.rerun()
if auto:
    st.markdown(f"<script>setTimeout(function(){{window.location.reload();}}, {refresh*1000});</script>", unsafe_allow_html=True)

market = state.get("market_state") or state.get("regime_name") or "WAITING"
color = state_color(market)
btc = state.get("btc", {}) or {}
setups = state.get("top_setups", []) or []
sector_counts = state.get("sector_counts", {}) or {}
state_counts = state.get("state_counts", {}) or {}
updated = state.get("generated_at") or state.get("timestamp") or ""
cycle = state.get("cycle_number", state.get("cycle", 0))
active = state.get("active_pairs", 0)

st.markdown('<div class="report-shell">', unsafe_allow_html=True)
st.markdown(f"""
<div class="header">
  <div class="header-left">
    <div class="brand"><div class="logo">A+</div><div><div class="title"><span>A+</span> SCANNER REPORT</div><div class="subtitle">Real Time Market Radar</div></div></div>
    <div class="meta"><div>📅 <b>{str(updated)[:10] or 'waiting'}</b></div><div>🕒 <b>{str(updated)[11:19] or '--:--:--'}</b></div><div>🔄 Cycle: <b>{cycle}</b></div><div>🎯 Active Pairs: <b>{active}</b></div></div>
  </div>
  <div class="state-box">
    <div class="state-label">Market State</div>
    <div class="state-value" style="color:{color};">{market}</div>
    <div class="state-sub" style="color:{color};">{'Market warming up' if market=='PREBULL' else 'Trade-ready conditions' if market=='BULL' else 'Weak tape' if market=='BEAR' else 'Waiting for data'}</div>
    <div class="state-reason">{btc.get('reason','Start scanner')}</div>
  </div>
</div>
""", unsafe_allow_html=True)

if not ok:
    st.markdown(f'<div class="notice">Data source: {source}</div>', unsafe_allow_html=True)

st.markdown('<div class="section-title"><span>★ Top 3 Setups ★</span></div>', unsafe_allow_html=True)
if setups:
    for i, setup in enumerate(setups[:3], start=1):
        render_setup_row(setup, i)
else:
    st.markdown('<div class="notice">No live setups yet. Start the scanner and wait for the next cycle.</div>', unsafe_allow_html=True)
    for i in range(1,4):
        render_setup_row({"coin":"WAIT", "pair":"WAITING", "tag":"PREBUILD", "trigger_score":0,"trade_score":0,"confidence":0,"chart_read":{"timing":"WAIT","read_30m":"Waiting","read_1h":"Waiting"},"flags":{}}, i)

# Bottom panels
sector_rows = "".join([f'<div class="sector-row"><span>{k}</span><span>{fires(v)}</span></div>' for k,v in sorted(sector_counts.items(), key=lambda x:x[1], reverse=True)[:6]]) or '<div class="small">No sector flow yet.</div>'
counts_rows = "".join([f'<div class="metric-row"><span>{k}</span><b>{v}</b></div>' for k,v in state_counts.items()]) or '<div class="small">No state counts yet.</div>'
btc_state = market if market != "PREBULL" else "WATCH"
st.markdown(f"""
<div class="bottom-grid">
  <div class="bottom-panel">
    <div class="panel-title">Market Snapshot</div>
    <div class="btc-big" style="color:{color};">BTC {btc_state}</div>
    <div class="small">{btc.get('reason','Higher-timeframe read')}</div>
    <div class="metric-row"><span>BTC 15M RSI</span><b>{btc.get('rsi_15m',0)}</b></div>
    <div class="metric-row"><span>BTC 1H RSI</span><b>{btc.get('rsi_60m', btc.get('rsi_1h',0))}</b></div>
    <div class="metric-row"><span>15M VWAP</span><b>{'YES' if btc.get('above_vwap_15m') else 'NO'}</b></div>
    <div class="metric-row"><span>1H VWAP</span><b>{'YES' if btc.get('above_vwap_60m') or btc.get('above_vwap_1h') else 'NO'}</b></div>
  </div>
  <div class="bottom-panel"><div class="panel-title">Sector Flow</div>{sector_rows}</div>
  <div class="bottom-panel">
    <div class="panel-title">How To Read This</div>
    <div class="read-row"><div class="read-key" style="color:#FFD93D;">PREBUILD</div><div class="read-desc">Setup forming. Watch for confirmation.</div></div>
    <div class="read-row"><div class="read-key" style="color:#78FF2E;">BULL</div><div class="read-desc">Market and setup aligned. Trade ready.</div></div>
    <div class="read-row"><div class="read-key" style="color:#FF4D4D;">SHARPSHOOTER</div><div class="read-desc">Strong coin in weak market. Smaller size only.</div></div>
    <div class="read-row"><div class="read-key" style="color:#35A7FF;">TIMING</div><div class="read-desc">ON TIME = best zone. LATE = avoid chasing.</div></div>
  </div>
</div>
<div class="footer"><div><span class="left">🏆 Focus. Discipline. Execution.</span><br/><span class="small">Scan • Filter • Rank • Execute</span></div><div class="small">Not financial advice. Live market-read journal.</div></div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

