"""Unit tests for GeminiLLMClient adapter."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.ai.llm.client import LLMMessage, ToolCall
from app.ai.llm.gemini_client import GeminiLLMClient


@pytest.mark.asyncio
async def test_gemini_missing_api_key_raises():
    client = GeminiLLMClient(api_key="")
    with pytest.raises(ValueError, match="GEMINI_API_KEY is not configured"):
        await client.complete([LLMMessage(role="user", content="Hello")])


@pytest.mark.asyncio
async def test_gemini_complete_text_response():
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Compound interest creates wealth over time."}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 25,
            "candidatesTokenCount": 8,
            "totalTokenCount": 33,
        },
    }

    mock_resp = httpx.Response(200, json=mock_response_data, request=httpx.Request("POST", "https://api.example.com"))

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        client = GeminiLLMClient(api_key="test_api_key")

        messages = [
            LLMMessage(role="system", content="You are a financial coach."),
            LLMMessage(role="user", content="Explain interest."),
        ]

        result = await client.complete(messages)

        assert result.content == "Compound interest creates wealth over time."
        assert len(result.tool_calls) == 0
        assert result.tokens_in == 25
        assert result.tokens_out == 8
        assert result.model == "gemini-flash-latest"


@pytest.mark.asyncio
async def test_gemini_complete_function_call():
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "functionCall": {
                                "name": "check_affordability",
                                "args": {"amount": 5000, "category": "shopping"},
                            }
                        }
                    ],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 40,
            "candidatesTokenCount": 15,
        },
    }

    mock_resp = httpx.Response(200, json=mock_response_data, request=httpx.Request("POST", "https://api.example.com"))

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        client = GeminiLLMClient(api_key="test_api_key")

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "check_affordability",
                    "description": "Assess if user can afford expense",
                    "parameters": {"type": "object", "properties": {"amount": {"type": "number"}}},
                },
            }
        ]

        result = await client.complete(
            [LLMMessage(role="user", content="Can I spend 5000?")],
            tools=tools,
        )

        assert len(result.tool_calls) == 1
        tc = result.tool_calls[0]
        assert tc.name == "check_affordability"
        assert tc.arguments["amount"] == 5000
