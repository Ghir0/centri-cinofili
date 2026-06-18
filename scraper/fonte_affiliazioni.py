"""
Fonte 1: ENCI e affiliazioni ufficiali.

ENCI pubblica un elenco di centri cinofili affiliati su:
  https://www.enci.it/soci/allevatori-e-affissi

L'approccio è:
1. Recuperare le pagine regionali/provinciali dell'ENCI
2. Estrarre nome centro, indirizzo, contatti
3. Normalizzare nel formato CentroRaw
"""

from __future__ import annotations

import logging
import re
from typing import Iterator

from bs4 import BeautifulSoup, Tag

from .core import CentroRaw, Fetcher, extract_contacts_from_text

logger = logging.getLogger("scraper.enci")

# URL delle pagine ENCI con elenco centri per regione
ENCI_BASE = "https://www.enci.it"
ENCI_CENTRI_URL = f"{ENCI_BASE}/addestratori-e-handler/centri-cinofili"


# ── Mappa regioni ENCI ai nomi canonici ──────────────────────
REGIONI_ITALIANE = [
    "abruzzo", "basilicata", "calabria", "campania", "emilia-romagna",
    "friuli-venezia-giulia", "lazio", "liguria", "lombardia", "marche",
    "molise", "piemonte", "puglia", "sardegna", "sicilia", "toscana",
    "trentino-alto-adige", "umbria", "valle-d-aosta", "veneto",
]


def scrape_enci(fetcher: Fetcher, regione: str | None = None) -> list[CentroRaw]:
    """Scraping centri cinofili dal sito ENCI.

    Args:
        fetcher: Fetcher HTTP configurato
        regione: Nome regione (es. 'marche') o None per tutte

    Returns:
        Lista di CentroRaw
    """
    risultati: list[CentroRaw] = []

    # Tentativo 1: pagina centri cinofili nazionale
    soup = fetcher.get_soup(ENCI_CENTRI_URL)
    if soup is None:
        logger.warning("ENCI: impossibile raggiungere %s", ENCI_CENTRI_URL)
        return risultati

    # Cerca link regionali
    region_links = _find_region_links(soup, regione)
    logger.info("ENCI: trovati %d link regionali", len(region_links))

    for nome_reg, url in region_links:
        logger.info("ENCI: scraping %s (%s)", nome_reg, url)
        centri_regione = _scrape_enci_region(fetcher, url, nome_reg)
        risultati.extend(centri_regione)
        logger.info("ENCI: estratti %d centri da %s", len(centri_regione), nome_reg)

    return risultati


def _find_region_links(soup: BeautifulSoup, target_regione: str | None) -> list[tuple[str, str]]:
    """Trova i link alle pagine regionali ENCI."""
    links: list[tuple[str, str]] = []

    # Pattern comuni: link che contengono il nome della regione
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        text = a.get_text(strip=True).lower()

        # Skip link non rilevanti
        if not text:
            continue

        # Check se il testo o l'href contengono una regione
        for reg in REGIONI_ITALIANE:
            if reg in text or reg in href.lower():
                nome = reg
                break
        else:
            continue

        if target_regione and nome != target_regione.lower():
            continue

        full_url = href if href.startswith("http") else f"{ENCI_BASE}{href}"
        links.append((nome, full_url))

    # Deduplica per URL
    seen: set[str] = set()
    unique: list[tuple[str, str]] = []
    for nome, url in links:
        if url not in seen:
            seen.add(url)
            unique.append((nome, url))

    return unique


def _scrape_enci_region(fetcher: Fetcher, url: str, regione: str) -> list[CentroRaw]:
    """Scraping di una pagina regionale ENCI."""
    risultati: list[CentroRaw] = []
    soup = fetcher.get_soup(url)
    if soup is None:
        return risultati

    # Pattern 1: tabella centri
    table = soup.find("table")
    if table:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue
            raw = _parse_enci_row(cells, regione)
            if raw:
                risultati.append(raw)

    # Pattern 2: lista / card
    if not risultati:
        cards = soup.find_all(["article", "div"], class_=re.compile(r"centro|card|item|entry", re.I))
        for card in cards:
            raw = _parse_enci_card(card, regione)
            if raw:
                risultati.append(raw)

    # Pattern 3: fallback — paragrafi strutturati
    if not risultati:
        raw_list = _parse_enci_text(soup, regione)
        risultati.extend(raw_list)

    return risultati


def _parse_enci_row(cells: list[Tag], regione: str) -> CentroRaw | None:
    """Parsing di una riga tabella ENCI."""
    texts = [c.get_text(" ", strip=True) for c in cells]

    # Euristica: la prima colonna è il nome, le altre indirizzo/contatti
    nome = texts[0] if len(texts) > 0 else None
    if not nome or len(nome) < 3:
        return None
    # Filtro header
    if nome.lower() in ("denominazione", "nome", "centro", "ragione sociale", "centri cinofili"):
        return None

    raw = CentroRaw(
        ragione_sociale=nome,
        regione=regione,
        fonte="enci",
        fonte_url=str(cells[0].find_parent("table")),
    )

    # Indirizzo e contatti dalle altre colonne
    full_text = " ".join(texts[1:]) if len(texts) > 1 else ""
    _fill_location_and_contacts(raw, full_text)

    return raw


def _parse_enci_card(card: Tag, regione: str) -> CentroRaw | None:
    """Parsing di una card/list-item ENCI."""
    text = card.get_text(" ", strip=True)
    if len(text) < 10:
        return None

    # Estrai nome (primo heading o testo significativo)
    heading = card.find(["h2", "h3", "h4", "strong"])
    nome = heading.get_text(strip=True) if heading else text.split(".")[0].strip()[:100]

    if len(nome) < 3:
        return None

    raw = CentroRaw(
        ragione_sociale=nome,
        regione=regione,
        fonte="enci",
        fonte_url=str(card),
    )
    _fill_location_and_contacts(raw, text)
    return raw


def _parse_enci_text(soup: BeautifulSoup, regione: str) -> list[CentroRaw]:
    """Fallback: parsing testo libero della pagina ENCI."""
    risultati: list[CentroRaw] = []

    # Cerca blocchi di testo che sembrano indirizzi
    main = soup.find("main") or soup.find("body") or soup
    if main is None:
        return risultati

    text = main.get_text("\n", strip=True)
    lines = text.split("\n")

    current_name: str | None = None
    current_text: str = ""

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Euristica: nuova entry quando troviamo un nome seguito da indirizzo
        if _looks_like_center_name(line) and current_name:
            raw = _make_raw(current_name, current_text, regione)
            if raw:
                risultati.append(raw)
            current_name = line
            current_text = ""
        elif _looks_like_center_name(line):
            current_name = line
            current_text = ""
        elif current_name:
            current_text += " " + line

    # Ultima entry
    if current_name:
        raw = _make_raw(current_name, current_text, regione)
        if raw:
            risultati.append(raw)

    return risultati


def _looks_like_center_name(text: str) -> bool:
    """Euristica: questa riga sembra il nome di un centro cinofilo?"""
    keywords = ["centro cinofilo", "asd", "a.s.d.", "ssd", "s.s.d.", "cinofilia",
                "dog", "cane", "addestramento", "educazione", "allevamento"]
    text_lower = text.lower()
    return any(kw in text_lower for kw in keywords) and len(text) > 5


def _make_raw(nome: str, text: str, regione: str) -> CentroRaw:
    raw = CentroRaw(
        ragione_sociale=nome.strip(),
        regione=regione,
        fonte="enci",
    )
    _fill_location_and_contacts(raw, text)
    return raw


def _fill_location_and_contacts(raw: CentroRaw, text: str) -> None:
    """Riempie indirizzo e contatti da testo libero."""
    # Contatti
    contacts = extract_contacts_from_text(text)
    if contacts.get("telefono"):
        raw.telefono = contacts["telefono"]
    if contacts.get("email"):
        raw.email = contacts["email"]
    if contacts.get("social_links"):
        raw.social_links.update(contacts["social_links"])

    # Sito web
    site_match = re.search(r"(?:https?://)?[a-zA-Z0-9][\w.-]+\.[a-zA-Z]{2,}(?:/\S*)?", text)
    if site_match and "facebook" not in site_match.group(0) and "instagram" not in site_match.group(0):
        url = site_match.group(0)
        if not url.startswith("http"):
            url = "https://" + url
        raw.sito_web = url

    # Indirizzo — cerca pattern "Via/Piazza/Corso ..."
    addr_match = re.search(
        r"(?:Via|Viale|Piazza|P.zza|Corso|Strada|Località|Loc\.|Contrada|S\.P\.|S\.S\.)\s+\S.+?(?=Tel|Telefono|Cell|\+|@|www\.|http|$)",
        text,
        re.IGNORECASE,
    )
    if addr_match:
        raw.indirizzo = addr_match.group(0).strip().rstrip(",-.")

    # Comune — cerca pattern "città (XX)" o "città"
    comune_match = re.search(
        r"(\d{5})\s+([A-Z][a-zàèéìòù]+(?:\s[A-Z][a-zàèéìòù]+)*)",
        text,
    )
    if comune_match:
        raw.cap = comune_match.group(1)
        raw.comune = comune_match.group(2).title()
    else:
        # Fallback: cerca dopo prov
        prov_match = re.search(r"\(([A-Z]{2})\)", text)
        if prov_match:
            raw.provincia = prov_match.group(1).upper()
            # Prova a prendere la parola prima della provincia come comune
            before_prov = text[:prov_match.start()].strip()
            words = before_prov.split()
            if words:
                raw.comune = words[-1].strip(",- ").title()

    # Affiliazione
    raw.affiliazioni.append("enci")


# ──────────────────────────────────────────────────────────────
# FICSS, CSEN, OPES — fonti secondarie
# ──────────────────────────────────────────────────────────────

FICSS_URL = "https://www.ficss.it/societa-affiliate/"
CSEN_URL = "https://www.csen.it/settori/cinofilia/"
OPES_URL = "https://www.opesitalia.it/cinofilia/"


def scrape_affiliazioni_secondarie(fetcher: Fetcher, regione: str | None = None) -> list[CentroRaw]:
    """Scraping da FICSS, CSEN, OPES."""
    risultati: list[CentroRaw] = []
    fonti = [
        (FICSS_URL, "ficss"),
        (CSEN_URL, "csen"),
        (OPES_URL, "opes-cinofilia"),
    ]

    for url, fonte in fonti:
        logger.info("Affiliazioni: scraping %s", url)
        soup = fetcher.get_soup(url)
        if soup is None:
            continue

        centri = _scrape_affiliazione_generica(soup, fonte, regione)
        logger.info("%s: estratti %d centri", fonte, len(centri))
        risultati.extend(centri)

    return risultati


def _scrape_affiliazione_generica(
    soup: BeautifulSoup, fonte: str, regione: str | None
) -> list[CentroRaw]:
    """Scraping generico di una pagina affiliati."""
    risultati: list[CentroRaw] = []

    # Pattern comuni: tabelle, liste, card
    tables = soup.find_all("table")
    for table in tables:
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) < 1:
                continue
            texts = [c.get_text(" ", strip=True) for c in cells]
            nome = texts[0]
            if not nome or len(nome) < 3:
                continue
            if nome.lower() in ("denominazione", "nome", "società", "associazione", "centro"):
                continue

            raw = CentroRaw(ragione_sociale=nome, fonte=fonte)
            raw.affiliazioni.append(fonte)
            full_text = " ".join(texts[1:]) if len(texts) > 1 else ""
            _fill_location_and_contacts(raw, full_text)

            if regione is None or (raw.regione and regione.lower() in raw.regione.lower()):
                risultati.append(raw)

    return risultati