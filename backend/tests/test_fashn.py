from __future__ import annotations

import json
from typing import Any

from app.fashn import FashnClient, FashnConfig


class FakeResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_fashn_client_submits_product_to_model_and_polls_status() -> None:
    calls: list[dict[str, Any]] = []

    def fake_opener(request, timeout: float) -> FakeResponse:
        payload = json.loads(request.data.decode("utf-8")) if request.data else None
        calls.append(
            {
                "url": request.full_url,
                "method": request.get_method(),
                "payload": payload,
                "timeout": timeout,
            }
        )
        if request.full_url.endswith("/v1/run"):
            return FakeResponse({"id": "pred-1", "error": None})
        return FakeResponse(
            {
                "id": "pred-1",
                "status": "completed",
                "output": ["https://cdn.example.com/pred-1/output.jpg"],
                "error": None,
            }
        )

    client = FashnClient(
        FashnConfig(
            api_key="test-key",
            base_url="https://api.test",
            timeout_seconds=5,
            poll_interval_seconds=0,
        ),
        opener=fake_opener,
        sleeper=lambda _seconds: None,
    )

    result = client.generate_model_shot(
        garment_image="data:image/png;base64,abc123",
        quality_profile={
            "quality_tier": "premium",
            "generation_mode": "product-to-model-quality",
        },
        product_category="Bottoms",
    )

    assert result.generated_image_url == "https://cdn.example.com/pred-1/output.jpg"
    assert result.prediction_id == "pred-1"
    assert calls[0]["method"] == "POST"
    assert calls[0]["payload"]["model_name"] == "product-to-model"
    assert calls[0]["payload"]["inputs"]["product_image"] == "data:image/png;base64,abc123"
    assert calls[0]["payload"]["inputs"]["generation_mode"] == "quality"
    assert calls[0]["payload"]["inputs"]["resolution"] == "2k"
    assert "model_image" not in calls[0]["payload"]["inputs"]
    assert calls[1]["method"] == "GET"
    assert calls[1]["url"] == "https://api.test/v1/status/pred-1"
