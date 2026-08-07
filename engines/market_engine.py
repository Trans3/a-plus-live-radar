from __future__ import annotations

"""
A+ Radar - Market Command Engine
--------------------------------
Consumes per-pair radar states and returns one aggregate market state for the UI.

Design goals:
- Stay backwards-compatible with the existing Radar keys.
- Separate bullish participation from simple directional synchronization.
- Detect expansion, pressure-building, reload, exhaustion, and dead-air states.
- Penalize late/chasing conditions.
- Expose enough diagnostics for the UI without forcing UI-side calculations.

Expected pair-state fields (all optional):
    pair, sector, change_1h, rsi_1m, rsi_5m, vwap, vwap_dist,
    action, phase, read_state, remaining
"""

from collections import defaultdict
from math import sqrt
from typing import Any, Dict, Iterable, List


BULLISH_REGIMES = {"BULL", "PREBULL", "EXPANSION", "ACCUMULATION"}
DEFENSIVE_REGIMES = {"BEAR", "DISTRIBUTION", "EXHAUSTION"}

BULLISH_VWAP_STATES = {"HOLDING", "ABOVE"}
TESTING_VWAP_STATES = {"TESTING"}

ACTIONABLE_ACTIONS = {"ENTER", "WAIT"}
SKIP_ACTIONS = {"SKIP", "HOLD / SKIP"}

DEPARTURE_PHASES = {"TAXIING", "TAKEOFF", "CLIMBING"}
LATE_PHASES = {"DESCENDING", "LANDING"}

STRUCTURE_READS = {
    "RELOAD READY",
    "RELOAD WATCH",
    "CONTINUATION WATCH",
    "PRESSURE BUILDING",
}
RELOAD_READS = {"RELOAD READY", "RELOAD WATCH"}
COMPRESSION_READS = {"PRESSURE BUILDING"}


def _num(v: Any, default: float = 0.0) -> float:
    try:
        return default if v is None else float(v)
    except (TypeError, ValueError):
        return default


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _text(v: Any) -> str:
    return str(v or "").strip().upper()


def _pct(count: int, total: int) -> float:
    return (count / total * 100.0) if total else 0.0


def _empty_state() -> Dict[str, Any]:
    return {
        "buyer_pressure": 50,
        "seller_pressure": 50,
        "opportunity": 0,
        "market_health": 0,
        "breadth": 0,
        "expansion_pressure": 0,
        "synchronization": 0,
        "bullish_synchronization": 0,
        "bearish_synchronization": 0,
        "avg_1h_move": 0.0,
        "move_dispersion": 0.0,
        "momentum": "Quiet",
        "visibility": "Poor",
        "wind": "Neutral",
        "turbulence": "Low",
        "leading_sector": "OTHER",
        "sector_flow": [],
        "market_mode": "DEAD_AIR",
        "recommended_mode": "Stand By",
        "recommended_mode_note": "Not enough radar data yet.",
        "market_bias": "NEUTRAL",
        "signal_quality": "LOW",
        "sample_confidence": 0,
        "verified_ratio": 0,
        "vwap_breadth": 0,
        "momentum_breadth": 0,
        "structure_breadth": 0,
        "compression_breadth": 0,
        "late_pct": 0,
        "enter_pairs": 0,
        "reload_pairs": 0,
        "late_pairs": 0,
        "verified_pairs": 0,
        "actionable_pairs": 0,
        "total_pairs": 0,
    }


def _sector_summary(flights: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    buckets = defaultdict(
        lambda: {
            "moves": [],
            "count": 0,
            "positive": 0,
            "above_vwap": 0,
            "departures": 0,
            "landings": 0,
            "actionable": 0,
            "enters": 0,
        }
    )

    for f in flights:
        sector = _text(f.get("sector")) or "OTHER"
        b = buckets[sector]

        move = _num(f.get("change_1h"))
        action = _text(f.get("action"))
        phase = _text(f.get("phase"))
        vwap = _text(f.get("vwap"))

        b["moves"].append(move)
        b["count"] += 1
        if move > 0:
            b["positive"] += 1
        if vwap in BULLISH_VWAP_STATES:
            b["above_vwap"] += 1
        if phase in DEPARTURE_PHASES:
            b["departures"] += 1
        if phase in LATE_PHASES:
            b["landings"] += 1
        if action in ACTIONABLE_ACTIONS:
            b["actionable"] += 1
        if action == "ENTER":
            b["enters"] += 1

    rows: List[Dict[str, Any]] = []
    for sector, b in buckets.items():
        avg = sum(b["moves"]) / len(b["moves"]) if b["moves"] else 0.0
        breadth = _pct(b["positive"], b["count"])
        vwap_breadth = _pct(b["above_vwap"], b["count"])

        # Sector score rewards broad participation and actionable departures,
        # not just one coin making a large move.
        score = _clamp(
            0.28 * breadth
            + 0.24 * vwap_breadth
            + 18.0 * (b["actionable"] / max(1, b["count"]))
            + 16.0 * (b["departures"] / max(1, b["count"]))
            + 10.0 * (b["enters"] / max(1, b["count"]))
            + min(max(avg, -3.0), 3.0) * 4.0
            - 12.0 * (b["landings"] / max(1, b["count"]))
        )

        rows.append(
            {
                "sector": sector,
                "avg_1h": round(avg, 3),
                "count": b["count"],
                "breadth": int(round(breadth)),
                "vwap_breadth": int(round(vwap_breadth)),
                "departures": b["departures"],
                "landings": b["landings"],
                "actionable": b["actionable"],
                "enters": b["enters"],
                "score": int(round(score)),
            }
        )

    rows.sort(
        key=lambda r: (
            r["score"],
            r["actionable"],
            r["departures"],
            r["avg_1h"],
        ),
        reverse=True,
    )
    return rows


def build_market_state(
    pair_states: Iterable[Dict[str, Any]],
    market_regime: str = "WAITING",
) -> Dict[str, Any]:
    """
    Build a single market command state from the Radar's pair states.

    The function intentionally returns the original v2 keys plus additional
    diagnostics. Existing UI code can continue reading the old keys unchanged.
    """

    flights = list(pair_states or [])
    if not flights:
        return _empty_state()

    verified = [f for f in flights if f.get("vwap_dist") is not None]

    # Prefer technically verified rows when we have enough of them. If only one
    # or two rows are verified, use the full universe so the aggregate does not
    # swing violently on a tiny sample.
    min_verified = max(3, int(round(len(flights) * 0.25)))
    sample = verified if len(verified) >= min_verified else flights

    n = len(sample)

    buyer_points = 0.0
    total_points = 0.0

    positive_1h = 0
    negative_1h = 0
    actionable = 0
    structure_count = 0
    above_vwap = 0
    testing_vwap = 0
    momentum_count = 0
    compression_count = 0
    reload_count = 0
    enter_count = 0
    late_count = 0
    departure_count = 0

    moves: List[float] = []
    opp_vals: List[float] = []

    for f in sample:
        ch1 = _num(f.get("change_1h"))
        r1 = _num(f.get("rsi_1m"), 50.0)
        r5 = _num(f.get("rsi_5m"), 50.0)
        vwap = _text(f.get("vwap"))
        action = _text(f.get("action"))
        phase = _text(f.get("phase"))
        read = _text(f.get("read_state"))

        moves.append(ch1)

        # VWAP control: strongest single component.
        total_points += 2.0
        if vwap in BULLISH_VWAP_STATES:
            buyer_points += 2.0
            above_vwap += 1
        elif vwap in TESTING_VWAP_STATES:
            buyer_points += 1.0
            testing_vwap += 1

        # 1H direction.
        total_points += 1.0
        if ch1 > 0:
            buyer_points += 1.0
            positive_1h += 1
        elif ch1 < 0:
            negative_1h += 1

        # Momentum alignment.
        total_points += 2.0
        if r5 >= 55:
            buyer_points += 1.0
            momentum_count += 1
        if r1 >= 50:
            buyer_points += 1.0

        # Actionability.
        total_points += 1.0
        if action in ACTIONABLE_ACTIONS:
            buyer_points += 1.0
            actionable += 1

        if action == "ENTER":
            enter_count += 1

        # Opportunity is only meaningful on non-skipped names.
        if action not in SKIP_ACTIONS:
            remaining = f.get("remaining")
            if remaining is not None:
                opp_vals.append(_clamp(_num(remaining)))

        if read in STRUCTURE_READS:
            structure_count += 1
        if read in RELOAD_READS:
            reload_count += 1
        if read in COMPRESSION_READS:
            compression_count += 1

        if phase in LATE_PHASES:
            late_count += 1
        if phase in DEPARTURE_PHASES:
            departure_count += 1

    buyers = int(round(_clamp((buyer_points / total_points) * 100.0))) if total_points else 50
    sellers = 100 - buyers

    breadth = int(round(_pct(positive_1h, n)))
    bearish_breadth = int(round(_pct(negative_1h, n)))

    opportunity = int(round(sum(opp_vals) / len(opp_vals))) if opp_vals else 0
    opportunity = int(_clamp(opportunity))

    avg_1h = sum(moves) / n
    variance = sum((x - avg_1h) ** 2 for x in moves) / n
    spread = sqrt(variance)

    # Directional synchronization is more useful than "max(up, down)" alone.
    bullish_sync = int(round(_pct(positive_1h, n)))
    bearish_sync = int(round(_pct(negative_1h, n)))
    synchronization = max(bullish_sync, bearish_sync)

    vwap_breadth = _pct(above_vwap, n)
    momentum_breadth = _pct(momentum_count, n)
    structure_breadth = _pct(structure_count, n)
    compression_breadth = _pct(compression_count, n)
    late_pct = _pct(late_count, n)
    departure_pct = _pct(departure_count, n)
    enter_pct = _pct(enter_count, n)

    # Expansion pressure should represent *bullish stored/active energy*.
    # Bearish synchronization no longer accidentally boosts long expansion.
    expansion_pressure = int(
        round(
            _clamp(
                0.26 * vwap_breadth
                + 0.22 * momentum_breadth
                + 0.19 * structure_breadth
                + 0.15 * bullish_sync
                + 0.10 * max(compression_breadth, departure_pct)
                + 0.08 * enter_pct
                - 0.12 * late_pct
            )
        )
    )

    structure_pct = structure_count / n
    late_ratio = late_count / n

    health = int(
        round(
            _clamp(
                0.28 * buyers
                + 0.18 * breadth
                + 0.17 * opportunity
                + 0.13 * bullish_sync
                + 0.14 * expansion_pressure
                + 0.10 * vwap_breadth
                + 10.0 * structure_pct
                - 18.0 * late_ratio
            )
        )
    )

    # Momentum label.
    if avg_1h >= 0.75 and breadth >= 60:
        momentum = "Rising Fast"
    elif avg_1h > 0.15 and breadth >= 50:
        momentum = "Rising"
    elif avg_1h <= -0.75 and bearish_breadth >= 60:
        momentum = "Falling Fast"
    elif avg_1h < -0.15 and bearish_breadth >= 50:
        momentum = "Falling"
    elif abs(avg_1h) < 0.15 and spread < 0.45:
        momentum = "Quiet"
    else:
        momentum = "Mixed"

    # Market-quality descriptors.
    if health >= 75 and breadth >= 60 and late_pct < 25:
        visibility = "Excellent"
    elif health >= 55:
        visibility = "Good"
    elif health >= 40:
        visibility = "Fair"
    else:
        visibility = "Poor"

    if buyers >= 65 and bullish_sync >= 55:
        wind = "Tailwind"
    elif buyers <= 35 and bearish_sync >= 55:
        wind = "Headwind"
    else:
        wind = "Crosswind"

    turbulence = "High" if spread >= 2.0 else "Medium" if spread >= 0.9 else "Low"

    # Data confidence prevents the UI from sounding too certain on thin input.
    verified_ratio = int(round(_pct(len(verified), len(flights))))
    sample_confidence = int(
        round(
            _clamp(
                min(100.0, len(sample) * 8.0)
                * 0.55
                + verified_ratio * 0.45
            )
        )
    )
    signal_quality = (
        "HIGH"
        if sample_confidence >= 70 and health >= 60
        else "MEDIUM"
        if sample_confidence >= 45
        else "LOW"
    )

    sectors = _sector_summary(flights)
    leading_sector = sectors[0]["sector"] if sectors else "OTHER"

    regime = _text(market_regime)

    # Market mode classification.
    # Ordering matters: exhaustion and active expansion should beat reload.
    if (
        regime in DEFENSIVE_REGIMES
        or buyers < 35
        or (bearish_sync >= 65 and avg_1h < -0.25)
    ):
        market_mode = "EXHAUSTION"
    elif (
        enter_count >= 2
        and buyers >= 60
        and bullish_sync >= 55
        and expansion_pressure >= 58
        and late_pct < 40
    ):
        market_mode = "EXPANSION"
    elif (
        expansion_pressure >= 74
        and bullish_sync >= 62
        and compression_breadth >= 15
        and enter_count < 2
    ):
        market_mode = "SPRING_LOADED"
    elif (
        expansion_pressure >= 58
        and buyers >= 54
        and structure_breadth >= 30
    ):
        market_mode = "BUILDING_PRESSURE"
    elif reload_count >= 2 and buyers >= 48 and late_pct < 50:
        market_mode = "RELOAD"
    elif health < 35 or (opportunity < 25 and abs(avg_1h) < 0.20):
        market_mode = "DEAD_AIR"
    else:
        market_mode = "MIXED_AIRSPACE"

    # Bias is separate from mode: a market can be bullish but poor for entry.
    if buyers >= 60 and breadth >= 55:
        market_bias = "BULLISH"
    elif buyers <= 40 and bearish_breadth >= 55:
        market_bias = "BEARISH"
    else:
        market_bias = "NEUTRAL"

    # Recommended execution layer.
    if sample_confidence < 30:
        recommended = "Stand By"
        note = "Radar sample is too thin for a confident market-level read."
    elif market_mode == "EXHAUSTION":
        recommended = "Defensive"
        note = "Protect capital. Avoid forcing long momentum entries."
    elif late_pct >= 55 and opportunity < 50:
        recommended = "Wait for Reset"
        note = "Too much of the board is late. Skip chases and wait for fresh structure."
    elif market_mode == "EXPANSION":
        if opportunity >= 60:
            recommended = "Expansion"
            note = "Broad momentum is active. Execute only confirmed leaders with room remaining."
        else:
            recommended = "No Chase"
            note = "Expansion is active, but remaining opportunity is limited. Wait for a reset."
    elif market_mode == "SPRING_LOADED":
        recommended = "Prepare for Expansion"
        note = "Pressure is synchronized but not fully released. Watch the strongest sectors for confirmation."
    elif market_mode == "BUILDING_PRESSURE":
        recommended = "Selective"
        note = "Conditions are improving. Favor names with VWAP control, 5m momentum, and clean structure."
    elif market_mode == "RELOAD":
        recommended = "Sharpshooter Reloads"
        note = "Favor 1m reloads that rejoin stronger 5m structure. Do not chase extended names."
    elif market_mode == "DEAD_AIR":
        recommended = "Stand By"
        note = "There is not enough clean movement or opportunity to justify forcing trades."
    elif opportunity < 40:
        recommended = "Wait for Reset"
        note = "Control may exist, but clean entry opportunity is limited."
    elif regime in BULLISH_REGIMES and buyers >= 52:
        recommended = "Selective Continuation"
        note = "Higher-level conditions are constructive. Trade only the strongest confirmed departures."
    else:
        recommended = "Selective"
        note = "Mixed airspace. Trade only clear outliers with defined risk."

    return {
        # Existing v2 output keys
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

        # Added command/diagnostic fields
        "market_bias": market_bias,
        "signal_quality": signal_quality,
        "sample_confidence": sample_confidence,
        "verified_ratio": verified_ratio,
        "bullish_synchronization": bullish_sync,
        "bearish_synchronization": bearish_sync,
        "vwap_breadth": int(round(vwap_breadth)),
        "momentum_breadth": int(round(momentum_breadth)),
        "structure_breadth": int(round(structure_breadth)),
        "compression_breadth": int(round(compression_breadth)),
        "late_pct": int(round(late_pct)),
        "move_dispersion": round(spread, 3),
        "enter_pairs": enter_count,
        "reload_pairs": reload_count,
        "late_pairs": late_count,
    }


if __name__ == "__main__":
    demo = [
        {
            "pair": "SOL/USD",
            "vwap": "Holding",
            "vwap_dist": 0.2,
            "change_1h": 1.1,
            "rsi_1m": 57,
            "rsi_5m": 63,
            "action": "WAIT",
            "phase": "Takeoff",
            "read_state": "RELOAD WATCH",
            "remaining": 78,
            "sector": "L1",
        },
        {
            "pair": "FET/USD",
            "vwap": "Above",
            "vwap_dist": 0.5,
            "change_1h": 1.8,
            "rsi_1m": 54,
            "rsi_5m": 66,
            "action": "ENTER",
            "phase": "Takeoff",
            "read_state": "RELOAD READY",
            "remaining": 88,
            "sector": "AI",
        },
        {
            "pair": "AVAX/USD",
            "vwap": "Holding",
            "vwap_dist": 0.3,
            "change_1h": 0.9,
            "rsi_1m": 58,
            "rsi_5m": 61,
            "action": "ENTER",
            "phase": "Climbing",
            "read_state": "CONTINUATION WATCH",
            "remaining": 72,
            "sector": "L1",
        },
    ]

    from pprint import pprint

    pprint(build_market_state(demo, "PREBULL"))
