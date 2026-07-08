"""
Fonti aggiuntive affiliazioni: ASC Cinofilia e CSEN Cinofilia.

ASC: https://www.ascinofilia.it/asd-ssd/elenco-affiliati/
  Tabella: Affiliata | Regione | E-Mail
  ~64 record

CSEN: https://discipline.csencinofilia.it/elenco-centri/
  Tabella: Nome Centro | Localita (con telefono concatenato) | Telefono | Email | Referente
  ~19 record
"""

import logging
import re
from urllib.parse import urlparse

import cloudscraper
from bs4 import BeautifulSoup

from .core import CentroRaw

logger = logging.getLogger("scraper.asc_csen")

ASC_URL = "https://www.ascinofilia.it/asd-ssd/elenco-affiliati/"
CSEN_URL = "https://discipline.csencinofilia.it/elenco-centri/"


def _normalize(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _slugify_localita(localita: str) -> tuple[str, str, str]:
    """Estrae comune e provincia da stringhe tipo 'Padova' o 'Via Roma 1, Milano (MI)'.

    Ritorna (indirizzo, comune, provincia_sigla)
    """
    localita = _normalize(localita)
    # Pattern: "Via/Piazza X, COMUNE (XX)" o "Via/Piazza X COMUNE (XX)"
    m = re.match(r"^(.*?)[,\s]+([A-Z][A-Za-z' ]+?)\s*\(([A-Z]{2})\)\s*$", localita)
    if m:
        return _normalize(m.group(1)), _normalize(m.group(2)), m.group(3).upper()

    # Pattern: "COMUNE (XX)"
    m = re.match(r"^([A-Z][A-Za-z' ]+?)\s*\(([A-Z]{2})\)\s*$", localita)
    if m:
        return "", _normalize(m.group(1)), m.group(2).upper()

    # Solo comune
    if localita:
        return "", localita, ""
    return "", "", ""


def scrape_asc(scraper: cloudscraper.CloudScraper) -> list[CentroRaw]:
    """Scarica tabella affiliati ASC."""
    logger.info("ASC: GET %s", ASC_URL)
    try:
        r = scraper.get(ASC_URL, timeout=30)
        r.raise_for_status()
    except Exception as e:
        logger.error("ASC fallita: %s", e)
        return []

    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table")
    if not table:
        logger.warning("ASC: tabella non trovata")
        return []

    results: list[CentroRaw] = []
    rows = table.find_all("tr")
    for row in rows:
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if len(cells) < 2:
            continue
        # Header?
        if "affiliata" in cells[0].lower():
            continue

        nome = _normalize(cells[0])
        if not nome:
            continue

        regione_nome = _normalize(cells[1]) if len(cells) > 1 else ""
        email = _normalize(cells[2]) if len(cells) > 2 else ""

        raw = CentroRaw(
            ragione_sociale=nome,
            regione=regione_nome.lower() if regione_nome else None,
            email=email or None,
            affiliazioni=["asc"],
            fonte="asc_elenco_affiliati",
            fonte_url=ASC_URL,
        )
        results.append(raw)

    logger.info("ASC: %d record", len(results))
    return results


def scrape_csen(scraper: cloudscraper.CloudScraper) -> list[CentroRaw]:
    """Scarica elenco centri tecnici CSEN."""
    logger.info("CSEN: GET %s", CSEN_URL)
    try:
        r = scraper.get(CSEN_URL, timeout=30)
        r.raise_for_status()
    except Exception as e:
        logger.error("CSEN fallita: %s", e)
        return []

    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table")
    if not table:
        logger.warning("CSEN: tabella non trovata")
        return []

    results: list[CentroRaw] = []
    rows = table.find_all("tr")
    for row in rows:
        cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
        if len(cells) < 3:
            continue

        nome_citta_raw = _normalize(cells[0])
        # Spesso la prima cella contiene "NOME CENTROwww.sito.it" → separo
        nome_match = re.match(r"^(.+?)(www\.[^\s]+|[a-z0-9-]+\.(?:it|com|org))?\s*$", nome_citta_raw)
        nome = _normalize(nome_match.group(1)) if nome_match else nome_citta_raw

        # Riga CSEN può avere formati:
        # "All'Alba Dei Border Collie | Misano Di Gera D'Adda (BG) | 338/2309571 | edeenrivaa@gmail.com | Eden Riva"
        # oppure unione di localita+telefono nella seconda cella

        # Localita + telefono concatenato: "Misano Di Gera D'Adda (BG)338/2309571"
        cell1 = _normalize(cells[1]) if len(cells) > 1 else ""
        cell_tel = _normalize(cells[2]) if len(cells) > 2 else ""
        cell_email = _normalize(cells[3]) if len(cells) > 3 else ""
        cell_ref = _normalize(cells[4]) if len(cells) > 4 else ""

        # Estrai localita e telefono da cell1
        m_localita_tel = re.match(r"^(.+?\([A-Z]{2}\))\s*([\d/\.\s]+)?$", cell1)
        localita_str = m_localita_tel.group(1) if m_localita_tel else cell1
        tel_inline = m_localita_tel.group(2) if m_localita_tel else ""

        indirizzo, comune, provincia = _slugify_localita(localita_str)
        telefono = cell_tel or tel_inline or None

        # Email — a volte ha "\xa0" o spazi strani
        email = cell_email.replace("\xa0", "").strip() or None
        if email and "@" not in email:
            email = None

        raw = CentroRaw(
            ragione_sociale=nome,
            indirizzo=indirizzo or None,
            comune=comune or None,
            provincia=provincia or None,
            telefono=_normalize_phone_inline(telefono),
            email=email,
            affiliazioni=["csen"],
            fonte="csen_elenco_centri",
            fonte_url=CSEN_URL,
            descrizione=f"Referente: {cell_ref}" if cell_ref else None,
        )
        results.append(raw)

    logger.info("CSEN: %d record", len(results))
    return results


def _normalize_phone_inline(tel: str | None) -> str | None:
    """Normalizza telefono CSEN tipo '338/2309571' → '+39 338 2309571'."""
    if not tel:
        return None
    digits = re.sub(r"[^\d]", "", tel)
    if not digits:
        return None
    if not digits.startswith("39"):
        digits = "39" + digits
    return "+" + " ".join([digits[0:3], digits[3:6], digits[6:]]) if len(digits) >= 9 else "+" + digits


def scrape_asc_csen() -> list[CentroRaw]:
    """Scarica entrambe le fonti."""
    scraper = cloudscraper.create_scraper()
    results: list[CentroRaw] = []
    results.extend(scrape_asc(scraper))
    results.extend(scrape_csen(scraper))
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = scrape_asc_csen()
    print(f"\nTotale: {len(results)} record")
    by_source = {}
    for r in results:
        s = r.fonte
        by_source.setdefault(s, []).append(r)
    for src, recs in by_source.items():
        print(f"  {src}: {len(recs)}")
        for r in recs[:3]:
            print(f"    - {r.ragione_sociale} | {r.comune or '?'} ({r.provincia or '?'}) | {r.email or '-'}")
