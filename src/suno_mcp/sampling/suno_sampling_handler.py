"""
Suno-MCP sampling fallback for FastMCP 3.1.

OpenAI-compatible **local** inference (e.g. Ollama at ``http://127.0.0.1:11434/v1``)
with no API key on loopback / private LAN. Set ``SUNO_SAMPLING_USE_CLIENT_LLM=1`` to
prefer the MCP host LLM when it supports sampling.

Env: ``SUNO_SAMPLING_BASE_URL``, ``SUNO_SAMPLING_MODEL``, ``SUNO_SAMPLING_API_KEY``,
``SUNO_SAMPLING_USE_OPENAI_KEY`` (uses ``OPENAI_API_KEY``).
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any
from urllib.parse import urlparse

import httpx
from mcp.shared.context import RequestContext
from mcp.types import CreateMessageRequestParams as SamplingParams
from mcp.types import (
    CreateMessageResult,
    CreateMessageResultWithTools,
    ImageContent,
    SamplingMessage,
    TextContent,
    Tool,
    ToolResultContent,
    ToolUseContent,
)

logger = logging.getLogger(__name__)


def _load_sampling_config() -> tuple[str, str, str | None]:
    """Return (base_url, model, api_key)."""
    base = os.getenv("SUNO_SAMPLING_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
    model = os.getenv("SUNO_SAMPLING_MODEL", "llama3.2")
    key = os.getenv("SUNO_SAMPLING_API_KEY")
    if os.getenv("SUNO_SAMPLING_USE_OPENAI_KEY", "").lower() in ("1", "true", "yes"):
        key = key or os.getenv("OPENAI_API_KEY")
    api_key = key.strip() if key else None
    return base, model, api_key


def _sampling_allows_empty_api_key(base_url: str) -> bool:
    try:
        parsed = urlparse(base_url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if host in ("127.0.0.1", "localhost", "::1"):
        return True
    if host.startswith("192.168."):
        return True
    if host.startswith("10."):
        return True
    if host.startswith("172."):
        parts = host.split(".")
        if len(parts) >= 2 and parts[0] == "172":
            try:
                second = int(parts[1])
            except ValueError:
                return False
            if 16 <= second <= 31:
                return True
    return False


def _sampling_http_enabled(api_key: str | None, base_url: str) -> bool:
    return bool(api_key and api_key.strip()) or _sampling_allows_empty_api_key(base_url)


def _hint_model(params: SamplingParams, default: str) -> str:
    mp = params.modelPreferences
    if mp is None:
        return default
    hints = getattr(mp, "hints", None) or []
    for h in hints:
        name = getattr(h, "name", None)
        if name:
            return name
    return default


def _tool_choice_openai(tc: Any | None) -> str | dict[str, Any]:
    if tc is None:
        return "auto"
    mode = getattr(tc, "mode", None)
    if mode == "required":
        return "required"
    if mode == "none":
        return "none"
    return "auto"


def _mcp_tools_to_openai(tools: list[Tool] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    out: list[dict[str, Any]] = []
    for t in tools:
        out.append(
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description or f"MCP tool {t.name}",
                    "parameters": (t.inputSchema if isinstance(t.inputSchema, dict) else {"type": "object"}),
                },
            }
        )
    return out


def _serialize_tool_result(tr: ToolResultContent) -> str:
    if tr.structuredContent is not None:
        try:
            return json.dumps(tr.structuredContent, ensure_ascii=False)[:80000]
        except (TypeError, ValueError):
            return str(tr.structuredContent)[:80000]
    parts: list[str] = []
    for block in tr.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        elif isinstance(block, ImageContent):
            parts.append("[image]")
        else:
            parts.append(str(block))
    body = "\n".join(parts).strip()
    if tr.isError:
        return f"[tool error] {body}" if body else "[tool error]"
    return body if body else "(empty tool result)"


def _sampling_messages_to_openai(
    messages: list[SamplingMessage],
    system_prompt: str | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if system_prompt:
        out.append({"role": "system", "content": system_prompt})

    for msg in messages:
        blocks = msg.content_as_list
        if msg.role == "user":
            tool_results = [b for b in blocks if isinstance(b, ToolResultContent)]
            texts = [b for b in blocks if isinstance(b, TextContent)]
            non_text = [b for b in blocks if not isinstance(b, (TextContent, ToolResultContent))]
            for tr in tool_results:
                out.append(
                    {
                        "role": "tool",
                        "tool_call_id": tr.toolUseId,
                        "content": _serialize_tool_result(tr),
                    }
                )
            if texts:
                joined = "\n".join(t.text for t in texts).strip()
                if joined:
                    out.append({"role": "user", "content": joined})
            for b in non_text:
                out.append(
                    {
                        "role": "user",
                        "content": f"[unsupported block in fallback handler: {type(b).__name__}]",
                    }
                )
        elif msg.role == "assistant":
            tool_uses = [b for b in blocks if isinstance(b, ToolUseContent)]
            texts = [b for b in blocks if isinstance(b, TextContent)]
            non_text = [b for b in blocks if not isinstance(b, (TextContent, ToolUseContent))]
            if tool_uses:
                tool_calls = []
                for tu in tool_uses:
                    args = tu.input
                    if isinstance(args, dict):
                        arg_str = json.dumps(args, ensure_ascii=False)
                    else:
                        arg_str = str(args)
                    tool_calls.append(
                        {
                            "id": tu.id or str(uuid.uuid4()),
                            "type": "function",
                            "function": {"name": tu.name, "arguments": arg_str},
                        }
                    )
                text_part = "\n".join(t.text for t in texts).strip() or None
                row: dict[str, Any] = {
                    "role": "assistant",
                    "tool_calls": tool_calls,
                }
                if text_part:
                    row["content"] = text_part
                else:
                    row["content"] = None
                out.append(row)
            else:
                joined = "\n".join(t.text for t in texts).strip()
                out.append({"role": "assistant", "content": joined})
            for b in non_text:
                out.append(
                    {
                        "role": "assistant",
                        "content": f"[unsupported block: {type(b).__name__}]",
                    }
                )
    return out


def _degraded_response_text(user_text: str, has_tools: bool) -> str:
    tool_note = (
        "Start **Ollama** (`ollama serve`), `ollama pull` your model, and set "
        "SUNO_SAMPLING_BASE_URL (default http://127.0.0.1:11434/v1) and SUNO_SAMPLING_MODEL. "
        "Or set SUNO_SAMPLING_USE_CLIENT_LLM=1 to use the MCP host LLM if it supports "
        "sampling with tools."
        if has_tools
        else (
            "Start **Ollama** on this machine (or point SUNO_SAMPLING_BASE_URL at your LAN "
            "Ollama host). No API key is needed on localhost/private LAN. "
            "Alternatively set SUNO_SAMPLING_USE_CLIENT_LLM=1 for host-provided sampling."
        )
    )
    _ = user_text
    return (
        "[Suno-MCP sampling — HTTP LLM not used]\n\n"
        f"{tool_note}\n\n"
        "Typical next step: suno_open_browser → suno_login → suno_generate_track, or "
        "agentic_suno_workflow once a local or cloud LLM endpoint is reachable."
    )


class SunoSamplingHandler:
    """
    OpenAI-compatible chat/completions (default: local Ollama).

    Callable as ``(messages, params, request_context)`` per FastMCP.
    """

    async def __call__(
        self,
        messages: list[SamplingMessage],
        params: SamplingParams,
        request_context: RequestContext[Any, Any],
    ) -> CreateMessageResult | CreateMessageResultWithTools | str:
        _ = request_context
        base_url, default_model, api_key = _load_sampling_config()
        model = _hint_model(params, default_model)
        max_tokens = params.maxTokens
        temperature = params.temperature
        sdk_tools = params.tools
        has_tools = bool(sdk_tools)

        openai_messages = _sampling_messages_to_openai(messages, params.systemPrompt)
        if not _sampling_http_enabled(api_key, base_url):
            last_user = ""
            for m in reversed(messages):
                if m.role == "user":
                    for b in m.content_as_list:
                        if isinstance(b, TextContent):
                            last_user = b.text
                            break
                    if last_user:
                        break
            text = _degraded_response_text(last_user, has_tools)
            if has_tools:
                return CreateMessageResultWithTools(
                    role="assistant",
                    model="none",
                    content=TextContent(type="text", text=text),
                    stopReason="endTurn",
                )
            return CreateMessageResult(
                role="assistant",
                model="none",
                content=TextContent(type="text", text=text),
                stopReason="endTurn",
            )

        url = f"{base_url}/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        oa_tools = _mcp_tools_to_openai(sdk_tools)
        if oa_tools:
            payload["tools"] = oa_tools
            payload["tool_choice"] = _tool_choice_openai(params.toolChoice)

        headers = {"Authorization": f"Bearer {api_key or ''}", "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(url, headers=headers, json=payload)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPStatusError as e:
            err_body = ""
            try:
                err_body = e.response.text[:2000]
            except Exception:
                pass
            msg = (
                f"[Suno-MCP sampling] HTTP {e.response.status_code} from {url}. "
                f"Check Ollama is running, SUNO_SAMPLING_MODEL is pulled, URL/base path, "
                f"and API key if using a cloud endpoint. Body: {err_body}"
            )
            logger.warning(msg)
            return CreateMessageResult(
                role="assistant",
                model=model,
                content=TextContent(type="text", text=msg),
                stopReason="endTurn",
            )
        except Exception as e:
            msg = f"[Suno-MCP sampling] Request failed: {e!s}"
            logger.exception("Sampling fallback failed")
            return CreateMessageResult(
                role="assistant",
                model=model,
                content=TextContent(type="text", text=msg),
                stopReason="endTurn",
            )

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        finish = (choice.get("finish_reason") or "stop") or "stop"
        tool_calls = msg.get("tool_calls") or []
        content_text = msg.get("content") or ""

        if tool_calls:
            blocks: list[TextContent | ToolUseContent] = []
            if isinstance(content_text, str) and content_text.strip():
                blocks.append(TextContent(type="text", text=content_text))
            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name") or "unknown_tool"
                raw_args = fn.get("arguments") or "{}"
                try:
                    parsed: Any = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    if not isinstance(parsed, dict):
                        parsed = {"value": parsed}
                except json.JSONDecodeError:
                    parsed = {"_raw": raw_args}
                tid = tc.get("id") or str(uuid.uuid4())
                blocks.append(ToolUseContent(type="tool_use", name=name, id=tid, input=parsed))
            return CreateMessageResultWithTools(
                role="assistant",
                model=str(data.get("model") or model),
                content=blocks,
                stopReason="toolUse",
            )

        if isinstance(content_text, list):
            text_parts = []
            for part in content_text:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text") or "")
                else:
                    text_parts.append(str(part))
            content_text = "\n".join(text_parts)

        stop_reason = "endTurn"
        if finish in ("length", "max_tokens", "maxTokens"):
            stop_reason = "maxTokens"
        return CreateMessageResult(
            role="assistant",
            model=str(data.get("model") or model),
            content=TextContent(type="text", text=str(content_text)),
            stopReason=stop_reason,
        )
