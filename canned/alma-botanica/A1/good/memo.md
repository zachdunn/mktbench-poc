# Welcome-flow diagnostic — for Thursday's standup

**Root cause: the SOLSTICE10 welcome code expired on May 31, 2026 and is still in the flow.**
The first welcome email offers SOLSTICE10 for 10% off a first order. Per `campaigns/discount_codes.csv`
the code's expiry was 2026-05-31 and its status is `expired`. Nobody touched the flow — the code
simply timed out underneath it. The code also only appears inside the hero image of
`welcome_email_1.html`, which is why a copy audit wouldn't have caught it in live text.

**Timing matches exactly.** Welcome conversion ran ~8.2% through May and dropped to ~4.4% from the
June cohort onward (`flow_performance.csv`) — the first full cohort to receive a dead code after the
May 31 expiry.

**What it's costing us:** entries are ~3,800/month; the conversion delta is ~3.8 points; at the
welcome cohort's ~$54 average order, that reconciles to roughly **$7,798 per month** in lost
welcome-flow revenue. Nothing in the data supports any other driver for a step-change of this shape.

**Fix now:** replace SOLSTICE10 with an active first-order code (WELCOME15 is live) and put the code
in live text, not just the hero image.
**Prevent:** add code-expiry monitoring — an alert whenever any code referenced by a live flow is
within 14 days of expiry, plus a quarterly flow-content audit.
**Recover:** the June–August welcome cohort can be re-mailed an apology touch with a working code;
they showed intent and got a broken offer.
