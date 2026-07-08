"""
Import del seed 00006_italia_scraped.json nel DB Supabase.

Usage:
    python -m scraper.import_seed

Carica:
- 133 record in `centri`
- Collegamento a `affiliazioni` (slug "enci" per tutti)

Prima di eseguire, verifica che .env.local abbia:
- NEXT_PUBLIC_SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
"""

import json
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("importer")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local")

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    sys.exit("Errore: NEXT_PUBLIC_SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY mancanti in .env.local")

SEED_FILE = ROOT / "supabase" / "seeds" / "00006_italia_scraped.json"


def main():
    client = create_client(SUPABASE_URL, SUPABASE_KEY)

    with open(SEED_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)
    logger.info("Caricati %d record dal file seed", len(records))

    # 1. Recupera le province per mappare sigla → ID
    logger.info("Recupero mappa province...")
    provinces_resp = client.table("province").select("id,sigla").execute()
    provincia_map = {p["sigla"]: p["id"] for p in provinces_resp.data}
    logger.info("Province caricate: %d", len(provincia_map))

    # 2. Recupera affiliazioni (ENCI/ASC/CSEN)
    aff_resp = client.table("affiliazioni").select("id,slug").execute()
    aff_map = {a["slug"]: a["id"] for a in aff_resp.data}
    logger.info("Affiliazioni caricate: %s", list(aff_map.keys()))

    # 3. Conta record esistenti
    existing = client.table("centri").select("id,slug", count="exact").execute()
    existing_slugs = {r["slug"] for r in existing.data} if existing.data else set()
    logger.info("Record esistenti: %d (slug unici: %d)", existing.count, len(existing_slugs))

    # 4. Prepara record per INSERT
    to_insert = []
    junction_to_insert = []

    for r in records:
        slug = r.get("slug")
        if not slug or slug in existing_slugs:
            continue

        provincia_id = provincia_map.get(r.get("provincia_sigla"))

        # Costruisci record DB
        db_rec = {
            "ragione_sociale": r["ragione_sociale"],
            "brand_name": r.get("brand_name"),
            "slug": slug,
            "indirizzo": r.get("indirizzo"),
            "comune": r.get("comune"),
            "cap": r.get("cap"),
            "provincia_id": provincia_id,
            "coordinate_gps": r.get("coordinate_gps"),
            "telefono": r.get("telefono"),
            "email": r.get("email"),
            "sito_web": r.get("sito_web"),
            "social_links": r.get("social_links", {}),
            "descrizione": r.get("descrizione"),
            "claim_status": "unclaimed",
        }

        # Pulisci None vuoti per JSONB
        if db_rec["social_links"] is None:
            db_rec["social_links"] = {}
        if db_rec.get("coordinate_gps"):
            # Verifica formato WKT valido
            wkt = db_rec["coordinate_gps"]
            if not wkt.startswith("POINT("):
                logger.warning("WKT malformato per %s: %s", slug, wkt)
                db_rec["coordinate_gps"] = None

        to_insert.append(db_rec)

    logger.info("Record da inserire: %d", len(to_insert))

    if not to_insert:
        logger.info("Niente da fare.")
        return

    # 5. INSERT in blocchi (PostgREST ha limiti per request)
    BATCH = 50
    inserted_ids: list[tuple[int, dict]] = []  # (id, original_record)

    for i in range(0, len(to_insert), BATCH):
        batch = to_insert[i:i + BATCH]
        try:
            resp = client.table("centri").insert(batch).execute()
            if resp.data:
                logger.info("Inseriti %d record (batch %d/%d)",
                            len(resp.data), i // BATCH + 1,
                            (len(to_insert) + BATCH - 1) // BATCH)
                # Mappa per junction
                for j, inserted in enumerate(resp.data):
                    inserted_ids.append((inserted["id"], to_insert[i + j]))
            else:
                logger.error("Errore inserimento batch %d: %s", i // BATCH + 1, resp)
        except Exception as e:
            logger.error("Eccezione inserimento batch %d: %s", i // BATCH + 1, e)
            raise

    # 6. Inserisci junction centri_affiliazioni per ogni affiliazione del record
    logger.info("Inserimento junction centri_affiliazioni...")
    # Recupera le affiliazioni dai record ORIGINALI via slug (sono nel file seed)
    slug_to_affs = {r["slug"]: r.get("affiliazioni") or [] for r in records if r.get("slug")}

    junction = []
    for cid, rec in inserted_ids:
        slug = rec.get("slug")
        affs = slug_to_affs.get(slug, [])
        for aff_slug in affs:
            aff_id = aff_map.get(aff_slug)
            if aff_id:
                junction.append({"centro_id": cid, "affiliazione_id": aff_id})

    for i in range(0, len(junction), BATCH):
        batch = junction[i:i + BATCH]
        try:
            client.table("centri_affiliazioni").insert(batch).execute()
            logger.info("Junction: %d record (batch %d)", len(batch), i // BATCH + 1)
        except Exception as e:
            logger.error("Errore junction batch %d: %s", i // BATCH + 1, e)

    logger.info("✅ Import completato!")
    logger.info("Centri inseriti: %d", len(inserted_ids))
    logger.info("Affiliazioni assegnate: %d", len(junction))


if __name__ == "__main__":
    main()