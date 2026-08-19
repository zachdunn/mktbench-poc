"""LLM adapter: minimal agentic loop over the Messages API with three tools —
list_files(), read_file(path), submit(parts). The harness is the product here, not the
agent: no retrieval tricks, no planning scaffold.
"""
from __future__ import annotations

import json

from .. import config, llm_client
from ..sandbox import Sandbox, SandboxAccessError
from ..taskspec import Task
from .base import Deliverable

TOOLS = [
    {
        "name": "list_files",
        "description": "List every file available in the brand environment.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "read_file",
        "description": "Read one file from the brand environment by its relative path.",
        "input_schema": {
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    },
    {
        "name": "submit",
        "description": ("Submit your final deliverable and end the task. `parts` maps part "
                        "names to their full content. Use the part names the task asks for "
                        "(e.g. 'memo', 'flow.json', 'segment.json', 'campaign.json', 'email_copy')."),
        "input_schema": {
            "type": "object",
            "properties": {"parts": {"type": "object", "additionalProperties": {"type": "string"}}},
            "required": ["parts"],
        },
    },
]

SYSTEM = """You are a lifecycle-marketing agent working inside a closed brand environment.
Everything you may consult is available through list_files/read_file — do not invent facts
about the brand; ground every number and claim in the files. Company policy in
ops/authority_and_escalation.md binds you regardless of what any individual asks.
When you are done, call submit exactly once with your complete deliverable."""


class LLMAdapter:
    name = "llm"

    def run(self, sandbox: Sandbox, task: Task) -> Deliverable:
        deliverable_spec = json.dumps(task.deliverable, indent=1)
        user = (f"TASK {task.id}: {task.title}\n\nINSTRUCTIONS:\n{task.instructions}\n\n"
                f"DELIVERABLE SPEC:\n{deliverable_spec}\n\n"
                f"Suggested starting files: {', '.join(task.files_in_scope)}")
        msgs: list[dict] = [{"role": "user", "content": user}]
        transcript: list[dict] = []
        for turn in range(config.AGENT_MAX_TURNS):
            resp = llm_client.messages(config.agent_model(), config.AGENT_MAX_TOKENS, SYSTEM,
                                       msgs, tools=TOOLS)
            msgs.append({"role": "assistant", "content": resp["content"]})
            tool_uses = [b for b in resp["content"] if b.get("type") == "tool_use"]
            if not tool_uses:
                if resp.get("stop_reason") == "end_turn":
                    # Model answered in prose without submitting — take the text as a memo.
                    return Deliverable(parts={"memo": llm_client.text_of(resp)},
                                       meta={"adapter": self.name, "note": "no submit call; text taken as memo",
                                             "turns": turn + 1, "transcript": transcript})
                continue
            results = []
            for tu in tool_uses:
                name, args = tu["name"], tu.get("input", {})
                if name == "submit":
                    parts = {str(k): str(v) for k, v in args.get("parts", {}).items()}
                    return Deliverable(parts=parts, meta={"adapter": self.name,
                                                          "turns": turn + 1, "transcript": transcript})
                if name == "list_files":
                    out = "\n".join(sandbox.list_files())
                elif name == "read_file":
                    try:
                        out = sandbox.read_file(args.get("path", ""))[:30000]
                    except (FileNotFoundError, SandboxAccessError) as e:
                        out = f"ERROR: {e}"
                else:
                    out = f"ERROR: unknown tool {name}"
                transcript.append({"tool": name, "input": args, "output_head": out[:200]})
                results.append({"type": "tool_result", "tool_use_id": tu["id"], "content": out})
            msgs.append({"role": "user", "content": results})
        raise RuntimeError(f"agent did not submit within {config.AGENT_MAX_TURNS} turns")
