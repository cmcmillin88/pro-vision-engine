"""Request and response schemas for the Pro Vision Engine API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Response returned by the health endpoint."""

    status: str
    service: str
    version: str


class CouponListResponse(BaseModel):
    """Response containing available coupon game types."""

    game_types: list[str]
    count: int = Field(ge=0)


class CouponMetadataResponse(BaseModel):
    """Metadata describing one imported coupon."""

    id: str | None
    game_type: str
    game_type_display: str
    source: str
    source_display: str
    deadline: datetime | None
    imported_at: datetime
    match_count: int = Field(ge=0)
    expected_match_count: int | None = Field(
        default=None,
        ge=0,
    )


class MatchResponse(BaseModel):
    """API representation of one football match."""

    number: int = Field(ge=1)
    home_team: str
    away_team: str
    competition: str | None
    kickoff: datetime | None
    status: str


class CouponResponse(BaseModel):
    """Complete versioned coupon response."""

    schema_version: str
    coupon: CouponMetadataResponse
    matches: list[MatchResponse]


class CouponAnalysisRunRequest(BaseModel):
    """Request containing one practical coupon-analysis document."""

    model_config = ConfigDict(
        extra="forbid",
    )

    analysis_document: dict[str, Any]


class CouponAnalysisRunResponse(BaseModel):
    """Versioned practical coupon-analysis result envelope."""

    result: dict[str, Any]


class CouponReductionRunRequest(BaseModel):
    """Request containing analysis and reduction configuration data."""

    model_config = ConfigDict(
        extra="forbid",
    )

    analysis_document: dict[str, Any]
    reduction_configuration: dict[str, Any]


class CouponReductionRunResponse(BaseModel):
    """Versioned practical coupon-reduction result envelope."""

    result: dict[str, Any]


class ErrorResponse(BaseModel):
    """Standard API error response."""

    detail: str