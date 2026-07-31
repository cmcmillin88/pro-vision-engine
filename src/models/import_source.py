"""Supported coupon import sources."""

from enum import Enum


class ImportSource(str, Enum):
    """Represents the source from which a coupon was imported."""

    MANUAL = "manual"
    TEXT_FILE = "text_file"
    SVENSKA_SPEL = "svenska_spel"

    @property
    def display_name(self) -> str:
        """Return a human-readable import source name."""

        names = {
            ImportSource.MANUAL: "Manual",
            ImportSource.TEXT_FILE: "Text file",
            ImportSource.SVENSKA_SPEL: "Svenska Spel",
        }

        return names[self]