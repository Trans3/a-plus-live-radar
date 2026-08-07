from __future__ import annotations

"""
A+ Radar - Learning Engine
==========================

Phase 8 of the Radar architecture.

Purpose
-------
The Learning Engine answers:

    "What is Radar learning from its own history?"

It analyzes Replay Engine data and identifies:

- Best / worst market modes
- Best / worst pairs
- Best / worst entry styles
- Confidence calibration drift
- Time-of-day performance
- Sector performance
- Which feature ranges are associated with higher expectancy
- Which thresholds may be too loose or too strict
- Which current rules deserve review

IMPORTANT
---------
This engine is ADVISORY by design.

It does NOT automatically modify thresholds or strategy logic.

Why?
Because auto-changing live trading rules from a limited sample is dangerous.
Instead, it generates evidence-based recommendations that you can approve.

This becomes the research layer feeding future strategy revisions.
"""

from collections import defaultdict
from datetime import datetime
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _num(v: Any, default: Optional[float] = 0.0) -> Optional[float]:
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


def _safe_mean(values: Iterable[float]) -> Optional[float]:
    vals = [float(x) for x in values if x is not None]
    return mean(vals) if vals else None


def _expectancy(rows: List[Dict[str, Any]]) -> Optional[float]:
    rs = [
        _num(r.get("realized_r"), None)
        for r in rows
        if r.get("realized_r") is not None
    ]
    rs = [x for x in rs if x is not None]
    return _safe_mean(rs)


def _win_rate(rows: List[Dict[str, Any]]) -> Optional[float]:
    wins = sum(1 for r in rows if _upper(r.get("outcome")) == "WIN")
    losses = sum(1 for r in rows if _upper(r.get("outcome")) == "LOSS")
    resolved = wins + losses
    return (wins / resolved * 100.0) if resolved else None


def _profit_factor(rows: List[Dict[str, Any]]) -> Optional[float]:
    rs = [
        _num(r.get("realized_r"), None)
        for r in rows
        if r.get("realized_r") is not None
    ]
    rs = [x for x in rs if x is not None]

    if not rs:
        return None

    gross_win = sum(x for x in rs if x > 0)
    gross_loss = abs(sum(x for x in rs if x < 0))

    if gross_loss > 0:
        return gross_win / gross_loss

    if gross_win > 0:
        return float("inf")

    return None


def _bucket_numeric(
    value: Optional[float],
    buckets: List[Tuple[str, float, float]],
) -> Optional[str]:
    if value is None:
        return None

    for name, lo, hi in buckets:
        if lo <= value < hi:
            return name

    return None


def _hour_from_iso(ts: Any) -> Optional[int]:
    if not ts:
        return None

    try:
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.hour
    except Exception:
        return None


def _feature_value(row: Dict[str, Any], key: str) -> Optional[float]:
    pair_state = row.get("pair_state") or {}
    entry_state = row.get("entry_state") or {}
    market_state = row.get("market_state") or {}

    search_order = [
        pair_state,
        entry_state,
        market_state,
        row,
    ]

    for src in search_order:
        if key in src and src.get(key) is not None:
            return _num(src.get(key), None)

    return None


# ---------------------------------------------------------------------------
# Learning Engine
# ---------------------------------------------------------------------------

class LearningEngine:
    """
    Analyze historical Radar replay data and produce advisory recommendations.
    """

    def __init__(
        self,
        replay_engine,
        *,
        min_group_trades: int = 12,
        min_threshold_trades: int = 20,
    ):
        self.replay = replay_engine
        self.min_group_trades = int(min_group_trades)
        self.min_threshold_trades = int(min_threshold_trades)

    # -----------------------------------------------------------------------
    # Data loading
    # -----------------------------------------------------------------------

    def _closed_entries(self, limit: int = 100000) -> List[Dict[str, Any]]:
        rows = self.replay.list_signals(
            decision="ENTER",
            status="CLOSED",
            limit=limit,
        )

        return [
            r for r in rows
            if _upper(r.get("outcome")) in {"WIN", "LOSS", "BREAKEVEN"}
        ]

    # -----------------------------------------------------------------------
    # Group summaries
    # -----------------------------------------------------------------------

    def _group_summary(
        self,
        rows: List[Dict[str, Any]],
        key_fn,
        label: str,
    ) -> List[Dict[str, Any]]:
        groups = defaultdict(list)

        for row in rows:
            key = key_fn(row)
            if key not in (None, ""):
                groups[str(key)].append(row)

        out = []

        for key, bucket in groups.items():
            if len(bucket) < self.min_group_trades:
                continue

            wr = _win_rate(bucket)
            exp = _expectancy(bucket)
            pf = _profit_factor(bucket)

            out.append({
                label: key,
                "trades": len(bucket),
                "win_rate": round(wr, 2) if wr is not None else None,
                "expectancy_r": round(exp, 3) if exp is not None else None,
                "profit_factor_r": (
                    "INF"
                    if pf == float("inf")
                    else round(pf, 3)
                    if isinstance(pf, (int, float))
                    else None
                ),
            })

        out.sort(
            key=lambda x: (
                x["expectancy_r"]
                if isinstance(x.get("expectancy_r"), (int, float))
                else -999
            ),
            reverse=True,
        )

        return out

    def performance_by_market_mode(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        rows = rows if rows is not None else self._closed_entries()
        return self._group_summary(
            rows,
            lambda r: _upper(r.get("market_mode")),
            "market_mode",
        )

    def performance_by_entry_style(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        rows = rows if rows is not None else self._closed_entries()
        return self._group_summary(
            rows,
            lambda r: _upper(r.get("entry_style")),
            "entry_style",
        )

    def performance_by_pair(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        rows = rows if rows is not None else self._closed_entries()
        return self._group_summary(
            rows,
            lambda r: r.get("pair"),
            "pair",
        )

    def performance_by_sector(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        rows = rows if rows is not None else self._closed_entries()
        return self._group_summary(
            rows,
            lambda r: (r.get("pair_state") or {}).get("sector"),
            "sector",
        )

    def performance_by_hour(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        rows = rows if rows is not None else self._closed_entries()
        return self._group_summary(
            rows,
            lambda r: _hour_from_iso(r.get("created_at")),
            "hour_utc",
        )

    # -----------------------------------------------------------------------
    # Confidence calibration diagnostics
    # -----------------------------------------------------------------------

    def confidence_buckets(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        rows = rows if rows is not None else self._closed_entries()

        buckets = [
            ("50-59", 50, 60),
            ("60-69", 60, 70),
            ("70-79", 70, 80),
            ("80-89", 80, 90),
            ("90-100", 90, 101),
        ]

        grouped = defaultdict(list)

        for row in rows:
            conf = _num(row.get("confidence"), None)

            if conf is None:
                conf = _feature_value(row, "confidence")

            name = _bucket_numeric(conf, buckets)

            if name:
                grouped[name].append(row)

        out = []

        for name, bucket in grouped.items():
            if len(bucket) < self.min_group_trades:
                continue

            lo = int(name.split("-")[0])
            hi = int(name.split("-")[1])

            nominal = (lo + hi) / 2.0
            wr = _win_rate(bucket)
            exp = _expectancy(bucket)

            calibration_error = (
                wr - nominal
                if wr is not None
                else None
            )

            out.append({
                "confidence_bucket": name,
                "trades": len(bucket),
                "nominal_confidence": round(nominal, 1),
                "historical_win_rate": round(wr, 2) if wr is not None else None,
                "calibration_error": (
                    round(calibration_error, 2)
                    if calibration_error is not None
                    else None
                ),
                "expectancy_r": round(exp, 3) if exp is not None else None,
            })

        return out

    # -----------------------------------------------------------------------
    # Feature studies
    # -----------------------------------------------------------------------

    def feature_study(
        self,
        feature: str,
        buckets: List[Tuple[str, float, float]],
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        rows = rows if rows is not None else self._closed_entries()
        grouped = defaultdict(list)

        for row in rows:
            value = _feature_value(row, feature)
            bucket = _bucket_numeric(value, buckets)

            if bucket:
                grouped[bucket].append(row)

        out = []

        for bucket_name, bucket_rows in grouped.items():
            if len(bucket_rows) < self.min_group_trades:
                continue

            wr = _win_rate(bucket_rows)
            exp = _expectancy(bucket_rows)

            out.append({
                "feature": feature,
                "bucket": bucket_name,
                "trades": len(bucket_rows),
                "win_rate": round(wr, 2) if wr is not None else None,
                "expectancy_r": round(exp, 3) if exp is not None else None,
            })

        out.sort(
            key=lambda x: (
                x["expectancy_r"]
                if isinstance(x.get("expectancy_r"), (int, float))
                else -999
            ),
            reverse=True,
        )

        return out

    def standard_feature_studies(
        self,
        rows: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        rows = rows if rows is not None else self._closed_entries()

        return {
            "rsi_1m": self.feature_study(
                "rsi_1m",
                [
                    ("<50", 0, 50),
                    ("50-54", 50, 55),
                    ("55-59", 55, 60),
                    ("60-64", 60, 65),
                    ("65-69", 65, 70),
                    ("70-74", 70, 75),
                    ("75+", 75, 101),
                ],
                rows,
            ),

            "rsi_5m": self.feature_study(
                "rsi_5m",
                [
                    ("<50", 0, 50),
                    ("50-54", 50, 55),
                    ("55-59", 55, 60),
                    ("60-64", 60, 65),
                    ("65-69", 65, 70),
                    ("70-74", 70, 75),
                    ("75+", 75, 101),
                ],
                rows,
            ),

            "vwap_dist": self.feature_study(
                "vwap_dist",
                [
                    ("0-0.25", 0, 0.25),
                    ("0.25-0.50", 0.25, 0.50),
                    ("0.50-0.75", 0.50, 0.75),
                    ("0.75-1.00", 0.75, 1.00),
                    ("1.00-1.50", 1.00, 1.50),
                    ("1.50+", 1.50, 999),
                ],
                rows,
            ),

            "impulse_pct": self.feature_study(
                "impulse_pct",
                [
                    ("<0.4", -999, 0.4),
                    ("0.4-0.6", 0.4, 0.6),
                    ("0.6-0.9", 0.6, 0.9),
                    ("0.9-1.2", 0.9, 1.2),
                    ("1.2-1.6", 1.2, 1.6),
                    ("1.6+", 1.6, 999),
                ],
                rows,
            ),

            "pullback_pct": self.feature_study(
                "pullback_pct",
                [
                    ("0-0.2", 0, 0.2),
                    ("0.2-0.4", 0.2, 0.4),
                    ("0.4-0.65", 0.4, 0.65),
                    ("0.65-1.0", 0.65, 1.0),
                    ("1.0+", 1.0, 999),
                ],
                rows,
            ),

            "pair_score": self.feature_study(
                "pair_score",
                [
                    ("<60", 0, 60),
                    ("60-69", 60, 70),
                    ("70-79", 70, 80),
                    ("80-89", 80, 90),
                    ("90+", 90, 101),
                ],
                rows,
            ),

            "remaining": self.feature_study(
                "remaining",
                [
                    ("<30", 0, 30),
                    ("30-49", 30, 50),
                    ("50-64", 50, 65),
                    ("65-79", 65, 80),
                    ("80+", 80, 101),
                ],
                rows,
            ),
        }

    # -----------------------------------------------------------------------
    # Recommendations
    # -----------------------------------------------------------------------

    def _recommend_from_confidence(
        self,
        confidence_rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        recs = []

        for row in confidence_rows:
            err = row.get("calibration_error")

            if not isinstance(err, (int, float)):
                continue

            if err <= -12:
                recs.append({
                    "type": "CONFIDENCE",
                    "severity": "HIGH",
                    "subject": row["confidence_bucket"],
                    "finding": (
                        f"Confidence bucket {row['confidence_bucket']} is "
                        f"overconfident by about {abs(err):.1f} points."
                    ),
                    "recommendation": (
                        "Reduce calibrated confidence for this bucket until "
                        "historical results improve."
                    ),
                })

            elif err >= 12:
                recs.append({
                    "type": "CONFIDENCE",
                    "severity": "MEDIUM",
                    "subject": row["confidence_bucket"],
                    "finding": (
                        f"Confidence bucket {row['confidence_bucket']} is "
                        f"understating historical results by about {err:.1f} points."
                    ),
                    "recommendation": (
                        "Consider allowing a modest upward calibration, but only "
                        "after the sample remains stable."
                    ),
                })

        return recs

    def _recommend_from_group(
        self,
        rows: List[Dict[str, Any]],
        label: str,
    ) -> List[Dict[str, Any]]:
        recs = []

        for row in rows:
            exp = row.get("expectancy_r")
            trades = row.get("trades", 0)
            value = row.get(label)

            if not isinstance(exp, (int, float)):
                continue

            if exp <= -0.25 and trades >= self.min_group_trades:
                recs.append({
                    "type": label.upper(),
                    "severity": "HIGH",
                    "subject": value,
                    "finding": (
                        f"{value} has negative expectancy of {exp:.2f}R "
                        f"across {trades} trades."
                    ),
                    "recommendation": (
                        "Downgrade or temporarily disable this context until "
                        "the setup logic is reviewed."
                    ),
                })

            elif exp >= 0.75 and trades >= self.min_group_trades:
                recs.append({
                    "type": label.upper(),
                    "severity": "MEDIUM",
                    "subject": value,
                    "finding": (
                        f"{value} is producing strong expectancy of {exp:.2f}R "
                        f"across {trades} trades."
                    ),
                    "recommendation": (
                        "Preserve this context and consider giving it more ranking "
                        "weight if the edge persists."
                    ),
                })

        return recs

    def _recommend_from_feature(
        self,
        feature: str,
        rows: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        recs = []

        valid = [
            r for r in rows
            if isinstance(r.get("expectancy_r"), (int, float))
            and r.get("trades", 0) >= self.min_threshold_trades
        ]

        if len(valid) < 2:
            return recs

        best = max(valid, key=lambda x: x["expectancy_r"])
        worst = min(valid, key=lambda x: x["expectancy_r"])

        gap = best["expectancy_r"] - worst["expectancy_r"]

        if gap >= 0.75:
            recs.append({
                "type": "FEATURE",
                "severity": "MEDIUM",
                "subject": feature,
                "finding": (
                    f"{feature} shows a meaningful expectancy spread: "
                    f"{best['bucket']} = {best['expectancy_r']:.2f}R versus "
                    f"{worst['bucket']} = {worst['expectancy_r']:.2f}R."
                ),
                "recommendation": (
                    f"Review whether the strategy should favor {best['bucket']} "
                    f"and penalize {worst['bucket']}."
                ),
            })

        return recs

    # -----------------------------------------------------------------------
    # Main report
    # -----------------------------------------------------------------------

    def build_learning_report(self) -> Dict[str, Any]:
        rows = self._closed_entries()

        market_modes = self.performance_by_market_mode(rows)
        entry_styles = self.performance_by_entry_style(rows)
        pairs = self.performance_by_pair(rows)
        sectors = self.performance_by_sector(rows)
        hours = self.performance_by_hour(rows)
        confidence = self.confidence_buckets(rows)
        features = self.standard_feature_studies(rows)

        recommendations: List[Dict[str, Any]] = []

        recommendations += self._recommend_from_confidence(confidence)
        recommendations += self._recommend_from_group(
            market_modes,
            "market_mode",
        )
        recommendations += self._recommend_from_group(
            entry_styles,
            "entry_style",
        )
        recommendations += self._recommend_from_group(
            sectors,
            "sector",
        )

        for feature_name, feature_rows in features.items():
            recommendations += self._recommend_from_feature(
                feature_name,
                feature_rows,
            )

        severity_order = {
            "HIGH": 3,
            "MEDIUM": 2,
            "LOW": 1,
        }

        recommendations.sort(
            key=lambda x: severity_order.get(
                x.get("severity"),
                0,
            ),
            reverse=True,
        )

        overall_wr = _win_rate(rows)
        overall_exp = _expectancy(rows)
        overall_pf = _profit_factor(rows)

        best_mode = market_modes[0] if market_modes else None
        worst_mode = market_modes[-1] if market_modes else None

        best_style = entry_styles[0] if entry_styles else None
        best_pair = pairs[0] if pairs else None
        best_sector = sectors[0] if sectors else None
        best_hour = hours[0] if hours else None

        return {
            "summary": {
                "trades_analyzed": len(rows),
                "overall_win_rate": (
                    round(overall_wr, 2)
                    if overall_wr is not None
                    else None
                ),
                "overall_expectancy_r": (
                    round(overall_exp, 3)
                    if overall_exp is not None
                    else None
                ),
                "overall_profit_factor_r": (
                    "INF"
                    if overall_pf == float("inf")
                    else round(overall_pf, 3)
                    if isinstance(overall_pf, (int, float))
                    else None
                ),
                "best_market_mode": (
                    best_mode.get("market_mode")
                    if best_mode else None
                ),
                "worst_market_mode": (
                    worst_mode.get("market_mode")
                    if worst_mode else None
                ),
                "best_entry_style": (
                    best_style.get("entry_style")
                    if best_style else None
                ),
                "best_pair": (
                    best_pair.get("pair")
                    if best_pair else None
                ),
                "best_sector": (
                    best_sector.get("sector")
                    if best_sector else None
                ),
                "best_hour_utc": (
                    best_hour.get("hour_utc")
                    if best_hour else None
                ),
                "recommendation_count": len(recommendations),
            },

            "performance": {
                "market_modes": market_modes,
                "entry_styles": entry_styles,
                "pairs": pairs,
                "sectors": sectors,
                "hours_utc": hours,
            },

            "confidence_calibration": confidence,

            "feature_studies": features,

            "recommendations": recommendations,
        }

    # -----------------------------------------------------------------------
    # Compact strategy review
    # -----------------------------------------------------------------------

    def strategy_review(self) -> Dict[str, Any]:
        report = self.build_learning_report()
        summary = report["summary"]
        recs = report["recommendations"]

        if summary["trades_analyzed"] < self.min_threshold_trades:
            posture = "COLLECT MORE DATA"
        elif any(r.get("severity") == "HIGH" for r in recs):
            posture = "REVIEW REQUIRED"
        elif recs:
            posture = "OPTIMIZATION AVAILABLE"
        else:
            posture = "STABLE"

        return {
            "posture": posture,
            "trades_analyzed": summary["trades_analyzed"],
            "overall_win_rate": summary["overall_win_rate"],
            "overall_expectancy_r": summary["overall_expectancy_r"],
            "best_market_mode": summary["best_market_mode"],
            "best_entry_style": summary["best_entry_style"],
            "top_recommendations": recs[:5],
        }


# ---------------------------------------------------------------------------
# Text renderer
# ---------------------------------------------------------------------------

def render_learning_report(report: Dict[str, Any]) -> str:
    summary = report.get("summary", {})
    recs = report.get("recommendations", [])

    lines = [
        "RADAR LEARNING REPORT",
        "",
        f"Trades analyzed: {summary.get('trades_analyzed', 0)}",
        f"Win rate: {summary.get('overall_win_rate')}",
        f"Expectancy: {summary.get('overall_expectancy_r')}R",
        f"Profit factor: {summary.get('overall_profit_factor_r')}",
    ]

    if summary.get("best_market_mode"):
        lines.append(
            f"Best market mode: {summary['best_market_mode']}"
        )

    if summary.get("best_entry_style"):
        lines.append(
            f"Best entry style: {summary['best_entry_style']}"
        )

    if summary.get("best_sector"):
        lines.append(
            f"Best sector: {summary['best_sector']}"
        )

    if recs:
        lines.append("")
        lines.append("Top learning recommendations:")

        for r in recs[:5]:
            lines.append(
                f"- [{r.get('severity')}] "
                f"{r.get('finding')} "
                f"{r.get('recommendation')}"
            )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    class MockReplay:
        def list_signals(self, **kwargs):
            rows = []

            # Expansion performs well.
            for i in range(30):
                win = i < 22
                rows.append({
                    "signal_id": f"e{i}",
                    "created_at": f"2026-08-{(i % 20) + 1:02d}T14:00:00+00:00",
                    "pair": "FET/USD" if i % 2 == 0 else "SOL/USD",
                    "decision": "ENTER",
                    "status": "CLOSED",
                    "outcome": "WIN" if win else "LOSS",
                    "realized_r": 1.6 if win else -1.0,
                    "confidence": 85,
                    "market_mode": "EXPANSION",
                    "entry_style": "EXPANSION",
                    "pair_state": {
                        "sector": "AI" if i % 2 == 0 else "L1",
                        "rsi_1m": 61,
                        "rsi_5m": 63,
                        "vwap_dist": 0.45,
                        "impulse_pct": 0.9,
                        "pullback_pct": 0.35,
                        "score": 84,
                        "remaining": 72,
                    },
                    "entry_state": {
                        "pair_score": 84,
                    },
                    "market_state": {},
                })

            # Mixed airspace / sharpshooter underperforms.
            for i in range(20):
                win = i < 7
                rows.append({
                    "signal_id": f"s{i}",
                    "created_at": f"2026-07-{(i % 20) + 1:02d}T02:00:00+00:00",
                    "pair": "XYZ/USD",
                    "decision": "ENTER",
                    "status": "CLOSED",
                    "outcome": "WIN" if win else "LOSS",
                    "realized_r": 1.2 if win else -1.0,
                    "confidence": 88,
                    "market_mode": "MIXED_AIRSPACE",
                    "entry_style": "SHARPSHOOTER",
                    "pair_state": {
                        "sector": "OTHER",
                        "rsi_1m": 76,
                        "rsi_5m": 72,
                        "vwap_dist": 1.4,
                        "impulse_pct": 1.8,
                        "pullback_pct": 0.8,
                        "score": 73,
                        "remaining": 30,
                    },
                    "entry_state": {
                        "pair_score": 73,
                    },
                    "market_state": {},
                })

            return rows

    engine = LearningEngine(
        MockReplay(),
        min_group_trades=5,
        min_threshold_trades=5,
    )

    report = engine.build_learning_report()

    print(render_learning_report(report))
