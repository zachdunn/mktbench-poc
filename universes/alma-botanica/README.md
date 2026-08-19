# Alma Botánica — MarketingBench sample universe (slice)

Fictional mid-size DTC clean-skincare brand. This is a *sample slice* of the full universe
(500-profile sample of a 342k-profile base; monthly rollups instead of full event streams),
built to show design partners what the environment, planted issues, and answer key look like.

**Vitals:** 342k email profiles (61% engaged-12m) · 41.2k SMS · AOV $62 · median repurchase 74d ·
~28% of revenue via subscriptions · lines: Solstice (hero, high-margin), Midnight (body), Terra (masks/tools).

**Contents:** see the phase-1 spec (§2) for the full manifest. Files here that carry planted issues
are the point of the demo; `answer_key/` is grader-only and would be withheld from any agent under test.

**Consistency note:** quantitative signatures reconcile — e.g. the welcome flow's conversion drop
(June 2026) matches the expired-code date in `campaigns/discount_codes.csv`, and the revenue delta
is exactly computable from `flows/flow_performance.csv`.
