"""Extract taxonomy (metodologie, discipline, infrastrutture) from centro descriptions."""
import logging, os, re
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("taxonomy")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env.local")
client = create_client(os.getenv("NEXT_PUBLIC_SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

# Keyword -> taxonomy slug mapping (Italian keywords to match in descriptions)
METHOD_KEYWORDS = {
    "cognitivo": "cognitivo-relazionale",
    "relazionale": "cognitivo-relazionale",
    "cognitivo relazionale": "cognitivo-relazionale",
    "cognitivo-relazionale": "cognitivo-relazionale",
    "etologico": "etologico",
    "etologia": "etologico",
    "gentile": "gentile",
    "gentili": "gentile",
    "metodo gentile": "gentile",
    "tradizionale": "tradizionale",
    "misto": "misto",
}

DISCIPLINE_KEYWORDS = {
    "agility": "agility-dog",
    "agility dog": "agility-dog",
    "rally": "rally-o",
    "rally-o": "rally-o",
    "rally obedience": "rally-o",
    "obedience": "obedience",
    "disc dog": "disc-dog",
    "dog dance": "dog-dance",
    "hoopers": "hoopers",
    "socializzazione": "socializzazione",
    "classi di socializzazione": "socializzazione",
    "educazione base": "educazione-base",
    "cuccioli": "educazione-base",
    "puppy class": "educazione-base",
    "nosework": "nosework",
    "ricerca olfattiva": "nosework",
    "olfatto": "nosework",
    "mantrailing": "mantrailing",
    "propriocezione": "propriocezione",
    "mobilità": "propriocezione",
    "mobilita": "propriocezione",
    "recupero comportamentale": "recupero-comportamentale",
    "riabilitazione comportamentale": "recupero-comportamentale",
    "scent detection": "scent-detection",
    "trick training": "trick-training",
    "ipo": "ipo-igp",
    "igp": "ipo-igp",
    "difesa": "ipo-igp",
    "protezione civile": "protezione-civile",
    "salvataggio": "protezione-civile",
    "riabilitazione": "riabilitazione",
}

INFRA_KEYWORDS = {
    "campo coperto": "campo-coperto",
    "indoor": "campo-coperto",
    "campo recintato": "campo-recintato",
    "recintato": "campo-recintato",
    "campo scoperto": "campo-scoperto",
    "scoperto": "campo-scoperto",
    "piscina": "piscina",
    "piscina cinofila": "piscina",
    "area socializzazione": "area-socializzazione",
    "socializzazione": "area-socializzazione",  # in infrastructure context
    "asilo": "asilo-diurno",
    "asilo diurno": "asilo-diurno",
    "pensione": "asilo-diurno",
}

def extract_taxonomy(text, keyword_map):
    """Match keywords in text, return set of taxonomy slugs."""
    text_lower = text.lower() if text else ""
    found = set()
    for keyword, slug in keyword_map.items():
        if keyword.lower() in text_lower:
            found.add(slug)
    return found

def main():
    # Load all taxonomy tables
    def load_table(table):
        resp = client.table(table).select("id,slug,nome").execute()
        return {r["slug"]: r["id"] for r in resp.data}

    metod_map = load_table("metodologie")
    disc_map = load_table("discipline")
    infra_map = load_table("infrastrutture")

    # Get existing junctions
    def load_junctions(table, fk):
        resp = client.table(table).select(f"centro_id,{fk}").execute()
        pairs = set()
        for r in resp.data:
            pairs.add((r["centro_id"], r[fk]))
        return pairs

    met_junctions = load_junctions("centri_metodologie", "metodologia_id")
    disc_junctions = load_junctions("centri_discipline", "disciplina_id")
    infra_junctions = load_junctions("centri_infrastrutture", "infrastruttura_id")

    # Get all centers with descriptions
    resp = client.table("centri").select("id,ragione_sociale,descrizione").not_.is_("descrizione", "null").execute()
    centers = resp.data
    logger.info("Centers with descriptions: %d", len(centers))

    met_inserts, disc_inserts, infra_inserts = [], [], []
    matched = 0

    for c in centers:
        desc = c.get("descrizione") or ""
        name = c["ragione_sociale"]
        full_text = f"{name} {desc}"

        method_slugs = extract_taxonomy(full_text, METHOD_KEYWORDS)
        disc_slugs = extract_taxonomy(full_text, DISCIPLINE_KEYWORDS)
        infra_slugs = extract_taxonomy(full_text, INFRA_KEYWORDS)

        cid = c["id"]
        for slug in method_slugs:
            tid = metod_map.get(slug)
            if tid and (cid, tid) not in met_junctions:
                met_inserts.append({"centro_id": cid, "metodologia_id": tid})
                met_junctions.add((cid, tid))

        for slug in disc_slugs:
            tid = disc_map.get(slug)
            if tid and (cid, tid) not in disc_junctions:
                disc_inserts.append({"centro_id": cid, "disciplina_id": tid})
                disc_junctions.add((cid, tid))

        for slug in infra_slugs:
            tid = infra_map.get(slug)
            if tid and (cid, tid) not in infra_junctions:
                infra_inserts.append({"centro_id": cid, "infrastruttura_id": tid})
                infra_junctions.add((cid, tid))

        if method_slugs or disc_slugs or infra_slugs:
            matched += 1

    logger.info("Matched %d/%d centers", matched, len(centers))
    logger.info("Inserts: %d metodologie, %d discipline, %d infrastrutture",
                len(met_inserts), len(disc_inserts), len(infra_inserts))

    BATCH = 50
    for table, data in [
        ("centri_metodologie", met_inserts),
        ("centri_discipline", disc_inserts),
        ("centri_infrastrutture", infra_inserts),
    ]:
        for i in range(0, len(data), BATCH):
            batch = data[i:i+BATCH]
            if batch:
                try:
                    client.table(table).insert(batch).execute()
                    logger.info("%s: inserted %d", table, len(batch))
                except Exception as e:
                    logger.error("%s batch error: %s", table, e)

    logger.info("Done.")

if __name__ == "__main__":
    main()
