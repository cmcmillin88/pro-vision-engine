"""Snapshot test for generated TypeScript contracts."""

import json
from pathlib import Path

from src.exporters.typescript_contract_exporter import (
    TypeScriptContractExporter,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_FILE = (
    PROJECT_ROOT
    / "contracts"
    / "openapi.json"
)
TYPESCRIPT_DIRECTORY = (
    PROJECT_ROOT
    / "contracts"
    / "typescript"
)


def test_committed_typescript_contract_matches_openapi() -> None:
    openapi_document = json.loads(
        OPENAPI_FILE.read_text(
            encoding="utf-8"
        )
    )
    exporter = TypeScriptContractExporter()

    expected_files = {
        "api-types.ts": (
            exporter.types_to_string(
                openapi_document
            )
        ),
        "api-client.ts": (
            exporter.client_to_string()
        ),
        "index.ts": (
            exporter.index_to_string()
        ),
    }

    for (
        filename,
        expected_content,
    ) in expected_files.items():
        committed_content = (
            TYPESCRIPT_DIRECTORY
            / filename
        ).read_text(
            encoding="utf-8"
        )

        assert (
            committed_content
            == expected_content
        )