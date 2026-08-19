"""Provider selection and Anthropic↔OpenAI format translation (no network)."""
import json
import os
import unittest
from unittest import mock

from harness import config
from harness.llm_client import (_from_openai_response, _openrouter_request,
                                _to_openai_messages, _to_openai_tools, text_of)


class TestProviderSelection(unittest.TestCase):
    def test_auto_detect(self):
        with mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "a", "OPENROUTER_API_KEY": "o"}, clear=True):
            self.assertEqual(config.provider(), "anthropic")   # anthropic wins if both set
            self.assertEqual(config.api_key(), "a")
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "o"}, clear=True):
            self.assertEqual(config.provider(), "openrouter")
            self.assertEqual(config.api_key(), "o")
            self.assertEqual(config.judge_model(), "anthropic/claude-sonnet-4.5")
            self.assertFalse(config.offline_default())
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(config.provider(), "anthropic")
            self.assertTrue(config.offline_default())

    def test_explicit_override(self):
        env = {"MB_PROVIDER": "openrouter", "OPENROUTER_API_KEY": "o", "ANTHROPIC_API_KEY": "a",
               "MB_JUDGE_MODEL": "openai/gpt-4.1"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(config.provider(), "openrouter")
            self.assertEqual(config.api_key(), "o")
            self.assertEqual(config.judge_model(), "openai/gpt-4.1")
        with mock.patch.dict(os.environ, {"MB_PROVIDER": "nope"}, clear=True):
            with self.assertRaises(ValueError):
                config.provider()


ANTHROPIC_TOOLS = [{"name": "read_file", "description": "Read a file.",
                    "input_schema": {"type": "object", "properties": {"path": {"type": "string"}},
                                     "required": ["path"]}}]


class TestFormatTranslation(unittest.TestCase):
    def test_tools_to_openai(self):
        out = _to_openai_tools(ANTHROPIC_TOOLS)
        self.assertEqual(out[0]["type"], "function")
        self.assertEqual(out[0]["function"]["name"], "read_file")
        self.assertEqual(out[0]["function"]["parameters"]["required"], ["path"])

    def test_message_round_trip_with_tool_use(self):
        msgs = [
            {"role": "user", "content": "do the task"},
            {"role": "assistant", "content": [
                {"type": "text", "text": "reading now"},
                {"type": "tool_use", "id": "tu_1", "name": "read_file", "input": {"path": "flows/flows.json"}},
            ]},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": "tu_1", "content": "{\"flows\": []}"},
            ]},
        ]
        out = _to_openai_messages("sys prompt", msgs)
        self.assertEqual(out[0], {"role": "system", "content": "sys prompt"})
        self.assertEqual(out[1], {"role": "user", "content": "do the task"})
        self.assertEqual(out[2]["tool_calls"][0]["function"]["name"], "read_file")
        self.assertEqual(json.loads(out[2]["tool_calls"][0]["function"]["arguments"]),
                         {"path": "flows/flows.json"})
        self.assertEqual(out[3], {"role": "tool", "tool_call_id": "tu_1", "content": "{\"flows\": []}"})

    def test_response_from_openai_tool_call(self):
        raw = {"model": "anthropic/claude-sonnet-4.5", "choices": [{
            "finish_reason": "tool_calls",
            "message": {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_9", "type": "function",
                 "function": {"name": "submit", "arguments": "{\"parts\": {\"memo\": \"hi\"}}"}}]}}]}
        resp = _from_openai_response(raw)
        self.assertEqual(resp["stop_reason"], "tool_use")
        tool_uses = [b for b in resp["content"] if b["type"] == "tool_use"]
        self.assertEqual(tool_uses[0]["name"], "submit")
        self.assertEqual(tool_uses[0]["input"], {"parts": {"memo": "hi"}})

    def test_response_from_openai_text(self):
        raw = {"choices": [{"finish_reason": "stop",
                            "message": {"role": "assistant", "content": "all done"}}]}
        resp = _from_openai_response(raw)
        self.assertEqual(resp["stop_reason"], "end_turn")
        self.assertEqual(text_of(resp), "all done")

    def test_openrouter_request_shape(self):
        url, body, headers = _openrouter_request(
            "anthropic/claude-sonnet-4.5", 100, "sys", [{"role": "user", "content": "hi"}],
            ANTHROPIC_TOOLS, "sk-or-xxx")
        self.assertIn("openrouter.ai", url)
        self.assertEqual(headers["authorization"], "Bearer sk-or-xxx")
        self.assertEqual(body["messages"][0]["role"], "system")
        self.assertEqual(body["tools"][0]["type"], "function")


if __name__ == "__main__":
    unittest.main()
