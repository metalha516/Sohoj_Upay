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
    """Sanitize JSON Schema / OpenAPI schema to be compliant with Google Gemini API Schema proto."""
    if isinstance(schema, dict):
        cleaned: dict[str, Any] = {}
        s = dict(schema)
        if "exclusiveMinimum" in s:
            s["minimum"] = s["exclusiveMinimum"]
        if "exclusiveMaximum" in s:
            s["maximum"] = s["exclusiveMaximum"]
        if "anyOf" in s:
            any_of = s["anyOf"]
            types = [t.get("type") for t in any_of if isinstance(t, dict) and "type" in t]
            if "null" in types:
                non_null = [t for t in any_of if t.get("type") != "null"]
                if len(non_null) == 1:
                    s.update(non_null[0])
                    s["nullable"] = True
                    s.pop("anyOf", None)
        for k, v in s.items():
            if k in (
                "additionalProperties",
                "exclusiveMinimum",
                "exclusiveMaximum",
                "$schema",
                "$defs",
                "definitions",
                "title",
            ):
                continue
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
                part = {"text": msg.content or " "}
                if contents and contents[-1]["role"] == "user":
                    contents[-1]["parts"].append(part)
                else:
                    contents.append({
                        "role": "user",
                        "parts": [part],
                    })
            elif msg.role == "assistant":
                if msg.raw_parts:
                    parts = []
                    for raw_p in msg.raw_parts:
                        p_copy = dict(raw_p)
                        if "functionCall" in p_copy:
                            if not p_copy.get("thoughtSignature") and not p_copy.get("thought_signature"):
                                p_copy["thoughtSignature"] = "skip_thought_signature_validator"
                        parts.append(p_copy)
                else:
                    parts = []
                    if msg.content:
                        parts.append({"text": msg.content})
                    for tc in msg.tool_calls:
                        p_dict: dict[str, Any] = {
                            "functionCall": {
                                "name": tc.name,
                                "args": tc.arguments,
                            },
                            "thoughtSignature": tc.thought_signature or "skip_thought_signature_validator",
                        }
                        parts.append(p_dict)
                if not parts:
                    parts = [{"text": " "}]
                if contents and contents[-1]["role"] == "model":
                    contents[-1]["parts"].extend(parts)
                else:
                    contents.append({
                        "role": "model",
                        "parts": parts,
                    })
            elif msg.role == "tool":
                # Function response part
                try:
                    resp_obj = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                except Exception:
                    resp_obj = {"result": msg.content}

                func_name = msg.name
                if not func_name and msg.tool_call_id:
                    for prev_msg in reversed(messages):
                        if prev_msg.role == "assistant" and prev_msg.tool_calls:
                            for prev_tc in prev_msg.tool_calls:
                                if prev_tc.id == msg.tool_call_id:
                                    func_name = prev_tc.name
                                    break
                        if func_name:
                            break
                if not func_name:
                    func_name = "tool"

                func_part = {
                    "functionResponse": {
                        "name": func_name,
                        "response": resp_obj if isinstance(resp_obj, dict) else {"result": resp_obj},
                    }
                }

                if contents and contents[-1]["role"] == "user":
                    contents[-1]["parts"].append(func_part)
                else:
                    contents.append({
                        "role": "user",
                        "parts": [func_part],
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
                    "parameters": _clean_schema_for_gemini(func.get("parameters", {})),
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
            if "text" in part and not part.get("thought", False):
                text_content += part["text"]
            if "functionCall" in part:
                fc = part["functionCall"]
                sig = (
                    part.get("thoughtSignature")
                    or part.get("thought_signature")
                    or fc.get("thoughtSignature")
                    or fc.get("thought_signature")
                )
                tool_calls.append(
                    ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}),
                        thought_signature=sig,
                        raw_part=part,
                    )
                )

        logger.info(f"Gemini returned {len(parts)} parts, tool_calls={len(tool_calls)}")

        usage = data.get("usageMetadata", {})
        tokens_in = usage.get("promptTokenCount", 0)
        tokens_out = usage.get("candidatesTokenCount", 0)

        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            model=self.model,
            raw_parts=parts,
        )
