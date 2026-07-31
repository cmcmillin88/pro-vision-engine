"""Common contract for Svenska Spel data clients."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from src.providers.svenska_spel.models import SvenskaSpelCouponData


@runtime_checkable
class SvenskaSpelClient(Protocol):
    """Defines how Svenska Spel coupon data is retrieved."""

    def fetch_coupon(
        self,
        source_reference: str | Path,
    ) -> SvenskaSpelCouponData:
        """Retrieve structured coupon data from Svenska Spel."""

        ...