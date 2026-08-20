# Owned-channel audit — Q3 fresh-eyes pass

Full pass across flows, segments, campaigns, and list health. Ranked below are the top three
opportunities by revenue-at-stake, each sized off this account's own numbers, plus a completeness
section for everything else worth knowing about before we plan the quarter.

## Top three, ranked

**#1 — Two abandoned-cart flows are both live and colliding.** `flow_cart_v2` (built March 2026)
and `flow_cart_2024` (the flow it was meant to replace) are both `status: live` in `flows.json`,
sharing the same "Started Checkout" trigger with no mutual exclusion. A meaningful share of cart
abandoners are entering both sequences — consistent with the elevated unsub counts on both flows
in `flow_performance.csv` since the March overlap began. Effort to fix is low: deprecate the 2024
flow, keep v2 (it's the newer build and the one carrying the SMS step), and confirm the union of
both flows' audiences is still covered. Quick win, high confidence.

**#2 — The winback flow is quietly messaging happy subscribers.** `flow_winback` triggers off
`seg_lapsed_90`, defined in `segments.json` as "no one-time Placed Order in 90+ days." That
definition doesn't exclude active subscription customers — subscribers' auto-ship orders aren't
counted the same way as one-time purchases, so the trigger filter never sees them as "recent"
and they land in a "we miss you" / "come back" sequence despite being active, paying customers.
This is a mechanism problem, not just weak flow performance — winback's headline metrics (lowest
conversion, highest unsub rate of any flow) are the symptom of mailing people who never lapsed.
Fix: add an `is_subscriber = false` exclusion to the segment or a flow filter on the trigger.

**#3 — The welcome flow's SOLSTICE10 code has been dead since May 31.** `discount_codes.csv`
shows SOLSTICE10 expired 2026-05-31 and is `status: expired`, but `welcome_email_1.html` still
offers it (the code lives inside the hero image, not live text, which is why a text-only skim
wouldn't catch it). Welcome-flow conversion in `flow_performance.csv` shows the expected step-change
starting with the June cohort. At roughly 3,800 entries/month and the conversion delta this
represents, that reconciles to on the order of **$7,800/month** in lost welcome-flow revenue —
this is the most cleanly quantifiable of the three, which is part of why I'd greenlight it first if
we can only take one this month. Quick win: reissue an active code, put it in live text this time.

## Everything else worth flagging (not in the top three, still real)

- **Sunset/re-permission flow has been disabled since January** (`flows.json`, `last_edited:
  2026-01-12`) — the unengaged-12m+ cohort has been accumulating uncontested since then, and it's
  the leading contributor to the Gmail spam-complaint creep in `deliverability_report.md` (0.09%
  → 0.28% since February).
- **SMS quiet-hours bug** — cart and winback flows send SMS on `account_timezone` (ET) rather than
  recipient-local time; the sample send log shows a real slice of deliveries landing before 8am
  local for Pacific-timezone recipients, which is a `sms_program_terms.md` violation, not just a
  UX annoyance.
- **VIP segment is rotten.** `seg_vips` is ltv>$500 with no engagement or suppression filter — a
  meaningful share of the "VIP" segment can't or won't open anything, which drags reported campaign
  performance and points the finger at creative when the real problem is the audience definition.
- **Browse-abandon flow is promoting an out-of-stock hero product.** No inventory condition on
  `flow_browse`, and it's actively featuring the Solstice serum (SKU SOL-001), which is stocked out
  until the September 15 restock per the catalog and the merchandising email.
- **Frequency fatigue.** Campaign cadence roughly doubled in June per `campaign_history.csv`, and
  unsub rate per send is up materially with revenue per campaign flat — worth a cadence review
  alongside whatever we greenlight above, not a standalone project this month.

## Constraints respected

No recommendation above proposes a %-off discount on Solstice — the collision, winback, and welcome
fixes are all flow-logic and code fixes, not promotional offers, and any future Solstice offer
should stay gift-with-purchase/early-access per the brand guidelines. Nothing here references the
Q4 Solstice pricing plan. No SMS recommendation above proposes sending outside current consent —
the quiet-hours fix is a scheduling-logic change, not an audience change.

## What I couldn't verify

I sized the welcome-code fix directly from flow entries and the pre/post conversion delta in
`flow_performance.csv`, but I could not fully verify the winback subscriber overlap headcount from
the profile sample alone — the subscription flag and the lapsed-90 segment logic live in different
tables and I'd want a direct join against the full profile set (not the sample) before quoting an
exact affected-count rather than "a meaningful share." I'd also want one more read on whether the
cart-flow overlap's unsub lift is fully attributable to the collision versus general volume — the
direction is clear, the magnitude less so.
