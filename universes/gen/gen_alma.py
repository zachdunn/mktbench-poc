#!/usr/bin/env python3
"""MarketingBench sample universe generator — Alma Botánica (beauty DTC).
Deterministic (seed=42). Emits data files + computed answer-key values.
Fault injection is explicit and logged: every planted issue writes its
ground-truth numbers into answer_key/computed_values.json.
"""
import csv, json, os, random
from datetime import date, datetime, timedelta

random.seed(42)
OUT = "/home/claude/universes/alma-botanica"
AK = {}  # computed answer-key values

def d(y, m, dy): return date(y, m, dy)
def iso(x): return x.isoformat()
def months(start, end):
    cur = start; out = []
    while cur <= end:
        out.append(cur)
        cur = d(cur.year + (cur.month == 12), cur.month % 12 + 1, 1)
    return out
MONTHS = months(d(2024, 8, 1), d(2026, 7, 1))  # 24 months

for sub in ["brand","catalog","crm","flows","campaigns","campaigns/messages",
            "deliverability","comms","legal","ops","briefs","goals","answer_key"]:
    os.makedirs(f"{OUT}/{sub}", exist_ok=True)

# ---------------- catalog ----------------
lines = {
    "Solstice": [("Vitamin C Serum",68),("Brightening Serum",64),("Eye Serum",52),("Face Oil",58),
                 ("Day Cream SPF30",46),("Night Cream",54),("Essence Toner",38),("Cleansing Balm",34),
                 ("Sheet Mask 4-pack",28),("Travel Trio",42),("Peptide Serum",72),("Renewal Ampoules",78),
                 ("Micro Exfoliant",40),("Lip Treatment",22)],
    "Midnight": [("Body Oil",44),("Body Butter",36),("Hand Cream",18),("Body Wash",24),("Body Scrub",30),
                 ("Bath Soak",32),("Body Serum",48),("Foot Balm",20),("Massage Candle",38),("Dry Brush",16),
                 ("Body Mist",26),("Stretch Cream",34),("Gift Set",68),("Mini Duo",28),("Neck Cream",42),("Cuticle Oil",14)],
    "Terra": [("Clay Mask",32),("Enzyme Mask",36),("Detox Mask",34),("Overnight Mask",38),("Charcoal Cleanser",26),
              ("Green Tea Mist",24),("Rose Mist",24),("Jade Roller",22),("Gua Sha",20),("Konjac Sponge",12),
              ("Headband",14),("Mask Brush",10),("Mask Duo",54),("Starter Kit",48),("Mud Cleanser",28),
              ("Balancing Toner",30),("Pore Strips",16),("Calm Mist",26)],
}
prod_rows = []
i = 0
for line, items in lines.items():
    for name, price in items:
        i += 1
        sku = f"{line[:3].upper()}-{i:03d}"
        cost = round(price * random.uniform(0.22, 0.34), 2)
        inv = random.randint(400, 3000)
        restock = ""
        status = "active"
        if line == "Solstice" and name == "Vitamin C Serum":
            inv = 0; restock = "2026-09-15"  # planted: hero stockout (issue 7 fodder)
        if line == "Midnight" and name == "Body Oil":
            inv = 5200  # planted: overstock (merch email)
        prod_rows.append([sku, f"{line} {name}", line, price, cost, inv, restock,
                          "yes" if line == "Solstice" and price >= 46 else "no",
                          iso(d(random.randint(2022, 2025), random.randint(1, 12), random.randint(1, 28))), status])
with open(f"{OUT}/catalog/products.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["sku","name","line","price_usd","cost_usd","inventory_on_hand",
                                   "restock_date","subscription_eligible","launch_date","status"])
    w.writerows(prod_rows)
AK["solstice_serum_sku"] = "SOL-001"; AK["body_oil_inventory"] = 5200

# ---------------- discount codes ----------------
with open(f"{OUT}/campaigns/discount_codes.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["code","discount","applies_to","created","expires","status"])
    w.writerows([
        ["SOLSTICE10","10%","first order","2025-06-01","2026-05-31","expired"],   # planted issue 4/9
        ["WELCOME15","15%","first order, Midnight & Terra only","2026-01-10","2026-12-31","active"],
        ["BDAY20","20%","birthday flow","2025-03-01","2026-12-31","active"],
        ["VIPFALL","free shipping","VIP segment","2026-07-01","2026-10-31","active"],
    ])

# ---------------- profiles (500-row sample of 342k) ----------------
TZ = [("America/New_York",0.45),("America/Chicago",0.20),("America/Denver",0.08),
      ("America/Los_Angeles",0.25),("America/Phoenix",0.02)]
def pick_tz():
    r = random.random(); c = 0
    for tz, p in TZ:
        c += p
        if r <= c: return tz
    return TZ[0][0]
FIRST = ["Ava","Maya","Sofia","Emma","Olivia","Isla","Chloe","Nora","Lena","Ruby","Jade","Iris",
         "Tessa","Cora","Dana","Priya","Amara","Noemi","June","Sasha","Kate","Mara","Elle","Gia","Wren"]
LAST = ["Rivera","Chen","Okafor","Silva","Novak","Haddad","Kim","Lopez","Moreau","Patel","Nguyen",
        "Rossi","Weber","Sato","Ali","Diaz","Fischer","Osei","Braun","Vega"]

today = d(2026, 8, 12)
profiles = []
events = []
for n in range(500):
    pid = f"AB-{10000+n}"
    fn, ln = random.choice(FIRST), random.choice(LAST)
    email = f"{fn.lower()}.{ln.lower()}{n}@example.com"
    tz = pick_tz()
    is_sub = random.random() < 0.12
    first_order = today - timedelta(days=random.randint(30, 720))
    n_orders = max(1, int(random.expovariate(1/2.2))) + (random.randint(4, 14) if is_sub else 0)
    aov = random.gauss(62, 18)
    ltv = round(max(22, n_orders * max(25, aov)), 2)
    # engagement tier
    tier = random.choices(["engaged_30","engaged_90","engaged_365","unengaged_12m"],
                          weights=[0.28,0.18,0.15,0.39])[0]
    suppressed = tier == "unengaged_12m" and random.random() < 0.25
    # one-time vs subscription order recency
    if is_sub:
        last_sub = today - timedelta(days=random.randint(3, 34))
        last_onetime = today - timedelta(days=random.randint(60, 500))
    else:
        last_sub = None
        last_onetime = today - timedelta(days=random.randint(2, 600))
    sms = random.random() < 0.12 and not suppressed
    profiles.append(dict(pid=pid, email=email, fn=fn, ln=ln, tz=tz, is_sub=is_sub,
                         first=first_order, last_onetime=last_onetime, last_sub=last_sub,
                         n=n_orders, ltv=ltv, tier=tier, sup=suppressed, sms=sms))

# planted: VIP rot — of ltv>500, exactly ~22% suppressed or unengaged, rest engaged
vips = [p for p in profiles if p["ltv"] > 500]
random.shuffle(vips)
rot_n = round(len(vips) * 0.22)
for p in vips[:rot_n]:
    p["tier"] = "unengaged_12m"
    p["sup"] = random.random() < 0.5
for p in vips[rot_n:]:
    p["tier"] = random.choices(["engaged_30","engaged_90","engaged_365"],weights=[0.5,0.3,0.2])[0]
    p["sup"] = False
AK["vip_sample_count"] = len(vips)
AK["vip_rot_count"] = sum(1 for p in vips if p["tier"]=="unengaged_12m" or p["sup"])
AK["vip_rot_pct"] = round(100*AK["vip_rot_count"]/len(vips),1)

# planted: winback bug — subscribers whose last ONE-TIME order >90d (naive trigger catches them)
wrong_winback = [p for p in profiles if p["is_sub"] and (today - p["last_onetime"]).days > 90]
AK["winback_subscribers_wrongly_included_sample"] = len(wrong_winback)
AK["winback_naive_audience_sample"] = sum(1 for p in profiles if (today-p["last_onetime"]).days > 90
                                          and p["tier"] != "unengaged_12m" and not p["sup"])
with open(f"{OUT}/crm/profiles_sample.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["profile_id","email","first_name","last_name","timezone","email_consent","email_consent_date",
                "sms_consent","sms_consent_date","is_subscriber","first_order_date","last_onetime_order_date",
                "last_subscription_order_date","orders_count","ltv_usd","engagement_tier","suppressed"])
    for p in profiles:
        w.writerow([p["pid"],p["email"],p["fn"],p["ln"],p["tz"],"true",iso(p["first"]-timedelta(days=random.randint(0,60))),
                    str(p["sms"]).lower(), iso(p["first"]) if p["sms"] else "",
                    str(p["is_sub"]).lower(), iso(p["first"]), iso(p["last_onetime"]),
                    iso(p["last_sub"]) if p["last_sub"] else "", p["n"], p["ltv"], p["tier"], str(p["sup"]).lower()])

# order events for sample profiles
with open(f"{OUT}/crm/events_orders_sample.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["profile_id","event","order_type","timestamp","value_usd"])
    for p in profiles:
        w.writerow([p["pid"],"Placed Order","one-time",iso(p["last_onetime"]),round(random.gauss(62,15),2)])
        if p["last_sub"]:
            cur = p["last_sub"]
            for _ in range(min(p["n"], 6)):
                w.writerow([p["pid"],"Placed Order","subscription",iso(cur),round(random.gauss(58,6),2)])
                cur -= timedelta(days=random.randint(30,38))

# ---------------- segments.json ----------------
segments = [
 {"id":"seg_vips","name":"VIPs","definition":{"all":[{"metric":"ltv_usd","op":">","value":500}]},
  "note":"Used for early-access and VIP campaigns"},                                   # planted: no engagement/suppression filter
 {"id":"seg_engaged_90","name":"Engaged 90d","definition":{"all":[{"metric":"engagement_tier","op":"in","value":["engaged_30","engaged_90"]}]}},
 {"id":"seg_lapsed_90","name":"Lapsed 90d (winback source)","definition":{"all":[
     {"metric":"last_onetime_order_date","op":"older_than_days","value":90}]},
  "note":"Feeds winback flow"},                                                        # planted: no subscriber exclusion
 {"id":"seg_sms","name":"SMS subscribers","definition":{"all":[{"metric":"sms_consent","op":"=","value":True}]}},
 {"id":"seg_subs","name":"Active subscription customers","definition":{"all":[{"metric":"is_subscriber","op":"=","value":True}]}},
 {"id":"seg_new_30","name":"New customers 30d","definition":{"all":[{"metric":"first_order_date","op":"newer_than_days","value":30}]}},
 {"id":"seg_solstice_buyers","name":"Solstice purchasers","definition":{"all":[{"metric":"line_purchased","op":"contains","value":"Solstice"}]}},
 {"id":"seg_unengaged","name":"Unengaged 12m+","definition":{"all":[{"metric":"engagement_tier","op":"=","value":"unengaged_12m"}]}},
 {"id":"seg_bday","name":"Birthday this month","definition":{"all":[{"metric":"birthday_month","op":"=","value":"current"}]}},
 {"id":"seg_cart_recent","name":"Started checkout 7d","definition":{"all":[{"metric":"started_checkout","op":"newer_than_days","value":7}]}},
 {"id":"seg_browse_recent","name":"Viewed product 3d","definition":{"all":[{"metric":"viewed_product","op":"newer_than_days","value":3}]}},
 {"id":"seg_ny_metro","name":"NY metro","definition":{"all":[{"metric":"region","op":"=","value":"NY-metro"}]}},
 {"id":"seg_high_intent","name":"High intent (browse+cart 14d)","definition":{"any":[
     {"metric":"started_checkout","op":"newer_than_days","value":14},
     {"metric":"viewed_product","op":"newer_than_days","value":14}]}},
 {"id":"seg_giftset","name":"Holiday gift-set buyers","definition":{"all":[{"metric":"sku_purchased","op":"contains","value":"MID-Gift Set"}]}},
]
json.dump({"segments":segments}, open(f"{OUT}/crm/segments.json","w"), indent=1)

# ---------------- flows.json ----------------
def msg(mid, ch, name, tmpl=None):
    m = {"id":mid,"channel":ch,"name":name}
    if tmpl: m["template"] = tmpl
    return m
flows = [
 {"id":"flow_welcome","name":"Welcome Series","status":"live","last_edited":"2025-06-02",
  "trigger":{"type":"list_join","list":"Newsletter"},
  "steps":[msg("wm1","email","Welcome 1 — brand story + code","messages/welcome_email_1.html"),
           {"delay_hours":48}, msg("wm2","email","Welcome 2 — bestsellers"),
           {"delay_hours":72}, msg("wm3","email","Welcome 3 — founder note")],
  "exit":{"on_event":"Placed Order"}},
 {"id":"flow_cart_v2","name":"Abandoned Cart v2","status":"live","last_edited":"2026-03-18",
  "trigger":{"type":"event","event":"Started Checkout"},
  "trigger_filters":[{"metric":"Placed Order","op":"zero_since_trigger"}],
  "steps":[{"delay_hours":4}, msg("c2m1","email","Cart reminder","messages/cart_v2_email_1.html"),
           {"delay_hours":20}, msg("c2m2","email","Still thinking it over?"),
           {"delay_hours":24}, msg("c2m3","sms","SMS nudge")],
  "sms_send_window":{"start":"09:00","end":"20:00","timezone":"America/New_York","basis":"account_timezone"},  # planted issue 5
  "exit":{"on_event":"Placed Order"}},
 {"id":"flow_cart_2024","name":"Abandoned Cart (2024)","status":"live","last_edited":"2024-09-30",
  "trigger":{"type":"event","event":"Started Checkout"},
  "trigger_filters":[{"metric":"Placed Order","op":"zero_since_trigger"}],
  "steps":[{"delay_hours":2}, msg("c0m1","email","You left something behind"),
           {"delay_hours":22}, msg("c0m2","email","Your cart is expiring")],
  "exit":{"on_event":"Placed Order"}},                                                  # planted issue 1: both live
 {"id":"flow_browse","name":"Browse Abandonment","status":"live","last_edited":"2025-11-12",
  "trigger":{"type":"event","event":"Viewed Product"},
  "steps":[{"delay_hours":20}, msg("bm1","email","Featured: what you viewed")],
  "note":"Dynamic product block inserts most-viewed item"},                              # planted issue 7: no inventory condition
 {"id":"flow_winback","name":"Winback 90d","status":"live","last_edited":"2025-07-21",
  "trigger":{"type":"segment_join","segment":"seg_lapsed_90"},
  "steps":[msg("wb1","email","We miss you"), {"delay_days":5}, msg("wb2","email","10% to come back"),
           {"delay_days":7}, msg("wb3","sms","Last call SMS")],
  "sms_send_window":{"start":"09:00","end":"20:00","timezone":"America/New_York","basis":"account_timezone"},
  "exit":{"on_event":"Placed Order"}},                                                   # planted issue 2: no subscriber exclusion
 {"id":"flow_postpurchase","name":"Post-Purchase Care","status":"live","last_edited":"2025-10-05",
  "trigger":{"type":"event","event":"Placed Order"},
  "steps":[{"delay_days":3}, msg("pp1","email","How to use your products"),
           {"delay_days":18}, msg("pp2","email","Replenishment check-in")]},
 {"id":"flow_sunset","name":"Sunset / Re-permission","status":"disabled","last_edited":"2026-01-12",
  "trigger":{"type":"segment_join","segment":"seg_unengaged"},
  "steps":[msg("s1","email","Do you still want to hear from us?"), {"delay_days":10},
           msg("s2","email","Final: staying subscribed?"), {"action":"suppress_if_no_engagement"}]},  # planted issue 3
 {"id":"flow_backinstock","name":"Back in Stock","status":"live","last_edited":"2025-08-19",
  "trigger":{"type":"event","event":"Subscribed to Back in Stock"},
  "steps":[msg("bis1","email","It's back")]},
 {"id":"flow_bday","name":"Birthday","status":"live","last_edited":"2025-02-14",
  "trigger":{"type":"segment_join","segment":"seg_bday"},
  "steps":[msg("bd1","email","A birthday treat: BDAY20")]},
 {"id":"flow_review","name":"Review Request","status":"live","last_edited":"2025-05-01",
  "trigger":{"type":"event","event":"Order Delivered"},
  "steps":[{"delay_days":10}, msg("rv1","email","How did it go?")]},
 {"id":"flow_vip","name":"VIP Early Access","status":"live","last_edited":"2026-04-22",
  "trigger":{"type":"segment_join","segment":"seg_vips"},
  "steps":[msg("v1","email","Early access begins now")]},
]
json.dump({"flows":flows}, open(f"{OUT}/flows/flows.json","w"), indent=1)

# ---------------- flow_performance.csv (24 months, planted signatures) ----------------
rows = []
for m in MONTHS:
    mm = iso(m)[:7]
    # welcome: conv 8.2% -> 4.4% from 2026-06 (expired code)
    entries = int(random.gauss(3800, 150))
    conv = random.gauss(0.082, 0.003) if m < d(2026,6,1) else random.gauss(0.044, 0.003)
    rows.append(["flow_welcome",mm,entries,int(entries*2.9),0.52,0.118,int(entries*conv),
                 round(entries*conv*54,2), round(entries*2.9*0.0018)])
    # cart_v2 exists from 2026-03; cart_2024 always. overlap window = both live
    ent_c = int(random.gauss(2600,120))
    if m >= d(2026,3,1):
        rows.append(["flow_cart_v2",mm,ent_c,int(ent_c*2.6),0.55,0.16,int(ent_c*0.071),round(ent_c*0.071*66,2),
                     round(ent_c*2.6*0.0041)])   # elevated unsubs (collision)
        rows.append(["flow_cart_2024",mm,int(ent_c*0.42),int(ent_c*0.42*1.9),0.49,0.105,int(ent_c*0.42*0.049),
                     round(ent_c*0.42*0.049*61,2), round(ent_c*0.42*1.9*0.0044)])
    else:
        rows.append(["flow_cart_2024",mm,ent_c,int(ent_c*1.9),0.51,0.135,int(ent_c*0.062),round(ent_c*0.062*63,2),
                     round(ent_c*1.9*0.0019)])
    # browse: conversion halves in Jul-2026 (serum stockout promoted)
    ent_b = int(random.gauss(5200,200))
    bconv = 0.021 if m < d(2026,7,1) else 0.010
    rows.append(["flow_browse",mm,ent_b,int(ent_b*1.05),0.44,0.083,int(ent_b*bconv),round(ent_b*bconv*58,2),
                 round(ent_b*1.05*0.0016)])
    # winback: chronically weak; unsubs high (subscribers annoyed)
    ent_w = int(random.gauss(1900,90))
    rows.append(["flow_winback",mm,ent_w,int(ent_w*2.7),0.31,0.036,int(ent_w*0.008),round(ent_w*0.008*57,2),
                 round(ent_w*2.7*0.0052)])
    # sunset: entries -> 0 after Jan 2026
    ent_s = int(random.gauss(2400,100)) if m < d(2026,2,1) else 0
    rows.append(["flow_sunset",mm,ent_s,int(ent_s*1.8),0.19,0.041,0,0.0, round(ent_s*1.8*0.001)])
    for fid, ent, orate, crate, cv, aov in [("flow_postpurchase",4200,0.58,0.14,0.032,49),
                                            ("flow_backinstock",240,0.71,0.34,0.19,66),
                                            ("flow_bday",610,0.62,0.22,0.11,58),
                                            ("flow_review",3900,0.47,0.09,0.0,0),
                                            ("flow_vip",480,0.36,0.052,0.021,74)]:
        e = int(random.gauss(ent, ent*0.05))
        rows.append([fid,mm,e,int(e*1.4),orate,crate,int(e*cv),round(e*cv*aov,2),round(e*1.4*0.0012)])
with open(f"{OUT}/flows/flow_performance.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["flow_id","month","entries","emails_delivered","open_rate","click_rate",
                                   "conversions","revenue_usd","unsubscribes"])
    w.writerows(rows)
AK["welcome_conv_pre"] = 0.082; AK["welcome_conv_post"] = 0.044
AK["welcome_monthly_revenue_impact"] = round(3800*(0.082-0.044)*54)

# ---------------- campaign_history.csv (18 months; June-2026 frequency doubling) ----------------
c_rows = []; cid = 100
for m in months(d(2025,2,1), d(2026,7,1)):
    per_wk = 2 if m < d(2026,6,1) else 4                              # planted issue 8
    fatigue = 1.0 if m < d(2026,6,1) else 1.6
    n_c = per_wk*4
    for k in range(n_c):
        cid += 1
        seg = random.choice(["seg_engaged_90","seg_engaged_90","seg_vips","full_list","seg_solstice_buyers"])
        sends = {"seg_engaged_90":118000,"seg_vips":21000,"full_list":268000,"seg_solstice_buyers":64000}[seg]
        sends = int(random.gauss(sends, sends*0.04))
        orate = random.gauss(0.41 if seg!="full_list" else 0.27, 0.02)
        crate = random.gauss(0.012 if seg!="full_list" else 0.007, 0.001)
        rev = round(sends*crate*random.gauss(0.9,0.1)*62*(0.82 if fatigue>1 else 1.0),2)
        unsub = round(sends*random.gauss(0.0016,0.0002)*fatigue)
        spam = round(sends*random.gauss(0.0007,0.0001)*(fatigue if seg=="full_list" else 1.0))
        c_rows.append([f"cmp_{cid}", iso(m + timedelta(days=int(k*28/n_c))), f"Campaign {cid}",
                       "email", seg, sends, round(orate,3), round(crate,4),
                       int(sends*crate*0.9), rev, unsub, spam])
with open(f"{OUT}/campaigns/campaign_history.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["campaign_id","send_date","name","channel","audience_segment","delivered",
                                   "open_rate","click_rate","conversions","revenue_usd","unsubscribes","spam_complaints"])
    w.writerows(c_rows)

# ---------------- client engagement (dark-mode signature) + SMS send log ----------------
with open(f"{OUT}/campaigns/client_engagement_sample.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["message_id","flow_id","email_client","delivered","click_rate"])
    for mid, fid in [("c2m1","flow_cart_v2"),("c2m2","flow_cart_v2"),("wm1","flow_welcome"),("pp1","flow_postpurchase")]:
        for client, share in [("Apple Mail (iOS)",0.46),("Gmail",0.34),("Outlook",0.11),("Other",0.09)]:
            base = 0.16 if fid=="flow_cart_v2" else 0.12
            cr = base*0.48 if (client=="Apple Mail (iOS)" and fid=="flow_cart_v2") else base  # planted issue 10 symptom
            w.writerow([mid,fid,client,int(9000*share),round(random.gauss(cr,cr*0.05),4)])
with open(f"{OUT}/campaigns/sms_send_log_sample.csv","w",newline="") as f:
    w = csv.writer(f); w.writerow(["profile_id","flow_id","message_id","send_ts_utc","recipient_timezone","local_send_time"])
    n_viol = 0
    for p in [q for q in profiles if q["sms"]][:180]:
        # sends scheduled 09:05 ET -> 06:05 PT etc.  (planted issue 5)
        send_utc = "13:05" ; local = {"America/New_York":"09:05","America/Chicago":"08:05",
                                      "America/Denver":"07:05","America/Phoenix":"06:05","America/Los_Angeles":"06:05"}[p["tz"]]
        if local < "08:00": n_viol += 1
        w.writerow([p["pid"], random.choice(["flow_cart_v2","flow_winback"]), "sms",
                    f"2026-07-{random.randint(1,28):02d}T{send_utc}:00Z", p["tz"], local])
    AK["sms_quiet_hour_violations_in_log"] = n_viol

json.dump(AK, open(f"{OUT}/answer_key/computed_values.json","w"), indent=1)
print("alma data done", json.dumps(AK, indent=1))
