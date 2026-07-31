"""Snapshot test for the committed OpenAPI contract."""

import json
from pathlib import Path

from src.api.app import create_app
from src.exporters.openapi_json_exporter import (
    OpenApiJsonExporter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_FILE = (
    PROJECT_ROOT
    / "contracts"
    / "openapi.json"
)


def test_committed_contract_matches_application() -> None:
    committed_contract = json.loads(
        CONTRACT_FILE.read_text(
            encoding="utf-8"
        )
    )

    generated_contract = (
        OpenApiJsonExporter().to_dict(
            create_app()
        )
    )

    assert (
        committed_contract
        == generated_contract
    )