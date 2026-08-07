from __future__ import annotations

"""
A+ Radar - Radar AI Orchestrator
================================

Phase 7 of the Radar architecture.

Purpose
-------
Radar AI is the orchestration layer above:

1. Market Engine
2. Pair Engine
3. Entry Engine
4. Replay Engine
5. Analyst Engine
6. Confidence Calibration

It does not replace those engines.

It combines their outputs into a single decision package and exposes
simple question-style methods such as:

    get_best_setup()
    explain_pair("FET/USD")
    get_avoid_list()
    get_highest_expectancy_setups()
    get_market_brief()
    compare_setups("SOL/USD", "FET/USD")

This module is deterministic and can run without an external LLM.
A future natural-language interface can call these same methods.
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
    return max(lo, min(hi, float(v)))


def _pair_name(row: Dict[str, Any]) -> str:
    return str(
        row.get("pair")
        or row.get("symbol")
        or ""
    )


# ---------------------------------------------------------------------------
# Radar AI
# ---------------------------------------------------------------------------

class RadarAI:
    """
    High-level orchestration layer.

    The caller supplies the existing engine functions/objects so this module
    remains easy to test and does not hard-code project import paths.

    Required callables/objects
    --------------------------
    market_builder:
        build_market_state(pair_states, market_regime)

    pair_builder:
        build_pair_rankings(pair_states, market_state)

    entry_builder:
        evaluate_entries(pair_rows, market_state)

    analyst:
        analyze_setup(pair_state, entry_state, market_state)

    calibrator:
        ConfidenceCalibrator instance

    replay:
        ReplayEngine instance
    """

    def __init__(
        self,
        *,
        market_builder,
        pair_builder,
        entry_builder,
        analyst,
        calibrator=None,
        replay=None,
    ):
        self.market_builder = market_builder
        self.pair_builder = pair_builder
        self.entry_builder = entry_builder
        self.analyst = analyst
        self.calibrator = calibrator
        self.replay = replay

    # -----------------------------------------------------------------------
    # Main orchestration
    # -----------------------------------------------------------------------

    def run(
        self,
        pair_states: Iterable[Dict[str, Any]],
        market_regime: str = "WAITING",
    ) -> Dict[str, Any]:
        """
        Run all live decision layers and return one unified Radar state.
        """

        pairs = list(pair_states or [])

        market_state = self.market_builder(
            pairs,
            market_regime,
        )

        pair_result = self.pair_builder(
            pairs,
            market_state,
        )

        watchlist = (
            pair_result.get("watchlist")
            or pair_result.get("top_5")
            or []
        )

        entry_result = self.entry_builder(
            watchlist,
            market_state,
        )

        ranked_by_pair = {
            _pair_name(row): row
            for row in pair_result.get("ranked_pairs", [])
        }

        analyzed = []

        for entry in entry_result.get("evaluated", []):
            name = _pair_name(entry)
            pair_row = ranked_by_pair.get(
                name,
                {"pair": name},
            )

            analysis = self.analyst(
                pair_row,
                entry,
                market_state,
            )

            calibrated = None

            if self.calibrator is not None:
                try:
                    calibrated = self.calibrator.calibrate(
                        entry,
                        market_state,
                    )
                except Exception as exc:
                    calibrated = {
                        "error": str(exc),
                        "raw_confidence": entry.get("confidence"),
                        "calibrated_confidence": entry.get("confidence"),
                        "reliability": "UNKNOWN",
                    }

            combined = {
                "pair": name,
                "pair_state": pair_row,
                "entry_state": entry,
                "analysis": analysis,
                "calibration": calibrated,
            }

            # Final confidence favors calibrated confidence when available.
            final_conf = _num(
                (calibrated or {}).get("calibrated_confidence"),
                _num(entry.get("confidence"), 50),
            )

            combined["final_confidence"] = round(
                _clamp(final_conf),
                2,
            )

            analyzed.append(combined)

        priority = {
            "ENTER": 5,
            "WAIT": 4,
            "CHASE": 2,
            "SKIP": 1,
        }

        analyzed.sort(
            key=lambda x: (
                priority.get(
                    _upper(
                        x["entry_state"].get("decision")
                    ),
                    0,
                ),
                x["final_confidence"],
                _num(x["pair_state"].get("score")),
            ),
            reverse=True,
        )

        best_setup = analyzed[0] if analyzed else None

        return {
            "market_state": market_state,
            "pair_result": pair_result,
            "entry_result": entry_result,
            "analyzed_setups": analyzed,
            "best_setup": best_setup,
            "command_brief": self._build_command_brief(
                market_state,
                pair_result,
                entry_result,
                best_setup,
            ),
        }

    # -----------------------------------------------------------------------
    # Command brief
    # -----------------------------------------------------------------------

    def _build_command_brief(
        self,
        market: Dict[str, Any],
        pair_result: Dict[str, Any],
        entry_result: Dict[str, Any],
        best_setup: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:

        mode = _upper(market.get("market_mode"))
        recommended = _text(market.get("recommended_mode"))
        health = _num(market.get("market_health"), 50)
        bias = _upper(market.get("market_bias"))
        leading_sector = _text(market.get("leading_sector"))

        enter_count = (
            entry_result.get("summary", {}).get("enter_count", 0)
        )

        best_pair = None
        best_decision = None
        best_confidence = None

        if best_setup:
            best_pair = best_setup["pair"]
            best_decision = _upper(
                best_setup["entry_state"].get("decision")
            )
            best_confidence = best_setup["final_confidence"]

        if enter_count > 0:
            posture = "ACTIVE"
        elif mode in {"BUILDING_PRESSURE", "SPRING_LOADED", "RELOAD"}:
            posture = "PREPARE"
        elif mode in {"EXHAUSTION", "DEAD_AIR"}:
            posture = "DEFENSIVE"
        else:
            posture = "SELECTIVE"

        headline_parts = []

        if mode:
            headline_parts.append(
                mode.replace("_", " ").title()
            )

        if bias:
            headline_parts.append(
                bias.title()
            )

        if best_pair and best_decision == "ENTER":
            headline = (
                f"{' / '.join(headline_parts)} — "
                f"{best_pair} is the top confirmed setup"
            )
        elif best_pair:
            headline = (
                f"{' / '.join(headline_parts)} — "
                f"{best_pair} is the top watch"
            )
        else:
            headline = (
                f"{' / '.join(headline_parts)} — "
                f"no actionable setup"
            )

        return {
            "headline": headline,
            "posture": posture,
            "recommended_mode": recommended,
            "market_health": round(health, 1),
            "leading_sector": leading_sector,
            "best_pair": best_pair,
            "best_decision": best_decision,
            "best_confidence": best_confidence,
            "enter_count": enter_count,
            "top_5": [
                row.get("pair")
                for row in pair_result.get("top_5", [])
            ],
        }

    # -----------------------------------------------------------------------
    # Question-style interface
    # -----------------------------------------------------------------------

    def get_market_brief(
        self,
        radar_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return radar_state.get(
            "command_brief",
            {},
        )

    def get_best_setup(
        self,
        radar_state: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        return radar_state.get("best_setup")

    def explain_pair(
        self,
        radar_state: Dict[str, Any],
        pair: str,
    ) -> Dict[str, Any]:
        target = _upper(pair)

        for row in radar_state.get("analyzed_setups", []):
            if _upper(row.get("pair")) == target:
                return {
                    "pair": row["pair"],
                    "decision": row["entry_state"].get("decision"),
                    "final_confidence": row["final_confidence"],
                    "headline": row["analysis"].get("headline"),
                    "verdict": row["analysis"].get("verdict"),
                    "why_ranked": row["analysis"].get("why_ranked"),
                    "why_not": row["analysis"].get("why_not"),
                    "what_changes_next": row["analysis"].get(
                        "what_changes_next"
                    ),
                    "calibration": row.get("calibration"),
                }

        # Fall back to ranked board if pair did not reach Entry Engine.
        for row in radar_state.get(
            "pair_result",
            {},
        ).get("ranked_pairs", []):
            if _upper(row.get("pair")) == target:
                return {
                    "pair": row.get("pair"),
                    "decision": "NOT EVALUATED",
                    "rank": row.get("rank"),
                    "score": row.get("score"),
                    "tier": row.get("tier"),
                    "disposition": row.get("disposition"),
                    "reasons": row.get("reasons"),
                    "risks": row.get("risks"),
                    "message": (
                        "Pair ranked on the board but did not qualify "
                        "for the current Entry Engine watchlist."
                    ),
                }

        return {
            "pair": pair,
            "error": "Pair not found in current Radar state",
        }

    def get_avoid_list(
        self,
        radar_state: Dict[str, Any],
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        rows = []

        for item in radar_state.get("analyzed_setups", []):
            decision = _upper(
                item["entry_state"].get("decision")
            )

            if decision in {"SKIP", "CHASE"}:
                rows.append(
                    {
                        "pair": item["pair"],
                        "decision": decision,
                        "confidence": item["final_confidence"],
                        "reason": item["analysis"].get(
                            "biggest_risk"
                        ),
                    }
                )

        # Also include heavily penalized ranked pairs that never reached
        # the Entry Engine.
        seen = {
            _upper(x["pair"])
            for x in rows
        }

        for pair in radar_state.get(
            "pair_result",
            {},
        ).get("ranked_pairs", []):
            if len(rows) >= limit:
                break

            name = pair.get("pair")

            if _upper(name) in seen:
                continue

            if (
                _num(pair.get("chase_penalty")) >= 20
                or _upper(pair.get("disposition")) == "SKIP"
            ):
                rows.append(
                    {
                        "pair": name,
                        "decision": "AVOID",
                        "confidence": None,
                        "reason": (
                            (pair.get("risks") or ["Poor entry quality"])[0]
                        ),
                    }
                )

        return rows[:limit]

    def get_highest_expectancy_setups(
        self,
        radar_state: Dict[str, Any],
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Rank current setups using calibrated confidence plus historical expectancy.
        """

        rows = []

        for item in radar_state.get("analyzed_setups", []):
            cal = item.get("calibration") or {}
            expectancy = cal.get("expectancy_r")

            exp = (
                float(expectancy)
                if isinstance(expectancy, (int, float))
                else 0.0
            )

            score = (
                item["final_confidence"]
                + max(-15.0, min(20.0, exp * 6.0))
            )

            rows.append(
                {
                    "pair": item["pair"],
                    "decision": item["entry_state"].get("decision"),
                    "final_confidence": item["final_confidence"],
                    "historical_win_rate": cal.get(
                        "historical_win_rate"
                    ),
                    "expectancy_r": expectancy,
                    "reliability": cal.get("reliability"),
                    "expectancy_score": round(score, 2),
                }
            )

        rows.sort(
            key=lambda x: x["expectancy_score"],
            reverse=True,
        )

        return rows[:max(1, int(limit))]

    def compare_setups(
        self,
        radar_state: Dict[str, Any],
        pair_a: str,
        pair_b: str,
    ) -> Dict[str, Any]:

        a = self.explain_pair(
            radar_state,
            pair_a,
        )

        b = self.explain_pair(
            radar_state,
            pair_b,
        )

        a_conf = _num(
            a.get("final_confidence"),
            _num(a.get("score"), 0),
        )

        b_conf = _num(
            b.get("final_confidence"),
            _num(b.get("score"), 0),
        )

        winner = (
            a.get("pair")
            if a_conf > b_conf
            else b.get("pair")
            if b_conf > a_conf
            else "TIE"
        )

        return {
            "pair_a": a,
            "pair_b": b,
            "preferred": winner,
            "confidence_gap": round(
                abs(a_conf - b_conf),
                2,
            ),
        }

    # -----------------------------------------------------------------------
    # Replay-aware questions
    # -----------------------------------------------------------------------

    def historical_pair_report(
        self,
        pair: str,
    ) -> Dict[str, Any]:
        if self.replay is None:
            return {
                "pair": pair,
                "error": "Replay Engine is not connected",
            }

        overall = self.replay.performance_summary(
            pair=pair,
        )

        signals = self.replay.list_signals(
            pair=pair,
            limit=100,
        )

        return {
            "pair": pair,
            "performance": overall,
            "signals_found": len(signals),
            "recent_signals": signals[:10],
        }

    def similar_market_performance(
        self,
        radar_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if self.replay is None:
            return {
                "error": "Replay Engine is not connected",
            }

        mode = radar_state.get(
            "market_state",
            {},
        ).get("market_mode")

        stats = self.replay.performance_summary(
            market_mode=mode,
        )

        return {
            "market_mode": mode,
            "historical_performance": stats,
        }


# ---------------------------------------------------------------------------
# Compact renderer
# ---------------------------------------------------------------------------

def render_command_brief(
    radar_state: Dict[str, Any],
) -> str:
    brief = radar_state.get("command_brief", {})

    lines = [
        brief.get("headline", "Radar status unavailable"),
        f"Posture: {brief.get('posture', 'UNKNOWN')}",
        f"Mode: {brief.get('recommended_mode', 'Unknown')}",
        f"Market Health: {brief.get('market_health', 0)}",
    ]

    if brief.get("leading_sector"):
        lines.append(
            f"Leading Sector: {brief['leading_sector']}"
        )

    if brief.get("best_pair"):
        lines.append(
            f"Best Setup: {brief['best_pair']} "
            f"({brief.get('best_decision')}, "
            f"{brief.get('best_confidence')} confidence)"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    # Minimal mock engines so the orchestrator can be tested standalone.
    def mock_market_builder(pairs, regime):
        return {
            "market_mode": "EXPANSION",
            "market_bias": "BULLISH",
            "market_health": 81,
            "recommended_mode": "Expansion",
            "leading_sector": "AI",
        }

    def mock_pair_builder(pairs, market):
        ranked = [
            {
                **p,
                "rank": i + 1,
                "score": p.get("score", 80),
                "disposition": "PRIORITY",
                "chase_penalty": 0,
            }
            for i, p in enumerate(pairs)
        ]

        return {
            "ranked_pairs": ranked,
            "top_5": ranked[:5],
            "watchlist": ranked[:5],
        }

    def mock_entry_builder(pairs, market):
        evaluated = []

        for i, p in enumerate(pairs):
            evaluated.append(
                {
                    "pair": p["pair"],
                    "decision": "ENTER" if i == 0 else "WAIT",
                    "entry_style": "EXPANSION",
                    "confidence": 91 - (i * 5),
                    "pair_score": p["score"],
                    "blockers": [],
                    "warnings": [],
                    "checks": {},
                }
            )

        return {
            "evaluated": evaluated,
            "entries": [
                x for x in evaluated
                if x["decision"] == "ENTER"
            ],
            "summary": {
                "enter_count": 1,
            },
        }

    def mock_analyst(pair, entry, market):
        return {
            "headline": f"{pair['pair']} analysis",
            "verdict": "Test verdict",
            "why_ranked": ["Strong relative strength"],
            "why_not": [],
            "what_changes_next": [],
            "biggest_risk": "No major blocker",
        }

    class MockCalibrator:
        def calibrate(self, entry, market):
            return {
                "calibrated_confidence": entry["confidence"] - 2,
                "historical_win_rate": 76.0,
                "expectancy_r": 1.2,
                "reliability": "HIGH",
            }

    radar = RadarAI(
        market_builder=mock_market_builder,
        pair_builder=mock_pair_builder,
        entry_builder=mock_entry_builder,
        analyst=mock_analyst,
        calibrator=MockCalibrator(),
    )

    result = radar.run(
        [
            {
                "pair": "FET/USD",
                "score": 89,
            },
            {
                "pair": "SOL/USD",
                "score": 83,
            },
        ],
        "PREBULL",
    )

    print(
        render_command_brief(
            result
        )
    )

    print()
    print(
        radar.explain_pair(
            result,
            "FET/USD",
        )
    )
