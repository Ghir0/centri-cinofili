"""
Fonte 3: Google Search organica + scraping siti web.

Approccio:
1. Cerca su Google: "centro cinofilo [comune]" e query simili
2. Dai risultati organici, estrae URL di siti web di centri
3. Visita i siti web e estrae: contatti, descrizione, servizi, posizione GPS
"""

from __future__ import annotations

import logging
import random
import re
import time
import urllib.parse
from typing import Any

from bs4 import BeautifulSoup

from .core import CentroRaw, Fetcher, extract_contacts

logger = logging.getLogger("scraper.search")

GOOGLE_SEARCH = "https://www.google.com/search"

# Query template per ricerca organica
SEARCH_TEMPLATES = [
    'centro cinofilo "{comune}"',
    'addestratore cinofilo "{comune}"',
    'educatore cinofilo "{comune}"',
    'campo cinofilo "{comune}"',
    'agility dog "{comune}"',
    'pensione cani addestramento "{comune}"',
    'allevamento cinofilo "{comune}"',
    'scuola cani "{comune}"',
]


def scrape_google_search(
    fetcher: Fetcher,
    regione: str,
    comuni: list[str],
    max_per_comune: int = 5,
    visit_sites: bool = True,
) -> list[CentroRaw]:
    """Cerca centri cinofili via Google Search e visita i siti.

    Args:
        fetcher: Fetcher HTTP
        regione: Nome regione
        comuni: Lista comuni da cercare
        max_per_comune: Max risultati per comune
        visit_sites: Se True, visita i siti web per estrarre più dati

    Returns:
        Lista di CentroRaw
    """
    risultati: list[CentroRaw] = []
    seen_urls: set[str] = set()

    for comune in comuni:
        logger.info("Google Search per comune: %s", comune)

        for template in SEARCH_TEMPLATES:
            if len([r for r in risultati if r.comune == comune]) >= max_per_comune:
                break

            query = template.format(comune=comune)
            centri = _search_google_organic(fetcher, query, regione, comune)

            for raw in centri:
                dedup_key = (raw.ragione_sociale or "", raw.sito_web or "", raw.comune or "")
                if dedup_key in seen_urls:
                    continue
                seen_urls.add(dedup_key)
                risultati.append(raw)

            time.sleep(random.uniform(2, 5))

    # Visita siti web per arricchire dati
    if visit_sites:
        logger.info("Visitando %d siti web per arricchire i dati...", len(risultati))
        for raw in risultati:
            if raw.sito_web and "google.com" not in raw.sito_web:
                _enrich_from_website(fetcher, raw)
                time.sleep(random.uniform(1, 3))

    return risultati


def _search_google_organic(
    fetcher: Fetcher,
    query: str,
    regione: str,
    comune: str,
) -> list[CentroRaw]:
    """Esegue una Google Search organica."""
    params = {
        "q": query,
        "hl": "it",
        "gl": "it",
        "num": 10,
    }
    url = f"{GOOGLE_SEARCH}?{urllib.parse.urlencode(params)}"

    soup = fetcher.get_soup(url, referer="https://www.google.com/")
    if soup is None:
        return []

    risultati: list[CentroRaw] = []

    for result in soup.select("div.g, div[data-hveid], div.MjjYud"):
        # Link
        link_elem = result.select_one("a[href]")
        if not link_elem:
            continue
        href = link_elem.get("href", "")

        # Filtra link Google interni
        if "google.com" in href and "/maps" not in href and "/search" in href:
            continue

        # Titolo
        title_elem = result.select_one("h3")
        titolo = title_elem.get_text(strip=True) if title_elem else ""

        # Snippet
        snippet_elems = result.select("div.VwiC3b, span.st, div[data-sncf]")
        snippet = " ".join(e.get_text(strip=True) for e in snippet_elems)

        if not titolo and not snippet:
            continue

        combined = f"{titolo} {snippet}"

        # Verifica pertinenza
        if not _is_relevant(combined):
            continue

        # Pulisci URL
        clean_url = _clean_google_url(href)

        raw = CentroRaw(
            ragione_sociale=_extract_name_from_title(titolo),
            comune=comune,
            regione=regione,
            fonte="google_search",
            fonte_url=clean_url,
        )

        if not raw.ragione_sociale:
            continue

        # Estrai contatti
        contacts = extract_contacts(combined)
        raw.telefono = contacts.get("telefono")
        raw.email = contacts.get("email")
        if contacts.get("social_links"):
            raw.social_links.update(contacts["social_links"])

        # Sito web
        if clean_url and "google.com" not in clean_url:
            raw.sito_web = clean_url

        # Indirizzo
        _extract_address_from_snippet(raw, combined)

        risultati.append(raw)

    return risultati


def _is_relevant(text: str) -> bool:
    """Verifica pertinenza cinofila."""
    keywords = [
        "centro cinofilo", "addestratore", "educatore cinofilo",
        "campo cinofilo", "agility", "cani", "cinofilia", "dog",
        "allevamento", "pensione cani",
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


def _clean_google_url(href: str) -> str:
    """Pulisce un URL di redirect Google."""
    # /url?q=https://example.com&sa=...
    if href.startswith("/url?"):
        match = re.search(r"q=([^&]+)", href)
        if match:
            return urllib.parse.unquote(match.group(1))
        return href

    # URL diretto
    if href.startswith("http"):
        return href

    return href


RE_NAME_FROM_TITLE = re.compile(
    r"^(.+?)(?:\s*[-–—|]\s*|\s*:\s*|\s+\d{1,2}\s*(?:recensioni|review)|$)",
)


def _extract_name_from_title(title: str) -> str:
    """Estrae nome centro dal titolo Google."""
    # Rimuovi suffissi comuni
    title = re.sub(r"\s*[-–—]\s*(?:Google Maps|Home|Facebook|Instagram).*$", "", title, flags=re.I)
    title = re.sub(r"\s*[-–—]\s*\d+.*$", "", title)
    # Prendi fino al primo separatore significativo
    match = RE_NAME_FROM_TITLE.match(title)
    if match:
        name = match.group(1).strip()
        if len(name) > 3:
            return name
    return title.strip()


RE_ADDRESS = re.compile(
    r"(?:Via|Viale|Piazza|Corso|Strada|Località|Contrada|S\.P\.|S\.S\.)\s+\S.+?(?:\s|,)*(\d{5})?\s*([A-Z][a-zàèéìòù]+(?:\s[A-Z][a-zàèéìòù]+)*)",
    re.IGNORECASE,
)


def _extract_address_from_snippet(raw: CentroRaw, text: str) -> None:
    """Estrae indirizzo dal testo."""
    m = RE_ADDRESS.search(text)
    if m:
        raw.indirizzo = m.group(0).strip().rstrip(",-")
        if m.group(1):
            raw.cap = m.group(1)
        if m.group(2):
            raw.comune = raw.comune or m.group(2).title()

    # Provincia tra parentesi
    prov_match = re.search(r"\(([A-Z]{2})\)", text)
    if prov_match:
        raw.provincia = prov_match.group(1).upper()


# ── Website Enrichment ──────────────────────────────────────────────

# Regex per estrarre coordinate da siti web
RE_GPS_EMBED = re.compile(
    r"""(?:maps\.google\.com/\?q=|@|ll=|center=|q=loc:)
       (-?\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)""",
    re.VERBOSE | re.IGNORECASE,
)

RE_GPS_META = re.compile(
    r"""(-?\d{1,2}\.\d{2,})\s*[,;]\s*(-?\d{1,3}\.\d{2,})"""
)

RE_GPS_IFRAME = re.compile(
    r"""!1d(-?\d+\.\d+)!2d(-?\d+\.\d+)"""
)


def _enrich_from_website(fetcher: Fetcher, raw: CentroRaw) -> None:
    """Visita il sito web del centro per estrarre più dati."""
    if not raw.sito_web:
        return

    logger.debug("Visitando sito: %s", raw.sito_web)
    soup = fetcher.get_soup(raw.sito_web)
    if soup is None:
        return

    # Prendi tutto il testo della pagina
    text = soup.get_text(" ", strip=True)

    # Contatti dal sito
    contacts = extract_contacts(text)
    if contacts.get("telefono") and not raw.telefono:
        raw.telefono = contacts["telefono"]
    if contacts.get("email") and not raw.email:
        raw.email = contacts["email"]
    if contacts.get("social_links"):
        for platform, url in contacts["social_links"].items():
            if platform not in raw.social_links:
                raw.social_links[platform] = url

    # Coordinate GPS da embed Google Maps
    for pattern in [RE_GPS_EMBED, RE_GPS_META, RE_GPS_IFRAME]:
        if raw.coordinate_gps:
            break
        for m in pattern.finditer(text):
            if "embed" in pattern.pattern or "iframe" in pattern.pattern:
                lon, lat = m.group(1), m.group(2)
            else:
                lat, lon = m.group(1), m.group(2)
            raw.coordinate_gps = f"POINT({lon} {lat})"
            break

    # Cerca anche nei tag iframe e script
    if not raw.coordinate_gps:
        for iframe in soup.find_all("iframe"):
            src = iframe.get("src", "")
            for pattern in [RE_GPS_EMBED, RE_GPS_IFRAME]:
                m = pattern.search(src)
                if m:
                    lon, lat = ("embed" in pattern.pattern or "iframe" in pattern.pattern) and (m.group(1), m.group(2)) or (m.group(2), m.group(1))
                    raw.coordinate_gps = f"POINT({lon} {lat})"
                    break
            if raw.coordinate_gps:
                break

    # Descrizione (meta description o primi 300 caratteri testo)
    meta_desc = soup.select_one("meta[name='description'], meta[property='og:description']")
    if meta_desc:
        desc = meta_desc.get("content", "")
        if desc and len(desc) > 20:
            raw.descrizione = desc[:500]

    # Tassonomia dal testo del sito
    _extract_taxonomy_from_text(raw, text)

    # Social links dal footer/header
    _extract_social_links_from_html(raw, soup)


DISCIPLINE_KEYWORDS: dict[str, str] = {
    "agility": "agility",
    "rally": "rally-o",
    "rally-o": "rally-o",
    "rally obedience": "rally-o",
    "hoopers": "hoopers",
    "nosework": "nosework",
    "ricerca olfattiva": "nosework",
    "olfattiva": "nosework",
    "propriocezione": "propriocezione",
    "socializzazione": "socializzazione",
    "recupero comportamentale": "recupero",
    "cuccioli": "educazione base",
    "educazione base": "educazione base",
    "obbedienza": "obbedienza",
}

METODOLOGIE_KEYWORDS: dict[str, str] = {
    "rinforzo positivo": "gentile",
    "metodo gentile": "gentile",
    "cognitivo": "cognitivo-relazionale",
    "relazionale": "cognitivo-relazionale",
    "cognitivo-relazionale": "cognitivo-relazionale",
    "coercizione": "tradizionale",
    "correzione": "tradizionale",
}


def _extract_taxonomy_from_text(raw: CentroRaw, text: str) -> None:
    """Estrae discipline e metodologie dal testo del sito."""
    text_lower = text.lower()

    for keyword, slug in DISCIPLINE_KEYWORDS.items():
        if keyword in text_lower and slug not in raw.discipline:
            raw.discipline.append(slug)

    for keyword, slug in METODOLOGIE_KEYWORDS.items():
        if keyword in text_lower and slug not in raw.metodologie:
            raw.metodologie.append(slug)

    # Infrastrutture
    if "campo coperto" in text_lower or "indoor" in text_lower:
        raw.infrastrutture.append("campo coperto")
    if "campo" in text_lower and "recintato" in text_lower:
        raw.infrastrutture.append("campo recintato")
    elif "campo" in text_lower:
        raw.infrastrutture.append("campo")
    if "piscina" in text_lower and ("cane" in text_lower or "cinofil" in text_lower or "dog" in text_lower):
        raw.infrastrutture.append("piscina")
    if "pensione" in text_lower or "asilo" in text_lower:
        raw.infrastrutture.append("pensione")


def _extract_social_links_from_html(raw: CentroRaw, soup: BeautifulSoup) -> None:
    """Estrae social links dai link del footer/header."""
    social_domains = {
        "facebook.com": "facebook",
        "instagram.com": "instagram",
        "tiktok.com": "tiktok",
        "youtube.com": "youtube",
        "t.me": "telegram",
        "wa.me": "whatsapp",
    }

    for a in soup.find_all("a", href=True):
        href = a["href"].lower().strip()
        for domain, platform in social_domains.items():
            if domain in href and platform not in raw.social_links:
                raw.social_links[platform] = href
