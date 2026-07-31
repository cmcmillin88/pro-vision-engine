"""Shared fixtures for practical coupon-analysis JSON tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_PATH = (
    PROJECT_ROOT
    / "examples"
    / "topptipset-analysis-input.json"
)
SCHEMA_PATH = (
    PROJECT_ROOT
    / "contracts"
    / "coupon-analysis-input.schema.json"
)


def load_example_payload() -> dict[str, Any]:
    """Return a mutable deep copy of the official example payload."""

    return copy.deepcopy(
        json.loads(
            EXAMPLE_PATH.read_text(
                encoding="utf-8"
            )
        )
    )