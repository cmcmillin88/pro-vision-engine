"""OpenAPI JSON exporter for the Pro Vision Engine API."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from fastapi import FastAPI


class OpenApiJsonExporter:
    """Exports a FastAPI OpenAPI contract as JSON."""

    def to_dict(
        self,
        application: FastAPI,
    ) -> dict[str, Any]:
        """Return an independent copy of the OpenAPI schema."""

        self._validate_application(
            application
        )

        schema = application.openapi()

        return deepcopy(schema)

    def to_json(
        self,
        application: FastAPI,
        *,
        indent: int | None = 2,
    ) -> str:
        """Serialize the OpenAPI schema as deterministic JSON."""

        payload = self.to_dict(
            application
        )

        return json.dumps(
            payload,
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )

    def write(
        self,
        application: FastAPI,
        destination: str | Path,
    ) -> Path:
        """Write the OpenAPI schema to a UTF-8 JSON file."""

        destination_path = Path(
            destination
        )

        destination_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        json_text = self.to_json(
            application
        )

        destination_path.write_text(
            f"{json_text}\n",
            encoding="utf-8",
        )

        return destination_path

    @staticmethod
    def _validate_application(
        application: FastAPI,
    ) -> None:
        """Ensure that a FastAPI application was supplied."""

        if not isinstance(
            application,
            FastAPI,
        ):
            raise TypeError(
                "OpenApiJsonExporter requires "
                "a FastAPI application."
            )