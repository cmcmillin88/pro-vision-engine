"""Shared immutable helpers for practical coupon-reduction tests."""

from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from src.models.coupon_reduction_run import CouponReductionRun
from src.services.coupon_reduction_file_runner import (
    CouponReductionFileRunner,
)


ANALYSIS_PATH = Path("examples/topptipset-analysis-input.json")
REDUCTION_PATH = Path("examples/topptipset-reduction-config.json")
FIXED_ANALYZED_AT = datetime(
    2026,
    8,
    1,
    0,
    15,
    tzinfo=timezone.utc,
)
FIXED_REDUCED_AT = datetime(
    2026,
    8,
    1,
    0,
    20,
    tzinfo=timezone.utc,
)


@lru_cache(maxsize=1)
def create_reduction_run() -> CouponReductionRun:
    """Run the complete example once and reuse its immutable result."""

    return CouponReductionFileRunner().run_files(
        ANALYSIS_PATH,
        REDUCTION_PATH,
        analyzed_at=FIXED_ANALYZED_AT,
        reduced_at=FIXED_REDUCED_AT,
    )