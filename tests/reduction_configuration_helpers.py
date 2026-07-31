"""Shared helpers for practical reduction-configuration tests."""

import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path
from typing import Any

from src.models.coupon_analysis_run import CouponAnalysisRun
from src.models.reduction_configuration_document import (
    ReductionConfigurationDocument,
)
from src.importer.reduction_configuration_json_importer import (
    ReductionConfigurationJsonImporter,
)
from tests.coupon_analysis_run_helpers import (
    create_analysis_run,
)


EXAMPLE_PATH = Path(
    "examples/topptipset-reduction-config.json"
)
SCHEMA_PATH = Path(
    "contracts/reduction-configuration.schema.json"
)


def load_example_payload() -> dict[str, Any]:
    """Load a fresh mutable copy of the example configuration."""

    return json.loads(
        EXAMPLE_PATH.read_text(
            encoding="utf-8"
        )
    )


def create_full_payload(
    analysis_run: CouponAnalysisRun | None = None,
) -> dict[str, Any]:
    """Create all five condition groups inside the actual frame."""

    run = analysis_run or create_analysis_run()
    payload = load_example_payload()

    first = run.reduction_frame.allowed_for_match(1)[0].value
    second = run.reduction_frame.allowed_for_match(2)[0].value
    third = run.reduction_frame.allowed_for_match(3)[0].value

    payload["target"]["frame_pattern"] = (
        run.recommendation_pattern
    )
    payload["conditions"]["colors"] = [
        {
            "color": "red",
            "cells": [
                {
                    "match": 1,
                    "outcome": first,
                },
                {
                    "match": 2,
                    "outcome": second,
                },
            ],
            "min": 0,
            "max": 2,
        },
        {
            "color": "yellow",
            "cells": [
                {
                    "match": 3,
                    "outcome": third,
                }
            ],
            "min": 0,
            "max": 1,
        },
    ]
    payload["conditions"]["points"] = {
        "assignments": [
            {
                "match": 1,
                "outcome": first,
                "points": 5,
            },
            {
                "match": 2,
                "outcome": second,
                "points": 4,
            },
            {
                "match": 3,
                "outcome": third,
                "points": 3,
            },
        ],
        "min": 0,
        "max": 12,
    }

    return payload


def copy_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Return a deep mutable copy of one payload."""

    return deepcopy(
        payload
    )


@lru_cache(maxsize=1)
def create_configuration_document() -> ReductionConfigurationDocument:
    """Import and cache the immutable all-condition document."""

    run = create_analysis_run()

    return ReductionConfigurationJsonImporter().from_dict(
        create_full_payload(
            run
        ),
        run,
        source_name="test-reduction-config.json",
    )