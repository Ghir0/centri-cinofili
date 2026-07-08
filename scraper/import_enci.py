#!/usr/bin/env python3
"""
Import ENCI-scraped centers into Supabase.
1. Delete the 10 demo centers
2. Map provincia_sigla -> provincia_id via DB lookup
3. Insert all centers + junction records
"""
import json
import re
import urllib.request
import urllib.error

# ── Config ──
env = {}
with open("C:/Users/miket/projects/centri-cinofili/.env.local") as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()

URL = env["NEXT_PUBLIC_SUPABASE_URL"]
KEY = env["SUPABASE_SERVICE_ROLE_KEY"]

HEADERS = {
    "apikey": KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

def api(method, path, body=None):
    url = f"{URL}/rest/v1/{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            content = r.read().decode()
            return r.status, json.loads(content) if content else []
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:500]

# ── Load scraped data ──
with open("C:/Users/miket/projects/centri-cinofili/supabase/seeds/00006_italia_scraped.json") as f:
    scraped = json.load(f)

print(f"Scraped records: {len(scraped)}")

# ── Sample check ──
print(f"Sample: {scraped[0]['ragione_sociale'][:60]} | {scraped[0]['provincia_sigla']}")
unique_sigle = sorted(set(c["provincia_sigla"] for c in scraped if c.get("provincia_sigla")))
print(f"Unique sigle province: {len(unique_sigle)}")
print(f"Sigle: {unique_sigle[:20]}")

# ── Fetch province mapping from DB ──
status, province_rows = api("GET", "province?select=id,sigla")
print(f"\nProvince in DB: {len(province_rows)}")
sigla_to_id = {}
for p in province_rows:
    if p.get("sigla"):
        sigla_to_id[p["sigla"].upper()] = p["id"]

# Check which sigle from scraped are NOT in DB
missing = [s for s in unique_sigle if s.upper() not in sigla_to_id]
print(f"Missing sigle (not in DB): {missing}")

# ── Stats on scraped data ──
with_coords = sum(1 for c in scraped if c.get("coordinate_gps"))
with_metodologie = sum(1 for c in scraped if c.get("metodologie"))
with_discipline = sum(1 for c in scraped if c.get("discipline"))
print(f"With coordinates: {with_coords}")
print(f"With metodologie: {with_metodologie}")
print(f"With discipline: {with_discipline}")

# ── Show sample sigla → id mapping ──
sample = {s: sigla_to_id.get(s.upper()) for s in list(unique_sigle)[:10]}
print(f"\nSample sigla→id: {sample}")
