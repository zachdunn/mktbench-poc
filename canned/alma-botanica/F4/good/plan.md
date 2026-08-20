# List-health / sunset re-permission program — before BFCM

## Why now
Deliverability has been flagging this for months. The Gmail spam-complaint rate has climbed from
0.09% in February to 0.28% in July (30-day rolling), above Gmail's 0.10% guidance and closing in
on the 0.30% enforcement line. A big driver: `flow_sunset` has sent nothing since it went dark on
2026-01-12, and the unengaged-12m pool has grown from 96k to 131k profiles while full-list
campaigns keep including them. Campaign cadence also doubled in June (2/wk to 4/wk) — that
frequency increase is compounding the same complaint trend, so hygiene alone won't fix this if
send volume keeps climbing at the same time.

## The program (reconciles flow_sunset, doesn't duplicate it)
We're re-enabling `flow_sunset` itself — not standing up a parallel flow next to the disabled
one — with tiered logic instead of the old binary "ask everyone the same thing" design:

- **Wave A — engaged_365 (soft).** These are lapsed-but-not-gone; one check-in email, no
  suppression threat. The goal is reactivation, not filtering.
- **Wave B — unengaged_12m (the real re-permission ask).** Two touches ten days apart: "do you
  still want these emails?" then a final "last call." Anyone who doesn't open or click either
  message gets suppressed. This is the segment the deliverability report is actually worried
  about — we deliberately do **not** touch the deeper 24-month-inactive file; remailing that
  cohort would be exactly the kind of full-list send beyond transactional-adjacent messaging the
  report's house rules warn against, and it would add complaint risk without a customer who's
  likely to respond.
- Actively-engaged tiers (engaged_30, engaged_90) are excluded entirely — they aren't a
  deliverability problem and don't belong in a sunset program.

## Timeline vs. BFCM
The program launches September 1. Wave A sends September 1–3. Wave B's first ask goes out
September 15, the final ask September 25, and non-response suppression completes by October 27
— three weeks ahead of the November 20 BFCM start. Nothing in this program sends, suppresses, or
re-permissions anyone during the BFCM window or its ramp; the list is stable and fully mailable
by the time BFCM volume starts.

## The tradeoff, quantified
The mailable list is roughly 342k profiles. 131k of those (about 38%) currently sit in the
unengaged-12m tier — up from 96k when `flow_sunset` went dark in January. If, in line with how
re-permission flows typically perform, Wave B suppresses the majority of non-responders in that
131k pool, we'd expect tens of thousands of profiles to leave the mailable file — a real, visible
shrink right before our biggest quarter. The trade we're making deliberately: that shrink buys us
headroom on the complaint rate (currently 0.28%, against a 0.30% enforcement line) by removing
the population most likely to hit "report spam" instead of unsubscribing, and it does so in
September/October, not during BFCM, so the revenue-bearing engaged file is untouched when it
matters most.

## Guardrails
No SMS is touched by this program. Email consent, suppression, and non-subscriber filters are
applied to both waves. This does not replace the frequency-cadence fix (issue #8) — hygiene and
send-volume discipline are two different levers, and this program only pulls one of them.
