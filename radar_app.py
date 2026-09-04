import base64
import json
import html
import os
import time
import textwrap
import xml.etree.ElementTree as ET
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
from engines import *

import requests
import streamlit as st
import plotly.graph_objects as go

print("✅ All Radar engines loaded.")

STATE_PATH = Path("radar_state.json")
DEFAULT_GITHUB_RADAR_REPO = "Trans3/a-plus-live-radar"
DEFAULT_GITHUB_RADAR_BRANCH = "main"
DEFAULT_GITHUB_RADAR_PATH = "radar_state.json"
DEFAULT_GITHUB_PERFORMANCE_PATH = "radar_performance.json"
st.set_page_config(
    page_title="A+ Decision Radar",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
table{
    font-size:14px;
}
.billboard-table{
    width:100%;
    overflow-x:auto;
    display:block;
}
.sticky-upgrade{
    position:sticky;
    top:0;
    z-index:999;
    background:#061018;
    border:1px solid #FFD93D;
    border-radius:12px;
    padding:12px 16px;
    margin-bottom:18px;
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:10px;
    flex-wrap:wrap;
}

.sticky-btn{
    background:#FFD93D;
    color:#000;
    padding:10px 16px;
    border-radius:10px;
    font-weight:900;
}
:root{
  --bg:#05080C; --panel:#091119; --panel2:#071017; --line:#22303A;
  --green:#78FF2E; --yellow:#FFD93D; --red:#FF4D4D; --orange:#FF8A3D;
  --blue:#35A7FF; --purple:#BF65FF; --white:#F5F7FA; --muted:#9AA6B2;
}
.stApp{background:radial-gradient(circle at top left,#0f1a20 0%,#05080C 36%,#020407 100%);color:var(--white);} 
.block-container{max-width:1220px;padding-top:.8rem;padding-bottom:1.5rem;}
[data-testid="stSidebar"]{background:#14171f;}
#MainMenu, footer, header{visibility:hidden;}
.report-shell{border:1px solid var(--line);border-radius:18px;background:rgba(3,6,9,.94);padding:18px 20px;box-shadow:0 0 36px rgba(120,255,46,.08);} 
.header{display:grid;grid-template-columns:1.55fr .8fr;gap:18px;align-items:stretch;margin-bottom:14px;}
.header-left{border:1px solid var(--line);border-radius:14px;background:linear-gradient(135deg,#04090d,#08121a);padding:20px 24px;}
.brand{display:flex;gap:18px;align-items:center;}.logo{width:84px;height:84px;border:2px solid var(--green);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--green);font-size:40px;font-weight:1000;box-shadow:0 0 18px rgba(120,255,46,.25);} 
.title{font-size:50px;font-weight:1000;line-height:.95;letter-spacing:-1.5px;color:white;text-transform:uppercase;}.title span{color:var(--green);} .subtitle{margin-top:8px;color:var(--green);font-weight:900;letter-spacing:1px;text-transform:uppercase;}
.meta{display:flex;gap:22px;margin-top:18px;color:var(--white);font-weight:700;font-size:14px;flex-wrap:wrap;} .meta b{color:var(--green);}
.state-box{border:1px solid var(--line);border-radius:14px;background:#05080C;padding:18px;text-align:center;}.state-label{font-size:14px;font-weight:900;color:white;text-transform:uppercase;letter-spacing:.8px;}.state-value{font-size:44px;font-weight:1000;margin:10px 0 6px;text-transform:uppercase;}.state-sub{font-size:15px;font-weight:900;text-transform:uppercase;}.state-reason{font-size:13px;color:white;margin-top:6px;line-height:1.35;}
.decision-banner{display:grid;grid-template-columns:1.1fr .9fr .9fr;gap:12px;margin:12px 0 18px;}.decision-tile{border:1px solid var(--line);border-radius:13px;background:#071017;padding:14px 16px;}.tile-k{color:var(--muted);text-transform:uppercase;font-weight:900;font-size:12px;letter-spacing:.8px;}.tile-v{font-size:26px;font-weight:1000;margin-top:4px;}.tile-sub{font-size:13px;color:white;margin-top:5px;}
.section-title{display:flex;align-items:center;gap:18px;justify-content:center;margin:15px 0 12px;}.section-title:before,.section-title:after{content:"";height:3px;background:var(--green);flex:1;box-shadow:0 0 8px rgba(120,255,46,.5);} .section-title span{font-size:28px;font-weight:1000;text-transform:uppercase;letter-spacing:1px;}
.setup-card{border:1px solid var(--line);border-radius:16px;background:rgba(9,17,25,.96);padding:18px;margin-bottom:18px;}.setup-top{display:grid;grid-template-columns:90px 255px 200px 1fr;gap:18px;align-items:center;}.rank-badge{height:142px;border:3px solid var(--green);border-radius:18px;display:flex;align-items:center;justify-content:center;font-size:54px;font-weight:1000;color:white;background:#05080C;}.coin-title{font-size:46px;font-weight:1000;letter-spacing:1px;line-height:1;color:white;}.pair-small{color:var(--muted);font-size:13px;font-weight:700;margin-top:4px;}.tag{display:inline-block;border-radius:6px;padding:5px 12px;margin-top:9px;font-size:18px;font-weight:1000;text-transform:uppercase;background:#080A0E;}.tag-pre{border:2px solid var(--yellow);color:var(--yellow);}.tag-bull{border:2px solid var(--green);color:var(--green);}.tag-sharp{border:2px solid var(--red);color:var(--red);}.tag-watch{border:2px solid var(--blue);color:var(--blue);} 
.bullets{margin-top:10px;color:white;font-size:15px;font-weight:700;line-height:1.55;}.bullets div:before{content:"›";color:var(--green);font-weight:1000;margin-right:8px;}.accent-orange .bullets div:before{color:var(--orange);} .accent-blue .bullets div:before{color:var(--blue);} 
.scores{border-left:1px solid var(--line);border-right:1px solid var(--line);padding:0 18px;}.score-line{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid var(--line);padding:8px 0;}.score-line:last-child{border-bottom:0}.score-label{font-size:12px;font-weight:900;color:white;text-transform:uppercase;line-height:1.05;}.score-num{font-size:40px;font-weight:1000;line-height:1;}.score-trigger{color:var(--green)}.score-trade{color:var(--purple)}.score-conf{color:var(--blue)}
.decision-box{border:1px solid var(--line);border-radius:12px;background:#071017;padding:14px;}.decision-head{font-size:13px;color:var(--muted);font-weight:900;text-transform:uppercase;}.projected{font-size:30px;font-weight:1000;color:var(--green);}.riskgrid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px}.riskcell{border-top:1px solid #17232D;padding-top:8px}.riskcell span{display:block;font-size:11px;color:var(--muted);font-weight:900;text-transform:uppercase}.riskcell b{font-size:17px;color:white}.riskcell .red{color:var(--red)}.riskcell .green{color:var(--green)}
.tool-grid{display:grid;grid-template-columns:1.05fr .95fr;gap:14px;margin-top:14px;}.tool-panel{border:1px solid var(--line);border-radius:12px;background:#071017;padding:12px;}.tool-title{font-size:14px;font-weight:1000;color:var(--green);text-transform:uppercase;margin-bottom:8px;}.stage-row{display:flex;align-items:center;gap:7px;flex-wrap:wrap;}.stage{padding:7px 9px;border:1px solid #27343D;border-radius:999px;font-size:12px;font-weight:1000;text-transform:uppercase;color:#9AA6B2;}.stage-on{border-color:var(--green);color:var(--green);box-shadow:0 0 12px rgba(120,255,46,.18)}.stage-current{background:rgba(120,255,46,.14)}.arrow{color:#64707A;font-weight:1000}.timing-track{position:relative;height:42px;margin:8px 0 2px;background:linear-gradient(90deg,rgba(255,217,61,.16),rgba(120,255,46,.22),rgba(255,77,77,.18));border:1px solid #27343D;border-radius:999px;}.timing-labels{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);font-weight:900;text-transform:uppercase;padding:0 8px}.timing-marker{position:absolute;top:-6px;width:8px;height:54px;border-radius:8px;background:white;box-shadow:0 0 14px white}.next-box{font-size:14px;line-height:1.45;color:white}.next-box b{color:var(--green)}.fail{color:var(--red);font-weight:900}.why{color:white;font-weight:700;line-height:1.5}.bottom-grid{display:grid;grid-template-columns:1.1fr 1fr 1.25fr;gap:14px;margin-top:14px;}.bottom-panel{border:1px solid var(--line);border-radius:14px;background:rgba(9,17,25,.92);padding:16px;min-height:178px;}.panel-title{color:var(--green);font-size:18px;font-weight:1000;text-transform:uppercase;text-align:center;margin-bottom:12px;}.btc-big{font-size:32px;font-weight:1000;text-transform:uppercase;}.metric-row{display:flex;justify-content:space-between;border-top:1px solid #17232D;padding:8px 0;color:white;font-size:14px;}.sector-row{display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #17232D;padding:6px 0;font-size:17px;font-weight:900;}.read-row{display:grid;grid-template-columns:130px 1fr;gap:8px;border-bottom:1px solid #17232D;padding:9px 0;}.read-key{font-weight:1000;text-transform:uppercase;}.read-desc{color:white;}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:16px;border-top:1px solid var(--line);padding-top:14px;color:white;font-weight:800;}.footer .left{color:var(--green);font-size:18px}.small{font-size:13px;color:var(--muted);font-weight:500;}.notice{border:1px solid #3b3f14;background:rgba(255,217,61,.18);border-radius:10px;padding:10px 14px;color:#fff3a3;margin:10px 0 14px;font-weight:700;}
.refresh-row{display:flex;justify-content:flex-end;align-items:center;gap:10px;margin:2px 0 10px;color:var(--muted);font-size:12px;font-weight:800;}
div.stButton > button:first-child{background:#071017;border:1px solid var(--green);color:var(--green);border-radius:999px;padding:.45rem 1rem;font-weight:1000;box-shadow:0 0 10px rgba(120,255,46,.12);}
div.stButton > button:first-child:hover{border-color:white;color:white;background:#0A1720;}

.perf-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:12px 0 18px;}.perf-card{border:1px solid var(--line);border-radius:13px;background:#071017;padding:14px 15px;}.perf-k{color:var(--muted);font-size:12px;font-weight:900;text-transform:uppercase;letter-spacing:.6px;}.perf-v{font-size:28px;font-weight:1000;color:var(--green);margin-top:4px;}.perf-sub{font-size:12px;color:white;margin-top:3px;}.perf-table{width:100%;border-collapse:collapse;margin-top:8px;}.perf-table th{color:var(--muted);font-size:12px;text-transform:uppercase;text-align:left;border-bottom:1px solid var(--line);padding:8px;}.perf-table td{color:white;border-bottom:1px solid #17232D;padding:8px;font-size:13px;}.badge-good{color:var(--green);font-weight:1000}.badge-warn{color:var(--yellow);font-weight:1000}.badge-bad{color:var(--red);font-weight:1000}
.proof-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:12px 0 18px;}.proof-panel{border:1px solid var(--line);border-radius:13px;background:#071017;padding:14px;}.proof-title{font-size:15px;font-weight:1000;color:var(--green);text-transform:uppercase;margin-bottom:8px;}.proof-table{width:100%;border-collapse:collapse;}.proof-table th{color:var(--muted);font-size:11px;text-transform:uppercase;text-align:left;border-bottom:1px solid var(--line);padding:6px;}.proof-table td{color:white;border-bottom:1px solid #17232D;padding:6px;font-size:12px;}.edge-pos{color:var(--green);font-weight:1000}.edge-neg{color:var(--red);font-weight:1000}
.env-box{border:1px solid #27343D;border-radius:12px;background:#05080C;padding:10px 12px;margin-top:10px;}.env-k{font-size:11px;color:var(--muted);font-weight:1000;text-transform:uppercase;letter-spacing:.7px;}.env-v{font-size:24px;font-weight:1000;margin-top:3px;color:var(--green);}.env-tier{display:inline-block;border:1px solid currentColor;border-radius:999px;padding:3px 9px;margin-left:8px;font-size:12px;font-weight:1000;}.env-adj{font-size:12px;color:white;margin-top:6px;line-height:1.35;}.env-pos{color:var(--green);font-weight:1000}.env-neg{color:var(--red);font-weight:1000}

.billboard-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:12px 0 18px;}
.billboard-panel{border:1px solid var(--line);border-radius:13px;background:#071017;padding:14px;}
.billboard-title{font-size:15px;font-weight:1000;color:var(--green);text-transform:uppercase;margin-bottom:8px;}
.billboard-table{width:100%;border-collapse:collapse;}
.billboard-table th{color:var(--muted);font-size:11px;text-transform:uppercase;text-align:left;border-bottom:1px solid var(--line);padding:6px;}
.billboard-table td{color:white;border-bottom:1px solid #17232D;padding:6px;font-size:12px;}
.billboard-up{color:var(--green);font-weight:1000}.billboard-down{color:var(--red);font-weight:1000}

.exec-clock{border:1px solid #27343D;border-radius:12px;background:#05080C;padding:10px 12px;margin-top:10px;}
.exec-k{font-size:11px;color:var(--muted);font-weight:1000;text-transform:uppercase;letter-spacing:.7px;}
.exec-v{font-size:24px;font-weight:1000;margin-top:3px;}
.exec-sub{font-size:13px;color:white;margin-top:3px;line-height:1.35;}
.exec-now{color:var(--green)}.exec-wait{color:var(--yellow)}.exec-late{color:var(--red)}.exec-watch{color:var(--blue)}
.countdown-pill{display:inline-block;border-radius:999px;border:1px solid currentColor;padding:3px 9px;margin-left:8px;font-size:12px;font-weight:1000;}
/* Premium decision-card upgrades */
.cta-main{border:1px solid var(--green);color:var(--green);border-radius:999px;padding:8px 12px;font-size:12px;font-weight:1000;background:rgba(120,255,46,.08);}
.cta-secondary{border:1px solid var(--yellow);color:var(--yellow);border-radius:999px;padding:8px 12px;font-size:12px;font-weight:1000;background:rgba(255,217,61,.08);}
.rank-wrap{height:142px;border:3px solid var(--green);border-radius:18px;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#05080C;}
.rank-num{font-size:52px;font-weight:1000;color:white;line-height:1;}
.rank-note{font-size:11px;text-transform:uppercase;color:var(--muted);font-weight:1000;margin-top:4px;}
.rank-stars{font-size:16px;color:var(--yellow);letter-spacing:1px;margin-top:2px;}
.coin-meta{display:flex;gap:7px;flex-wrap:wrap;margin-top:8px;}
.sector-chip{display:inline-block;border:1px solid #27343D;background:#05080C;border-radius:999px;color:white;padding:4px 9px;font-size:11px;font-weight:1000;text-transform:uppercase;}
.score-block{border-left:1px solid var(--line);border-right:1px solid var(--line);padding:0 18px;}
.score-card{border-bottom:1px solid var(--line);padding:8px 0;}
.score-card:last-child{border-bottom:0;}
.score-head{display:flex;justify-content:space-between;align-items:center;gap:8px;}
.score-name{font-size:11px;font-weight:1000;color:white;text-transform:uppercase;letter-spacing:.55px;}
.score-val{font-size:28px;font-weight:1000;line-height:1;}
.score-track{height:8px;background:#111B23;border-radius:999px;overflow:hidden;margin-top:7px;border:1px solid #23313A;}
.score-fill{height:100%;border-radius:999px;background:currentColor;box-shadow:0 0 10px currentColor;}
.verdict-box{border:1px solid #27343D;border-radius:12px;background:#05080C;padding:10px 12px;margin-bottom:10px;}
.verdict-k{font-size:11px;color:var(--muted);font-weight:1000;text-transform:uppercase;letter-spacing:.7px;}
.verdict-v{font-size:28px;font-weight:1000;margin-top:2px;text-transform:uppercase;}
.move-line{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px;align-items:center;}
.move-pill{border:1px solid #27343D;border-radius:10px;padding:8px;text-align:center;background:#05080C;}
.move-pill span{display:block;font-size:10px;color:var(--muted);font-weight:1000;text-transform:uppercase;}
.move-pill b{font-size:15px;color:white;}
.why-score{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px;}
.why-chip{border:1px solid #27343D;border-radius:10px;background:#05080C;padding:8px 9px;font-size:12px;font-weight:800;color:white;}
.why-chip b{float:right;}
.why-pos b{color:var(--green);} .why-neg b{color:var(--red);} .why-warn b{color:var(--yellow);}
.status-chip{display:inline-block;border:1px solid currentColor;border-radius:999px;padding:3px 9px;font-size:11px;font-weight:1000;text-transform:uppercase;}
@media(max-width:900px){
  .setup-top{grid-template-columns:1fr;}
  .rank-wrap{height:auto;padding:14px;}
  .score-block{border-left:0;border-right:0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);}
  .decision-banner,.header,.tool-grid,.bottom-grid,.billboard-grid,.proof-grid,.perf-grid{grid-template-columns:1fr;}
}

</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def normalize_streamlit_html(html: str) -> str:
    """Prevent Streamlit Markdown from rendering indented HTML as code blocks."""
    return "\n".join(line.lstrip() for line in str(html).splitlines()).strip()



def secret_or_env(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, os.getenv(name, default))).strip()
    except Exception:
        return str(os.getenv(name, default)).strip()


def normalize_repo(repo: str) -> str:
    """Keep the configured GitHub repo stable."""
    return (repo or DEFAULT_GITHUB_RADAR_REPO).strip()


def settings():
    return {
        "repo": normalize_repo(secret_or_env("GITHUB_RADAR_REPO", DEFAULT_GITHUB_RADAR_REPO)),
        "branch": secret_or_env("GITHUB_RADAR_BRANCH", DEFAULT_GITHUB_RADAR_BRANCH),
        "path": secret_or_env("GITHUB_RADAR_PATH", DEFAULT_GITHUB_RADAR_PATH),
        "performance_path": secret_or_env("GITHUB_PERFORMANCE_PATH", DEFAULT_GITHUB_PERFORMANCE_PATH),
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
    """Cloud-first loader.

    Streamlit deployments can accidentally include a stale local radar_state.json.
    Reading GitHub first prevents the site from freezing on an old bundled file.
    Set PREFER_LOCAL_STATE=1 only for local debugging.
    """
    prefer_local = secret_or_env("PREFER_LOCAL_STATE", "0") == "1"
    cfg = settings()

    def read_local():
        if STATE_PATH.exists():
            try:
                return json.loads(STATE_PATH.read_text(encoding="utf-8")), True, "local"
            except Exception as e:
                return sample_state(), False, f"local read error: {e}"
        return None

    if prefer_local:
        local = read_local()
        if local:
            return local

    raw_url = (
        "https://raw.githubusercontent.com/"
        f"{cfg['repo']}/{cfg['branch']}/{cfg['path']}?t={int(time.time())}"
    )

    try:
        r = requests.get(
            raw_url,
            headers={
                "User-Agent": "a-plus-radar-app",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            timeout=10,
        )

        if r.status_code == 200:
            return r.json(), True, "cloud: GitHub raw radar_state.json"

        cloud_error = f"GitHub raw HTTP {r.status_code}: {r.text[:120]}"

    except Exception as e:
        cloud_error = f"cloud read error: {e}"

    local = read_local()
    if local:
        data, ok, src = local
        return data, ok, f"{src}; cloud failed: {cloud_error}"

    return sample_state(), False, cloud_error



def sample_performance():
    return {
        "generated_at": "",
        "cycle_number": 0,
        "summary": {
            "total_signals": 0,
            "hit_1pct_rate": 0,
            "hit_2pct_rate": 0,
            "avg_max_move_pct": 0,
            "best_pair": "—",
            "best_move_pct": 0,
        },
        "records": [],
    }


@st.cache_data(ttl=8, show_spinner=False)
def load_performance():
    """Cloud-first loader for radar_performance.json."""
    prefer_local = secret_or_env("PREFER_LOCAL_STATE", "0") == "1"
    cfg = settings()
    local_path = Path(cfg.get("performance_path") or DEFAULT_GITHUB_PERFORMANCE_PATH)

    def read_local():
        if local_path.exists():
            try:
                return json.loads(local_path.read_text(encoding="utf-8")), True, "local"
            except Exception as e:
                return sample_performance(), False, f"local performance read error: {e}"
        return None

    if prefer_local:
        local = read_local()
        if local:
            return local

    raw_url = (
        "https://raw.githubusercontent.com/"
        f"{cfg['repo']}/{cfg['branch']}/{cfg['performance_path']}?t={int(time.time())}"
    )

    try:
        r = requests.get(
            raw_url,
            headers={
                "User-Agent": "a-plus-radar-app",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            },
            timeout=10,
        )

        if r.status_code == 200:
            return r.json(), True, "cloud: GitHub raw radar_performance.json"

        cloud_error = f"GitHub performance raw HTTP {r.status_code}: {r.text[:120]}"

    except Exception as e:
        cloud_error = f"cloud performance read error: {e}"

    local = read_local()
    if local:
        data, ok, src = local
        return data, ok, f"{src}; cloud failed: {cloud_error}"

    return sample_performance(), False, cloud_error


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


def safe_float(x, default=0.0):
    try:
        if x is None: return default
        return float(x)
    except Exception:
        return default

def pct_change(values):
    vals = [safe_float(v) for v in (values or []) if safe_float(v) > 0]
    if len(vals) < 2 or vals[0] <= 0: return 0.0
    return (vals[-1] - vals[0]) / vals[0] * 100.0


def range_pct(values):
    vals = [safe_float(v) for v in (values or []) if safe_float(v) > 0]
    if len(vals) < 2: return 0.0
    last = vals[-1] or 1
    return (max(vals) - min(vals)) / last * 100.0


def projected_move(setup, market):
    close30 = setup.get("close_30m", []) or []
    close1h = setup.get("close_1h", []) or []
    vol30 = range_pct(close30)
    vol1h = range_pct(close1h)
    ch30 = abs(pct_change(close30))
    flags = setup.get("flags", {}) or {}
    t = safe_float(setup.get("trigger_score"))
    tr = safe_float(setup.get("trade_score"))
    c = safe_float(setup.get("confidence"))
    quality = max(0.45, min(1.35, (0.45*t + 0.25*tr + 0.30*c) / 100.0))
    structure_boost = 0.35 if flags.get("vwap_accept") else 0.0
    structure_boost += 0.25 if flags.get("pullback") else 0.0
    structure_boost += 0.25 if flags.get("structure_break") else 0.0
    structure_boost += 0.20 if flags.get("volume_spike") else 0.0
    structure_boost += 0.25 if flags.get("acceleration") else 0.0
    regime = (market or "").upper()
    regime_mult = 1.15 if regime == "BULL" else 1.0 if regime == "PREBULL" else 0.78 if regime == "BEAR" else 0.9
    base = (0.45 * vol1h) + (0.35 * vol30) + (0.20 * ch30) + structure_boost
    high = max(0.35, min(8.0, base * quality * regime_mult))
    low = max(0.15, min(high * 0.72, high * 0.42))
    conf = int(max(20, min(95, 20 + (quality * 45) + (structure_boost * 12) + (12 if regime in {"BULL","PREBULL"} else 0))))
    return round(low, 2), round(high, 2), conf


def trade_levels(setup, market):
    price = safe_float(setup.get("price"))
    vwap = safe_float(setup.get("vwap"))
    low, high, _ = projected_move(setup, market)
    if price <= 0:
        return {"entry_low":"—", "entry_high":"—", "stop":"—", "target":"—", "rr":"—"}
    if vwap > 0 and vwap < price:
        entry_low = max(vwap, price * 0.992)
        entry_high = price * 1.002
        stop = min(vwap * 0.996, entry_low * 0.994)
    else:
        entry_low = price * 0.994
        entry_high = price * 1.002
        stop = price * 0.988
    target = price * (1 + high / 100.0)
    risk = max(1e-9, entry_high - stop)
    reward = max(0.0, target - entry_high)
    rr = reward / risk if risk else 0
    decimals = 6 if price < 1 else 4 if price < 10 else 2
    fmt = lambda x: f"${x:,.{decimals}f}"
    return {"entry_low":fmt(entry_low), "entry_high":fmt(entry_high), "stop":fmt(stop), "target":fmt(target), "rr":f"{rr:.1f}:1"}


def setup_stages(setup):
    flags = setup.get("flags", {}) or {}
    cr = setup.get("chart_read", {}) or {}
    timing = (cr.get("timing") or setup.get("entry_readiness_label") or "WATCH").upper()
    stages = [
        ("Compression", bool(flags.get("compression"))),
        ("Impulse", bool(flags.get("impulse") or flags.get("acceleration"))),
        ("Pullback", bool(flags.get("pullback"))),
        ("VWAP Hold", bool(flags.get("vwap_accept"))),
        ("Entry", timing == "ON TIME"),
    ]
    current = 0
    for i, (_, passed) in enumerate(stages):
        if passed: current = i
    return stages, current


def timing_position(timing):
    t = (timing or "").upper()
    if t == "EARLY": return 20
    if t in {"ON TIME", "OPTIMAL", "READY SOON"}: return 50
    if t in {"LATE", "REJECTED"}: return 84
    return 34

def parse_time_to_epoch(value):
    """Parse scanner timestamps safely. Returns current time if missing."""
    if not value:
        return time.time()
    try:
        txt = str(value).strip().replace("Z", "+00:00")
        # scanner usually exports local ISO without timezone; treat as local wall time.
        dt = datetime.fromisoformat(txt)
        if dt.tzinfo is not None:
            return dt.timestamp()
        return dt.timestamp()
    except Exception:
        return time.time()


def setup_age_minutes(setup, state_generated_at=""):
    """Best available setup age. Uses setup first_seen if scanner provides it; otherwise snapshot age."""
    for key in ("first_seen", "signal_time", "created_at", "detected_at"):
        if setup.get(key):
            return max(0.0, (time.time() - parse_time_to_epoch(setup.get(key))) / 60.0)
    # fallback: age of latest radar snapshot, usually near 0 in cloud refresh.
    return max(0.0, (time.time() - parse_time_to_epoch(state_generated_at)) / 60.0)


def execution_clock(setup, market="", state_generated_at=""):
    """Simple trader clock: NOW / WAIT / TOO LATE.
    Designed to answer: should I act now, wait, or skip?
    """
    cr = setup.get("chart_read", {}) or {}
    timing = (cr.get("timing") or setup.get("entry_readiness_label") or "WATCH").upper()
    flags = setup.get("flags", {}) or {}
    age = setup_age_minutes(setup, state_generated_at)
    rsi = safe_float(setup.get("rsi_1m"))
    price = safe_float(setup.get("price"))
    vwap = safe_float(setup.get("vwap"))
    dist_vwap = ((price - vwap) / vwap * 100.0) if price > 0 and vwap > 0 else 0.0

    # Hard late conditions: protects users from chasing.
    if timing in {"LATE", "REJECTED"} or rsi >= 74 or dist_vwap > 2.2:
        return {
            "status": "TOO LATE",
            "class": "exec-late",
            "window": "Skip this move",
            "minutes_left": 0,
            "message": "Move is extended. Wait for a fresh base, VWAP reclaim, or new pullback.",
        }

    # Prime execution zone: on-time pullback with control. This should be brief.
    if timing in {"ON TIME", "OPTIMAL", "READY SOON"}:
        valid_for = max(0, int(round(6 - age)))
        if valid_for <= 0:
            return {
                "status": "CHECK AGAIN",
                "class": "exec-watch",
                "window": "Window may be stale",
                "minutes_left": 0,
                "message": "Radar snapshot is aging. Refresh and confirm VWAP still holds before acting.",
            }
        return {
            "status": "EXECUTE ZONE",
            "class": "exec-now",
            "window": f"Next {valid_for} min",
            "minutes_left": valid_for,
            "message": "Act only on continuation confirmation. Stop is invalidation/VWAP loss.",
        }

    # Early impulse: do not buy first green move; wait for the pullback.
    if timing == "EARLY" or (flags.get("impulse") and not flags.get("pullback")):
        return {
            "status": "WAIT",
            "class": "exec-wait",
            "window": "Watch 5–15 min",
            "minutes_left": None,
            "message": "Do not chase the first push. Wait for pullback + VWAP hold.",
        }

    # Weak/no proof states.
    if not flags.get("vwap_accept"):
        return {
            "status": "NO ENTRY",
            "class": "exec-late",
            "window": "Needs VWAP reclaim",
            "minutes_left": None,
            "message": "No buyer control yet. Entry is not valid until VWAP/control returns.",
        }

    return {
        "status": "WATCH",
        "class": "exec-watch",
        "window": "Needs trigger",
        "minutes_left": None,
        "message": "Setup is visible, but no clean execution trigger yet.",
    }


def global_execution_decision(setups, market, state_generated_at=""):
    if not setups:
        return {"status":"WAIT", "class":"exec-watch", "window":"No setups", "message":"No valid setups detected."}
    # Prefer the first top-ranked setup, but avoid telling users to trade in dangerous market phases.
    best = setups[0]
    clock = execution_clock(best, market, state_generated_at)
    if str(market).upper() in {"BEAR", "DISTRIBUTION", "EXHAUSTION"} and clock["status"] == "EXECUTE ZONE":
        clock = dict(clock)
        clock["status"] = "SHARPSHOOTER ONLY"
        clock["class"] = "exec-wait"
        clock["message"] = "Market is not supportive. Smaller size only; skip if confirmation is not immediate."
    return clock



TOP_SETUP_LIMIT = 5
PERF_WIN_LEVEL_PCT = 2.0
PERF_SCALP_LEVEL_PCT = 1.0
PERF_FAIL_LEVEL_PCT = -1.2


def setup_key(setup):
    return f"{setup.get('pair','UNKNOWN')}|{setup.get('tag','')}"


def setup_timing(setup):
    return (setup.get("chart_read", {}) or {}).get("timing", setup.get("entry_readiness_label", "WATCH"))


def init_perf_tracker():
    if "perf_ledger" not in st.session_state:
        st.session_state.perf_ledger = {}
    if "perf_started_at" not in st.session_state:
        st.session_state.perf_started_at = time.time()


def update_perf_tracker(setups, market):
    """Browser-session performance tracker.
    Tracks what happens after a setup appears while this app is open.
    Production upgrade later: move this to scanner-side persistent history.
    """
    init_perf_tracker()
    now = time.time()
    active_keys = set()
    for setup in (setups or [])[:TOP_SETUP_LIMIT]:
        key = setup_key(setup)
        active_keys.add(key)
        price = safe_float(setup.get("price"))
        if price <= 0:
            continue
        low, high, pconf = projected_move(setup, market)
        if key not in st.session_state.perf_ledger:
            st.session_state.perf_ledger[key] = {
                "pair": setup.get("pair", ""),
                "tag": setup.get("tag", ""),
                "first_seen": now,
                "last_seen": now,
                "entry_price": price,
                "last_price": price,
                "max_price": price,
                "min_price": price,
                "projected_low": low,
                "projected_high": high,
                "confidence": int(setup.get("confidence", 0) or 0),
                "timing_first": setup_timing(setup),
                "timing_last": setup_timing(setup),
                "status": "OPEN",
            }
        rec = st.session_state.perf_ledger[key]
        rec["last_seen"] = now
        rec["last_price"] = price
        rec["max_price"] = max(safe_float(rec.get("max_price")), price)
        rec["min_price"] = min(safe_float(rec.get("min_price"), price), price)
        rec["timing_last"] = setup_timing(setup)
        rec["confidence"] = int(setup.get("confidence", rec.get("confidence", 0)) or 0)
        entry = safe_float(rec.get("entry_price"))
        if entry > 0:
            rec["max_gain_pct"] = round((rec["max_price"] - entry) / entry * 100, 3)
            rec["max_drawdown_pct"] = round((rec["min_price"] - entry) / entry * 100, 3)
            rec["current_pct"] = round((price - entry) / entry * 100, 3)
        else:
            rec["max_gain_pct"] = rec["max_drawdown_pct"] = rec["current_pct"] = 0.0
        if rec["max_gain_pct"] >= PERF_WIN_LEVEL_PCT:
            rec["status"] = "HIT +2%"
        elif rec["max_gain_pct"] >= PERF_SCALP_LEVEL_PCT:
            rec["status"] = "HIT +1%"
        elif rec["max_drawdown_pct"] <= PERF_FAIL_LEVEL_PCT:
            rec["status"] = "DRAWDOWN"
        else:
            rec["status"] = "OPEN"
    for key, rec in st.session_state.perf_ledger.items():
        if key not in active_keys and now - rec.get("last_seen", now) > 120:
            if rec.get("status") == "OPEN":
                rec["status"] = "INACTIVE"


def perf_summary():
    init_perf_tracker()
    records = list(st.session_state.perf_ledger.values())
    total = len(records)
    hit1 = sum(1 for r in records if safe_float(r.get("max_gain_pct")) >= PERF_SCALP_LEVEL_PCT)
    hit2 = sum(1 for r in records if safe_float(r.get("max_gain_pct")) >= PERF_WIN_LEVEL_PCT)
    dd = sum(1 for r in records if safe_float(r.get("max_drawdown_pct")) <= PERF_FAIL_LEVEL_PCT)
    avg = sum(safe_float(r.get("max_gain_pct")) for r in records) / total if total else 0
    best = max(records, key=lambda r: safe_float(r.get("max_gain_pct")), default={})
    return {
        "total": total,
        "hit1": hit1,
        "hit2": hit2,
        "dd": dd,
        "hit2_rate": (hit2 / total * 100) if total else 0,
        "hit1_rate": (hit1 / total * 100) if total else 0,
        "avg_max": avg,
        "best": best,
    }



def _render_proof_bucket(title, rows, limit=6):
    rows = rows or []
    if not rows:
        return f"""
        <div class="proof-panel"><div class="proof-title">{title}</div><div class="small">Waiting for enough tracked records.</div></div>
        """
    body = []
    for r in rows[:limit]:
        edge = safe_float(r.get("edge_score", 0))
        total = int(r.get("total", 0) or 0)
        sample_note = " <span style='color:#FFD93D;font-weight:900;'>LOW N</span>" if total < 20 else ""
        edge_cls = "edge-pos" if edge >= 0 else "edge-neg"
        body.append(
            f"<tr><td>{r.get('name','')}{sample_note}</td><td>{total}</td>"
            f"<td>{safe_float(r.get('hit_1pct_rate')):.0f}%</td><td>{safe_float(r.get('hit_2pct_rate')):.0f}%</td>"
            f"<td>{safe_float(r.get('avg_max_move_pct')):+.2f}%</td><td class='{edge_cls}'>{edge:+.1f}</td></tr>"
        )
    return f"""
    <div class="proof-panel"><div class="proof-title">{title}</div>
      <table class="proof-table"><thead><tr><th>Bucket</th><th>N</th><th>+1%</th><th>+2%</th><th>Avg Max</th><th>Edge</th></tr></thead><tbody>{''.join(body)}</tbody></table>
    </div>
    """


def render_proof_analytics(summary):
    proof = summary.get("proof_read", {}) or {}
    html = f"""
    <div class="section-title"><span> Proof Analytics </span></div>
    <div class="decision-banner">
      <div class="decision-tile"><div class="tile-k">Best Regime</div><div class="tile-v" style="color:#78FF2E;">{proof.get('best_regime','UNKNOWN')}</div><div class="tile-sub">Directional until sample size grows.</div></div>
      <div class="decision-tile"><div class="tile-k">Best Timing</div><div class="tile-v" style="color:#35A7FF;">{proof.get('best_timing','UNKNOWN')}</div><div class="tile-sub">Use this to refine alerts.</div></div>
      <div class="decision-tile"><div class="tile-k">Best Setup</div><div class="tile-v" style="color:#FFD93D;">{proof.get('best_setup_type','UNKNOWN')}</div><div class="tile-sub">Buckets under 30 samples are not proven yet.</div></div>
    </div>
    <div class="proof-grid">
      {_render_proof_bucket('By Regime', summary.get('by_regime'))}
      {_render_proof_bucket('By Timing', summary.get('by_timing'))}
      {_render_proof_bucket('By Sector', summary.get('by_sector'))}
      {_render_proof_bucket('By Tag', summary.get('by_tag'))}
      {_render_proof_bucket('By Setup Type', summary.get('by_setup_type'))}
      {_render_proof_bucket('By RSI Zone', summary.get('by_rsi_zone'))}
      {_render_proof_bucket('By VWAP Distance', summary.get('by_vwap_distance'))}
      {_render_proof_bucket('By Environment Tier', summary.get('by_environment_tier'))}
      {_render_proof_bucket('By Hour', summary.get('by_hour'))}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)



def fmt_pct(x):
    v = safe_float(x)
    cls = "billboard-up" if v >= 0 else "billboard-down"
    return f"<span class='{cls}'>{v:+.2f}%</span>"


def fmt_volume(x):
    v = safe_float(x)
    if v >= 1_000_000:
        return f"${v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v/1_000:.0f}K"
    return f"${v:.0f}"


def billboard_rows(rows, show_score=True):
    if not rows:
        return "<tr><td colspan='5'>Waiting for billboard data.</td></tr>"
    html = []
    for r in rows[:10]:
        score_cell = f"<td>{safe_float(r.get('billboard_score')):.2f}</td>" if show_score else ""
        html.append(
            "<tr>"
            f"<td><b>{r.get('pair','')}</b></td>"
            f"<td>{fmt_pct(r.get('change_1h_pct', 0))}</td>"
            f"<td>{fmt_pct(r.get('change_24h_pct', 0))}</td>"
            f"<td>{fmt_volume(r.get('usd_volume', 0))}</td>"
            f"{score_cell}"
            "</tr>"
        )
    return "".join(html)


def render_billboard_dashboard(state):
    billboard = (state or {}).get("billboard", {}) or {}
    one_hour = billboard.get("one_hour", []) or []
    twenty_four = billboard.get("twenty_four_hour", []) or []
    if membership == "Free":
        one_hour = one_hour[:5]
        twenty_four = twenty_four[:5]
    note = billboard.get("note", "1H board is primary. 24H board is context only.")

    upgrade_html = "" if has_tier(membership, "Pro Analytics") else '''
<div class="sticky-upgrade">
  <div>
    <div style="font-weight:900;color:#FFD93D;">PREBULL Momentum Detected</div>
    <div class="small">Unlock execution reasoning, invalidations, and analytics engine.</div>
  </div>
  <div class="sticky-btn">Upgrade Access</div>
</div>
'''
    st.markdown(f"""
{upgrade_html}
<div class="section-title"><span>Kraken Billboard</span></div>
<div class="notice">{note}</div>
<div class="billboard-grid">
  <div class="billboard-panel">
    <div class="billboard-title">ONE H Momentum Board | Primary Radar</div>
    <table class="billboard-table">
      <thead><tr><th>Pair</th><th>ONE H</th><th>TWENTY FOUR H</th><th>Vol</th><th>Score</th></tr></thead>
      <tbody>{billboard_rows(one_hour, show_score=True)}</tbody>
    </table>
  </div>
  <div class="billboard-panel">
    <div class="billboard-title">TWENTY FOUR H Context Board | Not Entry Signal</div>
    <table class="billboard-table">
      <thead><tr><th>Pair</th><th>ONE H</th><th>TWENTY FOUR H</th><th>Vol</th></tr></thead>
      <tbody>{billboard_rows(twenty_four, show_score=False)}</tbody>
    </table>
  </div>
</div>
""", unsafe_allow_html=True)



def tier_rank(tier):
    ranks = {
        "Free": 0,
        "Basic": 1,
        "Premium": 2,
        "Pro Analytics": 3,
    }
    return ranks.get(tier, 0)


def has_tier(tier, required):
    return tier_rank(tier) >= tier_rank(required)


def locked_panel(title, required_tier, body, cta="Get Full Radar"):
    st.markdown(f"""
    <div class="proof-panel" style="margin:12px 0 18px;">
      <div class="proof-title">LOCK {title}</div>
      <div class="small">{body}</div>
      <div style="margin-top:12px;color:#FFD93D;font-weight:1000;">Requires {required_tier} | {cta}</div>
    </div>
    """, unsafe_allow_html=True)


def simple_setup_action(setup, market, updated):
    clock = execution_clock(setup, market, updated)
    return clock.get("status", "WATCH"), clock.get("window", "Needs trigger"), clock.get("message", "Wait for clean confirmation.")


def render_top5_simple(setups, market, updated, membership):
    st.markdown('<div class="section-title"><span> Top 5 Decision Setups </span></div>', unsafe_allow_html=True)

    if not setups:
        st.markdown('<div class="notice">No live setups yet. Start the scanner and wait for the next cycle.</div>', unsafe_allow_html=True)
        return

    for i, setup in enumerate(setups[:TOP_SETUP_LIMIT], start=1):
        pair = setup.get("pair", "UNKNOWN")
        coin = setup.get("coin") or str(pair).split("/")[0]
        tag = tag_for(setup)
        cr = setup.get("chart_read", {}) or {}
        timing = cr.get("timing", setup.get("entry_readiness_label", "WATCH"))
        action, window, msg = simple_setup_action(setup, market, updated)
        trigger = int(setup.get("trigger_score", 0) or 0)
        trade = int(setup.get("trade_score", 0) or 0)
        confidence = int(setup.get("confidence", 0) or 0)

        if membership == "Free":
            detail = "Upgrade for reason, entry zone, invalidation, and proof analytics."
            scores = f"T{trigger}"
        else:
            detail = why_text(setup)
            scores = f"T{trigger} / TR{trade} / C{confidence}"

        # Keep each HTML block starting at column 0. Indented HTML can render as a code block in Streamlit Markdown.
        card_html = (
            '<div class="decision-tile" style="margin-bottom:10px;">'
            '<div style="display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap;">'
            '<div>'
            f'<div class="tile-k">#{i} · {tag}</div>'
            f'<div class="tile-v" style="font-size:26px;color:#F5F7FA;">{coin} <span class="small">{pair}</span></div>'
            '</div>'
            '<div style="text-align:right;">'
            '<div class="tile-k">Action</div>'
            f'<div class="tile-v" style="font-size:22px;color:{timing_color(timing)};">{action}</div>'
            f'<div class="small">{window} · {scores}</div>'
            '</div>'
            '</div>'
            f'<div class="tile-sub">{msg}</div>'
            f'<div class="small" style="margin-top:6px;">{detail}</div>'
            '</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    if membership == "Free":
        locked_panel(
            "Full setup reasoning locked",
            "Basic",
            "Free view shows the top five names and simple action labels. Basic unlocks the reasoning behind each setup.",
        )
    elif membership == "Basic":
        locked_panel(
            "Execution details locked",
            "Premium",
            "Premium unlocks entry zone, invalidation, target estimate, environment score, execution clock, and decision chart.",
        )


def render_performance_dashboard(perf_state=None, perf_ok=True, perf_source="cloud"):
    perf_state = perf_state or sample_performance()
    summary = perf_state.get("summary", {}) or {}
    records = perf_state.get("records", []) or []
    total = int(summary.get("total_signals", len(records)) or 0)
    hit1_rate = safe_float(summary.get("hit_1pct_rate", 0))
    hit2_rate = safe_float(summary.get("hit_2pct_rate", 0))
    avg_max = safe_float(summary.get("avg_max_move_pct", 0))
    best_pair = summary.get("best_pair", "—") or "—"
    best_gain = safe_float(summary.get("best_move_pct", 0))
    updated = perf_state.get("generated_at", "")
    source_note = "Persistent scanner-side history" if perf_ok else f"Performance source issue: {perf_source}"

    st.markdown(f"""
    <div class="section-title"><span> Performance Dashboard </span></div>
    <div class="perf-grid">
      <div class="perf-card"><div class="perf-k">Tracked Signals</div><div class="perf-v">{total}</div><div class="perf-sub">Scanner-side history</div></div>
      <div class="perf-card"><div class="perf-k">Hit +1%</div><div class="perf-v">{hit1_rate:.1f}%</div><div class="perf-sub">Since tracking started</div></div>
      <div class="perf-card"><div class="perf-k">Hit +2%</div><div class="perf-v">{hit2_rate:.2f}%</div><div class="perf-sub">Momentum target test</div></div>
      <div class="perf-card"><div class="perf-k">Avg Max Move</div><div class="perf-v">{avg_max:+.3f}%</div><div class="perf-sub">Observed after alert</div></div>
      <div class="perf-card"><div class="perf-k">Best Signal</div><div class="perf-v" style="font-size:22px;">{best_pair}</div><div class="perf-sub">{best_gain:+.1f}% max</div></div>
    </div>
    <div class="notice">{source_note}. Updated: {updated or 'waiting for scanner'}.</div>
    """, unsafe_allow_html=True)

    records = sorted(records, key=lambda r: r.get("last_seen", r.get("first_seen", "")), reverse=True)[:15]
    if records:
        rows = []
        for r in records:
            status = r.get("status", "OPEN")
            cls = "badge-good" if "HIT" in status else "badge-bad" if status == "DRAWDOWN" else "badge-warn"
            rows.append(
                f"<tr><td>{r.get('pair','')}</td><td>{r.get('tag','')}</td><td>{r.get('timing_last','')}</td>"
                f"<td class='{cls}'>{status}</td><td>{safe_float(r.get('current_pct')):+.2f}%</td>"
                f"<td>{safe_float(r.get('max_gain_pct', r.get('max_move_pct'))):+.2f}%</td>"
                f"<td>{safe_float(r.get('max_drawdown_pct', r.get('drawdown_pct'))):+.2f}%</td></tr>"
            )
        st.markdown("""
        <div class="bottom-panel" style="margin-bottom:18px;">
          <div class="panel-title">Recent Signal Outcomes</div>
          <table class="perf-table"><thead><tr><th>Pair</th><th>Type</th><th>Timing</th><th>Status</th><th>Now</th><th>Max</th><th>Drawdown</th></tr></thead><tbody>
        """ + "".join(rows) + "</tbody></table></div>", unsafe_allow_html=True)
    else:
        st.markdown('<div class="notice">No persistent performance records yet. Run v21 scanner through a full cycle.</div>', unsafe_allow_html=True)

    render_proof_analytics(summary)

def decision_chart(setup, market, accent="#78FF2E"):
    price = safe_float(setup.get("price"))
    vals = [safe_float(v) for v in (setup.get("close_30m") or setup.get("close_1h") or []) if safe_float(v) > 0]
    if not vals and price > 0:
        vals = [price]
    levels = trade_levels(setup, market)
    vwap = safe_float(setup.get("vwap"))
    fig = go.Figure()
    if len(vals) >= 2:
        fig.add_trace(go.Scatter(y=vals, mode="lines", name="Price", line=dict(width=3, color=accent)))
    else:
        fig.add_trace(go.Scatter(y=[price, price], mode="lines", name="Price", line=dict(width=3, color=accent)))
    # Plotly hlines require numeric levels; parse levels by using raw approximate from price/projection
    low, high, _ = projected_move(setup, market)
    if price > 0:
        target = price * (1 + high / 100)
        stop = price * 0.988
        if vwap > 0:
            fig.add_hline(y=vwap, line_dash="dot", line_color="#FFD93D", annotation_text="VWAP", annotation_font_color="#FFD93D")
        fig.add_hline(y=target, line_dash="dash", line_color="#78FF2E", annotation_text="Target", annotation_font_color="#78FF2E")
        fig.add_hline(y=stop, line_dash="dash", line_color="#FF4D4D", annotation_text="Invalid", annotation_font_color="#FF4D4D")
    fig.update_layout(height=205, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#071017", xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False)
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


def tag_for(setup):
    return setup.get("tag") or setup.get("state") or "WATCH"


def action_text(setup, timing):
    t = (timing or "").upper()
    if t == "ON TIME":
        return "Execute only if the next candles confirm continuation. If it hesitates or loses VWAP, skip."
    if t == "EARLY":
        return "Wait 5–15 minutes for pullback + VWAP hold. Do not chase the first push."
    if t == "LATE":
        return "Too late. Skip this move and wait for a new base or clean VWAP reclaim."
    return "Watch only. No clean trigger until price proves control."


def why_text(setup):
    flags = setup.get("flags", {}) or {}
    if flags.get("pullback") and flags.get("vwap_accept"):
        return "Buyers are defending VWAP after a move. That is where continuation setups become tradable."
    if flags.get("impulse") and not flags.get("pullback"):
        return "Impulse is visible, but the safer money waits for the first pullback instead of chasing expansion."
    if flags.get("vwap_accept"):
        return "Buyer control is present, but the setup still needs cleaner timing or confirmation."
    return "The radar sees activity, but this is not actionable until control and structure improve."





def clean_text(value, default=""):
    try:
        return html.escape(str(value if value is not None else default))
    except Exception:
        return html.escape(str(default))


def clamp_score(value):
    return max(0, min(100, int(safe_float(value, 0))))


def score_color(score):
    score = clamp_score(score)
    if score >= 80:
        return "#78FF2E"
    if score >= 60:
        return "#FFD93D"
    return "#FF4D4D"


def score_bar_html(label, value, color=None):
    score = clamp_score(value)
    color = color or score_color(score)
    return (
        '<div class="score-card">'
        '<div class="score-head">'
        f'<div class="score-name">{clean_text(label)}</div>'
        f'<div class="score-val" style="color:{color};">{score}</div>'
        '</div>'
        '<div class="score-track">'
        f'<div class="score-fill" style="width:{score}%;color:{color};"></div>'
        '</div>'
        '</div>'
    )


def setup_sector_label(setup):
    sector = (setup.get("sector") or "").upper()
    if sector and sector != "OTHER":
        return sector
    pair = str(setup.get("pair", "") or setup.get("coin", "")).upper()
    coin = (setup.get("coin") or pair.split("/")[0]).upper()
    local_map = {
        "TIA": "INFRA", "LINK": "INFRA", "GRT": "INFRA", "FIL": "INFRA",
        "SOL": "L1", "ETH": "L1", "ADA": "L1", "AVAX": "L1", "ATOM": "L1",
        "DOGE": "MEME", "SHIB": "MEME", "PEPE": "MEME", "BONK": "MEME", "WIF": "MEME",
        "UNI": "DEFI", "AAVE": "DEFI", "MKR": "DEFI", "CRV": "DEFI",
    }
    return local_map.get(coin, "OTHER")


def decision_label(setup, clock):
    status = (clock.get("status") or "WATCH").upper()
    if status in {"EXECUTE ZONE", "READY"}:
        return "READY"
    if status in {"WAIT", "WATCH", "CHECK AGAIN"}:
        return "WATCH"
    if status in {"TOO LATE", "NO ENTRY"}:
        return "AVOID"
    if "SHARPSHOOTER" in status:
        return "SHARPSHOOTER"
    return status


def star_rating(*scores):
    vals = [clamp_score(v) for v in scores if v is not None]
    avg = sum(vals) / len(vals) if vals else 0
    stars = max(1, min(5, round(avg / 20)))
    return "★" * stars + "☆" * (5 - stars)


def environment_tier_clean(setup, market):
    tier = (setup.get("environment_tier") or "").upper()
    if tier and tier != "UNKNOWN":
        return tier
    env = clamp_score(setup.get("environment_score", setup.get("composite_score", setup.get("trigger_score", 0))))
    if env >= 85:
        return "A+"
    if env >= 75:
        return "A"
    if env >= 60:
        return "B"
    if str(market).upper() in {"BULL", "EXPANSION"}:
        return "B"
    if str(market).upper() in {"PREBULL", "WATCH", "ACCUMULATION"}:
        return "C+"
    return "C"


def why_score_breakdown_html(setup, market, clock):
    flags = setup.get("flags", {}) or {}
    rows = []
    def add(label, points, cls=None):
        if cls is None:
            cls = "why-pos" if points >= 0 else "why-neg"
        sign = "+" if points >= 0 else ""
        rows.append(f'<div class="why-chip {cls}">{clean_text(label)} <b>{sign}{int(points)}</b></div>')
    if flags.get("vwap_accept"):
        add("VWAP control", 15)
    else:
        add("Needs VWAP", -10)
    if flags.get("pullback"):
        add("Pullback formed", 12)
    if flags.get("acceleration") or flags.get("impulse"):
        add("Momentum impulse", 12)
    if flags.get("structure_break"):
        add("Structure break", 10)
    if flags.get("volume_spike"):
        add("Volume support", 8)
    m = str(market).upper()
    if m in {"BULL", "EXPANSION"}:
        add("Market supportive", 10)
    elif m in {"BEAR", "DISTRIBUTION", "EXHAUSTION"}:
        add("Market risk", -12)
    else:
        add("Market neutral", -4, "why-warn")
    if clock.get("status") in {"TOO LATE", "NO ENTRY"}:
        add("Timing penalty", -15)
    elif clock.get("status") == "EXECUTE ZONE":
        add("Timing active", 10)
    return "".join(rows[:6]) or '<div class="why-chip why-warn">Waiting for proof <b>0</b></div>'

def environment_adjustments_html(setup, limit=4):
    rows = []
    for adj in (setup.get("environment_adjustments") or [])[:limit]:
        if isinstance(adj, dict):
            reason = adj.get("reason", "Adjustment")
            points = safe_float(adj.get("points"), 0)
        elif isinstance(adj, (list, tuple)) and len(adj) >= 2:
            reason, points = adj[0], safe_float(adj[1], 0)
        else:
            continue
        cls = "env-pos" if points >= 0 else "env-neg"
        sign = "+" if points >= 0 else ""
        rows.append(f"<div><span class='{cls}'>{sign}{int(points)}</span> {reason}</div>")
    return "".join(rows) or "<div>No environment adjustments yet.</div>"

def render_setup_card(setup, idx, market, state_generated_at=""):
    accents = ["#78FF2E", "#FF8A3D", "#35A7FF", "#BF65FF", "#FFD93D"]
    accent = accents[(idx-1) % len(accents)]
    accent_class = "accent-orange" if idx in (2,5) else "accent-blue" if idx == 3 else ""

    coin = setup.get("coin") or str(setup.get("pair", "NONE")).split("/")[0]
    pair = setup.get("pair", "")
    tag = tag_for(setup)
    sector = setup_sector_label(setup)
    cr = setup.get("chart_read", {}) or {}
    timing = cr.get("timing", setup.get("entry_readiness_label", "WATCH"))

    t = clamp_score(setup.get("trigger_score", 0))
    tr = clamp_score(setup.get("trade_score", 0))
    c = clamp_score(setup.get("confidence", 0))
    env_score = clamp_score(setup.get("environment_score", setup.get("composite_score", t)))
    env_tier = environment_tier_clean(setup, market)

    low, high, pconf = projected_move(setup, market)
    levels = trade_levels(setup, market)
    clock = execution_clock(setup, market, state_generated_at)
    verdict = decision_label(setup, clock)
    verdict_color = "#78FF2E" if verdict == "READY" else "#FFD93D" if verdict in {"WATCH", "SHARPSHOOTER"} else "#FF4D4D"
    stars = star_rating(t, tr, c, env_score)

    b = bullets_for(setup)
    bullet_html = "".join([f"<div>{clean_text(x)}</div>" for x in b])
    score_html = (
        score_bar_html("Trigger", t, "#78FF2E") +
        score_bar_html("Trade", tr, "#BF65FF") +
        score_bar_html("Confidence", c, "#35A7FF") +
        score_bar_html("Environment", env_score, score_color(env_score))
    )
    why_html = why_score_breakdown_html(setup, market, clock)
    env_adj_html = environment_adjustments_html(setup)

    stages, current = setup_stages(setup)
    stage_html = ""
    for i, (name, passed) in enumerate(stages):
        cls = "stage stage-on" if passed else "stage"
        if i == current:
            cls += " stage-current"
        stage_html += f"<span class='{cls}'>{clean_text(name)}</span>"
        if i < len(stages)-1:
            stage_html += "<span class='arrow'>→</span>"

    pos = timing_position(timing)
    st.markdown(normalize_streamlit_html(f"""
    <div class="setup-card {accent_class}">
      <div class="setup-top">
        <div class="rank-wrap" style="border-color:{accent};">
          <div class="rank-num">#{idx}</div>
          <div class="rank-note">Top Setup</div>
          <div class="rank-stars">{stars}</div>
        </div>

        <div>
          <div class="coin-title">{clean_text(coin)}</div>
          <div class="pair-small">{clean_text(pair)}</div>
          <div class="coin-meta">
            <span class="{tag_class(tag)}">{clean_text(tag)}</span>
            <span class="sector-chip">{clean_text(sector)}</span>
            <span class="sector-chip">BTC {clean_text(market)}</span>
          </div>
          <div class="bullets">{bullet_html}</div>
        </div>

        <div class="score-block">
          {score_html}
        </div>

        <div class="decision-box">
          <div class="verdict-box">
            <div class="verdict-k">Radar Decision</div>
            <div class="verdict-v" style="color:{verdict_color};">{verdict}</div>
            <div class="small">{clean_text(clock.get('message','Wait for clean timing.'))}</div>
          </div>

          <div class="decision-head">Expected Move Range</div>
          <div class="projected">+{low}% → +{high}%</div>
          <div class="small">Model confidence: {pconf}% | range estimate, not certainty</div>

          <div class="move-line">
            <div class="move-pill"><span>Invalid</span><b style="color:#FF4D4D;">{levels['stop']}</b></div>
            <div class="move-pill"><span>Entry Zone</span><b>{levels['entry_low']} — {levels['entry_high']}</b></div>
            <div class="move-pill"><span>Target</span><b style="color:#78FF2E;">{levels['target']}</b></div>
          </div>

          <div class="env-box">
            <div class="env-k">Environment Weight</div>
            <div class="env-v">{env_score}/100 <span class="env-tier">{clean_text(env_tier)}</span></div>
            <div class="env-adj">{env_adj_html}</div>
          </div>

          <div class="exec-clock">
            <div class="exec-k">Execution Clock</div>
            <div class="exec-v {clock['class']}">{clean_text(clock['status'])} <span class="countdown-pill">{clean_text(clock['window'])}</span></div>
            <div class="exec-sub">{clean_text(clock['message'])}</div>
          </div>
        </div>
      </div>

      <div class="tool-grid">
        <div class="tool-panel">
          <div class="tool-title">Decision Map: Price vs VWAP / Target / Invalidation</div>
    """), unsafe_allow_html=True)

    st.plotly_chart(decision_chart(setup, market, accent), width="stretch", config={"displayModeBar": False})

    st.markdown(normalize_streamlit_html(f"""
        </div>
        <div class="tool-panel">
          <div class="tool-title">Why It Scored This Way</div>
          <div class="why-score">{why_html}</div>

          <div class="tool-title" style="margin-top:14px;">Veteran Read</div>
          <div class="stage-row">{stage_html}</div>

          <div class="tool-title" style="margin-top:14px;color:{timing_color(timing)};">Timing Gauge</div>
          <div class="timing-track"><div class="timing-marker" style="left:{pos}%;background:{timing_color(timing)};box-shadow:0 0 12px {timing_color(timing)};"></div></div>
          <div class="timing-labels"><span>Early</span><span>On Time</span><span>Late</span></div>

          <div class="next-box" style="margin-top:12px;"><b>Simple answer:</b> <span class="{clock['class']}">{clean_text(clock['status'])}</span> | {clean_text(action_text(setup, timing))}</div>
          <div class="next-box" style="margin-top:8px;"><b>Why:</b> {clean_text(why_text(setup))}</div>
          <div class="next-box fail" style="margin-top:8px;">Fail condition: VWAP loss / lower low invalidates the idea.</div>
        </div>
      </div>
    </div>
    """), unsafe_allow_html=True)

def fires(n):
    try: n = int(n)
    except Exception: n = 0
    return "🔥" * min(max(n,0),3) if n else "—"




# ---------------------------------------------------------------------------
# ATC CONTROL TOWER UI
# Tracks each momentum opportunity like a flight:
# departure -> climb -> cruise -> descent -> landing.
# The user sees actionable timing, remaining opportunity, and what changes next.
# ---------------------------------------------------------------------------

ATC_CSS = """
<style>
.decision-3{grid-template-columns:repeat(3,minmax(0,1fr)) !important;}
.decision-3 .data-box{min-height:92px;}
@media(max-width:900px){.decision-3{grid-template-columns:1fr !important;}}

:root{
  --bg:#02070b; --panel:#07131b; --panel2:#040b11; --line:#18313f;
  --text:#f4f8fb; --muted:#8498a6; --green:#72ff9a; --yellow:#ffd85a;
  --red:#ff6262; --blue:#55bfff; --cyan:#79e7ff;
}
.stApp{
  background:
    radial-gradient(circle at 50% -10%,rgba(48,111,140,.14),transparent 34%),
    linear-gradient(rgba(27,61,76,.07) 1px,transparent 1px),
    linear-gradient(90deg,rgba(27,61,76,.07) 1px,transparent 1px),
    var(--bg);
  background-size:auto,56px 56px,56px 56px,auto;
  color:var(--text);
}
.block-container{max-width:1220px;padding-top:.65rem;padding-bottom:2rem;}
#MainMenu,footer,header{visibility:hidden;}
[data-testid="stSidebar"]{background:#07131b;}
.atc-shell{max-width:1160px;margin:0 auto;}
.atc-top{display:flex;justify-content:space-between;align-items:center;gap:14px;padding:10px 2px 15px;border-bottom:1px solid var(--line);}
.atc-brand{display:flex;align-items:center;gap:12px;}
.atc-logo{width:44px;height:44px;border:1px solid var(--cyan);border-radius:50%;display:flex;align-items:center;justify-content:center;color:var(--cyan);font-weight:1000;box-shadow:0 0 18px rgba(121,231,255,.12);}
.atc-name{font-size:20px;font-weight:1000;letter-spacing:.11em;}
.atc-sub{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.16em;margin-top:2px;}
.atc-sync{font-size:11px;color:var(--muted);font-weight:900;letter-spacing:.08em;}
.atc-sync:before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--green);margin-right:8px;box-shadow:0 0 12px var(--green);}
.tower-grid{display:grid;grid-template-columns:1.45fr .75fr;gap:14px;margin-top:16px;}
.tower-command{border:1px solid var(--line);border-radius:20px;background:linear-gradient(145deg,#07131b,#03080c);padding:26px;}
.kicker{font-size:11px;color:var(--muted);font-weight:1000;text-transform:uppercase;letter-spacing:.18em;}
.command-action{font-size:64px;line-height:.95;font-weight:1000;letter-spacing:-.04em;margin:12px 0 12px;}
.command-copy{font-size:17px;line-height:1.45;color:var(--text);}
.command-target{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-top:20px;padding-top:18px;border-top:1px solid var(--line);}
.command-cell{border:1px solid #142c38;border-radius:11px;background:#040b11;padding:11px;}
.command-k{font-size:10px;color:var(--muted);font-weight:1000;text-transform:uppercase;}
.command-v{font-size:17px;font-weight:1000;margin-top:4px;}
.airspace{border:1px solid var(--line);border-radius:20px;background:#07131b;padding:19px;}
.airspace-row{display:flex;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid var(--line);}
.airspace-row:last-child{border-bottom:0;}
.airspace-k{color:var(--muted);font-size:12px;font-weight:800;}
.airspace-v{font-size:16px;font-weight:1000;}
.section-head{display:flex;justify-content:space-between;align-items:end;gap:12px;margin:25px 0 10px;}
.section-title{font-size:18px;font-weight:1000;letter-spacing:.08em;text-transform:uppercase;}
.section-note{font-size:12px;color:var(--muted);}
.sector-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:9px;margin-bottom:18px;}
.sector-card{border:1px solid var(--line);border-radius:13px;background:#07131b;padding:12px;}
.sector-name{font-size:12px;font-weight:1000;text-transform:uppercase;}
.sector-read{font-size:18px;font-weight:1000;margin-top:5px;}
.sector-sub{font-size:11px;color:var(--muted);margin-top:4px;}
.flight-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;align-items:stretch;}
.flight-card{border:1px solid var(--line);border-radius:16px;background:#07131b;padding:16px;position:relative;min-height:330px;min-width:0;overflow:hidden;}
.flight-card:after{content:"";position:absolute;left:15px;right:15px;bottom:0;height:2px;background:currentColor;}
.flight-top{display:flex;justify-content:space-between;align-items:start;gap:10px;}
.flight-pair{font-size:20px;font-weight:1000;}
.flight-sector{font-size:10px;color:var(--muted);font-weight:1000;text-transform:uppercase;margin-top:3px;}
.flight-phase{font-size:11px;font-weight:1000;text-transform:uppercase;text-align:right;}
.flight-action{font-size:27px;font-weight:1000;margin:14px 0 6px;}
.flight-reason{font-size:13px;color:var(--text);line-height:1.4;min-height:37px;}
.flight-data{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px;}
.data-box{border:1px solid #142c38;border-radius:10px;background:#040b11;padding:9px;}
.data-k{font-size:9px;color:var(--muted);font-weight:1000;text-transform:uppercase;}
.data-v{font-size:14px;color:var(--text);font-weight:1000;margin-top:3px;}
.next-step{margin-top:11px;padding-top:10px;border-top:1px solid var(--line);font-size:12px;color:var(--muted);line-height:1.45;}.briefing{margin-top:12px;display:grid;grid-template-columns:1fr;gap:7px;}.brief-line{border-left:2px solid currentColor;padding-left:9px;font-size:12px;color:var(--text);line-height:1.4;}.brief-line b{color:var(--muted);font-size:10px;text-transform:uppercase;letter-spacing:.07em;display:block;margin-bottom:2px;}
.next-step b{color:var(--text);}
.progress-track{height:7px;border:1px solid #17313d;border-radius:999px;background:#03080c;overflow:hidden;margin-top:10px;}
.progress-fill{height:100%;background:currentColor;border-radius:999px;}
.empty{border:1px dashed var(--line);border-radius:14px;padding:22px;color:var(--muted);text-align:center;}
.detail{border:1px solid var(--line);border-radius:18px;background:#07131b;padding:20px;}
.detail-grid{display:grid;grid-template-columns:.72fr 1.28fr;gap:18px;}
.detail-left{border-right:1px solid var(--line);padding-right:18px;}
.detail-pair{font-size:25px;font-weight:1000;margin-top:5px;}
.detail-action{font-size:38px;font-weight:1000;margin:10px 0;}
.detail-checks{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.check{border:1px solid #142c38;border-radius:10px;background:#040b11;padding:10px;font-size:13px;}
.broadcast-badge{position:fixed;top:14px;right:18px;z-index:9999;border:1px solid var(--red);background:rgba(2,7,11,.9);color:var(--red);border-radius:999px;padding:6px 10px;font-size:11px;font-weight:1000;letter-spacing:.13em;text-transform:uppercase;}
.broadcast-mode [data-testid="stSidebar"],.broadcast-mode [data-testid="collapsedControl"],.broadcast-mode div.stButton,.broadcast-mode .stSelectbox>label{display:none!important;}
@media(max-width:900px){
  .tower-grid,.detail-grid{grid-template-columns:1fr;}
  .flight-grid{grid-template-columns:1fr;}
  .sector-strip{grid-template-columns:1fr 1fr;}
  .command-target{grid-template-columns:1fr;}
  .detail-left{border-right:0;border-bottom:1px solid var(--line);padding-right:0;padding-bottom:15px;}
  .command-action{font-size:50px;}
}

.live-tape-wrap{
  margin:14px 0 18px;
  border:1px solid var(--line);
  border-radius:12px;
  background:#040b11;
  overflow:hidden;
  position:relative;
}
.live-tape-label{
  display:inline-block;
  padding:8px 12px;
  border-right:1px solid var(--line);
  color:var(--cyan);
  font-size:10px;
  font-weight:1000;
  letter-spacing:.14em;
  text-transform:uppercase;
  background:#07131b;
  position:absolute;
  left:0;top:0;bottom:0;
  z-index:2;
  display:flex;
  align-items:center;
}
.live-tape-track{
  margin-left:118px;
  white-space:nowrap;
  overflow:hidden;
}
.live-tape-inner{
  display:inline-block;
  padding:9px 0;
  animation:atcTicker 34s linear infinite;
}
.live-tape-item{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding:0 22px;
  border-right:1px solid #17313d;
  font-size:12px;
  color:var(--text);
}
.live-tape-item b{font-size:12px;}
.live-tape-item .status{font-weight:1000;text-transform:uppercase;}
@keyframes atcTicker{
  from{transform:translateX(0);}
  to{transform:translateX(-50%);}
}
.traffic-feed{
  border:1px solid var(--line);
  border-radius:16px;
  background:#07131b;
  padding:14px;
  margin-top:14px;
}
.traffic-title{
  font-size:11px;
  color:var(--muted);
  font-weight:1000;
  text-transform:uppercase;
  letter-spacing:.14em;
  margin-bottom:8px;
}
.traffic-row{
  display:grid;
  grid-template-columns:62px 1fr;
  gap:10px;
  padding:8px 0;
  border-bottom:1px solid var(--line);
  font-size:12px;
}
.traffic-row:last-child{border-bottom:0;}
.traffic-time{color:var(--muted);font-weight:900;}
.traffic-event{color:var(--text);}
.sharp-badge{
  display:inline-block;
  border:1px solid var(--green);
  color:var(--green);
  border-radius:999px;
  padding:2px 7px;
  font-size:9px;
  font-weight:1000;
  letter-spacing:.05em;
  text-transform:uppercase;
}


.read-state{
  display:inline-block;
  border:1px solid currentColor;
  border-radius:999px;
  padding:3px 8px;
  font-size:9px;
  font-weight:1000;
  text-transform:uppercase;
  letter-spacing:.05em;
  margin-left:6px;
}


.news-rail{position:fixed;right:14px;top:220px;width:275px;max-height:68vh;overflow-y:auto;z-index:20;border:1px solid var(--line);border-radius:16px;background:rgba(7,19,27,.97);padding:14px;backdrop-filter:blur(8px);}
.news-title{font-size:11px;color:var(--muted);font-weight:1000;text-transform:uppercase;letter-spacing:.14em;margin-bottom:8px;}
.news-sub{font-size:11px;color:var(--muted);margin-bottom:10px;line-height:1.35;}
.news-item{display:block;padding:10px 0;border-bottom:1px solid var(--line);text-decoration:none!important;}
.news-item:last-child{border-bottom:0;}
.news-symbol{display:inline-block;color:var(--cyan);font-size:9px;font-weight:1000;text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;}
.news-headline{color:var(--text);font-size:12px;line-height:1.35;font-weight:800;}
.news-meta{color:var(--muted);font-size:10px;margin-top:4px;}
@media(max-width:1550px){.news-rail{position:relative;right:auto;top:auto;width:auto;max-height:none;margin:14px 0 18px;}}


.market-command-rail{
  position:fixed;
  left:14px;
  top:220px;
  width:275px;
  max-height:68vh;
  overflow-y:auto;
  z-index:20;
  border:1px solid var(--line);
  border-radius:16px;
  background:rgba(7,19,27,.97);
  padding:14px;
  backdrop-filter:blur(8px);
}

.aplus-feed-row{
  padding:10px 0;
  border-bottom:1px solid var(--line);
}
.aplus-feed-row:last-child{border-bottom:0;}
.aplus-feed-top{
  display:flex;
  justify-content:space-between;
  gap:8px;
  align-items:center;
}
.aplus-feed-pair{
  color:var(--text);
  font-size:12px;
  font-weight:1000;
}
.aplus-feed-status{
  font-size:9px;
  font-weight:1000;
  text-transform:uppercase;
  letter-spacing:.05em;
}
.aplus-feed-read{
  margin-top:4px;
  color:var(--cyan);
  font-size:10px;
  font-weight:900;
  text-transform:uppercase;
}
.aplus-feed-meta{
  margin-top:4px;
  color:var(--muted);
  font-size:10px;
  line-height:1.35;
}
.aplus-feed-time{
  color:var(--muted);
  font-size:9px;
  font-weight:900;
}

.market-command-title{
  font-size:11px;
  color:var(--muted);
  font-weight:1000;
  text-transform:uppercase;
  letter-spacing:.14em;
  margin-bottom:10px;
}
.control-block{
  padding:11px 0;
  border-bottom:1px solid var(--line);
}
.control-block:last-child{border-bottom:0;}
.control-label{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:10px;
  color:var(--muted);
  font-size:10px;
  font-weight:1000;
  text-transform:uppercase;
  letter-spacing:.07em;
}
.control-value{
  font-size:22px;
  font-weight:1000;
  color:var(--text);
  margin-top:4px;
}
.control-sub{
  color:var(--muted);
  font-size:10px;
  line-height:1.35;
  margin-top:4px;
}
.control-track{
  height:8px;
  border:1px solid #17313d;
  border-radius:999px;
  background:#03080c;
  overflow:hidden;
  margin-top:8px;
}
.control-fill{
  height:100%;
  border-radius:999px;
}
.balance-row{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:8px;
  margin-top:7px;
  font-size:10px;
  font-weight:900;
}
.weather-grid{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:7px;
  margin-top:8px;
}
.weather-cell{
  border:1px solid #142c38;
  border-radius:9px;
  background:#040b11;
  padding:8px;
}
.weather-k{
  color:var(--muted);
  font-size:9px;
  font-weight:1000;
  text-transform:uppercase;
}
.weather-v{
  color:var(--text);
  font-size:12px;
  font-weight:1000;
  margin-top:3px;
}
.flow-row{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:10px;
  padding:5px 0;
  font-size:11px;
}
.strategy-box{
  margin-top:8px;
  border:1px solid #142c38;
  border-radius:10px;
  background:#040b11;
  padding:9px;
}
.strategy-name{
  font-size:13px;
  font-weight:1000;
  color:var(--text);
}
.strategy-note{
  font-size:10px;
  color:var(--muted);
  line-height:1.35;
  margin-top:3px;
}
@media(max-width:1550px){
  .market-command-rail{
    position:relative;
    left:auto;
    top:auto;
    width:auto;
    max-height:none;
    margin:14px 0 18px;
  }
}

</style>
"""
st.markdown(ATC_CSS, unsafe_allow_html=True)


SECTOR_MAP = {
    "DOGE":"MEME","SHIB":"MEME","PEPE":"MEME","BONK":"MEME","WIF":"MEME","FLOKI":"MEME","PUMP":"MEME","FARTCOIN":"MEME",
    "FET":"AI","RENDER":"AI","RNDR":"AI","TAO":"AI","NEAR":"AI","AKT":"AI","GRT":"AI","VIRTUAL":"AI","ICP":"AI",
    "SOL":"L1","ETH":"L1","ADA":"L1","AVAX":"L1","ATOM":"L1","HBAR":"L1","DOT":"L1","SUI":"L1","SEI":"L1","APT":"L1",
    "ONDO":"RWA","XLM":"RWA","XRP":"RWA","LINK":"INFRA","TIA":"INFRA","FIL":"INFRA","AR":"INFRA",
    "AAVE":"DEFI","UNI":"DEFI","MKR":"DEFI","CRV":"DEFI","LDO":"DEFI","JUP":"DEFI",
    "IMX":"GAMING","BEAM":"GAMING","SUPER":"GAMING","GALA":"GAMING","SAND":"GAMING","MANA":"GAMING",
}


def atc_sector(setup):
    explicit = str(setup.get("sector", "") or "").upper()
    if explicit and explicit not in {"OTHER", "UNKNOWN"}:
        return explicit
    coin = str(setup.get("coin") or setup.get("pair", "")).split("/")[0].upper()
    return SECTOR_MAP.get(coin, "OTHER")


def atc_vwap(setup):
    flags = setup.get("flags", {}) or {}
    price = safe_float(setup.get("price", setup.get("last_price", setup.get("close", 0))))
    vwap = safe_float(setup.get("vwap", setup.get("vwap_1m", setup.get("session_vwap", 0))))
    if setup.get("vwap_distance_pct") is not None:
        distance = safe_float(setup.get("vwap_distance_pct"))
    elif price > 0 and vwap > 0:
        distance = (price - vwap) / vwap * 100
    else:
        return "Unavailable", None
    if flags.get("vwap_accept") and abs(distance) <= .65:
        return "Holding", distance
    if distance > .65:
        return "Above", distance
    if abs(distance) <= .35:
        return "Testing", distance
    return "Below", distance


def atc_metrics(setup, market, generated_at):
    flags = setup.get("flags", {}) or {}
    cr = setup.get("chart_read", {}) or {}

    ch1 = safe_float(setup.get("change_1h_pct", setup.get("pct_1h", pct_change(setup.get("close_1h", [])))))
    ch24 = safe_float(setup.get("change_24h_pct", setup.get("pct_24h", setup.get("twenty_four_hour_change", 0))))

    rsi1 = safe_float(setup.get("rsi_1m", setup.get("rsi", 50)), 50)
    rsi5 = safe_float(setup.get("rsi_5m", 50), 50)
    rsi15 = safe_float(setup.get("rsi_15m", 50), 50)

    macd1 = safe_float(setup.get("macd_hist_1m", setup.get("macd_hist", 0)))
    macd5 = safe_float(setup.get("macd_hist_5m", 0))
    macd15 = safe_float(setup.get("macd_hist_15m", 0))

    age = setup_age_minutes(setup, generated_at)
    timing = str(cr.get("timing") or setup.get("entry_readiness_label") or "WATCH").upper()
    vwap_label, vwap_dist = atc_vwap(setup)
    sector = atc_sector(setup)

    market_upper = str(market).upper()
    market_bad = market_upper in {"BEAR", "DISTRIBUTION", "EXHAUSTION"}
    market_supportive = market_upper in {"BULL", "PREBULL", "EXPANSION", "ACCUMULATION"}

    verified = vwap_dist is not None
    impulse = bool(flags.get("impulse") or flags.get("acceleration"))
    pullback = bool(flags.get("pullback"))
    structure_break = bool(flags.get("structure_break"))
    compression = bool(flags.get("compression"))
    vwap_accept = bool(flags.get("vwap_accept"))
    volume_spike = bool(flags.get("volume_spike"))

    # ------------------------------------------------------------
    # Relational timeframe reads.
    # ------------------------------------------------------------
    five_min_strong = (
        rsi5 >= 58
        and (macd5 > 0 or macd15 > 0 or impulse)
        and (not verified or vwap_label in {"Holding", "Above"})
    )
    one_min_cooling = 35 <= rsi1 < 52
    one_min_reloading = 48 <= rsi1 <= 58 and macd1 >= 0
    one_min_hot = rsi1 >= 72

    reload_watch = (
        verified
        and vwap_label in {"Holding", "Above", "Testing"}
        and five_min_strong
        and one_min_cooling
        and not one_min_hot
        and not market_bad
    )

    reload_ready = (
        verified
        and vwap_label in {"Holding", "Above"}
        and five_min_strong
        and one_min_reloading
        and (pullback or structure_break)
        and not market_bad
    )

    higher_tf_recovery = (
        rsi15 >= 48
        or macd15 >= 0
        or ch1 > 0
    )

    higher_tf_weak = (
        rsi15 < 45
        and macd15 < 0
        and ch1 < 0
    )

    # ------------------------------------------------------------
    # Lifecycle is presentation only.
    # ------------------------------------------------------------
    maturity = 8.0
    if verified:
        maturity += max(0, min(22, (vwap_dist or 0) * 6))
    maturity += max(0, min(20, ch1 * 5))
    maturity += max(0, min(14, (rsi1 - 50) * .55))
    if impulse:
        maturity += 12
    if structure_break:
        maturity += 8
    if pullback:
        maturity -= 7
    if compression:
        maturity -= 9
    if macd1 < 0 and rsi1 > 55:
        maturity += 6
    maturity = max(0, min(100, maturity))

    if maturity < 18:
        phase = "Taxiing"
    elif maturity < 34:
        phase = "Takeoff"
    elif maturity < 55:
        phase = "Climbing"
    elif maturity < 72:
        phase = "Cruising"
    elif maturity < 88:
        phase = "Descending"
    else:
        phase = "Landing"

    reasons = []
    risks = []

    if verified:
        if vwap_label == "Holding":
            reasons.append(f"VWAP is being defended ({vwap_dist:+.2f}%).")
        elif vwap_label == "Above":
            reasons.append(f"Price is {vwap_dist:+.2f}% above VWAP.")
        elif vwap_label == "Testing":
            reasons.append(f"Price is testing VWAP ({vwap_dist:+.2f}%).")
        else:
            risks.append(f"Price is below VWAP ({vwap_dist:+.2f}%).")
    else:
        risks.append("VWAP is not verified for this pair.")

    if five_min_strong:
        reasons.append(f"5m momentum is strong (RSI {rsi5:.0f}).")
    elif rsi5 < 50:
        risks.append(f"5m momentum is weak (RSI {rsi5:.0f}).")

    if reload_watch:
        reasons.append(f"1m has cooled to RSI {rsi1:.0f} while 5m remains strong.")
    elif reload_ready:
        reasons.append(f"1m momentum is reloading (RSI {rsi1:.0f}) into stronger 5m structure.")
    elif one_min_hot:
        risks.append(f"1m RSI is hot at {rsi1:.0f}.")

    if higher_tf_recovery:
        reasons.append("Higher-timeframe structure is stabilizing.")
    if higher_tf_weak:
        risks.append("Higher-timeframe structure is still weak.")

    if ch1 > 0.75:
        reasons.append(f"1H momentum is strong at {ch1:+.2f}%.")
    elif ch1 > 0.15:
        reasons.append(f"1H momentum is positive at {ch1:+.2f}%.")
    elif ch1 < -0.50:
        risks.append(f"1H momentum is weak at {ch1:+.2f}%.")

    if ch24 > 2:
        reasons.append(f"24H trend is supportive at {ch24:+.2f}%.")
    elif ch24 < -2:
        risks.append(f"24H context is weak at {ch24:+.2f}%.")

    if pullback:
        reasons.append("A pullback has formed.")
    elif impulse and not reload_watch:
        risks.append("Impulse is active without a confirmed pullback.")

    if structure_break:
        reasons.append("Structure break is confirmed.")
    elif phase in {"Taxiing", "Takeoff"}:
        risks.append("Structure break is not confirmed yet.")

    if compression:
        reasons.append("Compression is present before expansion.")
    if volume_spike:
        reasons.append("Volume expansion is supporting the move.")

    # ------------------------------------------------------------
    # Dynamic read state.
    # ------------------------------------------------------------
    if reload_ready:
        read_state = "RELOAD READY"
        read_color = "#72ff9a"
    elif reload_watch:
        read_state = "RELOAD WATCH"
        read_color = "#55bfff"
    elif five_min_strong and structure_break and vwap_accept:
        read_state = "CONTINUATION WATCH"
        read_color = "#55bfff"
    elif compression and vwap_accept:
        read_state = "PRESSURE BUILDING"
        read_color = "#ffd85a"
    else:
        read_state = "STANDARD WATCH"
        read_color = "#8498a6"

    extended = (
        timing in {"LATE", "REJECTED"}
        or (verified and (vwap_dist or 0) > 2.2)
        or one_min_hot
        or phase in {"Descending", "Landing"}
    )

    if extended:
        action, color = "SKIP", "#ff6262"
        entry_condition = "Wait for a new base or a clean VWAP reset."
        invalidation = "Current entry window is considered closed."
        tower_note = "This setup is too mature for a fresh entry."
        window_label = "Closed"
    elif reload_ready:
        action, color = "ENTER", "#72ff9a"
        entry_condition = "Enter only if 1m momentum continues turning up while VWAP holds and price confirms above the local trigger."
        invalidation = "Cancel entry if 1m momentum rolls back over or price loses VWAP."
        tower_note = "5m momentum is strong and the 1m reload is rejoining it."
        window_label = "~3–8 min"
    elif reload_watch:
        action, color = "WAIT", "#ffd85a"
        entry_condition = "Wait for 1m RSI to reclaim roughly 50–55 with momentum turning back up while VWAP holds."
        invalidation = "Stand down if VWAP fails or 5m momentum begins rolling over."
        tower_note = "Potential continuation reload: 5m is strong while 1m is cooling."
        window_label = "Reload forming"
    else:
        enter_ready = (
            verified
            and vwap_accept
            and timing in {"ON TIME", "OPTIMAL", "READY SOON"}
            and (pullback or structure_break)
            and rsi1 < 72
            and not market_bad
        )
        close_but_not_ready = (
            verified
            and vwap_label in {"Holding", "Above", "Testing"}
            and timing in {"EARLY", "WATCH", "WAIT", "ON TIME", "READY SOON"}
            and phase in {"Taxiing", "Takeoff"}
        )

        if enter_ready:
            action, color = "ENTER", "#72ff9a"
            entry_condition = "Enter only on confirmed continuation while VWAP remains defended."
            invalidation = "Cancel entry on VWAP loss or immediate breakout failure."
            tower_note = "The radar has a qualified continuation setup."
            window_label = "~4–10 min"
        elif close_but_not_ready:
            action, color = "WAIT", "#ffd85a"
            missing = []
            if not pullback:
                missing.append("pullback")
            if not structure_break:
                missing.append("breakout")
            if not vwap_accept:
                missing.append("VWAP hold")
            if rsi1 < 55:
                missing.append("momentum")
            entry_condition = f"Wait for {', '.join(missing[:3]) if missing else 'one more confirmation'} before entering."
            invalidation = "Stand down if VWAP fails or 1H momentum continues weakening."
            tower_note = "Close to departure, but the radar has not earned an entry yet."
            window_label = "Not open yet"
        elif phase == "Climbing":
            action, color = "WATCH", "#55bfff"
            entry_condition = "Only consider a new entry on a controlled retest back toward VWAP."
            invalidation = "Do not chase if price remains extended from VWAP."
            tower_note = "Momentum is airborne; entry quality now depends on a retest."
            window_label = "Retest only"
        elif phase == "Cruising":
            action, color = "HOLD / SKIP", "#ffd85a"
            entry_condition = "Existing positions manage the trend; new entries wait for reset."
            invalidation = "Fresh entry is invalid without a new base and renewed VWAP control."
            tower_note = "The move is established; reward-to-risk for new entry is shrinking."
            window_label = "Mostly gone"
        else:
            action, color = "WATCH", "#55bfff"
            entry_condition = "No entry until VWAP, momentum, and structure agree."
            invalidation = "Ignore the setup if momentum deteriorates before confirmation."
            tower_note = "Radar sees activity, not yet a trade."
            window_label = "Not open"

    opportunity = 50
    opportunity += 12 if verified and vwap_label in {"Holding", "Above"} else -12
    opportunity += 10 if pullback else 0
    opportunity += 9 if structure_break else 0
    opportunity += 8 if compression else 0
    opportunity += 8 if reload_watch else 0
    opportunity += 12 if reload_ready else 0
    opportunity += 6 if higher_tf_recovery else -7 if higher_tf_weak else 0
    opportunity += 5 if ch24 > 0 else -5 if ch24 < 0 else 0
    opportunity -= 18 if phase in {"Cruising", "Descending"} else 30 if phase == "Landing" else 0
    opportunity = max(0, min(95, opportunity))

    if action == "WAIT":
        opportunity = min(opportunity, 84)
    elif action == "WATCH":
        opportunity = min(opportunity, 72)
    elif action == "HOLD / SKIP":
        opportunity = min(opportunity, 48)
    elif action == "SKIP":
        opportunity = min(opportunity, 25)

    briefing_reasons = reasons[:4]
    briefing_risks = risks[:3]
    reason = briefing_reasons[0] if briefing_reasons else (
        briefing_risks[0] if briefing_risks else "Radar conditions are mixed."
    )

    return {
        "phase": phase,
        "progress": int(round(maturity)),
        "remaining": int(round(opportunity)),
        "window": window_label,
        "action": action,
        "color": color,
        "reason": reason,
        "reasons": briefing_reasons,
        "risks": briefing_risks,
        "entry_condition": entry_condition,
        "invalidation": invalidation,
        "tower_note": tower_note,
        "vwap": vwap_label,
        "vwap_dist": vwap_dist,
        "change_1h": ch1,
        "change_24h": ch24,
        "age": age,
        "sector": sector,
        "rsi_1m": rsi1,
        "rsi_5m": rsi5,
        "rsi_15m": rsi15,
        "timing": timing,
        "read_state": read_state,
        "read_color": read_color,
    }

def build_flights(state, market, generated_at):
    board = ((state or {}).get("billboard", {}) or {}).get("one_hour", []) or []
    setups = (state or {}).get("top_setups", []) or []
    board_map = {str(x.get("pair", "")).upper(): x for x in board}
    flights, seen = [], set()

    for setup in setups:
        pair = str(setup.get("pair", "UNKNOWN"))
        merged = dict(board_map.get(pair.upper(), {}))
        merged.update(setup)
        m = atc_metrics(merged, market, generated_at)
        flights.append({"pair": pair, "setup": merged, **m, "verified": m["vwap_dist"] is not None})
        seen.add(pair.upper())

    for row in board:
        pair = str(row.get("pair", "UNKNOWN"))
        if pair.upper() in seen:
            continue
        m = atc_metrics(row, market, generated_at)
        flights.append({"pair": pair, "setup": dict(row), **m, "verified": False})

    action_order = {"ENTER":0,"WAIT":1,"WATCH":2,"HOLD / SKIP":3,"SKIP":4}
    flights.sort(key=lambda x: (action_order.get(x["action"], 9), -x["remaining"], -x["change_1h"]))
    return flights


def sector_summary(flights):
    buckets = {}
    for f in flights:
        sector = f["sector"]
        b = buckets.setdefault(sector, {"moves": [], "departures": 0, "landings": 0, "count": 0})
        b["moves"].append(f["change_1h"])
        b["count"] += 1
        if f["phase"] in {"Taxiing", "Takeoff", "Climbing"}:
            b["departures"] += 1
        if f["phase"] in {"Descending", "Landing"}:
            b["landings"] += 1

    rows = []
    for sector, b in buckets.items():
        avg = sum(b["moves"]) / len(b["moves"]) if b["moves"] else 0
        rows.append({
            "sector": sector, "avg": avg, "count": b["count"],
            "departures": b["departures"], "landings": b["landings"],
        })
    rows.sort(key=lambda x: (x["departures"], x["avg"]), reverse=True)
    return rows


def tower_command(flights):
    enter = [f for f in flights if f["action"] == "ENTER"]
    wait = [f for f in flights if f["action"] == "WAIT"]
    watch = [f for f in flights if f["action"] == "WATCH"]

    if enter:
        f = enter[0]
        return "ENTRY OPEN", "#72ff9a", f"{f['pair']}: {f['entry_condition']}", f
    if wait:
        f = wait[0]
        return "HOLD SHORT", "#ffd85a", f"{f['pair']}: {f['entry_condition']}", f
    if watch:
        f = watch[0]
        return "MONITOR", "#55bfff", f"{f['pair']}: {f['tower_note']}", f
    return "NO DEPARTURES", "#8498a6", "No pair currently has a qualified entry condition.", None


def render_flight_card(f):
    """Compact ATC card: three decision items per pair."""
    setup = f.get("setup", {}) or {}
    market = f.get("market", "") or ""
    low_move, high_move, move_conf = projected_move(setup, market)
    levels = trade_levels(setup, market)

    price = safe_float(setup.get("price"))
    stop_text = levels.get("stop", "—")
    target_text = levels.get("target", "—")
    rr_text = levels.get("rr", "—")

    risk_pct = None
    try:
        stop_num = float(str(stop_text).replace("$", "").replace(",", ""))
        if price > 0 and stop_num > 0:
            risk_pct = abs((price - stop_num) / price * 100.0)
    except Exception:
        risk_pct = None

    potential_text = f"+{low_move:.2f}% to +{high_move:.2f}%"
    risk_text = f"-{risk_pct:.2f}%" if risk_pct is not None else "—"
    action = clean_text(f.get("action", "WATCH"))
    action_color = f.get("color", "#8498a6")
    timing = clean_text(f.get("timing", "WATCH"))
    window = clean_text(f.get("window", "Needs trigger"))
    invalidation = clean_text(
        f.get("invalidation") or "Stand down on VWAP loss / momentum rollover."
    )

    return f"""
<div class="flight-card" style="color:{action_color};">
  <div class="flight-top">
    <div>
      <div class="flight-pair">{clean_text(f.get('pair','UNKNOWN'))}</div>
      <div class="flight-sector">{clean_text(f.get('sector','OTHER'))} sector</div>
    </div>
    <div class="flight-phase">{clean_text(f.get('phase','WATCH'))}</div>
  </div>

  <div class="flight-action">{action}</div>
  <div class="flight-reason">{timing} · {window}</div>

  <div class="flight-data decision-3">
    <div class="data-box">
      <div class="data-k">Potential Move</div>
      <div class="data-v">{potential_text}</div>
      <div class="small">Estimate · {move_conf}% model confidence</div>
    </div>
    <div class="data-box">
      <div class="data-k">Risk / Reward</div>
      <div class="data-v">{risk_text} · {clean_text(rr_text)}</div>
      <div class="small">Target {clean_text(target_text)} · Stop {clean_text(stop_text)}</div>
    </div>
    <div class="data-box">
      <div class="data-k">Invalidation</div>
      <div class="data-v" style="font-size:13px;line-height:1.35;color:#ff8f8f;">{invalidation}</div>
    </div>
  </div>
</div>
"""

def sharpshooter_candidates(flights):
    """Use existing radar timing + structure to identify top sharpshooter options."""
    candidates = []
    for f in flights:
        s = f["setup"]
        flags = s.get("flags", {}) or {}
        timing = str(f.get("timing", "")).upper()
        score = 0
        if f["vwap_dist"] is not None and f["vwap"] in {"Holding", "Above"}:
            score += 2
        if flags.get("pullback"):
            score += 2
        if flags.get("structure_break"):
            score += 2
        if flags.get("compression"):
            score += 1
        if flags.get("acceleration") or flags.get("impulse"):
            score += 1
        if 55 <= safe_float(f.get("rsi_1m", 0)) < 72:
            score += 1
        if timing in {"ON TIME", "OPTIMAL", "READY SOON"}:
            score += 2
        if f["action"] == "ENTER":
            score += 2
        if f["action"] == "SKIP":
            score -= 4
        if score >= 5:
            candidates.append((score, f))
    candidates.sort(key=lambda x: (x[0], x[1]["remaining"]), reverse=True)
    return [f for _, f in candidates[:8]]


def render_live_ticker(flights):
    sharps = sharpshooter_candidates(flights)
    source_rows = sharps if sharps else flights[:8]
    if not source_rows:
        return '<div class="live-tape-wrap"><div class="live-tape-label">LIVE TAPE</div><div class="live-tape-track"><div class="live-tape-inner"><span class="live-tape-item">Waiting for radar traffic...</span></div></div></div>'

    items = []
    for f in source_rows:
        if f in sharps:
            status = "SHARPSHOOTER READY" if f["action"] == "ENTER" else "SHARPSHOOTER WATCH"
            status_color = "#72ff9a" if f["action"] == "ENTER" else "#ffd85a"
        else:
            status = f["action"]
            status_color = f["color"]
        reason = (f.get("reasons") or [f.get("tower_note", "")])[0]
        items.append(
            f'<span class="live-tape-item">'
            f'<span class="status" style="color:{status_color};">{clean_text(status)}</span>'
            f'<b>{clean_text(f["pair"])}</b>'
            f'<span>{clean_text(f.get("read_state", f["phase"]))}</span>'
            f'<span>VWAP {clean_text(f["vwap"])}</span>'
            f'<span>{clean_text(f["window"])}</span>'
            f'<span>{clean_text(reason)}</span>'
            f'</span>'
        )

    # Duplicate contents for seamless marquee loop.
    tape = "".join(items)
    return (
        '<div class="live-tape-wrap">'
        '<div class="live-tape-label">LIVE TAPE</div>'
        '<div class="live-tape-track"><div class="live-tape-inner">'
        + tape + tape +
        '</div></div></div>'
    )


def traffic_events(flights, sectors, updated):
    """Create a compact event feed from current live radar state."""
    events = []
    base_time = str(updated)[11:16] if updated else "--:--"

    sharps = sharpshooter_candidates(flights)
    for f in sharps[:3]:
        events.append((base_time, f"{f['pair']} entered Sharpshooter watch — {f['entry_condition']}"))

    entering = [f for f in flights if f["action"] == "ENTER"]
    for f in entering[:2]:
        events.append((base_time, f"{f['pair']} cleared for entry — {f['window']} window."))

    waiting = [f for f in flights if f["action"] == "WAIT"]
    for f in waiting[:2]:
        events.append((base_time, f"{f['pair']} holding short — {f['entry_condition']}"))

    if sectors:
        leader = sectors[0]
        events.append((base_time, f"{leader['sector']} sector leading traffic with {leader['departures']} departures."))

    landing = [f for f in flights if f["phase"] in {"Descending", "Landing"}]
    for f in landing[:1]:
        events.append((base_time, f"{f['pair']} approaching landing — fresh entry closed."))

    return events[:7]


def render_traffic_feed(flights, sectors, updated):
    events = traffic_events(flights, sectors, updated)
    rows = "".join(
        f'<div class="traffic-row"><div class="traffic-time">{clean_text(t)}</div><div class="traffic-event">{clean_text(e)}</div></div>'
        for t, e in events
    ) or '<div class="traffic-row"><div class="traffic-time">--:--</div><div class="traffic-event">No notable traffic changes yet.</div></div>'
    return f'<div class="traffic-feed"><div class="traffic-title">Tower Traffic Feed</div>{rows}</div>'


COIN_NEWS_NAMES = {
    "BTC":"Bitcoin","XBT":"Bitcoin","ETH":"Ethereum","SOL":"Solana","FET":"Artificial Superintelligence Alliance",
    "TAO":"Bittensor","WLD":"Worldcoin","RENDER":"Render","DOGE":"Dogecoin","SHIB":"Shiba Inu",
    "PEPE":"Pepe crypto","BONK":"Bonk crypto","LINK":"Chainlink","AVAX":"Avalanche crypto",
    "NEAR":"NEAR Protocol","HBAR":"Hedera","XRP":"XRP","ADA":"Cardano","ONDO":"Ondo Finance",
    "TRX":"TRON crypto","LTC":"Litecoin","XMR":"Monero","SUI":"Sui crypto","APT":"Aptos crypto",
}

@st.cache_data(ttl=300, show_spinner=False)
def fetch_pair_news(symbol, limit=2):
    sym = str(symbol).upper().strip()
    name = COIN_NEWS_NAMES.get(sym, sym)
    query = f'{name} crypto OR cryptocurrency'
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"
    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = []
        for item in root.findall(".//item")[:limit]:
            title = clean_text(item.findtext("title") or "")
            link = item.findtext("link") or ""
            pub = clean_text(item.findtext("pubDate") or "")
            source_node = item.find("source")
            source = clean_text(source_node.text if source_node is not None and source_node.text else "")
            if title and link:
                items.append({"symbol":sym,"title":title,"link":link,"pub":pub,"source":source})
        return items
    except Exception:
        return []

def relevant_news_flights(flights, limit_pairs=4):
    chosen, seen = [], set()
    groups = [
        sharpshooter_candidates(flights),
        [f for f in flights if f["action"] == "ENTER"],
        [f for f in flights if f["action"] == "WAIT"],
        [f for f in flights if f["action"] == "WATCH"],
    ]
    for group in groups:
        for f in group:
            symbol = str(f["pair"]).split("/")[0].upper()
            if symbol and symbol not in seen:
                chosen.append(f); seen.add(symbol)
            if len(chosen) >= limit_pairs:
                return chosen
    return chosen

def render_news_rail(selected, limit=4):
    """Right rail: news context only for the pair currently selected in Flight Readout."""
    if not selected:
        return (
            '<aside class="news-rail"><div class="news-title">Pair Intelligence</div>'
            '<div class="news-sub">Select a flight to load pair-specific news.</div></aside>'
        )

    pair = str(selected.get("pair", "UNKNOWN"))
    symbol = pair.split("/")[0].upper()
    action = str(selected.get("action", "WATCH")).upper()
    stories = fetch_pair_news(symbol, limit)

    if not stories:
        body = '<div class="news-sub">No directly related headlines found on this sweep.</div>'
    else:
        parts = []
        for s in stories:
            meta = " · ".join([x for x in [s.get("source"), s.get("pub")] if x])
            parts.append(
                f'<a class="news-item" href="{html.escape(s["link"])}" target="_blank" rel="noopener noreferrer">'
                f'<span class="news-symbol">{clean_text(pair)} · {clean_text(action)}</span>'
                f'<div class="news-headline">{clean_text(s["title"])}</div>'
                f'<div class="news-meta">{clean_text(meta)}</div></a>'
            )
        body = "".join(parts)

    return (
        '<aside class="news-rail">'
        '<div class="news-title">Pair Intelligence</div>'
        f'<div class="news-sub">Current headlines for <b>{clean_text(pair)}</b>. '
        'News supports context; Radar still controls the entry decision.</div>'
        + body +
        '</aside>'
    )



def market_command_metrics(flights, sectors, market):
    """Build current market-wide context from the same radar reads users see."""
    verified = [f for f in flights if f.get("vwap_dist") is not None]
    sample = verified if verified else flights

    if not sample:
        return {
            "buyers":50, "sellers":50, "opportunity":0, "health":0,
            "breadth":0, "momentum":"Quiet", "visibility":"Low",
            "wind":"Neutral", "turbulence":"Low", "strategy":"Stand By",
            "strategy_note":"Not enough live radar data yet.",
        }

    # Buyer control: market structure, not raw trade volume.
    buyer_points = 0.0
    total_points = 0.0
    positive_1h = 0
    actionable = 0
    clean_structure = 0

    for f in sample:
        # VWAP structure
        total_points += 2
        if f.get("vwap") in {"Holding", "Above"}:
            buyer_points += 2
        elif f.get("vwap") == "Testing":
            buyer_points += 1

        # 1H direction
        total_points += 1
        if safe_float(f.get("change_1h")) > 0:
            buyer_points += 1
            positive_1h += 1

        # Short timeframe momentum
        total_points += 2
        r1 = safe_float(f.get("rsi_1m"), 50)
        r5 = safe_float(f.get("rsi_5m"), 50)
        if r5 >= 55:
            buyer_points += 1
        if r1 >= 50:
            buyer_points += 1

        # Current radar read
        total_points += 1
        if f.get("action") in {"ENTER", "WAIT"}:
            buyer_points += 1
            actionable += 1

        if f.get("read_state") in {"RELOAD READY", "RELOAD WATCH", "CONTINUATION WATCH", "PRESSURE BUILDING"}:
            clean_structure += 1

    buyers = int(round((buyer_points / total_points) * 100)) if total_points else 50
    buyers = max(0, min(100, buyers))
    sellers = 100 - buyers

    breadth = int(round((positive_1h / len(sample)) * 100)) if sample else 0

    # Overall opportunity: current actionable quality, not trend direction.
    opp_vals = [
        safe_float(f.get("remaining"))
        for f in sample
        if f.get("action") not in {"SKIP", "HOLD / SKIP"}
    ]
    opportunity = int(round(sum(opp_vals) / len(opp_vals))) if opp_vals else 0
    opportunity = max(0, min(100, opportunity))

    # Health rewards coherent, early structure and penalizes late traffic.
    late_count = sum(1 for f in sample if f.get("phase") in {"Descending", "Landing"})
    structure_pct = clean_structure / len(sample) if sample else 0
    late_pct = late_count / len(sample) if sample else 0
    health = int(round(
        0.36 * buyers
        + 0.24 * breadth
        + 0.25 * opportunity
        + 15 * structure_pct
        - 18 * late_pct
    ))
    health = max(0, min(100, health))

    # Momentum label
    avg_1h = sum(safe_float(f.get("change_1h")) for f in sample) / len(sample)
    if avg_1h >= 0.75 and breadth >= 60:
        momentum = "Rising Fast"
    elif avg_1h > 0.15:
        momentum = "Rising"
    elif avg_1h < -0.75:
        momentum = "Falling Fast"
    elif avg_1h < -0.15:
        momentum = "Falling"
    else:
        momentum = "Mixed"

    # ATC weather translations.
    if health >= 75 and breadth >= 60:
        visibility = "Excellent"
    elif health >= 55:
        visibility = "Good"
    elif health >= 40:
        visibility = "Fair"
    else:
        visibility = "Poor"

    if buyers >= 65:
        wind = "Tailwind"
    elif buyers <= 35:
        wind = "Headwind"
    else:
        wind = "Crosswind"

    # Use spread of 1H moves as a simple turbulence proxy.
    vals = [safe_float(f.get("change_1h")) for f in sample]
    avg = sum(vals) / len(vals)
    variance = sum((x - avg) ** 2 for x in vals) / len(vals)
    spread = variance ** 0.5
    if spread >= 2.0:
        turbulence = "High"
    elif spread >= 0.9:
        turbulence = "Medium"
    else:
        turbulence = "Low"

    # Recommended operating style.
    market_upper = str(market).upper()
    reload_count = sum(1 for f in sample if f.get("read_state") in {"RELOAD WATCH", "RELOAD READY"})
    enter_count = sum(1 for f in sample if f.get("action") == "ENTER")

    if market_upper in {"BEAR", "DISTRIBUTION", "EXHAUSTION"} or buyers < 38:
        strategy = "Defensive"
        strategy_note = "Protect capital. Avoid forcing long momentum entries."
    elif reload_count >= 2 and buyers >= 50:
        strategy = "Sharpshooter Reloads"
        strategy_note = "Favor 1m reloads that rejoin stronger 5m structure."
    elif enter_count >= 2 and buyers >= 60 and opportunity >= 60:
        strategy = "Continuation"
        strategy_note = "Conditions support selective confirmed momentum entries."
    elif opportunity < 40:
        strategy = "Wait for Reset"
        strategy_note = "Control may exist, but clean entry opportunity is limited."
    else:
        strategy = "Selective"
        strategy_note = "Trade only the strongest confirmed departures."

    return {
        "buyers":buyers, "sellers":sellers, "opportunity":opportunity,
        "health":health, "breadth":breadth, "momentum":momentum,
        "visibility":visibility, "wind":wind, "turbulence":turbulence,
        "strategy":strategy, "strategy_note":strategy_note,
    }



def _feed_time_for_flight(f, fallback=""):
    setup = f.get("setup", {}) or {}
    for key in ("signal_time", "first_seen", "created_at", "detected_at"):
        value = setup.get(key)
        if value:
            txt = str(value)
            if "T" in txt and len(txt) >= 16:
                return txt[11:16]
            if " " in txt and len(txt) >= 16:
                return txt[11:16]
    txt = str(fallback or "")
    return txt[11:16] if len(txt) >= 16 else "--:--"


def render_aplus_live_feed(flights, updated="", limit=10):
    """Left rail: compact website mirror of the scanner/Discord decision stream."""
    if not flights:
        return (
            '<aside class="market-command-rail">'
            '<div class="market-command-title">A+ Live Feed</div>'
            '<div class="control-sub">Waiting for scanner events...</div>'
            '</aside>'
        )

    sharps = set(id(x) for x in sharpshooter_candidates(flights))
    rows = []

    for rank, f in enumerate(flights[:limit], start=1):
        setup = f.get("setup", {}) or {}
        action = str(f.get("action", "WATCH")).upper()
        read_state = str(f.get("read_state") or f.get("phase") or "WATCH").upper()
        timing = str(f.get("timing") or "WATCH").upper()
        trigger = int(safe_float(setup.get("trigger_score", 0)))
        trade = int(safe_float(setup.get("trade_score", 0)))
        streak = int(safe_float(setup.get("board_cycles", setup.get("streak", 0))))
        hits = int(safe_float(setup.get("watch_hits", setup.get("hits_last_2h", 0))))

        if id(f) in sharps:
            status = "SHARPSHOOTER READY" if action == "ENTER" else "SHARPSHOOTER WATCH"
        else:
            status = action

        status_color = (
            "#72ff9a" if action == "ENTER"
            else "#ffd85a" if action in {"WAIT", "WATCH"}
            else "#ff6262"
        )

        score_bits = []
        if trigger:
            score_bits.append(f"T{trigger}")
        if trade:
            score_bits.append(f"TR{trade}")
        if streak:
            score_bits.append(f"{streak} cycles")
        if hits:
            score_bits.append(f"{hits} hits")
        score_text = " · ".join(score_bits) if score_bits else clean_text(f.get("window", ""))

        rows.append(
            '<div class="aplus-feed-row">'
            '<div class="aplus-feed-top">'
            f'<span class="aplus-feed-pair">#{rank} {clean_text(f.get("pair","UNKNOWN"))}</span>'
            f'<span class="aplus-feed-time">{clean_text(_feed_time_for_flight(f, updated))}</span>'
            '</div>'
            f'<div class="aplus-feed-status" style="color:{status_color};">{clean_text(status)}</div>'
            f'<div class="aplus-feed-read">{clean_text(read_state)}</div>'
            f'<div class="aplus-feed-meta">{clean_text(timing)} · {clean_text(score_text)}</div>'
            '</div>'
        )

    return (
        '<aside class="market-command-rail">'
        '<div class="market-command-title">A+ Live Feed</div>'
        '<div class="news-sub">Same scanner decisions in-browser — no Discord tab required.</div>'
        + "".join(rows) +
        '</aside>'
    )


def render_market_command_rail(flights, sectors, market):
    m = market_command_metrics(flights, sectors, market)

    buyer_color = "#72ff9a" if m["buyers"] >= 55 else "#ffd85a" if m["buyers"] >= 45 else "#ff6262"
    opp_color = "#72ff9a" if m["opportunity"] >= 65 else "#ffd85a" if m["opportunity"] >= 40 else "#ff6262"
    health_color = "#79e7ff" if m["health"] >= 80 else "#72ff9a" if m["health"] >= 60 else "#ffd85a" if m["health"] >= 40 else "#ff6262"

    flow_html = ""
    for s in sectors[:4]:
        if s["avg"] > 0.5:
            arrow, color = "▲▲", "#72ff9a"
        elif s["avg"] > 0:
            arrow, color = "▲", "#72ff9a"
        elif s["avg"] < -0.5:
            arrow, color = "▼▼", "#ff6262"
        elif s["avg"] < 0:
            arrow, color = "▼", "#ff6262"
        else:
            arrow, color = "→", "#8498a6"
        flow_html += (
            f'<div class="flow-row"><span>{clean_text(s["sector"])}</span>'
            f'<span style="color:{color};font-weight:1000;">{arrow} {s["avg"]:+.2f}%</span></div>'
        )

    return f"""
<aside class="market-command-rail">
  <div class="market-command-title">Market Command Center</div>

  <div class="control-block">
    <div class="control-label"><span>Airspace Control</span><span style="color:{buyer_color};">{m['buyers']}% Buyers</span></div>
    <div class="control-track">
      <div class="control-fill" style="width:{m['buyers']}%;background:{buyer_color};"></div>
    </div>
    <div class="balance-row"><span style="color:#ff6262;">Sellers {m['sellers']}%</span><span style="color:#72ff9a;">Buyers {m['buyers']}%</span></div>
    <div class="control-sub">Weighted from VWAP control, 1H direction, RSI structure, and live radar state.</div>
  </div>

  <div class="control-block">
    <div class="control-label"><span>Overall Opportunity</span><span>{m['opportunity']}%</span></div>
    <div class="control-track"><div class="control-fill" style="width:{m['opportunity']}%;background:{opp_color};"></div></div>
    <div class="control-sub">How much clean entry quality remains across active traffic.</div>
  </div>

  <div class="control-block">
    <div class="control-label"><span>Radar Health</span><span style="color:{health_color};">{m['health']}/100</span></div>
    <div class="control-track"><div class="control-fill" style="width:{m['health']}%;background:{health_color};"></div></div>
    <div class="control-sub">Combines breadth, buyer control, opportunity, and lifecycle quality.</div>
  </div>

  <div class="control-block">
    <div class="control-label"><span>Market Weather</span><span>{clean_text(m['momentum'])}</span></div>
    <div class="weather-grid">
      <div class="weather-cell"><div class="weather-k">Visibility</div><div class="weather-v">{clean_text(m['visibility'])}</div></div>
      <div class="weather-cell"><div class="weather-k">Wind</div><div class="weather-v">{clean_text(m['wind'])}</div></div>
      <div class="weather-cell"><div class="weather-k">Turbulence</div><div class="weather-v">{clean_text(m['turbulence'])}</div></div>
      <div class="weather-cell"><div class="weather-k">Breadth</div><div class="weather-v">{m['breadth']}%</div></div>
    </div>
  </div>

  <div class="control-block">
    <div class="control-label"><span>Sector Flow</span><span>1H</span></div>
    {flow_html or '<div class="control-sub">No sector traffic yet.</div>'}
  </div>

  <div class="control-block">
    <div class="control-label"><span>Recommended Mode</span></div>
    <div class="strategy-box">
      <div class="strategy-name">{clean_text(m['strategy'])}</div>
      <div class="strategy-note">{clean_text(m['strategy_note'])}</div>
    </div>
  </div>
</aside>
"""



with st.sidebar:
    st.markdown("### Tower Controls")
    auto = st.toggle("Auto sync", value=True, key="atc_auto")
    broadcast_mode = st.toggle("Broadcast Mode", value=False, key="atc_broadcast")
    speed = st.select_slider("Scroll speed", ["Slow","Normal","Fast"], value="Normal", disabled=not broadcast_mode)
    manual = st.button("Sync Radar", key="atc_manual")
    clear_cache = st.button("Clear Cache", key="atc_clear")
    st.caption("ATC lifecycle · Entry windows · 24H context · Sector traffic")

if manual or clear_cache:
    st.cache_data.clear()
    st.rerun()

if auto and not broadcast_mode:
    st.markdown("<script>setTimeout(function(){window.location.reload();},20000);</script>", unsafe_allow_html=True)

if broadcast_mode:
    px = {"Slow":.35,"Normal":.7,"Fast":1.15}.get(speed,.7)
    st.markdown('<div class="broadcast-badge">Live ATC Feed</div>', unsafe_allow_html=True)
    st.markdown(f"""
<script>
(function(){{
 const d=window.parent.document; d.body.classList.add("broadcast-mode");
 let dir=parseInt(sessionStorage.getItem("atcDir")||"1");
 let y=parseFloat(sessionStorage.getItem("atcY")||"0");
 let pause=0; const speed={px};
 window.parent.scrollTo(0,y);
 function save(){{sessionStorage.setItem("atcY",String(window.parent.scrollY));sessionStorage.setItem("atcDir",String(dir));}}
 function step(){{
   const maxY=Math.max(0,d.documentElement.scrollHeight-window.parent.innerHeight-8), now=Date.now();
   if(now>=pause){{
     let n=window.parent.scrollY+speed*dir;
     if(dir>0&&n>=maxY){{n=maxY;dir=-1;pause=now+4000;}}
     if(dir<0&&n<=0){{n=0;dir=1;pause=now+4000;}}
     window.parent.scrollTo(0,n); save();
   }}
   requestAnimationFrame(step);
 }}
 requestAnimationFrame(step);
 setTimeout(function(){{save();window.parent.location.reload();}},20000);
}})();
</script>
""", unsafe_allow_html=True)

state, ok, source = load_state()
market = state.get("market_state") or state.get("regime_name") or "WAITING"
updated = state.get("generated_at") or state.get("timestamp") or ""
cycle = state.get("cycle_number", state.get("cycle", 0))
active = int(state.get("active_pairs", 0) or 0)

flights = build_flights(state, market, updated)

# ============================================================
# A+ RADAR 8-PHASE ENGINE PIPELINE
# ============================================================

engine_pairs = flights

# Phase 1 — Market Engine
engine_market = build_market_state(
    engine_pairs,
    market,
)

# Phase 2 — Pair Engine
engine_pairs_ranked = build_pair_rankings(
    engine_pairs,
    engine_market,
)

# Phase 3 — Entry Engine
engine_entries = evaluate_entries(
    engine_pairs_ranked.get("watchlist")
    or engine_pairs_ranked.get("top_5")
    or [],
    engine_market,
)

# Phase 4 — Replay Engine
replay_engine = ReplayEngine(
    "radar_replay.db"
)

# Phase 5 — Analyst Engine
engine_analysis = []

ranked_lookup = {
    row["pair"]: row
    for row in engine_pairs_ranked.get(
        "ranked_pairs",
        [],
    )
}

for entry in engine_entries.get("evaluated", []):
    pair_row = ranked_lookup.get(
        entry.get("pair"),
        {"pair": entry.get("pair")},
    )

    engine_analysis.append(
        analyze_setup(
            pair_row,
            entry,
            engine_market,
        )
    )

# Phase 6 — Confidence Calibration
confidence_calibrator = ConfidenceCalibrator(
    replay_engine
)

# Phase 7 — Radar AI
radar_ai_engine = RadarAI(
    market_builder=build_market_state,
    pair_builder=build_pair_rankings,
    entry_builder=evaluate_entries,
    analyst=analyze_setup,
    calibrator=confidence_calibrator,
    replay=replay_engine,
)

radar_ai_state = radar_ai_engine.run(
    engine_pairs,
    market,
)



# Phase 8 — Learning Engine
learning_engine = LearningEngine(
    replay_engine
)

learning_report = learning_engine.build_learning_report()


st.sidebar.write(
    "1. Market:",
    engine_market.get("market_mode")
)

st.sidebar.write(
    "2. Pair:",
    len(engine_pairs_ranked.get("ranked_pairs", [])),
    "ranked"
)

st.sidebar.write(
    "3. Entry:",
    engine_entries.get("summary", {}).get("enter_count", 0),
    "ENTER"
)

st.sidebar.write(
    "4. Replay:",
    len(replay_engine.open_signals()),
    "open"
)

st.sidebar.write(
    "5. Analyst:",
    len(engine_analysis),
    "analyses"
)

st.sidebar.write(
    "6. Confidence:",
    "ACTIVE" if confidence_calibrator else "OFF"
)

st.sidebar.write(
    "7. Radar AI:",
    radar_ai_state.get("command_brief", {}).get("best_pair")
    or "No setup"
)

st.sidebar.write(
    "8. Learning:",
    learning_report.get("summary", {}).get("trades_analyzed", 0),
    "trades"
)

print(
    "✅ Radar 8-phase pipeline active:",
    engine_market.get("market_mode"),
    radar_ai_state.get(
        "command_brief",
        {},
    ).get("best_pair"),
)

sectors = sector_summary(flights)
command, command_color, command_copy, primary = tower_command(flights)

departures = [f for f in flights if f["phase"] in {"Taxiing","Takeoff"}]
climbing = [f for f in flights if f["phase"] == "Climbing"]
cruising = [f for f in flights if f["phase"] == "Cruising"]
landing = [f for f in flights if f["phase"] in {"Descending","Landing"}]

st.markdown(render_aplus_live_feed(flights, updated, limit=10), unsafe_allow_html=True)
st.markdown('<div class="atc-shell">', unsafe_allow_html=True)

st.markdown(f"""
<div class="atc-top">
  <div class="atc-brand">
    <div class="atc-logo">A+</div>
    <div><div class="atc-name">MOMENTUM ATC</div><div class="atc-sub">Live Opportunity Control Tower</div></div>
  </div>
  <div class="atc-sync">RADAR SYNCED · CYCLE {cycle}</div>
</div>

{render_live_ticker(flights)}

<div class="tower-grid">
  <div class="tower-command">
    <div class="kicker">Tower Command</div>
    <div class="command-action" style="color:{command_color};">{clean_text(command)}</div>
    <div class="command-copy">{clean_text(command_copy)}</div>
    <div class="command-target">
      <div class="command-cell"><div class="command-k">Priority Flight</div><div class="command-v">{clean_text(primary['pair']) if primary else 'NONE'}</div></div>
      <div class="command-cell"><div class="command-k">Flight Phase</div><div class="command-v">{clean_text(primary['phase']) if primary else 'Grounded'}</div></div>
      <div class="command-cell"><div class="command-k">Entry Window</div><div class="command-v">{clean_text(primary['window']) if primary else '—'}</div></div>
    </div>
  </div>
  <div class="airspace">
    <div class="kicker">Airspace Status</div>
    <div class="airspace-row"><div class="airspace-k">Market</div><div class="airspace-v">{clean_text(str(market).title())}</div></div>
    <div class="airspace-row"><div class="airspace-k">Departures</div><div class="airspace-v">{len(departures)}</div></div>
    <div class="airspace-row"><div class="airspace-k">Climbing</div><div class="airspace-v">{len(climbing)}</div></div>
    <div class="airspace-row"><div class="airspace-k">Cruising</div><div class="airspace-v">{len(cruising)}</div></div>
    <div class="airspace-row"><div class="airspace-k">Landing</div><div class="airspace-v">{len(landing)}</div></div>
    <div class="airspace-row"><div class="airspace-k">Pairs Scanned</div><div class="airspace-v">{active}</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(render_traffic_feed(flights, sectors, updated), unsafe_allow_html=True)

st.markdown('<div class="section-head"><div class="section-title">Sector Traffic</div><div class="section-note">Where departures are concentrating</div></div>', unsafe_allow_html=True)
if sectors:
    sector_html = []
    for s in sectors[:5]:
        c = "#72ff9a" if s["avg"] > .5 else "#ffd85a" if s["avg"] >= 0 else "#ff6262"
        sector_html.append(f"""
<div class="sector-card">
  <div class="sector-name">{clean_text(s['sector'])}</div>
  <div class="sector-read" style="color:{c};">{s['avg']:+.2f}%</div>
  <div class="sector-sub">{s['departures']} departing · {s['landings']} landing</div>
</div>""")
    st.markdown('<div class="sector-strip">' + "".join(sector_html) + '</div>', unsafe_allow_html=True)

st.markdown('<div class="section-head"><div class="section-title">Departures Board</div><div class="section-note">Pairs closest to a qualified entry</div></div>', unsafe_allow_html=True)
departure_board = [f for f in flights if f["action"] in {"ENTER","WAIT"}][:6]
if departure_board:
    st.markdown('<div class="flight-grid">' + "".join(render_flight_card(f) for f in departure_board) + '</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="empty">No qualified departures right now.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-head"><div class="section-title">Airborne Traffic</div><div class="section-note">Momentum active — new entry requires a retest</div></div>', unsafe_allow_html=True)
airborne = [f for f in flights if f["action"] in {"WATCH","HOLD / SKIP"}][:6]
if airborne:
    st.markdown('<div class="flight-grid">' + "".join(render_flight_card(f) for f in airborne) + '</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="empty">No airborne opportunities currently tracked.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-head"><div class="section-title">Approach & Landing</div><div class="section-note">Momentum fading — fresh entry is closed</div></div>', unsafe_allow_html=True)
if landing:
    st.markdown('<div class="flight-grid">' + "".join(render_flight_card(f) for f in landing[:6]) + '</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="empty">No flights currently approaching landing.</div>', unsafe_allow_html=True)

st.markdown('<div class="section-head"><div class="section-title">Flight Readout</div><div class="section-note">Pair-specific radar briefing</div></div>', unsafe_allow_html=True)
if flights:
    if broadcast_mode:
        selected = flights[int(time.time() // 20) % len(flights)]
    else:
        selected_pair = st.selectbox("Flight", [f["pair"] for f in flights], key="atc_flight")
        selected = next(f for f in flights if f["pair"] == selected_pair)

    st.markdown(render_news_rail(selected), unsafe_allow_html=True)

    checks = [
        ("VWAP verified", selected["vwap_dist"] is not None),
        ("Radar timing actionable", selected.get("timing") in {"ON TIME", "OPTIMAL", "READY SOON"}),
        ("Entry window open", selected["action"] == "ENTER"),
        ("Fresh entry not extended", selected["action"] not in {"SKIP", "HOLD / SKIP"}),
    ]
    check_html = "".join(
        f'<div class="check" style="color:{"#72ff9a" if ok else "#ffd85a"};">{"✓" if ok else "□"} {clean_text(label)}</div>'
        for label, ok in checks
    )
    st.markdown(f"""
<div class="detail">
  <div class="detail-grid">
    <div class="detail-left">
      <div class="kicker">Flight</div>
      <div class="detail-pair">{clean_text(selected['pair'])}</div>
      <div class="detail-action" style="color:{selected['color']};">{clean_text(selected['action'])}</div>
      <div class="flight-sector">{clean_text(selected['sector'])} · {clean_text(selected['phase'])}</div>
    </div>
    <div>
      <div class="kicker">Action Checklist</div>
      <div class="detail-checks" style="margin-top:10px;">{check_html}</div>
      <div class="next-step"><b>TOWER READ:</b> {clean_text(selected['tower_note'])}</div>
      <div class="next-step"><b>BEST ENTRY:</b> {clean_text(selected['entry_condition'])}</div>
      <div class="next-step"><b>INVALIDATION:</b> {clean_text(selected['invalidation'])}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f'<div class="section-note" style="margin-top:18px;">Source: {clean_text(source)} · Estimated windows are model guidance, not guarantees.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
