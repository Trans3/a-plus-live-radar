from __future__ import annotations

"""
A+ Radar - Pair Engine
======================

Phase 2 of the Radar architecture.

Purpose
-------
The Market Engine answers:
    "Should I be trading right now?"

The Pair Engine answers:
    "Which pairs deserve my attention?"

This engine does NOT make the final entry decision.
That belongs to Phase 3: Entry Engine.

Primary outputs
---------------
- Full ranked board
- Top 25
- Top 5
- Outliers
- Sector leaders
- Watchlist
- Explainable pair scores

Expected pair-state fields (all optional)
-----------------------------------------
pair
symbol
sector
change_1h
change_24h
volume_24h
volume_ratio
rsi_1m
rsi_5m
rsi_15m
macd_1m
macd_5m
macd_15m
vwap
vwap_dist
btc_alignment
pair_strength_vs_btc
trend_score
impulse_pct
pullback_pct
time_since_impulse
phase
action
remaining
read_state
"""

from collections import defaultdict
from math import log10
from statistics import mean, pstdev
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


def _pct(part: int, whole: int) -> float:
    return (part / whole * 100.0) if whole else 0.0


def _safe_log_volume(v: float) -> float:
    return log10(v) if v > 0 else 0.0


def _rank_percentile(value: float, values: List[float]) -> float:
    if not values:
        return 50.0

    below = sum(1 for x in values if x < value)
    equal = sum(1 for x in values if x == value)

    return _clamp(((below + (0.5 * equal)) / len(values)) * 100.0)


def _is_bullish_vwap(v: Any) -> bool:
    return _text(v) in {"ABOVE", "HOLDING", "RECLAIMED"}


def _is_testing_vwap(v: Any) -> bool:
    return _text(v) in {"TESTING", "RECLAIM", "NEAR"}


def _macd_positive(v: Any) -> bool:
    if isinstance(v, bool):
        return v

    if isinstance(v, (int, float)):
        return float(v) > 0

    return _text(v) in {
        "POSITIVE",
        "BULLISH",
        "UP",
        "RISING",
        "TURNING UP",
        "CROSS UP",
        "ABOVE",
        "GREEN",
        "TRUE",
    }


def _btc_alignment_score(v: Any) -> float:
    if isinstance(v, bool):
        return 100.0 if v else 20.0

    if isinstance(v, (int, float)):
        x = float(v)

        if -1 <= x <= 1:
            return _clamp((x + 1) * 50.0)

        return _clamp(x)

    t = _text(v)

    if t in {"STRONG", "ALIGNED", "BULLISH", "YES", "SUPPORTIVE"}:
        return 100.0

    if t in {"PARTIAL", "NEUTRAL", "MIXED"}:
        return 55.0

    if t in {"WEAK", "MISALIGNED", "BEARISH", "NO"}:
        return 15.0

    return 50.0


def _phase_score(v: Any) -> float:
    return {
        "TAXIING": 88,
        "TAKEOFF": 100,
        "CLIMBING": 92,
        "CRUISING": 70,
        "DESCENDING": 30,
        "LANDING": 12,
    }.get(_text(v), 55.0)


def _read_state_score(v: Any) -> float:
    return {
        "RELOAD READY": 100,
        "CONTINUATION WATCH": 92,
        "PRESSURE BUILDING": 88,
        "RELOAD WATCH": 82,
        "PREBUILD": 78,
        "BUILDING": 72,
        "EXTENDED": 25,
        "EXHAUSTED": 10,
    }.get(_text(v), 55.0)


def _remaining_score(v: Any) -> float:
    return _clamp(_num(v, 50.0))


def _pullback_quality(v: Any) -> float:
    """
    Rewards controlled pullbacks.

    The engine intentionally does not treat 'no pullback' as perfect.
    A clean reset is generally more useful for future entry quality.
    """
    x = abs(_num(v))

    if x <= 0.10:
        return 55.0
    if x <= 0.35:
        return 100.0
    if x <= 0.65:
        return 90.0
    if x <= 1.00:
        return 55.0
    if x <= 1.50:
        return 30.0

    return 10.0


def _impulse_quality(v: Any) -> float:
    x = _num(v)

    if x <= 0:
        return 20.0
    if x < 0.30:
        return 40.0
    if x < 0.60:
        return 68.0
    if x <= 1.60:
        return 100.0
    if x <= 2.50:
        return 72.0

    return 42.0


def _rsi_quality(r1: float, r5: float, r15: float) -> float:
    score = 0.0

    if 55 <= r1 <= 72:
        score += 34
    elif 50 <= r1 < 55 or 72 < r1 <= 78:
        score += 25
    elif r1 > 78:
        score += 10
    else:
        score += max(0.0, (r1 - 35) * 0.8)

    if 54.5 <= r5 <= 72:
        score += 38
    elif 50 <= r5 < 54.5 or 72 < r5 <= 78:
        score += 27
    elif r5 > 78:
        score += 12
    else:
        score += max(0.0, (r5 - 35) * 0.8)

    if r15 >= 52:
        score += 28
    elif r15 >= 48:
        score += 18
    else:
        score += 8

    return _clamp(score)


def _vwap_quality(vwap: Any, vwap_dist: Any) -> float:
    state = _text(vwap)
    dist = abs(_num(vwap_dist, 999.0))

    if _is_bullish_vwap(state):
        base = 90.0
    elif _is_testing_vwap(state):
        base = 65.0
    elif state in {"BELOW", "LOST", "REJECTED"}:
        base = 20.0
    else:
        base = 50.0

    # Strongest area = above VWAP without being overextended.
    if dist <= 0.15:
        dist_score = 80.0
    elif dist <= 0.60:
        dist_score = 100.0
    elif dist <= 1.00:
        dist_score = 78.0
    elif dist <= 1.50:
        dist_score = 48.0
    elif dist <= 2.50:
        dist_score = 25.0
    else:
        dist_score = 10.0

    return _clamp((base * 0.65) + (dist_score * 0.35))


def _trend_quality(v: Any) -> float:
    x = _num(v, 50.0)

    if 0 <= x <= 1:
        x *= 100.0

    return _clamp(x)


# ---------------------------------------------------------------------------
# Sector scoring
# ---------------------------------------------------------------------------

def _build_sector_map(
    pairs: List[Dict[str, Any]],
    market_state: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, float]]:

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for p in pairs:
        sector = _text(p.get("sector")) or "OTHER"
        grouped[sector].append(p)

    market_sector_scores = {}

    if market_state:
        for row in market_state.get("sector_flow", []) or []:
            sector = _text(row.get("sector"))

            if sector:
                market_sector_scores[sector] = _num(row.get("score"), 50.0)

    sector_map: Dict[str, Dict[str, float]] = {}

    for sector, rows in grouped.items():
        moves = [_num(x.get("change_1h")) for x in rows]

        positive = sum(1 for x in moves if x > 0)
        above_vwap = sum(
            1 for x in rows
            if _is_bullish_vwap(x.get("vwap"))
        )

        avg_move = mean(moves) if moves else 0.0

        move_component = _clamp(((avg_move + 1.0) / 3.0) * 100.0)

        internal_score = _clamp(
            (0.35 * _pct(positive, len(rows)))
            + (0.30 * _pct(above_vwap, len(rows)))
            + (0.20 * move_component)
            + 15.0
        )

        external_score = market_sector_scores.get(sector)

        if external_score is not None:
            combined = _clamp(
                (internal_score * 0.55)
                + (external_score * 0.45)
            )
        else:
            combined = internal_score

        sector_map[sector] = {
            "score": round(combined, 2),
            "avg_1h": round(avg_move, 4),
            "breadth": round(_pct(positive, len(rows)), 2),
            "count": float(len(rows)),
        }

    return sector_map


# ---------------------------------------------------------------------------
# Pair scoring
# ---------------------------------------------------------------------------

def _score_pair(
    pair: Dict[str, Any],
    universe: List[Dict[str, Any]],
    sector_map: Dict[str, Dict[str, float]],
    market_state: Optional[Dict[str, Any]],
) -> Dict[str, Any]:

    pair_name = str(
        pair.get("pair")
        or pair.get("symbol")
        or "UNKNOWN"
    )

    sector = _text(pair.get("sector")) or "OTHER"

    ch1 = _num(pair.get("change_1h"))
    ch24 = _num(pair.get("change_24h"))

    r1 = _num(pair.get("rsi_1m"), 50.0)
    r5 = _num(pair.get("rsi_5m"), 50.0)
    r15 = _num(pair.get("rsi_15m"), 50.0)

    volume_ratio = _num(pair.get("volume_ratio"), 1.0)
    volume_24h = _num(pair.get("volume_24h"))

    one_hour_moves = [_num(x.get("change_1h")) for x in universe]
    day_moves = [_num(x.get("change_24h")) for x in universe]
    volume_ratios = [_num(x.get("volume_ratio"), 1.0) for x in universe]
    volumes = [_safe_log_volume(_num(x.get("volume_24h"))) for x in universe]

    rs_1h = _rank_percentile(ch1, one_hour_moves)
    rs_24h = _rank_percentile(ch24, day_moves)

    pair_strength = pair.get("pair_strength_vs_btc")

    if pair_strength is None:
        relative_strength = (rs_1h * 0.70) + (rs_24h * 0.30)
    else:
        x = _num(pair_strength, 50.0)

        if -1 <= x <= 1:
            x = (x + 1) * 50.0

        relative_strength = _clamp(
            (x * 0.60)
            + (rs_1h * 0.40)
        )

    sector_strength = sector_map.get(
        sector,
        {"score": 50.0},
    )["score"]

    vwap_score = _vwap_quality(
        pair.get("vwap"),
        pair.get("vwap_dist"),
    )

    rsi_score = _rsi_quality(r1, r5, r15)

    macd_score = _clamp(
        (34 if _macd_positive(pair.get("macd_1m")) else 8)
        + (36 if _macd_positive(pair.get("macd_5m")) else 8)
        + (30 if _macd_positive(pair.get("macd_15m")) else 8)
    )

    volume_ratio_rank = _rank_percentile(
        volume_ratio,
        volume_ratios,
    )

    volume_size_rank = _rank_percentile(
        _safe_log_volume(volume_24h),
        volumes,
    )

    volume_score = _clamp(
        (0.70 * volume_ratio_rank)
        + (0.30 * volume_size_rank)
    )

    trend_score = _trend_quality(pair.get("trend_score"))
    btc_score = _btc_alignment_score(pair.get("btc_alignment"))

    impulse_score = _impulse_quality(pair.get("impulse_pct"))
    pullback_score = _pullback_quality(pair.get("pullback_pct"))

    phase_score = _phase_score(pair.get("phase"))
    read_score = _read_state_score(pair.get("read_state"))
    remaining_score = _remaining_score(pair.get("remaining"))

    structure_score = _clamp(
        (phase_score * 0.34)
        + (read_score * 0.32)
        + (impulse_score * 0.18)
        + (pullback_score * 0.16)
    )

    momentum_score = _clamp(
        (rsi_score * 0.42)
        + (macd_score * 0.33)
        + (trend_score * 0.25)
    )

    # -----------------------------------------------------------------------
    # Market context
    # -----------------------------------------------------------------------

    market_state = market_state or {}

    market_mode = _text(market_state.get("market_mode"))
    market_bias = _text(market_state.get("market_bias"))
    market_health = _num(market_state.get("market_health"), 50.0)
    leading_sector = _text(market_state.get("leading_sector"))

    context_score = 50.0

    if market_bias == "BULLISH":
        context_score += 12
    elif market_bias == "BEARISH":
        context_score -= 16

    if market_mode == "EXPANSION":
        context_score += 16
    elif market_mode in {"SPRING_LOADED", "BUILDING_PRESSURE"}:
        context_score += 10
    elif market_mode == "RELOAD":
        context_score += 6
    elif market_mode in {"EXHAUSTION", "DEAD_AIR"}:
        context_score -= 18

    if leading_sector and sector == leading_sector:
        context_score += 8

    context_score += (market_health - 50.0) * 0.18
    context_score = _clamp(context_score)

    # -----------------------------------------------------------------------
    # Composite score
    # -----------------------------------------------------------------------

    raw_score = (
        (0.18 * relative_strength)
        + (0.12 * sector_strength)
        + (0.13 * vwap_score)
        + (0.15 * momentum_score)
        + (0.10 * volume_score)
        + (0.11 * structure_score)
        + (0.07 * btc_score)
        + (0.07 * remaining_score)
        + (0.07 * context_score)
    )

    # -----------------------------------------------------------------------
    # Anti-chase penalties
    # -----------------------------------------------------------------------

    chase_penalty = 0.0

    phase = _text(pair.get("phase"))
    action = _text(pair.get("action"))
    vwap_dist = abs(_num(pair.get("vwap_dist")))

    if phase == "DESCENDING":
        chase_penalty += 10

    elif phase == "LANDING":
        chase_penalty += 20

    if vwap_dist > 1.50:
        chase_penalty += min(
            18.0,
            (vwap_dist - 1.50) * 7.0,
        )

    if r1 > 78:
        chase_penalty += 8

    if r5 > 78:
        chase_penalty += 6

    if remaining_score < 30:
        chase_penalty += 10

    if action in {"SKIP", "HOLD / SKIP", "CHASE"}:
        chase_penalty += 12

    if not _is_bullish_vwap(pair.get("vwap")) and r5 < 52:
        chase_penalty += 8

    score = _clamp(raw_score - chase_penalty)

    # -----------------------------------------------------------------------
    # Explainability
    # -----------------------------------------------------------------------

    reasons: List[str] = []
    risks: List[str] = []

    if relative_strength >= 75:
        reasons.append("Strong relative strength")

    if sector_strength >= 70:
        reasons.append("Strong sector")

    if vwap_score >= 78:
        reasons.append("Good VWAP control")

    if momentum_score >= 75:
        reasons.append("Momentum aligned")

    if volume_score >= 70:
        reasons.append("Volume confirmation")

    if structure_score >= 75:
        reasons.append("Clean structure")

    if btc_score >= 75:
        reasons.append("BTC aligned")

    if remaining_score >= 65:
        reasons.append("Room remaining")

    if leading_sector and sector == leading_sector:
        reasons.append("Leading sector")

    if chase_penalty >= 12:
        risks.append("Chase risk")

    if phase in {"DESCENDING", "LANDING"}:
        risks.append("Late phase")

    if vwap_dist > 1.50:
        risks.append("Extended from VWAP")

    if r1 > 78 or r5 > 78:
        risks.append("Overheated RSI")

    if remaining_score < 35:
        risks.append("Limited remaining move")

    if btc_score < 35:
        risks.append("BTC misalignment")

    if score >= 85:
        tier = "A+"
    elif score >= 75:
        tier = "A"
    elif score >= 65:
        tier = "B"
    elif score >= 55:
        tier = "C"
    else:
        tier = "D"

    if chase_penalty >= 20 or remaining_score < 20:
        disposition = "SKIP"
    elif score >= 80 and chase_penalty < 12:
        disposition = "PRIORITY"
    elif score >= 70:
        disposition = "WATCH"
    elif score >= 58:
        disposition = "SECONDARY"
    else:
        disposition = "LOW PRIORITY"

    return {
        "pair": pair_name,
        "sector": sector,

        "score": round(score, 2),
        "raw_score": round(raw_score, 2),

        "tier": tier,
        "disposition": disposition,

        "relative_strength": round(relative_strength, 2),
        "sector_strength": round(sector_strength, 2),
        "vwap_score": round(vwap_score, 2),
        "momentum_score": round(momentum_score, 2),
        "volume_score": round(volume_score, 2),
        "structure_score": round(structure_score, 2),
        "btc_alignment_score": round(btc_score, 2),
        "remaining_score": round(remaining_score, 2),
        "context_score": round(context_score, 2),

        "chase_penalty": round(chase_penalty, 2),

        "change_1h": round(ch1, 4),
        "change_24h": round(ch24, 4),

        "rsi_1m": round(r1, 2),
        "rsi_5m": round(r5, 2),
        "rsi_15m": round(r15, 2),

        "vwap": pair.get("vwap"),
        "vwap_dist": pair.get("vwap_dist"),

        "phase": pair.get("phase"),
        "read_state": pair.get("read_state"),
        "action": pair.get("action"),
        "remaining": pair.get("remaining"),

        "reasons": reasons[:5],
        "risks": risks[:4],
    }


# ---------------------------------------------------------------------------
# Outlier detection
# ---------------------------------------------------------------------------

def _detect_outliers(
    ranked: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:

    if not ranked:
        return []

    moves = [x["change_1h"] for x in ranked]
    scores = [x["score"] for x in ranked]

    move_mean = mean(moves)
    score_mean = mean(scores)

    move_sd = pstdev(moves) if len(moves) > 1 else 0.0
    score_sd = pstdev(scores) if len(scores) > 1 else 0.0

    outliers = []

    for row in ranked:
        move_z = (
            (row["change_1h"] - move_mean) / move_sd
            if move_sd > 0 else 0.0
        )

        score_z = (
            (row["score"] - score_mean) / score_sd
            if score_sd > 0 else 0.0
        )

        reasons = []

        if move_z >= 1.25:
            reasons.append("1H momentum outlier")

        if score_z >= 1.0:
            reasons.append("Composite quality outlier")

        if row["relative_strength"] >= 90:
            reasons.append("Top-decile relative strength")

        if row["volume_score"] >= 90:
            reasons.append("Top-decile volume")

        if (
            row["sector_strength"] >= 80
            and row["score"] >= 75
        ):
            reasons.append("Leading-sector strength")

        if reasons and row["chase_penalty"] < 18:
            outliers.append(
                {
                    "pair": row["pair"],
                    "sector": row["sector"],
                    "score": row["score"],
                    "tier": row["tier"],
                    "change_1h": row["change_1h"],
                    "reasons": reasons[:3],
                }
            )

    outliers.sort(
        key=lambda x: (
            x["score"],
            x["change_1h"],
        ),
        reverse=True,
    )

    return outliers


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_pair_rankings(
    pair_states: Iterable[Dict[str, Any]],
    market_state: Optional[Dict[str, Any]] = None,
    top_n: int = 25,
    premium_n: int = 5,
) -> Dict[str, Any]:
    """
    Build the Phase 2 Pair Engine output.

    Returns
    -------
    ranked_pairs
        Entire board, best pair first.

    top_25
        Main Radar leaderboard.

    top_5
        Premium / highest-priority board.

    outliers
        Pairs exhibiting unusual relative momentum or composite quality.

    sector_leaders
        Highest-ranked pair within each sector.

    watchlist
        Priority and watch-tier names worth handing to the Entry Engine.
    """

    pairs = list(pair_states or [])

    if not pairs:
        return {
            "ranked_pairs": [],
            "top_25": [],
            "top_5": [],
            "outliers": [],
            "sector_leaders": [],
            "watchlist": [],
            "summary": {
                "pairs_scanned": 0,
                "priority_pairs": 0,
                "a_plus_pairs": 0,
                "best_pair": None,
                "best_sector": None,
                "average_score": 0.0,
            },
        }

    sector_map = _build_sector_map(
        pairs,
        market_state,
    )

    scored = [
        _score_pair(
            pair,
            pairs,
            sector_map,
            market_state,
        )
        for pair in pairs
    ]

    scored.sort(
        key=lambda x: (
            x["score"],
            x["relative_strength"],
            x["structure_score"],
            x["volume_score"],
        ),
        reverse=True,
    )

    for rank, row in enumerate(scored, start=1):
        row["rank"] = rank

    top_25 = scored[:max(1, int(top_n))]
    top_5 = scored[:max(1, int(premium_n))]

    # -----------------------------------------------------------------------
    # Sector leaders
    # -----------------------------------------------------------------------

    best_by_sector: Dict[str, Dict[str, Any]] = {}

    for row in scored:
        sector = row["sector"]

        if sector not in best_by_sector:
            best_by_sector[sector] = row

    sector_leaders = [
        {
            "sector": sector,
            "pair": row["pair"],
            "rank": row["rank"],
            "score": row["score"],
            "tier": row["tier"],
            "disposition": row["disposition"],
        }
        for sector, row in best_by_sector.items()
    ]

    sector_leaders.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    # -----------------------------------------------------------------------
    # Outliers
    # -----------------------------------------------------------------------

    outliers = _detect_outliers(scored)

    # -----------------------------------------------------------------------
    # Entry-engine handoff watchlist
    # -----------------------------------------------------------------------

    watchlist = [
        row
        for row in scored
        if row["disposition"] in {"PRIORITY", "WATCH"}
        and row["chase_penalty"] < 20
    ]

    priority_pairs = sum(
        1 for x in scored
        if x["disposition"] == "PRIORITY"
    )

    a_plus_pairs = sum(
        1 for x in scored
        if x["tier"] == "A+"
    )

    best_pair = scored[0]["pair"] if scored else None
    best_sector = sector_leaders[0]["sector"] if sector_leaders else None

    avg_score = mean(
        x["score"] for x in scored
    ) if scored else 0.0

    return {
        "ranked_pairs": scored,
        "top_25": top_25,
        "top_5": top_5,
        "outliers": outliers,
        "sector_leaders": sector_leaders,
        "watchlist": watchlist,

        "summary": {
            "pairs_scanned": len(scored),
            "priority_pairs": priority_pairs,
            "a_plus_pairs": a_plus_pairs,
            "best_pair": best_pair,
            "best_sector": best_sector,
            "average_score": round(avg_score, 2),
        },
    }


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def rank_pairs(
    pair_states: Iterable[Dict[str, Any]],
    market_state: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Convenience function for older UI code that only wants the ranked list.
    """
    return build_pair_rankings(
        pair_states,
        market_state,
    )["ranked_pairs"]


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pprint import pprint

    demo_market = {
        "market_mode": "EXPANSION",
        "market_bias": "BULLISH",
        "market_health": 78,
        "leading_sector": "AI",
        "sector_flow": [
            {"sector": "AI", "score": 88},
            {"sector": "L1", "score": 74},
        ],
    }

    demo_pairs = [
        {
            "pair": "FET/USD",
            "sector": "AI",
            "change_1h": 2.1,
            "change_24h": 7.8,
            "volume_24h": 220_000_000,
            "volume_ratio": 2.2,
            "rsi_1m": 61,
            "rsi_5m": 66,
            "rsi_15m": 62,
            "macd_1m": "bullish",
            "macd_5m": "bullish",
            "macd_15m": "bullish",
            "vwap": "holding",
            "vwap_dist": 0.45,
            "btc_alignment": "aligned",
            "pair_strength_vs_btc": 88,
            "trend_score": 84,
            "impulse_pct": 0.9,
            "pullback_pct": 0.3,
            "phase": "takeoff",
            "read_state": "reload ready",
            "remaining": 82,
            "action": "WAIT",
        },
        {
            "pair": "SOL/USD",
            "sector": "L1",
            "change_1h": 1.1,
            "change_24h": 4.2,
            "volume_24h": 900_000_000,
            "volume_ratio": 1.4,
            "rsi_1m": 58,
            "rsi_5m": 61,
            "rsi_15m": 59,
            "macd_1m": "bullish",
            "macd_5m": "bullish",
            "macd_15m": "bullish",
            "vwap": "above",
            "vwap_dist": 0.35,
            "btc_alignment": "aligned",
            "pair_strength_vs_btc": 73,
            "trend_score": 76,
            "impulse_pct": 0.7,
            "pullback_pct": 0.4,
            "phase": "climbing",
            "read_state": "continuation watch",
            "remaining": 71,
            "action": "WAIT",
        },
        {
            "pair": "XYZ/USD",
            "sector": "OTHER",
            "change_1h": 4.8,
            "change_24h": 12.0,
            "volume_24h": 5_000_000,
            "volume_ratio": 3.0,
            "rsi_1m": 84,
            "rsi_5m": 80,
            "rsi_15m": 73,
            "macd_1m": "bullish",
            "macd_5m": "bullish",
            "macd_15m": "bullish",
            "vwap": "above",
            "vwap_dist": 2.8,
            "btc_alignment": "aligned",
            "trend_score": 95,
            "impulse_pct": 2.7,
            "pullback_pct": 0.05,
            "phase": "landing",
            "read_state": "extended",
            "remaining": 15,
            "action": "CHASE",
        },
    ]

    result = build_pair_rankings(
        demo_pairs,
        demo_market,
    )

    pprint(result["summary"])
    print()
    pprint(result["top_5"])
