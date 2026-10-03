"""Google Gemini client adapter implementing the LLMClient protocol."""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any

import httpx

from app.ai.llm.client import LLMClient, LLMMessage, LLMResponse, ToolCall

logger = logging.getLogger(__name__)


def _clean_schema_for_gemini(schema: Any) -> Any:
    """Recursively clean OpenAPI / JSON-schema to conform strictly to Gemini Schema proto.

    Removes unsupported keys like 'additionalProperties', and translates
    'exclusiveMinimum' -> 'minimum', 'exclusiveMaximum' -> 'maximum'.
    """
    if isinstance(schema, dict):
        cleaned: dict[str, Any] = {}
        for k, v in schema.items():
            if k == "additionalProperties":
                continue
            elif k == "exclusiveMinimum":
                cleaned["minimum"] = _clean_schema_for_gemini(v)
            elif k == "exclusiveMaximum":
                cleaned["maximum"] = _clean_schema_for_gemini(v)
            else:
                cleaned[k] = _clean_schema_for_gemini(v)
        return cleaned
    elif isinstance(schema, list):
        return [_clean_schema_for_gemini(item) for item in schema]
    return schema


class GeminiLLMClient(LLMClient):
    """Google Gemini API client adapter supporting generateContent and function calling."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-flash-latest",
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
    ) -> None:
        self.api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("LLM_API_KEY")
            or ""
        )
        self.model = model
        self.base_url = base_url.rstrip("/")

    async def complete(
        self,
        messages: list[LLMMessage],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        """Call Google Gemini API with system instructions and function declarations."""
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key,
        }

        # Separate system instruction from conversational turns
        system_instructions: list[str] = []
        contents: list[dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                system_instructions.append(msg.content)
            elif msg.role == "user":
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.content or " "}],
                })
            elif msg.role == "assistant":
                parts: list[dict[str, Any]] = []
                if msg.content:
                    parts.append({"text": msg.content})
                for tc in msg.tool_calls:
                    fc_data: dict[str, Any] = {
                        "name": tc.name,
                        "args": tc.arguments,
                    }
                    if getattr(tc, "id", None):
                        fc_data["id"] = tc.id
                    p_dict: dict[str, Any] = {"functionCall": fc_data}
                    ts = getattr(tc, "thought_signature", None)
                    if ts:
                        p_dict["thoughtSignature"] = ts
                    parts.append(p_dict)
                contents.append({
                    "role": "model",
                    "parts": parts if parts else [{"text": " "}],
                })
            elif msg.role == "tool":
                # In Gemini REST API generateContent, function responses MUST be sent with role 'user'
                try:
                    resp_obj = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                except Exception:
                    resp_obj = {"result": msg.content}

                contents.append({
                    "role": "user",
                    "parts": [{
                        "functionResponse": {
                            "name": msg.name or "tool",
                            "response": resp_obj if isinstance(resp_obj, dict) else {"result": resp_obj},
                        }
                    }],
                })

        payload: dict[str, Any] = {
            "contents": contents if contents else [{"role": "user", "parts": [{"text": "Hello"}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        if system_instructions:
            payload["systemInstruction"] = {
                "parts": [{"text": "\n\n".join(system_instructions)}]
            }

        # Convert tool schemas (OpenAI function declaration to Gemini format)
        if tools:
            declarations: list[dict[str, Any]] = []
            for t in tools:
                func = t.get("function", t)
                raw_params = func.get("parameters", {})
                cleaned_params = _clean_schema_for_gemini(raw_params)
                declarations.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": cleaned_params,
                })
            payload["tools"] = [{"functionDeclarations": declarations}]

        import asyncio

        max_retries = 3
        data = None
        used_model = self.model

        candidate_models = [self.model]
        for fallback in ("gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.7-flash"):
            if fallback not in candidate_models:
                candidate_models.append(fallback)

        async with httpx.AsyncClient(timeout=30.0) as client:
            for model_name in candidate_models:
                used_model = model_name
                endpoint = f"{self.base_url}/models/{model_name}:generateContent"
                model_failed = False
                for attempt in range(max_retries):
                    resp = await client.post(endpoint, headers=headers, json=payload)
                    if resp.status_code == 200:
                        data = resp.json()
                        break
                    elif resp.status_code in (429, 503) and "RESOURCE_EXHAUSTED" in resp.text:
                        logger.warning(
                            "Model %s quota exhausted (429). Attempting fallback model...",
                            model_name,
                        )
                        model_failed = True
                        break
                    elif resp.status_code in (429, 503) and attempt < max_retries - 1:
                        wait_seconds = 1.0 * (2 ** attempt)
                        logger.warning(
                            f"Gemini API returned {resp.status_code}. Retrying in {wait_seconds}s (attempt {attempt + 1}/{max_retries})..."
                        )
                        await asyncio.sleep(wait_seconds)
                    elif resp.status_code == 404:
                        logger.warning(f"Model {model_name} not found (404). Attempting fallback...")
                        model_failed = True
                        break
                    else:
                        logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                        raise RuntimeError(
                            f"Gemini API error ({resp.status_code}): {resp.text[:200]}"
                        )
                if data:
                    break
                if not model_failed:
                    break

            if not data:
                raise RuntimeError("Gemini API call failed after retries.")

        candidates = data.get("candidates", [])
        if not candidates:
            return LLMResponse(
                content="I was unable to process that request.",
                tool_calls=[],
                tokens_in=0,
                tokens_out=0,
                model=used_model,
            )

        candidate = candidates[0]
        content_obj = candidate.get("content", {})
        parts = content_obj.get("parts", [])

        text_content = ""
        tool_calls: list[ToolCall] = []

        for part in parts:
            if "text" in part:
                text_content += part["text"]
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    ToolCall(
                        id=fc.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}),
                        thought_signature=part.get("thoughtSignature"),
                    )
                )

        usage = data.get("usageMetadata", {})
        tokens_in = usage.get("promptTokenCount", 0)
        tokens_out = usage.get("candidatesTokenCount", 0)

        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=used_model,
        )
