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
    """Protect against old Streamlit secrets/env using Trans3 instead of Trans3o."""
    repo = (repo or DEFAULT_GITHUB_RADAR_REPO).strip()
    if repo == "Trans3/a-plus-live-radar":
        return "Trans3o/a-plus-live-radar"
    return repo


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
    cfg = settings()
    prefer_local = secret_or_env("PREFER_LOCAL_STATE", "0") == "1"
    local_path = Path(cfg.get("performance_path", DEFAULT_GITHUB_PERFORMANCE_PATH))

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

    url = f"https://api.github.com/repos/{cfg['repo']}/contents/{cfg.get('performance_path', DEFAULT_GITHUB_PERFORMANCE_PATH)}"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "a-plus-radar-app", "X-GitHub-Api-Version": "2022-11-28"}
    if cfg["token"]:
        headers["Authorization"] = f"Bearer {cfg['token']}"
    try:
        r = requests.get(url, headers=headers, params={"ref": cfg["branch"]}, timeout=10)
        if r.status_code == 200:
            raw = base64.b64decode((r.json() or {}).get("content", "")).decode("utf-8")
            return json.loads(raw), True, f"cloud:{cfg['repo']}"
        cloud_error = f"GitHub performance {r.status_code}: {r.text[:120]}"
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
        edge_cls = "edge-pos" if edge >= 0 else "edge-neg"
        body.append(
            f"<tr><td>{r.get('name','')}</td><td>{int(r.get('total',0) or 0)}</td>"
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
    <div class="section-title"><span>★ Proof Analytics ★</span></div>
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
    note = billboard.get("note", "1H board is primary. 24H board is context only.")
    st.markdown(f"""
    <div class="section-title"><span>★ Kraken Billboard ★</span></div>
    <div class="notice">{note}</div>
    <div class="billboard-grid">
      <div class="billboard-panel">
        <div class="billboard-title">1H Momentum Board — Primary Radar</div>
        <table class="billboard-table">
          <thead><tr><th>Pair</th><th>1H</th><th>24H</th><th>Vol</th><th>Score</th></tr></thead>
          <tbody>{billboard_rows(one_hour, show_score=True)}</tbody>
        </table>
      </div>
      <div class="billboard-panel">
        <div class="billboard-title">24H Context Board — Not Entry Signal</div>
        <table class="billboard-table">
          <thead><tr><th>Pair</th><th>1H</th><th>24H</th><th>Vol</th></tr></thead>
          <tbody>{billboard_rows(twenty_four, show_score=False)}</tbody>
        </table>
      </div>
    </div>
    """, unsafe_allow_html=True)


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
    <div class="section-title"><span>★ Performance Dashboard ★</span></div>
    <div class="perf-grid">
      <div class="perf-card"><div class="perf-k">Tracked Signals</div><div class="perf-v">{total}</div><div class="perf-sub">Scanner-side history</div></div>
      <div class="perf-card"><div class="perf-k">Hit +1%</div><div class="perf-v">{hit1_rate:.0f}%</div><div class="perf-sub">Since tracking started</div></div>
      <div class="perf-card"><div class="perf-k">Hit +2%</div><div class="perf-v">{hit2_rate:.0f}%</div><div class="perf-sub">Momentum target test</div></div>
      <div class="perf-card"><div class="perf-k">Avg Max Move</div><div class="perf-v">{avg_max:+.2f}%</div><div class="perf-sub">Observed after alert</div></div>
      <div class="perf-card"><div class="perf-k">Best Signal</div><div class="perf-v" style="font-size:22px;">{best_pair}</div><div class="perf-sub">{best_gain:+.2f}% max</div></div>
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
          <div class="small">Model confidence: {pconf}% · range estimate, not certainty</div>
          <div class="env-box">
            <div class="env-k">Environment Weight</div>
            <div class="env-v">{env_score}/100 <span class="env-tier">{env_tier}</span></div>
            <div class="env-adj">{env_adj_html}</div>
          </div>
          <div class="riskgrid">
            <div class="riskcell"><span>Entry Zone</span><b>{levels['entry_low']} – {levels['entry_high']}</b></div>
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
          <div class="next-box" style="margin-top:12px;"><b>Simple answer:</b> <span class="{clock['class']}">{clock['status']}</span> — {action_text(setup, timing)}</div>
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
    <div class="brand"><div class="logo">A+</div><div><div class="title"><span>A+</span> DECISION RADAR</div><div class="subtitle">Visual Market Command Center</div></div></div>
    <div class="meta"><div>📅 <b>{str(updated)[:10] or 'waiting'}</b></div><div>🕒 <b>{str(updated)[11:19] or '--:--:--'}</b></div><div>🔄 Cycle: <b>{cycle}</b></div><div>🎯 Active Pairs: <b>{active}</b></div></div>
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

render_performance_dashboard(perf_state, perf_ok, perf_source)

st.markdown('<div class="section-title"><span>★ Top 5 Decision Setups ★</span></div>', unsafe_allow_html=True)
if setups:
    for i, setup in enumerate(setups[:TOP_SETUP_LIMIT], start=1):
        render_setup_card(setup, i, market, updated)
else:
    st.markdown('<div class="notice">No live setups yet. Start the scanner and wait for the next cycle.</div>', unsafe_allow_html=True)
    for i in range(1,TOP_SETUP_LIMIT+1):
        render_setup_card({"coin":"WAIT", "pair":"WAITING", "tag":"PREBUILD", "trigger_score":0,"trade_score":0,"confidence":0,"chart_read":{"timing":"WAIT","read_30m":"Waiting","read_1h":"Waiting"},"flags":{}}, i, market, updated)

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
  <div class="bottom-panel"><div class="panel-title">Sector Flow</div>{sector_rows}<br/><div class="panel-title">State Counts</div>{counts_rows}</div>
  <div class="bottom-panel">
    <div class="panel-title">How To Read This</div>
    <div class="read-row"><div class="read-key" style="color:#78FF2E;">Projected</div><div class="read-desc">Estimated move range from volatility, impulse, scores, VWAP, and BTC regime.</div></div>
    <div class="read-row"><div class="read-key" style="color:#FFD93D;">Entry Zone</div><div class="read-desc">Area where risk can be defined. Not a blind buy signal.</div></div>
    <div class="read-row"><div class="read-key" style="color:#FF4D4D;">Invalid</div><div class="read-desc">Where the trade idea is wrong. Respect this first.</div></div>
    <div class="read-row"><div class="read-key" style="color:#35A7FF;">Timing</div><div class="read-desc">EXECUTE ZONE = next few minutes only. WAIT = let setup form. TOO LATE = skip chase.</div></div>
  </div>
</div>
<div class="footer"><div><span class="left">🏆 Focus. Discipline. Execution.</span><br/><span class="small">Expected ranges are estimates, not guarantees. Trade risk first.</span></div><div class="small">Not financial advice. Live market-read journal.</div></div>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
# === A+ SCANNER V3 LEADERBOARD CORE ===
# Full upgrade:
# - Keeps watch leaderboard as the core engine
# - Adds rank-change tracking on leaderboard
# - Adds time-on-board / cycle streak tracking
# - Adds fresh breakout markers
# - Adds top-3 summary line each cycle
# - Premium alerts now promote strong leaderboard names
# - Computes BTC regime once per cycle
# - Keeps trend / volume / structure / acceleration filters
# - Keeps scanner_log.txt logging
# - v19 adds composite score, veteran decision, position size, relative strength
# - v21 adds proof analytics buckets: regime, timing, sector, tag, RSI, VWAP distance, setup type, hour
#
# Notes:
# - Discord main webhook = promoted leaderboard / TRADE READY alerts only
# - Watch webhook = leaderboard/watch list pings
# - Market cap gate uses CoinGecko cache with stale-cache fallback

import os
import time
import math
import json
import base64
import hashlib
import re
import datetime as dt
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import traceback

import requests
import numpy as np
from colorama import init, Fore, Style

init(autoreset=True)

# =========================
# CONFIG
# =========================

KRAKEN_API_BASE = "https://api.kraken.com/0/public"

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
WATCH_WEBHOOK_URL = os.getenv("WATCH_WEBHOOK_URL", "").strip()
SECTOR_WEBHOOK_URL = os.getenv("SECTOR_WEBHOOK_URL", "").strip()

# Free visual radar webhook. If FREE_RADAR_WEBHOOK_URL is not set, the scanner
# uses WATCH_WEBHOOK_URL as the free radar channel.
FREE_RADAR_WEBHOOK_URL = os.getenv("FREE_RADAR_WEBHOOK_URL", "").strip() or WATCH_WEBHOOK_URL

WATCH_MIN_SCORE = 60
WATCH_TOP_N = 5
WATCH_SEND_EVERY_CYCLE = False

# Leaderboard-first promotion rules
PREMIUM_MIN_TRIGGER = 75
PREMIUM_MIN_TRADE_SCORE = 70
PREMIUM_MIN_BOARD_CYCLES = 3
PREMIUM_MIN_WATCH_HITS = 2
TOP3_SUMMARY_COUNT = 3

# Pre-alert / early positioning
PRE_ALERT_MIN_TRIGGER = 65
PRE_ALERT_MIN_TRADE_SCORE = 55
PRE_ALERT_MIN_STREAK = 2
PRE_ALERT_MIN_WATCH_HITS = 2
PRE_ALERT_TOP_N = 3
PRE_ALERT_COOLDOWN_SECONDS = 20 * 60
PRE_ALERT_RESEND_RANK_IMPROVE = True

# Sector flow / rotation
SECTOR_BOOST_SCORE = 10
STRONG_SECTOR_MIN_COINS = 2
STRONG_SECTOR_MIN_COMBINED_TRIGGER = 140
TOP_SECTOR_SUMMARY_COUNT = 4
SECTOR_WEBHOOK_EVERY_N_CYCLES = 999999
SECTOR_MIN_POST_COINS = 1

# Discord formatting
DISCORD_COMPACT_MODE = True
HOT_STREAK_MIN = 3
STRICT_MODE = True
MAX_BLOCKED_PRINT = 5
MAX_EARLY_PRINT = 3
MAX_LATE_PRINT = 2

SECTORS = {
    "AI": {"FET", "AGIX", "OCEAN", "TAO", "RENDER", "RNDR", "AKT", "WLD", "ARKM", "NMR"},
    "L1": {"SOL", "ETH", "ADA", "AVAX", "ATOM", "DOT", "SEI", "SUI", "APT", "ALGO", "NEAR", "TRX"},
    "L2": {"ARB", "OP", "STRK", "MNT", "ZK", "ZKS", "IMX"},
    "DEFI": {"UNI", "AAVE", "COMP", "MKR", "CRV", "SNX", "SUSHI", "1INCH", "LDO", "DYDX", "JUP"},
    "MEME": {"DOGE", "SHIB", "PEPE", "BONK", "WIF", "FLOKI", "BRETT", "POPCAT", "MOG"},
    "GAMING": {"IMX", "GALA", "BEAM", "AXS", "SAND", "MANA", "ILV", "YGG"},
    "INFRA": {"LINK", "GRT", "FIL", "AR", "TIA", "PYTH", "API3", "BAND"},
    "PAYMENTS": {"XRP", "XLM", "LTC", "BCH", "HBAR", "XMR"},
    "RWA": {"ONDO", "POLYX", "MPL"},
}

TOP_N_PAIRS = 100

# Kraken Billboard Radar
USE_KRAKEN_BILLBOARD = True
BILLBOARD_TOP_N = 50
BILLBOARD_MIN_24H_CHANGE_PCT = 0.0
BILLBOARD_MIN_24H_USD_VOLUME = 25_000

# Billboard v7: fresh 1H momentum is the main radar.
# 24H change stays as context only.
BILLBOARD_USE_1H_MOMENTUM = True
BILLBOARD_MIN_1H_CHANGE_PCT = -99.0
BILLBOARD_1H_SHORTLIST_N = 90
BILLBOARD_VOLUME_WEIGHT = 0.35
BILLBOARD_1H_WEIGHT = 0.65
BILLBOARD_CHANGE_WEIGHT = 0.55  # legacy fallback only
BILLBOARD_PRINT_TOP_N = 10

# Website billboard snapshot. Scanner fills this every cycle so the Streamlit
# app can show both fresh 1H movers and broader 24H context.
BILLBOARD_EXPORT_TOP_N = int(os.getenv("BILLBOARD_EXPORT_TOP_N", "12"))
LAST_BILLBOARD_SNAPSHOT = {"one_hour": [], "twenty_four_hour": []}

PAIR_REFRESH_SECONDS = 60
SCAN_SLEEP_SECONDS = 15
PER_PAIR_THROTTLE_SECONDS = 0.05
OHLC_TIMEOUT_SECONDS = 8

COOLDOWN_SECONDS = 10 * 60

# --- Market Cap Gate ---
USE_MARKET_CAP_GATE = True
MIN_MARKET_CAP_USD = 100_000
MARKET_CAP_CACHE_PATH = "market_caps.json"
MARKET_CAP_TTL_SECONDS = 24 * 60 * 60
COINGECKO_PAGES = 1
COINGECKO_TIMEOUT = 15

# BTC regime engine
BTC_REGIME_PAIR_LIMITS = {
    "BEAR": 40,
    "WATCH": 75,
    "BULL_ATTACK": 140,
}
BTC_REGIME_REFRESH_SECONDS = {
    "BEAR": 90,
    "WATCH": 45,
    "BULL_ATTACK": 20,
}
BTC_REGIME_SCAN_SLEEP_SECONDS = {
    "BEAR": 20,
    "WATCH": 12,
    "BULL_ATTACK": 6,
}

ATTACK_HOLD_SECONDS = 20 * 60
ATTACK_INVALIDATION_CYCLES = 2
REFRESH_MARKET_CAPS_DURING_RUNTIME = False
RUNTIME_MARKET_CAP_REFRESH_SECONDS = 6 * 60 * 60

# A+ rules
RSI_1M_MIN = 55.0
RSI_1M_MAX = 75.0
RSI_5M_MIN = 54.5
MACD_HIST_15M_MIN = 0.0

REGIME_RULES = {
    # Legacy names kept for backward compatibility with older UI / Discord wording.
    "BEAR": {
        "rsi_1m_min": 55.0,
        "rsi_1m_max": 75.0,
        "rsi_5m_min": 54.5,
        "macd_hist_15m_min": 0.0,
        "watch_min_score": 60,
        "premium_enabled": False,
        "trade_allowed": False,
        "mode_note": "No normal longs. Sharpshooter only.",
    },
    "WATCH": {
        "rsi_1m_min": 54.5,
        "rsi_1m_max": 78.0,
        "rsi_5m_min": 53.0,
        "macd_hist_15m_min": -0.00000001,
        "watch_min_score": 58,
        "premium_enabled": False,
        "trade_allowed": True,
        "mode_note": "Selective watch. Pullback required.",
    },
    "BULL_ATTACK": {
        "rsi_1m_min": 53.5,
        "rsi_1m_max": 80.0,
        "rsi_5m_min": 52.0,
        "macd_hist_15m_min": -0.00000001,
        "watch_min_score": 55,
        "premium_enabled": True,
        "trade_allowed": True,
        "mode_note": "Expansion. Normal A+ long rules allowed.",
    },
    # v17 Veteran Regime Model: this replaces blunt bull/bear labels with tradability phases.
    "ACCUMULATION": {
        "rsi_1m_min": 54.5,
        "rsi_1m_max": 74.0,
        "rsi_5m_min": 52.0,
        "macd_hist_15m_min": -0.00000001,
        "watch_min_score": 62,
        "premium_enabled": False,
        "trade_allowed": True,
        "mode_note": "Base forming. Small/selective. Wait for proof.",
    },
    "EXPANSION": {
        "rsi_1m_min": 53.5,
        "rsi_1m_max": 76.0,
        "rsi_5m_min": 53.0,
        "macd_hist_15m_min": -0.00000001,
        "watch_min_score": 56,
        "premium_enabled": True,
        "trade_allowed": True,
        "mode_note": "Clean trend. Best environment for continuation.",
    },
    "DISTRIBUTION": {
        "rsi_1m_min": 56.0,
        "rsi_1m_max": 70.0,
        "rsi_5m_min": 54.0,
        "macd_hist_15m_min": 0.0,
        "watch_min_score": 70,
        "premium_enabled": False,
        "trade_allowed": False,
        "mode_note": "Price elevated but momentum weakening. Sharpshooter only.",
    },
    "EXHAUSTION": {
        "rsi_1m_min": 56.0,
        "rsi_1m_max": 68.0,
        "rsi_5m_min": 54.0,
        "macd_hist_15m_min": 0.0,
        "watch_min_score": 72,
        "premium_enabled": False,
        "trade_allowed": False,
        "mode_note": "Overextended. Avoid chase; wait for reset.",
    },
    "CHOP": {
        "rsi_1m_min": 55.0,
        "rsi_1m_max": 72.0,
        "rsi_5m_min": 53.5,
        "macd_hist_15m_min": 0.0,
        "watch_min_score": 68,
        "premium_enabled": False,
        "trade_allowed": False,
        "mode_note": "No clean regime. Only extreme relative-strength exceptions.",
    },
}

# Use the same pacing controls for the new veteran phases.
BTC_REGIME_PAIR_LIMITS.update({
    "ACCUMULATION": 75,
    "EXPANSION": 140,
    "DISTRIBUTION": 55,
    "EXHAUSTION": 40,
    "CHOP": 50,
})
BTC_REGIME_REFRESH_SECONDS.update({
    "ACCUMULATION": 45,
    "EXPANSION": 20,
    "DISTRIBUTION": 60,
    "EXHAUSTION": 90,
    "CHOP": 75,
})
BTC_REGIME_SCAN_SLEEP_SECONDS.update({
    "ACCUMULATION": 12,
    "EXPANSION": 6,
    "DISTRIBUTION": 16,
    "EXHAUSTION": 20,
    "CHOP": 18,
})

# VWAP / flags
VWAP_LOOKBACK_1M = 240

# Bollinger compression
BB_PERIOD = 20
BB_STD = 2.0
BB_WIDTH_MAX = 0.012

# Impulse / pullback heuristics
IMPULSE_MIN_RETURN = 0.004
PULLBACK_MAX_DROP = 0.006

# Momentum acceleration detection
ACCEL_LOOKBACK_BARS = 3
ACCEL_MIN_RETURN = 0.0035
ACCEL_MULTIPLIER = 1.20

# Trend filter
TREND_EMA_PERIOD_15M = 50
TREND_EMA_PERIOD_1H = 50

# Volume spike
VOLUME_LOOKBACK_BARS = 20
VOLUME_SPIKE_MULTIPLIER = 1.5

# Structure break
STRUCTURE_LOOKBACK_BARS = 20
STRUCTURE_EXCLUDE_RECENT_BARS = 5

# Trade readiness
TRADE_SCORE_READY = 70

# Stable exclusions
EXCLUDE_BASES = {"USDT", "USDC", "DAI", "TUSD", "PAXG", "PYUSD"}

# Rolling hit tracking
HIT_WINDOW_SECONDS = 2 * 60 * 60
recent_hits: Dict[str, List[float]] = {}
recent_watch_hits: Dict[str, List[float]] = {}
watch_cycle_streaks: Dict[str, int] = {}
leaderboard_prev_ranks: Dict[str, int] = {}
setup_cycle_streaks: Dict[str, int] = {}
setup_started_at: Dict[str, float] = {}
pre_alert_last_sent: Dict[str, float] = {}
pre_alert_last_rank: Dict[str, int] = {}


# =========================
# CONSOLE COLORS
# =========================

def color_bool(value: bool) -> str:
    return f"{Fore.GREEN}{value}{Style.RESET_ALL}" if value else f"{Fore.RED}{value}{Style.RESET_ALL}"

def color_score(score: int) -> str:
    if score >= 80:
        return f"{Fore.GREEN}{score}{Style.RESET_ALL}"
    if score >= 60:
        return f"{Fore.YELLOW}{score}{Style.RESET_ALL}"
    return f"{Fore.RED}{score}{Style.RESET_ALL}"

def color_label(label: str) -> str:
    if label == "TRADE READY":
        return f"{Fore.GREEN}{Style.BRIGHT}{label}{Style.RESET_ALL}"
    if label == "Watch":
        return f"{Fore.YELLOW}{Style.BRIGHT}{label}{Style.RESET_ALL}"
    return f"{Fore.RED}{label}{Style.RESET_ALL}"

def color_symbol(sym: str) -> str:
    return f"{Fore.CYAN}{Style.BRIGHT}{sym}{Style.RESET_ALL}"

def color_hits(hits: int, stars: str) -> str:
    if hits >= 3:
        return f"{Fore.MAGENTA}{hits} {stars}{Style.RESET_ALL}"
    if hits >= 1:
        return f"{Fore.YELLOW}{hits} {stars}{Style.RESET_ALL}"
    return f"{Fore.WHITE}{hits} {stars}{Style.RESET_ALL}"

def color_accel(accel: bool) -> str:
    return f"{Fore.GREEN}ACCEL{Style.RESET_ALL}" if accel else f"{Fore.WHITE}-{Style.RESET_ALL}"

def btc_console_label(value) -> str:
    if isinstance(value, str):
        if value in {"BULL_ATTACK", "EXPANSION"}:
            return f"{Fore.GREEN}{Style.BRIGHT}BTC EXPANSION{Style.RESET_ALL}"
        if value in {"WATCH", "ACCUMULATION"}:
            return f"{Fore.YELLOW}{Style.BRIGHT}BTC ACCUMULATION{Style.RESET_ALL}"
        if value == "DISTRIBUTION":
            return f"{Fore.MAGENTA}{Style.BRIGHT}BTC DISTRIBUTION{Style.RESET_ALL}"
        if value == "EXHAUSTION":
            return f"{Fore.RED}{Style.BRIGHT}BTC EXHAUSTION{Style.RESET_ALL}"
        if value == "CHOP":
            return f"{Fore.BLUE}{Style.BRIGHT}BTC CHOP{Style.RESET_ALL}"
        return f"{Fore.RED}{Style.BRIGHT}BTC BEAR{Style.RESET_ALL}"
    return f"{Fore.GREEN}{Style.BRIGHT}BTC EXPANSION{Style.RESET_ALL}" if value else f"{Fore.RED}{Style.BRIGHT}BTC BEAR{Style.RESET_ALL}"

def compact_missing_list(missing: List[str], limit: int = 2) -> str:
    if not missing:
        return "None"
    return ", ".join(missing[:limit])

def strip_ansi(text: str) -> str:
    return re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', text)


def color_state(state: str) -> str:
    mapping = {
        "READY": f"{Fore.GREEN}{Style.BRIGHT}READY{Style.RESET_ALL}",
        "BUILDING": f"{Fore.YELLOW}{Style.BRIGHT}BUILDING{Style.RESET_ALL}",
        "EARLY": f"{Fore.CYAN}{Style.BRIGHT}EARLY{Style.RESET_ALL}",
        "LATE": f"{Fore.MAGENTA}{Style.BRIGHT}LATE{Style.RESET_ALL}",
        "BLOCKED": f"{Fore.RED}{Style.BRIGHT}BLOCKED{Style.RESET_ALL}",
    }
    return mapping.get(state, state)

def cycle_mode_label(btc_ok: bool) -> str:
    return f"{Fore.GREEN}{Style.BRIGHT}TRADE ALLOWED{Style.RESET_ALL}" if btc_ok else f"{Fore.RED}{Style.BRIGHT}NO TRADE{Style.RESET_ALL}"

def console_divider(char: str = "=") -> str:
    return f"{Fore.BLUE}{char * 58}{Style.RESET_ALL}"

def primary_blocker(er, btc_ok: bool, sector_count: int = 0, sector_strong: bool = False) -> str:
    if not btc_ok:
        return "BTC BEAR"
    if sector_count and sector_count < 2:
        return "NO SECTOR SUPPORT"
    if sector_count and not sector_strong:
        return "WEAK SECTOR"
    if getattr(er, "trap_risk", "LOW") == "HIGH":
        return "TRAP RISK"
    if getattr(er, "momentum_quality", "UNKNOWN") == "FAILING":
        return "MOMENTUM FAILING"
    if not er.flags.get("vwap_accept", False):
        return "VWAP NOT ACCEPTED"
    if not er.flags.get("trend_ok", False):
        return "TREND NOT ALIGNED"
    if not er.flags.get("volume_spike", False):
        return "NO VOLUME"
    if not er.flags.get("structure_break", False):
        return "NO BREAK"
    if not er.flags.get("pullback", False):
        return "NO PULLBACK"
    if er.rsi_1m > RSI_1M_MAX:
        return "RSI HOT"
    if er.rsi_1m < RSI_1M_MIN:
        return "RSI LOW"
    return "WAIT CONFIRM"

def classify_entry_state(er, btc_ok: bool, sector_count: int = 0, sector_strong: bool = False) -> Tuple[str, str]:
    if not btc_ok:
        return "BLOCKED", "BTC BEAR"
    if er.trap_risk == "HIGH":
        return "BLOCKED", "TRAP RISK"
    if er.momentum_quality == "FAILING":
        return "BLOCKED", "MOMENTUM FAILING"
    if er.rsi_1m > RSI_1M_MAX:
        return "LATE", "RSI HOT"
    if sector_count and sector_count < 2:
        return "BLOCKED", "NO SECTOR SUPPORT"
    if not er.flags.get("vwap_accept", False):
        return "BLOCKED", "VWAP NOT ACCEPTED"
    if er.flags.get("trend_ok", False) and er.flags.get("volume_spike", False) and er.flags.get("structure_break", False) and er.flags.get("pullback", False):
        return "READY", "ALL GATES PASS"
    if er.flags.get("trend_ok", False) and er.flags.get("vwap_accept", False):
        if not er.flags.get("pullback", False):
            return "EARLY", "NO PULLBACK"
        if not er.flags.get("volume_spike", False):
            return "BUILDING", "NO VOLUME"
        if not er.flags.get("structure_break", False):
            return "BUILDING", "NO BREAK"
        return "BUILDING", "WAIT CONFIRM"
    return "BLOCKED", primary_blocker(er, btc_ok, sector_count, sector_strong)

def strongest_blocker_reason(state_counts: Dict[str, int], btc_ok: bool) -> str:
    if not btc_ok:
        return "BTC BEAR"
    if state_counts.get("READY", 0) > 0:
        return "READY NAMES PRESENT"
    if state_counts.get("BUILDING", 0) > 0:
        return "SETUPS BUILDING"
    if state_counts.get("EARLY", 0) > 0:
        return "EARLY / WAIT PULLBACK"
    return "NO CONFIRMED STRUCTURE"

def build_console_cycle_start(cycle_time: str, btc_ok: bool, pair_count: int) -> str:
    mode = "TRADE ALLOWED" if btc_ok else "NO TRADE"
    reason = "BTC BULL + HARD GATES ACTIVE" if btc_ok else "BTC BEAR"
    return "\n".join([
        "",
        console_divider("="),
        f"{Fore.CYAN}{Style.BRIGHT}CYCLE START | {cycle_time}{Style.RESET_ALL}",
        f"MODE: {Fore.GREEN + mode + Style.RESET_ALL if btc_ok else Fore.RED + mode + Style.RESET_ALL}",
        f"REASON: {Fore.GREEN + reason + Style.RESET_ALL if btc_ok else Fore.RED + reason + Style.RESET_ALL}",
        f"POOL: {pair_count} pairs",
        console_divider("="),
    ])

def build_console_cycle_story(cycle_time: str, btc_ok: bool, pair_count: int, state_counts: Dict[str, int], top_watch: List[dict], sector_counts: Dict[str, int], strongest_item: Optional[dict], blocker_reason: str) -> str:
    top_names = ", ".join(item["er"].wsname for item in top_watch[:5]) if top_watch else "none"
    if sector_counts:
        top_sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        sector_line = " | ".join(f"{name} {count}" for name, count in top_sectors)
    else:
        sector_line = "none"
    strongest_line = "none"
    if strongest_item:
        er = strongest_item["er"]
        strongest_line = f"{er.wsname} T{er.trigger_score} TR{strongest_item.get('effective_trade_score', er.trade_score)}"
    cycle_read = "Trade allowed. Execute READY only. BUILDING means wait for final confirmation." if btc_ok else f"Weak tape. {blocker_reason}. Stand down."
    lines = [
        console_divider("="),
        f"{Fore.CYAN}{Style.BRIGHT}CYCLE SUMMARY | {cycle_time}{Style.RESET_ALL}",
        f"PAIR SUMMARY | READY:{state_counts.get('READY', 0)} BUILDING:{state_counts.get('BUILDING', 0)} EARLY:{state_counts.get('EARLY', 0)} BLOCKED:{state_counts.get('BLOCKED', 0)} LATE:{state_counts.get('LATE', 0)}",
        f"TOP WATCH: {top_names}",
        f"SECTOR FLOW: {sector_line}",
        f"STRONGEST: {strongest_line}",
        f"CYCLE READ: {cycle_read}",
        console_divider("="),
    ]
    return "\n".join(lines)

# =========================
# UTIL
# =========================

def ts() -> str:
    return dt.datetime.now().strftime("%H:%M:%S")

def safe_float(x, default=0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def request_json(url: str, params: Optional[dict] = None, timeout: int = 15) -> dict:
    r = requests.get(
        url,
        params=params,
        timeout=timeout,
        headers={"User-Agent": "aplus-scanner/2.0"},
    )
    r.raise_for_status()
    return r.json()

def normalize_symbol(sym: str) -> str:
    return (sym or "").strip().upper()

def normalize_kraken_asset_code(code: str) -> str:
    c = normalize_symbol(code)

    mapping = {
        "XBT": "BTC",
        "XDG": "DOGE",
        "XXBT": "BTC",
        "XETH": "ETH",
        "XXETH": "ETH",
        "ZUSD": "USD",
        "ZEUR": "EUR",
        "ZGBP": "GBP",
        "ZCAD": "CAD",
        "ZAUD": "AUD",
        "ZJPY": "JPY",
        "XREP": "REP",
        "XMLN": "MLN",
        "XICN": "ICN",
    }
    if c in mapping:
        return mapping[c]

    if len(c) >= 4 and c[0] in {"X", "Z"} and c[1:].isalpha():
        stripped = c[1:]
        if 2 <= len(stripped) <= 6:
            return stripped

    return c

def asset_base_from_wsname(wsname: str) -> str:
    base = (wsname or "").split("/")[0].strip().upper()
    return normalize_kraken_asset_code(base)

def get_sector(symbol: str) -> str:
    sym = normalize_kraken_asset_code(symbol)
    for sector, coins in SECTORS.items():
        if sym in coins:
            return sector
    return "OTHER"

def compute_sector_flow(watch_candidates: List[dict]) -> Tuple[Dict[str, int], Dict[str, int], List[str]]:
    sector_counts: Dict[str, int] = {}
    sector_scores: Dict[str, int] = {}
    for item in watch_candidates:
        er = item["er"]
        sector = er.sector
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        sector_scores[sector] = sector_scores.get(sector, 0) + er.trigger_score

    strong_sectors = [
        sector for sector in sector_counts
        if sector_counts[sector] >= STRONG_SECTOR_MIN_COINS
        and sector_scores.get(sector, 0) >= STRONG_SECTOR_MIN_COMBINED_TRIGGER
    ]
    strong_sectors.sort(key=lambda s: (sector_scores.get(s, 0), sector_counts.get(s, 0)), reverse=True)
    return sector_counts, sector_scores, strong_sectors

def build_sector_summary(sector_counts: Dict[str, int], sector_scores: Dict[str, int], strong_sectors: List[str]) -> str:
    if not sector_counts:
        return "🌐 Sector Flow: none"

    ranked = sorted(
        sector_counts.keys(),
        key=lambda s: (1 if s in strong_sectors else 0, sector_scores.get(s, 0), sector_counts.get(s, 0)),
        reverse=True,
    )[:TOP_SECTOR_SUMMARY_COUNT]

    lines = ["🌐 Sector Flow:"]
    for sector in ranked:
        marker = "🔥" if sector in strong_sectors else "•"
        lines.append(f"{marker} {sector}: {sector_counts.get(sector, 0)}c | {sector_scores.get(sector, 0)}t")
    return "\n".join(lines)

# =========================
# DISCORD
# =========================

def send_webhook_url(webhook_url: str, content: str = "") -> bool:
    if not webhook_url:
        return False

    payload = {"content": content[:2000]}
    try:
        r = requests.post(webhook_url, json=payload, timeout=10)
        if r.status_code == 429:
            try:
                data = r.json()
                retry_after = float(data.get("retry_after", 1.0))
            except Exception:
                retry_after = 1.0
            time.sleep(retry_after)
            r = requests.post(webhook_url, json=payload, timeout=10)
        return 200 <= r.status_code < 300
    except Exception:
        return False

def send_discord_webhook(content: str = "") -> bool:
    return send_webhook_url(DISCORD_WEBHOOK_URL, content)

def send_watch_webhook(content: str = "") -> bool:
    if not WATCH_WEBHOOK_URL:
        return False

    clean_content = strip_ansi(content)
    payload = {"content": clean_content[:2000]}
    try:
        r = requests.post(WATCH_WEBHOOK_URL, json=payload, timeout=10)

        if r.status_code == 429:
            try:
                data = r.json()
                retry_after = float(data.get("retry_after", 1.0))
            except Exception:
                retry_after = 1.0
            time.sleep(retry_after)
            r = requests.post(WATCH_WEBHOOK_URL, json=payload, timeout=10)

        return 200 <= r.status_code < 300
    except Exception:
        return False

def send_sector_webhook(content: str = "") -> bool:
    return send_webhook_url(SECTOR_WEBHOOK_URL, content)

def compute_sector_snapshot(cycle_watch, cycle_results):
    snapshot = {}
    source = cycle_watch if cycle_watch else cycle_results

    for item in source:
        er = item["er"]
        sector = er.sector
        bucket = snapshot.setdefault(sector, {
            "count": 0,
            "total_score": 0,
            "leaders": []
        })
        bucket["count"] += 1
        bucket["total_score"] += er.trigger_score
        if len(bucket["leaders"]) < 3 and er.wsname not in bucket["leaders"]:
            bucket["leaders"].append(er.wsname)

    return snapshot

def build_sector_webhook_block(cycle_time, btc_ok, snapshot):
    lines = [
        f"🌐 **SECTOR HEALTH** | {cycle_time}",
        f"BTC: {'🟢 BULL' if btc_ok else '🔴 BEAR'}",
        "",
    ]

    ranked = sorted(
        snapshot.items(),
        key=lambda x: (x[1]["total_score"], x[1]["count"]),
        reverse=True
    )[:5]

    if not ranked:
        lines.append("No sector leaders this cycle.")
        return "\n".join(lines)

    for sector, data in ranked:
        leaders = ", ".join(data["leaders"]) if data["leaders"] else "none"
        lines.append(f"{sector}: {data['count']} coins | Score {data['total_score']}")
        lines.append(f"→ {leaders}")
        lines.append("")

    return "\n".join(lines)

def build_watch_block(lines: List[str], cycle_time: str, btc_ok: bool, top3: str, sector_summary: str) -> str:
    if not lines:
        return ""

    btc_label = "🟢 BULL" if btc_ok else "🔴 BEAR"
    header_lines = [
        f"📊 **WATCH LEADERBOARD** | {cycle_time}",
        f"BTC: {btc_label}",
        "",
        top3,
        "",
        sector_summary,
        "",
        "════════════════════",
    ]

    return "\n".join(header_lines + lines)

def build_startup_status_bar(main_ok: bool, watch_ok: bool, sector_ok: bool) -> str:
    def flag(ok: bool, configured: bool) -> str:
        if not configured:
            return "OFF"
        return "OK" if ok else "FAIL"
    return (
        f"WEBHOOK STATUS | "
        f"MAIN={flag(main_ok, bool(DISCORD_WEBHOOK_URL))} | "
        f"WATCH={flag(watch_ok, bool(WATCH_WEBHOOK_URL))} | "
        f"SECTOR={flag(sector_ok, bool(SECTOR_WEBHOOK_URL))}"
    )

def startup_ping_all_webhooks(total_pairs: int, picked_pairs: int) -> tuple[bool, bool, bool]:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    base = (
        "🟢 **Scanner Startup Check**\n"
        f"Time: `{now_str}`\n"
        f"Pairs Found: **{total_pairs}** | Pool: **{picked_pairs}**\n"
    )

    main_msg = base + "Channel: **premium / main alerts**"
    watch_msg = base + "Channel: **watch leaderboard**"
    sector_msg = base + "Channel: **sector / market health**"

    main_ok = send_discord_webhook(main_msg) if DISCORD_WEBHOOK_URL else False
    watch_ok = send_watch_webhook(watch_msg) if WATCH_WEBHOOK_URL else False
    sector_ok = send_sector_webhook(sector_msg) if SECTOR_WEBHOOK_URL else False
    return main_ok, watch_ok, sector_ok

def discord_startup_ping(total_pairs: int, picked_pairs: int) -> None:
    now_str = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (
        "🟢 **Kraken A+ Scanner Connected**\n"
        f"Time: `{now_str}`\n"
        f"Total USD Pairs Found: **{total_pairs}**\n"
        f"Top Movers Pool (this cycle): **{picked_pairs}**\n"
        "TFs: `1m / 5m / 15m / 1H`\n"
        "Discord: **Leaderboard promotion alerts** ✅\n"
        "Watch: **Leaderboard enabled** ✅"
    )
    ok = send_discord_webhook(msg)
    print(f"[{ts()}] Discord startup ping " + (f"{Fore.GREEN}sent{Style.RESET_ALL}" if ok else f"{Fore.RED}failed{Style.RESET_ALL}"))



def update_setup_tracking(current_setup_pairs: set):
    now = time.time()
    current_set = set(current_setup_pairs)

    for pair in list(setup_cycle_streaks.keys()):
        if pair not in current_set:
            setup_cycle_streaks[pair] = 0
    for pair in list(setup_started_at.keys()):
        if pair not in current_set:
            del setup_started_at[pair]

    for pair in current_set:
        if pair not in setup_started_at:
            setup_started_at[pair] = now
        setup_cycle_streaks[pair] = setup_cycle_streaks.get(pair, 0) + 1

    return dict(setup_cycle_streaks), dict(setup_started_at)

def format_setup_age(seconds_alive: float) -> str:
    if seconds_alive <= 0:
        return "0m"
    mins = int(seconds_alive // 60)
    if mins < 60:
        return f"{mins}m"
    hrs = mins // 60
    rem = mins % 60
    return f"{hrs}h{rem:02d}m"

def compute_entry_readiness(
    er: "EvalResult",
    regime_name: str,
    effective_trade_score: int,
    watch_hits: int,
    streak: int,
    sector_count: int,
    sector_strong: bool,
    setup_cycles: int,
) -> Tuple[int, str]:
    score = 0
    score += min(20, max(0, effective_trade_score - 40))
    score += 12 if er.flags.get("vwap_accept", False) else 0
    score += 10 if er.flags.get("trend_ok", False) else 0
    score += 10 if er.flags.get("pullback", False) else 0
    score += 10 if er.flags.get("volume_spike", False) else 0
    score += 10 if er.flags.get("structure_break", False) else 0
    score += 8 if er.flags.get("acceleration", False) else 0
    score += 8 if sector_strong else (4 if sector_count >= 2 else 0)
    score += min(6, watch_hits * 2)
    score += min(6, streak * 2)
    score += min(6, setup_cycles * 2)
    score += 8 if regime_name == "BULL_ATTACK" else (4 if regime_name == "WATCH" else 0)

    if er.rsi_1m >= 74 and er.flags.get("acceleration", False) and not er.flags.get("pullback", False):
        score -= 15
    if not er.flags.get("pullback", False) and not er.flags.get("structure_break", False):
        score -= 8
    if not er.flags.get("volume_spike", False) and regime_name != "WATCH":
        score -= 5

    score = max(0, min(100, int(score)))

    if er.rsi_1m >= 74 and er.flags.get("acceleration", False) and not er.flags.get("pullback", False):
        label = "LATE"
    elif score >= 80:
        label = "OPTIMAL"
    elif score >= 65:
        label = "READY SOON"
    elif score >= 50:
        label = "EARLY"
    else:
        label = "TOO EARLY"

    return score, label

def should_send_pre_alert(symbol: str, rank_now: int) -> bool:
    now = time.time()
    last_sent = pre_alert_last_sent.get(symbol, 0.0)
    last_rank = pre_alert_last_rank.get(symbol)

    if (now - last_sent) >= PRE_ALERT_COOLDOWN_SECONDS:
        return True
    if PRE_ALERT_RESEND_RANK_IMPROVE and last_rank is not None and rank_now < last_rank:
        return True
    return False

def mark_pre_alert_sent(symbol: str, rank_now: int):
    pre_alert_last_sent[symbol] = time.time()
    pre_alert_last_rank[symbol] = rank_now

def classify_execution_plan(er: "EvalResult", regime_name: str = "BEAR") -> str:
    if er.flags.get("compression", False) and er.flags.get("pullback", False) and er.flags.get("acceleration", False):
        return "compression breakout continuation"
    if er.flags.get("compression", False) and er.flags.get("pullback", False):
        return "compression break + pullback reclaim"
    if er.flags.get("impulse", False) and er.flags.get("pullback", False) and er.flags.get("acceleration", False):
        return "impulse pullback acceleration"
    if er.flags.get("impulse", False) and er.flags.get("pullback", False):
        return "impulse pullback continuation"
    if er.flags.get("trend_ok", False) and er.flags.get("vwap_accept", False):
        return "trend + VWAP continuation"
    if regime_name == "WATCH":
        return "watchlist stalker setup"
    return "momentum build"

def build_single_hard_stop(er: "EvalResult") -> str:
    if er.flags.get("pullback", False):
        return "Exit immediately on a 1m close back below VWAP or below the pullback low."
    return "Exit immediately on a failed 1m hold above VWAP."

def is_pre_aplus_candidate(er: "EvalResult", streak: int, watch_hits: int, effective_trade_score: int, regime_name: str) -> bool:
    if regime_name in {"BEAR", "DISTRIBUTION", "EXHAUSTION", "CHOP"}:
        return False
    return (
        er.trigger_score >= PRE_ALERT_MIN_TRIGGER
        and effective_trade_score >= PRE_ALERT_MIN_TRADE_SCORE
        and er.flags.get("trend_ok", False)
        and er.flags.get("vwap_accept", False)
        and (
            streak >= PRE_ALERT_MIN_STREAK
            or watch_hits >= PRE_ALERT_MIN_WATCH_HITS
            or er.flags.get("acceleration", False)
        )
    )

def build_pre_aplus_message(
    er: "EvalResult",
    rank_now: int,
    watch_hits: int,
    streak: int,
    effective_trade_score: int,
    sector_count: int,
    sector_strong: bool,
    regime_name: str,
    entry_readiness_score: int,
    entry_readiness_label: str,
    setup_cycles: int,
    setup_age_text: str,
) -> str:
    sector_note = "strong sector" if sector_strong else f"sector count={sector_count}"
    plan_type = classify_execution_plan(er, regime_name)
    if er.flags.get("pullback", False):
        next_step = "Stalk the next 1m hold above VWAP / pullback low and be ready before premium confirmation."
    else:
        next_step = "Do not enter yet. Wait for first controlled pullback or a clean higher-low to form."
    return (
        f"⚠️ **PRE-A+ BUILDING**\n"
        f"Symbol: **{er.wsname}** | Rank: **#{rank_now}**\n"
        f"Scores: **T{er.trigger_score} / TR{effective_trade_score} / C{er.confidence}**\n"
        f"Context: **BTC={regime_name} | Streak={streak} | Watch Hits={watch_hits} | {sector_note}**\n"
        f"Plan type: **{plan_type}**\n"
        f"Entry readiness: **{entry_readiness_score}/100 ({entry_readiness_label})**\n"
        f"Time in setup: **{setup_cycles} cycles | {setup_age_text}**\n\n"
        f"**Pre-Entry Read:**\n"
        f"• Price: `{er.price:.8f}`\n"
        f"• VWAP: `{er.vwap_ny:.8f}`\n"
        f"• RSI 1m / 5m: `{er.rsi_1m:.2f}` / `{er.rsi_5m:.2f}`\n"
        f"• Flags: `pullback={er.flags.get('pullback', False)} | accel={er.flags.get('acceleration', False)} | break={er.flags.get('structure_break', False)} | vol={er.flags.get('volume_spike', False)}`\n\n"
        f"**Execution Heads-Up:**\n"
        f"• Next step: `{next_step}`\n"
        f"• Single hard stop: `{build_single_hard_stop(er)}`\n"
    )

def premium_execution_plan(er: "EvalResult", regime_name: str = "BEAR", sector_count: int = 0, sector_strong: bool = False) -> str:
    setup_type_parts = []
    if er.flags.get("compression", False):
        setup_type_parts.append("compression")
    if er.flags.get("impulse", False):
        setup_type_parts.append("impulse")
    if er.flags.get("pullback", False):
        setup_type_parts.append("pullback")
    if er.flags.get("acceleration", False):
        setup_type_parts.append("acceleration")
    setup_type = " + ".join(setup_type_parts) if setup_type_parts else "momentum build"

    entry_style = "aggressive continuation"
    if er.flags.get("pullback", False):
        entry_style = "confirmation after pullback"
    if regime_name == "WATCH":
        entry_style = "patient watch-to-confirm entry"
    elif regime_name == "BULL_ATTACK":
        entry_style = "fast continuation entry"

    entry_window = "next 1-2 candles" if er.flags.get("acceleration", False) else "next 2-4 candles"
    trigger = "1m close continues to hold above VWAP and the latest higher-low stays intact"
    if not er.flags.get("pullback", False):
        trigger = "wait for the first controlled pullback into VWAP / local support before entry"

    confirmation_checks = [
        f"VWAP hold={'YES' if er.flags.get('vwap_accept', False) else 'NO'}",
        f"Trend={'YES' if er.flags.get('trend_ok', False) else 'NO'}",
        f"Volume spike={'YES' if er.flags.get('volume_spike', False) else 'NO'}",
        f"Structure break={'YES' if er.flags.get('structure_break', False) else 'NO'}",
    ]
    if sector_count:
        confirmation_checks.append(f"Sector count={sector_count}")
    if sector_strong:
        confirmation_checks.append("Strong sector=YES")

    stop_basis = "below VWAP or below the latest higher-low, whichever breaks first"
    first_target = "+3% to +5% for first trim"
    second_target = "trail remainder while 1m/5m momentum stays intact"
    if regime_name == "BULL_ATTACK":
        first_target = "+4% to +6% for first trim"
        second_target = "hold runner for expansion while BTC attack mode remains active"

    chase_note = "Do not chase a vertical extension after two fast green candles."
    if er.flags.get("acceleration", False):
        chase_note = "Acceleration is live. Either enter on immediate confirmation or let it go."

    return (
        f"**Execution Plan:**\n"
        f"• Setup type: `{setup_type}`\n"
        f"• Entry style: `{entry_style}`\n"
        f"• Entry window: `{entry_window}`\n"
        f"• Trigger: `{trigger}`\n"
        f"• Confirmation checks: `{' | '.join(confirmation_checks)}`\n"
        f"• Invalidation: `{stop_basis}`\n"
        f"• Profit plan: `{first_target}` then `{second_target}`\n"
        f"• Trade tip: `{chase_note}`\n"
    )

def build_discord_aplus_message(
    er: "EvalResult",
    btc_ok: bool,
    board_cycles: int = 0,
    watch_hits: int = 0,
    rank_now: int = 0,
    rank_change: str = "NEW",
    fresh_breakout: bool = False,
    effective_trade_score: int = 0,
    sector_count: int = 0,
    sector_strong: bool = False,
    regime_name: str = "BEAR",
    entry_readiness_score: int = 0,
    entry_readiness_label: str = "EARLY",
    setup_cycles: int = 0,
    setup_age_text: str = "0m",
) -> str:
    chk = "✅"
    sym = er.wsname
    sector_note = "strong sector" if sector_strong else f"sector count={sector_count}"
    entry_bias = "Continuation bias" if er.flags.get("acceleration", False) else "Confirmation bias"
    setup_grade = "A" if effective_trade_score >= 85 else "B" if effective_trade_score >= 75 else "C"

    msg = (
        f"{chk} **TRADE READY PROMOTION**\n"
        f"Symbol: **{sym}** | Rank: **#{rank_now}** ({rank_change}) | Grade: **{setup_grade}**\n"
        f"Scores: **T{er.trigger_score} / TR{effective_trade_score or er.trade_score} / C{er.confidence}**\n"
        f"Context: **BTC={regime_name} | Board Cycles={board_cycles} | Watch Hits={watch_hits} | {sector_note}**\n"
        f"Fresh Breakout: **{fresh_breakout}** | Stars: **{er.hits_last_2h} {er.stars or ''}** | Bias: **{entry_bias}**\n"
        f"Entry Readiness: **{entry_readiness_score}/100 ({entry_readiness_label})** | Time In Setup: **{setup_cycles} cycles | {setup_age_text}**\n\n"
        "**Setup Check:**\n"
        f"• Price: `{er.price:.8f}`\n"
        f"• VWAP: `{er.vwap_ny:.8f}`\n"
        f"• RSI 1m / 5m: `{er.rsi_1m:.2f}` / `{er.rsi_5m:.2f}`\n"
        f"• MACD hist 15m: `{er.macd_hist_15m:.8f}`\n"
        f"• 24h Change: `{er.change_24h_pct:+.2f}%`\n"
        f"• Market Cap: `${er.market_cap_usd:,.0f}`\n"
        f"• Flags: `compression={er.flags.get('compression', False)} | impulse={er.flags.get('impulse', False)} | pullback={er.flags.get('pullback', False)} | accel={er.flags.get('acceleration', False)}`\n\n"
        f"{premium_execution_plan(er, regime_name=regime_name, sector_count=sector_count, sector_strong=sector_strong)}\n"
        f"**Single Hard Stop:** `{build_single_hard_stop(er)}`\n"
    )
    return msg


# =========================
# CONTENT-READY OUTPUT LAYER
# =========================

CONTENT_POST_TOP_N = 3
CONTENT_POST_WRITE_FILE = True
CONTENT_POST_PATH = "scanner_content_post.txt"
CONTENT_POST_HISTORY_PATH = "scanner_content_history.txt"


# Visual radar image output
RADAR_IMAGE_ENABLED = True
RADAR_IMAGE_PATH = "scanner_radar_report.png"
RADAR_IMAGE_HISTORY_DIR = "scanner_radar_history"
RADAR_IMAGE_SEND_TO_WATCH_ON_PREALERT = True
RADAR_IMAGE_SEND_TO_MAIN_ON_TRADE_READY = True
RADAR_IMAGE_SEND_TO_WATCH_EACH_CYCLE = False  # keep False to avoid Discord spam

# Clean free Discord radar posting. This sends the visual image only when the
# market state/top 3/timing changes, or after a minimum cooldown.
RADAR_FREE_POST_ENABLED = True
RADAR_FREE_POST_ON_CHANGE_ONLY = True
RADAR_FREE_MIN_SECONDS_BETWEEN_POSTS = 8 * 60
RADAR_FREE_SEND_ON_ON_TIME = True
RADAR_FREE_SEND_ON_MARKET_STATE_CHANGE = True
RADAR_FREE_SEND_ON_TOP3_CHANGE = True

RADAR_IMAGE_WIDTH = 1080
RADAR_IMAGE_HEIGHT = 1500

radar_free_last_signature: Optional[str] = None
radar_free_last_state: Optional[str] = None
radar_free_last_sent_at: float = 0.0


def content_regime_label(regime_name: str) -> str:
    mapping = {
        "BULL_ATTACK": "BULL",
        "WATCH": "PREBULL",
        "BEAR": "BEAR",
        "EXPANSION": "EXPANSION",
        "ACCUMULATION": "ACCUMULATION",
        "DISTRIBUTION": "DISTRIBUTION",
        "EXHAUSTION": "EXHAUSTION",
        "CHOP": "CHOP",
    }
    return mapping.get(regime_name, regime_name)


def content_signal_tag(er: "EvalResult", regime_name: str, item: Optional[dict] = None) -> str:
    if regime_name == "BEAR":
        return "SHARPSHOOTER" if er.trigger_score >= 80 and er.flags.get("trend_ok", False) and er.flags.get("vwap_accept", False) else "WATCHLIST"
    if er.trade_ready:
        return "BULL"
    return "PREBUILD"


def translate_signal(er: "EvalResult") -> str:
    if er.flags.get("acceleration", False):
        momentum = "momentum is increasing"
    elif er.flags.get("impulse", False):
        momentum = "a strong move just happened"
    else:
        momentum = "momentum is building slowly"

    if er.flags.get("pullback", False):
        structure = "it is pulling back after the move"
    elif er.flags.get("structure_break", False):
        structure = "it is breaking structure upward"
    else:
        structure = "it is still trying to prove structure"

    if er.flags.get("vwap_accept", False):
        control = "buyers are holding control above VWAP"
    else:
        control = "buyers have not fully taken VWAP control yet"

    return f"{momentum}, {structure}, and {control}."


def explain_why_it_matters(er: "EvalResult", regime_name: str, item: Optional[dict] = None) -> str:
    tag = content_signal_tag(er, regime_name, item)
    if tag == "BULL":
        return "This is aligned with the stronger market tape, so continuation has cleaner odds."
    if tag == "SHARPSHOOTER":
        return "BTC is weak, but this name is showing independent strength; that can reveal rotation before the crowd sees it."
    if er.flags.get("vwap_accept", False) and er.flags.get("trend_ok", False):
        return "The setup is forming because trend and buyer control are starting to line up."
    return "The move is on the radar, but it still needs cleaner confirmation before it deserves action."


def explain_what_watching(er: "EvalResult", regime_name: str, item: Optional[dict] = None) -> str:
    tag = content_signal_tag(er, regime_name, item)
    if tag == "BULL":
        return "A clean continuation hold above VWAP with momentum staying intact."
    if tag == "SHARPSHOOTER":
        return "A quick VWAP hold or pullback reclaim only; no chasing."
    if er.flags.get("pullback", False):
        return "Whether the pullback holds and buyers step back in."
    return "A controlled pullback or clean higher-low before entry."


def build_content_post(top_setups: List[dict], regime_name: str, cycle_time: Optional[str] = None) -> str:
    state = content_regime_label(regime_name)
    cycle_time = cycle_time or dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: List[str] = []
    lines.append(f"📊 MARKET STATE: {state}")
    lines.append(f"Time: {cycle_time}")
    lines.append("")

    if state in {"BULL", "EXPANSION"}:
        lines.append("Plain English: clean expansion. Continuation trades can work, but timing still matters.")
    elif state in {"PREBULL", "ACCUMULATION"}:
        lines.append("Plain English: base-building. Setups are forming; pullback confirmation matters.")
    elif state == "DISTRIBUTION":
        lines.append("Plain English: price is elevated but momentum is weakening. Sharpshooter only.")
    elif state == "EXHAUSTION":
        lines.append("Plain English: market is stretched. Avoid chasing and wait for reset.")
    else:
        lines.append("Plain English: no clean regime. I’m only watching elite outliers, not forcing trades.")

    lines.append("")
    lines.append("━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("🎯 TOP SETUPS")
    lines.append("")

    if not top_setups:
        lines.append("No clean setups this cycle. Cash is a position.")
        lines.append("")
    else:
        for i, item in enumerate(top_setups[:CONTENT_POST_TOP_N], start=1):
            er = item["er"]
            tag = content_signal_tag(er, regime_name, item)
            eff_trade = item.get("effective_trade_score", er.trade_score)
            readiness = item.get("entry_readiness_label", "WATCH")
            readiness_score = item.get("entry_readiness_score", 0)

            lines.append(f"{i}. {er.wsname} ({tag})")
            lines.append(f"→ What it’s doing: {translate_signal(er)}")
            lines.append(f"→ Why it matters: {explain_why_it_matters(er, regime_name, item)}")
            lines.append(f"→ What I’m watching: {explain_what_watching(er, regime_name, item)}")
            lines.append(f"→ Scanner read: T{er.trigger_score} / TR{eff_trade} / C{er.confidence} | Readiness {readiness_score}/100 ({readiness})")
            lines.append(f"→ Quality filter: Momentum={getattr(er, 'momentum_quality', 'UNKNOWN')} | Trap risk={getattr(er, 'trap_risk', 'LOW')}")
            lines.append("")

    lines.append("━━━━━━━━━━━━━━━━")
    lines.append("")
    lines.append("🧠 HOW TO READ THIS")
    lines.append("PREBUILD = setup forming, not automatic entry")
    lines.append("BULL = market and setup aligned")
    lines.append("SHARPSHOOTER = strong coin in a weak market; smaller size only")
    lines.append("")
    lines.append("This is not financial advice. It is a live market-read journal from my scanner.")

    return "\n".join(lines)


def write_content_post(content_post: str) -> None:
    if not CONTENT_POST_WRITE_FILE:
        return
    try:
        with open(CONTENT_POST_PATH, "w", encoding="utf-8") as f:
            f.write(content_post + "\n")
        with open(CONTENT_POST_HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write("\n" + "=" * 72 + "\n")
            f.write(content_post + "\n")
    except Exception as e:
        print(f"[{ts()}] Content post write failed: {e}")


# =========================
# RADAR APP JSON EXPORT
# =========================

RADAR_STATE_JSON_PATH = "radar_state.json"
RADAR_STATE_HISTORY_PATH = "radar_state_history.jsonl"

# =========================
# CLOUD DATA PIPELINE
# =========================
# Clean bridge for Streamlit Cloud:
# Scanner writes radar_state.json locally, then pushes the same JSON to GitHub.
# Streamlit Cloud reads radar_state.json from GitHub.
#
# Required on your local scanner PC:
#   $env:GITHUB_RADAR_TOKEN = "your_github_token"
#
# Optional overrides:
#   $env:GITHUB_RADAR_REPO = "Trans3o/a-plus-live-radar"
#   $env:GITHUB_RADAR_BRANCH = "main"
#   $env:GITHUB_RADAR_PATH = "radar_state.json"

CLOUD_PUSH_ENABLED = os.getenv("CLOUD_PUSH_ENABLED", "1").strip() != "0"
GITHUB_RADAR_TOKEN = os.getenv("GITHUB_RADAR_TOKEN", "").strip()

def normalize_github_repo(repo: str) -> str:
    """Protect against old env values from earlier app versions."""
    repo = (repo or "Trans3o/a-plus-live-radar").strip()
    if repo == "Trans3/a-plus-live-radar":
        return "Trans3o/a-plus-live-radar"
    return repo

GITHUB_RADAR_REPO = normalize_github_repo(os.getenv("GITHUB_RADAR_REPO", "Trans3/a-plus-live-radar"))
GITHUB_RADAR_BRANCH = os.getenv("GITHUB_RADAR_BRANCH", "main").strip()
GITHUB_RADAR_PATH = os.getenv("GITHUB_RADAR_PATH", "radar_state.json").strip()
CLOUD_PUSH_MIN_SECONDS = int(os.getenv("CLOUD_PUSH_MIN_SECONDS", "15"))

_last_cloud_push_ts = 0.0
_last_cloud_push_hash = ""
_cloud_config_warning_printed = False


def _json_safe_number(value, default=0.0):
    try:
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def _pct_change_from_list(values):
    try:
        vals = [float(v) for v in (values or []) if v is not None and float(v) > 0]
        if len(vals) < 2 or vals[0] <= 0:
            return 0.0
        return (vals[-1] - vals[0]) / vals[0] * 100.0
    except Exception:
        return 0.0


def _chart_read_for_app(er):
    p30 = er.close_30m_tail or []
    p1h = er.close_1h_tail or []
    ch30 = _pct_change_from_list(p30)
    ch1h = _pct_change_from_list(p1h)

    if er.flags.get("pullback", False) and er.flags.get("vwap_accept", False):
        read_30m = "Pullback holding VWAP"
    elif er.flags.get("acceleration", False):
        read_30m = "Momentum burst"
    elif er.flags.get("impulse", False):
        read_30m = "Fresh impulse"
    elif ch30 > 0.25:
        read_30m = "Building upward"
    elif ch30 < -0.25:
        read_30m = "Cooling off"
    else:
        read_30m = "Range building"

    if er.flags.get("trend_ok", False) and ch1h >= 0:
        read_1h = "Trend intact"
    elif er.flags.get("trend_ok", False):
        read_1h = "Trend trying to hold"
    elif ch1h > 0.5:
        read_1h = "Strong but needs proof"
    elif ch1h < -0.5:
        read_1h = "Weak 1H structure"
    else:
        read_1h = "No clean 1H trend"

    if er.rsi_1m > 72 and not er.flags.get("pullback", False):
        timing = "LATE"
    elif er.flags.get("pullback", False) and er.flags.get("vwap_accept", False):
        timing = "ON TIME"
    elif er.flags.get("impulse", False) or er.flags.get("acceleration", False):
        timing = "EARLY"
    elif not er.flags.get("vwap_accept", False):
        timing = "WAIT"
    else:
        timing = "WATCH"

    return {
        "read_30m": read_30m,
        "read_1h": read_1h,
        "timing": timing,
        "change_30m_pct": round(ch30, 3),
        "change_1h_pct": round(ch1h, 3),
    }


def export_radar_state_json(
    top_setups,
    regime_name,
    regime,
    active_pairs,
    cycle_number,
    sector_counts=None,
    state_counts=None,
    output_path=RADAR_STATE_JSON_PATH,
):
    """Write the latest scanner state to JSON for radar_app.py."""
    sector_counts = sector_counts or {}
    state_counts = state_counts or {}
    now_iso = dt.datetime.now().isoformat(timespec="seconds")
    state_label = content_regime_label(regime_name)

    setups = []
    for rank, item in enumerate((top_setups or [])[:10], start=1):
        er = item.get("er")
        if not er:
            continue
        chart_read = _chart_read_for_app(er)
        eff_trade = int(item.get("effective_trade_score", er.trade_score))
        setups.append({
            "rank": rank,
            "pair": er.wsname,
            "coin": er.wsname.split("/")[0],
            "tag": content_signal_tag(er, regime_name, item),
            "price": _json_safe_number(er.price),
            "change_24h_pct": round(_json_safe_number(er.change_24h_pct), 3),
            "trigger_score": int(er.trigger_score),
            "trade_score": int(eff_trade),
            "confidence": int(er.confidence),
            "entry_readiness_score": int(item.get("entry_readiness_score", 0)),
            "entry_readiness_label": item.get("entry_readiness_label", "WATCH"),
            "sector": er.sector,
            "state": item.get("state", ""),
            "blocker": item.get("blocker", ""),
            "flags": {k: bool(v) for k, v in (er.flags or {}).items()},
            "missing": list(er.missing or []),
            "rsi_1m": round(_json_safe_number(er.rsi_1m), 3),
            "rsi_5m": round(_json_safe_number(er.rsi_5m), 3),
            "vwap": _json_safe_number(er.vwap_ny),
            "macd_hist_15m": _json_safe_number(er.macd_hist_15m),
            "close_30m": [round(_json_safe_number(x), 10) for x in (er.close_30m_tail or [])],
            "close_1h": [round(_json_safe_number(x), 10) for x in (er.close_1h_tail or [])],
            "chart_read": chart_read,
            "momentum_quality": getattr(er, "momentum_quality", "UNKNOWN"),
            "trap_risk": getattr(er, "trap_risk", "LOW"),
            "volatility_state": getattr(er, "volatility_state", "UNKNOWN"),
            "structure_type": getattr(er, "structure_type", "UNKNOWN"),
            "relative_strength_pct": round(_json_safe_number(getattr(er, "relative_strength_pct", 0.0)), 3),
            "distance_from_vwap_pct": round(_json_safe_number(getattr(er, "distance_from_vwap_pct", 0.0)), 3),
            "composite_score": int(getattr(er, "composite_score", 0)),
            "environment_score": int(item.get("environment_score", getattr(er, "composite_score", 0))),
            "environment_tier": item.get("environment_tier", "UNKNOWN"),
            "environment_adjustments": item.get("environment_adjustments", []),
            "billboard_score": int(item.get("billboard_score", 0)),
            "billboard_penalty": int(item.get("billboard_penalty", 0)),
            "billboard_reasons": list(item.get("billboard_reasons", [])),
            "veteran_decision": getattr(er, "veteran_decision", "IGNORE"),
            "position_size": getattr(er, "position_size", "NO TRADE"),
            "decision_reason": getattr(er, "decision_reason", "no clean edge yet"),
            "caption": translate_signal(er),
        })

    payload = {
        "generated_at": now_iso,
        "cycle_number": int(cycle_number or 0),
        "active_pairs": int(active_pairs or 0),
        "market_state": state_label,
        "regime_name": regime_name,
        "btc": {
            "reason": regime.get("reason", "") if isinstance(regime, dict) else "",
            "market_phase": regime.get("market_phase", regime_name) if isinstance(regime, dict) else regime_name,
            "volatility_state": regime.get("volatility_state", "UNKNOWN") if isinstance(regime, dict) else "UNKNOWN",
            "price_5m": _json_safe_number(regime.get("price_5m", 0.0)) if isinstance(regime, dict) else 0.0,
            "price_15m": _json_safe_number(regime.get("price_15m", 0.0)) if isinstance(regime, dict) else 0.0,
            "price_60m": _json_safe_number(regime.get("price_60m", 0.0)) if isinstance(regime, dict) else 0.0,
            "rsi_15m": round(_json_safe_number(regime.get("rsi_15m", 0.0)), 2) if isinstance(regime, dict) else 0.0,
            "rsi_60m": round(_json_safe_number(regime.get("rsi_60m", 0.0)), 2) if isinstance(regime, dict) else 0.0,
            "above_vwap_15m": bool(regime.get("above_vwap_15m", False)) if isinstance(regime, dict) else False,
            "above_vwap_60m": bool(regime.get("above_vwap_60m", False)) if isinstance(regime, dict) else False,
        },
        "sector_counts": dict(sector_counts),
        "state_counts": dict(state_counts),
        "billboard": {
            "one_hour": list((LAST_BILLBOARD_SNAPSHOT or {}).get("one_hour", [])),
            "twenty_four_hour": list((LAST_BILLBOARD_SNAPSHOT or {}).get("twenty_four_hour", [])),
            "note": "1H board is primary. 24H board is context only.",
        },
        "top_setups": setups,
    }

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        with open(RADAR_STATE_HISTORY_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload) + "\n")
        return True
    except Exception as e:
        print(f"[{ts()}] Radar JSON export failed: {e}")
        return False


def push_radar_state_to_github(path: str = RADAR_STATE_JSON_PATH, force: bool = False) -> bool:
    """Push radar_state.json to GitHub so Streamlit Cloud can read live scanner data.

    Uses GitHub Contents API. The token should be stored in the environment, never in code.
    This function throttles pushes and skips unchanged JSON to avoid commit spam.
    """
    global _last_cloud_push_ts, _last_cloud_push_hash, _cloud_config_warning_printed

    if not CLOUD_PUSH_ENABLED:
        return False

    if not GITHUB_RADAR_TOKEN or not GITHUB_RADAR_REPO:
        if not _cloud_config_warning_printed:
            print(f"[{ts()}] Cloud push OFF: token_set={bool(GITHUB_RADAR_TOKEN)} repo={GITHUB_RADAR_REPO!r}. Set GITHUB_RADAR_TOKEN to publish radar_state.json to GitHub.")
            _cloud_config_warning_printed = True
        return False

    try:
        with open(path, "rb") as f:
            raw = f.read()
    except Exception as e:
        print(f"[{ts()}] Cloud push skipped: could not read {path}: {e}")
        return False

    current_hash = hashlib.sha256(raw).hexdigest()
    now = time.time()
    if not force:
        if current_hash == _last_cloud_push_hash:
            return False
        if (now - _last_cloud_push_ts) < CLOUD_PUSH_MIN_SECONDS:
            return False

    api_url = f"https://api.github.com/repos/{GITHUB_RADAR_REPO}/contents/{GITHUB_RADAR_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_RADAR_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "a-plus-radar-scanner",
    }

    sha = None
    try:
        get_resp = requests.get(api_url, headers=headers, params={"ref": GITHUB_RADAR_BRANCH}, timeout=15)
        if get_resp.status_code == 200:
            sha = (get_resp.json() or {}).get("sha")
        elif get_resp.status_code not in (404,):
            print(f"[{ts()}] Cloud push lookup warning: HTTP {get_resp.status_code} {get_resp.text[:120]}")
    except Exception as e:
        print(f"[{ts()}] Cloud push lookup failed: {e}")

    payload = {
        "message": f"update radar state {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": GITHUB_RADAR_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    try:
        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=20)
        if 200 <= put_resp.status_code < 300:
            _last_cloud_push_ts = now
            _last_cloud_push_hash = current_hash
            print(f"[{ts()}] Cloud radar_state.json pushed to GitHub ({GITHUB_RADAR_REPO}/{GITHUB_RADAR_PATH})")
            return True
        print(f"[{ts()}] Cloud push failed: HTTP {put_resp.status_code} {put_resp.text[:180]}")
        return False
    except Exception as e:
        print(f"[{ts()}] Cloud push failed: {e}")
        return False



# =========================
# PERSISTENT PERFORMANCE ENGINE
# =========================
# Scanner-side tracking so the website can show real outcomes instead of
# browser-session placeholders.

PERFORMANCE_JSON_PATH = os.getenv("PERFORMANCE_JSON_PATH", "radar_performance.json").strip()
GITHUB_PERFORMANCE_PATH = os.getenv("GITHUB_PERFORMANCE_PATH", "radar_performance.json").strip()
PERF_TOP_N = int(os.getenv("PERF_TOP_N", "5"))
PERF_HIT_1_PCT = float(os.getenv("PERF_HIT_1_PCT", "1.0"))
PERF_HIT_2_PCT = float(os.getenv("PERF_HIT_2_PCT", "2.0"))
PERF_DRAWDOWN_FAIL_PCT = float(os.getenv("PERF_DRAWDOWN_FAIL_PCT", "-1.2"))
PERF_INACTIVE_AFTER_SECONDS = int(os.getenv("PERF_INACTIVE_AFTER_SECONDS", str(30 * 60)))
PERF_MAX_RECORDS = int(os.getenv("PERF_MAX_RECORDS", "250"))


def _load_performance_payload(path: str = PERFORMANCE_JSON_PATH) -> dict:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    data.setdefault("records", [])
                    data.setdefault("summary", {})
                    return data
    except Exception as e:
        print(f"[{ts()}] Performance load warning: {e}")
    return {"generated_at": "", "summary": {}, "records": []}


def _perf_record_status(max_gain: float, drawdown: float) -> str:
    if max_gain >= PERF_HIT_2_PCT:
        return "HIT +2%"
    if max_gain >= PERF_HIT_1_PCT:
        return "HIT +1%"
    if drawdown <= PERF_DRAWDOWN_FAIL_PCT:
        return "DRAWDOWN"
    return "OPEN"


def _summarize_performance(records: list) -> dict:
    total = len(records)
    hit1 = sum(1 for r in records if safe_float(r.get("max_gain_pct")) >= PERF_HIT_1_PCT)
    hit2 = sum(1 for r in records if safe_float(r.get("max_gain_pct")) >= PERF_HIT_2_PCT)
    dd = sum(1 for r in records if safe_float(r.get("max_drawdown_pct")) <= PERF_DRAWDOWN_FAIL_PCT)
    avg_max = sum(safe_float(r.get("max_gain_pct")) for r in records) / total if total else 0.0
    best = max(records, key=lambda r: safe_float(r.get("max_gain_pct")), default={})
    open_count = sum(1 for r in records if r.get("status") == "OPEN")
    return {
        "total_signals": total,
        "open_signals": open_count,
        "hit_1pct_count": hit1,
        "hit_2pct_count": hit2,
        "drawdown_count": dd,
        "hit_1pct_rate": round((hit1 / total * 100.0), 2) if total else 0.0,
        "hit_2pct_rate": round((hit2 / total * 100.0), 2) if total else 0.0,
        "avg_max_move_pct": round(avg_max, 3),
        "best_pair": best.get("pair", "—"),
        "best_move_pct": round(safe_float(best.get("max_gain_pct")), 3) if best else 0.0,
    }





def _rsi_zone(value) -> str:
    rsi = safe_float(value)
    if rsi <= 0:
        return "UNKNOWN"
    if rsi < 50:
        return "RSI <50"
    if rsi < 56:
        return "RSI 50-55"
    if rsi <= 62:
        return "RSI 56-62"
    if rsi <= 70:
        return "RSI 63-70"
    if rsi <= 75:
        return "RSI 71-75"
    return "RSI >75 HOT"


def _vwap_distance_zone(value) -> str:
    dist = safe_float(value)
    if dist < -0.5:
        return "Below VWAP"
    if dist <= 0.5:
        return "VWAP +/-0.5%"
    if dist <= 1.25:
        return "VWAP +0.5-1.25%"
    if dist <= 2.25:
        return "VWAP +1.25-2.25%"
    return "Extended >2.25%"


def _hour_bucket_from_iso(value: str) -> str:
    try:
        dt_obj = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return f"{dt_obj.hour:02d}:00"
    except Exception:
        return "UNKNOWN"


def _score_zone(value) -> str:
    score = safe_float(value)
    if score >= 90:
        return "90-100"
    if score >= 80:
        return "80-89"
    if score >= 70:
        return "70-79"
    if score >= 60:
        return "60-69"
    return "<60"


def _performance_bucket_rates(records: list, field: str, top_n: int = 10) -> list:
    """Return compact win-rate buckets for regime/timing/sector analytics."""
    buckets = {}
    for r in records:
        key = str(r.get(field, "UNKNOWN") or "UNKNOWN")
        b = buckets.setdefault(key, {
            "name": key,
            "total": 0,
            "hit_1pct": 0,
            "hit_2pct": 0,
            "drawdown": 0,
            "avg_max_move_pct": 0.0,
            "avg_drawdown_pct": 0.0,
            "avg_current_pct": 0.0,
        })
        b["total"] += 1
        max_gain = safe_float(r.get("max_gain_pct"))
        drawdown = safe_float(r.get("max_drawdown_pct"))
        current = safe_float(r.get("current_pct"))
        if max_gain >= PERF_HIT_1_PCT:
            b["hit_1pct"] += 1
        if max_gain >= PERF_HIT_2_PCT:
            b["hit_2pct"] += 1
        if drawdown <= PERF_DRAWDOWN_FAIL_PCT:
            b["drawdown"] += 1
        b["avg_max_move_pct"] += max_gain
        b["avg_drawdown_pct"] += drawdown
        b["avg_current_pct"] += current

    rows = []
    for b in buckets.values():
        total = max(1, int(b["total"]))
        hit2_rate = b["hit_2pct"] / total * 100.0
        drawdown_rate = b["drawdown"] / total * 100.0
        avg_max = b["avg_max_move_pct"] / total
        avg_dd = b["avg_drawdown_pct"] / total
        rows.append({
            "name": b["name"],
            "total": b["total"],
            "hit_1pct_rate": round(b["hit_1pct"] / total * 100.0, 2),
            "hit_2pct_rate": round(hit2_rate, 2),
            "drawdown_rate": round(drawdown_rate, 2),
            "avg_max_move_pct": round(avg_max, 3),
            "avg_drawdown_pct": round(avg_dd, 3),
            "avg_current_pct": round(b["avg_current_pct"] / total, 3),
            "edge_score": round((hit2_rate * 0.55) + (avg_max * 12.0) - (drawdown_rate * 0.35) + (avg_dd * 4.0), 2),
        })
    return sorted(rows, key=lambda x: (x["edge_score"], x["total"], x["hit_2pct_rate"]), reverse=True)[:top_n]


def _summarize_performance_plus(records: list) -> dict:
    """Main summary plus proof buckets for selling/testing."""
    summary = _summarize_performance(records)
    summary["by_regime"] = _performance_bucket_rates(records, "regime_first")
    summary["by_timing"] = _performance_bucket_rates(records, "timing_first")
    summary["by_sector"] = _performance_bucket_rates(records, "sector")
    summary["by_tag"] = _performance_bucket_rates(records, "tag")
    summary["by_setup_type"] = _performance_bucket_rates(records, "setup_type")
    summary["by_rsi_zone"] = _performance_bucket_rates(records, "rsi_zone")
    summary["by_vwap_distance"] = _performance_bucket_rates(records, "vwap_distance_zone")
    summary["by_hour"] = _performance_bucket_rates(records, "hour_bucket", top_n=24)
    summary["by_veteran_decision"] = _performance_bucket_rates(records, "veteran_decision")
    summary["by_position_size"] = _performance_bucket_rates(records, "position_size")
    summary["by_environment_tier"] = _performance_bucket_rates(records, "environment_tier_first")
    summary["proof_read"] = {
        "best_regime": (summary.get("by_regime") or [{}])[0].get("name", "UNKNOWN"),
        "best_timing": (summary.get("by_timing") or [{}])[0].get("name", "UNKNOWN"),
        "best_sector": (summary.get("by_sector") or [{}])[0].get("name", "UNKNOWN"),
        "best_setup_type": (summary.get("by_setup_type") or [{}])[0].get("name", "UNKNOWN"),
        "sample_warning": "Treat buckets under 30 samples as directional, not proven.",
    }
    return summary




# =========================
# ENVIRONMENT WEIGHTING ENGINE
# =========================

def environment_weight_score(
    er,
    regime_name,
    sector_count=0,
    sector_strong=False,
    entry_readiness_score=0,
    entry_readiness_label="WATCH",
):
    """Context-aware probability score.

    Starts from the scanner's composite score, then adjusts based on the
    trading environment. This makes ranking closer to a veteran trader's read:
    same setup, different regime = different odds.
    """
    score = int(getattr(er, "composite_score", 0) or 0)
    adjustments = []

    def add(reason: str, points: int):
        nonlocal score
        score += int(points)
        adjustments.append({"reason": reason, "points": int(points)})

    # Regime weighting
    if regime_name in {"EXPANSION", "BULL_ATTACK"}:
        add("Expansion regime", 12)
    elif regime_name in {"ACCUMULATION", "WATCH"}:
        add("Accumulation regime", 4)
    elif regime_name == "DISTRIBUTION":
        add("Distribution risk", -10)
    elif regime_name in {"EXHAUSTION", "CHOP", "BEAR"}:
        add("Weak regime", -18)

    # Sector flow
    if sector_strong:
        add("Strong sector", 10)
    elif int(sector_count or 0) >= 2:
        add("Sector support", 5)
    else:
        add("Weak sector", -4)

    # Entry timing/readiness
    label = str(entry_readiness_label or "WATCH").upper()
    if label in {"OPTIMAL", "ON TIME"} or int(entry_readiness_score or 0) >= 80:
        add("Optimal timing", 10)
    elif label == "READY SOON" or int(entry_readiness_score or 0) >= 65:
        add("Good timing", 5)
    elif label == "EARLY":
        add("Early setup", -2)
    elif label in {"LATE", "TOO LATE"}:
        add("Late entry risk", -12)

    # Volatility state
    vol_state = str(getattr(er, "volatility_state", "UNKNOWN") or "UNKNOWN").upper()
    if vol_state in {"EXPANDING", "EXPANSION"}:
        add("Volatility expansion", 8)
    elif vol_state in {"COMPRESSED", "COMPRESSING"}:
        add("Compression potential", 4)
    elif vol_state in {"ERRATIC", "CHAOTIC"}:
        add("Erratic volatility", -8)

    # Momentum quality
    momentum_quality = str(getattr(er, "momentum_quality", "UNKNOWN") or "UNKNOWN").upper()
    if momentum_quality in {"STRONG", "BUILDING"}:
        add("Positive momentum", 8)
    elif momentum_quality in {"FAILING", "WEAKENING"}:
        add("Momentum failing", -14)

    # VWAP distance: value is generally better than chase distance
    dist = abs(safe_float(getattr(er, "distance_from_vwap_pct", 0.0)))
    if dist <= 0.35:
        add("Near VWAP", 6)
    elif dist >= 2.0:
        add("Extended from VWAP", -10)

    # Relative strength
    rs = safe_float(getattr(er, "relative_strength_pct", 0.0))
    if rs >= 1.5:
        add("Relative strength leader", 8)
    elif rs <= -1.0:
        add("Weak vs market", -8)

    # Hard penalties
    if str(getattr(er, "trap_risk", "LOW") or "LOW").upper() == "HIGH":
        add("Trap risk", -20)
    if not getattr(er, "flags", {}).get("vwap_accept", False):
        add("No VWAP hold", -8)
    if not getattr(er, "flags", {}).get("trend_ok", False):
        add("Trend not aligned", -8)

    final_score = max(0, min(100, int(score)))
    if final_score >= 90:
        tier = "ELITE"
    elif final_score >= 80:
        tier = "A+"
    elif final_score >= 70:
        tier = "B"
    elif final_score >= 60:
        tier = "C"
    else:
        tier = "AVOID"

    return {
        "final_score": final_score,
        "tier": tier,
        "adjustments": adjustments,
    }


# =========================
# BILLBOARD QUALITY FILTER
# =========================

def billboard_quality_filter(er, min_score: int = 55) -> dict:
    """Filter noisy movers before they reach the site/watchboard.

    Goal: keep the billboard as a tradability radar, not a random movers board.
    A coin can still be scanned, but weak/extended/trappy names do not get
    promoted into the visual top list.
    """
    allow = True
    penalty = 0
    reasons = []

    def reject(reason: str):
        nonlocal allow
        allow = False
        reasons.append(reason)

    def penalize(reason: str, points: int):
        nonlocal penalty
        penalty += int(points)
        reasons.append(f"{reason} -{int(points)}")

    flags = getattr(er, "flags", {}) or {}
    momentum = str(getattr(er, "momentum_quality", "UNKNOWN") or "UNKNOWN").upper()
    trap = str(getattr(er, "trap_risk", "LOW") or "LOW").upper()

    # Hard quality gates.
    if not flags.get("trend_ok", False):
        reject("trend not aligned")
    if not flags.get("vwap_accept", False):
        reject("no VWAP hold")
    if momentum == "FAILING":
        reject("momentum failing")
    if trap == "HIGH":
        reject("high trap risk")

    # Soft penalties: still visible if the score is strong enough.
    if safe_float(getattr(er, "rsi_1m", 0.0)) >= 74:
        penalize("RSI extended", 10)
    if not flags.get("pullback", False):
        penalize("no pullback", 8)
    if not flags.get("volume_spike", False):
        penalize("weak volume", 6)
    if not flags.get("structure_break", False):
        penalize("no structure break", 6)

    distance_from_vwap = abs(safe_float(getattr(er, "distance_from_vwap_pct", 0.0)))
    if distance_from_vwap >= 2.25:
        penalize("extended from VWAP", 15)

    if safe_float(getattr(er, "relative_strength_pct", 0.0)) <= -1:
        penalize("weak relative strength", 12)

    base_score = int(getattr(er, "trigger_score", 0) or 0)
    score = max(0, base_score - penalty)
    if score < int(min_score):
        allow = False
        reasons.append(f"billboard score below {int(min_score)}")

    return {
        "allow": bool(allow),
        "score": int(score),
        "penalty": int(penalty),
        "reasons": reasons[:8],
    }


def update_performance_history(top_setups: list, cycle_number: int, regime_name: str, path: str = PERFORMANCE_JSON_PATH) -> bool:
    """Persistent scanner-side outcome tracking.

    This is the proof layer. Every top setup gets an episode record, then each
    cycle updates what happened after the setup appeared:
    - current move
    - max move
    - max drawdown
    - +1% / +2% hit status
    - inactive status after it disappears

    Important: this creates a NEW episode after an old setup goes inactive.
    That prevents a pair like XMR/USD from being merged into one giant forever
    record across different days and regimes.
    """
    now_dt = dt.datetime.now()
    now_iso = now_dt.isoformat(timespec="seconds")
    now_ts = time.time()
    payload = _load_performance_payload(path)
    records = payload.get("records", []) if isinstance(payload.get("records", []), list) else []

    # Find the latest still-active episode for each pair/tag. Older inactive or
    # resolved records remain preserved as proof history.
    active_by_key = {}
    for r in sorted(records, key=lambda x: x.get("last_seen", ""), reverse=True):
        active_key = r.get("active_key") or r.get("key")
        if not active_key:
            continue
        status = str(r.get("status", "OPEN")).upper()
        last_ts = safe_float(r.get("last_seen_ts"), 0.0)
        still_live = status == "OPEN" and (now_ts - last_ts) < PERF_INACTIVE_AFTER_SECONDS
        if still_live and active_key not in active_by_key:
            active_by_key[active_key] = r

    seen_active_keys = set()

    for rank, item in enumerate((top_setups or [])[:PERF_TOP_N], start=1):
        er = item.get("er") if isinstance(item, dict) else None
        if not er:
            continue

        price = safe_float(getattr(er, "price", 0.0))
        if price <= 0:
            continue

        tag = content_signal_tag(er, regime_name, item)
        active_key = f"{er.wsname}|{tag}"
        seen_active_keys.add(active_key)

        try:
            chart_read = _chart_read_for_app(er)
            timing = chart_read.get("timing", item.get("entry_readiness_label", "WATCH"))
        except Exception:
            chart_read = {}
            timing = item.get("entry_readiness_label", "WATCH")

        rec = active_by_key.get(active_key)
        if rec is None:
            # Episode key is unique enough for proof while still readable.
            episode_id = f"{active_key}|cycle-{int(cycle_number or 0)}|{int(now_ts)}"
            rec = {
                "key": episode_id,
                "active_key": active_key,
                "pair": er.wsname,
                "coin": er.wsname.split("/")[0],
                "tag": tag,
                "first_seen": now_iso,
                "first_seen_ts": now_ts,
                "first_cycle": int(cycle_number or 0),
                "entry_price": price,
                "max_price_after": price,
                "min_price_after": price,
                "last_price": price,
                "last_seen": now_iso,
                "last_seen_ts": now_ts,
                "rank_first": rank,
                "rank_best": rank,
                "rank_last": rank,
                "regime_first": regime_name,
                "regime_last": regime_name,
                "timing_first": timing,
                "timing_last": timing,
                "trigger_score": int(getattr(er, "trigger_score", 0)),
                "trade_score": int(item.get("effective_trade_score", getattr(er, "trade_score", 0))),
                "confidence": int(getattr(er, "confidence", 0)),
                "environment_score_first": int(item.get("environment_score", getattr(er, "composite_score", 0))),
                "environment_tier_first": item.get("environment_tier", "UNKNOWN"),
                "sector": getattr(er, "sector", "OTHER"),
                "setup_type": classify_execution_plan(er, regime_name),
                "veteran_decision": getattr(er, "veteran_decision", "IGNORE"),
                "position_size": getattr(er, "position_size", "NO TRADE"),
                "rsi_1m_first": round(safe_float(getattr(er, "rsi_1m", 0.0)), 3),
                "rsi_5m_first": round(safe_float(getattr(er, "rsi_5m", 0.0)), 3),
                "macd_hist_15m_first": round(safe_float(getattr(er, "macd_hist_15m", 0.0)), 8),
                "distance_from_vwap_pct_first": round(safe_float(getattr(er, "distance_from_vwap_pct", 0.0)), 3),
                "rsi_zone": _rsi_zone(getattr(er, "rsi_1m", 0.0)),
                "vwap_distance_zone": _vwap_distance_zone(getattr(er, "distance_from_vwap_pct", 0.0)),
                "hour_bucket": _hour_bucket_from_iso(now_iso),
                "trigger_score_zone": _score_zone(getattr(er, "trigger_score", 0)),
                "trade_score_zone": _score_zone(item.get("effective_trade_score", getattr(er, "trade_score", 0))),
                "confidence_zone": _score_zone(getattr(er, "confidence", 0)),
                "status": "OPEN",
            }
            records.append(rec)
            active_by_key[active_key] = rec

        # Update live fields.
        rec["last_price"] = price
        rec["last_seen"] = now_iso
        rec["last_seen_ts"] = now_ts
        rec["rank_last"] = rank
        rec["rank_best"] = min(int(rec.get("rank_best", rank) or rank), rank)
        rec["regime_last"] = regime_name
        rec["timing_last"] = timing
        rec["trigger_score"] = int(getattr(er, "trigger_score", rec.get("trigger_score", 0)))
        rec["trade_score"] = int(item.get("effective_trade_score", getattr(er, "trade_score", rec.get("trade_score", 0))))
        rec["confidence"] = int(getattr(er, "confidence", rec.get("confidence", 0)))
        rec["environment_score_last"] = int(item.get("environment_score", rec.get("environment_score_first", getattr(er, "composite_score", 0))))
        rec["environment_tier_last"] = item.get("environment_tier", rec.get("environment_tier_first", "UNKNOWN"))
        rec.setdefault("rsi_zone", _rsi_zone(rec.get("rsi_1m_first", getattr(er, "rsi_1m", 0.0))))
        rec.setdefault("vwap_distance_zone", _vwap_distance_zone(rec.get("distance_from_vwap_pct_first", getattr(er, "distance_from_vwap_pct", 0.0))))
        rec.setdefault("hour_bucket", _hour_bucket_from_iso(rec.get("first_seen", now_iso)))
        rec.setdefault("trigger_score_zone", _score_zone(rec.get("trigger_score", getattr(er, "trigger_score", 0))))
        rec.setdefault("trade_score_zone", _score_zone(rec.get("trade_score", item.get("effective_trade_score", getattr(er, "trade_score", 0)))))
        rec.setdefault("confidence_zone", _score_zone(rec.get("confidence", getattr(er, "confidence", 0))))
        rec["max_price_after"] = max(safe_float(rec.get("max_price_after"), price), price)
        rec["min_price_after"] = min(safe_float(rec.get("min_price_after"), price), price)
        rec["age_minutes"] = round((now_ts - safe_float(rec.get("first_seen_ts"), now_ts)) / 60.0, 2)

        entry = safe_float(rec.get("entry_price"), price)
        if entry > 0:
            max_gain = (safe_float(rec.get("max_price_after")) - entry) / entry * 100.0
            drawdown = (safe_float(rec.get("min_price_after")) - entry) / entry * 100.0
            current = (price - entry) / entry * 100.0
        else:
            max_gain = drawdown = current = 0.0

        rec["max_gain_pct"] = round(max_gain, 3)
        rec["max_move_pct"] = round(max_gain, 3)
        rec["max_drawdown_pct"] = round(drawdown, 3)
        rec["drawdown_pct"] = round(drawdown, 3)
        rec["current_pct"] = round(current, 3)
        rec["hit_1pct"] = max_gain >= PERF_HIT_1_PCT
        rec["hit_2pct"] = max_gain >= PERF_HIT_2_PCT
        rec["status"] = _perf_record_status(max_gain, drawdown)

    # Mark stale open episodes inactive but preserve wins/drawdowns.
    for rec in records:
        active_key = rec.get("active_key") or rec.get("key")
        if active_key not in seen_active_keys:
            last_ts = safe_float(rec.get("last_seen_ts"), now_ts)
            if now_ts - last_ts >= PERF_INACTIVE_AFTER_SECONDS and rec.get("status") == "OPEN":
                rec["status"] = "INACTIVE"
                rec["inactive_at"] = now_iso

    # Keep newest proof records only. The cap prevents the file from growing forever.
    records = sorted(records, key=lambda r: r.get("last_seen", ""), reverse=True)[:PERF_MAX_RECORDS]
    payload = {
        "generated_at": now_iso,
        "cycle_number": int(cycle_number or 0),
        "settings": {
            "hit_1pct": PERF_HIT_1_PCT,
            "hit_2pct": PERF_HIT_2_PCT,
            "drawdown_fail_pct": PERF_DRAWDOWN_FAIL_PCT,
            "tracked_top_n": PERF_TOP_N,
            "inactive_after_seconds": PERF_INACTIVE_AFTER_SECONDS,
            "max_records": PERF_MAX_RECORDS,
        },
        "summary": _summarize_performance_plus(records),
        "records": records,
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"[{ts()}] Performance state updated: {path} | records={len(records)}")
        return True
    except Exception as e:
        print(f"[{ts()}] Performance write failed: {e}")
        return False


def push_performance_to_github(path: str = PERFORMANCE_JSON_PATH, force: bool = False) -> bool:
    """Push radar_performance.json to GitHub using the same token/repo/branch."""
    if not CLOUD_PUSH_ENABLED:
        return False
    if not GITHUB_RADAR_TOKEN or not GITHUB_RADAR_REPO:
        return False
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except Exception as e:
        print(f"[{ts()}] Performance cloud push skipped: could not read {path}: {e}")
        return False

    api_url = f"https://api.github.com/repos/{GITHUB_RADAR_REPO}/contents/{GITHUB_PERFORMANCE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_RADAR_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "a-plus-radar-scanner",
    }
    sha = None
    try:
        get_resp = requests.get(api_url, headers=headers, params={"ref": GITHUB_RADAR_BRANCH}, timeout=15)
        if get_resp.status_code == 200:
            sha = (get_resp.json() or {}).get("sha")
        elif get_resp.status_code not in (404,):
            print(f"[{ts()}] Performance push lookup warning: HTTP {get_resp.status_code} {get_resp.text[:120]}")
    except Exception as e:
        print(f"[{ts()}] Performance push lookup failed: {e}")

    payload = {
        "message": f"update radar performance {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "content": base64.b64encode(raw).decode("ascii"),
        "branch": GITHUB_RADAR_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    try:
        put_resp = requests.put(api_url, headers=headers, json=payload, timeout=20)
        if 200 <= put_resp.status_code < 300:
            print(f"[{ts()}] Cloud radar_performance.json pushed to GitHub ({GITHUB_RADAR_REPO}/{GITHUB_PERFORMANCE_PATH})")
            return True
        print(f"[{ts()}] Performance cloud push failed: HTTP {put_resp.status_code} {put_resp.text[:180]}")
        return False
    except Exception as e:
        print(f"[{ts()}] Performance cloud push failed: {e}")
        return False

# =========================
# VISUAL RADAR IMAGE OUTPUT
# =========================

def _load_font(size: int, bold: bool = False):
    """Load a clean local font. Falls back safely if the system font is unavailable."""
    try:
        from PIL import ImageFont
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
            "arialbd.ttf" if bold else "arial.ttf",
        ]
        for fp in candidates:
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
        return ImageFont.load_default()
    except Exception:
        return None


def _safe_text(text: str, max_len: int = 64) -> str:
    text = str(text or "").replace("\n", " ").strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


def _draw_rounded(draw, box, radius, outline=None, fill=None, width=1):
    try:
        draw.rounded_rectangle(box, radius=radius, outline=outline, fill=fill, width=width)
    except Exception:
        draw.rectangle(box, outline=outline, fill=fill, width=width)


def _pct_change(prices: Optional[List[float]]) -> float:
    try:
        pts = [float(v) for v in (prices or []) if v and float(v) > 0]
        if len(pts) < 2 or pts[0] <= 0:
            return 0.0
        return (pts[-1] - pts[0]) / pts[0] * 100.0
    except Exception:
        return 0.0


def _draw_spark_chart(draw, prices, box, label: str, accent="#00FF9C"):
    """Small friendly price-action sparkline used inside the dual 30M / 1H panel."""
    x1, y1, x2, y2 = box
    draw.text((x1 + 6, y1), label, fill=accent, font=_load_font(14, True))
    chart_top = y1 + 22
    chart_bottom = y2 - 18
    chart_left = x1 + 6
    chart_right = x2 - 6

    pts = [float(v) for v in (prices or [])[-30:] if v and float(v) > 0]
    if len(pts) < 4:
        draw.text((chart_left + 4, chart_top + 22), "waiting", fill="#7A8792", font=_load_font(13))
        return

    lo, hi = min(pts), max(pts)
    if hi <= lo:
        hi = lo * 1.001

    # soft grid so beginners can read direction without being overwhelmed
    for k in range(2):
        gy = chart_top + int((chart_bottom - chart_top) * (k + 1) / 3)
        draw.line((chart_left, gy, chart_right, gy), fill="#12202A", width=1)

    coords = []
    usable_w = max(1, chart_right - chart_left)
    usable_h = max(1, chart_bottom - chart_top)
    for idx, price in enumerate(pts):
        x = chart_left + int(idx * usable_w / max(1, len(pts) - 1))
        y = chart_bottom - int((price - lo) / (hi - lo) * usable_h)
        coords.append((x, y))

    for idx in range(1, len(coords)):
        px, py = coords[idx - 1]
        cx, cy = coords[idx]
        color = accent if pts[idx] >= pts[idx - 1] else "#FF5A4D"
        draw.line((px, py, cx, cy), fill=color, width=3)
        draw.rectangle((cx - 2, cy - 3, cx + 2, cy + 3), fill=color)

    chg = _pct_change(pts)
    chg_color = accent if chg >= 0 else "#FF5A4D"
    draw.text((x1 + 6, y2 - 15), f"{chg:+.2f}%", fill=chg_color, font=_load_font(13, True))


def build_chart_read(er: "EvalResult") -> Tuple[str, str, str]:
    """Human-readable chart read: solves the intimidation problem for beginners."""
    change_30m = _pct_change(er.close_30m_tail)
    change_1h = _pct_change(er.close_1h_tail)
    dist_vwap = ((er.price - er.vwap_ny) / er.vwap_ny * 100.0) if er.vwap_ny else 0.0

    if er.flags.get("pullback", False) and er.flags.get("vwap_accept", False):
        read_30 = "Pullback holding"
    elif er.flags.get("acceleration", False):
        read_30 = "Momentum burst"
    elif change_30m > 0.45:
        read_30 = "Buyers active"
    elif change_30m < -0.35:
        read_30 = "Cooling off"
    else:
        read_30 = "Building slowly"

    if er.flags.get("trend_ok", False) and change_1h >= 0:
        read_1h = "Trend intact"
    elif change_1h > 0.75:
        read_1h = "Strong 1H push"
    elif change_1h < -0.50:
        read_1h = "Trend cooling"
    else:
        read_1h = "Needs proof"

    # Timing: the part you personally need most.
    if er.rsi_1m >= 74 or dist_vwap > 2.2:
        timing = "LATE"
    elif er.rsi_1m <= 45 or not er.flags.get("vwap_accept", False):
        timing = "WAIT"
    elif er.flags.get("pullback", False) and er.flags.get("vwap_accept", False):
        timing = "ON TIME"
    elif er.flags.get("impulse", False) or er.flags.get("acceleration", False):
        timing = "EARLY"
    else:
        timing = "WAIT"

    return read_30, read_1h, timing


def _draw_timing_pill(draw, box, timing: str):
    x1, y1, x2, y2 = box
    color = {
        "ON TIME": "#77FF3B",
        "EARLY": "#FFD93D",
        "WAIT": "#35A7FF",
        "LATE": "#FF4D4D",
        "REJECTED": "#FF4D4D",
    }.get(timing, "#9AA6B2")
    _draw_rounded(draw, box, 7, outline=color, fill="#05080C", width=2)
    draw.text((x1 + 10, y1 + 5), f"TIMING: {timing}", fill=color, font=_load_font(17, True))


def _draw_dual_momentum_panel(draw, box, prices_30m, prices_1h, read_30: str, read_1h: str, timing: str, accent="#00FF9C"):
    """Beginner-friendly 30M + 1H chart panel for the radar graphic."""
    x1, y1, x2, y2 = box
    _draw_rounded(draw, box, 10, outline="#22303A", fill="#071017", width=2)
    draw.text((x1 + 14, y1 + 9), "30M + 1H CHART READ", fill=accent, font=_load_font(16, True))

    mid = (x1 + x2) // 2
    _draw_spark_chart(draw, prices_30m, (x1 + 10, y1 + 34, mid - 5, y1 + 122), "30M", accent)
    _draw_spark_chart(draw, prices_1h, (mid + 5, y1 + 34, x2 - 10, y1 + 122), "1H", accent)
    draw.line((mid, y1 + 34, mid, y1 + 122), fill="#22303A", width=1)

    draw.text((x1 + 14, y1 + 128), f"30M: {_safe_text(read_30, 22)}", fill="#F5F7FA", font=_load_font(14, True))
    draw.text((x1 + 14, y1 + 150), f"1H: {_safe_text(read_1h, 22)}", fill="#F5F7FA", font=_load_font(14, True))
    _draw_timing_pill(draw, (x2 - 150, y1 + 134, x2 - 14, y1 + 168), timing)

def _fire_count(n: int) -> str:
    n = max(0, min(3, int(n)))
    return "🔥" * n if n else "—"


def _score_color(score: int) -> str:
    if score >= 80:
        return "#77FF3B"
    if score >= 60:
        return "#FFD93D"
    return "#FF8A3D"


def build_radar_caption(top_setups: List[dict], regime_name: str) -> str:
    state = content_regime_label(regime_name)
    names = []
    for item in top_setups[:3]:
        er = item["er"]
        names.append(f"{er.wsname}={content_signal_tag(er, regime_name, item)}")
    top_line = " | ".join(names) if names else "No clean setups"
    return f"📡 **A+ Radar Update** | {state}\n{top_line}\nStay selective. Scan • Filter • Rank • Execute."


def send_discord_image(webhook_url: str, image_path: str, content: str = "") -> bool:
    if not webhook_url or not image_path:
        return False
    try:
        with open(image_path, "rb") as f:
            files = {"file": (os.path.basename(image_path), f, "image/png")}
            data = {"content": content[:1800]}
            r = requests.post(webhook_url, data=data, files=files, timeout=15)
            if r.status_code == 429:
                try:
                    retry_after = float(r.json().get("retry_after", 1.0))
                except Exception:
                    retry_after = 1.0
                time.sleep(retry_after)
                with open(image_path, "rb") as f2:
                    files = {"file": (os.path.basename(image_path), f2, "image/png")}
                    r = requests.post(webhook_url, data=data, files=files, timeout=15)
            return 200 <= r.status_code < 300
    except Exception as e:
        print(f"[{ts()}] Discord image send failed: {e}")
        return False




def _radar_free_signature(top_setups: List[dict], regime_name: str) -> str:
    parts = [content_regime_label(regime_name)]
    for item in (top_setups or [])[:3]:
        er = item.get("er")
        if not er:
            continue
        chart_read = _chart_read_for_app(er)
        parts.append(
            f"{er.wsname}:{content_signal_tag(er, regime_name, item)}:"
            f"T{int(er.trigger_score)}:TR{int(item.get('effective_trade_score', er.trade_score))}:"
            f"{chart_read.get('timing', 'WATCH')}"
        )
    return "|".join(parts)


def should_send_free_radar_update(top_setups: List[dict], regime_name: str) -> Tuple[bool, str]:
    """Return whether the free webhook should receive a fresh visual radar post.

    The point is to avoid Discord spam while still posting meaningful changes:
    market-state flips, top-3 changes, timing changes, or ON TIME setups.
    """
    global radar_free_last_signature, radar_free_last_state, radar_free_last_sent_at

    if not RADAR_FREE_POST_ENABLED or not FREE_RADAR_WEBHOOK_URL:
        return False, "free radar disabled or webhook missing"

    now = time.time()
    state = content_regime_label(regime_name)
    signature = _radar_free_signature(top_setups, regime_name)
    elapsed = now - float(radar_free_last_sent_at or 0.0)

    market_changed = radar_free_last_state is not None and state != radar_free_last_state
    top_changed = radar_free_last_signature is not None and signature != radar_free_last_signature

    on_time_present = False
    for item in (top_setups or [])[:3]:
        er = item.get("er")
        if er and _chart_read_for_app(er).get("timing") == "ON TIME":
            on_time_present = True
            break

    first_post = radar_free_last_signature is None
    cooldown_ok = elapsed >= RADAR_FREE_MIN_SECONDS_BETWEEN_POSTS

    reasons = []
    if first_post:
        reasons.append("first radar post")
    if RADAR_FREE_SEND_ON_MARKET_STATE_CHANGE and market_changed:
        reasons.append("market state changed")
    if RADAR_FREE_SEND_ON_TOP3_CHANGE and top_changed:
        reasons.append("top 3/timing changed")
    if RADAR_FREE_SEND_ON_ON_TIME and on_time_present:
        reasons.append("ON TIME setup present")

    should_send = bool(reasons) and (cooldown_ok or first_post or market_changed)

    if should_send:
        radar_free_last_signature = signature
        radar_free_last_state = state
        radar_free_last_sent_at = now
        return True, ", ".join(reasons)

    # Keep state/signature updated after cooldown-blocked changes so the next
    # major flip is still cleanly evaluated.
    if first_post:
        radar_free_last_signature = signature
        radar_free_last_state = state

    return False, "no meaningful change or cooldown active"


def build_free_radar_caption(top_setups: List[dict], regime_name: str, reason: str = "") -> str:
    state = content_regime_label(regime_name)
    names = []
    for item in (top_setups or [])[:3]:
        er = item.get("er")
        if not er:
            continue
        chart_read = _chart_read_for_app(er)
        names.append(f"{er.wsname} — {content_signal_tag(er, regime_name, item)} / {chart_read.get('timing', 'WATCH')}")
    top_line = "\n".join(names) if names else "No clean top setups yet."
    reason_line = f"\nReason: {reason}" if reason else ""
    return (
        f"📡 **A+ Free Radar** | **{state}**{reason_line}\n"
        f"{top_line}\n"
        f"Visual read only. Wait for clean timing. Not financial advice."
    )

def render_radar_report_image(
    top_setups: List[dict],
    regime_name: str,
    cycle_time: Optional[str] = None,
    active_pairs: int = 0,
    cycle_number: int = 0,
    sector_counts: Optional[Dict[str, int]] = None,
    btc_reason: str = "",
    output_path: str = RADAR_IMAGE_PATH,
) -> Optional[str]:
    """Render the scanner's live radar as a polished image with top setups and friendly 30M/1H chart reads."""
    if not RADAR_IMAGE_ENABLED:
        return None

    try:
        from PIL import Image, ImageDraw
    except Exception as e:
        print(f"[{ts()}] Pillow not installed. Run: pip install pillow. Error: {e}")
        return None

    cycle_time = cycle_time or dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sector_counts = sector_counts or {}
    state = content_regime_label(regime_name)

    W, H = RADAR_IMAGE_WIDTH, RADAR_IMAGE_HEIGHT
    img = Image.new("RGB", (W, H), "#05080C")
    draw = ImageDraw.Draw(img)

    # Palette
    green = "#78FF2E"
    yellow = "#FFD93D"
    red = "#FF4D4D"
    orange = "#FF8A3D"
    blue = "#35A7FF"
    purple = "#BF65FF"
    white = "#F5F7FA"
    muted = "#9AA6B2"
    panel = "#091119"
    line = "#25313A"

    state_color = green if state == "BULL" else yellow if state == "PREBULL" else red

    # Header
    _draw_rounded(draw, (18, 18, W - 18, 220), 12, outline=line, fill="#030609", width=2)
    draw.text((52, 46), "A+", fill=green, font=_load_font(84, True))
    draw.text((172, 56), "SCANNER REPORT", fill=white, font=_load_font(58, True))
    draw.text((174, 126), "REAL TIME MARKET RADAR", fill=green, font=_load_font(22, True))
    draw.text((52, 176), f"📅 {cycle_time[:10]}", fill=white, font=_load_font(20, True))
    draw.text((260, 176), f"🕒 {cycle_time[-8:]}", fill=white, font=_load_font(20, True))
    draw.text((460, 176), f"🔄 CYCLE: {cycle_number}", fill=white, font=_load_font(20, True))
    draw.text((650, 176), f"🎯 ACTIVE PAIRS: {active_pairs}", fill=green, font=_load_font(20, True))

    _draw_rounded(draw, (770, 38, W - 42, 196), 10, outline=line, fill="#05080C", width=2)
    draw.text((835, 58), "MARKET STATE", fill=white, font=_load_font(22, True))
    _draw_rounded(draw, (812, 92, W - 80, 142), 7, outline=state_color, fill="#080A0E", width=2)
    draw.text((850, 96), state, fill=state_color, font=_load_font(40, True))
    sub = "MARKET WARMING UP" if state == "PREBULL" else "TRADE READY CONDITIONS" if state == "BULL" else "WEAK TAPE"
    draw.text((820, 154), sub, fill=state_color, font=_load_font(18, True))
    draw.text((830, 178), "SETUPS FORMING" if state != "BEAR" else "SELECTIVE ONLY", fill=white, font=_load_font(18, True))

    # Section title
    draw.line((50, 250, 390, 250), fill=green, width=3)
    draw.line((690, 250, W - 50, 250), fill=green, width=3)
    draw.text((430, 230), "★  TOP 3 SETUPS  ★", fill=white, font=_load_font(30, True))

    # Setup rows
    row_y = [280, 560, 840]
    accents = [green, orange, blue]
    for idx in range(3):
        y = row_y[idx]
        item = top_setups[idx] if idx < len(top_setups) else None
        _draw_rounded(draw, (18, y, W - 18, y + 255), 12, outline=line, fill=panel, width=2)

        accent = accents[idx]
        _draw_rounded(draw, (40, y + 35, 115, y + 205), 14, outline=accent, fill="#05080C", width=3)
        draw.text((65, y + 70), str(idx + 1), fill=white, font=_load_font(52, True))

        if item is None:
            draw.text((155, y + 70), "NO SETUP", fill=muted, font=_load_font(42, True))
            draw.text((155, y + 125), "Cash is a position", fill=muted, font=_load_font(22))
            continue

        er = item["er"]
        tag = content_signal_tag(er, regime_name, item)
        tag_color = red if tag == "SHARPSHOOTER" else green if tag == "BULL" else yellow
        eff_trade = int(item.get("effective_trade_score", er.trade_score))
        readiness = item.get("entry_readiness_label", "WATCH")

        coin = er.wsname.split("/")[0]
        draw.ellipse((135, y + 28, 235, y + 128), outline=accent, width=3, fill="#071017")
        draw.text((164, y + 58), coin[:2], fill=accent, font=_load_font(30, True))

        draw.text((260, y + 32), _safe_text(coin, 10), fill=white, font=_load_font(44, True))
        _draw_rounded(draw, (262, y + 92, 430, y + 126), 5, outline=tag_color, fill="#080A0E", width=2)
        draw.text((275, y + 96), tag, fill=tag_color, font=_load_font(21, True))

        bullets = []
        if er.flags.get("acceleration", False):
            bullets.append("Momentum increasing")
        elif er.flags.get("impulse", False):
            bullets.append("Strong move")
        else:
            bullets.append("Momentum building")
        if er.flags.get("pullback", False):
            bullets.append("Pullback forming")
        elif er.flags.get("structure_break", False):
            bullets.append("Structure breaking")
        else:
            bullets.append("Needs structure")
        bullets.append("Buyers holding VWAP" if er.flags.get("vwap_accept", False) else "Needs VWAP control")

        by = y + 136
        for b in bullets:
            draw.text((270, by), "›", fill=tag_color, font=_load_font(24, True))
            draw.text((294, by), _safe_text(b, 32), fill=white, font=_load_font(20, True))
            by += 26

        # Scores
        sx = 505
        draw.text((sx, y + 36), "TRIGGER", fill=white, font=_load_font(17, True))
        draw.text((sx + 112, y + 24), str(er.trigger_score), fill=_score_color(er.trigger_score), font=_load_font(46, True))
        draw.line((sx, y + 82, sx + 235, y + 82), fill=line, width=1)

        draw.text((sx, y + 94), "TRADE", fill=white, font=_load_font(17, True))
        draw.text((sx + 112, y + 82), str(eff_trade), fill=purple, font=_load_font(46, True))
        draw.line((sx, y + 140, sx + 235, y + 140), fill=line, width=1)

        draw.text((sx, y + 150), "CONFIDENCE", fill=white, font=_load_font(17, True))
        draw.text((sx + 112, y + 138), str(er.confidence), fill=blue, font=_load_font(46, True))

        # Friendly dual chart read: 30M timing + 1H context
        read_30, read_1h, timing = build_chart_read(er)
        _draw_dual_momentum_panel(
            draw,
            (760, y + 24, W - 42, y + 205),
            er.close_30m_tail,
            er.close_1h_tail,
            read_30,
            read_1h,
            timing,
            accent=accent,
        )
        draw.text((770, y + 216), f"RADAR: {_safe_text(readiness, 18)}", fill=accent, font=_load_font(16, True))

    # Bottom panels
    bottom_y = 1120
    _draw_rounded(draw, (18, bottom_y, 358, H - 72), 10, outline=line, fill=panel, width=2)
    draw.text((80, bottom_y + 18), "MARKET SNAPSHOT", fill=green, font=_load_font(20, True))
    draw.text((46, bottom_y + 65), "₿", fill="#FFB21A", font=_load_font(64, True))
    draw.text((125, bottom_y + 66), "BTC STATUS", fill=white, font=_load_font(17, True))
    draw.text((125, bottom_y + 92), state if state != "PREBULL" else "WATCH", fill=state_color, font=_load_font(28, True))
    draw.text((125, bottom_y + 130), _safe_text(btc_reason or "Higher-timeframe read", 32), fill=white, font=_load_font(16))

    _draw_rounded(draw, (375, bottom_y, 690, H - 72), 10, outline=line, fill=panel, width=2)
    draw.text((460, bottom_y + 18), "SECTOR FLOW", fill=green, font=_load_font(20, True))
    sectors = sorted(sector_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    if not sectors:
        sectors = [("AI", 0), ("L1", 0), ("MEME", 0)]
    sy = bottom_y + 58
    for name, count in sectors:
        draw.text((410, sy), name, fill=white, font=_load_font(20, True))
        draw.text((545, sy), _fire_count(count), fill=orange, font=_load_font(20, True))
        sy += 31

    _draw_rounded(draw, (708, bottom_y, W - 18, H - 72), 10, outline=line, fill=panel, width=2)
    draw.text((770, bottom_y + 18), "HOW TO READ THIS", fill=green, font=_load_font(20, True))
    draw.text((748, bottom_y + 58), "PREBUILD", fill=yellow, font=_load_font(18, True))
    draw.text((860, bottom_y + 58), "Watch list, not entry.", fill=white, font=_load_font(17))
    draw.text((748, bottom_y + 94), "BULL", fill=green, font=_load_font(18, True))
    draw.text((860, bottom_y + 94), "Clean setup alignment.", fill=white, font=_load_font(17))
    draw.text((748, bottom_y + 130), "SHARPSHOOTER", fill=red, font=_load_font(18, True))
    draw.text((905, bottom_y + 130), "Small size only.", fill=white, font=_load_font(17))

    # Footer
    draw.text((50, H - 48), "🏆 FOCUS. DISCIPLINE. EXECUTION.", fill=green, font=_load_font(20, True))
    draw.text((50, H - 25), "1–2% targets. Small size. Big consistency.", fill=white, font=_load_font(16))
    draw.text((690, H - 48), "SCAN • FILTER • RANK • EXECUTE", fill=white, font=_load_font(18, True))
    draw.text((690, H - 25), "Not financial advice. Live market-read journal.", fill=muted, font=_load_font(15))

    img.save(output_path, "PNG")

    # Save timestamped history copy.
    try:
        os.makedirs(RADAR_IMAGE_HISTORY_DIR, exist_ok=True)
        hist_name = f"radar_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(os.path.join(RADAR_IMAGE_HISTORY_DIR, hist_name), "PNG")
    except Exception:
        pass

    return output_path

# =========================
# MARKET CAP (CoinGecko)
# =========================

def load_or_refresh_market_caps(
    cache_path: str,
    ttl_seconds: int,
    fail_open: bool = True,
) -> Dict[str, float]:
    now = time.time()
    cached_caps: Dict[str, float] = {}
    cache_found = False

    try:
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, dict) and "fetched_at" in data and "caps" in data:
                fetched_at = float(data["fetched_at"])
                raw_caps = data["caps"]

                if isinstance(raw_caps, dict):
                    cached_caps = {
                        normalize_symbol(k): safe_float(v)
                        for k, v in raw_caps.items()
                        if normalize_symbol(k)
                    }
                    cache_found = True
                    cache_age = now - fetched_at

                    if cache_age <= ttl_seconds:
                        print(f"[marketcap] using fresh cache (age={cache_age:.0f}s)")
                        return cached_caps
                    else:
                        print(f"[marketcap] cache stale (age={cache_age:.0f}s), attempting refresh...")
    except Exception as e:
        print(f"[marketcap] cache read failed: {e}")

    caps: Dict[str, float] = {}

    try:
        for page in range(1, COINGECKO_PAGES + 1):
            url = "https://api.coingecko.com/api/v3/coins/markets"
            params = {
                "vs_currency": "usd",
                "order": "market_cap_desc",
                "per_page": 250,
                "page": page,
                "sparkline": "false",
                "price_change_percentage": "24h",
            }

            last_err = None
            arr = None

            for attempt in range(3):
                try:
                    arr = request_json(url, params=params, timeout=COINGECKO_TIMEOUT)
                    break
                except Exception as e:
                    last_err = e
                    wait_s = 5 * (attempt + 1)
                    print(f"[marketcap] page {page} request failed (attempt {attempt + 1}/3): {e}")
                    if attempt < 2:
                        time.sleep(wait_s)

            if arr is None:
                if last_err and "429" in str(last_err):
                    print("[marketcap] RATE LIMITED — using cache only")
                    return cached_caps if cached_caps else {}
                raise last_err if last_err else RuntimeError(f"Unknown CoinGecko failure on page {page}")

            if not isinstance(arr, list):
                break

            for item in arr:
                sym = normalize_symbol(item.get("symbol", ""))
                mc = safe_float(item.get("market_cap", 0.0), 0.0)
                if sym and mc > 0:
                    caps[sym] = max(caps.get(sym, 0.0), mc)

            time.sleep(2.0)

        if caps:
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump({"fetched_at": now, "caps": caps}, f, indent=2)
                print(f"[marketcap] refreshed {len(caps)} symbols and updated cache")
            except Exception as e:
                print(f"[marketcap] cache write failed: {e}")

        return caps

    except Exception as e:
        if cache_found and cached_caps:
            print(f"[marketcap] refresh failed, using STALE cache instead: {e}")
            return cached_caps

        if fail_open:
            print(f"[marketcap] refresh failed (no cache available, fail-open): {e}")
            return {}

        raise

# =========================
# KRAKEN API HELPERS
# =========================

def get_all_asset_pairs() -> Dict[str, dict]:
    url = f"{KRAKEN_API_BASE}/AssetPairs"
    data = request_json(url, timeout=20)
    return data.get("result", {}) or {}

def get_usd_pairs(asset_pairs: Dict[str, dict]) -> List[Tuple[str, dict]]:
    out = []
    for pair_key, meta in asset_pairs.items():
        wsname = meta.get("wsname", "")
        if not wsname or "/USD" not in wsname:
            continue

        base = normalize_kraken_asset_code(meta.get("base", ""))
        if base in EXCLUDE_BASES:
            continue

        out.append((pair_key, meta))
    return out

def get_ticker(pair_keys: List[str]) -> Dict[str, dict]:
    if not pair_keys:
        return {}
    url = f"{KRAKEN_API_BASE}/Ticker"
    params = {"pair": ",".join(pair_keys)}
    data = request_json(url, params=params, timeout=20)
    return data.get("result", {}) or {}

def pct_change_24h_from_ticker(t: dict) -> float:
    last = safe_float((t.get("c") or ["0"])[0], 0.0)
    opn = safe_float(t.get("o"), 0.0)
    if opn <= 0:
        return 0.0
    return (last - opn) / opn * 100.0

def usd_volume_24h_from_ticker(t: dict) -> float:
    """Approximate 24h USD volume from Kraken ticker: 24h base volume * last price."""
    last = safe_float((t.get("c") or ["0"])[0], 0.0)
    vols = t.get("v") or []
    vol_24h = safe_float(vols[1] if len(vols) > 1 else 0.0, 0.0)
    return max(0.0, last * vol_24h)

def pct_change_from_closes(closes: Optional[np.ndarray], bars_back: int) -> float:
    """Percent change from N bars back to latest close."""
    if closes is None or len(closes) <= bars_back:
        return 0.0
    start = float(closes[-(bars_back + 1)])
    end = float(closes[-1])
    if start <= 0:
        return 0.0
    return (end - start) / start * 100.0

def get_1h_momentum_pct(pair_key: str) -> float:
    """Fresh 1H momentum using 5m candles, not stale 24H ticker change."""
    try:
        res = get_ohlc(pair_key, 5)
        closes = closes_from_ohlc(res)
        return pct_change_from_closes(closes, 12)  # 12 five-minute candles = 1 hour
    except Exception:
        return 0.0

def _billboard_export_row(r: dict, score: float = 0.0) -> dict:
    meta = r.get("meta", {}) or {}
    ws = meta.get("wsname", r.get("pair_key", ""))
    return {
        "pair": ws,
        "coin": str(ws).split("/")[0],
        "change_1h_pct": round(safe_float(r.get("change_1h_pct", 0.0)), 3),
        "change_24h_pct": round(safe_float(r.get("change_pct", 0.0)), 3),
        "usd_volume": round(safe_float(r.get("usd_volume", 0.0)), 2),
        "billboard_score": round(float(score or r.get("billboard_score", 0.0)), 4),
    }


def pick_kraken_billboard_markets(
    usd_pairs: List[Tuple[str, dict]],
    top_n: int,
    min_change_pct: float = BILLBOARD_MIN_24H_CHANGE_PCT,
    min_usd_volume: float = BILLBOARD_MIN_24H_USD_VOLUME,
) -> List[Tuple[str, dict]]:
    """Rank Kraken USD markets by fresh 1H momentum plus estimated 24H USD volume."""
    global LAST_BILLBOARD_SNAPSHOT

    pair_keys = [pk for pk, _ in usd_pairs]
    tick = get_ticker(pair_keys)

    rows = []
    for pk, meta in usd_pairs:
        t = tick.get(pk) or tick.get(meta.get("wsname"), None)
        if not t:
            continue
        chg24 = pct_change_24h_from_ticker(t)
        usd_vol = usd_volume_24h_from_ticker(t)
        if chg24 < min_change_pct or usd_vol < min_usd_volume:
            continue
        rows.append({"pair_key": pk, "meta": meta, "change_pct": chg24, "usd_volume": usd_vol})

    if not rows:
        LAST_BILLBOARD_SNAPSHOT = {"one_hour": [], "twenty_four_hour": []}
        return pick_top_n_markets_by_24h_change(usd_pairs, top_n)

    # 24H context board. This is exported to the site but does not dominate scans.
    by_24h_context = sorted(rows, key=lambda r: (r["change_pct"], r["usd_volume"]), reverse=True)
    LAST_BILLBOARD_SNAPSHOT["twenty_four_hour"] = [
        _billboard_export_row(r, score=0.0)
        for r in by_24h_context[:BILLBOARD_EXPORT_TOP_N]
    ]

    if BILLBOARD_USE_1H_MOMENTUM:
        # Shortlist first with ticker data so we do not pull OHLC for every pair.
        rows.sort(key=lambda r: (r["usd_volume"], r["change_pct"]), reverse=True)
        shortlist = rows[:max(top_n, BILLBOARD_1H_SHORTLIST_N)]

        for r in shortlist:
            r["change_1h_pct"] = get_1h_momentum_pct(r["pair_key"])

        shortlist = [r for r in shortlist if r.get("change_1h_pct", 0.0) >= BILLBOARD_MIN_1H_CHANGE_PCT]
        if not shortlist:
            shortlist = rows[:max(top_n, BILLBOARD_1H_SHORTLIST_N)]
            for r in shortlist:
                r["change_1h_pct"] = 0.0

        by_1h = sorted(shortlist, key=lambda r: r.get("change_1h_pct", 0.0), reverse=True)
        by_volume = sorted(shortlist, key=lambda r: r["usd_volume"], reverse=True)
        momentum_rank = {r["pair_key"]: i for i, r in enumerate(by_1h, start=1)}
        volume_rank = {r["pair_key"]: i for i, r in enumerate(by_volume, start=1)}
        total = max(1, len(shortlist))

        scored = []
        for r in shortlist:
            momentum_strength = 1.0 - ((momentum_rank[r["pair_key"]] - 1) / total)
            volume_strength = 1.0 - ((volume_rank[r["pair_key"]] - 1) / total)
            billboard_score = (momentum_strength * BILLBOARD_1H_WEIGHT) + (volume_strength * BILLBOARD_VOLUME_WEIGHT)
            r["billboard_score"] = billboard_score
            scored.append((billboard_score, r))
        scored.sort(key=lambda x: x[0], reverse=True)

        LAST_BILLBOARD_SNAPSHOT["one_hour"] = [
            _billboard_export_row(r, score=s)
            for s, r in scored[:BILLBOARD_EXPORT_TOP_N]
        ]

        print(f"[{ts()}] KRAKEN BILLBOARD | top {min(top_n, len(scored))} by 1H momentum + USD volume")
        for i, (_, r) in enumerate(scored[:BILLBOARD_PRINT_TOP_N], start=1):
            ws = r["meta"].get("wsname", r["pair_key"])
            print(f"#{i:<2} {ws:<12} | 1H={r.get('change_1h_pct', 0.0):+.2f}% | 24h={r['change_pct']:+.2f}% | Vol=${r['usd_volume']:,.0f}")
        return [(r["pair_key"], r["meta"]) for _, r in scored[:top_n]]

    # Legacy fallback: 24H change + USD volume.
    by_change = sorted(rows, key=lambda r: r["change_pct"], reverse=True)
    by_volume = sorted(rows, key=lambda r: r["usd_volume"], reverse=True)
    change_rank = {r["pair_key"]: i for i, r in enumerate(by_change, start=1)}
    volume_rank = {r["pair_key"]: i for i, r in enumerate(by_volume, start=1)}
    total = max(1, len(rows))

    scored = []
    for r in rows:
        change_strength = 1.0 - ((change_rank[r["pair_key"]] - 1) / total)
        volume_strength = 1.0 - ((volume_rank[r["pair_key"]] - 1) / total)
        billboard_score = (change_strength * BILLBOARD_CHANGE_WEIGHT) + (volume_strength * BILLBOARD_VOLUME_WEIGHT)
        r["billboard_score"] = billboard_score
        scored.append((billboard_score, r))
    scored.sort(key=lambda x: x[0], reverse=True)

    LAST_BILLBOARD_SNAPSHOT["one_hour"] = []
    LAST_BILLBOARD_SNAPSHOT["twenty_four_hour"] = [
        _billboard_export_row(r, score=s)
        for s, r in scored[:BILLBOARD_EXPORT_TOP_N]
    ]

    print(f"[{ts()}] KRAKEN BILLBOARD | top {min(top_n, len(scored))} by 24h change + USD volume")
    for i, (_, r) in enumerate(scored[:BILLBOARD_PRINT_TOP_N], start=1):
        ws = r["meta"].get("wsname", r["pair_key"])
        print(f"#{i:<2} {ws:<12} | 24h={r['change_pct']:+.2f}% | Vol=${r['usd_volume']:,.0f}")

    return [(r["pair_key"], r["meta"]) for _, r in scored[:top_n]]


def build_scan_pool(usd_pairs: List[Tuple[str, dict]], pair_limit: int) -> List[Tuple[str, dict]]:
    if USE_KRAKEN_BILLBOARD:
        return pick_kraken_billboard_markets(
            usd_pairs,
            top_n=min(pair_limit, BILLBOARD_TOP_N),
            min_change_pct=BILLBOARD_MIN_24H_CHANGE_PCT,
            min_usd_volume=BILLBOARD_MIN_24H_USD_VOLUME,
        )
    return pick_top_n_markets_by_24h_change(usd_pairs, pair_limit)

def pick_top_n_markets_by_24h_change(
    usd_pairs: List[Tuple[str, dict]],
    top_n: int,
) -> List[Tuple[str, dict]]:
    pair_keys = [pk for pk, _ in usd_pairs]
    tick = get_ticker(pair_keys)

    scored: List[Tuple[float, str, dict]] = []
    for pk, meta in usd_pairs:
        t = tick.get(pk)
        if not t:
            ws = meta.get("wsname")
            t = tick.get(ws, None)
        if not t:
            continue

        chg = pct_change_24h_from_ticker(t)
        scored.append((chg, pk, meta))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [(pk, meta) for _, pk, meta in scored[:top_n]]

def get_ohlc(pair_key: str, interval: int) -> dict:
    url = f"{KRAKEN_API_BASE}/OHLC"
    params = {"pair": pair_key, "interval": interval}
    data = request_json(url, params=params, timeout=OHLC_TIMEOUT_SECONDS)
    return data.get("result", {}) or {}

def closes_from_ohlc(res: dict) -> Optional[np.ndarray]:
    keys = [k for k in res.keys() if k != "last"]
    if not keys:
        return None
    arr = res[keys[0]]
    if not isinstance(arr, list) or len(arr) < 30:
        return None
    closes = [safe_float(row[4], np.nan) for row in arr]
    return np.array(closes, dtype=float)

def volumes_from_ohlc(res: dict) -> Optional[np.ndarray]:
    keys = [k for k in res.keys() if k != "last"]
    if not keys:
        return None
    arr = res[keys[0]]
    if not isinstance(arr, list) or len(arr) < 10:
        return None
    vols = [safe_float(row[6], np.nan) for row in arr]
    return np.array(vols, dtype=float)

def vwap_from_ohlc(res: dict, lookback: int) -> float:
    keys = [k for k in res.keys() if k != "last"]
    if not keys:
        return 0.0
    arr = res[keys[0]]
    if not isinstance(arr, list) or len(arr) < 5:
        return 0.0

    tail = arr[-lookback:] if len(arr) >= lookback else arr
    num = 0.0
    den = 0.0
    for row in tail:
        c = safe_float(row[4], 0.0)
        v = safe_float(row[6], 0.0)
        num += c * v
        den += v
    return (num / den) if den > 0 else 0.0

# =========================
# INDICATORS / FLAGS
# =========================

def rsi(series: np.ndarray, period: int = 14) -> float:
    if series is None or len(series) < period + 2:
        return float("nan")
    delta = np.diff(series)
    gain = np.where(delta > 0, delta, 0.0)
    loss = np.where(delta < 0, -delta, 0.0)
    avg_gain = np.mean(gain[-period:])
    avg_loss = np.mean(loss[-period:])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))

def bollinger_width(series: np.ndarray, period: int = 20, std_mult: float = 2.0) -> float:
    if series is None or len(series) < period + 2:
        return float("nan")
    window = series[-period:]
    ma = np.mean(window)
    sd = np.std(window)
    upper = ma + std_mult * sd
    lower = ma - std_mult * sd
    if ma <= 0:
        return float("nan")
    return (upper - lower) / ma

def ema(series: np.ndarray, span: int) -> np.ndarray:
    if series is None or len(series) < span + 2:
        return np.array([], dtype=float)
    alpha = 2 / (span + 1)
    out = np.zeros_like(series, dtype=float)
    out[0] = series[0]
    for i in range(1, len(series)):
        out[i] = alpha * series[i] + (1 - alpha) * out[i - 1]
    return out

def macd_hist(series: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> float:
    if series is None or len(series) < slow + signal + 5:
        return float("nan")
    e_fast = ema(series, fast)
    e_slow = ema(series, slow)
    if len(e_fast) == 0 or len(e_slow) == 0:
        return float("nan")
    macd_line = e_fast - e_slow
    sig = ema(macd_line, signal)
    if len(sig) == 0:
        return float("nan")
    hist = macd_line[-1] - sig[-1]
    return float(hist)

def macd_hist_series(series: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> np.ndarray:
    """Return MACD histogram series for slope/quality checks."""
    if series is None or len(series) < slow + signal + 5:
        return np.array([], dtype=float)
    e_fast = ema(series, fast)
    e_slow = ema(series, slow)
    if len(e_fast) == 0 or len(e_slow) == 0:
        return np.array([], dtype=float)
    macd_line = e_fast - e_slow
    sig = ema(macd_line, signal)
    if len(sig) == 0:
        return np.array([], dtype=float)
    return macd_line - sig


def slope_last(values, lookback: int = 4) -> float:
    try:
        arr = np.array(values, dtype=float)
        if len(arr) < lookback + 1:
            return 0.0
        return float(arr[-1] - arr[-(lookback + 1)])
    except Exception:
        return 0.0


def pct_return(values, lookback: int = 6) -> float:
    try:
        arr = np.array(values, dtype=float)
        if len(arr) < lookback + 1 or arr[-(lookback + 1)] <= 0:
            return 0.0
        return float((arr[-1] - arr[-(lookback + 1)]) / arr[-(lookback + 1)] * 100.0)
    except Exception:
        return 0.0


def realized_vol_pct(values, lookback: int = 20) -> float:
    try:
        arr = np.array(values, dtype=float)
        if len(arr) < lookback + 2:
            return 0.0
        window = arr[-lookback:]
        rets = np.diff(window) / window[:-1]
        return float(np.std(rets) * math.sqrt(lookback) * 100.0)
    except Exception:
        return 0.0


def classify_momentum_quality(rsi_now: float, rsi_prev: float, macd_now: float, macd_prev: float) -> str:
    rsi_delta = safe_float(rsi_now, 0.0) - safe_float(rsi_prev, 0.0)
    macd_delta = safe_float(macd_now, 0.0) - safe_float(macd_prev, 0.0)
    if rsi_delta > 1.0 and macd_delta > 0:
        return "BUILDING"
    if rsi_delta < -1.0 and macd_delta < 0:
        return "FAILING"
    if safe_float(rsi_now, 0.0) >= 68 and macd_delta <= 0:
        return "PEAKING"
    if macd_delta < 0 or rsi_delta < -1.0:
        return "WEAKENING"
    return "STABLE"


def classify_volatility_state(close_series: np.ndarray) -> str:
    vol = realized_vol_pct(close_series, 20)
    prior = realized_vol_pct(close_series[:-10], 20) if close_series is not None and len(close_series) > 35 else vol
    if vol <= 0:
        return "UNKNOWN"
    if vol > max(prior * 1.35, 1.25):
        return "EXPANDING"
    if vol < prior * 0.75:
        return "COMPRESSING"
    if vol > 1.75:
        return "HIGH"
    return "NORMAL"


def classify_trap_risk(price: float, vwap_value: float, rsi_now: float, rsi_prev: float, macd_now: float, macd_prev: float, structure_break: bool, pullback: bool) -> str:
    above_vwap = vwap_value > 0 and price > vwap_value
    rsi_falling = safe_float(rsi_now, 0.0) < safe_float(rsi_prev, 0.0) - 1.0
    macd_falling = safe_float(macd_now, 0.0) < safe_float(macd_prev, 0.0)
    if above_vwap and rsi_falling and macd_falling and not structure_break:
        return "HIGH"
    if above_vwap and (rsi_falling or macd_falling) and not pullback:
        return "MEDIUM"
    return "LOW"


def detect_impulse(close_1m: np.ndarray) -> bool:
    if close_1m is None or len(close_1m) < 20:
        return False
    recent = close_1m[-12:]
    lo = float(np.min(recent))
    hi = float(np.max(recent))
    if lo <= 0:
        return False
    return (hi - lo) / lo >= IMPULSE_MIN_RETURN

def detect_pullback(close_1m: np.ndarray) -> bool:
    if close_1m is None or len(close_1m) < 20:
        return False
    recent = close_1m[-20:]
    peak = float(np.max(recent))
    last = float(recent[-1])
    if peak <= 0:
        return False
    drop = (peak - last) / peak
    return 0.0 < drop <= PULLBACK_MAX_DROP

def detect_acceleration(close_1m: np.ndarray) -> bool:
    if close_1m is None:
        return False
    bars = ACCEL_LOOKBACK_BARS
    needed = (bars * 2) + 2
    if len(close_1m) < needed:
        return False

    latest_start = float(close_1m[-(bars + 1)])
    latest_end = float(close_1m[-1])
    prior_start = float(close_1m[-((bars * 2) + 1)])
    prior_end = float(close_1m[-(bars + 1)])

    if latest_start <= 0 or prior_start <= 0 or prior_end <= 0:
        return False

    latest_ret = (latest_end - latest_start) / latest_start
    prior_ret = (prior_end - prior_start) / prior_start

    return latest_ret >= ACCEL_MIN_RETURN and latest_ret >= max(prior_ret * ACCEL_MULTIPLIER, ACCEL_MIN_RETURN)

def detect_volume_spike(
    volumes: np.ndarray,
    lookback: int = VOLUME_LOOKBACK_BARS,
    multiplier: float = VOLUME_SPIKE_MULTIPLIER,
) -> bool:
    if volumes is None or len(volumes) < lookback + 1:
        return False
    baseline = volumes[-(lookback + 1):-1]
    latest = float(volumes[-1])
    avg = float(np.mean(baseline)) if len(baseline) > 0 else 0.0
    if avg <= 0:
        return False
    return latest >= avg * multiplier

def detect_structure_break(
    close_1m: np.ndarray,
    lookback: int = STRUCTURE_LOOKBACK_BARS,
    exclude_recent: int = STRUCTURE_EXCLUDE_RECENT_BARS,
) -> bool:
    if close_1m is None or len(close_1m) < (lookback + exclude_recent + 1):
        return False
    prior_window = close_1m[-(lookback + exclude_recent):-exclude_recent]
    if len(prior_window) == 0:
        return False
    recent_high = float(np.max(prior_window))
    last = float(close_1m[-1])
    return last > recent_high

def detect_trend_ok(
    close_15m: np.ndarray,
    close_1h: np.ndarray,
    ema_period_15m: int = TREND_EMA_PERIOD_15M,
    ema_period_1h: int = TREND_EMA_PERIOD_1H,
) -> bool:
    if close_15m is None or close_1h is None:
        return False
    ema15 = ema(close_15m, ema_period_15m)
    ema1h = ema(close_1h, ema_period_1h)
    if len(ema15) == 0 or len(ema1h) == 0:
        return False
    return float(close_15m[-1]) > float(ema15[-1]) and float(close_1h[-1]) > float(ema1h[-1])

def compute_trade_score(
    trend_ok: bool,
    volume_spike: bool,
    structure_break: bool,
    acceleration: bool,
    hits_last_2h: int,
    btc_ok: bool,
    vwap_accept: bool,
) -> int:
    score = 0
    score += 25 if trend_ok else 0
    score += 20 if volume_spike else 0
    score += 20 if structure_break else 0
    score += 15 if acceleration else 0
    score += 10 if hits_last_2h >= 2 else 0
    score += 5 if btc_ok else 0
    score += 5 if vwap_accept else 0
    return int(score)


# =========================
# v19 VETERAN COMPOSITE DECISION ENGINE
# =========================

def classify_structure_type(trend_ok: bool, structure_break: bool, pullback: bool, vwap_accept: bool) -> str:
    """Classify the pair's tradable structure. Avoid treating every green move as trend."""
    if trend_ok and structure_break and pullback and vwap_accept:
        return "TRENDING"
    if structure_break and vwap_accept:
        return "BREAKOUT"
    if trend_ok and vwap_accept:
        return "BASE"
    if vwap_accept:
        return "RANGE"
    return "WEAK"

def compute_relative_strength_pct(pair_return_pct: float, btc_return_pct: float) -> float:
    """Positive = pair outperforming BTC over the comparison window."""
    return round(_json_safe_number(pair_return_pct) - _json_safe_number(btc_return_pct), 3)

def compute_composite_score(
    momentum_quality: str,
    structure_type: str,
    volatility_state: str,
    distance_from_vwap_pct: float,
    relative_strength_pct: float,
    btc_phase: str,
    trap_risk: str = "LOW",
) -> int:
    """
    0-100 decision score. This is not a prediction. It is a weighted tradability score.
    Weighting: momentum 20, structure 20, volatility 15, location 15, relative strength 15, BTC phase 15.
    """
    score = 0.0

    # 1) Momentum quality (20)
    mq = (momentum_quality or "UNKNOWN").upper()
    if mq == "BUILDING":
        score += 20
    elif mq == "STABLE":
        score += 12
    elif mq == "WEAKENING":
        score += 5
    else:  # FAILING / UNKNOWN
        score += 0

    # 2) Structure (20)
    st = (structure_type or "WEAK").upper()
    if st == "TRENDING":
        score += 20
    elif st == "BREAKOUT":
        score += 16
    elif st == "BASE":
        score += 11
    elif st == "RANGE":
        score += 6
    else:
        score += 0

    # 3) Volatility state (15)
    vol = (volatility_state or "UNKNOWN").upper()
    if vol == "EXPANDING":
        score += 15
    elif vol == "NORMAL":
        score += 9
    elif vol == "COMPRESSING":
        score += 6
    elif vol == "HIGH":
        score += 4
    else:
        score += 2

    # 4) Location vs VWAP (15). Sweet spot is close enough to define risk, not stretched.
    dist = abs(_json_safe_number(distance_from_vwap_pct))
    if dist <= 0.30:
        score += 15
    elif dist <= 0.75:
        score += 11
    elif dist <= 1.50:
        score += 6
    elif dist <= 2.25:
        score += 2
    else:
        score += 0

    # 5) Relative strength vs BTC (15)
    rs = _json_safe_number(relative_strength_pct)
    if rs >= 0.75:
        score += 15
    elif rs >= 0.25:
        score += 11
    elif rs >= 0.0:
        score += 7
    elif rs >= -0.25:
        score += 3
    else:
        score += 0

    # 6) BTC phase (15). BTC is a throttle, not a prison.
    phase = (btc_phase or "CHOP").upper()
    if phase == "EXPANSION":
        score += 15
    elif phase == "ACCUMULATION":
        score += 11
    elif phase == "DISTRIBUTION":
        score += 5
    elif phase == "CHOP":
        score += 3
    else:  # EXHAUSTION
        score += 0

    # Hard quality penalties: a veteran rejects traps even when indicators look decent.
    tr = (trap_risk or "LOW").upper()
    if tr == "MEDIUM":
        score -= 8
    elif tr == "HIGH":
        score -= 20
    if mq == "FAILING":
        score -= 10

    return max(0, min(100, int(round(score))))

def classify_veteran_decision(composite_score: int, trap_risk: str, momentum_quality: str, timing: str = "") -> str:
    tr = (trap_risk or "LOW").upper()
    mq = (momentum_quality or "UNKNOWN").upper()
    tm = (timing or "").upper()

    if tr == "HIGH" or mq == "FAILING":
        return "AVOID"
    if tm == "LATE":
        return "WAIT"
    if composite_score >= 85:
        return "TRADE"
    if composite_score >= 72:
        return "WATCH"
    if composite_score >= 62:
        return "SHARPSHOOTER"
    return "IGNORE"

def classify_position_size(composite_score: int, btc_phase: str, trap_risk: str, veteran_decision: str) -> str:
    phase = (btc_phase or "CHOP").upper()
    tr = (trap_risk or "LOW").upper()
    decision = (veteran_decision or "IGNORE").upper()

    if decision in {"AVOID", "IGNORE"} or tr == "HIGH":
        return "NO TRADE"
    if composite_score >= 88 and phase == "EXPANSION":
        return "FULL"
    if composite_score >= 78 and phase in {"EXPANSION", "ACCUMULATION"}:
        return "HALF"
    if composite_score >= 62:
        return "SCOUT"
    return "NO TRADE"

def build_decision_reason(er, btc_phase: str = "CHOP") -> str:
    reasons = []
    if getattr(er, "trap_risk", "LOW") == "HIGH":
        reasons.append("trap risk high")
    if getattr(er, "momentum_quality", "UNKNOWN") in {"FAILING", "WEAKENING"}:
        reasons.append(f"momentum {er.momentum_quality.lower()}")
    if getattr(er, "relative_strength_pct", 0.0) > 0.25:
        reasons.append("outperforming BTC")
    if getattr(er, "distance_from_vwap_pct", 999.0) <= 0.75:
        reasons.append("near VWAP/value")
    if getattr(er, "structure_type", "WEAK") in {"TRENDING", "BREAKOUT"}:
        reasons.append(er.structure_type.lower())
    if btc_phase in {"DISTRIBUTION", "EXHAUSTION"}:
        reasons.append(f"BTC {btc_phase.lower()}")
    return ", ".join(reasons[:4]) if reasons else "no clean edge yet"

# =========================
# DATA STRUCTURE
# =========================

@dataclass
class EvalResult:
    pair: str
    wsname: str

    price: float
    change_24h_pct: float

    rsi_1m: float
    rsi_5m: float
    macd_hist_15m: float
    vwap_ny: float

    market_cap_usd: float

    trigger_score: int
    confidence: int

    flags: Dict[str, bool]
    missing: List[str]

    hits_last_2h: int = 0
    stars: str = ""

    is_aplus: bool = False
    trade_score: int = 0
    trade_ready: bool = False
    sector: str = "OTHER"
    sector_boost: int = 0
    close_1h_tail: Optional[List[float]] = None
    close_30m_tail: Optional[List[float]] = None
    momentum_quality: str = "UNKNOWN"
    trap_risk: str = "LOW"
    volatility_state: str = "UNKNOWN"
    structure_type: str = "UNKNOWN"
    relative_strength_pct: float = 0.0
    distance_from_vwap_pct: float = 0.0
    composite_score: int = 0
    veteran_decision: str = "IGNORE"
    position_size: str = "NO TRADE"
    decision_reason: str = "no clean edge yet"

# =========================
# SCORING + EVAL
# =========================

def eval_pair(
    pair_key: str,
    meta: dict,
    ticker: dict,
    market_caps: Dict[str, float],
    regime_settings: Optional[dict] = None,
) -> Optional[EvalResult]:
    wsname = meta.get("wsname", pair_key)
    regime_settings = regime_settings or REGIME_RULES["BEAR"]
    rsi_1m_min = float(regime_settings.get("rsi_1m_min", RSI_1M_MIN))
    rsi_1m_max = float(regime_settings.get("rsi_1m_max", RSI_1M_MAX))
    rsi_5m_min = float(regime_settings.get("rsi_5m_min", RSI_5M_MIN))
    macd_hist_15m_min = float(regime_settings.get("macd_hist_15m_min", MACD_HIST_15M_MIN))

    price = safe_float((ticker.get("c") or ["0"])[0], 0.0)
    chg24 = pct_change_24h_from_ticker(ticker)

    c1 = get_ohlc(pair_key, 1)
    c5 = get_ohlc(pair_key, 5)
    c15 = get_ohlc(pair_key, 15)
    c60 = get_ohlc(pair_key, 60)

    close1 = closes_from_ohlc(c1)
    close5 = closes_from_ohlc(c5)
    close15 = closes_from_ohlc(c15)
    close60 = closes_from_ohlc(c60)
    vol1 = volumes_from_ohlc(c1)

    if close1 is None or close5 is None or close15 is None or close60 is None:
        return None

    rsi1 = rsi(close1, 14)
    rsi1_prev = rsi(close1[:-3], 14) if len(close1) > 20 else float("nan")
    rsi5 = rsi(close5, 14)
    rsi5_prev = rsi(close5[:-2], 14) if len(close5) > 20 else float("nan")
    mh15 = macd_hist(close15, 12, 26, 9)
    mh15_prev = macd_hist(close15[:-1], 12, 26, 9) if len(close15) > 40 else float("nan")
    vwap = vwap_from_ohlc(c1, VWAP_LOOKBACK_1M)

    bb_w = bollinger_width(close1, BB_PERIOD, BB_STD)
    compression = (not math.isnan(bb_w)) and (bb_w <= BB_WIDTH_MAX)
    impulse = detect_impulse(close1)
    pullback = detect_pullback(close1)
    acceleration = detect_acceleration(close1)
    vwap_accept = (price >= vwap) if vwap > 0 else False

    trend_ok = detect_trend_ok(close15, close60)
    volume_spike = detect_volume_spike(vol1)
    structure_break = detect_structure_break(close1)
    momentum_quality = classify_momentum_quality(rsi1, rsi1_prev, mh15, mh15_prev)
    volatility_state = classify_volatility_state(close1)
    trap_risk = classify_trap_risk(price, vwap, rsi1, rsi1_prev, mh15, mh15_prev, structure_break, pullback)
    structure_type = classify_structure_type(trend_ok, structure_break, pullback, vwap_accept)
    distance_from_vwap_pct = ((price - vwap) / vwap * 100.0) if vwap > 0 else 999.0
    pair_15m_return_pct = pct_return(close15, 4)
    btc_15m_return_pct = safe_float(regime_settings.get("btc_15m_return_pct", 0.0), 0.0)
    relative_strength_pct = compute_relative_strength_pct(pair_15m_return_pct, btc_15m_return_pct)
    btc_phase = regime_settings.get("market_phase", regime_settings.get("name", "CHOP"))
    composite_score = compute_composite_score(
        momentum_quality=momentum_quality,
        structure_type=structure_type,
        volatility_state=volatility_state,
        distance_from_vwap_pct=distance_from_vwap_pct,
        relative_strength_pct=relative_strength_pct,
        btc_phase=btc_phase,
        trap_risk=trap_risk,
    )

    rsi_ok = (
        (not math.isnan(rsi1))
        and (rsi_1m_min <= rsi1 <= rsi_1m_max)
        and (not math.isnan(rsi5))
        and (rsi5 >= rsi_5m_min)
    )
    macd_turn_up = (not math.isnan(mh15)) and (mh15 >= macd_hist_15m_min)

    flags = {
        "compression": bool(compression),
        "impulse": bool(impulse),
        "vwap_accept": bool(vwap_accept),
        "pullback": bool(pullback),
        "acceleration": bool(acceleration),
        "rsi_ok": bool(rsi_ok),
        "macd_turn_up": bool(macd_turn_up),
        "trend_ok": bool(trend_ok),
        "volume_spike": bool(volume_spike),
        "structure_break": bool(structure_break),
        "momentum_building": momentum_quality == "BUILDING",
        "momentum_failing": momentum_quality in {"FAILING", "WEAKENING"},
        "trap_risk_high": trap_risk == "HIGH",
        "relative_strength_positive": relative_strength_pct > 0,
        "composite_a_plus": composite_score >= 85,
    }

    missing: List[str] = []
    if not compression:
        missing.append("no compression")
    if not impulse:
        missing.append("no impulse")
    if not vwap_accept:
        missing.append("VWAP not accepted")
    if not pullback:
        missing.append("no pullback")
    if not trend_ok:
        missing.append("trend not aligned")
    if not volume_spike:
        missing.append("no volume spike")
    if not structure_break:
        missing.append("no structure break")
    if trap_risk == "HIGH":
        missing.append("trap/distribution risk high")
    if momentum_quality == "FAILING":
        missing.append("momentum failing")
    elif momentum_quality == "WEAKENING":
        missing.append("momentum weakening")

    if math.isnan(rsi1):
        missing.append("RSI1m NaN")
    else:
        if not (rsi_1m_min <= rsi1 <= rsi_1m_max):
            missing.append(f"RSI<{rsi_1m_min:.1f} or RSI>{rsi_1m_max:.1f} (RSI={rsi1:.2f})")

    if math.isnan(rsi5):
        missing.append("5m RSI NaN")
    else:
        if rsi5 < RSI_5M_MIN:
            missing.append(f"5m RSI<{rsi_5m_min:.1f} (RSI={rsi5:.2f})")

    if math.isnan(mh15):
        missing.append("15m MACD hist NaN")
    else:
        if mh15 < macd_hist_15m_min:
            missing.append("15m MACD hist < 0")

    trigger_score = 0
    trigger_score += 20 if compression else 0
    trigger_score += 20 if impulse else 0
    trigger_score += 20 if vwap_accept else 0
    trigger_score += 20 if pullback else 0
    trigger_score += 10 if (not math.isnan(rsi1) and rsi_1m_min <= rsi1 <= rsi_1m_max) else 0
    trigger_score += 10 if (not math.isnan(rsi5) and rsi5 >= rsi_5m_min) else 0
    trigger_score += 10 if acceleration else 0
    if momentum_quality == "BUILDING":
        trigger_score += 5
    elif momentum_quality == "WEAKENING":
        trigger_score -= 10
    elif momentum_quality == "FAILING":
        trigger_score -= 20
    if trap_risk == "MEDIUM":
        trigger_score -= 10
    elif trap_risk == "HIGH":
        trigger_score -= 25
    if volatility_state == "HIGH" and not pullback:
        trigger_score -= 10
    if relative_strength_pct < -0.25:
        trigger_score -= 8
    trigger_score = max(0, min(100, int(trigger_score)))

    confidence = trigger_score
    is_aplus = len(missing) == 0

    base = normalize_kraken_asset_code(meta.get("base", ""))
    base_norm = normalize_kraken_asset_code(base)
    mc = safe_float(market_caps.get(base_norm, 0.0), 0.0)
    sector = get_sector(base_norm)

    return EvalResult(
        pair=pair_key,
        wsname=wsname,
        price=price,
        change_24h_pct=chg24,
        rsi_1m=float(rsi1),
        rsi_5m=float(rsi5),
        macd_hist_15m=float(mh15),
        vwap_ny=float(vwap),
        market_cap_usd=mc,
        trigger_score=int(trigger_score),
        confidence=int(confidence),
        flags=flags,
        missing=missing,
        is_aplus=is_aplus,
        trade_score=0,
        trade_ready=False,
        sector=sector,
        sector_boost=0,
        close_1h_tail=[float(x) for x in close60[-40:]] if close60 is not None and len(close60) else None,
        close_30m_tail=[float(x) for x in close1[-30:]] if close1 is not None and len(close1) else None,
        momentum_quality=momentum_quality,
        trap_risk=trap_risk,
        volatility_state=volatility_state,
        structure_type=structure_type,
        relative_strength_pct=float(relative_strength_pct),
        distance_from_vwap_pct=float(distance_from_vwap_pct),
        composite_score=int(composite_score),
        veteran_decision=classify_veteran_decision(composite_score, trap_risk, momentum_quality),
        position_size=classify_position_size(composite_score, btc_phase, trap_risk, classify_veteran_decision(composite_score, trap_risk, momentum_quality)),
        decision_reason="",
    )

def status_label(er: EvalResult, cooldown_hit: bool, regime_settings: Optional[dict] = None) -> str:
    regime_settings = regime_settings or REGIME_RULES["BEAR"]
    watch_min_score = int(regime_settings.get("watch_min_score", WATCH_MIN_SCORE))
    if er.trade_ready and not cooldown_hit:
        return "TRADE READY"
    if er.trigger_score >= watch_min_score:
        return "Watch"
    return "Fail"

def watch_rank_tuple(er: EvalResult, watch_hits: int, streak: int):
    return (
        getattr(er, "composite_score", 0),
        er.trigger_score,
        er.trade_score,
        1 if getattr(er, "momentum_quality", "") == "BUILDING" else 0,
        -2 if getattr(er, "trap_risk", "LOW") == "HIGH" else (-1 if getattr(er, "trap_risk", "LOW") == "MEDIUM" else 0),
        streak,
        watch_hits,
        er.hits_last_2h,
        1 if er.flags.get("acceleration") else 0,
        er.change_24h_pct,
    )


def rank_change_label(symbol: str, current_rank: int) -> str:
    prev_rank = leaderboard_prev_ranks.get(symbol)
    if prev_rank is None:
        return "NEW"
    delta = prev_rank - current_rank
    if delta > 0:
        return f"↑{delta}"
    if delta < 0:
        return f"↓{abs(delta)}"
    return "→0"

def fresh_breakout_marker(streak: int, er: EvalResult) -> str:
    is_fresh = (
        streak == 1
        and er.trigger_score >= PREMIUM_MIN_TRIGGER
        and er.trade_score >= PREMIUM_MIN_TRADE_SCORE
        and er.flags.get("acceleration", False)
    )
    return "🆕" if is_fresh else ""

def build_top3_summary(top_watch: List[dict]) -> str:
    if not top_watch:
        return "🔥 Top 3:\nnone"

    lines = ["🔥 Top 3:"]
    for idx, item in enumerate(top_watch[:TOP3_SUMMARY_COUNT], start=1):
        er = item["er"]
        eff_trade = item.get("effective_trade_score", er.trade_score)
        stars = er.stars if er.stars else ""
        hot = " 🔥HOT" if item.get("streak", 0) >= HOT_STREAK_MIN else ""
        ready = " ✅READY" if er.trade_ready else ""
        lines.append(
            f"{idx}. {er.wsname} [{er.sector}] | T{er.trigger_score} / TR{eff_trade} / C{er.confidence} | W{item.get('watch_hits', 0)} {stars}{hot}{ready}".rstrip()
        )
    return "\n".join(lines)

def discord_ready_tag(er: EvalResult) -> str:
    return " ✅ TRADE READY" if er.trade_ready else ""

def discord_hot_tag(streak: int) -> str:
    return " 🔥 HOT" if streak >= HOT_STREAK_MIN else ""

def build_discord_entry(rank: int, er: EvalResult, watch_hits: int, streak: int, rank_change: str, fresh_marker: str, eff_trade: int) -> List[str]:
    stars = er.stars if er.stars else ""
    blocker = compact_missing_list(er.missing, limit=1)
    accel_state = "ACCEL" if er.flags.get("acceleration") else "-"
    hot_tag = discord_hot_tag(streak)
    ready_tag = discord_ready_tag(er)
    title = f"**#{rank} {er.wsname}** {rank_change}{fresh_marker}{hot_tag}{ready_tag}".rstrip()

    if DISCORD_COMPACT_MODE:
        return [
            title,
            f"T:{er.trigger_score} | TR:{eff_trade} | C:{er.confidence}",
            f"{accel_state} | Hits:{er.hits_last_2h}{stars} | Watch:{watch_hits} | Streak:{streak}",
            f"{er.sector} | {blocker} | Mom:{getattr(er, 'momentum_quality', 'UNK')} | Trap:{getattr(er, 'trap_risk', 'LOW')}",
            "━━━━━━━━━━━━━━━━━━━━",
        ]

    return [
        title,
        f"Scores: T{er.trigger_score} | TR{eff_trade} | C{er.confidence}",
        f"State: {accel_state} | Hits:{er.hits_last_2h}{stars} | Watch:{watch_hits} | Streak:{streak}",
        f"Context: {er.sector} | Blocker/Need: {blocker}",
        "━━━━━━━━━━━━━━━━━━━━",
    ]

def should_print_console_state(state: str, state_print_counts: Dict[str, int]) -> bool:
    if state == "READY":
        return True
    if state == "BUILDING":
        return True
    if state == "EARLY":
        return state_print_counts.get("EARLY", 0) < MAX_EARLY_PRINT
    if state == "LATE":
        return state_print_counts.get("LATE", 0) < MAX_LATE_PRINT
    if state == "BLOCKED":
        return state_print_counts.get("BLOCKED", 0) < MAX_BLOCKED_PRINT
    return True

def print_result_line(er: EvalResult, idx: int, n: int, cooldown_hit: bool, btc_ok: bool, state_print_counts: Dict[str, int], regime_settings: Optional[dict] = None, regime_name: str = "BEAR"):
    label = status_label(er, cooldown_hit, regime_settings)
    state, blocker = classify_entry_state(er, btc_ok)
    accel_label = color_accel(er.flags.get("acceleration"))
    line1 = (
        f"({color_symbol(er.wsname):<10}) {ts()} | Scanning {idx}/{n} | TFs: 1m/5m/15m/1H | "
        f"{btc_console_label(regime_name)} | Hits={color_hits(er.hits_last_2h, er.stars)} | {accel_label}"
    )
    trade_tag = f" | {Fore.GREEN}{Style.BRIGHT}TRADE READY ✅{Style.RESET_ALL}" if er.trade_ready else ""
    line2 = (
        f"{color_label(label):<14} | TriggerScore={color_score(er.trigger_score):<3} | "
        f"TradeScore={color_score(er.trade_score):<3} | Composite={color_score(getattr(er, 'composite_score', 0)):<3} | Confidence={color_score(er.confidence):<3}{trade_tag}"
    )
    line3 = (
        f"{color_state(state):<14} | Blocker={Fore.YELLOW}{blocker}{Style.RESET_ALL} | "
        f"Trend={'Y' if er.flags.get('trend_ok') else 'N'} | Vol={'Y' if er.flags.get('volume_spike') else 'N'} | Break={'Y' if er.flags.get('structure_break') else 'N'} | "
        f"Mom={getattr(er, 'momentum_quality', 'UNK')} | Trap={getattr(er, 'trap_risk', 'LOW')} | Decision={getattr(er, 'veteran_decision', 'IGNORE')} | Size={getattr(er, 'position_size', 'NO TRADE')}"
    )
    if should_print_console_state(state, state_print_counts):
        print(line1)
        print(line2)
        print(line3)
        state_print_counts[state] = state_print_counts.get(state, 0) + 1
    return line1, line2, line3, label, state, blocker

# =========================
# STATE HELPERS
# =========================

def prune_recent_events(store: Dict[str, List[float]], window_seconds: int):
    now = time.time()
    for pair in list(store.keys()):
        store[pair] = [t for t in store[pair] if now - t <= window_seconds]
        if not store[pair]:
            del store[pair]

def update_recent_hits(pair: str, did_hit: bool):
    now = time.time()
    if pair not in recent_hits:
        recent_hits[pair] = []
    recent_hits[pair] = [t for t in recent_hits[pair] if now - t <= HIT_WINDOW_SECONDS]
    if did_hit:
        recent_hits[pair].append(now)
    return len(recent_hits[pair])

def update_recent_watch_hits(pair: str, did_watch: bool):
    now = time.time()
    if pair not in recent_watch_hits:
        recent_watch_hits[pair] = []
    recent_watch_hits[pair] = [t for t in recent_watch_hits[pair] if now - t <= HIT_WINDOW_SECONDS]
    if did_watch:
        recent_watch_hits[pair].append(now)
    return len(recent_watch_hits[pair])

def update_watch_cycle_streak(current_watch_pairs: set):
    current_set = set(current_watch_pairs)
    for pair in list(watch_cycle_streaks.keys()):
        if pair not in current_set:
            watch_cycle_streaks[pair] = 0
    for pair in current_set:
        watch_cycle_streaks[pair] = watch_cycle_streaks.get(pair, 0) + 1
    return dict(watch_cycle_streaks)

def get_star_label(hit_count: int) -> str:
    if hit_count <= 0:
        return ""
    if hit_count == 1:
        return "☆"
    if hit_count == 2:
        return "⭐"
    if hit_count == 3:
        return "⭐⭐"
    return "⭐⭐⭐"

def log_scan(er: EvalResult, hits: int, stars: str, btc_state: bool, regime_name: str = "BEAR"):
    try:
        with open("scanner_log.txt", "a", encoding="utf-8") as f:
            f.write(
                f"{dt.datetime.now()} | {er.wsname} | "
                f"price={er.price:.8f} | "
                f"RSI1={er.rsi_1m:.2f} | "
                f"RSI5={er.rsi_5m:.2f} | "
                f"MACD15={er.macd_hist_15m:.6f} | "
                f"VWAP={er.vwap_ny:.8f} | "
                f"HITS={hits} | "
                f"STARS={stars} | "
                f"BTC={btc_state} | REGIME={regime_name} | "
                f"ACCEL={er.flags.get('acceleration')} | "
                f"TREND={er.flags.get('trend_ok')} | "
                f"VOLSPIKE={er.flags.get('volume_spike')} | "
                f"STRUCTBREAK={er.flags.get('structure_break')} | "
                f"TRIGGERSCORE={er.trigger_score} | "
                f"TRADESCORE={er.trade_score} | "
                f"TRADEREADY={er.trade_ready}\n"
            )
    except Exception:
        pass

def build_regime_settings(regime_name: str) -> dict:
    base = dict(REGIME_RULES.get(regime_name, REGIME_RULES["BEAR"]))
    base["name"] = regime_name
    base["pair_limit"] = BTC_REGIME_PAIR_LIMITS.get(regime_name, TOP_N_PAIRS)
    base["pair_refresh_seconds"] = BTC_REGIME_REFRESH_SECONDS.get(regime_name, PAIR_REFRESH_SECONDS)
    base["scan_sleep_seconds"] = BTC_REGIME_SCAN_SLEEP_SECONDS.get(regime_name, SCAN_SLEEP_SECONDS)
    return base

def classify_btc_regime() -> dict:
    """v17 Veteran Regime Model.

    Classifies BTC into market phases based on control, momentum direction, and volatility.
    This avoids the old problem of calling the market bullish just because price is above VWAP.
    """
    try:
        res5 = get_ohlc("XBTUSD", 5)
        res15 = get_ohlc("XBTUSD", 15)
        res60 = get_ohlc("XBTUSD", 60)

        close5 = closes_from_ohlc(res5)
        close15 = closes_from_ohlc(res15)
        close60 = closes_from_ohlc(res60)

        if close5 is None or close15 is None or close60 is None:
            settings = build_regime_settings("CHOP")
            settings["reason"] = "BTC DATA INCOMPLETE"
            return settings

        price5 = float(close5[-1])
        price15 = float(close15[-1])
        price60 = float(close60[-1])

        vwap5 = vwap_from_ohlc(res5, 96)
        vwap15 = vwap_from_ohlc(res15, 96)
        vwap60 = vwap_from_ohlc(res60, 72)

        rsi5 = rsi(close5, 14)
        rsi15 = rsi(close15, 14)
        rsi60 = rsi(close60, 14)
        rsi15_prev = rsi(close15[:-2], 14) if len(close15) > 20 else float("nan")
        rsi60_prev = rsi(close60[:-1], 14) if len(close60) > 20 else float("nan")

        macd15 = macd_hist(close15, 12, 26, 9)
        macd60 = macd_hist(close60, 12, 26, 9)
        macd15_prev = macd_hist(close15[:-1], 12, 26, 9) if len(close15) > 40 else float("nan")
        macd60_prev = macd_hist(close60[:-1], 12, 26, 9) if len(close60) > 40 else float("nan")

        above_5 = vwap5 > 0 and price5 > vwap5
        above_15 = vwap15 > 0 and price15 > vwap15
        above_60 = vwap60 > 0 and price60 > vwap60
        near_15 = vwap15 > 0 and abs(price15 - vwap15) / vwap15 <= 0.004
        near_60 = vwap60 > 0 and abs(price60 - vwap60) / vwap60 <= 0.006

        rsi15_rising = not math.isnan(rsi15) and not math.isnan(rsi15_prev) and rsi15 > rsi15_prev + 0.75
        rsi60_rising = not math.isnan(rsi60) and not math.isnan(rsi60_prev) and rsi60 >= rsi60_prev
        rsi15_falling = not math.isnan(rsi15) and not math.isnan(rsi15_prev) and rsi15 < rsi15_prev - 0.75
        rsi_hot = not math.isnan(rsi15) and rsi15 >= 68

        macd15_rising = not math.isnan(macd15) and not math.isnan(macd15_prev) and macd15 > macd15_prev
        macd60_rising = not math.isnan(macd60) and not math.isnan(macd60_prev) and macd60 >= macd60_prev
        macd15_falling = not math.isnan(macd15) and not math.isnan(macd15_prev) and macd15 < macd15_prev
        macd_flat_or_down = not math.isnan(macd15) and not math.isnan(macd15_prev) and macd15 <= macd15_prev

        ret5 = pct_return(close5, 6)
        ret15 = pct_return(close15, 4)
        vol15 = realized_vol_pct(close15, 20)
        impulse5 = detect_impulse(close5)
        vol_state = classify_volatility_state(close15)

        expansion = (
            above_15 and above_60 and above_5
            and not math.isnan(rsi15) and rsi15 >= 55
            and not math.isnan(rsi60) and rsi60 >= 51
            and macd15 >= 0 and macd60 >= -0.00000001
            and rsi15_rising and macd15_rising
            and (impulse5 or ret5 > 0.20 or ret15 > 0.35)
        )
        accumulation = (
            (near_15 or above_15)
            and (near_60 or above_60)
            and not math.isnan(rsi15) and 45 <= rsi15 <= 58
            and not math.isnan(rsi60) and 45 <= rsi60 <= 58
            and vol_state in {"COMPRESSING", "NORMAL"}
            and not rsi15_falling
        )
        exhaustion = (
            (above_15 or above_60)
            and (rsi_hot or ret15 > 1.0)
            and macd_flat_or_down
            and not macd15_rising
        )
        distribution = (
            (above_15 or above_60)
            and (rsi15_falling or macd15_falling)
            and not expansion
        )

        if expansion:
            phase = "EXPANSION"
            reason = "BTC above 15M/1H VWAP with rising RSI/MACD and fresh momentum"
        elif exhaustion:
            phase = "EXHAUSTION"
            reason = "BTC elevated but momentum is hot/flattening; chase risk high"
        elif distribution:
            phase = "DISTRIBUTION"
            reason = "BTC price elevated but RSI/MACD momentum is weakening"
        elif accumulation:
            phase = "ACCUMULATION"
            reason = "BTC near/above VWAP with neutral-to-building momentum"
        else:
            phase = "CHOP"
            reason = "BTC lacks clean higher-timeframe control"

        settings = build_regime_settings(phase)
        settings["reason"] = reason
        settings["market_phase"] = phase
        settings["volatility_state"] = vol_state
        settings["price_5m"] = price5
        settings["price_15m"] = price15
        settings["price_60m"] = price60
        settings["rsi_5m"] = float(rsi5) if not math.isnan(rsi5) else float("nan")
        settings["rsi_15m"] = float(rsi15) if not math.isnan(rsi15) else float("nan")
        settings["rsi_60m"] = float(rsi60) if not math.isnan(rsi60) else float("nan")
        settings["macd_15m"] = float(macd15) if not math.isnan(macd15) else float("nan")
        settings["macd_60m"] = float(macd60) if not math.isnan(macd60) else float("nan")
        settings["macd_15m_prev"] = float(macd15_prev) if not math.isnan(macd15_prev) else float("nan")
        settings["above_vwap_5m"] = above_5
        settings["above_vwap_15m"] = above_15
        settings["above_vwap_60m"] = above_60
        settings["impulse_5m"] = impulse5
        settings["rsi15_rising"] = rsi15_rising
        settings["rsi15_falling"] = rsi15_falling
        settings["macd15_rising"] = macd15_rising
        settings["macd15_falling"] = macd15_falling
        settings["btc_15m_return_pct"] = round(ret15, 3)
        settings["btc_volatility_15m"] = round(vol15, 3)
        return settings
    except Exception:
        settings = build_regime_settings("CHOP")
        settings["reason"] = "BTC REGIME ERROR"
        return settings


def get_btc_regime_settings() -> dict:
    return classify_btc_regime()

# =========================
# MAIN
# =========================

def main():
    print(f"{Fore.CYAN}{Style.BRIGHT}=== STARTING Kraken A+ Scanner V3 ==={Style.RESET_ALL}")
    print(f"[{ts()}] Cloud pipeline: enabled={CLOUD_PUSH_ENABLED} repo={GITHUB_RADAR_REPO} branch={GITHUB_RADAR_BRANCH} path={GITHUB_RADAR_PATH} token_set={bool(GITHUB_RADAR_TOKEN)}")

    last_alert: Dict[str, float] = {}
    last_pool_refresh = 0.0
    picked: List[Tuple[str, dict]] = []
    market_caps: Dict[str, float] = {}

    asset_pairs = get_all_asset_pairs()
    usd_pairs = get_usd_pairs(asset_pairs)

    if USE_MARKET_CAP_GATE:
        market_caps = load_or_refresh_market_caps(
            cache_path=MARKET_CAP_CACHE_PATH,
            ttl_seconds=MARKET_CAP_TTL_SECONDS,
            fail_open=True,
        )
        if market_caps:
            print(f"[marketcap] loaded {len(market_caps):,} caps from cache/refresh")
        else:
            print("[marketcap] gate disabled (no cap data / fail-open)")

    picked = build_scan_pool(usd_pairs, BTC_REGIME_PAIR_LIMITS["WATCH"])

    if USE_MARKET_CAP_GATE and market_caps:
        before = len(picked)
        gated = []
        for pk, meta in picked:
            base = normalize_kraken_asset_code(meta.get("base", ""))
            base_norm = normalize_kraken_asset_code(base)
            mc = safe_float(market_caps.get(base_norm, 0.0), 0.0)
            if mc >= MIN_MARKET_CAP_USD:
                gated.append((pk, meta))
        picked = gated
        print(f"[marketcap] gate: {len(picked)}/{before} pairs >= ${MIN_MARKET_CAP_USD:,}")

    discord_startup_ping(total_pairs=len(usd_pairs), picked_pairs=len(picked))
    last_pool_refresh = time.time()
    last_market_cap_refresh = time.time()
    attack_hold_until = 0.0
    attack_invalidation_cycles = 0

    cycle_number = 0

    while True:
        cycle_number += 1
        cycle_start = time.time()
        watch_candidates = []
        cycle_results = []
        current_watch_pairs = set()
        state_print_counts = {"BLOCKED": 0, "EARLY": 0, "LATE": 0}
        pre_alerted_this_cycle = set()

        # BTC regime once per cycle
        raw_regime = get_btc_regime_settings()
        raw_regime_name = raw_regime.get("name", "BEAR")
        now_ts = time.time()

        invalid_attack = not (
            raw_regime.get("above_vwap_15m", False)
            and raw_regime.get("above_vwap_60m", False)
            and safe_float(raw_regime.get("rsi_15m", 0.0), 0.0) >= 52.0
            and safe_float(raw_regime.get("macd_15m", -1.0), -1.0) >= 0.0
        )

        if raw_regime_name in {"BULL_ATTACK", "EXPANSION"}:
            attack_hold_until = now_ts + ATTACK_HOLD_SECONDS
            attack_invalidation_cycles = 0
            regime = raw_regime
            regime["reason"] = raw_regime.get("reason", "BTC ATTACK TRIGGERED")
        elif attack_hold_until > now_ts:
            if invalid_attack:
                attack_invalidation_cycles += 1
            else:
                attack_invalidation_cycles = 0

            if attack_invalidation_cycles < ATTACK_INVALIDATION_CYCLES:
                regime = build_regime_settings("EXPANSION")
                for key in ("price_5m", "price_15m", "price_60m", "rsi_5m", "rsi_15m", "rsi_60m", "macd_15m", "macd_60m", "above_vwap_5m", "above_vwap_15m", "above_vwap_60m", "impulse_5m"):
                    if key in raw_regime:
                        regime[key] = raw_regime[key]
                regime["reason"] = f"ATTACK HOLD ACTIVE ({int(max(0, attack_hold_until - now_ts))}s left)"
            else:
                attack_hold_until = 0.0
                attack_invalidation_cycles = 0
                regime = raw_regime
        else:
            regime = raw_regime

        regime_name = regime.get("name", "BEAR")
        btc_ok = bool(regime.get("trade_allowed", regime_name != "BEAR"))
        premium_enabled = bool(regime.get("premium_enabled", False))
        pair_limit = int(regime.get("pair_limit", TOP_N_PAIRS))
        pair_refresh_seconds = int(regime.get("pair_refresh_seconds", PAIR_REFRESH_SECONDS))
        scan_sleep_seconds = int(regime.get("scan_sleep_seconds", SCAN_SLEEP_SECONDS))

        print(build_console_cycle_start(ts(), btc_ok, len(picked)))
        if not btc_ok:
            print(f"{Fore.RED}{Style.BRIGHT}GLOBAL FILTER: {regime_name}. Normal longs blocked; Sharpshooter/relative-strength names only.{Style.RESET_ALL}")
        print(f"[{ts()}] BTC regime this cycle: {btc_console_label(regime_name)} | reason: {regime.get('reason', 'n/a')}")

        # Optional background market-cap refresh. Runtime scanner never depends on it.
        if (
            REFRESH_MARKET_CAPS_DURING_RUNTIME
            and USE_MARKET_CAP_GATE
            and (time.time() - last_market_cap_refresh) >= RUNTIME_MARKET_CAP_REFRESH_SECONDS
        ):
            try:
                refreshed_caps = load_or_refresh_market_caps(
                    cache_path=MARKET_CAP_CACHE_PATH,
                    ttl_seconds=MARKET_CAP_TTL_SECONDS,
                    fail_open=True,
                )
                if refreshed_caps:
                    market_caps = refreshed_caps
                    print(f"[marketcap] background refresh loaded {len(market_caps):,} caps")
                last_market_cap_refresh = time.time()
            except Exception as e:
                print(f"[{ts()}] marketcap background refresh skipped: {e}")
                last_market_cap_refresh = time.time()

        # Refresh movers pool periodically
        if (time.time() - last_pool_refresh) >= pair_refresh_seconds:
            try:
                picked = build_scan_pool(usd_pairs, pair_limit)

                if USE_MARKET_CAP_GATE and market_caps:
                    before = len(picked)
                    gated = []
                    for pk, meta in picked:
                        base = normalize_kraken_asset_code(meta.get("base", ""))
                        base_norm = normalize_kraken_asset_code(base)
                        mc = safe_float(market_caps.get(base_norm, 0.0), 0.0)
                        if mc >= MIN_MARKET_CAP_USD:
                            gated.append((pk, meta))
                    picked = gated
                    print(f"[marketcap] gate: {len(picked)}/{before} pairs >= ${MIN_MARKET_CAP_USD:,}")

                last_pool_refresh = time.time()
            except Exception as e:
                print(f"[{ts()}] ERROR refreshing pool: {e}")

        try:
            pair_keys = [pk for pk, _ in picked]
            ticker_map = get_ticker(pair_keys)
        except Exception as e:
            print(f"[{ts()}] ERROR fetching ticker batch: {e}")
            time.sleep(3)
            continue

        n = len(picked)
        if n == 0:
            print(f"[{ts()}] Pool empty. Sleeping {scan_sleep_seconds}s...")
            time.sleep(scan_sleep_seconds)
            continue

        for idx, (pk, meta) in enumerate(picked, start=1):
            t = ticker_map.get(pk)
            if not t:
                ws = meta.get("wsname")
                t = ticker_map.get(ws, None)
            if not t:
                continue

            try:
                er = eval_pair(pk, meta, t, market_caps, regime)
                if er is None:
                    continue

                now = time.time()
                last = last_alert.get(pk, 0.0)
                cooldown_hit = (now - last) < COOLDOWN_SECONDS

                hits = update_recent_hits(er.wsname, er.is_aplus)
                stars = get_star_label(hits)

                er.hits_last_2h = hits
                er.stars = stars

                er.trade_score = compute_trade_score(
                    trend_ok=er.flags.get("trend_ok", False),
                    volume_spike=er.flags.get("volume_spike", False),
                    structure_break=er.flags.get("structure_break", False),
                    acceleration=er.flags.get("acceleration", False),
                    hits_last_2h=hits,
                    btc_ok=btc_ok,
                    vwap_accept=er.flags.get("vwap_accept", False),
                )
                # v17 Veteran filter: movement is not enough. Penalize fading momentum and trap risk.
                if er.momentum_quality == "BUILDING":
                    er.trade_score += 5
                elif er.momentum_quality == "WEAKENING":
                    er.trade_score -= 10
                elif er.momentum_quality == "FAILING":
                    er.trade_score -= 20
                if er.trap_risk == "MEDIUM":
                    er.trade_score -= 10
                elif er.trap_risk == "HIGH":
                    er.trade_score -= 25
                if er.volatility_state == "HIGH" and not er.flags.get("pullback", False):
                    er.trade_score -= 10
                er.trade_score = max(0, min(100, int(er.trade_score)))
                # v19 composite score is the primary tradability score. Use it to prevent low-quality momentum from ranking too high.
                if getattr(er, "composite_score", 0) > 0:
                    er.trade_score = max(0, min(100, int(round((er.trade_score * 0.45) + (er.composite_score * 0.55)))))
                phase_for_decision = regime.get("market_phase", regime_name) if isinstance(regime, dict) else regime_name
                chart_decision = _chart_read_for_app(er).get("timing", "") if "_chart_read_for_app" in globals() else ""
                er.veteran_decision = classify_veteran_decision(er.composite_score, er.trap_risk, er.momentum_quality, chart_decision)
                er.position_size = classify_position_size(er.composite_score, phase_for_decision, er.trap_risk, er.veteran_decision)
                er.decision_reason = build_decision_reason(er, phase_for_decision)

                er.trade_ready = False

                log_scan(er, hits, stars, btc_ok, regime_name)

                line1, line2, line3, label, state, blocker = print_result_line(er, idx, n, cooldown_hit, btc_ok, state_print_counts, regime, regime_name)
                if idx % 10 == 0:
                    print(f"[{ts()}] heartbeat | scanned {idx}/{n} pairs this cycle...")

                is_watch_candidate = (
                    label == "Watch"
                    and er.trigger_score >= int(regime.get("watch_min_score", WATCH_MIN_SCORE))
                )
                watch_hits = update_recent_watch_hits(er.wsname, is_watch_candidate)
                projected_streak = (watch_cycle_streaks.get(er.wsname, 0) + 1) if is_watch_candidate else 0

                er.trade_ready = False

                cycle_results.append({
                    "pair_key": pk,
                    "er": er,
                    "label": label,
                    "state": state,
                    "blocker": blocker,
                    "watch_hits": watch_hits,
                    "scan_idx": idx,
                    "line1": line1,
                    "line2": line2,
                    "line3": line3,
                })

                if is_watch_candidate:
                    quality = billboard_quality_filter(
                        er,
                        min_score=int(regime.get("watch_min_score", WATCH_MIN_SCORE)),
                    )
                    if quality["allow"]:
                        current_watch_pairs.add(er.wsname)
                        watch_candidates.append({
                            "pair_key": pk,
                            "er": er,
                            "line1": line1,
                            "line2": line2,
                            "line3": line3,
                            "watch_hits": watch_hits,
                            "projected_streak": projected_streak,
                            "scan_idx": idx,
                            "billboard_score": quality["score"],
                            "billboard_penalty": quality["penalty"],
                            "billboard_reasons": quality["reasons"],
                        })
                    else:
                        print(f"[{ts()}] Billboard filtered {er.wsname}: score={quality['score']} | {', '.join(quality['reasons'][:3])}")

            except Exception as e:
                print(f"[{ts()}] Eval error on {meta.get('wsname', pk)}: {e}")
                traceback.print_exc()

            time.sleep(PER_PAIR_THROTTLE_SECONDS)

        prune_recent_events(recent_hits, HIT_WINDOW_SECONDS)
        prune_recent_events(recent_watch_hits, HIT_WINDOW_SECONDS)
        streaks = update_watch_cycle_streak(current_watch_pairs)

        current_setup_pairs = {
            item["er"].wsname
            for item in cycle_results
            if item["state"] in {"BUILDING", "EARLY", "READY"} and item["er"].flags.get("trend_ok", False) and item["er"].flags.get("vwap_accept", False)
        }
        setup_streaks, setup_started_map = update_setup_tracking(current_setup_pairs)

        current_ranks = {}
        sector_counts: Dict[str, int] = {}
        sector_scores: Dict[str, int] = {}
        strong_sectors: List[str] = []

        if watch_candidates:
            full_watch = sorted(
                watch_candidates,
                key=lambda x: (
                    x.get("billboard_score", 0),
                    watch_rank_tuple(
                        x["er"],
                        x.get("watch_hits", 0),
                        streaks.get(x["er"].wsname, 0),
                    ),
                ),
                reverse=True,
            )

            sector_counts, sector_scores, strong_sectors = compute_sector_flow(full_watch)

            for rank, item in enumerate(full_watch, start=1):
                er = item["er"]
                streak = streaks.get(er.wsname, 0)
                er.sector_boost = SECTOR_BOOST_SCORE if er.sector in strong_sectors else 0
                item["streak"] = streak
                item["rank"] = rank
                item["rank_change"] = rank_change_label(er.wsname, rank)
                item["fresh_marker"] = fresh_breakout_marker(streak, er)
                item["effective_trade_score"] = min(100, er.trade_score + er.sector_boost)
                item["sector_count"] = sector_counts.get(er.sector, 0)
                item["sector_strong"] = er.sector in strong_sectors
                item["setup_cycles"] = setup_streaks.get(er.wsname, 0)
                item["setup_age_seconds"] = max(0.0, time.time() - setup_started_map.get(er.wsname, time.time())) if er.wsname in setup_started_map else 0.0
                readiness_score, readiness_label = compute_entry_readiness(
                    er,
                    regime_name=regime_name,
                    effective_trade_score=item["effective_trade_score"],
                    watch_hits=item.get("watch_hits", 0),
                    streak=streak,
                    sector_count=item["sector_count"],
                    sector_strong=item["sector_strong"],
                    setup_cycles=item["setup_cycles"],
                )
                item["entry_readiness_score"] = readiness_score
                item["entry_readiness_label"] = readiness_label
                env_result = environment_weight_score(
                    er,
                    regime_name=regime_name,
                    sector_count=item["sector_count"],
                    sector_strong=item["sector_strong"],
                    entry_readiness_score=readiness_score,
                    entry_readiness_label=readiness_label,
                )
                item["environment_score"] = env_result["final_score"]
                item["environment_tier"] = env_result["tier"]
                item["environment_adjustments"] = env_result["adjustments"]
                sharpshooter_bypass = (
                    er.veteran_decision == "SHARPSHOOTER"
                    and er.composite_score >= 75
                    and er.relative_strength_pct >= 0.35
                    and er.trap_risk != "HIGH"
                    and er.momentum_quality in {"BUILDING", "STABLE"}
                )
                premium_candidate = (
                    (premium_enabled or sharpshooter_bypass)
                    and (btc_ok or sharpshooter_bypass)
                    and er.flags.get("vwap_accept", False)
                    and item.get("sector_count", 0) >= 1
                    and er.trigger_score >= PREMIUM_MIN_TRIGGER
                    and item.get("effective_trade_score", er.trade_score) >= PREMIUM_MIN_TRADE_SCORE
                    and er.composite_score >= 72
                    and item.get("environment_score", er.composite_score) >= 70
                    and er.trap_risk != "HIGH"
                    and er.momentum_quality != "FAILING"
                    and er.veteran_decision in {"TRADE", "WATCH", "SHARPSHOOTER"}
                    and streak >= PREMIUM_MIN_BOARD_CYCLES
                    and item.get("watch_hits", 0) >= PREMIUM_MIN_WATCH_HITS
                )
                er.trade_ready = premium_candidate
                current_ranks[er.wsname] = rank

            # V22: final board ranking uses environment-weighted probability context.
            full_watch = sorted(
                full_watch,
                key=lambda x: (
                    x.get("environment_score", 0),
                    x.get("entry_readiness_score", 0),
                    x.get("effective_trade_score", x["er"].trade_score),
                    x["er"].trigger_score,
                    x.get("watch_hits", 0),
                ),
                reverse=True,
            )
            current_ranks = {}
            for rank, item in enumerate(full_watch, start=1):
                er = item["er"]
                item["rank"] = rank
                item["rank_change"] = rank_change_label(er.wsname, rank)
                current_ranks[er.wsname] = rank

            top_watch = full_watch[:WATCH_TOP_N]

            top3_summary = build_top3_summary(top_watch)
            sector_summary = build_sector_summary(sector_counts, sector_scores, strong_sectors)

            lines = []
            for item in top_watch:
                er = item["er"]
                watch_hits = item.get("watch_hits", 0)
                streak = item.get("streak", 0)
                rank = item.get("rank", 0)
                rank_change = item.get("rank_change", "NEW")
                fresh_marker = item.get("fresh_marker", "")
                eff_trade = item.get("effective_trade_score", er.trade_score)
                entry_lines = build_discord_entry(
                    rank=rank,
                    er=er,
                    watch_hits=watch_hits,
                    streak=streak,
                    rank_change=rank_change,
                    fresh_marker=f" {fresh_marker}" if fresh_marker else "",
                    eff_trade=eff_trade,
                )
                lines.extend(entry_lines)

            if WATCH_SEND_EVERY_CYCLE and WATCH_WEBHOOK_URL:
                msg = build_watch_block(lines, ts(), btc_ok, top3_summary, sector_summary)
                ok = send_watch_webhook(msg)
                print(f"[{ts()}] Watch leaderboard " + (f"{Fore.GREEN}sent{Style.RESET_ALL}" if ok else f"{Fore.RED}failed{Style.RESET_ALL}"))

            radar_image_path = None
            try:
                radar_image_path = render_radar_report_image(
                    full_watch[:CONTENT_POST_TOP_N],
                    regime_name,
                    cycle_time=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    active_pairs=n,
                    cycle_number=cycle_number,
                    sector_counts=sector_counts,
                    btc_reason=btc_reason,
                    output_path=RADAR_IMAGE_PATH,
                )
                if radar_image_path:
                    print(f"[{ts()}] Radar image ready: {radar_image_path}")
                    if RADAR_IMAGE_SEND_TO_WATCH_EACH_CYCLE and WATCH_WEBHOOK_URL:
                        send_discord_image(WATCH_WEBHOOK_URL, radar_image_path, build_radar_caption(full_watch[:CONTENT_POST_TOP_N], regime_name))

                    # Free Discord radar image: clean, meaningful, non-spammy.
                    should_free_post, free_reason = should_send_free_radar_update(full_watch[:CONTENT_POST_TOP_N], regime_name)
                    if should_free_post:
                        free_caption = build_free_radar_caption(full_watch[:CONTENT_POST_TOP_N], regime_name, free_reason)
                        free_ok = send_discord_image(FREE_RADAR_WEBHOOK_URL, radar_image_path, free_caption)
                        print(f"[{ts()}] Free radar image " + (f"{Fore.GREEN}sent{Style.RESET_ALL}" if free_ok else f"{Fore.RED}failed{Style.RESET_ALL}") + f" | {free_reason}")
                    else:
                        print(f"[{ts()}] Free radar image skipped | {free_reason}")
            except Exception as e:
                print(f"[{ts()}] Radar image render/send error: {e}")

            pre_alert_candidates = []
            for item in full_watch:
                er = item["er"]
                watch_hits = item.get("watch_hits", 0)
                streak = item.get("streak", 0)
                effective_trade_score = item.get("effective_trade_score", er.trade_score)
                if is_pre_aplus_candidate(
                    er,
                    streak=streak,
                    watch_hits=watch_hits,
                    effective_trade_score=effective_trade_score,
                    regime_name=regime_name,
                ):
                    pre_alert_candidates.append(item)

            for item in pre_alert_candidates[:PRE_ALERT_TOP_N]:
                er = item["er"]
                rank_now = item.get("rank", 0)
                if er.wsname in pre_alerted_this_cycle:
                    continue
                if not should_send_pre_alert(er.wsname, rank_now):
                    continue
                pre_msg = build_pre_aplus_message(
                    er,
                    rank_now=rank_now,
                    watch_hits=item.get("watch_hits", 0),
                    streak=item.get("streak", 0),
                    effective_trade_score=item.get("effective_trade_score", er.trade_score),
                    sector_count=item.get("sector_count", 0),
                    sector_strong=item.get("sector_strong", False),
                    regime_name=regime_name,
                    entry_readiness_score=item.get("entry_readiness_score", 0),
                    entry_readiness_label=item.get("entry_readiness_label", "EARLY"),
                    setup_cycles=item.get("setup_cycles", 0),
                    setup_age_text=format_setup_age(item.get("setup_age_seconds", 0.0)),
                )
                if RADAR_IMAGE_SEND_TO_WATCH_ON_PREALERT and radar_image_path:
                    pre_ok = send_discord_image(WATCH_WEBHOOK_URL, radar_image_path, build_radar_caption(full_watch[:CONTENT_POST_TOP_N], regime_name))
                else:
                    pre_ok = send_watch_webhook(pre_msg)
                if pre_ok:
                    pre_alerted_this_cycle.add(er.wsname)
                    mark_pre_alert_sent(er.wsname, rank_now)

            for item in full_watch:
                er = item["er"]
                pair_key = item.get("pair_key")
                rank_now = item.get("rank", 0)
                rank_change = item.get("rank_change", "NEW")
                effective_trade_score = item.get("effective_trade_score", er.trade_score)
                sharpshooter_bypass = (
                    er.veteran_decision == "SHARPSHOOTER"
                    and er.composite_score >= 75
                    and er.relative_strength_pct >= 0.35
                    and er.trap_risk != "HIGH"
                    and er.momentum_quality in {"BUILDING", "STABLE"}
                )
                premium_candidate = (
                    (premium_enabled or sharpshooter_bypass)
                    and (btc_ok or sharpshooter_bypass)
                    and er.flags.get("vwap_accept", False)
                    and item.get("sector_count", 0) >= 1
                    and er.trigger_score >= PREMIUM_MIN_TRIGGER
                    and effective_trade_score >= PREMIUM_MIN_TRADE_SCORE
                    and er.composite_score >= 72
                    and item.get("environment_score", er.composite_score) >= 70
                    and er.trap_risk != "HIGH"
                    and er.momentum_quality != "FAILING"
                    and er.veteran_decision in {"TRADE", "WATCH", "SHARPSHOOTER"}
                    and item.get("streak", 0) >= PREMIUM_MIN_BOARD_CYCLES
                    and item.get("watch_hits", 0) >= PREMIUM_MIN_WATCH_HITS
                )

                # BTC is a throttle, not a prison: only relative-strength sharpshooters can bypass weak BTC.
                er.trade_ready = premium_candidate
                if premium_candidate and (pair_key is not None) and (not ((time.time() - last_alert.get(pair_key, 0.0)) < COOLDOWN_SECONDS)):
                    msg = build_discord_aplus_message(
                        er,
                        btc_ok,
                        board_cycles=item.get("streak", 0),
                        watch_hits=item.get("watch_hits", 0),
                        rank_now=rank_now,
                        rank_change=rank_change,
                        fresh_breakout=bool(item.get("fresh_marker")),
                        effective_trade_score=effective_trade_score,
                        sector_count=item.get("sector_count", 0),
                        sector_strong=item.get("sector_strong", False),
                        regime_name=regime_name,
                        entry_readiness_score=item.get("entry_readiness_score", 0),
                        entry_readiness_label=item.get("entry_readiness_label", "EARLY"),
                        setup_cycles=item.get("setup_cycles", 0),
                        setup_age_text=format_setup_age(item.get("setup_age_seconds", 0.0)),
                    )
                    if RADAR_IMAGE_SEND_TO_MAIN_ON_TRADE_READY and radar_image_path:
                        ok = send_discord_image(DISCORD_WEBHOOK_URL, radar_image_path, build_radar_caption(full_watch[:CONTENT_POST_TOP_N], regime_name))
                    else:
                        ok = send_discord_webhook(msg)
                    if ok:
                        last_alert[pair_key] = time.time()

            leaderboard_prev_ranks.clear()
            leaderboard_prev_ranks.update(current_ranks)
        else:
            leaderboard_prev_ranks.clear()

        cycle_watch = sorted(
            cycle_results,
            key=lambda x: (x.get("environment_score", x["er"].trigger_score), x.get("entry_readiness_score", 0), x["er"].trigger_score, x.get("watch_hits", 0)),
            reverse=True,
        )
        if not sector_counts and cycle_watch:
            temp_sector_counts: Dict[str, int] = {}
            for item in cycle_watch[:WATCH_TOP_N]:
                sec = item["er"].sector
                temp_sector_counts[sec] = temp_sector_counts.get(sec, 0) + 1
            sector_counts = temp_sector_counts
        state_counts = {"READY": 0, "BUILDING": 0, "EARLY": 0, "BLOCKED": 0, "LATE": 0}
        for item in cycle_results:
            state_counts[item["state"]] = state_counts.get(item["state"], 0) + 1
        strongest_item = cycle_watch[0] if cycle_watch else None
        blocker_reason = strongest_blocker_reason(state_counts, btc_ok)
        if state_counts.get("BLOCKED", 0) > MAX_BLOCKED_PRINT:
            print(f"{Fore.RED}BLOCKED entries compressed: showing {MAX_BLOCKED_PRINT} of {state_counts.get('BLOCKED', 0)}{Style.RESET_ALL}")
        if state_counts.get("EARLY", 0) > MAX_EARLY_PRINT:
            print(f"{Fore.YELLOW}EARLY entries compressed: showing {MAX_EARLY_PRINT} of {state_counts.get('EARLY', 0)}{Style.RESET_ALL}")
        if state_counts.get("LATE", 0) > MAX_LATE_PRINT:
            print(f"{Fore.MAGENTA}LATE entries compressed: showing {MAX_LATE_PRINT} of {state_counts.get('LATE', 0)}{Style.RESET_ALL}")
        print(build_console_cycle_story(ts(), btc_ok, n, state_counts, cycle_watch[:5], sector_counts, strongest_item, blocker_reason))
        if cycle_watch:
            print(f"{Fore.CYAN}{Style.BRIGHT}MINI BOARD{Style.RESET_ALL}")
            for pos, item in enumerate(cycle_watch[:5], start=1):
                er = item["er"]
                state = item["state"]
                blocker = item["blocker"]
                print(
                    f"#{pos} {color_symbol(er.wsname)} | {color_state(state)} | "
                    f"ENV{color_score(item.get('environment_score', er.trigger_score))} {item.get('environment_tier', '')} | "
                    f"T{color_score(er.trigger_score)} TR{color_score(item.get('effective_trade_score', er.trade_score))} C{color_score(er.confidence)} | "
                    f"Blocker={Fore.YELLOW}{blocker}{Style.RESET_ALL}"
                )
            print(console_divider("-"))

        try:
            export_ok = export_radar_state_json(
                cycle_watch[:10],
                regime_name=regime_name,
                regime=regime,
                active_pairs=n,
                cycle_number=cycle_number,
                sector_counts=sector_counts,
                state_counts=state_counts,
            )
            if export_ok:
                print(f"[{ts()}] Radar app state updated: {RADAR_STATE_JSON_PATH}")
                cloud_ok = push_radar_state_to_github(RADAR_STATE_JSON_PATH, force=True)
                print(f"[{ts()}] Cloud push status: {'OK' if cloud_ok else 'SKIPPED/FAILED'}")
                perf_ok = update_performance_history(cycle_watch[:5], cycle_number, regime_name, PERFORMANCE_JSON_PATH)
                if perf_ok:
                    perf_cloud_ok = push_performance_to_github(PERFORMANCE_JSON_PATH, force=True)
                    print(f"[{ts()}] Performance cloud push status: {'OK' if perf_cloud_ok else 'SKIPPED/FAILED'}")
        except Exception as e:
            print(f"[{ts()}] Radar JSON/performance export error: {e}")

        try:
            content_post = build_content_post(cycle_watch[:CONTENT_POST_TOP_N], regime_name, cycle_time=dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            write_content_post(content_post)
            print(f"{Fore.GREEN}{Style.BRIGHT}CONTENT POST READY{Style.RESET_ALL}")
            print(console_divider("="))
            print(content_post)
            print(console_divider("="))
        except Exception as e:
            print(f"[{ts()}] Content post error: {e}")

        try:
            sector_snapshot = compute_sector_snapshot(cycle_watch, cycle_results)
            if SECTOR_WEBHOOK_URL and (cycle_number % SECTOR_WEBHOOK_EVERY_N_CYCLES == 0):
                sector_msg = build_sector_webhook_block(ts(), btc_ok, sector_snapshot)
                sector_ok = send_sector_webhook(sector_msg)
                print(f"[{ts()}] Sector webhook {'sent' if sector_ok else 'failed'}")
        except Exception as e:
            print(f"[{ts()}] Sector webhook error: {e}")

        elapsed = time.time() - cycle_start
        print(f"[{ts()}] Cycle complete in {elapsed:.1f}s. Sleeping {scan_sleep_seconds}s...")
        time.sleep(scan_sleep_seconds)

if __name__ == "__main__":
    main()
