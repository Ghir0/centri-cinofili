#!/usr/bin/env python3
"""
Arricchisce i centri cinofili cercando le loro pagine Facebook e Instagram
(spesso l'unica presenza web per piccole ASD cinofile).

Usa la libreria googlesearch-python come motore primario (bypassa il
blocco JS di Google). Fallback su Startpage in caso di errori.

Per ogni centro senza descrizione (o tutti, con --all):
1. Cerca su Google: "{nome centro} {comune} facebook" / "... instagram"
2. Se trova la pagina social, la visita ed estrae: bio/descrizione, categoria
3. Aggiorna social_links e descrizione su Supabase
4. Fallback: snippet da ricerca generica se FB/IG non trovati

Usage:
  uv run python scraper/enrich_social_v2.py                    # solo centri senza descrizione
  uv run python scraper/enrich_social_v2.py --all              # tutti i centri
  uv run python scraper/enrich_social_v2.py --limit 10 --dry-run
  uv run python scraper/enrich_social_v2.py --only-facebook
  uv run python scraper/enrich_social_v2.py --only-instagram
"""

from __future__ import annotations

import logging
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from supabase import create_client

# ── Setup ───────────────────────────────────────────────────
PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "scraper"))

from core import USER_AGENTS, _random_ua, _parse_html

try:
    from googlesearch import search as google_search_lib
    HAS_GOOGLE_SEARCH = True
except ImportError:
    HAS_GOOGLE_SEARCH = False

load_dotenv(PROJECT_DIR / ".env.local")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("enrich_social")

SUPABASE_URL = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Constants ───────────────────────────────────────────────
TIMEOUT = 20
STARTPAGE_SEARCH = "https://www.startpage.com/sp/search"

# Headers anti-detection per pagine social
SOCIAL_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Cache-Control": "max-age=0",
    "Sec-Ch-Ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
}


def _build_search_headers() -> dict:
    """Costruisce headers per Startpage."""
    return {
        **SOCIAL_HEADERS,
        "User-Agent": _random_ua(),
    }


def clean_name(name: str) -> str:
    """Pulisce il nome per la ricerca social: rimuove prefissi legali, suffissi, e mantiene solo il brand."""
    # ── Frasi legali/societarie complete da rimuovere ovunque ──
    legali_patterns = [
        r"\bASSOCIAZIONE\s+SPORTIVA\s+DILETTANTISTICA\s*(?:CINOFILA)?\b",
        r"\bASSOCIAZIONE\s+CULTURALE\b",
        r"\bASSOCIAZIONE\s+DI\s+(?:PROMOZIONE|VOLONTARIATO)\s+SOCIALE\b",
        r"\bCENTRO\s+ADDESTRAMENTO\s+CINOFILO\b",
        r"\bCENTRO\s+CINOTECNICO\b",
        r"\bAZIENDA\s+AGRICOLA\b",
        r"\bSOCIET[AÀ]\s+(?:COOPERATIVA|SPORTIVA|AGRICOLA)\b",
        r"\bASSOCIAZIONE\s+SPORTIVA\s+DILETTANTISTICA\b",  # ridondante ma sicuro
    ]
    for pat in legali_patterns:
        name = re.sub(pat, "", name, flags=re.IGNORECASE)

    # ── "E" leftover da rimozione concatenata di prefissi (es. "AZIENDA AGRICOLA E CENTRO CINOTECNICO" → "E ...")
    name = re.sub(r"^\s*E\s+", "", name, flags=re.IGNORECASE)

    # ── "CENTRO CINOFILO" — rimuovi solo se il nome risultante ha almeno 3 parole ──
    # (per evitare di ridurre "CENTRO CINOFILO CASALOTTI" a solo "CASALOTTI")
    m = re.match(r"\s*CENTRO\s+CINOFILO\s+(.+)", name, re.IGNORECASE)
    if m and len(m.group(1).split()) >= 2:
        name = m.group(1)  # "IL REGNO DEL CANE" — OK, togli CENTRO CINOFILO
    # Altrimenti lascia "CENTRO CINOFILO X" intatto (es. "CENTRO CINOFILO CASALOTTI")

    # ── Sigle legali (con o senza punti) ──
    sigle = (
        r"\b(?:A\.?S\.?D\.?|A\.?S\.?S\.?N\.?E\.?|"
        r"S\.?S\.?D\.?(?:\s*R\.?L\.?)?|"
        r"S\.?R\.?L\.?(?:\s*S\.?)?|"
        r"S\.?N\.?C\.?|"
        r"A\.?P\.?S\.?|"
        r"E\.?T\.?S\.?|"
        r"O\.?D\.?V\.?|"
        r"O\.?N\.?L\.?U\.?S\.?"
        r")\b"
    )
    name = re.sub(sigle, "", name, flags=re.IGNORECASE)

    # ── ASSOCIAZIONE standalone (solo se non è l'unica parola rimasta) ──
    name = re.sub(r"\bASSOCIAZIONE\b", "", name, flags=re.IGNORECASE)

    # ── Suffissi geografici tipo "- PIEMONTE", "- VENETO" ──
    regioni = (
        r"PIEMONTE|VENETO|LOMBARDIA|LAZIO|TOSCANA|EMILIA\s*ROMAGNA|EMILIA|ROMAGNA|"
        r"SICILIA|PUGLIA|CAMPANIA|CALABRIA|SARDEGNA|MARCHE|ABRUZZO|"
        r"FRIULI\s*VENEZIA\s*GIULIA|FRIULI|TRENTINO\s*ALTO\s*ADIGE|TRENTINO|ALTO\s*ADIGE|"
        r"UMBRIA|BASILICATA|MOLISE|LIGURIA|VALLE\s*D['']AOSTA"
    )
    name = re.sub(rf"\s*[-\u2013\u2014]\s*(?:{regioni})\s*$", "", name, flags=re.IGNORECASE)

    # ── "DI NOME COGNOME" / "DI COGNOME" finale ──
    name = re.sub(r"\s+DI\s+[A-Z][A-Z\s]+$", "", name, flags=re.IGNORECASE)

    # ── "APS ETS" "APS" "ETS" ──
    name = re.sub(r"\b(?:APS|ETS)\b", "", name, flags=re.IGNORECASE)

    # ── "SENZA SCOPO DI LUCRO", "SENZA SCOPO", "ONLUS" ──
    name = re.sub(r"\bSENZA\s+SCOPO(?:\s+DI\s+LUCRO)?\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\bONLUS\b", "", name, flags=re.IGNORECASE)
    name = re.sub(r"\bSPORTIVA\s+DILETTANTISTICA\b", "", name, flags=re.IGNORECASE)

    # ── Pulisci apici, virgolette, punteggiatura dai bordi ──
    name = re.sub(
        r"^['""'\u00ab\u00bb\u201a\u2018\u201e\u201c*,.\s\-\u2013\u2014]+|"
        r"['""'\u00ab\u00bb\u201a\u2018\u201e\u201c*,.\s\-\u2013\u2014]+$",
        "", name,
    )

    # ── Rimuovi apici sparsi nel corpo ──
    name = re.sub(r"\s['""'\u2018\u201c]\s", " ", name)

    # ── Normalizza spazi multipli e HTML entities ──
    name = re.sub(r"\s+", " ", name)
    name = name.replace("&amp;", "&").replace("&#39;", "'")

    return name.strip()


def search_social(query: str, num: int = 10) -> list[dict]:
    """Cerca su Google (via googlesearch-python) o Startpage (fallback)."""
    results: list[dict] = []

    # ── Primario: googlesearch-python ──
    if HAS_GOOGLE_SEARCH:
        try:
            raw_urls = list(
                google_search_lib(query, num_results=num, lang='it',
                                 sleep_interval=1)
            )
            for url in raw_urls:
                if url not in {r['url'] for r in results}:
                    results.append({"url": url, "snippet": None, "source": "google"})
            if results:
                log.debug(f"  google_search: {len(results)} risultati")
                return results[:num]
        except Exception as e:
            log.debug(f"  google_search fallita: {e}, provo Startpage")

    # ── Fallback: Startpage ──
    url = f"{STARTPAGE_SEARCH}?query={urllib.parse.quote(query)}&lang=it&num={num}"
    headers = _build_search_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=False)
        # Startpage CAPTCHA redirects to localhost
        if resp.status_code in (301, 302, 307, 308):
            loc = resp.headers.get('Location', '')
            if 'localhost' in loc or 'captcha' in loc.lower():
                log.debug(f"  Startpage: CAPTCHA redirect → {loc[:60]}")
                return results
            # Follow non-captcha redirects
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 403 or 'captcha' in resp.text.lower():
            log.debug("  Startpage: CAPTCHA o blocco")
            return results
        resp.raise_for_status()
    except Exception as e:
        log.debug(f"  Startpage fallita: {e}")
        return results

    soup = _parse_html(resp.text)
    seen = {r['url'] for r in results}
    for result_div in soup.select(".result"):
        link_elem = result_div.select_one("a[href]")
        if not link_elem:
            continue
        href = link_elem.get("href", "")
        if not href.startswith("http"):
            continue
        if "startpage.com" in href or "startmail.com" in href:
            continue
        if href in seen:
            continue
        seen.add(href)
        snippet_elem = result_div.select_one(".description")
        snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
        results.append({"url": href, "snippet": snippet, "source": "startpage"})

    return results[:num]


def scrape_facebook(fb_url: str) -> dict | None:
    """Visita una pagina Facebook e estrae og:description e categoria."""
    headers = {
        **_build_search_headers(),
        "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    }

    try:
        resp = requests.get(fb_url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        if resp.status_code == 403:
            log.debug(f"    FB 403 — probabile blocco, provo con mobile UA")
            # Riprova con mobile UA
            headers["User-Agent"] = (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
            )
            resp = requests.get(fb_url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        log.debug(f"    FB visit failed: {e}")
        return None

    result: dict = {"social": {"facebook": fb_url}}

    # og:description (fonte principale di descrizione)
    desc_match = re.search(
        r'<meta[^>]+(?:property="og:description"|name="description")[^>]+content="([^"]+)"',
        html,
        re.IGNORECASE,
    )
    if desc_match:
        desc = desc_match.group(1)
        if desc and len(desc) > 20 and not desc.startswith("Facebook"):
            result["descrizione"] = desc[:500]

    # og:title (nome pagina)
    title_match = re.search(
        r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
        html,
        re.IGNORECASE,
    )
    if title_match and "Facebook" not in title_match.group(1):
        result["page_name"] = title_match.group(1)[:200]

    # Categoria (da JSON-LD o inline JS)
    cat_match = re.search(r'"category_type":"([^"]+)"|"category":"([^"]+)"', html)
    if cat_match:
        cat = cat_match.group(1) or cat_match.group(2)
        if cat and cat != "null":
            result["categoria"] = cat

    # Link Instagram dalla pagina FB (spesso linkato nella bio/sezione about)
    ig_in_fb = re.search(r'instagram\.com/([\w.\-]+)', html, re.IGNORECASE)
    if ig_in_fb:
        ig_handle = ig_in_fb.group(1)
        if ig_handle not in ("p", "reel", "stories"):
            result["social"]["instagram"] = f"https://instagram.com/{ig_handle}"

    return result if result.get("descrizione") or result.get("page_name") else None


def scrape_instagram(ig_url: str) -> dict | None:
    """Visita un profilo Instagram e estrae bio/descrizione."""
    headers = _build_search_headers()

    try:
        resp = requests.get(ig_url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        log.debug(f"    IG visit failed: {e}")
        return None

    result: dict = {"social": {"instagram": ig_url}}

    # og:description di Instagram: "X followers, Y following, Z posts – Bio text"
    desc_match = re.search(
        r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"',
        html,
        re.IGNORECASE,
    )
    if desc_match:
        desc = desc_match.group(1)
        # Rimuovi il prefisso metriche "X followers, Y following, Z posts – "
        desc = re.sub(
            r"^[\d,]+\s*followers?,\s*[\d,]+\s*following,\s*[\d,]+\s*posts?\s*[–\-—]\s*",
            "",
            desc,
        )
        desc = desc.strip()
        if desc and "This Account is Private" not in desc and len(desc) > 10:
            result["descrizione"] = desc[:500]

    # og:title
    title_match = re.search(
        r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
        html,
        re.IGNORECASE,
    )
    if title_match:
        title = title_match.group(1)
        if "instagram" not in title.lower() and "login" not in title.lower():
            result["page_name"] = title[:200]

    return result if result.get("descrizione") or result.get("page_name") else None


def enrich_centro(
    centro: dict,
    idx: int,
    total: int,
    *,
    search_facebook: bool = True,
    search_instagram: bool = True,
    dry_run: bool = False,
) -> bool:
    """Arricchisce un singolo centro cercando Facebook e/o Instagram."""
    display_name = centro.get("brand_name") or centro.get("ragione_sociale", "")
    comune = centro.get("comune", "")
    current_desc = centro.get("descrizione")
    current_social = centro.get("social_links") or {}
    search_name = clean_name(display_name)

    # Se il nome pulito è troppo corto, usa l'originale
    if len(search_name) < 4:
        search_name = display_name.strip()

    log.info(f"[{idx}/{total}] {display_name[:60]} ({comune})")

    new_social: dict = {}
    descrizione: str | None = None

    # ── 1. Cerca Facebook ──
    if search_facebook and "facebook" not in current_social:
        fb_query = f'"{search_name}" {comune} facebook'
        fb_results = search_social(fb_query)
        time.sleep(1)

        for r in fb_results:
            if "facebook.com" in r["url"] and "/events/" not in r["url"]:
                log.debug(f"    📘 {r['url'][:80]}")
                fb_data = scrape_facebook(r["url"])
                time.sleep(1.5)
                if fb_data:
                    new_social.update(fb_data.get("social", {}))
                    if fb_data.get("descrizione"):
                        log.info(f"  📘 FB: {fb_data['descrizione'][:100]}...")
                        descrizione = fb_data["descrizione"]
                    if fb_data.get("categoria"):
                        log.info(f"  📘 Cat: {fb_data['categoria']}")
                break

    # ── 2. Cerca Instagram ──
    if search_instagram and "instagram" not in current_social and "instagram" not in new_social:
        ig_query = f'"{search_name}" {comune} instagram'
        ig_results = search_social(ig_query)
        time.sleep(1)

        for r in ig_results:
            if "instagram.com" in r["url"] and "/p/" not in r["url"] and "/reel/" not in r["url"]:
                log.debug(f"    📸 {r['url'][:80]}")
                ig_data = scrape_instagram(r["url"])
                time.sleep(1.5)
                if ig_data:
                    new_social.update(ig_data.get("social", {}))
                    if ig_data.get("descrizione") and not descrizione:
                        log.info(f"  📸 IG: {ig_data['descrizione'][:100]}...")
                        descrizione = ig_data["descrizione"]
                break

    # ── 3. Fallback: snippet da ricerca generica ──
    if not descrizione and not current_desc:
        time.sleep(1)
        desc_query = f'"{search_name}" {comune} centro cinofilo'
        desc_results = search_social(desc_query, num=3)
        for r in desc_results:
            if r.get("snippet") and len(r["snippet"]) > 50:
                descrizione = r["snippet"][:500]
                log.info(f"  🔍 Snippet: {r['snippet'][:100]}...")
                break

    # ── 4. Se ancora niente, prova una ricerca senza comune ──
    if not descrizione and not new_social and not current_desc:
        time.sleep(1)
        last_query = f'"{search_name}" centro cinofilo'
        last_results = search_social(last_query, num=5)
        for r in last_results:
            if "facebook.com" in r["url"] and "facebook" not in new_social:
                fb_data = scrape_facebook(r["url"])
                time.sleep(1.5)
                if fb_data:
                    new_social.update(fb_data.get("social", {}))
                    if fb_data.get("descrizione"):
                        descrizione = fb_data["descrizione"]
                    break
            elif "instagram.com" in r["url"] and "instagram" not in new_social:
                ig_data = scrape_instagram(r["url"])
                time.sleep(1.5)
                if ig_data:
                    new_social.update(ig_data.get("social", {}))
                    if ig_data.get("descrizione") and not descrizione:
                        descrizione = ig_data["descrizione"]
                    break

    # ── Determina se aggiornare ──
    has_social = bool(new_social)
    has_desc = bool(descrizione)

    if not has_social and not has_desc:
        log.info("  ❌ Nessun social né descrizione trovati")
        return False

    # ── Prepara update ──
    update_data: dict = {}

    if has_social:
        merged_social = {**current_social, **new_social}
        update_data["social_links"] = merged_social

    if has_desc and not current_desc:
        update_data["descrizione"] = descrizione

    if not update_data:
        log.info("  ⏭️ Nessun nuovo dato da aggiornare")
        return False

    # ── Aggiorna DB ──
    if dry_run:
        log.info(f"  🧪 [DRY RUN] Aggiornerei: {list(update_data.keys())}")
        return True

    try:
        supabase.table("centri").update(update_data).eq("id", centro["id"]).execute()
        if has_social:
            log.info(f"  ✅ Social: {list(new_social.keys())}")
        if has_desc:
            log.info(f"  ✅ Desc: {descrizione[:80]}...")
        return True
    except Exception as e:
        log.error(f"  ❌ Errore DB: {e}")
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Arricchisce centri cinofili con dati da Facebook e Instagram (via Startpage)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Processa TUTTI i centri, non solo quelli senza descrizione"
    )
    parser.add_argument("--limit", "-n", type=int, help="Limita a N centri")
    parser.add_argument("--dry-run", action="store_true", help="Non scrivere nel DB")
    parser.add_argument("--only-facebook", action="store_true", help="Cerca solo Facebook")
    parser.add_argument("--only-instagram", action="store_true", help="Cerca solo Instagram")
    parser.add_argument("--delay", type=float, default=8.0, help="Delay tra centri in secondi (default: 8)")
    parser.add_argument("--batch-size", type=int, default=10, help="Centri per batch prima della pausa (default: 10)")
    parser.add_argument("--batch-pause", type=int, default=900, help="Secondi di pausa tra batch (default: 900 = 15 min)")
    parser.add_argument("--verbose", "-v", action="store_true", help="DEBUG logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    search_fb = not args.only_instagram
    search_ig = not args.only_facebook

    # ── Query centri ──
    log.info("🔍 Caricamento centri da Supabase...")

    query = supabase.table("centri").select(
        "id, ragione_sociale, brand_name, comune, descrizione, social_links, sito_web"
    )

    if not args.all:
        query = query.is_("descrizione", "null")

    query = query.order("id")

    if args.limit:
        query = query.limit(args.limit)

    resp = query.execute()
    centri = resp.data

    if not centri:
        log.info("✅ Nessun centro da processare!")
        return

    target_label = "TUTTI" if args.all else "senza descrizione"
    log.info(f"📋 {len(centri)} centri ({target_label}) da arricchire")
    log.info(
        f"   Fonti: {'Facebook' if search_fb else ''}"
        f"{' + ' if search_fb and search_ig else ''}"
        f"{'Instagram' if search_ig else ''}"
    )
    log.info(f"   Batch: {args.batch_size} centri, pausa: {args.batch_pause}s ({args.batch_pause // 60} min)")
    if args.dry_run:
        log.info("   🧪 DRY RUN — nessun dato verrà scritto")
    log.info("")

    enriched = 0
    batch_count = 0
    for i, centro in enumerate(centri, 1):
        try:
            if enrich_centro(
                centro,
                i,
                len(centri),
                search_facebook=search_fb,
                search_instagram=search_ig,
                dry_run=args.dry_run,
            ):
                enriched += 1
        except Exception as e:
            log.error(f"  ❌ Errore inatteso: {e}")

        # Rate limiting tra centri
        if i < len(centri):
            time.sleep(args.delay)

        # Batch pause: pausa lunga ogni batch_size centri (per evitare CAPTCHA)
        if i % args.batch_size == 0 and i < len(centri):
            batch_count += 1
            eta_next = (len(centri) - i) * (args.delay + 12) / 60  # minuti stimati rimanenti
            log.info(f"")
            log.info(f"⏸️  Batch {batch_count} completato. {enriched} arricchiti su {i} processati.")
            log.info(f"   ⏳ Pausa di {args.batch_pause}s ({args.batch_pause // 60} min) per evitare CAPTCHA...")
            log.info(f"   ⏱️  Ancora ~{eta_next:.0f} min stimati")
            for sec in range(args.batch_pause, 0, -30):
                time.sleep(30)
                if sec % 120 == 0:
                    log.debug(f"   ...ancora {sec}s")

    # ── Riepilogo ──
    log.info("")
    log.info(f"✨ Completato. {enriched}/{len(centri)} centri arricchiti.")
    if args.dry_run:
        log.info("   (dry run — nessun dato modificato)")


if __name__ == "__main__":
    main()
