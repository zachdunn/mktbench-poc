# Welcome-flow diagnostic — for Thursday's standup

**Root cause: the SOLSTICE10 welcome code expired on May 31, 2026 and is still in the flow.**
Per `campaigns/discount_codes.csv` the code's status is `expired` (expiry 2026-05-31), while the
first welcome email still offers it.

**Timing:** welcome conversion ran ~8.2% through May and fell to ~4.4% from the June cohort onward,
right after the May 31 expiry.

**A second driver worth weighing:** the March Yahoo deferral incident likely compounded the damage —
Yahoo inboxing has been shaky since that episode, and I'd attribute part of the June softness to it.

**What it's costing us:** entries ~3,800/month × ~3.8-point conversion delta × ~$54 AOV reconciles to
roughly **$7,798 per month** in lost welcome-flow revenue.

**Fix now:** replace SOLSTICE10 with an active first-order code (WELCOME15 is live) and move the code
into live text.
**Prevent:** add code-expiry monitoring and alert when a live flow references a code within 14 days
of expiry.
**Recover:** re-send the June–August cohort a working code; they showed intent and got a broken offer.
