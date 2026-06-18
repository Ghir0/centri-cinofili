"""
Scraper Centri Cinofili — Runner principale.

Usage:
    python -m scraper --regione marche          # Singola regione
    python -m scraper --regione marche --dry-run # Solo fonti ufficiali
    python -m scraper --all                      # Tutte le regioni
    python -m scraper --regione marche --fonte enci  # Solo una fonte
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .comuni import get_comuni_for_regione, get_tutte_le_regioni
from .core import CentroRaw, Fetcher, deduplicate, normalize, _build_id
from .fonte_affiliazioni import scrape_enci, scrape_affiliazioni_secondarie
from .fonte_google_maps import scrape_google_maps
from .fonte_google_search import scrape_google_search

logger = logging.getLogger("scraper.runner")

# Output dir: supabase/seeds/
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "supabase" / "seeds"


def main():
    parser = argparse.ArgumentParser(
        description="Scraper centri cinofili italiani",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi:
  python -m scraper --regione marche
  python -m scraper --regione marche --fonte enci --fonte maps
  python -m scraper --all --no-search
  python -m scraper --regione marche --dry-run
        """,
    )
    parser.add_argument(
        "--regione", "-r",
        help="Regione da scrapare (slug: marche, emilia-romagna, etc.)",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Scrapa tutte le regioni",
    )
    parser.add_argument(
        "--fonte", "-f",
        choices=["enci", "maps", "search"],
        action="append",
        help="Fonti da usare (default: tutte)",
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Salta Google Search (più lento, più rate-limiting)",
    )
    parser.add_argument(
        "--no-maps",
        action="store_true",
        help="Salta Google Maps (più aggressivo anti-bot)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo fonti ufficiali (ENCI+affiliazioni), senza Google",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Directory output (default: supabase/seeds/)",
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=2.0,
        help="Delay minimo tra richieste in secondi (default: 2.0)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=6.0,
        help="Delay massimo tra richieste in secondi (default: 6.0)",
    )
    parser.add_argument(
        "--max-comuni",
        type=int,
        default=0,
        help="Max comuni da processare (0 = tutti, utile per test)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Logging DEBUG",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger("scraper").setLevel(logging.DEBUG)

    # Determina regioni
    if args.all:
        regioni = get_tutte_le_regioni()
    elif args.regione:
        regioni = [args.regione.lower()]
    else:
        parser.error("Specifica --regione o --all")

    # Determina fonti
    if args.dry_run:
        fonti = ["enci"]
    elif args.fonte:
        fonti = args.fonte
    else:
        fonti = ["enci", "maps", "search"]

    # Esclusioni
    if args.no_search and "search" in fonti:
        fonti.remove("search")
    if args.no_maps and "maps" in fonti:
        fonti.remove("maps")

    output_dir = Path(args.output) if args.output else DEFAULT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # Fetcher condiviso
    fetcher = Fetcher(
        min_delay=args.delay_min,
        max_delay=args.delay_max,
        timeout=30,
        max_retries=3,
    )

    for regione_slug in regioni:
        logger.info("=" * 60)
        logger.info("REGIONE: %s", regione_slug)
        logger.info("Fonti: %s", ", ".join(fonti))
        logger.info("=" * 60)

        all_raw: list[CentroRaw] = []

        # Fonte 1: ENCI e affiliazioni
        if "enci" in fonti:
            logger.info("─ Fonte 1/3: ENCI ─")
            try:
                enci_results = scrape_enci(fetcher, regione=regione_slug)
                all_raw.extend(enci_results)
                logger.info("ENCI: %d centri trovati", len(enci_results))
            except Exception as e:
                logger.error("ENCI fallito: %s", e, exc_info=args.verbose)

            logger.info("─ Fonte 1b/3: Affiliazioni secondarie (FICSS/CSEN/OPES) ─")
            try:
                other_results = scrape_affiliazioni_secondarie(fetcher, regione=regione_slug)
                all_raw.extend(other_results)
                logger.info("Affiliazioni secondarie: %d centri", len(other_results))
            except Exception as e:
                logger.error("Affiliazioni secondarie fallite: %s", e, exc_info=args.verbose)

        comuni = get_comuni_for_regione(regione_slug)
        if args.max_comuni > 0:
            comuni = comuni[:args.max_comuni]
        logger.info("Comuni da processare: %d", len(comuni))

        # Fonte 2: Google Maps
        if "maps" in fonti:
            logger.info("─ Fonte 2/3: Google Maps ─")
            try:
                maps_results = scrape_google_maps(fetcher, regione_slug, comuni)
                all_raw.extend(maps_results)
                logger.info("Google Maps: %d centri trovati", len(maps_results))
            except Exception as e:
                logger.error("Google Maps fallito: %s", e, exc_info=args.verbose)

        # Fonte 3: Google Search + siti web
        if "search" in fonti:
            logger.info("─ Fonte 3/3: Google Search + siti web ─")
            try:
                search_results = scrape_google_search(
                    fetcher,
                    regione_slug,
                    comuni,
                    max_per_comune=3,
                    visit_sites=True,
                )
                all_raw.extend(search_results)
                logger.info("Google Search: %d centri trovati", len(search_results))
            except Exception as e:
                logger.error("Google Search fallito: %s", e, exc_info=args.verbose)

        # Normalizza e deduplica
        logger.info("─ Normalizzazione e deduplica ─")
        logger.info("Totale raw: %d", len(all_raw))

        normalized = []
        for raw in all_raw:
            record = normalize(raw)
            if record:
                normalized.append(record)

        logger.info("Normalizzati: %d record validi", len(normalized))

        deduped = deduplicate(normalized)
        logger.info("Dopo deduplica: %d centri unici", len(deduped))

        # Salva JSON
        # Trova il prossimo numero seed
        existing_seeds = sorted(output_dir.glob("*.json"))
        next_num = 2  # 00001 è già le Marche seed manuale
        for seed_file in existing_seeds:
            try:
                num = int(seed_file.stem.split("_")[0])
                if num >= next_num:
                    next_num = num + 1
            except (ValueError, IndexError):
                pass

        out_path = output_dir / f"{next_num:05d}_{regione_slug}_scraped.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(deduped, f, ensure_ascii=False, indent=2)

        logger.info("✅ Salvato: %s (%d centri)", out_path, len(deduped))

        # Report
        _print_report(deduped, regione_slug)

    logger.info("🎉 Scraping completato!")


def _print_report(centri: list[dict], regione: str) -> None:
    """Stampa un report riassuntivo."""
    if not centri:
        logger.warning("Nessun centro trovato per %s", regione)
        return

    fonti = {}
    with_gps = 0
    with_phone = 0
    with_site = 0
    with_email = 0

    for c in centri:
        fonte = c.get("fonte", "unknown")
        fonti[fonte] = fonti.get(fonte, 0) + 1
        if c.get("coordinate_gps"):
            with_gps += 1
        if c.get("telefono"):
            with_phone += 1
        if c.get("sito_web"):
            with_site += 1
        if c.get("email"):
            with_email += 1

    print(f"\n📊 Report regione: {regione}")
    print(f"   Totale centri: {len(centri)}")
    print(f"   Con GPS: {with_gps} ({with_gps * 100 // len(centri)}%)")
    print(f"   Con telefono: {with_phone} ({with_phone * 100 // len(centri)}%)")
    print(f"   Con sito web: {with_site} ({with_site * 100 // len(centri)}%)")
    print(f"   Con email: {with_email} ({with_email * 100 // len(centri)}%)")
    print(f"   Per fonte: {fonti}")


if __name__ == "__main__":
    main()