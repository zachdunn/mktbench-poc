"""Provider-agnostic LLM client over urllib (no third-party deps).

Two backends:
  - anthropic:  Anthropic Messages API (native format)
  - openrouter: OpenRouter's OpenAI-style /chat/completions

The harness speaks Anthropic's message shape internally (content blocks, tool_use /
tool_result); the OpenRouter backend translates at the boundary, so graders and adapters
are provider-blind. Select with MB_PROVIDER=anthropic|openrouter, or let it auto-detect
from whichever API key is present (see config.provider()).
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

from . import config


class LLMError(RuntimeError):
    pass


def messages(model: str, max_tokens: int, system: str | None, msgs: list[dict],
             tools: list[dict] | None = None, retries: int = 3) -> dict:
    """Send a chat request; returns an Anthropic-shaped response dict regardless of provider."""
    provider = config.provider()
    key = config.api_key()
    if not key:
        raise LLMError("no API key set — export ANTHROPIC_API_KEY or OPENROUTER_API_KEY, or run offline")
    if provider == "openrouter":
        url, body, headers = _openrouter_request(model, max_tokens, system, msgs, tools, key)
    else:
        url, body, headers = _anthropic_request(model, max_tokens, system, msgs, tools, key)
    raw = _post(url, body, headers, retries)
    if provider == "openrouter":
        return _from_openai_response(raw)
    return raw


def text_of(response: dict) -> str:
    return "".join(b.get("text", "") for b in response.get("content", []) if b.get("type") == "text")


# ---------- transport ----------

def _post(url: str, body: dict, headers: dict, retries: int) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"content-type": "application/json", **headers},
                                 method="POST")
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            if e.code in (408, 429, 500, 502, 503, 529) and attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                last_err = LLMError(f"HTTP {e.code}: {detail}")
                continue
            raise LLMError(f"HTTP {e.code}: {detail}") from e
        except urllib.error.URLError as e:
            if attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                last_err = e
                continue
            raise LLMError(str(e)) from e
    raise LLMError(str(last_err))


# ---------- anthropic backend ----------

def _anthropic_request(model, max_tokens, system, msgs, tools, key):
    body: dict = {"model": model, "max_tokens": max_tokens, "messages": msgs}
    if system:
        body["system"] = system
    if tools:
        body["tools"] = tools
    headers = {"x-api-key": key, "anthropic-version": config.ANTHROPIC_VERSION}
    return config.ANTHROPIC_API_URL, body, headers


# ---------- openrouter backend (OpenAI chat-completions format) ----------

def _to_openai_tools(tools: list[dict]) -> list[dict]:
    return [{"type": "function",
             "function": {"name": t["name"], "description": t.get("description", ""),
                          "parameters": t.get("input_schema", {"type": "object"})}}
            for t in tools]


def _to_openai_messages(system: str | None, msgs: list[dict]) -> list[dict]:
    out: list[dict] = []
    if system:
        out.append({"role": "system", "content": system})
    for m in msgs:
        content = m["content"]
        if isinstance(content, str):
            out.append({"role": m["role"], "content": content})
            continue
        if m["role"] == "assistant":
            text = "".join(b.get("text", "") for b in content if b.get("type") == "text")
            tool_calls = [{"id": b["id"], "type": "function",
                           "function": {"name": b["name"], "arguments": json.dumps(b.get("input", {}))}}
                          for b in content if b.get("type") == "tool_use"]
            msg: dict = {"role": "assistant", "content": text or None}
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)
        else:  # user turn: tool_result blocks and/or text blocks
            texts = []
            for b in content:
                if b.get("type") == "tool_result":
                    c = b.get("content", "")
                    if isinstance(c, list):
                        c = "".join(x.get("text", "") for x in c if x.get("type") == "text")
                    out.append({"role": "tool", "tool_call_id": b["tool_use_id"], "content": str(c)})
                elif b.get("type") == "text":
                    texts.append(b["text"])
            if texts:
                out.append({"role": "user", "content": "\n".join(texts)})
    return out


def _openrouter_request(model, max_tokens, system, msgs, tools, key):
    body: dict = {"model": model, "max_tokens": max_tokens,
                  "messages": _to_openai_messages(system, msgs)}
    if tools:
        body["tools"] = _to_openai_tools(tools)
    headers = {"authorization": f"Bearer {key}",
               "http-referer": "https://github.com/marketingbench",
               "x-title": "MarketingBench eval harness"}
    return config.OPENROUTER_API_URL, body, headers


def _from_openai_response(raw: dict) -> dict:
    """Convert an OpenAI-style completion to the Anthropic response shape the harness uses."""
    if "choices" not in raw or not raw["choices"]:
        raise LLMError(f"unexpected OpenRouter response: {json.dumps(raw)[:300]}")
    choice = raw["choices"][0]
    msg = choice.get("message", {})
    content: list[dict] = []
    if msg.get("content"):
        content.append({"type": "text", "text": msg["content"]})
    for tc in msg.get("tool_calls") or []:
        try:
            args = json.loads(tc["function"].get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        content.append({"type": "tool_use", "id": tc.get("id", "call_0"),
                        "name": tc["function"]["name"], "input": args})
    finish = choice.get("finish_reason")
    stop_reason = {"stop": "end_turn", "tool_calls": "tool_use",
                   "length": "max_tokens"}.get(finish, finish or "end_turn")
    return {"content": content, "stop_reason": stop_reason, "model": raw.get("model"),
            "usage": raw.get("usage", {})}
