from __future__ import annotations
"""
A+ Radar - Confidence Calibration Engine
Phase 6

Purpose
-------
Replace static confidence with historically calibrated confidence.

Inputs
------
- Replay Engine performance history
- Current Market / Pair / Entry state

Outputs
-------
- calibrated_confidence
- historical_win_rate
- expectancy_r
- confidence_delta
- reliability
"""

from typing import Dict, Any

def _clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, float(v)))

class ConfidenceCalibrator:
    def __init__(self, replay_engine):
        self.replay = replay_engine

    def calibrate(self,
                  entry_state: Dict[str,Any],
                  market_state: Dict[str,Any]) -> Dict[str,Any]:

        raw = _clamp(entry_state.get("confidence",50))

        pair = entry_state.get("pair")
        style = entry_state.get("entry_style")
        mode = market_state.get("market_mode")

        global_stats = self.replay.performance_summary(
            market_mode=mode,
            entry_style=style
        )

        pair_stats = self.replay.performance_summary(
            pair=pair,
            market_mode=mode,
            entry_style=style
        )

        # Prefer pair history when sample is meaningful.
        stats = pair_stats if pair_stats["trades"] >= 20 else global_stats

        trades = stats["trades"] or 0
        reliability = min(100.0, trades * 2.5)

        win_rate = stats["win_rate"]
        expectancy = stats["expectancy_r"]

        calibrated = raw

        if win_rate is not None:
            calibrated = raw*0.55 + win_rate*0.45

        if expectancy is not None:
            if expectancy > 2:
                calibrated += 6
            elif expectancy > 1:
                calibrated += 3
            elif expectancy < 0:
                calibrated -= 8

        if reliability < 30:
            calibrated = raw*0.75 + calibrated*0.25

        calibrated = _clamp(calibrated)

        if reliability >= 80:
            rel = "HIGH"
        elif reliability >= 50:
            rel = "MEDIUM"
        else:
            rel = "LOW"

        return {
            "pair": pair,
            "raw_confidence": round(raw,2),
            "calibrated_confidence": round(calibrated,2),
            "confidence_delta": round(calibrated-raw,2),
            "historical_win_rate": win_rate,
            "expectancy_r": expectancy,
            "trades_used": trades,
            "reliability": rel,
            "reliability_score": round(reliability,1),
            "historical_market_mode": mode,
            "historical_entry_style": style,
        }

if __name__ == "__main__":
    class MockReplay:
        def performance_summary(self, **kwargs):
            return {
                "trades":42,
                "win_rate":78.4,
                "expectancy_r":1.31
            }

    engine = ConfidenceCalibrator(MockReplay())
    result = engine.calibrate(
        {
            "pair":"FET/USD",
            "entry_style":"EXPANSION",
            "confidence":90,
        },
        {
            "market_mode":"EXPANSION",
        }
    )

    from pprint import pprint
    pprint(result)
