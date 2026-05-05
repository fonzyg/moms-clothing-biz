from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

DEFAULT_FASHN_BASE_URL = "https://api.fashn.ai"


class FashnError(RuntimeError):
    """Raised when the model-shot provider cannot complete a generation."""


@dataclass(frozen=True)
class FashnConfig:
    api_key: str | None
    model_image_url: str | None = None
    base_url: str = DEFAULT_FASHN_BASE_URL
    timeout_seconds: float = 120.0
    poll_interval_seconds: float = 2.0

    @classmethod
    def from_env(cls) -> FashnConfig:
        return cls(
            api_key=os.getenv("FASHN_API_KEY"),
            model_image_url=os.getenv("FASHN_MODEL_IMAGE_URL"),
            base_url=os.getenv("FASHN_API_BASE_URL", DEFAULT_FASHN_BASE_URL),
            timeout_seconds=_float_env("FASHN_TIMEOUT_SECONDS", 120.0),
            poll_interval_seconds=_float_env("FASHN_POLL_INTERVAL_SECONDS", 2.0),
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)


@dataclass(frozen=True)
class FashnModelShot:
    generated_image_url: str
    prediction_id: str
    model_name: str
    generation_mode: str


class FashnClient:
    def __init__(
        self,
        config: FashnConfig,
        *,
        opener: Callable[..., Any] = urllib.request.urlopen,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.config = config
        self._opener = opener
        self._sleeper = sleeper
        self._clock = clock

    def generate_model_shot(
        self,
        *,
        garment_image: str,
        quality_profile: dict[str, Any],
        product_category: str,
    ) -> FashnModelShot:
        if not self.config.api_key:
            raise FashnError("FASHN_API_KEY is not configured.")

        if self.config.model_image_url:
            _validate_provider_image(self.config.model_image_url, "FASHN_MODEL_IMAGE_URL")
        _validate_provider_image(garment_image, "source image")

        model_name = "product-to-model"
        payload = self._build_run_payload(
            model_name=model_name,
            garment_image=garment_image,
            quality_profile=quality_profile,
            product_category=product_category,
        )
        run = self._request_json("POST", "/v1/run", payload)
        prediction_id = str(run.get("id") or "")
        if not prediction_id:
            raise FashnError("FASHN did not return a prediction id.")

        generated_url = self._wait_for_output(prediction_id)
        return FashnModelShot(
            generated_image_url=generated_url,
            prediction_id=prediction_id,
            model_name=model_name,
            generation_mode=str(quality_profile["generation_mode"]),
        )

    def _build_run_payload(
        self,
        *,
        model_name: str,
        garment_image: str,
        quality_profile: dict[str, Any],
        product_category: str,
    ) -> dict[str, Any]:
        inputs = {
            "product_image": garment_image,
            "prompt": _prompt_for_category(product_category),
            "aspect_ratio": "4:5",
            "resolution": _resolution_for_quality(quality_profile),
            "generation_mode": _product_to_model_mode(quality_profile),
            "output_format": "jpeg",
        }
        if self.config.model_image_url:
            inputs["model_image"] = self.config.model_image_url

        return {"model_name": model_name, "inputs": inputs}

    def _wait_for_output(self, prediction_id: str) -> str:
        deadline = self._clock() + self.config.timeout_seconds
        last_status = "queued"

        while self._clock() <= deadline:
            status = self._request_json("GET", f"/v1/status/{prediction_id}")
            last_status = str(status.get("status") or last_status)

            if last_status == "completed":
                output = status.get("output")
                if isinstance(output, list) and output:
                    return str(output[0])
                if isinstance(output, str) and output:
                    return output
                raise FashnError("FASHN completed without an output image.")

            if last_status in {"failed", "canceled"}:
                error = status.get("error") or status.get("message") or "unknown provider error"
                raise FashnError(f"FASHN generation {last_status}: {error}")

            self._sleeper(self.config.poll_interval_seconds)

        raise FashnError(f"FASHN timed out while status was {last_status}.")

    def _request_json(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.config.base_url.rstrip('/')}{endpoint}"
        data = None
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Accept": "application/json",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener(request, timeout=self.config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise FashnError(f"FASHN HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise FashnError(f"FASHN network error: {exc.reason}") from exc

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise FashnError("FASHN returned invalid JSON.") from exc

        if not isinstance(decoded, dict):
            raise FashnError("FASHN returned an unexpected response shape.")
        return decoded


def is_fashn_configured() -> bool:
    return FashnConfig.from_env().is_configured


def generate_fashn_model_shot(
    *,
    garment_image: str,
    quality_profile: dict[str, Any],
    product_category: str,
) -> FashnModelShot:
    client = FashnClient(FashnConfig.from_env())
    return client.generate_model_shot(
        garment_image=garment_image,
        quality_profile=quality_profile,
        product_category=product_category,
    )


def _product_to_model_mode(quality_profile: dict[str, Any]) -> str:
    if quality_profile["quality_tier"] == "premium":
        return "quality"
    if quality_profile["quality_tier"] == "balanced":
        return "balanced"
    return "fast"


def _resolution_for_quality(quality_profile: dict[str, Any]) -> str:
    if quality_profile["quality_tier"] == "premium":
        return "2k"
    return "1k"


def _prompt_for_category(product_category: str) -> str:
    base_prompt = "clean studio e-commerce model shot, natural pose, product clearly visible"
    if product_category == "Bottoms":
        return f"{base_prompt}, full body framing"
    if product_category == "Dresses":
        return f"{base_prompt}, dress shown full length"
    if product_category == "Outerwear":
        return f"{base_prompt}, outerwear layered naturally"
    return base_prompt


def _validate_provider_image(value: str, field_name: str) -> None:
    if value.startswith(("http://", "https://", "data:image/")):
        return
    raise FashnError(f"{field_name} must be a public URL or a base64 image data URL.")


def _float_env(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default
