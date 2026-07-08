"""
Enrichment delle entry OPES/ASC.

Cerca su Google ogni centro cinofilo (nome + comune), trova il sito web,
visita il sito per estrarre contatti e dati, geocodifica l'indirizzo.

Usage:
    python -m scraper.enrich_opes_asc

Input: supabase/seeds/00007_opes_asc_to_enrich.json
Output: supabase/seeds/00007_opes_asc_enriched.json
"""

from __future__ import annotations

import json, logging, os, random, re, sys, time, urllib.parse
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("opes_asc")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local")

INPUT = ROOT / "supabase" / "seeds" / "00007_opes_asc_to_enrich.json"
OUTPUT = ROOT / "supabase" / "seeds" / "00007_opes_asc_enriched.json"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


def _ua():
    return random.choice(USER_AGENTS)


def _soup(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def _get(url, referer=None, timeout=20):
    headers = {
        "User-Agent": _ua(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "DNT": "1",
    }
    if referer:
        headers["Referer"] = referer
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp
        except requests.HTTPError as e:
            status = e.response.status_code if e.response else 0
            if status == 429:
                time.sleep(10 * (attempt + 1))
            elif status >= 500:
                time.sleep(2 * (attempt + 1))
            elif status in (403, 404):
                return None
            else:
                return None
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    return None


def _extract_search_results(html: str) -> list[dict]:
    """Estrae risultati organici da una pagina SERP Google."""
    soup = _soup(html)
    results = []
    for g in soup.select("div.g, div[data-sokoban-container]"):
        a = g.select_one("a[href^='http']")
        if not a:
            continue
        href = a.get("href", "")
        # Salta Google Maps, immagini, etc.
        skip_domains = ["google.com/maps", "google.com/search", "youtube.com", "facebook.com/plugins"]
        if any(s in href for s in skip_domains):
            continue

        title_el = g.select_one("h3")
        title = title_el.get_text(strip=True) if title_el else ""
        snippet_el = g.select_one("div.VwiC3b, span.st, div[data-sncf]")
        snippet = snippet_el.get_text(strip=True) if snippet_el else ""
        if title and href:
            results.append({"title": title, "url": href, "snippet": snippet})
    return results


def _search_google(query: str) -> list[dict]:
    """Cerca su Google e restituisce risultati organici."""
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=it&num=10"
    resp = _get(url)
    if not resp:
        return []
    return _extract_search_results(resp.text)


def _extract_contacts_from_html(html: str) -> dict:
    """Estrae telefono, email, social da HTML."""
    result = {}

    # Telefono
    tel_patterns = [
        r'(?:Tel|Telefono|Phone|Chiama|Contattaci)[:\s]*([\+\d][\d\s\.\-\/\(\)]{7,18})',
        r'"telephone"\s*:\s*"([^"]+)"',
        r'href="tel:([^"]+)"',
        r'([\+]?3[0-9]{1,2}[\s\.\-]?[0-9]{3,4}[\s\.\-]?[0-9]{3,4})',
    ]
    for p in tel_patterns:
        m = re.search(p, html, re.I)
        if m:
            tel = re.sub(r'[^\d+]', '', m.group(1))
            if len(tel) >= 9:
                result["telefono"] = tel if tel.startswith("+") else f"+39 {tel[1:]}" if tel.startswith("0") else tel
                break

    # Email
    em = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', html, re.I)
    if em:
        result["email"] = em.group(0).lower()

    # Social
    social_patterns = {
        "instagram": r'(?:https?://)?(?:www\.)?instagram\.com/([A-Za-z0-9._]+)',
        "facebook": r'(?:https?://)?(?:www\.)?facebook\.com/([A-Za-z0-9._]+)',
        "tiktok": r'(?:https?://)?(?:www\.)?tiktok\.com/@([A-Za-z0-9._]+)',
        "youtube": r'(?:https?://)?(?:www\.)?youtube\.com/@([A-Za-z0-9._\-]+)',
    }
    social = {}
    for platform, pat in social_patterns.items():
        m = re.search(pat, html, re.I)
        if m:
            handle = m.group(1)
            if platform == "instagram":
                social["instagram"] = f"@{handle}"
            elif platform == "facebook":
                social["facebook"] = f"https://facebook.com/{handle}"
            elif platform == "tiktok":
                social["tiktok"] = f"@{handle}"
            elif platform == "youtube":
                social["youtube"] = f"https://youtube.com/@{handle}"
    if social:
        result["social_links"] = social

    # Indirizzo (pattern italiano)
    addr_m = re.search(r'(?:Via|via|Viale|viale|Piazza|piazza|Corso|corso|Strada|Contrada|Località)[\s]+([A-Za-zÀ-ÿ\s]+)[\s,]+(\d+[A-Za-z]?)[\s,\-]+(\d{5})[\s]+([A-ZÀ-Ÿ][a-zà-ÿ]+)', html)
    if addr_m:
        result["indirizzo"] = f"{addr_m.group(0).strip()}"
    elif not addr_m:
        # Fallback: cerca pattern indirizzo più generico nel footer
        addr_m2 = re.search(r'([A-Za-zÀ-ÿ\s]+)\s+(\d+[A-Za-z]?)\s*[\-–]\s*(\d{5})\s+([A-ZÀ-Ÿ][a-zà-ÿ]+)', html)
        if addr_m2:
            result["indirizzo"] = f"{addr_m2.group(0).strip()}"

    return result


def _geocode_osm(query: str) -> dict | None:
    """Geocodifica via Nominatim OSM (1 req/sec)."""
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1&countrycodes=it"
    resp = _get(url, timeout=15)
    if not resp:
        return None
    try:
        data = resp.json()
        if data:
            return {"lat": float(data[0]["lat"]), "lon": float(data[0]["lon"])}
    except Exception:
        pass
    return None


def enrich_entry(entry: dict, idx: int, total: int) -> dict:
    """Arricchisce una singola entry OPES/ASC."""
    nome = entry["nome"]
    comune = entry["comune"]
    source = entry.get("source", "OPES/ASC")

    logger.info("[%d/%d] %s | %s", idx, total, nome[:60], comune)

    result = dict(entry)  # copy
    result["affiliazioni"] = []

    # Determina affiliazione
    if source == "OPES":
        result["affiliazioni"] = ["opes"]
    elif source == "ASC":
        result["affiliazioni"] = ["asc"]
    else:
        result["affiliazioni"] = ["opes_asc"]

    # 1. Cerca su Google
    query = f'"{nome}" centro cinofilo {comune}'
    time.sleep(random.uniform(2, 4))
    serp_results = _search_google(query)

    if not serp_results:
        # Retry senza virgolette
        query2 = f'{nome} centro cinofilo {comune}'
        time.sleep(random.uniform(2, 4))
        serp_results = _search_google(query2)

    sito_web = None
    if serp_results:
        sito_web = serp_results[0]["url"]
        result["sito_web"] = sito_web

    # 2. Visita il sito per estrarre contatti
    if sito_web:
        time.sleep(random.uniform(2, 4))
        resp = _get(sito_web)
        if resp:
            site_info = _extract_contacts_from_html(resp.text)
            for k, v in site_info.items():
                if v and k not in result:
                    result[k] = v
            logger.info("  → Sito: %s | Tel: %s | Email: %s | Social: %s",
                        sito_web[:50],
                        result.get("telefono", "–"),
                        result.get("email", "–"),
                        list(result.get("social_links", {}).keys()))

    # 3. Geocodifica (comune o indirizzo)
    geo_query = result.get("indirizzo", f"{comune}, Italia")
    time.sleep(1.5)  # Nominatim rate limit
    coords = _geocode_osm(geo_query)
    if coords:
        result["coordinate_gps"] = coords
        logger.info("  → GPS: %.5f, %.5f", coords["lat"], coords["lon"])
    else:
        logger.info("  → GPS: non trovato")

    # 4. Genera slug
    raw_slug = nome.lower().replace(" ", "-").replace(".", "").replace("'", "")[:80]
    result["slug"] = re.sub(r"[^a-z0-9\-]", "", raw_slug).strip("-")

    return result


def main():
    if not INPUT.exists():
        logger.error("Input non trovato: %s", INPUT)
        sys.exit(1)

    entries = json.loads(INPUT.read_text(encoding="utf-8"))
    logger.info("Caricate %d entry da arricchire", len(entries))

    enriched = []
    for i, entry in enumerate(entries, 1):
        try:
            result = enrich_entry(entry, i, len(entries))
            enriched.append(result)
        except Exception as e:
            logger.error("Errore su %s: %s", entry.get("nome", "?")[:50], e)
            enriched.append(entry)  # Keep original on error

    # Salva
    OUTPUT.write_text(json.dumps(enriched, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("\n" + "=" * 50)
    logger.info("Salvate %d entry arricchite in %s", len(enriched), OUTPUT)

    # Statistiche
    con_sito = sum(1 for e in enriched if e.get("sito_web"))
    con_tel = sum(1 for e in enriched if e.get("telefono"))
    con_email = sum(1 for e in enriched if e.get("email"))
    con_gps = sum(1 for e in enriched if e.get("coordinate_gps"))
    con_social = sum(1 for e in enriched if e.get("social_links"))
    logger.info("  Con sito web:   %d/%d", con_sito, len(enriched))
    logger.info("  Con telefono:   %d/%d", con_tel, len(enriched))
    logger.info("  Con email:      %d/%d", con_email, len(enriched))
    logger.info("  Con coordinate: %d/%d", con_gps, len(enriched))
    logger.info("  Con social:     %d/%d", con_social, len(enriched))


if __name__ == "__main__":
    main()
