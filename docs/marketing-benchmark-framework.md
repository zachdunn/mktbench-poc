# MarketingBench: Design Framework for a Klaviyo-Published Marketing Agent Benchmark

**Working document · August 2026**
**Reference model: Harvey's Legal Agent Benchmark (LAB), with cross-checks against Vals AI's vertical benchmarks and the Finance Agent Benchmark**

---

## 1. What Harvey actually built, and why it worked

Before designing the marketing analog, it's worth being precise about the anatomy of Harvey LAB, because its credibility comes from specific structural choices, not from the fact of publishing a benchmark.

**Task structure.** Every task has four parts: **Instructions** (a ~50-word directive framed as a partner-to-associate request), an **Environment** (a closed universe of matter files, templates, and communications the agent must navigate), an expected **Output** (reviewable work product — a memo, an analysis), and **Verification** (an expert-written rubric). ~1,670 tasks across 24 practice areas, graded against 75,000+ rubric criteria.

**Task sourcing.** Tasks were decomposed from real client matters by practicing lawyers — not invented by researchers. This is the single biggest credibility driver: the tasks smell like real work because they are real work, sanitized.

**Grading.** Rubrics decompose each deliverable into atomic, binary pass/fail criteria (facts, citations, calculations, conclusions, formatting, recommended actions). Scoring is **all-pass**: miss one criterion, fail the task — justified by how high-stakes legal work is actually reviewed. LLM-as-judge applies the criteria; each criterion links to specific files, enabling per-criterion reward signals.

**Positioning.** Open-sourced (MIT), launched deliberately *without* a leaderboard, with an explicit invitation to lawyers, firms, labs, and researchers to audit and contribute. Anthropic, OpenAI, Google DeepMind, and Stanford groups were named as research partners at launch. Vals AI now runs it as an industry-partner benchmark (51 models tested), giving Harvey neutral third-party grading.

**Why it worked strategically.** Harvey converted its proprietary asset (access to real legal workflows and expert reviewers) into public infrastructure. Labs now optimize against Harvey's definition of "good legal work." That's the play Klaviyo would be replicating: whoever defines the eval defines the standard for what a competent AI marketer is.

**The white space is real.** Vals AI's vertical lineup covers legal, finance, healthcare, coding, and web search. There is no credible marketing or lifecycle-marketing benchmark from anyone with real domain authority. Academic efforts (e.g., MerchantBench for e-commerce operations coherence) exist but nothing anchored in real practitioner workflows and real customer-data environments. Klaviyo is arguably the *only* company positioned to build one: it has the workflow surface, the aggregate performance data, the agency ecosystem to validate tasks, and — since the Composer/Customer Agent launch — a strategic reason to define the standard.

---

## 2. The central design problem: marketing is not law

The naive move is to copy LAB's structure directly. The structure mostly transfers, but one assumption does not, and it's the assumption everything else in LAB rests on:

> **In law, expert consensus is ground truth. In marketing, it isn't — the market is.**

Two excellent lifecycle marketers given the same brief will produce different campaigns, and both can be right. The "true" score of a campaign is incremental revenue, which is only observable in production, is confounded by everything else the brand is doing, and is noisy even in a clean A/B test. A marketing benchmark that pretends expert rubrics fully capture quality will be dismissed by practitioners; one that only scores fuzzy "quality" will be dismissed by researchers.

The resolution is to recognize that marketing work decomposes into layers with very different verifiability, and to grade each layer the way it can actually be graded:

| Layer | Nature | Verifiability | Grading approach |
|---|---|---|---|
| **L1 — Data & factual correctness** | Right numbers pulled, right products referenced, right past-performance facts cited | Fully objective | Binary criteria, all-pass |
| **L2 — Execution correctness** | Segment logic, flow triggers/filters, exclusions, send-time windows, UTM/link hygiene, discount codes, rendering | Fully objective | Binary criteria, all-pass |
| **L3 — Compliance & safety** | CAN-SPAM, TCPA/SMS consent & quiet hours, GDPR/CASL, unsubscribe handling, claims substantiation, price/promo accuracy | Fully objective | Binary criteria, all-pass, zero tolerance |
| **L4 — Strategic judgment** | Prioritization, audience choice, offer strategy, test design, calendar logic | Partially objective — experts converge on *failure modes* even when they diverge on ideal answers | Expert rubric: "a competent senior marketer would never…" criteria, mostly binary |
| **L5 — Craft & brand voice** | Copy quality, subject lines, adherence to brand guidelines, creative brief quality | Subjective but constrainable | Rubric against in-environment brand guidelines + calibrated LLM judge; optionally comparative/preference grading |
| **L6 — Outcomes** | Did it actually perform? | Only observable in market | Backtesting against historical realized results (see §6) — Klaviyo's unique unlock, phase 2 |

A key insight hiding in L4: much of "marketing judgment" becomes objectively gradable if you write criteria as **known-necessary elements and known failure modes** rather than as ideal answers. "Did the winback campaign exclude customers who purchased in the last 30 days?" is binary. "Did the SMS send respect quiet hours for the subscriber's timezone?" is binary. "Is this the *best possible* winback strategy?" is unanswerable — so don't ask it. Harvey's rubrics quietly do the same thing (they grade what must be present, not what perfection looks like), which is why the model transfers better than it first appears.

**Scoring implication — modify all-pass.** Harvey's pure all-pass standard maps to legal review culture. Marketing review culture is different: a campaign with a broken discount code or a compliance miss is a failure no matter how good the copy is, but among shippable campaigns there are meaningful quality gradations. The natural adaptation is **two-tier scoring**:

- **Shippable rate** — all-pass across L1–L3 gate criteria (+ hard L4 failure modes). Binary. This is the headline metric and it will be brutally low at first, which is good for credibility.
- **Quality score** — graded performance on L4–L5 criteria, reported *conditional on shippable*. This preserves the "one error kills the task" realism without flattening all quality signal into pass/fail.

---

## 3. The questions that need answering

Organized by decision area. The bolded ones are load-bearing — get these wrong and the benchmark either lacks credibility or creates strategic problems.

### 3.1 Purpose & positioning

1. **What is the primary audience: AI labs (shape frontier model training), practitioners/buyers (shape the market's definition of a competent AI marketer), or press/analysts (category leadership)?** Harvey targeted all three but sequenced labs first (research partners at launch, leaderboard later). The audience choice drives everything downstream — task difficulty, open-sourcing, leaderboard timing.
2. **Does Klaviyo's own Composer appear on the benchmark at launch, and what happens if it doesn't win?** Harvey has the same exposure and handled it by launching the dataset before any leaderboard. A benchmark where the publisher's product conveniently wins is a press release, not a benchmark. Options: launch dataset-first (Harvey's move), commit publicly to publishing Composer's scores whatever they are, or scope v1 to foundation models only.
3. **Who grades — Klaviyo or a neutral third party?** Harvey partnered with Vals AI for independent model testing. A Klaviyo × Vals (or academic lab) partnership is probably table stakes for the leaderboard phase.
4. Naming/brand collision: Klaviyo already publishes widely-cited *performance* benchmarks (industry open rates, conversion rates). The agent benchmark must be clearly distinguished — it measures *AI capability on marketing work*, not *marketing performance norms*. This is also an asset: the existing benchmark data can calibrate the synthetic environments (§4).
5. What's the relationship to the "autonomous B2C CRM" narrative? The benchmark implicitly argues "this work is delegable to agents and here is how to measure whether an agent is ready" — which is exactly the Composer sales motion. Decide how explicit to make that link; too explicit undermines neutrality.

### 3.2 Scope: what counts as "marketing work"

6. **Which marketing is in scope for v1?** Recommendation: retention/lifecycle marketing for consumer brands (email, SMS, push, segmentation, flows, campaign strategy) — Klaviyo's authority zone. Excluding paid acquisition, SEO, and brand strategy in v1 is defensible and keeps the environment closed-universe. Harvey covered 24 practice areas at launch, but they had years of workflow data; 6–10 well-chosen task categories beat 24 thin ones.
7. Single-shot deliverables vs. longitudinal coherence? Real marketing is a calendar, not a task — decisions compound (frequency/fatigue, list health, promo cadence). MerchantBench-style multi-week simulated operation is powerful but hard to grade. Recommendation: v1 tasks are discrete (Harvey-style); hold longitudinal simulation for v2.
8. Human-in-the-loop assumed? Composer itself requires human approval before launch. Does the benchmark grade the *draft-for-approval* (deliverable quality) or *autonomous execution*? Grading the deliverable is cleaner and matches current product reality.

### 3.3 Environment & data

9. **Real (anonymized) brand data or synthetic brands?** Legal matters can be sanitized; customer PII at scale cannot, practically. Recommendation: fully **synthetic brand universes** — fictional DTC brands with statistically realistic data, calibrated against Klaviyo's aggregate benchmark data so that open rates, AOVs, purchase cycles, and list-churn patterns are true-to-life. This is a capability almost no one else has: synthetic data that's *distributionally honest* because it's fit to the largest real dataset in the industry.
10. How many brand universes, and how varied? Difficulty and correct answers change with vertical (beauty ≠ supplements ≠ apparel), brand size (10k list ≠ 2M list), and maturity (no flows ≠ 113 colliding automations — the AS Beauty story from the Composer beta is itself a perfect benchmark task). Suggest 4–6 universes spanning vertical × size × maturity.
11. **What does the closed universe contain?** The analog of Harvey's "matter files": product catalog with margins and inventory; 18–24 months of customer profiles, events, and order history; existing segments, flows, and campaign history *with realized performance*; brand + voice guidelines; deliverability/list-health stats; promo calendar and revenue targets; stakeholder communications (the founder's Slack message, the merchandiser's email) that carry constraints the agent must discover. Buried, cross-document constraints — Harvey's "peripheral files" trick — are what separate agentic evaluation from Q&A.
12. What tools does the agent get? Options range from file-system-only (Harvey's model: read files, produce documents) to a mock-Klaviyo API (query segments, build flows as structured objects). A structured mock API makes L2 grading (segment logic, flow definitions) machine-checkable rather than judge-dependent — a big grading-cost win. But it risks looking Klaviyo-proprietary; a neutral schema (documented, open) mitigates.
13. Contamination strategy: fully open dataset (Harvey/MIT) risks training contamination; fully private (Vals CorpFin model) limits ecosystem adoption. Common resolution: open dev set + private held-out set, refreshed periodically. The Finance Agent Benchmark's approach (only post-2024 documents) doesn't apply since our data is synthetic — a genuine advantage: **synthetic universes can be regenerated on demand**, making refresh cheap.

### 3.4 Task sourcing & validation

14. **Who decomposes real work into tasks?** Harvey's answer was practicing lawyers; the analog is senior lifecycle marketers and — critically — **Klaviyo's agency partner ecosystem**, who play the role law firms play for Harvey: they see hundreds of accounts, they know what briefs actually look like, and their sign-off is the practitioner credibility signal. Also a distribution channel: agencies co-authoring benchmark tasks become invested evangelists.
15. What's the instruction register? Harvey's partner-to-associate framing maps to "ecomm director / founder to lifecycle marketing manager," ~50 words, realistically underspecified ("Black Friday is in 6 weeks and our list has gone cold — what are we doing about it?"). Underspecification is a feature: discovering the real requirements from the environment is part of the eval.
16. Expert requirements and inter-rater checks: Finance Agent Benchmark used 2–3+ years experience with peer review and multi-stage validation. Set an explicit bar (e.g., 5+ years lifecycle marketing or agency leadership, portfolio of managed revenue) and require every task's rubric to be independently validated by a second expert. Report inter-rater agreement in the methodology paper.

### 3.5 Grading mechanics

17. **Rubric authorship discipline:** every criterion atomic, binary, and linked to specific environment files (Harvey's per-criterion traceability). Target order-of-magnitude: 30–60 criteria per task (Harvey's flagship example: 57 criteria across 9 issues).
18. LLM-judge calibration: which judge model, how audited? Standard answer: human experts grade a stratified sample; report judge-vs-human agreement per criterion type. Expect L5 (craft) agreement to be weakest — consider human-only or ensemble judging for that layer, or comparative (pairwise) judging which is more reliable than absolute scoring for copy quality.
19. How is brand-voice adherence graded without taste wars? Ground it in the environment: the brand guidelines document *is* the rubric source ("never uses discount-led language," "reading level ≤ grade 7," "forbidden words list"). Voice becomes compliance-with-a-spec, which is gradable; residual aesthetic quality goes to pairwise expert preference on a sample.
20. What's the human baseline? Finance Agent reported expert time (16.8 min/task) vs. model time. Commission a set of human lifecycle marketers to complete tasks under the same environment; report human shippable-rate and time. A benchmark where humans also fail some gates is *more* credible, not less.

### 3.6 Metrics & reporting

21. Headline metrics: **shippable rate** (all-pass on gates, reported pass^1/pass^4, by program and overall), **quality score conditional on shippable**, criteria-level diagnostics (which failure modes dominate), and **cost/latency vs. human baseline**. Resist a single blended number at launch. When a composite does come: **weight each program by its share of attributed owned-channel revenue across Klaviyo's platform** — the direct analog of Vals' GDP-weighted cross-domain index, except the weights come from Klaviyo's actual observed economy of this work, which no one else can measure or credibly dispute. Abandonment recovery counts for more than birthday flows because it *is* more of the economy.
22. Leaderboard timing: Harvey deliberately launched without one. Same recommendation — dataset + methodology + baseline results on frontier models first; leaderboard once submission-normalization standards exist (what harness, what tools, what budget).

### 3.7 Governance, maintenance, risk

23. Who owns task additions and disputes? An advisory board (agencies + brands + a lab + an academic) is cheap insurance against "Klaviyo grades its own homework."
24. Refresh cadence and versioning (marketing norms drift: SMS regulations, deliverability rules like Gmail/Yahoo sender requirements, channel mix). Version the benchmark; date-stamp compliance criteria.
25. Legal review of compliance-layer criteria (TCPA especially — you're effectively publishing an opinionated spec of lawful SMS marketing).
26. Failure-mode risk: the benchmark reveals that *all* agents, including Composer, are far from shippable on hard tasks. Decide in advance that this is the story ("the work is harder than the hype — here's the measuring stick"), which is exactly how Harvey and Vals played low scores (best finance agent: 46.8%).

---

## 4. Proposed task taxonomy (v1)

Eight categories, each decomposed from real briefs, each with the four-part Harvey structure. Illustrative gate (G) and quality (Q) criteria shown.

**1. Account audit & opportunity diagnosis** — "Audit this account and tell me the top 3 revenue opportunities." The Composer flagship motion; also the AS Beauty flow-collision story as a task archetype. *G: correctly identifies the broken/colliding flows planted in the environment; revenue estimates use actual account data. Q: prioritization matches expert consensus ranking; effort/impact framing.*

**2. Segmentation & audience building** — "Build the audience for the VIP early-access drop." *G: segment logic exactly matches the brief's constraints (spend threshold, engagement recency, exclusions); correct audience count derivable from the data; suppressions applied (recent purchasers, unengaged, SMS-non-consented). Q: enrichment choices, edge-case handling.*

**3. Campaign strategy & planning** — "Plan the 6-week Black Friday runway." *G: calendar respects the promo constraints buried in stakeholder emails; frequency caps honored; list-warming accounted for given the deliverability stats in the environment. Q: offer architecture, channel mix rationale, test plan.*

**4. Flow/automation design** — "Rebuild the abandoned-cart flow; it's underperforming." *G: trigger/filter logic correct as structured output; no collisions with existing flows in the environment; branch conditions valid; SMS steps consent-gated and quiet-hour-safe. Q: timing/branching strategy vs. expert rubric.*

**5. Creative & copy** — "Write the winback email and 2 SMS variants." *G: brand-guideline compliance (voice spec, forbidden claims, required legal footer, link/UTM hygiene, char limits); factual product claims match catalog; offer terms match what merchandising approved. Q: pairwise expert/judge preference; subject-line craft.*

**6. Experimentation & measurement** — "Design the test to settle whether plain-text outperforms designed emails for us." *G: valid test design (randomization unit, sample size vs. the list size actually available, guardrail metrics); no peeking/multiple-comparison traps. Q: hypothesis quality, decision rule.*

**7. Analytics & reporting** — "What drove the Q2 revenue dip? Board slide by Friday." *G: numbers reconcile with the environment's event data; attribution claims don't exceed what the data supports; correct handling of the deliverability incident planted in month 2. Q: narrative quality, recommended actions.*

**8. Compliance & deliverability** — "Legal flagged our SMS program; review and fix." *G: every planted violation found (consent gaps, quiet-hour sends, missing opt-out language, sender-requirement breaches); remediations correct. Q: process recommendations.*

Difficulty scales within each category the way Finance Agent Benchmark's does (52% easy / 27% medium / 21% hard is a sane starting distribution), primarily by how deeply constraints are buried across environment files and how much cross-document reconciliation is required.

## 4a. The reporting taxonomy: programs, not just skills

The eight categories above are a **skill** taxonomy — how eval designers organize work. Harvey's 24 practice areas are a **jobs** taxonomy — delegable units of work a buyer hires for ("contract review"). Public results should be reported on the jobs axis, because "Model A is 61% shippable on abandonment recovery but 19% on promotional planning" is the sentence a CMO can act on. This is a tagging problem, not a redesign: every task already lives in some program, so tasks carry a two-axis label (skill × program) and the program axis is the primary public rollup.

**The nine programs** (the practice-area equivalent, matching how lifecycle marketing divides into ownable jobs — and how Klaviyo's flow templates and Composer's opportunity categories already carve the space):

1. **Welcome & onboarding** — new-subscriber and new-customer journeys
2. **Abandonment recovery** — cart, browse, checkout
3. **Post-purchase & retention** — care sequences, replenishment, cross-sell, warranty/registration
4. **Winback & reactivation** — lapsed-customer programs
5. **Newsletter & editorial program** — recurring content-led sends; distinct rhythm (no single conversion event, fatigue-managed)
6. **Promotional & seasonal campaigns** — BFCM, launches, sales windows
7. **Loyalty, VIP & subscription management**
8. **List growth, consent & hygiene** — signup, preference centers, sunset/re-permission, deliverability stewardship
9. **Measurement & reporting** — attribution, performance narratives, test programs

Channel (email/SMS/push) is a tag, not a category. A second dimension worth tagging: **mode** — build new vs. operate/maintain ongoing vs. diagnose & repair. Maintaining a healthy newsletter program is different work from building one, and agents will show different profiles across modes.

**Delegation readiness.** Per program, the composite of shippable pass^4 + collateral damage + escalation behavior rolls into transparent tiers — *ready with review / narrow scope only / not ready* — the buyer-legible output that maps benchmark results onto what an agent can actually be trusted to own. Tier thresholds must be published and mechanical, or the tiers read as editorial.

**Sampling implication:** v1's 300–500 tasks are sampled to program balance, and rubric authorship recruits at least one expert per program, the way Harvey staffs per practice area. The pilot's task set covers ~5 of 9 programs, which is sufficient for proving the grading stack but not for program-level claims.

---

## 5. What the eval criteria design looks like in practice

A worked miniature, Harvey-style. Task: *"Our winback flow hasn't been touched in a year and BFCM is coming. Rework it — audience, structure, and the first email."* (Environment: 24 months of data; winback flow currently targets 90-day lapsed including recent SMS purchasers; brand guidelines forbid %-off framing for the hero product line; a founder email in the environment mentions a coming price increase.)

Gate criteria (all-pass, binary, file-linked):
- Audience excludes customers with a purchase in the last 30 days *(links: segment definition, order events)*
- Audience excludes suppressed/unengaged-over-12-months profiles *(deliverability doc)*
- SMS touchpoints restricted to consented profiles; sends within quiet hours *(consent fields, compliance doc)*
- Copy contains no %-off framing for the hero line *(brand guidelines §4)*
- Price-increase messaging consistent with the founder's email — does not pre-announce the unannounced increase *(stakeholder email — the buried constraint)*
- Revenue-at-stake estimate reconciles with lapsed-cohort AOV × cohort size from the actual data *(events export)*
- Required footer, functioning unsubscribe, correct UTMs *(templates)*

Quality criteria (scored, expert-rubric):
- Flow structure includes an incentive-escalation branch gated on non-engagement (expert-consensus best practice for this vertical)
- Timing rationale references the brand's actual median repurchase cycle (computable from data) rather than generic heuristics
- Subject lines: pairwise preference vs. reference set, judged against voice spec

Note what happened: nine criteria, seven of them binary and machine-checkable given a structured environment, one requiring data computation, one requiring calibrated preference judgment. That ratio — mostly-verifiable with a thin subjective layer — is what makes this domain benchmarkable at all, and the two-tier scoring makes the subjective layer honest instead of hidden inside a pass/fail.

---

## 6. The phase-2 unlock nobody else can build: outcome-grounded evaluation

Everything above is Harvey's playbook adapted. This section is where Klaviyo can exceed it.

Harvey can never know whether the memo *worked* — legal outcomes are unobservable at benchmark scale. Klaviyo observes realized outcomes for billions of sends. That enables two things no other benchmark publisher can do:

**Rubric validation.** Klaviyo can empirically test whether its L4 "expert judgment" criteria actually predict performance in the historical record (do campaigns that satisfy criterion X reliably outperform matched campaigns that don't?). Criteria that don't predict anything get cut. This converts the benchmark's weakest layer (expert opinion) into its strongest claim: *these criteria are validated against real-world outcomes at scale.* No legal or finance benchmark can say that sentence.

**Backtest-style outcome tasks.** A held-out task family where the agent chooses among decisions whose outcomes are already known (real, anonymized, aggregated A/B tests and campaign variants): "here are two subject lines / send-time strategies / audience definitions that actually ran — predict the winner and by how much." Noisy per-item, informative in aggregate, impossible to contaminate if drawn from private data, and it directly measures the thing practitioners actually care about. Caveats to handle honestly: survivorship and selection effects in which tests ran, winner noise on small samples (grade only tests with significant results), and privacy review on task construction.

Simulated-customer evaluation (LLM personas "receiving" the campaign) is the trendy third option; recommend against relying on it — validity is unproven and it would be the first thing critics attack. At most, an exploratory appendix.

---

## 7. Suggested sequencing

**Phase 0 — Design partner recruitment.** 2–3 agencies + 2–3 in-house lifecycle leaders as task decomposers and rubric validators; a neutral eval partner conversation (Vals or academic) early, since their normalization standards shape the harness.

**Phase 1 — Pilot.** One synthetic brand universe, 2 task categories (audit + flow design are the most gate-heavy, hence cheapest to grade), ~40 tasks, frontier-model baselines, human-marketer baseline on a subsample. Goal: prove the grading stack (judge-vs-human agreement numbers) before scaling.

**Phase 2 — v1 launch.** 4–6 universes, 8 categories, 300–500 tasks, open dev set + private held-out set, methodology paper, no leaderboard yet (Harvey's sequencing), named research partners.

**Phase 3 — Leaderboard + outcome layer.** Third-party-run leaderboard with submission normalization; outcome-validated rubrics and backtest task family as the differentiating v2 announcement.

---

## 8. Open questions to resolve next

The shortlist that most needs a decision or more digging, in rough priority order: (1) Composer's relationship to the leaderboard and the grade-your-own-homework problem; (2) synthetic-universe generation approach and whether Klaviyo's aggregate data can be used for calibration under its data-use terms; (3) neutral grading partner; (4) mock-API vs. file-system environment (determines how much of L2 is machine-checkable); (5) agency partner selection and incentives; (6) legal review of publishing compliance criteria; (7) naming, given the existing Klaviyo performance benchmarks.

---

## Appendix: Reference summaries

**Harvey LAB** — 1,671 tasks, 24 practice areas, 75k+ binary criteria, all-pass grading, closed-universe environments from real matters, MIT-licensed with open harness, launched dataset-first without a leaderboard; now independently run on Vals (51 models).

**Vals AI** — the de facto neutral home for vertical benchmarks (legal, finance, healthcare, web search); mixes open and private benchmarks; runs industry-partner benchmarks (Harvey's) and publishes a GDP-weighted cross-domain index. No marketing benchmark exists in its lineup.

**Finance Agent Benchmark** — 537 expert-written tasks (bulge-bracket/HF/PE authors, 2–3+ yrs experience, peer-reviewed), 9 categories across 3 difficulty tiers, ReAct harness with real tools (EDGAR, search), rubric + LLM-judge grading with contradiction detection, human time baseline (16.8 min vs 3.1), best model 46.8% — low scores framed as the finding.

**Klaviyo agent context** — Composer (public beta): audits accounts, surfaces ranked revenue opportunities, builds cross-channel campaigns, human approval gate. Customer Agent: service interactions across channels. Positioning: agents acting on unified CRM context. The benchmark would be the measurement layer for exactly this class of work.
