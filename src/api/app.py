"""FastAPI application for Pro Vision Engine."""

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException

from src.exporters.coupon_json_exporter import (
    CouponJsonExporter,
)
from src.services.demo_coupon_catalog import (
    DemoCouponCatalog,
    DemoCouponNotFoundError,
)


API_VERSION = "0.1.0-alpha"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COUPON_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def create_app(
    catalog: DemoCouponCatalog | None = None,
    exporter: CouponJsonExporter | None = None,
) -> FastAPI:
    """Create and configure the Pro Vision Engine API."""

    resolved_catalog = (
        catalog
        or DemoCouponCatalog(
            DEFAULT_COUPON_DIRECTORY
        )
    )
    resolved_exporter = (
        exporter
        or CouponJsonExporter()
    )

    application = FastAPI(
        title="Pro Vision Engine API",
        version=API_VERSION,
        description=(
            "Football pool coupon import, validation "
            "and analysis API for Project 13."
        ),
    )

    @application.get(
        "/api/v1/health",
        tags=["System"],
        summary="Check API health",
    )
    def get_health() -> dict[str, str]:
        """Return the current API health status."""

        return {
            "status": "ok",
            "service": "pro-vision-engine",
            "version": API_VERSION,
        }

    @application.get(
        "/api/v1/coupons",
        tags=["Coupons"],
        summary="List available demo coupons",
    )
    def list_coupons() -> dict[str, Any]:
        """Return all available demonstration coupon types."""

        game_types = list(
            resolved_catalog.available_game_types
        )

        return {
            "game_types": game_types,
            "count": len(game_types),
        }

    @application.get(
        "/api/v1/coupons/{game_type}",
        tags=["Coupons"],
        summary="Get one validated demo coupon",
    )
    def get_coupon(
        game_type: str,
    ) -> dict[str, Any]:
        """Return one imported and validated coupon."""

        try:
            coupon = resolved_catalog.load(
                game_type
            )
        except DemoCouponNotFoundError as error:
            raise HTTPException(
                status_code=404,
                detail=str(error),
            ) from error

        return resolved_exporter.to_dict(
            coupon
        )

    return application


app = create_app()