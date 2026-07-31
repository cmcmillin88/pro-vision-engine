"""FastAPI application for Pro Vision Engine."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import (
    CouponListResponse,
    CouponResponse,
    ErrorResponse,
    HealthResponse,
)
from src.api.settings import ApiSettings
from src.exporters.coupon_json_exporter import (
    CouponJsonExporter,
)
from src.services.demo_coupon_catalog import (
    DemoCouponCatalog,
    DemoCouponNotFoundError,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COUPON_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def create_app(
    catalog: DemoCouponCatalog | None = None,
    exporter: CouponJsonExporter | None = None,
    settings: ApiSettings | None = None,
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
    resolved_settings = (
        settings
        or ApiSettings()
    )

    application = FastAPI(
        title=resolved_settings.title,
        version=resolved_settings.version,
        description=resolved_settings.description,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(
            resolved_settings.allowed_origins
        ),
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @application.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Check API health",
    )
    def get_health() -> HealthResponse:
        """Return the current API health status."""

        return HealthResponse(
            status="ok",
            service=resolved_settings.service_name,
            version=resolved_settings.version,
        )

    @application.get(
        "/api/v1/coupons",
        response_model=CouponListResponse,
        tags=["Coupons"],
        summary="List available demo coupons",
    )
    def list_coupons() -> CouponListResponse:
        """Return all available demonstration coupon types."""

        game_types = list(
            resolved_catalog.available_game_types
        )

        return CouponListResponse(
            game_types=game_types,
            count=len(game_types),
        )

    @application.get(
        "/api/v1/coupons/{game_type}",
        response_model=CouponResponse,
        responses={
            404: {
                "model": ErrorResponse,
                "description": (
                    "The requested demonstration "
                    "coupon does not exist."
                ),
            }
        },
        tags=["Coupons"],
        summary="Get one validated demo coupon",
    )
    def get_coupon(
        game_type: str,
    ) -> CouponResponse:
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

        payload = resolved_exporter.to_dict(
            coupon
        )

        return CouponResponse.model_validate(
            payload
        )

    return application


app = create_app()