#!/usr/bin/env python3
"""MarketingBench sample universe — Meridian Travel Goods (premium DTC luggage; Away-like
category dynamics, fully fictional brand). Seed=7. Data + docs + answer key.
Contrast with Alma: durable goods (3.8yr median luggage repurchase), gift-heavy Q4,
strict no-discount policy, high AOV — the 'right answers' change with the category."""
import csv, json, os, random
from datetime import date, timedelta
random.seed(7)
OUT = "/home/claude/universes/meridian-travel-goods"
AK = {}
def d(y,m,dy): return date(y,m,dy)
def iso(x): return x.isoformat()
def months(s,e):
    cur=s; out=[]
    while cur<=e:
        out.append(cur); cur=d(cur.year+(cur.month==12), cur.month%12+1, 1)
    return out
MONTHS = months(d(2024,8,1), d(2026,7,1))
for sub in ["brand","catalog","crm","flows","campaigns","campaigns/messages","deliverability",
            "comms","legal","ops","briefs","goals","answer_key"]:
    os.makedirs(f"{OUT}/{sub}", exist_ok=True)
def W(p,s): open(f"{OUT}/{p}","w").write(s.strip()+"\n")

# ---------------- catalog ----------------
COLORS = ["Harbor","Dune","Ink","Alpine","Coast"]  # Coast discontinued
prods = []
i=0
base = [("Carry-On 38L","Poly",275),("Carry-On Plus 46L","Poly",295),("Checked 65L","Poly",325),
        ("Checked 95L","Poly",345),("Carry-On 38L","Aluminum",495),("Checked 65L","Aluminum",595)]
for name, line, price in base:
    for c in COLORS if line=="Poly" else ["Harbor","Ink"]:
        i+=1
        status = "discontinued" if c=="Coast" else "active"
        inv = 0 if c=="Coast" else random.randint(150,1400)
        if line=="Aluminum": inv = random.randint(800,1600)   # planted: aluminum overstock pre-refresh
        prods.append([f"MER-{i:03d}", f"{name} — {c}", line, price, round(price*random.uniform(0.30,0.42),2),
                      inv, "", "no", status])
acc = [("Packing Cubes (4)",45),("Toiletry Case",55),("Everywhere Tote",145),("Garment Sleeve",65),
       ("Luggage Tag",25),("Travel Wellness Kit",38),("Daypack",125),("Tech Organizer",48),
       ("Shoe Cubes (2)",35),("Compression Cubes (2)",52)]
for name, price in acc:
    for c in ["Harbor","Dune","Ink"]:
        i+=1
        prods.append([f"MER-{i:03d}", f"{name} — {c}", "Accessories", price, round(price*0.3,2),
                      random.randint(300,2500), "", "no", "active"])
with open(f"{OUT}/catalog/products.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["sku","name","line","price_usd","cost_usd","inventory_on_hand",
                                 "restock_date","subscription_eligible","status"])
    w.writerows(prods)
AK["coast_skus"] = [p[0] for p in prods if "Coast" in p[1]]
AK["aluminum_inventory_total"] = sum(p[5] for p in prods if p[2]=="Aluminum")

with open(f"{OUT}/campaigns/discount_codes.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["code","discount","applies_to","created","expires","status","note"])
    w.writerows([
        ["WANDER10","10%","cart recovery","2025-09-12","","active","added by former agency; see brand policy"],  # planted M3
        ["PASSAGE-S26","15%","Passage Sale (June 2026) — sitewide","2026-06-05","2026-06-12","expired","sanctioned twice-yearly sale"],
        ["CREW","varies","employee/wholesale accounts","2024-01-01","","active","internal"],
    ])

# ---------------- profiles (500 sample of 910k) ----------------
FIRST=["Alex","Jordan","Sam","Casey","Morgan","Riley","Devon","Quinn","Harper","Rowan","Elena",
       "Marcus","Nina","Theo","Leah","Omar","Ingrid","Felix","Dana","Yuki"]
LAST=["Ramirez","Kowalski","Ito","Bennett","Achebe","Lindqvist","Torres","MacLeod","Haas","Duval",
      "Okada","Reyes","Nowak","Grant","Sy","Petrov","Lang","Mbeki","Costa","Ferris"]
TZ=[("America/New_York",0.42),("America/Chicago",0.18),("America/Denver",0.07),
    ("America/Los_Angeles",0.30),("America/Phoenix",0.03)]
def pick_tz():
    r=random.random(); c=0
    for tz,p in TZ:
        c+=p
        if r<=c: return tz
    return TZ[0][0]
today=d(2026,8,12)
profiles=[]
for n in range(500):
    pid=f"MT-{20000+n}"
    fn,ln=random.choice(FIRST),random.choice(LAST)
    tz=pick_tz()
    is_wholesale = random.random()<0.03                      # planted M6 fodder
    n_orders = random.randint(12,40) if is_wholesale else max(1,int(random.expovariate(1/1.5)))
    aov = random.gauss(285,80) if not is_wholesale else random.gauss(310,40)
    ltv = round(max(45, n_orders*max(60,aov)),2)
    first = today - timedelta(days=random.randint(60, 1500))
    last = today - timedelta(days=random.randint(5, 900))
    # gift purchasers: bought in Nov/Dec, shipped to different address
    is_gift_giver = random.random()<0.14 and not is_wholesale   # planted M2 fodder
    if is_gift_giver:
        last = d(2025,12,random.randint(1,22))
    tier = random.choices(["engaged_30","engaged_90","engaged_365","unengaged_12m"],
                          weights=[0.22,0.20,0.24,0.34])[0]
    sms = random.random()<0.09
    profiles.append(dict(pid=pid,fn=fn,ln=ln,tz=tz,ws=is_wholesale,n=n_orders,ltv=ltv,
                         first=first,last=last,gift=is_gift_giver,tier=tier,sms=sms,dup=False))
# planted M7: domain-migration duplicates — 8% of profiles duplicated with new pid, same email
dups=[]
for p in random.sample(profiles, 40):
    q=dict(p); q["pid"]=f"MT-{int(p['pid'][3:])+70000}"; q["dup"]=True
    dups.append(q)
profiles += dups
AK["duplicate_profiles_in_sample"]=len(dups)
AK["wholesale_in_insiders_sample"]=sum(1 for p in profiles if p["ws"] and p["ltv"]>1200)
with open(f"{OUT}/crm/profiles_sample.csv","w",newline="") as f:
    w=csv.writer(f)
    w.writerow(["profile_id","email","first_name","last_name","timezone","account_type","is_gift_purchaser_2025Q4",
                "first_order_date","last_order_date","orders_count","ltv_usd","engagement_tier","sms_consent",
                "created_source"])
    for p in profiles:
        email=f"{p['fn'].lower()}.{p['ln'].lower()}{p['pid'][3:]}@example.com" if not p["dup"] else \
              f"{p['fn'].lower()}.{p['ln'].lower()}{int(p['pid'][3:])-70000}@example.com"   # same email as original!
        w.writerow([p["pid"],email,p["fn"],p["ln"],p["tz"],"wholesale" if p["ws"] else "consumer",
                    str(p["gift"]).lower(),iso(p["first"]),iso(p["last"]),p["n"],p["ltv"],p["tier"],
                    str(p["sms"]).lower(),"site_migration_2026_03" if p["dup"] else "checkout"])

# ---------------- segments ----------------
segments=[
 {"id":"seg_insiders","name":"Insiders (VIP)","definition":{"all":[{"metric":"ltv_usd","op":">","value":1200}]},
  "note":"Early access + referral perks"},                       # planted M6: no account_type filter -> wholesale pollution
 {"id":"seg_lapsed_90","name":"Lapsed 90d","definition":{"all":[{"metric":"last_order_date","op":"older_than_days","value":90}]},
  "note":"Feeds winback"},                                        # planted M1: 90d lapse on durable goods
 {"id":"seg_engaged_90","name":"Engaged 90d","definition":{"all":[{"metric":"engagement_tier","op":"in","value":["engaged_30","engaged_90"]}]}},
 {"id":"seg_full_list","name":"Full list","definition":{"all":[{"metric":"email_consent","op":"=","value":True}]}},
 {"id":"seg_luggage_owners","name":"Luggage owners","definition":{"all":[{"metric":"line_purchased","op":"in","value":["Poly","Aluminum"]}]},
  "note":"Used by post-purchase care; NOTE: includes 2025Q4 gift purchasers (givers, not owners)"},  # planted M2
 {"id":"seg_accessories_only","name":"Accessories-only buyers","definition":{"all":[{"metric":"line_purchased","op":"only","value":"Accessories"}]}},
 {"id":"seg_sms","name":"SMS list","definition":{"all":[{"metric":"sms_consent","op":"=","value":True}]}},
 {"id":"seg_coast_waitlist","name":"Coast colorway waitlist","definition":{"all":[{"metric":"back_in_stock_sku","op":"in","value":AK["coast_skus"]}]},
  "note":"3,400 profiles waiting on discontinued SKUs"},          # planted M4
]
json.dump({"segments":segments}, open(f"{OUT}/crm/segments.json","w"), indent=1)

# ---------------- flows ----------------
flows=[
 {"id":"flow_welcome","name":"Welcome Series","status":"live","last_edited":"2025-08-02",
  "trigger":{"type":"list_join","list":"Newsletter"},
  "steps":[{"msg":"w1","channel":"email","name":"Welcome — the Meridian standard",
            "links":["https://meridian-travel.com/collections/all"]},                      # planted M5: OLD domain
           {"delay_hours":72},
           {"msg":"w2","channel":"email","name":"Which case fits how you travel",
            "links":["https://meridian-travel.com/quiz"]}],
  "note":"Site migrated to meridiantravel.co on 2026-03-02; templates not updated"},
 {"id":"flow_cart","name":"Abandoned Cart","status":"live","last_edited":"2025-09-12",
  "trigger":{"type":"event","event":"Started Checkout"},
  "steps":[{"delay_hours":6},{"msg":"c1","channel":"email","name":"Your case is waiting"},
           {"delay_hours":18},{"msg":"c2","channel":"email","name":"10% if you complete today","code":"WANDER10"}],
  "note":"Added by former agency Sep 2025"},                                               # planted M3
 {"id":"flow_winback","name":"Winback 90d","status":"live","last_edited":"2025-04-30",
  "trigger":{"type":"segment_join","segment":"seg_lapsed_90"},
  "steps":[{"msg":"wb1","channel":"email","name":"We miss you"},
           {"delay_days":6},{"msg":"wb2","channel":"email","name":"Come back and see what's new"}]},  # planted M1
 {"id":"flow_postpurchase","name":"Owner Care Series","status":"live","last_edited":"2025-10-20",
  "trigger":{"type":"event","event":"Placed Order","filter":{"line":["Poly","Aluminum"]}},
  "steps":[{"delay_days":7},{"msg":"pp1","channel":"email","name":"Caring for your case"},
           {"delay_days":21},{"msg":"pp2","channel":"email","name":"Register your lifetime warranty"},
           {"delay_days":45},{"msg":"pp3","channel":"email","name":"Packing like you mean it"}],
  "note":"Targets purchaser profile; no gift-recipient branch"},                            # planted M2
 {"id":"flow_backinstock","name":"Back in Stock","status":"live","last_edited":"2024-11-15",
  "trigger":{"type":"event","event":"Subscribed to Back in Stock"},
  "steps":[{"msg":"bis1","channel":"email","name":"It's back"}],
  "note":"No SKU-status check; Coast waitlist (3,400) still enrolled"},                     # planted M4
 {"id":"flow_referral","name":"Referral nudge","status":"live","last_edited":"2025-06-10",
  "trigger":{"type":"event","event":"Order Delivered"},
  "steps":[{"delay_days":21},{"msg":"rf1","channel":"email","name":"Give $30, get $30"}]},
]
json.dump({"flows":flows}, open(f"{OUT}/flows/flows.json","w"), indent=1)

# ---------------- flow performance ----------------
rows=[]
for m in MONTHS:
    mm=iso(m)[:7]
    # welcome: click-to-session collapse after Mar-2026 migration (clicks fine, sessions/conv die)
    e=int(random.gauss(6100,250)); pre = m < d(2026,3,1)
    conv = 0.041 if pre else 0.009
    rows.append(["flow_welcome",mm,e,int(e*1.9),0.49,0.128,round(0.128*e*(0.62 if pre else 0.11)),  # sessions
                 int(e*conv), round(e*conv*265,2)])
    # cart: WANDER10 redemptions climbing (trained abandonment)
    e=int(random.gauss(3400,150))
    monthidx=MONTHS.index(m)
    red = int(e*min(0.028+0.0012*monthidx, 0.06))
    rows.append(["flow_cart",mm,e,int(e*1.85),0.57,0.19,red,int(e*0.062),round(e*0.062*288,2)])
    # winback: near-zero conversion (durable goods)
    e=int(random.gauss(8900,300))
    rows.append(["flow_winback",mm,e,int(e*1.8),0.24,0.021,0,int(e*0.0011),round(e*0.0011*118,2)])
    # owner care: open-rate craters for Dec/Jan cohorts (gift givers)
    e=int(random.gauss(2100,120)) if m.month not in (11,12) else int(random.gauss(5200,200))
    orate = 0.61 if m.month not in (12,1) else 0.29
    rows.append(["flow_postpurchase",mm,e,int(e*2.7),orate,0.135,0,int(e*0.018),round(e*0.018*74,2)])
    # back in stock: high sends, complaint blip (Coast dead-ends)
    e=int(random.gauss(700,60))
    rows.append(["flow_backinstock",mm,e,e,0.66,0.31,0,int(e*0.04),round(e*0.04*300,2)])
    e=int(random.gauss(2900,150))
    rows.append(["flow_referral",mm,e,int(e*1.05),0.52,0.088,0,int(e*0.012),round(e*0.012*260,2)])
with open(f"{OUT}/flows/flow_performance.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["flow_id","month","entries","emails_delivered","open_rate","click_rate",
                                 "col_extra","conversions","revenue_usd"])
    w.writerows(rows)
# col_extra: welcome=sessions_from_clicks, cart=code_redemptions, others=0/misc — documented in README
AK["welcome_conv_pre_migration"]=0.041; AK["welcome_conv_post_migration"]=0.009
AK["winback_monthly_sends"]=8900*1.8; AK["winback_conv_rate"]=0.0011

# ---------------- campaign history: full-file newsletter dilution ----------------
c_rows=[]; cid=500
for m in months(d(2025,2,1), d(2026,7,1)):
    for k in range(6):
        cid+=1
        if k<2:  # travel newsletter to FULL LIST (planted M8)
            seg="seg_full_list"; sends=int(random.gauss(884000,9000)); orate=random.gauss(0.208,0.01)
        else:
            seg=random.choice(["seg_engaged_90","seg_insiders","seg_accessories_only","seg_luggage_owners"])
            sends={"seg_engaged_90":238000,"seg_insiders":19000,"seg_accessories_only":86000,
                   "seg_luggage_owners":143000}[seg]
            sends=int(random.gauss(sends,sends*0.04)); orate=random.gauss(0.39,0.02)
        crate=random.gauss(0.006 if seg=="seg_full_list" else 0.011,0.001)
        c_rows.append([f"cmp_{cid}",iso(m+timedelta(days=k*4+2)),f"Campaign {cid}","email",seg,sends,
                       round(orate,3),round(max(crate,0.001),4),int(sends*crate*0.35),
                       round(sends*crate*0.35*random.gauss(240,30),2),
                       round(sends*random.gauss(0.0011,0.0002)*(1.7 if seg=="seg_full_list" else 1.0))])
with open(f"{OUT}/campaigns/campaign_history.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["campaign_id","send_date","name","channel","audience_segment","delivered",
                                 "open_rate","click_rate","conversions","revenue_usd","unsubscribes"])
    w.writerows(c_rows)

json.dump(AK, open(f"{OUT}/answer_key/computed_values.json","w"), indent=1)
print("meridian data done", json.dumps(AK, indent=1)[:400])
