"""FastAPI application for Pro Vision Engine."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.api.schemas import (
    CouponAnalysisRunRequest,
    CouponAnalysisRunResponse,
    CouponListResponse,
    CouponReductionRunRequest,
    CouponReductionRunResponse,
    CouponResponse,
    ErrorResponse,
    HealthResponse,
)
from src.api.settings import ApiSettings
from src.exporters.coupon_json_exporter import (
    CouponJsonExporter,
)
from src.services.coupon_catalog_protocol import (
    CouponCatalog,
    CouponNotFoundError,
)
from src.services.coupon_source_registry import (
    CouponSourceRegistry,
)
from src.services.demo_coupon_catalog import (
    DemoCouponCatalog,
)
from src.services.practical_run_api_service import (
    PracticalRunApiService,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COUPON_DIRECTORY = (
    PROJECT_ROOT
    / "examples"
    / "svenska_spel"
)


def create_app(
    catalog: CouponCatalog | None = None,
    registry: CouponSourceRegistry | None = None,
    exporter: CouponJsonExporter | None = None,
    practical_service: PracticalRunApiService | None = None,
    settings: ApiSettings | None = None,
) -> FastAPI:
    """Create and configure the Pro Vision Engine API."""

    resolved_registry = _resolve_registry(
        catalog=catalog,
        registry=registry,
    )
    resolved_exporter = (
        exporter
        or CouponJsonExporter()
    )
    resolved_practical_service = (
        practical_service
        or PracticalRunApiService()
    )
    resolved_settings = (
        settings
        or ApiSettings()
    )

    if not isinstance(
        resolved_practical_service,
        PracticalRunApiService,
    ):
        raise TypeError(
            "practical_service must be a "
            "PracticalRunApiService or None."
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
        allow_methods=[
            "GET",
            "POST",
        ],
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
            resolved_registry.available_game_types()
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
            coupon = resolved_registry.load(
                game_type
            )
        except CouponNotFoundError as error:
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

    @application.post(
        "/api/v1/analysis-runs",
        response_model=CouponAnalysisRunResponse,
        responses={
            422: {
                "model": ErrorResponse,
                "description": (
                    "The supplied analysis document "
                    "failed strict domain validation."
                ),
            }
        },
        tags=["Analysis Runs"],
        summary="Run complete coupon analysis",
    )
    def create_analysis_run(
        request: CouponAnalysisRunRequest,
    ) -> CouponAnalysisRunResponse:
        """Run the complete analysis pipeline from JSON data."""

        try:
            result = resolved_practical_service.create_analysis_run(
                request.analysis_document
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

        return CouponAnalysisRunResponse(
            result=result
        )

    @application.post(
        "/api/v1/reduction-runs",
        response_model=CouponReductionRunResponse,
        responses={
            422: {
                "model": ErrorResponse,
                "description": (
                    "The supplied analysis or reduction "
                    "document failed strict domain validation."
                ),
            }
        },
        tags=["Reduction Runs"],
        summary="Run complete coupon analysis and reduction",
    )
    def create_reduction_run(
        request: CouponReductionRunRequest,
    ) -> CouponReductionRunResponse:
        """Run analysis and reduction from two JSON documents."""

        try:
            result = resolved_practical_service.create_reduction_run(
                request.analysis_document,
                request.reduction_configuration,
            )
        except (
            TypeError,
            ValueError,
        ) as error:
            raise HTTPException(
                status_code=422,
                detail=str(error),
            ) from error

        return CouponReductionRunResponse(
            result=result
        )

    return application


def _resolve_registry(
    *,
    catalog: CouponCatalog | None,
    registry: CouponSourceRegistry | None,
) -> CouponSourceRegistry:
    """Resolve the source registry used by the API."""

    if (
        catalog is not None
        and registry is not None
    ):
        raise ValueError(
            "Provide either catalog or registry, "
            "not both."
        )

    if registry is not None:
        return registry

    resolved_catalog = (
        catalog
        or DemoCouponCatalog(
            DEFAULT_COUPON_DIRECTORY
        )
    )

    return CouponSourceRegistry(
        [resolved_catalog],
        default_source_name=(
            resolved_catalog.source_name
        ),
    )


app = create_app()