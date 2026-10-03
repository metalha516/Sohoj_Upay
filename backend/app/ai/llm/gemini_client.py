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

        endpoint = f"{self.base_url}/models/{self.model}:generateContent"
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
                    parts.append({
                        "functionCall": {
                            "name": tc.name,
                            "args": tc.arguments,
                        }
                    })
                contents.append({
                    "role": "model",
                    "parts": parts if parts else [{"text": " "}],
                })
            elif msg.role == "tool":
                # Function response part
                try:
                    resp_obj = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                except Exception:
                    resp_obj = {"result": msg.content}

                contents.append({
                    "role": "function",
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
                declarations.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                })
            payload["tools"] = [{"functionDeclarations": declarations}]

        import asyncio

        max_retries = 3
        data = None

        async with httpx.AsyncClient(timeout=30.0) as client:
            for attempt in range(max_retries):
                resp = await client.post(endpoint, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    break
                elif resp.status_code in (429, 503) and attempt < max_retries - 1:
                    wait_seconds = 1.0 * (2 ** attempt)
                    logger.warning(
                        f"Gemini API returned {resp.status_code}. Retrying in {wait_seconds}s (attempt {attempt + 1}/{max_retries})..."
                    )
                    await asyncio.sleep(wait_seconds)
                else:
                    logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                    raise RuntimeError(
                        f"Gemini API error ({resp.status_code}): {resp.text[:200]}"
                    )

            if not data:
                raise RuntimeError("Gemini API call failed after retries.")

        candidates = data.get("candidates", [])
        if not candidates:
            return LLMResponse(
                content="I was unable to process that request.",
                tool_calls=[],
                tokens_in=0,
                tokens_out=0,
                model=self.model,
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
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}),
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
            model=self.model,
        )
