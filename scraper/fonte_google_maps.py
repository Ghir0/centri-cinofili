"""
Fonte 2: Google Maps scraping gratuito (via Google Search + Places redirect).

Approccio completamente gratuito, senza SerpAPI:
1. Cerca su Google: "centro cinofilo [comune]" + site:google.com/maps
2. Segue i redirect a Google Maps per estrarre dati dai risultati
3. Fallback: usa Google Search per identificare centri e poi cerca info sui loro siti

Limitazioni senza API key:
- Dati GPS approssimativi (da geocoding testuale o dai siti web)
- Meno risultati rispetto a Google Places API
- Rischio rate-limiting più alto
"""

from __future__ import annotations

import json
import logging
import re
import time
import urllib.parse
from typing import Any, Iterator

from bs4 import BeautifulSoup

from .core import CentroRaw, Fetcher, extract_contacts

logger = logging.getLogger("scraper.maps")

GOOGLE_SEARCH = "https://www.google.com/search"
GOOGLE_MAPS_SEARCH = "https://www.google.com/maps/search/"


def scrape_google_maps(
    fetcher: Fetcher,
    regione: str,
    comuni: list[str],
    query_templates: list[str] | None = None,
) -> list[CentroRaw]:
    """Cerca centri cinofili su Google Maps tramite Google Search.

    Args:
        fetcher: Fetcher HTTP
        regione: Nome regione per metadata
        comuni: Lista comuni da cercare
        query_templates: Template query di ricerca

    Returns:
        Lista di CentroRaw
    """
    if query_templates is None:
        query_templates = [
            "centro cinofilo {comune}",
            "addestratore cinofilo {comune}",
            "educatore cinofilo {comune}",
            "campo cinofilo {comune}",
            "pensione cani addestramento {comune}",
            "agility dog {comune}",
        ]

    risultati: list[CentroRaw] = []

    for comune in comuni:
        for template in query_templates:
            query = template.format(comune=comune, regione=regione)
            logger.info("Google Maps Search: '%s'", query)

            centri = _search_google_for_maps_results(fetcher, query, regione)
            risultati.extend(centri)

            # Delay extra per evitare rate limiting su Google
            time.sleep(random.uniform(3, 8))

    # Deduplica
    return risultati


def _search_google_for_maps_results(
    fetcher: Fetcher, query: str, regione: str
) -> list[CentroRaw]:
    """Esegue una Google Search, estrae risultati che puntano a Google Maps.

    Google Search parametri (approccio gratuito):
    - q: query
    - hl=it: lingua italiana
    - gl=it: geolocalizzazione Italia
    """
    params = {
        "q": query,
        "hl": "it",
        "gl": "it",
        "num": 20,  # Più risultati
    }
    url = f"{GOOGLE_SEARCH}?{urllib.parse.urlencode(params)}"

    soup = fetcher.get_soup(url, referer="https://www.google.com/")
    if soup is None:
        return []

    risultati: list[CentroRaw] = []

    # Estrai risultati organici
    for result in soup.select("div.g, div[data-hveid], div.MjjYud"):
        # Link
        link_elem = result.select_one("a[href]")
        if not link_elem:
            continue
        href = link_elem.get("href", "")

        # Titolo
        title_elem = result.select_one("h3")
        titolo = title_elem.get_text(strip=True) if title_elem else ""

        # Snippet
        snippet_elems = result.select("div.VwiC3b, span.st, div[data-sncf]")
        snippet = " ".join(e.get_text(strip=True) for e in snippet_elems)

        if not titolo and not snippet:
            continue

        combined = f"{titolo} {snippet}"

        # Check se è un risultato Google Maps o sembra un centro cinofilo
        is_maps = "google.com/maps" in href.lower() or "/maps/place" in href.lower()
        is_relevant = _is_center_related(combined)

        if not (is_maps or is_relevant):
            continue

        raw = CentroRaw(
            ragione_sociale=titolo if titolo else None,
            regione=regione,
            fonte="google_maps",
            fonte_url=href,
        )

        # Estrai contatti dallo snippet
        contacts = extract_contacts(combined)
        raw.telefono = contacts.get("telefono")
        raw.email = contacts.get("email")
        if contacts.get("social_links"):
            raw.social_links.update(contacts["social_links"])

        # Prova ad estrarre indirizzo
        _extract_address_from_snippet(raw, combined)

        # Prova a ottenere più dettagli dalla pagina Maps
        if is_maps:
            _enrich_from_maps_page(fetcher, raw, href)

        if raw.ragione_sociale or raw.indirizzo:
            risultati.append(raw)

    return risultati


def _is_center_related(text: str) -> bool:
    """Verifica se il testo è relativo a un centro cinofilo."""
    keywords = [
        "centro cinofilo", "addestratore", "educatore cinofilo",
        "campo cinofilo", "agility", "dog", "cani", "cinofilia",
        "allevamento", "pensione cani", "toelettatura",
    ]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords)


RE_ADDRESS_FROM_SNIPPET = re.compile(
    r"(?:Via|Viale|Piazza|Corso|Strada|Località|S\.P\.|S\.S\.)\s+\S.+?(?:\d{5})?\s+([A-Z][a-zàèéìòù]+(?:\s[A-Z][a-zàèéìòù]+)*)",
    re.IGNORECASE,
)


def _extract_address_from_snippet(raw: CentroRaw, text: str) -> None:
    """Estrae indirizzo e comune da uno snippet Google."""
    # Pattern: "Via/Piazza X, CAP Città"
    m = RE_ADDRESS_FROM_SNIPPET.search(text)
    if m:
        raw.indirizzo = m.group(0).strip().rstrip(",-")
        raw.comune = m.group(1).title()

    # CAP
    cap_match = re.search(r"\b(\d{5})\b", text)
    if cap_match:
        raw.cap = cap_match.group(1)

    # Provincia (tra parentesi)
    prov_match = re.search(r"\(([A-Z]{2})\)", text)
    if prov_match:
        raw.provincia = prov_match.group(1).upper()

    # Coordinate GPS (se presenti nel testo)
    coord_match = re.search(
        r"(\d{1,2}\.\d+),\s*(-?\d{1,3}\.\d+)",
        text,
    )
    if coord_match:
        lon, lat = coord_match.group(1), coord_match.group(2)
        raw.coordinate_gps = f"POINT({lon} {lat})"


def _enrich_from_maps_page(fetcher: Fetcher, raw: CentroRaw, url: str) -> None:
    """Tenta di estrarre più dettagli da una pagina Google Maps."""
    soup = fetcher.get_soup(url, referer="https://www.google.com/maps")
    if soup is None:
        return

    # Nome del posto
    title = soup.select_one("h1, meta[property='og:title']")
    if title:
        name = title.get("content", "") if title.name == "meta" else title.get_text(strip=True)
        if name and (not raw.ragione_sociale or len(name) > len(raw.ragione_sociale)):
            raw.ragione_sociale = name

    # Coordinate GPS da meta
    meta_geo = soup.select_one("meta[property='place:location:latitude']")
    if meta_geo:
        lat = meta_geo.get("content", "")
        lon_meta = soup.select_one("meta[property='place:location:longitude']")
        lon = lon_meta.get("content", "") if lon_meta else ""
        if lat and lon:
            raw.coordinate_gps = f"POINT({lon} {lat})"

    # Telefono da meta
    meta_tel = soup.select_one("meta[property='business:contact_data:phone_number']")
    if meta_tel:
        raw.telefono = meta_tel.get("content", "")

    # Sito web
    meta_site = soup.select_one("meta[property='business:contact_data:website']")
    if meta_site and not raw.sito_web:
        raw.sito_web = meta_site.get("content", "")


# Ogmify: metodo alternativo usando Google Maps URL diretti
def scrape_google_maps_direct(
    fetcher: Fetcher,
    regione: str,
    queries: list[str],
) -> list[CentroRaw]:
    """Approccio diretto: cerca su google.com/maps/search con URL diretti.

    Questo metodo è più fragile (anti-bot di Google Maps è aggressivo)
    ma può funzionare con rate limiting sufficiente.
    """
    risultati: list[CentroRaw] = []

    for query in queries:
        encoded = urllib.parse.quote(query)
        url = f"{GOOGLE_MAPS_SEARCH}{encoded}"

        logger.info("Google Maps direct: %s", query)
        soup = fetcher.get_soup(url, referer="https://www.google.com/maps")
        if soup is None:
            continue

        # Estrai dati dai div dei risultati
        for card in soup.select("div[role='article'], div[data-result], div.Nv2PK"):
            name_elem = card.select_one("div.qBF1Pd, div.fontHeadlineSmall, span.fontHeadlineSmall")
            nome = name_elem.get_text(strip=True) if name_elem else ""

            if not nome or len(nome) < 3:
                continue

            raw = CentroRaw(
                ragione_sociale=nome,
                regione=regione,
                fonte="google_maps_direct",
                fonte_url=url,
            )

            # Estrai tutti i testi dalla card
            card_text = card.get_text(" ", strip=True)
            contacts = extract_contacts(card_text)
            raw.telefono = contacts.get("telefono")
            raw.email = contacts.get("email")

            _extract_address_from_snippet(raw, card_text)

            if raw.ragione_sociale:
                risultati.append(raw)

        # Delay extra per Maps
        time.sleep(random.uniform(5, 10))

    return risultati


import random  # noqa: E402 (usato sopra, import esplicito per chiarezza)
