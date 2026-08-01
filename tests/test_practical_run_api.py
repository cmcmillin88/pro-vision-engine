"""Integration tests for practical analysis and reduction API routes."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.services.practical_run_api_service import (
    PracticalRunApiService,
)


ANALYSIS_PATH = Path(
    "examples/topptipset-analysis-input.json"
)
REDUCTION_PATH = Path(
    "examples/topptipset-reduction-config.json"
)


def load_json(path: Path) -> dict[str, object]:
    """Load one committed UTF-8 example document."""

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create one reusable API test client."""

    return TestClient(
        create_app()
    )


def test_analysis_run_endpoint_returns_success(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
        },
    )

    assert response.status_code == 200


def test_analysis_run_endpoint_returns_result_envelope(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
        },
    )

    payload = response.json()

    assert set(payload) == {
        "result",
    }
    assert payload["result"]["schema_version"] == (
        "p13-analysis-result-v1"
    )


def test_analysis_endpoint_returns_all_matches(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/analysis-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
        },
    )

    result = response.json()["result"]

    assert result["coupon"]["match_count"] == 8
    assert len(result["matches"]) == 8


def test_analysis_endpoint_preserves_unicode(
    client: TestClient,
) -> None:
    document = load_json(
        ANALYSIS_PATH
    )
    document["matches"][0]["home_team"] = "Malmö FF"

    response = client.post(
        "/api/v1/analysis-runs",
        json={
            "analysis_document": document,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["result"]["matches"][0]["home_team"]
        == "Malmö FF"
    )


def test_reduction_run_endpoint_returns_success(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/reduction-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
            "reduction_configuration": load_json(
                REDUCTION_PATH
            ),
        },
    )

    assert response.status_code == 200


def test_reduction_run_endpoint_returns_result_envelope(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/reduction-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
            "reduction_configuration": load_json(
                REDUCTION_PATH
            ),
        },
    )

    payload = response.json()

    assert set(payload) == {
        "result",
    }
    assert payload["result"]["schema_version"] == (
        "p13-reduction-result-v1"
    )


def test_reduction_endpoint_returns_consistent_counts(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/reduction-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
            "reduction_configuration": load_json(
                REDUCTION_PATH
            ),
        },
    )

    counts = response.json()["result"]["result"]["counts"]

    assert (
        counts["approved"]
        + counts["rejected"]
        == counts["original"]
    )


def test_reduction_endpoint_returns_approved_rows(
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/reduction-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
            "reduction_configuration": load_json(
                REDUCTION_PATH
            ),
        },
    )

    result = response.json()["result"]

    assert result["rows"]["approved_count"] == len(
        result["rows"]["approved"]
    )


def test_analysis_endpoint_rejects_unsupported_schema(
    client: TestClient,
) -> None:
    document = load_json(
        ANALYSIS_PATH
    )
    document["schema_version"] = "unsupported"

    response = client.post(
        "/api/v1/analysis-runs",
        json={
            "analysis_document": document,
        },
    )

    assert response.status_code == 422
    assert "Unsupported" in response.json()["detail"]


def test_reduction_endpoint_rejects_unsupported_schema(
    client: TestClient,
) -> None:
    configuration = load_json(
        REDUCTION_PATH
    )
    configuration["schema_version"] = "unsupported"

    response = client.post(
        "/api/v1/reduction-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
            "reduction_configuration": configuration,
        },
    )

    assert response.status_code == 422
    assert "Unsupported" in response.json()["detail"]


@pytest.mark.parametrize(
    "endpoint",
    (
        "/api/v1/analysis-runs",
        "/api/v1/reduction-runs",
    ),
)
def test_run_endpoints_reject_empty_requests(
    client: TestClient,
    endpoint: str,
) -> None:
    response = client.post(
        endpoint,
        json={},
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "endpoint",
    (
        "/api/v1/analysis-runs",
        "/api/v1/reduction-runs",
    ),
)
def test_run_endpoints_reject_extra_top_level_fields(
    client: TestClient,
    endpoint: str,
) -> None:
    request = {
        "analysis_document": load_json(
            ANALYSIS_PATH
        ),
        "unexpected": True,
    }

    if endpoint.endswith(
        "reduction-runs"
    ):
        request["reduction_configuration"] = load_json(
            REDUCTION_PATH
        )

    response = client.post(
        endpoint,
        json=request,
    )

    assert response.status_code == 422


def test_openapi_contains_analysis_run_endpoint(
    client: TestClient,
) -> None:
    schema = client.get(
        "/openapi.json"
    ).json()

    assert "post" in schema["paths"][
        "/api/v1/analysis-runs"
    ]


def test_openapi_contains_reduction_run_endpoint(
    client: TestClient,
) -> None:
    schema = client.get(
        "/openapi.json"
    ).json()

    assert "post" in schema["paths"][
        "/api/v1/reduction-runs"
    ]


@pytest.mark.parametrize(
    "schema_name",
    (
        "CouponAnalysisRunRequest",
        "CouponAnalysisRunResponse",
        "CouponReductionRunRequest",
        "CouponReductionRunResponse",
    ),
)
def test_openapi_contains_practical_run_schemas(
    client: TestClient,
    schema_name: str,
) -> None:
    schema = client.get(
        "/openapi.json"
    ).json()

    assert schema_name in schema[
        "components"
    ]["schemas"]


def test_cors_preflight_allows_post(
    client: TestClient,
) -> None:
    response = client.options(
        "/api/v1/analysis-runs",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert "POST" in response.headers[
        "access-control-allow-methods"
    ]


def test_existing_health_endpoint_remains_available(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/health"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_app_rejects_invalid_practical_service() -> None:
    with pytest.raises(
        TypeError,
        match="PracticalRunApiService",
    ):
        create_app(
            practical_service=object()  # type: ignore[arg-type]
        )


def test_app_accepts_explicit_practical_service() -> None:
    explicit_client = TestClient(
        create_app(
            practical_service=PracticalRunApiService()
        )
    )

    response = explicit_client.post(
        "/api/v1/analysis-runs",
        json={
            "analysis_document": load_json(
                ANALYSIS_PATH
            ),
        },
    )

    assert response.status_code == 200