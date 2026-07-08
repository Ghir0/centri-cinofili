"""
Fonte ENCI — usa l'API XML ufficiale di ENCI per estrarre tutti i centri cinofili.

API scoperta analizzando il controller JS:
  https://www.enci.it/scripts/Enci/Controllers/CentriCinofiliController.js

Endpoint dati:
  GET https://www.enci.it/umbraco/enci/CentriCinofiliCorsiApi/GetCentriCinofili
  → restituisce XML con tutti i centri affiliati (133 attivi a giugno 2026)

Campi disponibili:
  NomeCentro, Indirizzo, Localita, Cap, CodRegione, DesProvincia, CodProvincia,
  Email1, Email2, Tel1, Tel2, Cell1, Cell2, Web, NumeroCorsiProssimi
"""

import json
import logging
import xml.etree.ElementTree as ET
from typing import Iterator

import cloudscraper

from .core import CentroRaw

logger = logging.getLogger("scraper.enci_api")

ENCI_API_URL = "https://www.enci.it/umbraco/enci/CentriCinofiliCorsiApi/GetCentriCinofili"
NS = "{http://schemas.datacontract.org/2004/07/Enci.Service.ApiModels}"


def _phone_candidates(rec: dict) -> list[str]:
    """Estrae numeri di telefono candidati da Tel1/Tel2/Cell1/Cell2."""
    out = []
    for f in ("Tel1", "Tel2", "Cell1", "Cell2"):
        v = (rec.get(f) or "").strip()
        if v and not v.startswith("0"):
            # Formato: "NOME 3331234567" → prendi dopo lo spazio
            parts = v.split(None, 1)
            if len(parts) == 2 and parts[1].replace(" ", "").isdigit():
                v = parts[1]
        if v:
            out.append(v)
    return out


def scrape_enci_api(regione: str | None = None) -> list[CentroRaw]:
    """Scarica l'elenco completo dei centri ENCI dall'API XML ufficiale.

    Args:
        regione: slug regione (es. 'marche', 'lombardia') o None per tutte
    """
    logger.info("ENCI API: GET %s", ENCI_API_URL)
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(ENCI_API_URL, timeout=30)
    resp.raise_for_status()

    # ENCI restituisce XML, non JSON
    root = ET.fromstring(resp.content)

    raw_records: list[dict] = []
    for r_xml in root.findall(f"{NS}CentriCinofiliSearchResult"):
        rec = {}
        for child in r_xml:
            tag = child.tag.replace(NS, "")
            rec[tag] = (child.text or "").strip()
        raw_records.append(rec)

    logger.info("ENCI API: %d record totali", len(raw_records))

    # Filtra solo attivi (Status == 'true')
    active = [r for r in raw_records if r.get("Status", "").lower() == "true"]
    logger.info("ENCI API: %d record attivi", len(active))

    # Filtra per regione se richiesto
    regione_code_map = {
        "abruzzo": "ABR",
        "basilicata": "BAS",
        "calabria": "CAL",
        "campania": "CAM",
        "emilia-romagna": "EMR",
        "friuli-venezia-giulia": "FVG",
        "lazio": "LAZ",
        "liguria": "LIG",
        "lombardia": "LOM",
        "marche": "MAR",
        "molise": "MOL",
        "piemonte": "PIE",
        "puglia": "PUG",
        "sardegna": "SAR",
        "sicilia": "SIC",
        "toscana": "TOS",
        "trentino-alto-adige": "TAA",
        "umbria": "UMB",
        "valle-d-aosta": "VDA",
        "veneto": "VEN",
    }

    if regione:
        target_code = regione_code_map.get(regione.lower())
        if not target_code:
            logger.warning("ENCI API: codice regione non trovato per '%s'", regione)
            return []
        active = [r for r in active if r.get("CodRegione", "").upper() == target_code]
        logger.info("ENCI API: %d record per regione '%s' (%s)", len(active), regione, target_code)

    # Converti in CentroRaw
    results: list[CentroRaw] = []
    for rec in active:
        nome = rec.get("NomeCentro", "").strip()
        if not nome:
            continue

        phones = _phone_candidates(rec)
        tel = phones[0] if phones else None

        sito = rec.get("Web", "").strip() or None
        if sito and not sito.startswith("http"):
            sito = "https://" + sito

        email = rec.get("Email1", "").strip() or None

        raw = CentroRaw(
            ragione_sociale=nome,
            indirizzo=rec.get("Indirizzo", "").strip() or None,
            comune=rec.get("Localita", "").strip() or None,
            cap=rec.get("Cap", "").strip() or None,
            provincia=rec.get("CodProvincia", "").strip() or None,
            regione=regione.lower() if regione else None,
            telefono=tel,
            email=email,
            sito_web=sito,
            affiliazioni=["enci"],
            fonte="enci_api",
            fonte_url=ENCI_API_URL,
        )

        results.append(raw)

    logger.info("ENCI API: %d CentroRaw pronti", len(results))
    return results


if __name__ == "__main__":
    import sys
    reg = sys.argv[1] if len(sys.argv) > 1 else None
    results = scrape_enci_api(regione=reg)
    print(f"Trovati {len(results)} centri")
    for r in results[:5]:
        print(f"  - {r.ragione_sociale} | {r.comune} ({r.provincia}) | {r.telefono} | {r.email}")
