import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
import streamlit as st
import plotly.graph_objects as go

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
<style>
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
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


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

        cfg = settings()

    raw_url = "https://raw.githubusercontent.com/Trans3/a-plus-live-radar/main/radar_state.json"
    st.caption("Radar Engine v2.2 • PREBULL Framework")
    try:
        r = requests.get(
            raw_url,
            headers={"User-Agent": "a-plus-radar-app"},
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
    local_path = Path(DEFAULT_GITHUB_PERFORMANCE_PATH)

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

    raw_url = "https://raw.githubusercontent.com/Trans3/a-plus-live-radar/main/radar_performance.json"
    st.caption("Radar Engine v2.2 • PREBULL Framework")
    try:
        r = requests.get(
            raw_url,
            headers={"User-Agent": "a-plus-radar-app"},
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
    st.markdown(f"""
    <div class="sticky-upgrade">
    <div>
        <div style="font-weight:900;color:#FFD93D;">
            PREBULL Momentum Detected
        </div>
        <div class="small">
            Unlock execution reasoning, invalidations, and analytics engine.
        </div>
    </div>

    <div class="sticky-btn">
        Upgrade Access
    </div>
</div>
       
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
      <div class="perf-card"><div class="perf-k">Hit +1%</div><div class="perf-v">{hit1_rate:.f}%</div><div class="perf-sub">Since tracking started</div></div>
      <div class="perf-card"><div class="perf-k">Hit +2%</div><div class="perf-v">{hit2_rate:.f}%</div><div class="perf-sub">Momentum target test</div></div>
      <div class="perf-card"><div class="perf-k">Avg Max Move</div><div class="perf-v">{avg_max:+.f}%</div><div class="perf-sub">Observed after alert</div></div>
      <div class="perf-card"><div class="perf-k">Best Signal</div><div class="perf-v" style="font-size:22px;">{best_pair}</div><div class="perf-sub">{best_gain:+.f}% max</div></div>
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
    cr = setup.get("chart_read", {}) or {}
    timing = cr.get("timing", setup.get("entry_readiness_label", "WATCH"))
    b = bullets_for(setup)
    bullet_html = "".join([f"<div>{x}</div>" for x in b])
    t = int(setup.get("trigger_score", 0) or 0)
    tr = int(setup.get("trade_score", 0) or 0)
    c = int(setup.get("confidence", 0) or 0)
    env_score = int(setup.get("environment_score", setup.get("composite_score", t)) or 0)
    env_tier = setup.get("environment_tier", "UNKNOWN") or "UNKNOWN"
    env_adj_html = environment_adjustments_html(setup)
    low, high, pconf = projected_move(setup, market)
    levels = trade_levels(setup, market)
    clock = execution_clock(setup, market, state_generated_at)
    stages, current = setup_stages(setup)
    stage_html = ""
    for i, (name, passed) in enumerate(stages):
        cls = "stage stage-on" if passed else "stage"
        if i == current: cls += " stage-current"
        stage_html += f"<span class='{cls}'>{name}</span>"
        if i < len(stages)-1: stage_html += "<span class='arrow'>→</span>"
    pos = timing_position(timing)
    st.markdown(f"""
    <div class="setup-card {accent_class}">
      <div class="setup-top">
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
          <div class="score-line"><div class="score-label">Environment<br/>Score</div><div class="score-num score-trigger">{env_score}</div></div>
        </div>
        <div class="decision-box">
          <div class="decision-head">Expected Move Range</div>
          <div class="projected">+{low}% to +{high}%</div>
          <div class="small">Model confidence: {pconf}% | range estimate, not certainty</div>
          <div class="env-box">
            <div class="env-k">Environment Weight</div>
            <div class="env-v">{env_score}/100 <span class="env-tier">{env_tier}</span></div>
            <div class="env-adj">{env_adj_html}</div>
          </div>
          <div class="riskgrid">
            <div class="riskcell"><span>Entry Zone</span><b>{levels['entry_low']} | {levels['entry_high']}</b></div>
            <div class="riskcell"><span>Target</span><b class="green">{levels['target']}</b></div>
            <div class="riskcell"><span>Invalidation</span><b class="red">{levels['stop']}</b></div>
          </div>
          <div class="exec-clock">
            <div class="exec-k">Execution Clock</div>
            <div class="exec-v {clock['class']}">{clock['status']} <span class="countdown-pill">{clock['window']}</span></div>
            <div class="exec-sub">{clock['message']}</div>
          </div>
        </div>
      </div>
      <div class="tool-grid">
        <div class="tool-panel">
          <div class="tool-title">Decision Map: Price vs VWAP / Target / Invalidation</div>
    """, unsafe_allow_html=True)
    st.plotly_chart(decision_chart(setup, market, accent), width="stretch", config={"displayModeBar": False})
    st.markdown(f"""
        </div>
        <div class="tool-panel">
          <div class="tool-title">Veteran Read</div>
          <div class="stage-row">{stage_html}</div>
          <div class="tool-title" style="margin-top:14px;color:{timing_color(timing)};">Timing Gauge</div>
          <div class="timing-track"><div class="timing-marker" style="left:{pos}%;background:{timing_color(timing)};box-shadow:0 0 12px {timing_color(timing)};"></div></div>
          <div class="timing-labels"><span>Early</span><span>On Time</span><span>Late</span></div>
          <div class="next-box" style="margin-top:12px;"><b>Simple answer:</b> <span class="{clock['class']}">{clock['status']}</span> | {action_text(setup, timing)}</div>
          <div class="next-box" style="margin-top:8px;"><b>Why:</b> {why_text(setup)}</div>
          <div class="next-box fail" style="margin-top:8px;">Fail condition: VWAP loss / lower low invalidates the idea.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def fires(n):
    try: n = int(n)
    except Exception: n = 0
    return "🔥" * min(max(n,0),3) if n else "—"


with st.sidebar:
    st.markdown("### Radar Controls")
    auto = st.toggle("Auto refresh", value=True, key="auto_refresh_toggle_v22")
    refresh = 20  # fixed refresh interval; no user slider to avoid duplicate Streamlit widget IDs
    manual = st.button("Refresh Now", key="sidebar_refresh_v22")
    reset_perf = st.button("Clear app cache", key="clear_app_cache_v22")
    st.caption("Scanner → GitHub JSON → Streamlit decision report")

    st.markdown(
    '<div style="color:#FFD93D;font-weight:1000;text-transform:uppercase;margin:10px 0 6px;">Membership View</div>',
    unsafe_allow_html=True
)

membership = st.radio(
    "Membership View",
    ["Free", "Basic", "Premium", "Pro Analytics"],
    horizontal=True,
    label_visibility="collapsed",
    key="membership_view_main_v1",
)
cta_text = "Get Full Radar"
st.markdown("""
<div class="proof-panel" style="margin:10px 0 18px;">
  <div class="proof-title">How To Use</div>

  <div class="read-row">
    <div class="read-key" style="color:#78FF2E;">1</div>
    <div class="read-desc">Check Market State</div>
  </div>

  <div class="read-row">
    <div class="read-key" style="color:#FFD93D;">2</div>
    <div class="read-desc">Watch Top Setups</div>
  </div>

  <div class="read-row">
    <div class="read-key" style="color:#35A7FF;">3</div>
    <div class="read-desc">Enter only during EXECUTE ZONE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# Prominent refresh control for the main page (sidebar can stay collapsed).
st.markdown('<div class="refresh-row"><span>Live data source refreshes from GitHub JSON.</span></div>', unsafe_allow_html=True)
top_left, top_mid, top_right = st.columns([6, 1.5, 1.5])
with top_right:
    top_refresh = st.button("↻ Refresh Radar", key="top_refresh_v22")

if reset_perf:
    st.cache_data.clear()
    st.rerun()
if manual or top_refresh:
    st.cache_data.clear()
    st.rerun()
if auto:
    st.markdown(f"<script>setTimeout(function(){{window.location.reload();}}, {refresh*1000});</script>", unsafe_allow_html=True)

state, ok, source = load_state()

# Expose the active source so stale local/GitHub issues are obvious on the site.
st.caption(f"Data source: {source}")

market = state.get("market_state") or state.get("regime_name") or "WAITING"
color = state_color(market)
btc = state.get("btc", {}) or {}
setups = state.get("top_setups", []) or []
sector_counts = state.get("sector_counts", {}) or {}
state_counts = state.get("state_counts", {}) or {}
updated = state.get("generated_at") or state.get("timestamp") or ""
cycle = state.get("cycle_number", state.get("cycle", 0))
active = state.get("active_pairs", 0)
perf_state, perf_ok, perf_source = load_performance()

# Decision banner values
best = setups[0] if setups else {}
best_coin = best.get("pair", "None yet")
best_timing = (best.get("chart_read", {}) or {}).get("timing", "WAIT") if best else "WAIT"
global_clock = global_execution_decision(setups, market, updated)
action = global_clock.get("status", "WAIT")
action_color = "#78FF2E" if global_clock.get("class") == "exec-now" else "#FFD93D" if global_clock.get("class") in {"exec-wait", "exec-watch"} else "#FF4D4D"

st.markdown('<div class="report-shell">', unsafe_allow_html=True)
st.markdown(f"""
<div class="header">
  <div class="header-left">
    <div class="brand"><div class="logo">A+</div><div><div class="title"><span>A+</span> DECISION RADAR</div><div class="subtitle">Momentum execution radar built to reduce emotional trading and identify high-probability continuation setups.</div></div></div>
    <div class="small">
Built using live Kraken market data, momentum structure analysis, VWAP positioning, and execution-based filtering.
</div>
    <div class="meta"><div>📅 <b>{str(updated)[:10] or 'waiting'}</b></div><div>🕒 <b>{str(updated)[11:19] or '--:--:--'}</b></div><div>🔄 Cycle: <b>{cycle}</b></div><div>🎯 Active Pairs: <b>{active}</b></div></div>
<div style="margin-top:18px;display:flex;gap:12px;flex-wrap:wrap;">
  <div class="cta-main">⚡ LIVE RADAR ACTIVE</div>
  <div class="cta-secondary">Upgrade For Full Execution Engine</div>
</div>  
  </div>
  <div class="state-box">
    <div class="state-label">Market State</div>
    <div class="state-value" style="color:{color};">{market}</div>
    <div class="state-sub" style="color:{color};">{'Market warming up' if market=='PREBULL' else 'Trade-ready conditions' if market=='BULL' else 'Weak tape' if market=='BEAR' else 'Waiting for data'}</div>
    <div class="state-reason">{btc.get('reason','Start scanner')}</div>
  </div>
</div>
<div class="decision-banner">
  <div class="decision-tile"><div class="tile-k">What To Do Now</div><div class="tile-v" style="color:{action_color};">{action}</div><div class="tile-sub">{global_clock.get('message','Wait for clean timing.')}</div></div>
  <div class="decision-tile"><div class="tile-k">Execution Window</div><div class="tile-v" style="color:{action_color};">{global_clock.get('window','Needs trigger')}</div><div class="tile-sub">Best setup: <b>{best_coin}</b> · Timing: <b style="color:{timing_color(best_timing)};">{best_timing}</b></div></div>
  <div class="decision-tile"><div class="tile-k">Too Late Rule</div><div class="tile-v" style="color:#FF4D4D;">Skip Chases</div><div class="tile-sub">Too far from VWAP, RSI hot, or no pullback = no entry.</div></div>
</div>
""", unsafe_allow_html=True)

if not ok:
    st.markdown(f'<div class="notice">Data source: {source}</div>', unsafe_allow_html=True)

render_billboard_dashboard(state)

if has_tier(membership, "Premium"):
    st.markdown('<div class="section-title"><span> Top 5 Decision Setups </span></div>', unsafe_allow_html=True)
    if setups:
        for i, setup in enumerate(setups[:TOP_SETUP_LIMIT], start=1):
            render_setup_card(setup, i, market, updated)
    else:
        st.markdown('<div class="notice">No live setups yet. Start the scanner and wait for the next cycle.</div>', unsafe_allow_html=True)
        for i in range(1, TOP_SETUP_LIMIT + 1):
            render_setup_card({"coin":"WAIT", "pair":"WAITING", "tag":"PREBUILD", "trigger_score":0,"trade_score":0,"confidence":0,"chart_read":{"timing":"WAIT","read_30m":"Waiting","read_1h":"Waiting"},"flags":{}}, i, market, updated)
else:
    render_top5_simple(setups, market, updated, membership)

if has_tier(membership, "Pro Analytics"):
    render_performance_dashboard(perf_state, perf_ok, perf_source)
else:
    locked_panel(
        "Proof / Backtesting Analytics",
        "Pro Analytics",
        "Regime, timing, RSI zone, VWAP distance, setup type, sector, hour, and performance tables stay behind the analytics tier.",
    )

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
  <div class="bottom-panel"><div class="panel-title">State Counts</div>{counts_rows}</div>
  <div class="bottom-panel">
    <div class="panel-title">How To Read This</div>
    <div class="read-row"><div class="read-key" style="color:#78FF2E;">Projected</div><div class="read-desc">Estimated move range from volatility, impulse, scores, VWAP, and BTC regime.</div></div>
    <div class="read-row"><div class="read-key" style="color:#FFD93D;">Entry Zone</div><div class="read-desc">Area where risk can be defined. Not a blind buy signal.</div></div>
    <div class="read-row"><div class="read-key" style="color:#FF4D4D;">Invalid</div><div class="read-desc">Where the trade idea is wrong. Respect this first.</div></div>
    <div class="read-row"><div class="read-key" style="color:#35A7FF;">Timing</div><div class="read-desc">EXECUTE ZONE = next few minutes only. WAIT = let setup form. TOO LATE = skip chase.</div></div>
  </div>
</div>
<span class="left">🏆 Built to reduce emotional trading and improve momentum execution discipline.</span>
""", unsafe_allow_html=True)
