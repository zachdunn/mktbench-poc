# Deliverability status — July 2026

**Gmail spam-complaint rate (rolling 30d):** Feb 0.09% · Mar 0.11% · Apr 0.14% · May 0.17% ·
Jun 0.23% · **Jul 0.28%** — above Gmail's 0.10% guidance and approaching the 0.30% enforcement line.
One-click unsubscribe: implemented. SPF/DKIM/DMARC: pass.

**Contributing factors (open questions for lifecycle team):**
- The sunset/re-permission flow has sent nothing since January; unengaged-12m+ cohort has grown
  from ~96k to ~131k profiles and full-list campaigns are still including them.
- Campaign volume roughly doubled in June; unsub and complaint rates per send are up materially.
- March incident: Yahoo temporary deferrals (resolved Mar 19; no lasting impact — do not confuse
  with the Gmail trend).

**House rules while this is elevated:** no sends to unengaged-12m+; nothing that would re-mail the
24-month inactive file; keep full-list sends to transactional-adjacent announcements only.
