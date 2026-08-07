from __future__ import annotations

"""
A+ Radar - Entry Engine
=======================

Phase 3 of the Radar architecture.

Purpose
-------
The Market Engine answers:
    "Should I be trading right now?"

The Pair Engine answers:
    "Which pairs deserve my attention?"

The Entry Engine answers:
    "Is this pair actually ready to enter right now?"

This module is intentionally strict.

Primary outputs
---------------
- ENTER
- WAIT
- SKIP
- CHASE
- confidence
- trigger score
- stop reference
- target reference
- risk/reward estimate
- expiration timer
- reason / blockers
- entry style:
    EXPANSION
    SHARPSHOOTER
    RELOAD
    CONTINUATION

Expected pair fields (all optional)
-----------------------------------
pair
price
high_1m
low_1m
atr_1m
atr_pct_1m
vwap
vwap_price
vwap_dist
rsi_1m
rsi_5m
rsi_15m
macd_1m
macd_5m
macd_15m
macd_hist_1m
macd_hist_1m_prev
macd_hist_15m
volume_ratio
impulse_pct
pullback_pct
time_since_impulse
phase
read_state
remaining
pair_score
score
tier
disposition
btc_alignment
trend_score
recent_high
recent_low
entry_price
support_price

Expected market-state fields
----------------------------
market_mode
recommended_mode
market_bias
market_health
expansion_pressure
buyer_pressure
late_pct
signal_quality
"""

from typing import Any, Dict, Iterable, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _num(v: Any, default: float = 0.0) -> float:
    try:
        return default if v is None else float(v)
    except (TypeError, ValueError):
        return default


def _text(v: Any) -> str:
    return str(v or "").strip().upper()


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _boolish(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return float(v) > 0
    return _text(v) in {
        "TRUE", "YES", "Y", "ON", "BULLISH", "POSITIVE",
        "UP", "RISING", "ALIGNED", "SUPPORTIVE", "GREEN"
    }


def _macd_positive(v: Any) -> bool:
    if isinstance(v, (int, float)):
        return float(v) >= 0
    return _text(v) in {
        "POSITIVE", "BULLISH", "UP", "RISING",
        "TURNING UP", "CROSS UP", "ABOVE", "GREEN", "TRUE"
    }


def _macd_turning_up(current: Any, previous: Any) -> bool:
    if isinstance(current, (int, float)) and isinstance(previous, (int, float)):
        return float(current) > float(previous)
    return _text(current) in {
        "TURNING UP", "RISING", "CROSS UP", "BULLISH", "POSITIVE"
    }


def _btc_aligned(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        x = float(v)
        if -1 <= x <= 1:
            return x >= 0
        return x >= 50
    return _text(v) in {
        "ALIGNED", "BULLISH", "STRONG", "YES", "SUPPORTIVE"
    }


def _is_above_vwap(v: Any) -> bool:
    return _text(v) in {"ABOVE", "HOLDING", "RECLAIMED"}


def _is_testing_vwap(v: Any) -> bool:
    return _text(v) in {"TESTING", "RECLAIM", "NEAR"}


def _phase(v: Any) -> str:
    return _text(v)


def _read(v: Any) -> str:
    return _text(v)


def _pair_score(pair: Dict[str, Any]) -> float:
    for key in ("pair_score", "score"):
        if pair.get(key) is not None:
            return _clamp(_num(pair.get(key), 50.0))
    return 50.0


# ---------------------------------------------------------------------------
# Entry-style selection
# ---------------------------------------------------------------------------

def _select_entry_style(
    pair: Dict[str, Any],
    market_state: Dict[str, Any],
) -> str:
    mode = _text(market_state.get("market_mode"))
    recommended = _text(market_state.get("recommended_mode"))
    read_state = _read(pair.get("read_state"))
    phase = _phase(pair.get("phase"))

    if mode == "EXPANSION" or recommended == "EXPANSION":
        return "EXPANSION"

    if read_state in {"RELOAD READY", "RELOAD WATCH"}:
        return "RELOAD"

    if mode in {"RELOAD", "MIXED_AIRSPACE", "BUILDING_PRESSURE"}:
        return "SHARPSHOOTER"

    if phase in {"TAKEOFF", "CLIMBING"}:
        return "CONTINUATION"

    return "SHARPSHOOTER"


# ---------------------------------------------------------------------------
# Trigger components
# ---------------------------------------------------------------------------

def _vwap_component(pair: Dict[str, Any]) -> Dict[str, Any]:
    state = _text(pair.get("vwap"))
    dist = abs(_num(pair.get("vwap_dist"), 999.0))

    passed = False
    score = 0.0
    note = ""

    if _is_above_vwap(state):
        passed = True

        if dist <= 0.60:
            score = 100
            note = "Above VWAP with controlled distance"
        elif dist <= 1.00:
            score = 80
            note = "Above VWAP"
        elif dist <= 1.50:
            score = 55
            note = "Above VWAP but getting extended"
        else:
            score = 25
            note = "Too extended from VWAP"

    elif _is_testing_vwap(state):
        score = 55
        note = "VWAP reclaim/test in progress"

    elif state in {"BELOW", "LOST", "REJECTED"}:
        score = 5
        note = "VWAP control lost"

    else:
        score = 40
        note = "VWAP state unclear"

    return {
        "passed": passed,
        "score": score,
        "note": note,
    }


def _momentum_component(pair: Dict[str, Any]) -> Dict[str, Any]:
    r1 = _num(pair.get("rsi_1m"), 50.0)
    r5 = _num(pair.get("rsi_5m"), 50.0)

    m1 = _macd_positive(pair.get("macd_1m"))
    m5 = _macd_positive(pair.get("macd_5m"))
    m15 = _macd_positive(pair.get("macd_15m"))

    hist_now = pair.get("macd_hist_1m")
    hist_prev = pair.get("macd_hist_1m_prev")
    turn = _macd_turning_up(hist_now, hist_prev)

    score = 0.0

    # Radar historical thresholds:
    # RSI 1m >=55
    # RSI 5m >=54.5
    if r1 >= 55:
        score += 25
    elif r1 >= 52:
        score += 15

    if r5 >= 54.5:
        score += 30
    elif r5 >= 52:
        score += 18

    if m1:
        score += 15

    if m5:
        score += 15

    if m15:
        score += 8

    if turn:
        score += 7

    overheated = r1 > 80 or r5 > 78

    passed = (
        r1 >= 55
        and r5 >= 54.5
        and m1
        and m5
        and not overheated
    )

    return {
        "passed": passed,
        "score": _clamp(score),
        "rsi_1m": r1,
        "rsi_5m": r5,
        "macd_turn_up": turn,
        "overheated": overheated,
    }


def _structure_component(pair: Dict[str, Any]) -> Dict[str, Any]:
    impulse = _num(pair.get("impulse_pct"))
    pullback = abs(_num(pair.get("pullback_pct")))
    phase = _phase(pair.get("phase"))
    read_state = _read(pair.get("read_state"))

    score = 0.0

    # Existing Radar logic:
    # impulse >= 0.6%
    # pullback <= 0.65
    if impulse >= 0.60:
        score += 35
    elif impulse >= 0.40:
        score += 22

    if 0.10 <= pullback <= 0.65:
        score += 30
    elif pullback < 0.10:
        score += 16
    elif pullback <= 1.0:
        score += 12

    if phase == "TAKEOFF":
        score += 20
    elif phase == "CLIMBING":
        score += 16
    elif phase == "TAXIING":
        score += 12
    elif phase in {"DESCENDING", "LANDING"}:
        score -= 20

    if read_state == "RELOAD READY":
        score += 15
    elif read_state in {
        "CONTINUATION WATCH",
        "PRESSURE BUILDING",
        "RELOAD WATCH",
    }:
        score += 10

    passed = (
        impulse >= 0.60
        and pullback <= 0.65
        and phase not in {"DESCENDING", "LANDING"}
    )

    return {
        "passed": passed,
        "score": _clamp(score),
        "impulse_pct": impulse,
        "pullback_pct": pullback,
        "phase": phase,
        "read_state": read_state,
    }


def _timing_component(pair: Dict[str, Any]) -> Dict[str, Any]:
    t = _num(pair.get("time_since_impulse"), -1)

    # Units are assumed to be minutes if this field is supplied.
    # Missing timing data is treated as neutral, not as a failure.
    if t < 0:
        return {
            "passed": True,
            "score": 60,
            "time_since_impulse": None,
            "note": "Timing data unavailable",
        }

    if t <= 2:
        return {
            "passed": True,
            "score": 82,
            "time_since_impulse": t,
            "note": "Fresh impulse",
        }

    if t <= 8:
        return {
            "passed": True,
            "score": 100,
            "time_since_impulse": t,
            "note": "Prime timing window",
        }

    if t <= 15:
        return {
            "passed": True,
            "score": 72,
            "time_since_impulse": t,
            "note": "Still actionable",
        }

    if t <= 30:
        return {
            "passed": False,
            "score": 38,
            "time_since_impulse": t,
            "note": "Impulse aging",
        }

    return {
        "passed": False,
        "score": 12,
        "time_since_impulse": t,
        "note": "Impulse stale",
    }


def _remaining_component(pair: Dict[str, Any]) -> Dict[str, Any]:
    remaining = _clamp(_num(pair.get("remaining"), 50.0))

    if remaining >= 70:
        score = 100
    elif remaining >= 55:
        score = 82
    elif remaining >= 40:
        score = 62
    elif remaining >= 25:
        score = 38
    else:
        score = 12

    return {
        "passed": remaining >= 35,
        "score": score,
        "remaining": remaining,
    }


# ---------------------------------------------------------------------------
# Stop / target / RR
# ---------------------------------------------------------------------------

def _calculate_trade_levels(pair: Dict[str, Any]) -> Dict[str, Any]:
    price = _num(
        pair.get("price"),
        _num(pair.get("entry_price"), 0.0),
    )

    if price <= 0:
        return {
            "entry": None,
            "stop": None,
            "target_1": None,
            "target_2": None,
            "risk_pct": None,
            "rr_1": None,
            "rr_2": None,
            "rr_pass": False,
        }

    atr = abs(_num(pair.get("atr_1m")))
    support = _num(pair.get("support_price"))
    recent_low = _num(pair.get("recent_low"))
    vwap_price = _num(pair.get("vwap_price"))

    candidates = []

    # Structural stop candidates below price.
    for value in (support, recent_low, vwap_price):
        if 0 < value < price:
            candidates.append(value)

    if atr > 0:
        candidates.append(price - (atr * 1.25))

    # Fallback: 0.8% risk.
    if not candidates:
        stop = price * 0.992
    else:
        # Use closest sensible structure under price.
        stop = max(candidates)

    if stop >= price:
        stop = price * 0.992

    risk = price - stop
    risk_pct = (risk / price) * 100 if price else 0.0

    recent_high = _num(pair.get("recent_high"))

    # Target 1 = either structural high if meaningful, or 1.5R.
    rr15_target = price + (risk * 1.5)

    if recent_high > price:
        target_1 = max(recent_high, rr15_target)
    else:
        target_1 = rr15_target

    target_2 = price + (risk * 2.5)

    rr1 = (
        (target_1 - price) / risk
        if risk > 0 else 0.0
    )

    rr2 = (
        (target_2 - price) / risk
        if risk > 0 else 0.0
    )

    rr_pass = (
        risk_pct <= 1.5
        and rr1 >= 1.5
    )

    return {
        "entry": round(price, 8),
        "stop": round(stop, 8),
        "target_1": round(target_1, 8),
        "target_2": round(target_2, 8),
        "risk_pct": round(risk_pct, 3),
        "rr_1": round(rr1, 2),
        "rr_2": round(rr2, 2),
        "rr_pass": rr_pass,
    }


# ---------------------------------------------------------------------------
# Expiration
# ---------------------------------------------------------------------------

def _expiration_minutes(
    style: str,
    phase: str,
    score: float,
) -> int:
    if style == "EXPANSION":
        base = 4
    elif style == "SHARPSHOOTER":
        base = 6
    elif style == "RELOAD":
        base = 8
    else:
        base = 7

    if phase == "TAKEOFF":
        base -= 1
    elif phase == "CLIMBING":
        base += 1

    if score >= 90:
        base += 1

    return max(2, min(12, base))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def evaluate_entry(
    pair: Dict[str, Any],
    market_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluate one ranked pair and return the current entry decision.
    """

    market_state = market_state or {}

    name = str(
        pair.get("pair")
        or pair.get("symbol")
        or "UNKNOWN"
    )

    pair_score = _pair_score(pair)

    market_mode = _text(market_state.get("market_mode"))
    recommended_mode = _text(market_state.get("recommended_mode"))
    market_bias = _text(market_state.get("market_bias"))
    market_health = _num(market_state.get("market_health"), 50.0)
    late_pct = _num(market_state.get("late_pct"), 0.0)

    style = _select_entry_style(
        pair,
        market_state,
    )

    vwap = _vwap_component(pair)
    momentum = _momentum_component(pair)
    structure = _structure_component(pair)
    timing = _timing_component(pair)
    remaining = _remaining_component(pair)
    levels = _calculate_trade_levels(pair)

    btc_ok = _btc_aligned(pair.get("btc_alignment"))

    # -----------------------------------------------------------------------
    # Trigger score
    # -----------------------------------------------------------------------

    trigger_score = _clamp(
        (0.22 * vwap["score"])
        + (0.25 * momentum["score"])
        + (0.22 * structure["score"])
        + (0.10 * timing["score"])
        + (0.09 * remaining["score"])
        + (0.12 * pair_score)
    )

    # Market context modifies confidence, not raw technical trigger.
    context_modifier = 0.0

    if market_bias == "BULLISH":
        context_modifier += 5

    elif market_bias == "BEARISH":
        context_modifier -= 12

    if market_mode == "EXPANSION":
        context_modifier += 6

    elif market_mode in {"SPRING_LOADED", "BUILDING_PRESSURE"}:
        context_modifier += 3

    elif market_mode in {"EXHAUSTION", "DEAD_AIR"}:
        context_modifier -= 15

    if market_health >= 70:
        context_modifier += 4

    elif market_health < 40:
        context_modifier -= 7

    if late_pct >= 50:
        context_modifier -= 8

    if btc_ok:
        context_modifier += 3
    else:
        context_modifier -= 7

    confidence = _clamp(
        trigger_score + context_modifier
    )

    # -----------------------------------------------------------------------
    # Hard blockers
    # -----------------------------------------------------------------------

    blockers: List[str] = []
    warnings: List[str] = []
    positives: List[str] = []

    phase = _phase(pair.get("phase"))
    vwap_dist = abs(_num(pair.get("vwap_dist")))
    r1 = momentum["rsi_1m"]
    r5 = momentum["rsi_5m"]

    if market_mode == "EXHAUSTION":
        blockers.append("Market is in exhaustion")

    if market_bias == "BEARISH" and style != "SHARPSHOOTER":
        blockers.append("Market bias is bearish")

    if not vwap["passed"]:
        blockers.append("VWAP confirmation missing")

    if not momentum["passed"]:
        blockers.append("Momentum trigger incomplete")

    if not structure["passed"]:
        blockers.append("Structure is not entry-ready")

    if not timing["passed"]:
        blockers.append("Impulse timing is stale")

    if not remaining["passed"]:
        blockers.append("Not enough move remaining")

    if phase in {"DESCENDING", "LANDING"}:
        blockers.append("Pair is in a late phase")

    if vwap_dist > 1.75:
        blockers.append("Price is too extended from VWAP")

    if r1 > 82 or r5 > 80:
        blockers.append("Momentum is overheated")

    if levels["entry"] is not None and not levels["rr_pass"]:
        warnings.append("Risk/reward below preferred threshold")

    if not btc_ok:
        warnings.append("BTC alignment weak")

    if pair_score < 60:
        warnings.append("Pair Engine score is weak")

    # -----------------------------------------------------------------------
    # Positive explanations
    # -----------------------------------------------------------------------

    if vwap["passed"]:
        positives.append("VWAP confirmed")

    if momentum["passed"]:
        positives.append("1m/5m momentum aligned")

    if momentum["macd_turn_up"]:
        positives.append("1m MACD turning up")

    if structure["passed"]:
        positives.append("Impulse/pullback structure valid")

    if timing["score"] >= 80:
        positives.append("Timing window is fresh")

    if remaining["remaining"] >= 60:
        positives.append("Good remaining opportunity")

    if btc_ok:
        positives.append("BTC aligned")

    if pair_score >= 75:
        positives.append("High Pair Engine rank")

    # -----------------------------------------------------------------------
    # Decision
    # -----------------------------------------------------------------------

    hard_chase = (
        phase in {"DESCENDING", "LANDING"}
        or vwap_dist > 2.0
        or r1 > 82
        or remaining["remaining"] < 20
    )

    all_core = (
        vwap["passed"]
        and momentum["passed"]
        and structure["passed"]
        and timing["passed"]
        and remaining["passed"]
    )

    # Strict execution thresholds by style.
    if style == "EXPANSION":
        min_conf = 76
    elif style == "RELOAD":
        min_conf = 78
    elif style == "SHARPSHOOTER":
        min_conf = 82
    else:
        min_conf = 79

    if hard_chase:
        decision = "CHASE"

    elif (
        all_core
        and confidence >= min_conf
        and not blockers
        and pair_score >= 65
    ):
        decision = "ENTER"

    elif (
        confidence >= 55
        and not hard_chase
        and phase not in {"DESCENDING", "LANDING"}
    ):
        decision = "WAIT"

    else:
        decision = "SKIP"

    # If RR data is available and clearly bad, downgrade ENTER to WAIT.
    if (
        decision == "ENTER"
        and levels["entry"] is not None
        and not levels["rr_pass"]
    ):
        decision = "WAIT"
        blockers.append("Entry valid technically, but RR is not good enough")

    # Explicitly respect market-engine no-chase / stand-by instructions.
    if recommended_mode in {"NO CHASE", "STAND BY", "DEFENSIVE"}:
        if decision == "ENTER":
            decision = "WAIT"
            blockers.append(
                f"Market Engine recommends {recommended_mode.title()}"
            )

    expiry = (
        _expiration_minutes(
            style,
            phase,
            confidence,
        )
        if decision in {"ENTER", "WAIT"}
        else 0
    )

    return {
        "pair": name,

        "decision": decision,
        "entry_style": style,

        "confidence": round(confidence, 2),
        "trigger_score": round(trigger_score, 2),
        "minimum_confidence": min_conf,

        "pair_score": round(pair_score, 2),

        "expiration_minutes": expiry,

        "entry": levels["entry"],
        "stop": levels["stop"],
        "target_1": levels["target_1"],
        "target_2": levels["target_2"],
        "risk_pct": levels["risk_pct"],
        "rr_1": levels["rr_1"],
        "rr_2": levels["rr_2"],

        "market_mode": market_mode or "UNKNOWN",
        "market_bias": market_bias or "UNKNOWN",

        "checks": {
            "vwap": vwap,
            "momentum": momentum,
            "structure": structure,
            "timing": timing,
            "remaining": remaining,
            "btc_aligned": btc_ok,
        },

        "positives": positives[:6],
        "blockers": blockers[:6],
        "warnings": warnings[:4],
    }


def evaluate_entries(
    pairs: Iterable[Dict[str, Any]],
    market_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Evaluate a ranked Pair Engine board.

    Intended input:
        pair_engine["watchlist"]
        or
        pair_engine["top_5"]

    Returns:
        entries
        waiting
        skips
        chases
        evaluated
    """

    rows = [
        evaluate_entry(pair, market_state)
        for pair in list(pairs or [])
    ]

    # Best entry opportunity first.
    rows.sort(
        key=lambda x: (
            x["decision"] == "ENTER",
            x["confidence"],
            x["pair_score"],
        ),
        reverse=True,
    )

    entries = [
        x for x in rows
        if x["decision"] == "ENTER"
    ]

    waiting = [
        x for x in rows
        if x["decision"] == "WAIT"
    ]

    skips = [
        x for x in rows
        if x["decision"] == "SKIP"
    ]

    chases = [
        x for x in rows
        if x["decision"] == "CHASE"
    ]

    return {
        "entries": entries,
        "waiting": waiting,
        "skips": skips,
        "chases": chases,
        "evaluated": rows,

        "summary": {
            "evaluated_pairs": len(rows),
            "enter_count": len(entries),
            "wait_count": len(waiting),
            "skip_count": len(skips),
            "chase_count": len(chases),
            "best_entry": entries[0]["pair"] if entries else None,
            "best_confidence": (
                entries[0]["confidence"]
                if entries else None
            ),
        },
    }


# ---------------------------------------------------------------------------
# Convenience API
# ---------------------------------------------------------------------------

def get_entries(
    pairs: Iterable[Dict[str, Any]],
    market_state: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Return only currently valid ENTER signals.
    """
    return evaluate_entries(
        pairs,
        market_state,
    )["entries"]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pprint import pprint

    market = {
        "market_mode": "EXPANSION",
        "recommended_mode": "Expansion",
        "market_bias": "BULLISH",
        "market_health": 82,
        "late_pct": 12,
    }

    candidate = {
        "pair": "FET/USD",
        "price": 1.2500,

        "score": 88.9,

        "vwap": "holding",
        "vwap_price": 1.2440,
        "vwap_dist": 0.48,

        "rsi_1m": 61,
        "rsi_5m": 64,
        "rsi_15m": 59,

        "macd_1m": "bullish",
        "macd_5m": "bullish",
        "macd_15m": "bullish",

        "macd_hist_1m": 0.004,
        "macd_hist_1m_prev": 0.002,

        "impulse_pct": 0.86,
        "pullback_pct": 0.34,
        "time_since_impulse": 5,

        "phase": "takeoff",
        "read_state": "reload ready",
        "remaining": 78,

        "btc_alignment": "aligned",

        "atr_1m": 0.006,
        "recent_low": 1.2420,
        "recent_high": 1.2750,
    }

    pprint(
        evaluate_entry(
            candidate,
            market,
        )
    )
