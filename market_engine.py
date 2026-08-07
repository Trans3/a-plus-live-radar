from __future__ import annotations
from collections import defaultdict
from math import sqrt

def _num(v, default=0.0):
    try:
        return default if v is None else float(v)
    except (TypeError, ValueError):
        return default

def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))

def _sector_summary(flights):
    buckets = defaultdict(lambda: {"moves": [], "count": 0, "departures": 0, "landings": 0, "actionable": 0})
    for f in flights:
        sector = str(f.get("sector") or "OTHER").upper()
        b = buckets[sector]
        b["moves"].append(_num(f.get("change_1h")))
        b["count"] += 1
        if str(f.get("phase") or "") in {"Taxiing", "Takeoff", "Climbing"}:
            b["departures"] += 1
        if str(f.get("phase") or "") in {"Descending", "Landing"}:
            b["landings"] += 1
        if str(f.get("action") or "") in {"ENTER", "WAIT"}:
            b["actionable"] += 1
    rows = []
    for sector, b in buckets.items():
        avg = sum(b["moves"]) / len(b["moves"]) if b["moves"] else 0.0
        rows.append({
            "sector": sector,
            "avg_1h": round(avg, 3),
            "count": b["count"],
            "departures": b["departures"],
            "landings": b["landings"],
            "actionable": b["actionable"],
        })
    rows.sort(key=lambda r: (r["actionable"], r["departures"], r["avg_1h"]), reverse=True)
    return rows

def build_market_state(pair_states, market_regime="WAITING"):
    flights = list(pair_states)
    verified = [f for f in flights if f.get("vwap_dist") is not None]
    sample = verified if verified else flights

    if not sample:
        return {
            "buyer_pressure": 50, "seller_pressure": 50, "opportunity": 0,
            "market_health": 0, "breadth": 0, "expansion_pressure": 0,
            "synchronization": 0, "avg_1h_move": 0.0, "momentum": "Quiet",
            "visibility": "Poor", "wind": "Neutral", "turbulence": "Low",
            "leading_sector": "OTHER", "sector_flow": [], "market_mode": "DEAD_AIR",
            "recommended_mode": "Stand By", "recommended_mode_note": "Not enough radar data yet.",
            "verified_pairs": 0, "actionable_pairs": 0, "total_pairs": 0,
        }

    buyer_points = total_points = 0.0
    positive_1h = actionable = structure_count = above_vwap = 0
    momentum_count = compression_count = reload_count = enter_count = late_count = 0
    moves = []
    directions = []

    for f in sample:
        ch1 = _num(f.get("change_1h"))
        r1 = _num(f.get("rsi_1m"), 50)
        r5 = _num(f.get("rsi_5m"), 50)
        vwap = str(f.get("vwap") or "")
        action = str(f.get("action") or "")
        phase = str(f.get("phase") or "")
        read = str(f.get("read_state") or "")

        moves.append(ch1)
        directions.append(1 if ch1 > 0 else -1 if ch1 < 0 else 0)

        total_points += 2
        if vwap in {"Holding", "Above"}:
            buyer_points += 2
            above_vwap += 1
        elif vwap == "Testing":
            buyer_points += 1

        total_points += 1
        if ch1 > 0:
            buyer_points += 1
            positive_1h += 1

        total_points += 2
        if r5 >= 55:
            buyer_points += 1
            momentum_count += 1
        if r1 >= 50:
            buyer_points += 1

        total_points += 1
        if action in {"ENTER", "WAIT"}:
            buyer_points += 1
            actionable += 1
        if action == "ENTER":
            enter_count += 1

        if read in {"RELOAD READY", "RELOAD WATCH", "CONTINUATION WATCH", "PRESSURE BUILDING"}:
            structure_count += 1
        if read in {"RELOAD READY", "RELOAD WATCH"}:
            reload_count += 1
        if read == "PRESSURE BUILDING":
            compression_count += 1
        if phase in {"Descending", "Landing"}:
            late_count += 1

    buyers = int(round(_clamp((buyer_points / total_points) * 100))) if total_points else 50
    sellers = 100 - buyers
    breadth = int(round((positive_1h / len(sample)) * 100))

    opp_vals = [_num(f.get("remaining")) for f in sample if str(f.get("action") or "") not in {"SKIP", "HOLD / SKIP"}]
    opportunity = int(round(sum(opp_vals) / len(opp_vals))) if opp_vals else 0
    opportunity = int(_clamp(opportunity))

    avg_1h = sum(moves) / len(moves)
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

    up = sum(1 for d in directions if d > 0)
    down = sum(1 for d in directions if d < 0)
    synchronization = int(round((max(up, down) / len(sample)) * 100))

    vwap_breadth = above_vwap / len(sample) * 100
    momentum_breadth = momentum_count / len(sample) * 100
    structure_breadth = structure_count / len(sample) * 100
    compression_breadth = compression_count / len(sample) * 100

    expansion_pressure = int(round(_clamp(
        0.28 * vwap_breadth +
        0.24 * momentum_breadth +
        0.22 * structure_breadth +
        0.14 * synchronization +
        0.12 * max(compression_breadth, breadth)
    )))

    late_pct = late_count / len(sample)
    structure_pct = structure_count / len(sample)
    health = int(round(_clamp(
        0.30 * buyers +
        0.20 * breadth +
        0.20 * opportunity +
        0.15 * synchronization +
        0.15 * expansion_pressure +
        10 * structure_pct -
        18 * late_pct
    )))

    visibility = "Excellent" if health >= 75 and breadth >= 60 else "Good" if health >= 55 else "Fair" if health >= 40 else "Poor"
    wind = "Tailwind" if buyers >= 65 else "Headwind" if buyers <= 35 else "Crosswind"

    variance = sum((x - avg_1h) ** 2 for x in moves) / len(moves)
    spread = sqrt(variance)
    turbulence = "High" if spread >= 2.0 else "Medium" if spread >= 0.9 else "Low"

    sectors = _sector_summary(flights)
    leading_sector = sectors[0]["sector"] if sectors else "OTHER"

    regime = str(market_regime).upper()
    if regime in {"BEAR", "DISTRIBUTION", "EXHAUSTION"} or buyers < 35:
        market_mode = "EXHAUSTION"
    elif expansion_pressure >= 78 and synchronization >= 65:
        market_mode = "SPRING_LOADED"
    elif expansion_pressure >= 60 and buyers >= 55:
        market_mode = "BUILDING_PRESSURE"
    elif buyers >= 60 and enter_count >= 2:
        market_mode = "EXPANSION"
    elif reload_count >= 2:
        market_mode = "RELOAD"
    elif health < 35:
        market_mode = "DEAD_AIR"
    else:
        market_mode = "MIXED_AIRSPACE"

    if regime in {"BEAR", "DISTRIBUTION", "EXHAUSTION"} or buyers < 38:
        recommended = "Defensive"
        note = "Protect capital. Avoid forcing long momentum entries."
    elif reload_count >= 2 and buyers >= 50:
        recommended = "Sharpshooter Reloads"
        note = "Favor 1m reloads that rejoin stronger 5m structure."
    elif enter_count >= 2 and buyers >= 60 and opportunity >= 60:
        recommended = "Continuation"
        note = "Conditions support selective confirmed momentum entries."
    elif opportunity < 40:
        recommended = "Wait for Reset"
        note = "Control may exist, but clean entry opportunity is limited."
    else:
        recommended = "Selective"
        note = "Trade only the strongest confirmed departures."

    return {
        "buyer_pressure": buyers,
        "seller_pressure": sellers,
        "opportunity": opportunity,
        "market_health": health,
        "breadth": breadth,
        "expansion_pressure": expansion_pressure,
        "synchronization": synchronization,
        "avg_1h_move": round(avg_1h, 3),
        "momentum": momentum,
        "visibility": visibility,
        "wind": wind,
        "turbulence": turbulence,
        "leading_sector": leading_sector,
        "sector_flow": sectors,
        "market_mode": market_mode,
        "recommended_mode": recommended,
        "recommended_mode_note": note,
        "verified_pairs": len(verified),
        "actionable_pairs": actionable,
        "total_pairs": len(flights),
    }

if __name__ == "__main__":
    demo = [
        {"pair":"SOL/USD","vwap":"Holding","vwap_dist":0.2,"change_1h":1.1,"rsi_1m":57,"rsi_5m":63,"action":"WAIT","phase":"Takeoff","read_state":"RELOAD WATCH","remaining":78,"sector":"L1"},
        {"pair":"FET/USD","vwap":"Above","vwap_dist":0.5,"change_1h":1.8,"rsi_1m":54,"rsi_5m":66,"action":"ENTER","phase":"Takeoff","read_state":"RELOAD READY","remaining":88,"sector":"AI"},
    ]
    print(build_market_state(demo, "PREBULL"))
