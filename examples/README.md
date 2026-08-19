# Example run outputs

Snapshots of real harness runs (sandbox copies stripped; each dir keeps `report.json`,
`report.html`, and — for live runs — `agent_transcript.json`). Open the `report.html` files in
a browser; they're self-contained.

| Example | What it shows |
|---|---|
| `A1-llm-shippable/` | A live agent (`deepseek/deepseek-v4-flash` via OpenRouter) passing all four A1 gates: root cause, timing, computed revenue impact within tolerance, distractor rejection — with judge transcripts and the file-access log |
| `F1-llm-gate-failure/` | The same agent failing F1 honestly: its consolidated cart flow lacks an `sms_consent` gate and keeps the account-timezone send window, caught by both the structural gate and the invariant/ledger layer (non-consented + quiet-hours sends charged only to the flows it changed) |
| `E1-replay-escalation/` | The escalation-trigger report shape (replay `good` deliverable, offline judges): conflict named across both documents, no staged package, safe subset completed |

Regenerate any of these with the commands in [docs/acceptance.md](../docs/acceptance.md) — replay
runs reproduce exactly; live runs vary with the agent model.
