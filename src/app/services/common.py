"""Shared service helpers: time context, rounding, KPI builder, time-query validation."""
from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional

from .. import config

_ISO_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?$")


class TimeContext:
    """Validated selected-period + snapshot window (TIME_SEMANTICS.md)."""

    def __init__(self, period_start: date, period_end: date, as_of: datetime):
        self.period_start = period_start
        self.period_end = period_end
        self.as_of = as_of

    @property
    def as_of_month(self) -> str:
        return self.as_of.strftime("%Y-%m")

    @property
    def as_of_date_str(self) -> str:
        return self.as_of.strftime("%Y-%m-%d")

    def iso(self) -> tuple[str, str, str]:
        return (
            self.period_start.isoformat(),
            self.period_end.isoformat(),
            self.as_of.isoformat(),
        )


def default_context() -> TimeContext:
    return TimeContext(config.DATASET_PERIOD_START, config.DATASET_PERIOD_END, config.DATASET_AS_OF)


def resolve_time_context(
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    as_of: Optional[str] = None,
) -> TimeContext:
    """Build and validate a TimeContext from query parameters.

    Raises ValueError with a user-facing message (routers map to HTTP 422). Dates outside
    the supported synthetic dataset are rejected explicitly — never silently clamped.
    """
    ps = period_start or config.DATASET_PERIOD_START
    pe = period_end or config.DATASET_PERIOD_END

    # independent bounds check first (each date must lie inside the prototype dataset)
    if (
        ps < config.DATASET_PERIOD_START
        or pe > config.DATASET_PERIOD_END
        or ps > config.DATASET_PERIOD_END
        or pe < config.DATASET_PERIOD_START
    ):
        raise ValueError(
            "Requested period is outside the supported synthetic dataset "
            f"({config.DATASET_PERIOD_START.isoformat()}..{config.DATASET_PERIOD_END.isoformat()})."
        )
    if ps > pe:
        raise ValueError("period_start must be <= period_end.")

    if as_of is None:
        as_of_dt = config.DATASET_AS_OF
    else:
        if not _ISO_DATETIME_RE.match(as_of):
            raise ValueError("as_of must be an ISO datetime, e.g. 2025-12-31T18:00:00.")
        try:
            as_of_dt = datetime.fromisoformat(as_of)
        except ValueError as exc:  # pragma: no cover - regex already guards
            raise ValueError("as_of must be a valid ISO datetime.") from exc

    if as_of_dt > config.DATASET_AS_OF:
        raise ValueError(
            f"as_of is beyond the dataset snapshot ({config.DATASET_AS_OF.isoformat()})."
        )
    if as_of_dt.date() < ps:
        raise ValueError("as_of date must not be earlier than period_start.")

    return TimeContext(ps, pe, as_of_dt)


# --------------------------------------------------------------------------- rounding


def r1(v: float) -> float:
    return round(v, 1)


def r2(v: float) -> float:
    return round(v, 2)


def r3(v: float) -> float:
    return round(v, 3)


def pct(numerator: float, denominator: float) -> float:
    """Percentage with 2 decimals; 0.0 when denominator is zero. Never NaN/Infinity."""
    return round(numerator * 100.0 / denominator, 2) if denominator else 0.0


def downgrade_rate(metrics: list[dict], processed: float) -> float:
    """Weighted downgrade rate across batches (approved metric). Shared by the report
    service and the analyst tools — one deterministic source."""
    downgraded_t = sum(m["downgrade_rate"] * m["processed_weight_t"] / 100.0 for m in metrics)
    return pct(downgraded_t, processed)


# --------------------------------------------------------------------------- KPI builder


def build_meta(ctx: TimeContext) -> dict:
    ps, pe, as_of = ctx.iso()
    return {
        "dataset_type": "synthetic_prototype",
        "currency": "AUD",
        "weight_unit": "t",
        "period_start": ps,
        "period_end": pe,
        "as_of": as_of,
        "seed": config.DATASET_SEED,
        "prototype": True,
    }


def make_kpi(
    kpi_id: str,
    label: str,
    value: float,
    unit: str,
    basis: str,
    description: str,
    status: str = "neutral",
) -> dict:
    return {
        "id": kpi_id,
        "label": label,
        "value": value,
        "unit": unit,
        "basis": basis,
        "status": status,
        "description": description,
        "prototype": True,
        "comparison_value": None,
        "change_absolute": None,
        "change_percent": None,
        "trend": None,
    }
