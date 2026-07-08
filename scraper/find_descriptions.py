"""Find descriptions for centers via Google search snippets."""
import json, logging, os, random, re, sys, time, urllib.parse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("desc_finder")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(SUPABASE_URL, SUPABASE_KEY)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

def google_search(query, retries=2):
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=it&num=5"
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "it-IT,it;q=0.9",
    }
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=headers, timeout=12)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code == 429:
                time.sleep(10 * (attempt + 1))
        except:
            time.sleep(2)
    return None

def extract_snippet(html):
    try:
        soup = BeautifulSoup(html, "lxml")
    except:
        soup = BeautifulSoup(html, "html.parser")
    for sel in ["div.VwiC3b", "span.st", "div[data-sncf]", "div.IsZvec"]:
        el = soup.select_one(sel)
        if el:
            text = el.get_text(strip=True)
            if len(text) > 30:
                return text[:500]
    return None

def main():
    # Get centers without descriptions
    resp = client.table("centri").select("id,ragione_sociale,brand_name,comune,descrizione").is_("descrizione", "null").limit(109).execute()
    centers = resp.data
    logger.info("Centers without description: %d", len(centers))

    updated = 0
    for i, c in enumerate(centers):
        name = c["brand_name"] or c["ragione_sociale"]
        comune = c.get("comune", "") or ""
        
        # Clean name — remove legal suffixes
        clean_name = re.sub(r"\b(?:A\.?S\.?D\.?|S\.?S\.?D\.?|S\.?R\.?L\.?|ASSOCIAZIONE SPORTIVA DILETTANTISTICA|SOCIETA SPORTIVA DILETTANTISTICA)\b", "", name, flags=re.I).strip()
        if len(clean_name) < 5:
            clean_name = name
        
        query = f"{clean_name[:80]} centro cinofilo {comune}"
        
        time.sleep(random.uniform(2, 4))
        html = google_search(query)
        
        if not html:
            # retry without comune
            time.sleep(random.uniform(2, 3))
            html = google_search(f"{clean_name[:80]} centro cinofilo")
        
        if html:
            snippet = extract_snippet(html)
            if snippet:
                try:
                    client.table("centri").update({"descrizione": snippet}).eq("id", c["id"]).execute()
                    updated += 1
                    logger.info("[%d/%d] %s: %s...", i+1, len(centers), clean_name[:40], snippet[:80])
                except Exception as e:
                    logger.warning("Update failed for %d: %s", c["id"], e)
            else:
                logger.info("[%d/%d] %s: no snippet found", i+1, len(centers), clean_name[:40])
        else:
            logger.info("[%d/%d] %s: Google blocked/no result", i+1, len(centers), clean_name[:40])

    logger.info("Done. Updated %d/%d centers.", updated, len(centers))

if __name__ == "__main__":
    main()
