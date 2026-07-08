"""
Scraper Centri Cinofili — Runner principale.

Usage:
    python -m scraper --regione marche          # Singola regione (tutte le fonti)
    python -m scraper --regione marche --dry-run # Solo ENCI (API ufficiale)
    python -m scraper --all                      # Tutte le regioni
    python -m scraper --enci-only                # Solo ENCI, Italia intera
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .comuni import get_comuni_for_regione, get_tutte_le_regioni
from .core import CentroRaw, Fetcher, deduplicate, normalize
from .fonte_enci_api import scrape_enci_api
from .fonte_google_maps import scrape_google_maps
from .fonte_google_search import scrape_google_search
from .fonte_affiliazioni import scrape_altre_affiliazioni
from .fonte_asc_csen import scrape_asc_csen

logger = logging.getLogger("scraper.runner")
OUT = Path(__file__).resolve().parent.parent / "supabase" / "seeds"


def main():
    p = argparse.ArgumentParser(description="Scraper centri cinofili italiani")
    p.add_argument("--regione", "-r", help="Regione (slug: marche, emilia-romagna, ...)")
    p.add_argument("--all", "-a", action="store_true", help="Tutte le regioni")
    p.add_argument("--enci-only", action="store_true", help="Solo ENCI API su tutta Italia")
    p.add_argument("--fonte", "-f", choices=["enci","maps","search","affiliazioni","asc_csen"],
                   action="append", help="Fonti (default: enci + asc_csen + maps + search)")
    p.add_argument("--dry-run", action="store_true", help="Solo ENCI")
    p.add_argument("--no-search", action="store_true")
    p.add_argument("--no-maps", action="store_true")
    p.add_argument("--output", "-o", default=None)
    p.add_argument("--delay-min", type=float, default=2.0)
    p.add_argument("--delay-max", type=float, default=6.0)
    p.add_argument("--max-comuni", type=int, default=0)
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    if args.verbose:
        logging.getLogger("scraper").setLevel(logging.DEBUG)

    # Regioni
    if args.enci_only:
        regioni = [None]  # ENCI API senza filtro regione → tutte
    elif args.all:
        regioni = get_tutte_le_regioni()
    elif args.regione:
        regioni = [args.regione.lower()]
    else:
        p.error("Specifica --regione, --all, o --enci-only")

    # Fonti
    if args.dry_run or args.enci_only:
        fonti = ["enci", "asc_csen"]
    elif args.fonte:
        fonti = args.fonte
    else:
        fonti = ["enci", "asc_csen", "maps", "search"]  # default

    if args.no_search and "search" in fonti:
        fonti.remove("search")
    if args.no_maps and "maps" in fonti:
        fonti.remove("maps")

    output_dir = Path(args.output) if args.output else OUT
    output_dir.mkdir(parents=True, exist_ok=True)

    fetcher = Fetcher(min_delay=args.delay_min, max_delay=args.delay_max)

    for regione_slug in regioni:
        label = regione_slug or "italia"
        logger.info("=" * 60)
        logger.info("REGIONE: %s | Fonti: %s", label, ",".join(fonti))
        logger.info("=" * 60)

        all_raw: list[CentroRaw] = []

        # Fonte 1: ENCI API ufficiale (PRINCIPALE)
        if "enci" in fonti:
            logger.info("--- ENCI API ---")
            try:
                enci_results = scrape_enci_api(regione=regione_slug)
                all_raw.extend(enci_results)
                logger.info("ENCI: %d centri", len(enci_results))
            except Exception as e:
                logger.error("ENCI fallita: %s", e, exc_info=args.verbose)

        # Fonte 2: altre affiliazioni (FICSS/CSEN/OPES)
        if "affiliazioni" in fonti and regione_slug:
            logger.info("--- Altre affiliazioni ---")
            try:
                other = scrape_altre_affiliazioni(fetcher, regione=regione_slug)
                all_raw.extend(other)
            except Exception as e:
                logger.error("Affiliazioni fallite: %s", e)

        # Fonte 2b: ASC + CSEN (tabelle pubbliche HTML)
        if "asc_csen" in fonti:
            logger.info("--- ASC + CSEN ---")
            try:
                asc_csen_results = scrape_asc_csen()
                all_raw.extend(asc_csen_results)
                logger.info("ASC+CSEN: %d centri", len(asc_csen_results))
            except Exception as e:
                logger.error("ASC+CSEN fallita: %s", e)

        # Per Google Maps/Search serve la lista comuni
        comuni = []
        if regione_slug and ("maps" in fonti or "search" in fonti):
            comuni = get_comuni_for_regione(regione_slug)
            if args.max_comuni > 0:
                comuni = comuni[:args.max_comuni]
            logger.info("Comuni: %d", len(comuni))

        if "maps" in fonti and comuni:
            logger.info("--- Google Maps ---")
            try:
                maps_results = scrape_google_maps(fetcher, regione_slug, comuni)
                all_raw.extend(maps_results)
                logger.info("Maps: %d centri", len(maps_results))
            except Exception as e:
                logger.error("Maps fallita: %s", e)

        if "search" in fonti and comuni:
            logger.info("--- Google Search ---")
            try:
                search_results = scrape_google_search(fetcher, regione_slug, comuni)
                all_raw.extend(search_results)
                logger.info("Search: %d centri", len(search_results))
            except Exception as e:
                logger.error("Search fallita: %s", e)

        logger.info("Raw total: %d", len(all_raw))
        normalized = [n for n in (normalize(r) for r in all_raw) if n]
        deduped = deduplicate(normalized)
        logger.info("Dopo dedup: %d centri unici", len(deduped))

        # File output
        existing = sorted(output_dir.glob("*.json"))
        next_num = 2
        for sf in existing:
            try:
                n = int(sf.stem.split("_")[0])
                if n >= next_num:
                    next_num = n + 1
            except Exception:
                pass

        out = output_dir / f"{next_num:05d}_{label}_scraped.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(deduped, f, ensure_ascii=False, indent=2)
        logger.info("SAVED: %s (%d centri)", out, len(deduped))

        # Report
        if deduped:
            gps = sum(1 for c in deduped if c.get("coordinate_gps"))
            tel = sum(1 for c in deduped if c.get("telefono"))
            web = sum(1 for c in deduped if c.get("sito_web"))
            email = sum(1 for c in deduped if c.get("email"))
            print(f"\nReport {label}: {len(deduped)} centri | "
                  f"GPS:{gps} | Tel:{tel} | Web:{web} | Email:{email}")

    logger.info("Done!")


if __name__ == "__main__":
    main()