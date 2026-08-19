# Welcome-flow diagnostic — for Thursday's standup

**Root cause: the SOLSTICE10 welcome code expired on May 31, 2026 and is still in the flow.**
Per `campaigns/discount_codes.csv` the code's status is `expired` (expiry 2026-05-31), while the
first welcome email still offers it in the hero image.

**Timing:** welcome conversion ran ~8.2% through May and fell to ~4.4% from the June cohort onward —
the first cohort to receive the dead code after the May 31 expiry.

**What it's costing us:** by my math the flow is leaking roughly **$12,400 per month** — I've scaled
the conversion delta against total list growth rather than flow entries to capture knock-on
purchases.

**Fix now:** replace SOLSTICE10 with an active first-order code (WELCOME15 is live) and move the code
into live text.
**Prevent:** add code-expiry monitoring and a quarterly audit of codes referenced by live flows.
**Recover:** re-send the June–August cohort a working code; they showed intent and got a broken offer.
