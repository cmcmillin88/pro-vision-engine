"""Local JSON client for Svenska Spel coupon data."""

import json
from pathlib import Path
from typing import Any

from src.providers.svenska_spel.models import (
    SvenskaSpelCouponData,
)
from src.providers.svenska_spel.payload_parser import (
    SvenskaSpelPayloadError,
    SvenskaSpelPayloadParser,
)


class SvenskaSpelJsonClientError(ValueError):
    """Raised when local Svenska Spel JSON data is invalid."""


class SvenskaSpelJsonClient:
    """Reads Svenska Spel coupon data from a local JSON file."""

    def __init__(
        self,
        parser: SvenskaSpelPayloadParser | None = None,
    ) -> None:
        """Create the client with a shared payload parser."""

        self._parser = parser or SvenskaSpelPayloadParser()

    def fetch_coupon(
        self,
        source_reference: str | Path,
    ) -> SvenskaSpelCouponData:
        """Read and convert a local Svenska Spel JSON file."""

        path = Path(source_reference)
        raw_payload = self._read_json(path)

        try:
            return self._parser.parse(raw_payload)
        except SvenskaSpelPayloadError as error:
            raise SvenskaSpelJsonClientError(
                str(error)
            ) from error

    @staticmethod
    def _read_json(path: Path) -> Any:
        """Read and decode a JSON file."""

        try:
            with path.open(encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError as error:
            raise SvenskaSpelJsonClientError(
                f"Svenska Spel JSON file was not found: {path}"
            ) from error
        except json.JSONDecodeError as error:
            raise SvenskaSpelJsonClientError(
                f"Invalid JSON in file {path}: {error.msg}"
            ) from error
        except OSError as error:
            raise SvenskaSpelJsonClientError(
                f"Could not read Svenska Spel JSON file: {path}"
            ) from error