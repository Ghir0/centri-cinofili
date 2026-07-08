"""Fonte: ENCI e affiliazioni ufficiali (FICSS, CSEN, OPES)."""

import logging, re
from .core import CentroRaw, Fetcher, extract_contacts

logger = logging.getLogger("scraper.enci")

ENCI_BASE = "https://www.enci.it"
ENCI_URL = f"{ENCI_BASE}/addestratori-e-handler/centri-cinofili"

def _fill(raw, text):
    c = extract_contacts(text)
    if c.get("telefono"): raw.telefono = c["telefono"]
    if c.get("email"): raw.email = c["email"]
    if c.get("social_links"): raw.social_links.update(c["social_links"])
    sm = re.search(r"(?:https?://)?[a-zA-Z0-9][\w.-]+\.[a-zA-Z]{2,}(?:/\S*)?", text)
    if sm and "facebook" not in sm.group() and "instagram" not in sm.group():
        url = sm.group()
        if not url.startswith("http"): url = "https://" + url
        raw.sito_web = url
    am = re.search(r"(?:Via|Viale|Piazza|Corso|Strada|Località|S\.P\.|S\.S\.)\s+\S.+?(?=Tel|Telefono|Cell|\+|@|www|http|$)", text, re.I)
    if am: raw.indirizzo = am.group().strip().rstrip(",-.")
    cm = re.search(r"(\d{5})\s+([A-Z][a-zàèéìòù]+(?:\s[A-Z][a-zàèéìòù]+)*)", text)
    if cm: raw.cap, raw.comune = cm.group(1), cm.group(2).title()
    pm = re.search(r"\(([A-Z]{2})\)", text)
    if pm: raw.provincia = pm.group(1).upper()

def scrape_enci(fetcher, regione=None):
    results = []
    soup = fetcher.get_soup(ENCI_URL)
    if not soup:
        logger.warning("ENCI unreachable: %s", ENCI_URL)
        return results

    main = soup.find("main") or soup.find("body") or soup
    # Cerca link a regioni
    region_links = []
    for a in soup.find_all("a", href=True):
        href = a.get("href","")
        txt = a.get_text(strip=True).lower()
        if "marche" in txt or "marche" in href.lower():
            full = href if href.startswith("http") else ENCI_BASE + href
            region_links.append(("marche", full))

    if not region_links:
        # Fallback: scraping diretto della pagina
        logger.info("ENCI: scraping pagina centrale (no link regionali trovati)")
        region_links.append(("italia", ENCI_URL))

    for rname, url in region_links:
        if regione and rname != regione.lower():
            continue
        logger.info("ENCI: scraping %s -> %s", rname, url)
        page = fetcher.get_soup(url)
        if not page:
            continue
        text = page.get_text(" ", strip=True)
        # Prova tabella
        table = page.find("table")
        if table:
            for row in table.find_all("tr"):
                cells = [c.get_text(" ", strip=True) for c in row.find_all(["td","th"])]
                if not cells or len(cells[0]) < 3 or cells[0].lower() in ("denominazione","nome","centro"):
                    continue
                raw = CentroRaw(ragione_sociale=cells[0], regione=rname, fonte="enci")
                raw.affiliazioni.append("enci")
                _fill(raw, " ".join(cells[1:]) if len(cells)>1 else "")
                results.append(raw)
        # Fallback: parsing testo
        if not results:
            for h in page.find_all(["h2","h3","strong"]):
                name = h.get_text(strip=True)
                if len(name) > 5 and any(kw in name.lower() for kw in ("centro","cinofil","dog","asd","a.s.d.","addestramento","allevamento")):
                    raw = CentroRaw(ragione_sociale=name, regione=rname, fonte="enci")
                    raw.affiliazioni.append("enci")
                    _fill(raw, text)
                    results.append(raw)

    return results

def scrape_altre_affiliazioni(fetcher, regione=None):
    results = []
    urls = [
        ("https://www.ficss.it/societa-affiliate/", "ficss"),
        ("https://www.csen.it/settori/cinofilia/", "csen"),
        ("https://www.opesitalia.it/cinofilia/", "opes-cinofilia"),
    ]
    for url, fonte in urls:
        soup = fetcher.get_soup(url)
        if not soup:
            continue
        for row in soup.find_all("tr"):
            cells = [c.get_text(" ", strip=True) for c in row.find_all(["td","th"])]
            if not cells or len(cells[0]) < 3 or cells[0].lower() in ("denominazione","nome","società"):
                continue
            raw = CentroRaw(ragione_sociale=cells[0], fonte=fonte)
            raw.affiliazioni.append(fonte)
            _fill(raw, " ".join(cells[1:]) if len(cells)>1 else "")
            results.append(raw)
        logger.info("%s: %d centri", fonte, len([r for r in results if r.fonte==fonte]))
    return results