"""
Arricchisce centri OPES/ASC senza descrizione cercando le loro pagine
Facebook e Instagram (spesso unica presenza web per piccole ASD).

Per ogni centro senza descrizione:
1. Cerca su Google: "{nome centro} facebook" o "{nome centro} instagram"
2. Se trova la pagina, visita e estrae: bio/descrizione, categoria, link
3. Salva social_links e descrizione nel DB
"""

import asyncio
import logging
import os
import sys
import json
import re
import urllib.parse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import aiohttp
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ["NEXT_PUBLIC_SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def clean_name_for_search(name: str) -> str:
    """Pulisce il nome per la ricerca: rimuove caratteri strani, sigle ASD, ecc."""
    # Rimuovi prefissi/suffissi comuni
    name = re.sub(r'\b(A\.?S\.?D\.?|A\.?S\.?S\.?N\.?E\.?|S\.?R\.?L\.?S\.?|S\.?R\.?L\.?)\b', '', name, flags=re.IGNORECASE)
    name = re.sub(r'^[.\s\-–—]+|[.\s\-–—]+$', '', name)
    return name.strip()


async def google_search(session: aiohttp.ClientSession, query: str) -> list[dict]:
    """Cerca su Google e restituisce risultati organici."""
    url = f"https://www.google.com/search?q={urllib.parse.quote(query)}&hl=it&num=5"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "it-IT,it;q=0.9",
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            html = await resp.text()
    except Exception as e:
        log.debug(f"  Google search failed: {e}")
        return []

    # Estrai link dai risultati
    results = []
    # Pattern per estrarre URL e titolo dai risultati Google
    link_pattern = re.findall(r'<a[^>]*href="(/url\?q=([^&"]+)|(https?://[^&"]+))[^>]*>(.*?)</a>', html, re.DOTALL)
    seen = set()
    for match in link_pattern:
        url = match[1] or match[2]
        if not url or url.startswith('/') or 'google.com' in url:
            continue
        if url in seen:
            continue
        seen.add(url)

        # Estrai snippet se disponibile
        snippet_match = re.search(
            re.escape(url[:50]) + r'[^<]*<[^>]*>[^<]*<span[^>]*>(.*?)</span>',
            html, re.DOTALL
        )
        snippet = None
        if snippet_match:
            snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()

        results.append({"url": url, "snippet": snippet, "source": "google"})

    return results[:5]


async def extract_from_facebook(session: aiohttp.ClientSession, fb_url: str) -> dict | None:
    """Prova a estrarre informazioni da una pagina Facebook."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "it-IT,it;q=0.9",
    }
    try:
        async with session.get(fb_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            html = await resp.text()
    except Exception:
        return None

    result = {"social": {"facebook": fb_url}}

    # Cerca descrizione nella meta description o og:description
    desc_match = re.search(
        r'<meta[^>]+(?:property="og:description"|name="description")[^>]+content="([^"]+)"',
        html, re.IGNORECASE
    )
    if desc_match:
        result["descrizione"] = desc_match.group(1)[:500]

    # Cerca categoria
    cat_match = re.search(
        r'"category_type":"([^"]+)"|"category":"([^"]+)"',
        html
    )
    if cat_match:
        cat = cat_match.group(1) or cat_match.group(2)
        if cat and cat != "null":
            result["categoria"] = cat

    return result if len(result) > 1 else None


async def extract_from_instagram(session: aiohttp.ClientSession, ig_url: str) -> dict | None:
    """Prova a estrarre informazioni da Instagram."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "it-IT,it;q=0.9",
    }
    try:
        async with session.get(ig_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            html = await resp.text()
    except Exception:
        return None

    result = {"social": {"instagram": ig_url}}

    desc_match = re.search(
        r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"',
        html, re.IGNORECASE
    )
    if desc_match:
        desc = desc_match.group(1)
        # Instagram desc inizia tipicamente con "X followers, Y following, Z posts – "
        desc = re.sub(r'^[\d,]+\s*followers?,\s*[\d,]+\s*following,\s*[\d,]+\s*posts?\s*[–\-—]\s*', '', desc)
        if desc.strip():
            result["descrizione"] = desc.strip()[:500]

    return result if len(result) > 1 else None


async def enrich_centro(
    session: aiohttp.ClientSession,
    centro: dict,
    idx: int,
    total: int,
) -> bool:
    """Arricchisce un singolo centro cercando Facebook/Instagram."""
    display_name = centro.get("brand_name") or centro.get("ragione_sociale", "")
    comune = centro.get("comune", "")
    search_name = clean_name_for_search(display_name)

    log.info(f"[{idx}/{total}] {display_name}")

    updated = False
    social_links = centro.get("social_links") or {}
    new_social = {}

    # 1. Cerca Facebook
    fb_query = f'"{search_name}" {comune} facebook'
    fb_results = await google_search(session, fb_query)

    for r in fb_results:
        if "facebook.com" in r["url"]:
            fb_data = await extract_from_facebook(session, r["url"])
            if fb_data:
                new_social.update(fb_data.get("social", {}))
                if fb_data.get("descrizione"):
                    log.info(f"  📘 Facebook: {fb_data['descrizione'][:80]}...")
                    updated = True
                break

    # 2. Cerca Instagram (parallelo o sequenziale)
    ig_query = f'"{search_name}" {comune} instagram'
    ig_results = await google_search(session, ig_query)

    for r in ig_results:
        if "instagram.com" in r["url"]:
            ig_data = await extract_from_instagram(session, r["url"])
            if ig_data:
                new_social.update(ig_data.get("social", {}))
                if ig_data.get("descrizione"):
                    log.info(f"  📸 Instagram: {ig_data['descrizione'][:80]}...")
                    updated = True
                break

    if not updated and not new_social:
        log.info("  ❌ Nessun social trovato")
        return False

    # Aggiorna DB
    if new_social:
        social_links.update(new_social)

    update_data = {"social_links": social_links}

    # Cerca descrizione dai risultati Google come fallback
    if not centro.get("descrizione"):
        desc_query = f'"{search_name}" {comune} centro cinofilo'
        desc_results = await google_search(session, desc_query)
        for r in desc_results:
            if r.get("snippet") and len(r["snippet"]) > 50:
                update_data["descrizione"] = r["snippet"][:500]
                log.info(f"  📝 Snippet: {r['snippet'][:80]}...")
                updated = True
                break

    try:
        supabase.table("centri").update(update_data).eq("id", centro["id"]).execute()
        log.info("  ✅ Aggiornato")
        return True
    except Exception as e:
        log.error(f"  ❌ Errore DB: {e}")
        return False


async def main():
    log.info("🔍 Caricamento centri senza descrizione...")

    # Trova centri senza descrizione
    result = (
        supabase.table("centri")
        .select("id, ragione_sociale, brand_name, comune, descrizione, social_links, sito_web")
        .is_("descrizione", "null")
        .order("id")
        .execute()
    )

    if not result.data:
        log.info("✅ Tutti i centri hanno già una descrizione!")
        return

    centri = result.data
    log.info(f"📋 {len(centri)} centri senza descrizione da processare")

    connector = aiohttp.TCPConnector(limit=3, force_close=True)
    timeout = aiohttp.ClientTimeout(total=30)

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        enriched = 0
        for i, centro in enumerate(centri, 1):
            try:
                if await enrich_centro(session, centro, i, len(centri)):
                    enriched += 1
            except Exception as e:
                log.error(f"  ❌ Errore: {e}")
            await asyncio.sleep(2)  # Rate limit

    log.info(f"\n✨ Completato. {enriched} centri arricchiti su {len(centri)}.")


if __name__ == "__main__":
    asyncio.run(main())
