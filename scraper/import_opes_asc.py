"""
Import delle entry OPES/ASC arricchite nel DB Supabase.

Usage:
    python -m scraper.import_opes_asc

Legge il file 00007_opes_asc_enriched.json (output di enrich_opes_asc.py)
e inserisce nuovi centri + junction affiliazioni nel DB.
"""

import json, logging, os, re, sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("import_opes_asc")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    sys.exit("Errore: variabili d'ambiente mancanti in .env.local")

SEED_FILE = ROOT / "supabase" / "seeds" / "00007_opes_asc_enriched.json"


def normalize(n):
    return re.sub(r'[^a-z0-9]', '', (n or '').lower())


def token_overlap(a, b):
    """Jaccard sui token di almeno 3 lettere."""
    ta = set(re.findall(r'[a-z]{3,}', normalize(a)))
    tb = set(re.findall(r'[a-z]{3,}', normalize(b)))
    if not ta or not tb:
        return 0
    return len(ta & tb) / len(ta | tb)


def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Carica dati
    if not SEED_FILE.exists():
        sys.exit(f"File non trovato: {SEED_FILE}. Esegui prima enrich_opes_asc.py")

    entries = json.loads(SEED_FILE.read_text(encoding="utf-8"))
    logger.info("Caricate %d entry arricchite", len(entries))

    # 2. Mappa province (sigla -> id) e comuni -> provincia_id
    logger.info("Recupero mappa province...")
    province_resp = client.table("province").select("id,nome,sigla").execute()
    province_map = {p["sigla"]: p["id"] for p in province_resp.data}  # sigla -> id
    province_by_name = {p["nome"].lower(): p["id"] for p in province_resp.data}  # nome -> id
    logger.info("Province: %d", len(province_map))

    # 3. Mappa comuni -> provincia (dal DB centri esistenti)
    logger.info("Recupero comuni esistenti...")
    centri_resp = client.table("centri").select("id,slug,comune,provincia_id").execute()
    existing_slugs = set()
    comune_prov_map = {}  # comune -> provincia_id più comune
    for c in centri_resp.data:
        existing_slugs.add(c["slug"])
        cm = (c.get("comune") or "").lower()
        if cm and c.get("provincia_id"):
            # Keep first province found per comune (or most common if multiple)
            if cm not in comune_prov_map:
                comune_prov_map[cm] = c["provincia_id"]

    logger.info("Comuni unici esistenti: %d", len(comune_prov_map))
    logger.info("Slug esistenti: %d", len(existing_slugs))

    # 4. Affiliazioni
    aff_resp = client.table("affiliazioni").select("id,slug").execute()
    aff_map = {a["slug"]: a["id"] for a in aff_resp.data}
    logger.info("Affiliazioni: %s", list(aff_map.keys()))
    opes_id = aff_map.get("opes")
    asc_id = aff_map.get("asc")

    # 5. Per ogni entry, risolvi provincia e prepara insert
    to_insert = []
    junctions = []
    skipped_dupes = 0
    skipped_no_comune = 0

    for e in entries:
        comune = (e.get("comune") or "").strip()
        if not comune:
            skipped_no_comune += 1
            continue

        # Slug univoco
        slug = e.get("slug") or ""
        if slug in existing_slugs:
            # Cerca di generare slug alternativo
            base = re.sub(r'[^a-z0-9\-]', '', slug)[:80]
            for suffix in range(2, 100):
                alt = f"{base}-{suffix}"
                if alt not in existing_slugs:
                    slug = alt
                    break
            else:
                skipped_dupes += 1
                continue

        # Determina provincia_id
        provincia_id = None
        cm_lower = comune.lower()

        # Prima prova: comune_prov_map
        if cm_lower in comune_prov_map:
            provincia_id = comune_prov_map[cm_lower]
        else:
            # Seconda prova: cerca comune nel DB province (comuni italiani)
            # Tramite query: trova provincia da coordinate GPS
            # Fallback: lascia NULL
            pass

        # Coordinate GPS
        gps = e.get("coordinate_gps")
        if gps and gps.get("lat") and gps.get("lon"):
            coordinate_gps = {"lat": gps["lat"], "lon": gps["lon"]}
        else:
            coordinate_gps = None

        db_rec = {
            "ragione_sociale": e["nome"],
            "brand_name": None,
            "slug": slug,
            "indirizzo": e.get("indirizzo"),
            "comune": comune,
            "cap": e.get("cap"),
            "provincia_id": provincia_id,
            "coordinate_gps": coordinate_gps,
            "telefono": e.get("telefono"),
            "email": e.get("email"),
            "sito_web": e.get("sito_web"),
            "social_links": e.get("social_links") or {},
            "descrizione": e.get("descrizione"),
            "claim_status": "unclaimed",
        }

        to_insert.append(db_rec)
        existing_slugs.add(slug)

        # Affiliazione junction
        source = e.get("source", "")
        if source == "OPES":
            junctions.append((slug, opes_id))
        elif source == "ASC":
            junctions.append((slug, asc_id))

    logger.info("\nRiepilogo:")
    logger.info("  Da inserire: %d", len(to_insert))
    logger.info("  Skp duplicati slug: %d", skipped_dupes)
    logger.info("  Skippati (no comune): %d", skipped_no_comune)

    if not to_insert:
        logger.info("Niente da inserire.")
        return

    # 6. INSERT in blocchi
    BATCH = 50
    slug_to_id = {}

    for i in range(0, len(to_insert), BATCH):
        batch = to_insert[i:i + BATCH]
        try:
            resp = client.table("centri").insert(batch).execute()
            if resp.data:
                logger.info("Inseriti %d record (batch %d/%d)",
                            len(resp.data), i // BATCH + 1,
                            (len(to_insert) + BATCH - 1) // BATCH)
                for rec in resp.data:
                    slug_to_id[rec["slug"]] = rec["id"]
            else:
                logger.error("Errore batch %d", i // BATCH + 1)
        except Exception as ex:
            logger.error("Eccezione batch %d: %s", i // BATCH + 1, ex)

    # 7. Inserisci junction affiliazioni
    logger.info("\nInserimento junction...")
    junction_rows = []
    for slug, aff_id in junctions:
        cid = slug_to_id.get(slug)
        if cid:
            junction_rows.append({"centro_id": cid, "affiliazione_id": aff_id})

    if junction_rows:
        for i in range(0, len(junction_rows), BATCH):
            batch = junction_rows[i:i + BATCH]
            try:
                client.table("centri_affiliazioni").insert(batch).execute()
                logger.info("Junction: %d record (batch %d)", len(batch), i // BATCH + 1)
            except Exception as ex:
                logger.error("Errore junction batch %d: %s", i // BATCH + 1, ex)

    logger.info("\n✓ Completato. %d nuovi centri importati.", len(slug_to_id))
    logger.info("✓ %d junction affiliazioni.", len(junction_rows))


if __name__ == "__main__":
    main()
