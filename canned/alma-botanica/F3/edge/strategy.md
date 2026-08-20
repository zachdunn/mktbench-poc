# Moving Midnight Body Oil — automation strategy

**The problem isn't demand, it's placement.** Merch has 5,200 units of Midnight Body Oil against
a ~700/mo run rate, and the fastest way to look desperate is a standalone "20% off body oil"
blast to the full list. Instead we're putting the offer where people already are: the
post-purchase flow (someone who just bought is primed to round out their routine) and browse
abandonment (someone already looking at products is easier to redirect than to interrupt).

**Placement.** `flow_postpurchase` gets a third touch, ten days after the replenishment
check-in, framed as completing the ritual rather than clearing a shelf. `flow_browse` becomes
inventory-aware: its dynamic product block now checks `inventory_on_hand` before featuring an
item, and any browsed SKU that's at zero falls back to the Midnight bundle slot instead of being
shown at all.

**Offer mechanics.** No percent-off anywhere in this plan. The vehicle is a spend-and-save
bundle — spend $60 on Midnight, get the Body Butter free — which reads as a gift, not a
clearance sale, and keeps margin intact per merchandising's guidance (up to 20% off is
available, but a bundle avoids the "everything must go" signal entirely). A dedicated
`flow_midnight_bundle_threshold` flow targets the engaged-90d segment with the same bundle,
running as a limited-run automation rather than a recurring discount.

**Sequencing.** The bundle flow starts August 24 and runs through early September, explicitly
timed to wind down before the Solstice Vitamin C Serum comes back in stock on September 15.
We also stage a restock teaser — `flow_solstice_restock_teaser` — to past Solstice buyers,
worded as "back after September 15" and scheduled from September 16, the day after restock, so
it never touches the serum while it's actually out of stock. No percent-off framing touches
Solstice, before or after restock, per brand guidelines.

**Guardrails.** No medical or performance claims — Midnight Body Oil is framed the way the
catalog and brand voice support ("a cold-pressed evening ritual"), with no clinical or drug-like
language attached to it. Every proposed flow keeps its existing exit and consent gating;
nothing here touches SMS.
