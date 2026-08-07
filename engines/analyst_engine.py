from __future__ import annotations

"""
A+ Radar - Analyst Engine
=========================

Phase 5 of the Radar architecture.

Purpose
-------
Market Engine:
    "Should I be trading?"

Pair Engine:
    "Which pairs deserve attention?"

Entry Engine:
    "Is this pair ready right now?"

Replay Engine:
    "What happened afterward?"

Analyst Engine:
    "Explain the decision in plain English."

This engine is deterministic and rule-based.
It does not require an LLM.

Primary outputs
---------------
- headline
- verdict
- why_ranked
- why_not
- strongest_edge
- biggest_risk
- market_context
- what_changes_next
- analyst_summary
- confidence_label
- setup_grade

The goal is to make Radar explain itself without inventing information.
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
    return str(v or "").strip()


def _upper(v: Any) -> str:
    return _text(v).upper()


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def _fmt_pct(v: Any, digits: int = 1) -> str:
    x = _num(v)
    return f"{x:.{digits}f}%"


def _fmt_num(v: Any, digits: int = 1) -> str:
    x = _num(v)
    return f"{x:.{digits}f}"


def _confidence_label(v: float) -> str:
    if v >= 90:
        return "VERY HIGH"
    if v >= 80:
        return "HIGH"
    if v >= 70:
        return "GOOD"
    if v >= 60:
        return "MODERATE"
    return "LOW"


def _setup_grade(score: float, decision: str) -> str:
    if decision == "CHASE":
        return "F"
    if score >= 90:
        return "A+"
    if score >= 82:
        return "A"
    if score >= 74:
        return "B+"
    if score >= 66:
        return "B"
    if score >= 58:
        return "C"
    return "D"


def _sentence_join(items: Iterable[str]) -> str:
    vals = [x.strip().rstrip(".") for x in items if x and x.strip()]
    if not vals:
        return ""
    if len(vals) == 1:
        return vals[0] + "."
    if len(vals) == 2:
        return vals[0] + " and " + vals[1] + "."
    return ", ".join(vals[:-1]) + ", and " + vals[-1] + "."


# ---------------------------------------------------------------------------
# Context explanations
# ---------------------------------------------------------------------------

def _market_context(market: Dict[str, Any]) -> List[str]:
    out: List[str] = []

    mode = _upper(market.get("market_mode"))
    bias = _upper(market.get("market_bias"))
    health = _num(market.get("market_health"), 50)
    buyers = _num(market.get("buyer_pressure"), 50)
    breadth = _num(market.get("breadth"), 50)
    expansion = _num(market.get("expansion_pressure"), 0)
    leading_sector = _text(market.get("leading_sector"))

    if mode:
        out.append(f"Market mode is {mode.replace('_', ' ').title()}")

    if bias == "BULLISH":
        out.append("market bias is bullish")
    elif bias == "BEARISH":
        out.append("market bias is bearish")
    elif bias:
        out.append("market bias is neutral")

    if health >= 75:
        out.append(f"market health is strong at {health:.0f}")
    elif health >= 55:
        out.append(f"market health is constructive at {health:.0f}")
    elif health < 40:
        out.append(f"market health is weak at {health:.0f}")

    if buyers >= 65:
        out.append(f"buyers control about {buyers:.0f}% of the board")

    if breadth >= 65:
        out.append(f"breadth is broad at {breadth:.0f}%")
    elif breadth < 40:
        out.append(f"breadth is narrow at {breadth:.0f}%")

    if expansion >= 70:
        out.append(f"expansion pressure is elevated at {expansion:.0f}")

    if leading_sector:
        out.append(f"{leading_sector} is the leading sector")

    return out[:5]


def _pair_edges(pair: Dict[str, Any]) -> List[str]:
    edges: List[str] = []

    score = _num(pair.get("score"))
    rank = pair.get("rank")
    rs = _num(pair.get("relative_strength"))
    sector = _num(pair.get("sector_strength"))
    vwap = _num(pair.get("vwap_score"))
    momentum = _num(pair.get("momentum_score"))
    volume = _num(pair.get("volume_score"))
    structure = _num(pair.get("structure_score"))
    btc = _num(pair.get("btc_alignment_score"))
    remaining = _num(pair.get("remaining_score"))
    penalty = _num(pair.get("chase_penalty"))

    if rank is not None and int(rank) <= 5:
        edges.append(f"ranked #{int(rank)} on the board")

    if score >= 85:
        edges.append(f"composite pair score is elite at {score:.1f}")
    elif score >= 75:
        edges.append(f"pair score is strong at {score:.1f}")

    if rs >= 80:
        edges.append(f"relative strength is excellent at {rs:.0f}")
    elif rs >= 70:
        edges.append(f"relative strength is strong at {rs:.0f}")

    if sector >= 75:
        edges.append(f"sector strength is strong at {sector:.0f}")

    if vwap >= 80:
        edges.append("VWAP structure is clean")

    if momentum >= 80:
        edges.append("momentum is well aligned")
    elif momentum >= 70:
        edges.append("momentum is constructive")

    if volume >= 80:
        edges.append("volume is confirming the move")

    if structure >= 80:
        edges.append("price structure is clean")

    if btc >= 75:
        edges.append("BTC alignment is supportive")

    if remaining >= 70:
        edges.append("there is meaningful room left in the move")

    if penalty == 0:
        edges.append("no meaningful chase penalty is present")

    return edges[:7]


def _pair_risks(pair: Dict[str, Any]) -> List[str]:
    risks: List[str] = []

    penalty = _num(pair.get("chase_penalty"))
    remaining = _num(pair.get("remaining_score"), 50)
    vwap_dist = abs(_num(pair.get("vwap_dist")))
    r1 = _num(pair.get("rsi_1m"), 50)
    r5 = _num(pair.get("rsi_5m"), 50)
    phase = _upper(pair.get("phase"))
    btc = _num(pair.get("btc_alignment_score"), 50)
    structure = _num(pair.get("structure_score"), 50)

    existing = pair.get("risks") or []
    risks.extend(str(x) for x in existing if x)

    if penalty >= 20 and "Chase risk" not in risks:
        risks.append("high chase penalty")

    if remaining < 30:
        risks.append("limited remaining opportunity")

    if vwap_dist > 1.5:
        risks.append("price is extended from VWAP")

    if r1 > 78 or r5 > 78:
        risks.append("RSI is overheated")

    if phase in {"DESCENDING", "LANDING"}:
        risks.append("the move is already late")

    if btc < 35:
        risks.append("BTC alignment is weak")

    if structure < 50:
        risks.append("structure quality is weak")

    # Deduplicate while preserving order.
    seen = set()
    clean = []
    for x in risks:
        key = x.lower()
        if key not in seen:
            seen.add(key)
            clean.append(x)

    return clean[:6]


def _entry_edges(entry: Dict[str, Any]) -> List[str]:
    out: List[str] = []

    checks = entry.get("checks") or {}
    confidence = _num(entry.get("confidence"))
    rr1 = entry.get("rr_1")
    style = _text(entry.get("entry_style"))

    if confidence >= 85:
        out.append(f"entry confidence is high at {confidence:.0f}")

    if style:
        out.append(f"setup fits the {style.title()} playbook")

    if checks.get("vwap", {}).get("passed"):
        out.append("VWAP confirmation passed")

    if checks.get("momentum", {}).get("passed"):
        out.append("1m and 5m momentum checks passed")

    if checks.get("structure", {}).get("passed"):
        out.append("impulse and pullback structure passed")

    if checks.get("timing", {}).get("passed"):
        out.append("timing is still actionable")

    if checks.get("remaining", {}).get("passed"):
        out.append("remaining-move check passed")

    if checks.get("btc_aligned"):
        out.append("BTC is aligned")

    if rr1 is not None and _num(rr1) >= 2:
        out.append(f"estimated reward/risk is {_num(rr1):.2f}R")

    return out[:6]


def _entry_blockers(entry: Dict[str, Any]) -> List[str]:
    blockers = list(entry.get("blockers") or [])
    warnings = list(entry.get("warnings") or [])

    combined = [str(x) for x in blockers + warnings if x]

    seen = set()
    clean: List[str] = []

    for x in combined:
        key = x.lower()

        if key not in seen:
            seen.add(key)
            clean.append(x)

    return clean[:6]


# ---------------------------------------------------------------------------
# What must change?
# ---------------------------------------------------------------------------

def _next_changes(
    pair: Dict[str, Any],
    entry: Dict[str, Any],
    market: Dict[str, Any],
) -> List[str]:
    decision = _upper(entry.get("decision"))
    changes: List[str] = []

    checks = entry.get("checks") or {}

    if decision == "ENTER":
        changes.append("Nothing major needs to improve; execution and risk control matter now")
        changes.append("Invalidate the setup if the defined stop or VWAP structure fails")
        return changes

    vwap_check = checks.get("vwap") or {}
    momentum = checks.get("momentum") or {}
    structure = checks.get("structure") or {}
    timing = checks.get("timing") or {}
    remaining = checks.get("remaining") or {}

    if not vwap_check.get("passed", False):
        changes.append("Price needs to reclaim and hold VWAP")

    if not momentum.get("passed", False):
        r1 = _num(momentum.get("rsi_1m"), 50)
        r5 = _num(momentum.get("rsi_5m"), 50)

        if r1 < 55:
            changes.append("1m RSI needs to push above 55")

        if r5 < 54.5:
            changes.append("5m RSI needs to hold above roughly 54.5")

        changes.append("1m/5m MACD alignment needs to improve")

    if not structure.get("passed", False):
        impulse = _num(structure.get("impulse_pct"))
        pullback = abs(_num(structure.get("pullback_pct")))

        if impulse < 0.6:
            changes.append("A stronger impulse of roughly 0.6% or more is needed")

        if pullback > 0.65:
            changes.append("The pullback needs to tighten below roughly 0.65%")

    if not timing.get("passed", True):
        changes.append("Wait for a fresh impulse instead of using the stale move")

    if not remaining.get("passed", True):
        changes.append("Wait for the board to reset and create more remaining opportunity")

    if _upper(market.get("market_mode")) in {"EXHAUSTION", "DEAD_AIR"}:
        changes.append("Market conditions need to improve before taking the setup seriously")

    if _num(pair.get("chase_penalty")) >= 20:
        changes.append("Price needs a reset before the chase penalty clears")

    # Deduplicate.
    seen = set()
    clean = []

    for x in changes:
        key = x.lower()
        if key not in seen:
            seen.add(key)
            clean.append(x)

    return clean[:6]


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def _headline(
    pair_name: str,
    decision: str,
    grade: str,
    confidence: float,
) -> str:
    if decision == "ENTER":
        return f"{pair_name}: {grade} setup — entry conditions are confirmed"

    if decision == "WAIT":
        return f"{pair_name}: promising setup, but confirmation is incomplete"

    if decision == "CHASE":
        return f"{pair_name}: move is too late to justify chasing"

    return f"{pair_name}: setup does not currently justify an entry"


def _verdict(decision: str, pair_score: float, confidence: float) -> str:
    if decision == "ENTER":
        if confidence >= 90 and pair_score >= 80:
            return "High-quality setup with broad confirmation."
        return "Entry is valid, but risk control remains mandatory."

    if decision == "WAIT":
        return "The setup has enough quality to monitor, but not enough confirmation to execute."

    if decision == "CHASE":
        return "The move may still rise, but the current entry quality is poor relative to the risk."

    return "The opportunity is currently weaker than other uses of capital."


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_setup(
    pair_state: Dict[str, Any],
    entry_state: Dict[str, Any],
    market_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate a plain-English Radar analysis for one setup.
    """

    market = market_state or {}

    pair_name = str(
        pair_state.get("pair")
        or pair_state.get("symbol")
        or entry_state.get("pair")
        or "UNKNOWN"
    )

    decision = _upper(entry_state.get("decision")) or "UNKNOWN"

    pair_score = _num(
        entry_state.get("pair_score"),
        _num(pair_state.get("score"), 50),
    )

    confidence = _clamp(
        _num(entry_state.get("confidence"), 50)
    )

    grade = _setup_grade(
        pair_score,
        decision,
    )

    market_points = _market_context(market)
    pair_points = _pair_edges(pair_state)
    entry_points = _entry_edges(entry_state)

    risks = _pair_risks(pair_state)
    blockers = _entry_blockers(entry_state)

    combined_risks = []

    seen = set()
    for item in blockers + risks:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            combined_risks.append(item)

    strongest_edge = (
        pair_points[0]
        if pair_points
        else entry_points[0]
        if entry_points
        else "No dominant edge identified"
    )

    biggest_risk = (
        combined_risks[0]
        if combined_risks
        else "No major technical blocker identified"
    )

    next_changes = _next_changes(
        pair_state,
        entry_state,
        market,
    )

    why_ranked = pair_points + [
        x for x in entry_points
        if x not in pair_points
    ]

    why_ranked = why_ranked[:7]

    why_not = combined_risks[:6]

    market_sentence = _sentence_join(market_points)
    edge_sentence = _sentence_join(why_ranked[:4])
    risk_sentence = _sentence_join(why_not[:3])

    if decision == "ENTER":
        summary_parts = [
            f"{pair_name} is currently an actionable {grade} setup.",
            edge_sentence,
        ]

        if risk_sentence:
            summary_parts.append(f"Main risks: {risk_sentence}")

    elif decision == "WAIT":
        summary_parts = [
            f"{pair_name} is worth watching but is not entry-ready yet.",
            edge_sentence,
        ]

        if risk_sentence:
            summary_parts.append(f"The hold-up is {risk_sentence}")

    elif decision == "CHASE":
        summary_parts = [
            f"{pair_name} has momentum, but the present location is poor for a fresh entry.",
        ]

        if risk_sentence:
            summary_parts.append(risk_sentence)

    else:
        summary_parts = [
            f"{pair_name} is not a priority setup right now.",
        ]

        if risk_sentence:
            summary_parts.append(risk_sentence)

    if market_sentence:
        summary_parts.append(f"Market context: {market_sentence}")

    analyst_summary = " ".join(
        x for x in summary_parts
        if x
    )

    return {
        "pair": pair_name,
        "decision": decision,

        "headline": _headline(
            pair_name,
            decision,
            grade,
            confidence,
        ),

        "verdict": _verdict(
            decision,
            pair_score,
            confidence,
        ),

        "setup_grade": grade,
        "confidence": round(confidence, 2),
        "confidence_label": _confidence_label(confidence),

        "strongest_edge": strongest_edge,
        "biggest_risk": biggest_risk,

        "why_ranked": why_ranked,
        "why_not": why_not,

        "market_context": market_points,
        "what_changes_next": next_changes,

        "analyst_summary": analyst_summary,
    }


def analyze_board(
    pair_rows: Iterable[Dict[str, Any]],
    entry_rows: Iterable[Dict[str, Any]],
    market_state: Optional[Dict[str, Any]] = None,
    limit: int = 5,
) -> Dict[str, Any]:
    """
    Analyze multiple Pair Engine / Entry Engine rows.

    Pair and entry rows are matched by pair name.
    """

    market = market_state or {}

    pair_map = {}

    for p in pair_rows or []:
        name = str(
            p.get("pair")
            or p.get("symbol")
            or ""
        )

        if name:
            pair_map[name] = p

    analyses = []

    for entry in entry_rows or []:
        name = str(
            entry.get("pair")
            or entry.get("symbol")
            or ""
        )

        pair = pair_map.get(
            name,
            {"pair": name},
        )

        analyses.append(
            analyze_setup(
                pair,
                entry,
                market,
            )
        )

    priority = {
        "ENTER": 4,
        "WAIT": 3,
        "CHASE": 2,
        "SKIP": 1,
    }

    analyses.sort(
        key=lambda x: (
            priority.get(x["decision"], 0),
            x["confidence"],
        ),
        reverse=True,
    )

    top = analyses[:max(1, int(limit))]

    best = top[0] if top else None

    return {
        "analyses": analyses,
        "top_analysis": top,

        "summary": {
            "analyzed": len(analyses),

            "enter_count": sum(
                1 for x in analyses
                if x["decision"] == "ENTER"
            ),

            "wait_count": sum(
                1 for x in analyses
                if x["decision"] == "WAIT"
            ),

            "skip_count": sum(
                1 for x in analyses
                if x["decision"] == "SKIP"
            ),

            "chase_count": sum(
                1 for x in analyses
                if x["decision"] == "CHASE"
            ),

            "best_setup": (
                best["pair"]
                if best else None
            ),

            "best_headline": (
                best["headline"]
                if best else None
            ),
        },
    }


# ---------------------------------------------------------------------------
# Simple terminal / Discord style renderer
# ---------------------------------------------------------------------------

def render_analysis_text(
    analysis: Dict[str, Any],
) -> str:
    """
    Convert an analysis result into a compact human-readable block.
    """

    lines = [
        analysis.get("headline", ""),
        "",
        analysis.get("verdict", ""),
        "",
        f"Confidence: {analysis.get('confidence', 0):.0f} "
        f"({analysis.get('confidence_label', 'UNKNOWN')})",
        f"Strongest edge: {analysis.get('strongest_edge', '')}",
        f"Biggest risk: {analysis.get('biggest_risk', '')}",
    ]

    why = analysis.get("why_ranked") or []

    if why:
        lines.append("")
        lines.append("Why Radar likes it:")
        lines.extend(
            f"- {x}"
            for x in why[:5]
        )

    changes = analysis.get("what_changes_next") or []

    if changes and analysis.get("decision") != "ENTER":
        lines.append("")
        lines.append("What needs to change:")
        lines.extend(
            f"- {x}"
            for x in changes[:5]
        )

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    market = {
        "market_mode": "EXPANSION",
        "market_bias": "BULLISH",
        "market_health": 82,
        "buyer_pressure": 74,
        "breadth": 68,
        "expansion_pressure": 86,
        "leading_sector": "AI",
    }

    pair = {
        "pair": "FET/USD",
        "rank": 1,
        "score": 88.9,
        "relative_strength": 92,
        "sector_strength": 88,
        "vwap_score": 94,
        "momentum_score": 90,
        "volume_score": 84,
        "structure_score": 91,
        "btc_alignment_score": 100,
        "remaining_score": 78,
        "chase_penalty": 0,
        "vwap_dist": 0.45,
        "rsi_1m": 61,
        "rsi_5m": 64,
        "phase": "TAKEOFF",
    }

    entry = {
        "pair": "FET/USD",
        "decision": "ENTER",
        "entry_style": "EXPANSION",
        "confidence": 93,
        "pair_score": 88.9,
        "rr_1": 2.4,

        "checks": {
            "vwap": {
                "passed": True,
            },
            "momentum": {
                "passed": True,
                "rsi_1m": 61,
                "rsi_5m": 64,
                "macd_turn_up": True,
            },
            "structure": {
                "passed": True,
                "impulse_pct": 0.9,
                "pullback_pct": 0.3,
            },
            "timing": {
                "passed": True,
            },
            "remaining": {
                "passed": True,
            },
            "btc_aligned": True,
        },

        "blockers": [],
        "warnings": [],
    }

    result = analyze_setup(
        pair,
        entry,
        market,
    )

    print(
        render_analysis_text(
            result
        )
    )
