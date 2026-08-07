from __future__ import annotations

"""
A+ Radar - Replay Engine
========================

Phase 4 of the Radar architecture.

Purpose
-------
The Market Engine answers:
    "Should I be trading right now?"

The Pair Engine answers:
    "Which pairs deserve my attention?"

The Entry Engine answers:
    "Is this pair actually ready to enter right now?"

The Replay Engine answers:
    "What happened after Radar made that decision?"

This module gives Radar durable memory.

Core responsibilities
---------------------
1. Record every evaluated setup.
2. Preserve the exact Market / Pair / Entry state at signal time.
3. Track outcome, exit price, MFE and MAE.
4. Calculate realized R-multiple and return %.
5. Produce historical performance summaries.
6. Support later Confidence Calibration and Radar AI.

Storage
-------
SQLite is used by default because it is:
- durable
- local
- queryable
- lightweight
- easy to move to a hosted DB later

Default database:
    radar_replay.db

No external dependencies are required.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


SCHEMA_VERSION = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _num(v: Any, default: Optional[float] = 0.0) -> Optional[float]:
    try:
        return default if v is None else float(v)
    except (TypeError, ValueError):
        return default


def _text(v: Any) -> str:
    return str(v or "").strip()


def _upper(v: Any) -> str:
    return _text(v).upper()


def _json_dumps(value: Any) -> str:
    return json.dumps(
        value,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )


def _json_loads(value: Any, default: Any) -> Any:
    if value in (None, ""):
        return default

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    out = dict(row)

    for field in (
        "market_state_json",
        "pair_state_json",
        "entry_state_json",
        "tags_json",
        "notes_json",
    ):
        if field in out:
            key = field.replace("_json", "")
            default = [] if field in {"tags_json", "notes_json"} else {}
            out[key] = _json_loads(out.pop(field), default)

    return out


def _round(v: Optional[float], digits: int = 4) -> Optional[float]:
    return round(v, digits) if v is not None else None


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

class ReplayEngine:
    """
    Durable replay database for Radar signals.

    Example
    -------
    replay = ReplayEngine("radar_replay.db")

    signal_id = replay.record_signal(
        pair_state=pair_row,
        market_state=market_state,
        entry_state=entry_result,
    )

    replay.update_market_path(
        signal_id,
        high_price=1.28,
        low_price=1.23,
        current_price=1.27,
    )

    replay.close_signal(
        signal_id,
        exit_price=1.29,
        exit_reason="target",
    )
    """

    def __init__(self, db_path: str = "radar_replay.db") -> None:
        self.db_path = str(Path(db_path))
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    signal_id TEXT PRIMARY KEY,

                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    closed_at TEXT,

                    pair TEXT NOT NULL,
                    sector TEXT,

                    decision TEXT,
                    entry_style TEXT,

                    market_mode TEXT,
                    market_bias TEXT,
                    recommended_mode TEXT,

                    pair_rank INTEGER,
                    pair_score REAL,
                    confidence REAL,
                    trigger_score REAL,

                    entry_price REAL,
                    stop_price REAL,
                    target_1 REAL,
                    target_2 REAL,

                    initial_risk REAL,
                    initial_risk_pct REAL,

                    status TEXT NOT NULL DEFAULT 'OPEN',
                    outcome TEXT,

                    exit_price REAL,
                    exit_reason TEXT,

                    highest_price REAL,
                    lowest_price REAL,

                    mfe_pct REAL,
                    mae_pct REAL,
                    mfe_r REAL,
                    mae_r REAL,

                    return_pct REAL,
                    realized_r REAL,

                    bars_observed INTEGER DEFAULT 0,
                    minutes_observed REAL DEFAULT 0,

                    screenshot_ref TEXT,

                    market_state_json TEXT NOT NULL,
                    pair_state_json TEXT NOT NULL,
                    entry_state_json TEXT NOT NULL,

                    tags_json TEXT NOT NULL DEFAULT '[]',
                    notes_json TEXT NOT NULL DEFAULT '[]'
                )
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_signals_pair
                ON signals(pair)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_signals_created
                ON signals(created_at)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_signals_mode
                ON signals(market_mode)
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_signals_status
                ON signals(status)
                """
            )

            conn.execute(
                """
                INSERT OR REPLACE INTO metadata(key, value)
                VALUES('schema_version', ?)
                """,
                (str(SCHEMA_VERSION),),
            )

            conn.commit()

    # -----------------------------------------------------------------------
    # Signal creation
    # -----------------------------------------------------------------------

    def record_signal(
        self,
        pair_state: Dict[str, Any],
        market_state: Dict[str, Any],
        entry_state: Dict[str, Any],
        *,
        screenshot_ref: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        notes: Optional[Iterable[str]] = None,
        signal_id: Optional[str] = None,
    ) -> str:
        """
        Save the complete state of one Radar decision.

        Recommended usage:
            Record every Entry Engine result, not only ENTER signals.

        That gives Phase 6 enough data to compare:
            ENTER vs WAIT vs SKIP vs CHASE
        """

        sid = signal_id or uuid.uuid4().hex
        now = _utc_now()

        pair = (
            pair_state.get("pair")
            or pair_state.get("symbol")
            or entry_state.get("pair")
            or "UNKNOWN"
        )

        sector = pair_state.get("sector")
        decision = _upper(entry_state.get("decision"))
        entry_style = _upper(entry_state.get("entry_style"))

        entry_price = _num(
            entry_state.get("entry"),
            _num(pair_state.get("price"), None),
        )

        stop_price = _num(entry_state.get("stop"), None)
        target_1 = _num(entry_state.get("target_1"), None)
        target_2 = _num(entry_state.get("target_2"), None)

        initial_risk = None

        if (
            entry_price is not None
            and stop_price is not None
            and entry_price > stop_price
        ):
            initial_risk = entry_price - stop_price

        risk_pct = _num(entry_state.get("risk_pct"), None)

        pair_rank = pair_state.get("rank")
        pair_score = _num(
            entry_state.get("pair_score"),
            _num(pair_state.get("score"), None),
        )

        confidence = _num(entry_state.get("confidence"), None)
        trigger_score = _num(entry_state.get("trigger_score"), None)

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO signals (
                    signal_id,
                    created_at,
                    updated_at,

                    pair,
                    sector,

                    decision,
                    entry_style,

                    market_mode,
                    market_bias,
                    recommended_mode,

                    pair_rank,
                    pair_score,
                    confidence,
                    trigger_score,

                    entry_price,
                    stop_price,
                    target_1,
                    target_2,

                    initial_risk,
                    initial_risk_pct,

                    highest_price,
                    lowest_price,

                    screenshot_ref,

                    market_state_json,
                    pair_state_json,
                    entry_state_json,
                    tags_json,
                    notes_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    sid,
                    now,
                    now,

                    str(pair),
                    _text(sector),

                    decision,
                    entry_style,

                    _upper(market_state.get("market_mode")),
                    _upper(market_state.get("market_bias")),
                    _upper(market_state.get("recommended_mode")),

                    int(pair_rank) if pair_rank is not None else None,
                    pair_score,
                    confidence,
                    trigger_score,

                    entry_price,
                    stop_price,
                    target_1,
                    target_2,

                    initial_risk,
                    risk_pct,

                    entry_price,
                    entry_price,

                    screenshot_ref,

                    _json_dumps(market_state),
                    _json_dumps(pair_state),
                    _json_dumps(entry_state),
                    _json_dumps(list(tags or [])),
                    _json_dumps(list(notes or [])),
                ),
            )

            conn.commit()

        return sid

    # -----------------------------------------------------------------------
    # Path tracking
    # -----------------------------------------------------------------------

    def update_market_path(
        self,
        signal_id: str,
        *,
        current_price: Optional[float] = None,
        high_price: Optional[float] = None,
        low_price: Optional[float] = None,
        bars_added: int = 1,
        minutes_added: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Update MFE / MAE while a setup is being observed.

        MFE = Maximum Favorable Excursion
        MAE = Maximum Adverse Excursion

        For long signals:
            MFE measures highest move above entry.
            MAE measures deepest move below entry.
        """

        signal = self.get_signal(signal_id)

        if not signal:
            raise KeyError(f"Unknown signal_id: {signal_id}")

        entry = _num(signal.get("entry_price"), None)

        if entry is None or entry <= 0:
            return signal

        old_high = _num(signal.get("highest_price"), entry)
        old_low = _num(signal.get("lowest_price"), entry)

        candidates_high = [x for x in (old_high, high_price, current_price) if x is not None]
        candidates_low = [x for x in (old_low, low_price, current_price) if x is not None]

        highest = max(float(x) for x in candidates_high)
        lowest = min(float(x) for x in candidates_low)

        mfe_pct = ((highest - entry) / entry) * 100.0
        mae_pct = ((lowest - entry) / entry) * 100.0

        risk = _num(signal.get("initial_risk"), None)

        mfe_r = None
        mae_r = None

        if risk is not None and risk > 0:
            mfe_r = (highest - entry) / risk
            mae_r = (lowest - entry) / risk

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE signals
                SET
                    updated_at = ?,
                    highest_price = ?,
                    lowest_price = ?,
                    mfe_pct = ?,
                    mae_pct = ?,
                    mfe_r = ?,
                    mae_r = ?,
                    bars_observed = COALESCE(bars_observed, 0) + ?,
                    minutes_observed = COALESCE(minutes_observed, 0) + ?
                WHERE signal_id = ?
                """,
                (
                    _utc_now(),
                    highest,
                    lowest,
                    mfe_pct,
                    mae_pct,
                    mfe_r,
                    mae_r,
                    int(bars_added),
                    float(minutes_added),
                    signal_id,
                ),
            )

            conn.commit()

        return self.get_signal(signal_id) or {}

    # -----------------------------------------------------------------------
    # Signal resolution
    # -----------------------------------------------------------------------

    def close_signal(
        self,
        signal_id: str,
        *,
        exit_price: float,
        exit_reason: str = "",
        outcome: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Close a replay record and calculate realized performance.

        Outcome is inferred from realized R if not supplied:
            WIN      > +0.10R
            LOSS     < -0.10R
            BREAKEVEN otherwise
        """

        signal = self.get_signal(signal_id)

        if not signal:
            raise KeyError(f"Unknown signal_id: {signal_id}")

        entry = _num(signal.get("entry_price"), None)
        exit_p = _num(exit_price, None)

        if entry is None or entry <= 0 or exit_p is None:
            raise ValueError("A valid entry and exit price are required.")

        # Make sure final exit is included in MFE/MAE.
        self.update_market_path(
            signal_id,
            current_price=exit_p,
            bars_added=0,
            minutes_added=0,
        )

        signal = self.get_signal(signal_id) or signal

        return_pct = ((exit_p - entry) / entry) * 100.0

        risk = _num(signal.get("initial_risk"), None)

        realized_r = None

        if risk is not None and risk > 0:
            realized_r = (exit_p - entry) / risk

        if outcome:
            final_outcome = _upper(outcome)
        elif realized_r is not None:
            if realized_r > 0.10:
                final_outcome = "WIN"
            elif realized_r < -0.10:
                final_outcome = "LOSS"
            else:
                final_outcome = "BREAKEVEN"
        else:
            if return_pct > 0.05:
                final_outcome = "WIN"
            elif return_pct < -0.05:
                final_outcome = "LOSS"
            else:
                final_outcome = "BREAKEVEN"

        now = _utc_now()

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE signals
                SET
                    updated_at = ?,
                    closed_at = ?,
                    status = 'CLOSED',
                    outcome = ?,
                    exit_price = ?,
                    exit_reason = ?,
                    return_pct = ?,
                    realized_r = ?
                WHERE signal_id = ?
                """,
                (
                    now,
                    now,
                    final_outcome,
                    exit_p,
                    _text(exit_reason),
                    return_pct,
                    realized_r,
                    signal_id,
                ),
            )

            conn.commit()

        return self.get_signal(signal_id) or {}

    def expire_signal(
        self,
        signal_id: str,
        *,
        reason: str = "Signal expired before entry",
    ) -> Dict[str, Any]:
        """
        Mark a WAIT / untriggered setup as expired without fabricating a trade.
        """

        now = _utc_now()

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE signals
                SET
                    updated_at = ?,
                    closed_at = ?,
                    status = 'EXPIRED',
                    outcome = 'NO TRADE',
                    exit_reason = ?
                WHERE signal_id = ?
                """,
                (
                    now,
                    now,
                    _text(reason),
                    signal_id,
                ),
            )
            conn.commit()

        return self.get_signal(signal_id) or {}

    # -----------------------------------------------------------------------
    # Notes / tags
    # -----------------------------------------------------------------------

    def add_note(self, signal_id: str, note: str) -> Dict[str, Any]:
        signal = self.get_signal(signal_id)

        if not signal:
            raise KeyError(f"Unknown signal_id: {signal_id}")

        notes = list(signal.get("notes") or [])
        notes.append(
            {
                "timestamp": _utc_now(),
                "text": str(note),
            }
        )

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE signals
                SET notes_json = ?, updated_at = ?
                WHERE signal_id = ?
                """,
                (
                    _json_dumps(notes),
                    _utc_now(),
                    signal_id,
                ),
            )
            conn.commit()

        return self.get_signal(signal_id) or {}

    def add_tag(self, signal_id: str, tag: str) -> Dict[str, Any]:
        signal = self.get_signal(signal_id)

        if not signal:
            raise KeyError(f"Unknown signal_id: {signal_id}")

        tags = list(signal.get("tags") or [])

        clean = _upper(tag)

        if clean and clean not in tags:
            tags.append(clean)

        with self._connect() as conn:
            conn.execute(
                """
                UPDATE signals
                SET tags_json = ?, updated_at = ?
                WHERE signal_id = ?
                """,
                (
                    _json_dumps(tags),
                    _utc_now(),
                    signal_id,
                ),
            )
            conn.commit()

        return self.get_signal(signal_id) or {}

    # -----------------------------------------------------------------------
    # Queries
    # -----------------------------------------------------------------------

    def get_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT *
                FROM signals
                WHERE signal_id = ?
                """,
                (signal_id,),
            ).fetchone()

        return _row_to_dict(row) if row else None

    def list_signals(
        self,
        *,
        pair: Optional[str] = None,
        market_mode: Optional[str] = None,
        decision: Optional[str] = None,
        outcome: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:

        where = []
        args: List[Any] = []

        filters = {
            "pair": pair,
            "market_mode": market_mode,
            "decision": decision,
            "outcome": outcome,
            "status": status,
        }

        for key, value in filters.items():
            if value is not None:
                where.append(f"{key} = ?")
                args.append(_upper(value) if key != "pair" else str(value))

        sql = "SELECT * FROM signals"

        if where:
            sql += " WHERE " + " AND ".join(where)

        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(max(1, int(limit)))

        with self._connect() as conn:
            rows = conn.execute(sql, args).fetchall()

        return [_row_to_dict(row) for row in rows]

    def open_signals(self) -> List[Dict[str, Any]]:
        return self.list_signals(
            status="OPEN",
            limit=10_000,
        )

    # -----------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------

    def performance_summary(
        self,
        *,
        pair: Optional[str] = None,
        market_mode: Optional[str] = None,
        entry_style: Optional[str] = None,
        decision: str = "ENTER",
    ) -> Dict[str, Any]:
        """
        Return historical performance for completed trades.

        Phase 6 will later use these same fields for calibration.
        """

        where = [
            "status = 'CLOSED'",
            "decision = ?",
        ]

        args: List[Any] = [_upper(decision)]

        if pair is not None:
            where.append("pair = ?")
            args.append(str(pair))

        if market_mode is not None:
            where.append("market_mode = ?")
            args.append(_upper(market_mode))

        if entry_style is not None:
            where.append("entry_style = ?")
            args.append(_upper(entry_style))

        sql = f"""
            SELECT *
            FROM signals
            WHERE {' AND '.join(where)}
            ORDER BY created_at ASC
        """

        with self._connect() as conn:
            rows = conn.execute(sql, args).fetchall()

        trades = [_row_to_dict(row) for row in rows]

        if not trades:
            return {
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "breakeven": 0,
                "win_rate": None,
                "avg_return_pct": None,
                "avg_r": None,
                "expectancy_r": None,
                "avg_mfe_pct": None,
                "avg_mae_pct": None,
                "profit_factor_r": None,
                "best_trade_r": None,
                "worst_trade_r": None,
            }

        wins = [t for t in trades if _upper(t.get("outcome")) == "WIN"]
        losses = [t for t in trades if _upper(t.get("outcome")) == "LOSS"]
        breakeven = [
            t for t in trades
            if _upper(t.get("outcome")) == "BREAKEVEN"
        ]

        returns = [
            _num(t.get("return_pct"), None)
            for t in trades
            if t.get("return_pct") is not None
        ]

        rs = [
            _num(t.get("realized_r"), None)
            for t in trades
            if t.get("realized_r") is not None
        ]

        mfes = [
            _num(t.get("mfe_pct"), None)
            for t in trades
            if t.get("mfe_pct") is not None
        ]

        maes = [
            _num(t.get("mae_pct"), None)
            for t in trades
            if t.get("mae_pct") is not None
        ]

        avg_return = (
            sum(returns) / len(returns)
            if returns else None
        )

        avg_r = (
            sum(rs) / len(rs)
            if rs else None
        )

        # Expectancy per trade in R.
        expectancy_r = avg_r

        gross_win_r = sum(r for r in rs if r > 0)
        gross_loss_r = abs(sum(r for r in rs if r < 0))

        if gross_loss_r > 0:
            profit_factor = gross_win_r / gross_loss_r
        elif gross_win_r > 0:
            profit_factor = float("inf")
        else:
            profit_factor = None

        resolved = len(wins) + len(losses)

        win_rate = (
            len(wins) / resolved * 100.0
            if resolved else None
        )

        return {
            "trades": len(trades),
            "wins": len(wins),
            "losses": len(losses),
            "breakeven": len(breakeven),

            "win_rate": _round(win_rate, 2),

            "avg_return_pct": _round(avg_return, 3),
            "avg_r": _round(avg_r, 3),
            "expectancy_r": _round(expectancy_r, 3),

            "avg_mfe_pct": _round(
                sum(mfes) / len(mfes) if mfes else None,
                3,
            ),

            "avg_mae_pct": _round(
                sum(maes) / len(maes) if maes else None,
                3,
            ),

            "profit_factor_r": (
                "INF"
                if profit_factor == float("inf")
                else _round(profit_factor, 3)
            ),

            "best_trade_r": _round(max(rs), 3) if rs else None,
            "worst_trade_r": _round(min(rs), 3) if rs else None,
        }

    def performance_by_market_mode(self) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            modes = conn.execute(
                """
                SELECT DISTINCT market_mode
                FROM signals
                WHERE
                    status = 'CLOSED'
                    AND decision = 'ENTER'
                    AND market_mode IS NOT NULL
                    AND market_mode != ''
                ORDER BY market_mode
                """
            ).fetchall()

        results = []

        for row in modes:
            mode = row["market_mode"]

            stats = self.performance_summary(
                market_mode=mode,
            )

            results.append(
                {
                    "market_mode": mode,
                    **stats,
                }
            )

        results.sort(
            key=lambda x: (
                x["expectancy_r"]
                if isinstance(x.get("expectancy_r"), (int, float))
                else -999
            ),
            reverse=True,
        )

        return results

    def performance_by_pair(
        self,
        min_trades: int = 1,
    ) -> List[Dict[str, Any]]:

        with self._connect() as conn:
            pairs = conn.execute(
                """
                SELECT DISTINCT pair
                FROM signals
                WHERE
                    status = 'CLOSED'
                    AND decision = 'ENTER'
                ORDER BY pair
                """
            ).fetchall()

        results = []

        for row in pairs:
            pair = row["pair"]

            stats = self.performance_summary(
                pair=pair,
            )

            if stats["trades"] >= min_trades:
                results.append(
                    {
                        "pair": pair,
                        **stats,
                    }
                )

        results.sort(
            key=lambda x: (
                x["expectancy_r"]
                if isinstance(x.get("expectancy_r"), (int, float))
                else -999
            ),
            reverse=True,
        )

        return results

    # -----------------------------------------------------------------------
    # Replay view
    # -----------------------------------------------------------------------

    def replay_signal(self, signal_id: str) -> Dict[str, Any]:
        """
        Return a UI-ready replay package for one historical setup.
        """

        signal = self.get_signal(signal_id)

        if not signal:
            raise KeyError(f"Unknown signal_id: {signal_id}")

        return {
            "signal_id": signal["signal_id"],
            "pair": signal["pair"],
            "created_at": signal["created_at"],
            "closed_at": signal["closed_at"],

            "decision": signal["decision"],
            "entry_style": signal["entry_style"],

            "market": {
                "mode": signal["market_mode"],
                "bias": signal["market_bias"],
                "recommended_mode": signal["recommended_mode"],
                "state": signal["market_state"],
            },

            "pair_state": signal["pair_state"],
            "entry_state": signal["entry_state"],

            "trade": {
                "entry": signal["entry_price"],
                "stop": signal["stop_price"],
                "target_1": signal["target_1"],
                "target_2": signal["target_2"],
                "exit": signal["exit_price"],
                "exit_reason": signal["exit_reason"],
            },

            "result": {
                "status": signal["status"],
                "outcome": signal["outcome"],
                "return_pct": signal["return_pct"],
                "realized_r": signal["realized_r"],
                "mfe_pct": signal["mfe_pct"],
                "mae_pct": signal["mae_pct"],
                "mfe_r": signal["mfe_r"],
                "mae_r": signal["mae_r"],
            },

            "screenshot_ref": signal["screenshot_ref"],
            "tags": signal["tags"],
            "notes": signal["notes"],
        }


# ---------------------------------------------------------------------------
# Functional convenience API
# ---------------------------------------------------------------------------

def create_replay_engine(
    db_path: str = "radar_replay.db",
) -> ReplayEngine:
    return ReplayEngine(db_path)


def record_replay(
    pair_state: Dict[str, Any],
    market_state: Dict[str, Any],
    entry_state: Dict[str, Any],
    *,
    db_path: str = "radar_replay.db",
) -> str:
    """
    One-call convenience function for Radar's main loop.
    """
    engine = ReplayEngine(db_path)

    return engine.record_signal(
        pair_state=pair_state,
        market_state=market_state,
        entry_state=entry_state,
    )


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from pprint import pprint
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        db = str(Path(tmp) / "replay_test.db")

        replay = ReplayEngine(db)

        market_state = {
            "market_mode": "EXPANSION",
            "market_bias": "BULLISH",
            "recommended_mode": "Expansion",
            "market_health": 82,
        }

        pair_state = {
            "pair": "FET/USD",
            "sector": "AI",
            "rank": 1,
            "score": 88.92,
            "price": 1.25,
            "rsi_1m": 61,
            "rsi_5m": 64,
            "vwap": "HOLDING",
        }

        entry_state = {
            "pair": "FET/USD",
            "decision": "ENTER",
            "entry_style": "EXPANSION",
            "confidence": 92,
            "trigger_score": 88,
            "pair_score": 88.92,
            "entry": 1.25,
            "stop": 1.24,
            "target_1": 1.275,
            "target_2": 1.29,
            "risk_pct": 0.8,
        }

        signal_id = replay.record_signal(
            pair_state,
            market_state,
            entry_state,
        )

        replay.update_market_path(
            signal_id,
            high_price=1.282,
            low_price=1.246,
            minutes_added=5,
        )

        replay.close_signal(
            signal_id,
            exit_price=1.278,
            exit_reason="Target / manual exit",
        )

        print("Replay:")
        pprint(replay.replay_signal(signal_id))

        print("\nStats:")
        pprint(replay.performance_summary())
