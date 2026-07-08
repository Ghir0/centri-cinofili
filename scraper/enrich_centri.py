#!/usr/bin/env python3
"""
Enrichment scraper per centri cinofili.
Per ogni centro con sito web:
1. Visita il sito
2. Estrae social links (FB, IG, YT, TikTok)
3. Estrae descrizione
4. Identifica metodologie, discipline, infrastrutture
5. Aggiorna Supabase

Usage: uv run python scraper/enrich_centri.py [--limit N] [--dry-run]
"""

import os, sys, re, json, time, urllib.parse
from pathlib import Path
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from supabase import create_client

# ── Config ────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR))

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
}

TIMEOUT = 15

# ── Social pattern ───────────────────────────────────────
SOCIAL_PATTERNS = {
    "facebook": re.compile(r"(?:facebook\.com|fb\.com|fb\.me)/[\w.\-]+", re.I),
    "instagram": re.compile(r"instagram\.com/[\w.\-]+", re.I),
    "youtube": re.compile(r"(?:youtube\.com|youtu\.be)/[@\w\-]+", re.I),
    "tiktok": re.compile(r"tiktok\.com/@[\w.\-]+", re.I),
    "linkedin": re.compile(r"linkedin\.com/(?:company|in)/[\w.\-]+", re.I),
}

# ── Keyword-based classifiers ────────────────────────────
DISCIPLINE_KEYWORDS = [
    ("Agility Dog", ["agility", "agility dog"]),
    ("Rally-Obedience", ["rally", "rally-o", "rally obedience"]),
    ("Obedience", ["obedience", "obbedienza"]),
    ("Hoopers", ["hoopers"]),
    ("Scent Detection", ["scent", "olfatto", "odorato", "discriminazione olfattiva"]),
    ("Mantrailing", ["mantrail", "mantrailing"]),
    ("Sheepdog", ["sheepdog", "pecore", "gregge", "bestiame"]),
    ("Dog Dance", ["dog dance", "danza", "freestyle"]),
    ("Disc Dog", ["disc dog", "frisbee"]),
    ("Protezione Civile", ["protezione civile", "soccorso"]),
    ("IPO/IGP", ["ipo", "igp", "schutzhund"]),
    ("Utilità e Difesa", ["utilità", "difesa", "attacco"]),
    ("Trick Training", ["trick", "trucchi"]),
    ("Socializzazione", ["socializzazione", "cuccioli", "puppy class"]),
    ("Riabilitazione", ["riabilitazione", "recupero comportamentale", "problemi comportamentali"]),
]

METODOLOGIA_KEYWORDS = [
    ("Cognitivo-Relazionale", ["cognitivo", "relazionale", "gentile", "zooantropologia"]),
    ("Gentile/Positivo", ["rinforzo positivo", "clicker", "positivo", "gentile"]),
    ("Tradizionale", ["tradizionale"]),
    ("Misto", ["misto"]),
    ("Etologico", ["etologico", "etologia"]),
]

INFRASTRUTTURA_KEYWORDS = [
    ("Campo Coperto", ["coperto", "indoor", "al chiuso", "tensostruttura"]),
    ("Campo Scoperto", ["scoperto", "outdoor", "campo", "recinto", "recintato"]),
    ("Agility Field", ["campo agility", "attrezzi agility"]),
    ("Piscina", ["piscina", "idroterapia", "nuoto"]),
    ("Area Socializzazione", ["area socializzazione", "sgambamento"]),
]


def load_env():
    """Carica variabili d'ambiente da .env.local"""
    env_path = PROJECT_DIR / ".env.local"
    env_vars = {}
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env_vars[k] = v
    return env_vars


def classify_keywords(text, keyword_map):
    """Classifica il testo contro una mappa di keyword → [id, nome]"""
    text_lower = text.lower()
    found = []
    for name, keywords in keyword_map:
        for kw in keywords:
            if kw.lower() in text_lower:
                found.append(name)
                break
    return found


def extract_social_links(soup, url):
    """Estrae link social dal DOM."""
    social = {}
    # Cerca in tutti i link
    all_links = []
    for a in soup.find_all("a", href=True):
        all_links.append(a["href"])

    # Cerca anche nel testo della pagina
    page_text = soup.get_text()
    all_links.extend(re.findall(r"https?://[^\s<>\"]+", page_text))

    for link in all_links:
        link = link.strip().rstrip("/")
        for platform, pattern in SOCIAL_PATTERNS.items():
            if platform in social:
                continue
            match = pattern.search(link)
            if match:
                found = "https://" + match.group(0)
                social[platform] = found
                break

    return social


def extract_meta_description(soup):
    """Estrae description da og:description o meta description."""
    for attr in ["og:description", "description"]:
        tag = soup.find("meta", attrs={"name": attr}) or soup.find("meta", attrs={"property": attr})
        if tag and tag.get("content"):
            desc = tag["content"].strip()
            if len(desc) > 30:
                return desc[:500]
    return None


def extract_body_text(soup):
    """Estrae testo significativo dalla pagina."""
    # Rimuovi script, style, nav, footer
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Prendi main o body
    main = soup.find("main") or soup.find("article") or soup
    text = main.get_text(separator=" ", strip=True)
    # Pulisci
    text = re.sub(r"\s+", " ", text)
    return text[:3000]


def scrape_website(url):
    """Scrapa un sito web e restituisce i dati estratti."""
    if not url or not url.startswith("http"):
        return {}

    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ⚠ {url[:60]}: {e}")
        return {}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Estrai social
    social = extract_social_links(soup, url)

    # Descrizione (preferisce meta desc, fallback su h1+p)
    desc = extract_meta_description(soup)
    if not desc:
        h1 = soup.find("h1")
        p = soup.find("p")
        if h1 and p:
            desc = f"{h1.get_text(strip=True)}. {p.get_text(strip=True)}"[:300]
        elif p:
            desc = p.get_text(strip=True)[:300]

    # Classifica keyword nel body
    body_text = extract_body_text(soup)
    discipline = classify_keywords(body_text, DISCIPLINE_KEYWORDS)
    metodologie = classify_keywords(body_text, METODOLOGIA_KEYWORDS)
    infrastrutture = classify_keywords(body_text, INFRASTRUTTURA_KEYWORDS)

    result = {
        "social_links": social,
        "descrizione": desc,
        "discipline_keywords": discipline,
        "metodologia_keywords": metodologie,
        "infrastruttura_keywords": infrastrutture,
    }

    # Filtra vuoti
    return {k: v for k, v in result.items() if v}


def main():
    dry_run = "--dry-run" in sys.argv
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == "--limit" and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    env = load_env()
    supabase_url = env.get("NEXT_PUBLIC_SUPABASE_URL")
    supabase_key = env.get("SUPABASE_SERVICE_ROLE_KEY") or env.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not supabase_url or not supabase_key:
        print("❌ Variabili Supabase mancanti in .env.local")
        sys.exit(1)

    supabase = create_client(supabase_url, supabase_key)

    # Query centri con sito web
    query = supabase.table("centri").select("id,ragione_sociale,sito_web,comune").not_.is_("sito_web", "null")
    if limit:
        query = query.limit(limit)
    resp = query.execute()

    centri = resp.data
    print(f"🔍 {len(centri)} centri con sito web da arricchire\n")

    enriched = 0
    for centro in centri:
        cid = centro["id"]
        nome = centro["ragione_sociale"][:60]
        url = centro["sito_web"]

        if not url or not url.startswith("http"):
            continue

        print(f"🌐 [{cid}] {nome}")
        data = scrape_website(url)

        if not data:
            continue

        # Prepara update
        update = {}
        if data.get("social_links"):
            update["social_links"] = data["social_links"]
            print(f"   📱 Social: {list(data['social_links'].keys())}")
        if data.get("descrizione"):
            update["descrizione"] = data["descrizione"]
            print(f"   📝 Desc: {data['descrizione'][:80]}...")
        if data.get("discipline_keywords"):
            update["discipline"] = data["discipline_keywords"]
            print(f"   🏅 Discipline trovate: {data['discipline_keywords']}")
        if data.get("metodologia_keywords"):
            update["metodologie"] = data["metodologia_keywords"]
            print(f"   🧠 Metodologia: {data['metodologia_keywords']}")
        if data.get("infrastruttura_keywords"):
            update["infrastrutture"] = data["infrastruttura_keywords"]
            print(f"   🏗️ Infrastrutture: {data['infrastruttura_keywords']}")

        if update and not dry_run:
            try:
                supabase.table("centri").update(update).eq("id", cid).execute()
                enriched += 1
                print(f"   ✅ Aggiornato")
            except Exception as e:
                print(f"   ❌ Errore: {e}")

        time.sleep(1)  # Rate limit

    print(f"\n✨ Completato. {enriched} centri arricchiti su {len(centri)}.")
    if dry_run:
        print("   (dry run — nessun dato modificato)")


if __name__ == "__main__":
    main()
