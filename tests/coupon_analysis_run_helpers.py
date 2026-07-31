"""Shared immutable helpers for practical coupon-analysis run tests."""

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from src.models.coupon_analysis_run import CouponAnalysisRun
from src.services.coupon_analysis_file_runner import (
    CouponAnalysisFileRunner,
)


EXAMPLE_PATH = Path(
    "examples/topptipset-analysis-input.json"
)
FIXED_ANALYZED_AT = datetime(
    2026,
    8,
    1,
    0,
    15,
    tzinfo=timezone.utc,
)


@lru_cache(maxsize=1)
def create_analysis_run() -> CouponAnalysisRun:
    """Run the complete example once and reuse its immutable result."""

    return CouponAnalysisFileRunner().run_file(
        EXAMPLE_PATH,
        analyzed_at=FIXED_ANALYZED_AT,
    )