"""
Core engine dello scraper: fetching HTTP con anti-detection, parsing, normalizzazione.

Usage:
    python -m scraper --regione marche
"""

from __future__ import annotations

import json
import logging
import random
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("scraper")


# ══════════════════════════════════════════════════════════════════
# ANTI-DETECTION
# ══════════════════════════════════════════════════════════════════

USER_AGENTS: list[str] = [
    # Chrome on Windows 11
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

DEFAULT_HEADERS: dict[str, str] = {
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
}


def _random_user_agent() -> str:
    return random.choice(USER_AGENTS)


def _build_headers(referer: str | None = None) -> dict[str, str]:
    headers = dict(DEFAULT_HEADERS)
    headers["User-Agent"] = _random_user_agent()
    if referer:
        headers["Referer"] = referer
    return headers


class RobotsCache:
    """Cache robotparser per dominio, rispetta robots.txt."""

    def __init__(self) -> None:
        self._cache: dict[str, RobotFileParser | None] = {}

    def is_allowed(self, url: str, ua: str = "*") -> bool:
        domain = urlparse(url).netloc
        if domain not in self._cache:
            rp = RobotFileParser()
            robots_url = f"https://{domain}/robots.txt"
            try:
                rp.set_url(robots_url)
                rp.read()
                self._cache[domain] = rp
            except Exception:
                # Se robots.txt non è raggiungibile, permetti tutto
                self._cache[domain] = None
                return True
        rp = self._cache[domain]
        if rp is None:
            return True
        return rp.can_fetch(ua, url)


_robots_cache = RobotsCache()


def _parse_html(html: str) -> BeautifulSoup:
    """Parse HTML con il miglior parser disponibile (lxml → html.parser)."""
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


# ══════════════════════════════════════════════════════════════════
# FETCHER ANTI-DETECTION
# ══════════════════════════════════════════════════════════════════

class Fetcher:
    """HTTP fetcher con rotazione UA, delay casuale, retry, robots.txt."""

    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 6.0,
        timeout: int = 30,
        max_retries: int = 3,
    ) -> None:
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self._last_request: float = 0.0

    def _respect_delay(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self.min_delay:
            jitter = random.uniform(0, self.max_delay - self.min_delay)
            sleep_time = (self.min_delay - elapsed) + jitter
            logger.debug("Sleeping %.1fs (rate limit + jitter)", sleep_time)
            time.sleep(sleep_time)
        self._last_request = time.time()

    def get(self, url: str, referer: str | None = None, **kwargs) -> requests.Response | None:
        """GET con retry, delay, robots.txt e headers anti-detection."""
        if not _robots_cache.is_allowed(url):
            logger.info("Blocked by robots.txt: %s", url)
            return None

        self._respect_delay()

        headers = _build_headers(referer)
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs,
                )
                resp.raise_for_status()
                return resp
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status == 429:
                    backoff = 10 * attempt
                    logger.warning("429 rate limited on %s, backoff %ds (attempt %d/%d)", url, backoff, attempt, self.max_retries)
                    time.sleep(backoff)
                elif status >= 500:
                    logger.warning("Server error %s on %s (attempt %d/%d)", status, url, attempt, self.max_retries)
                    time.sleep(2 * attempt)
                elif status in (403, 404):
                    logger.info("HTTP %s on %s, skipping", status, url)
                    return None
                else:
                    logger.error("HTTP %s on %s: %s", status, url, e)
                    return None
            except requests.RequestException as e:
                logger.warning("Request failed on %s (attempt %d/%d): %s", url, attempt, self.max_retries, e)
                time.sleep(2 * attempt)

        logger.error("All retries exhausted for %s", url)
        return None

    def get_soup(self, url: str, referer: str | None = None) -> BeautifulSoup | None:
        """Fetch e parse HTML."""
        resp = self.get(url, referer)
        if resp is None:
            return None
        # Prova parser in ordine: lxml → html.parser (fallback integrato Python)
        return _parse_html(resp.text)

    def get_json(self, url: str, referer: str | None = None, **kwargs) -> Any | None:
        """Fetch e parse JSON."""
        headers = kwargs.pop("headers", {})
        headers.setdefault("Accept", "application/json, text/javascript, */*; q=0.01")
        kwargs["headers"] = headers
        resp = self.get(url, referer, **kwargs)
        if resp is None:
            return None
        try:
            return resp.json()
        except json.JSONDecodeError:
            logger.warning("Invalid JSON from %s", url)
            return None


# ══════════════════════════════════════════════════════════════════
# DATA MODEL: Centro
# ══════════════════════════════════════════════════════════════════

@dataclass
class CentroRaw:
    """Dato grezzo estratto da qualsiasi fonte, prima della normalizzazione."""

    # Identificativi
    ragione_sociale: str | None = None
    brand_name: str | None = None

    # Località
    indirizzo: str | None = None
    comune: str | None = None
    cap: str | None = None
    provincia: str | None = None  # sigla (PU, AN, ...)
    regione: str | None = None
    coordinate_gps: str | None = None  # WKT: "POINT(lon lat)"

    # Contatti
    telefono: str | None = None
    email: str | None = None
    sito_web: str | None = None
    social_links: dict[str, str] = field(default_factory=dict)

    # Tassonomia (nomi testuali, non ID)
    descrizione: str | None = None
    metodologie: list[str] = field(default_factory=list)
    discipline: list[str] = field(default_factory=list)
    infrastrutture: list[str] = field(default_factory=list)
    affiliazioni: list[str] = field(default_factory=list)

    # Metadata
    fonte: str | None = None  # "enci", "ficss", "google_maps", "google_search", "sito_web"
    fonte_url: str | None = None
    osm_id: str | None = None
    osm_type: str | None = None

    id_univoco: str | None = None  # hash per deduplica (nome+comune+provincia)


# ══════════════════════════════════════════════════════════════════
# UTILITY: deduplica, normalizzazione
# ══════════════════════════════════════════════════════════════════

def _build_id(raw: CentroRaw) -> str:
    """Crea un ID univoco stabile per deduplica."""
    base = f"{raw.ragione_sociale or ''}|{raw.comune or ''}|{raw.provincia or ''}"
    return base.strip("|").lower().replace(" ", "-")


def _normalize_phone(tel: str) -> str | None:
    """Pulisce numero di telefono: +39 123 456 7890 → +39 1234567890."""
    if not tel:
        return None
    cleaned = re.sub(r"[^\d+]", "", tel)
    # Forza formato italiano se inizia con 3
    if cleaned.startswith("3") and len(cleaned) >= 9:
        cleaned = "+39 " + cleaned
    return cleaned or None


def _lookup_provincia_sigla(nome_o_sigla: str) -> str | None:
    """Converte nome provincia in sigla (es. 'Pesaro-Urbino' → 'PU')."""
    PROVINCE: dict[str, str] = {
        "agrigento": "AG", "alessandria": "AL", "ancona": "AN", "aosta": "AO",
        "arezzo": "AR", "ascoli piceno": "AP", "ascoli-piceno": "AP", "asti": "AT",
        "avellino": "AV", "bari": "BA", "barletta-andria-trani": "BT", "belluno": "BL",
        "benevento": "BN", "bergamo": "BG", "biella": "BI", "bologna": "BO",
        "bolzano": "BZ", "brescia": "BS", "brindisi": "BR", "cagliari": "CA",
        "caltanissetta": "CL", "campobasso": "CB", "caserta": "CE", "catania": "CT",
        "catanzaro": "CZ", "chieti": "CH", "como": "CO", "cosenza": "CS",
        "cremona": "CR", "crotone": "KR", "cuneo": "CN", "enna": "EN",
        "fermo": "FM", "ferrara": "FE", "firenze": "FI", "foggia": "FG",
        "forli-cesena": "FC", "forlì-cesena": "FC", "frosinone": "FR", "genova": "GE",
        "gorizia": "GO", "grosseto": "GR", "imperia": "IM", "isernia": "IS",
        "l-aquila": "AQ", "laquila": "AQ", "la spezia": "SP", "latina": "LT",
        "lecce": "LE", "lecco": "LC", "livorno": "LI", "lodi": "LO",
        "lucca": "LU", "macerata": "MC", "mantova": "MN", "massa-carrara": "MS",
        "matera": "MT", "messina": "ME", "milano": "MI", "modena": "MO",
        "monza-brianza": "MB", "napoli": "NA", "novara": "NO", "nuoro": "NU",
        "oristano": "OR", "padova": "PD", "palermo": "PA", "parma": "PR",
        "pavia": "PV", "perugia": "PG", "pesaro-urbino": "PU", "pesaro": "PU",
        "pescara": "PE", "piacenza": "PC", "pisa": "PI", "pistoia": "PT",
        "pordenone": "PN", "potenza": "PZ", "prato": "PO", "ragusa": "RG",
        "ravenna": "RA", "reggio calabria": "RC", "reggio emilia": "RE",
        "reggio-calabria": "RC", "reggio-emilia": "RE", "rieti": "RI", "rimini": "RN",
        "roma": "RM", "rovigo": "RO", "salerno": "SA", "sassari": "SS",
        "savona": "SV", "siena": "SI", "siracusa": "SR", "sondrio": "SO",
        "sud sardegna": "SU", "sud-sardegna": "SU", "taranto": "TA", "teramo": "TE",
        "terni": "TR", "torino": "TO", "trapani": "TP", "trento": "TN",
        "treviso": "TV", "trieste": "TS", "udine": "UD", "varese": "VA",
        "venezia": "VE", "verbano-cusio-ossola": "VB", "vercelli": "VC", "verona": "VR",
        "vibo valentia": "VV", "vibo-valentia": "VV", "vicenza": "VI", "viterbo": "VT",
    }
    key = nome_o_sigla.strip().lower() if nome_o_sigla else ""
    # Se è già una sigla di 2 lettere
    if len(key) == 2 and key.isalpha():
        return key.upper()
    return PROVINCE.get(key)


RE_CONTATTI = re.compile(
    r"(?:tel[.:]?\s*|telefono[.:]?\s*|cell[.:]?\s*|cellulare[.:]?\s*)?([\+0]\d[\d\s\.\-\(\)/]{7,18})",
    re.IGNORECASE,
)

RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.IGNORECASE)

RE_SOCIAL = {
    "facebook": re.compile(r"(?:https?://)?(?:www\.)?facebook\.com/[A-Za-z0-9._\-]+", re.I),
    "instagram": re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/[A-Za-z0-9._\-]+", re.I),
    "tiktok": re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@[A-Za-z0-9._\-]+", re.I),
    "youtube": re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/@[A-Za-z0-9._\-]+", re.I),
}


def extract_contacts_from_text(text: str) -> dict[str, Any]:
    """Estrae telefono, email, social da testo libero."""
    result: dict[str, Any] = {}

    tel_match = RE_CONTATTI.search(text)
    if tel_match:
        result["telefono"] = _normalize_phone(tel_match.group(1))

    email_match = RE_EMAIL.search(text)
    if email_match:
        result["email"] = email_match.group(0).lower()

    social_links: dict[str, str] = {}
    for platform, pattern in RE_SOCIAL.items():
        m = pattern.search(text)
        if m:
            url = m.group(0)
            if not url.startswith("http"):
                url = "https://" + url.lstrip("/")
            social_links[platform] = url
    if social_links:
        result["social_links"] = social_links

    return result


# ══════════════════════════════════════════════════════════════════
# NORMALIZER → formato seed JSON
# ══════════════════════════════════════════════════════════════════

METODOLOGIE_MAP = {
    "cognitivo-relazionale": "cognitivo-relazionale",
    "cognitivo relazionale": "cognitivo-relazionale",
    "relazionale": "cognitivo-relazionale",
    "gentile": "gentile",
    "rinforzo positivo": "gentile",
    "positivo": "gentile",
    "tradizionale": "tradizionale",
    "utilitaristico": "tradizionale",
    "misto": "non-specificato",
}

DISCIPLINE_MAP = {
    "agility": "agility-dog",
    "agility dog": "agility-dog",
    "rally": "rally-o",
    "rally-o": "rally-o",
    "rally obedience": "rally-o",
    "hoopers": "hoopers",
    "nosework": "nosework",
    "ricerca olfattiva": "nosework",
    "olfattiva": "nosework",
    "propriocezione": "propriocezione",
    "mobilità": "propriocezione",
    "mobilita": "propriocezione",
    "socializzazione": "socializzazione",
    "recupero comportamentale": "recupero-comportamentale",
    "recupero": "recupero-comportamentale",
    "comportamentale": "recupero-comportamentale",
    "educazione base": "educazione-base",
    "cuccioli": "educazione-base",
    "educazione": "educazione-base",
    "obbedienza": "educazione-base",
}

INFRASTRUTTURE_MAP = {
    "campo coperto": "campo-coperto",
    "indoor": "campo-coperto",
    "coperto": "campo-coperto",
    "campo recintato": "campo-recintato",
    "recintato": "campo-recintato",
    "campo": "campo-recintato",
    "piscina": "piscina",
    "asilo": "asilo-diurno",
    "pensione": "asilo-diurno",
}

AFFILIAZIONI_MAP = {
    "enci": "enci",
    "opes": "opes-cinofilia",
    "opes cinofilia": "opes-cinofilia",
    "ficss": "ficss",
    "csen": "csen",
    "fisc": "fisc",
    "asc": "asc",
}


def _map_name(name: str, mapping: dict[str, str]) -> str | None:
    """Mappa un nome testuale a uno slug canonico."""
    if not name:
        return None
    key = name.strip().lower()
    # Match esatto
    if key in mapping:
        return mapping[key]
    # Match parziale
    for pattern, slug in mapping.items():
        if pattern in key or key in pattern:
            return slug
    return None


def normalize(raw: CentroRaw) -> dict[str, Any]:
    """Converte CentroRaw in dizionario compatibile col seed JSON.

    Restituisce None se mancano dati minimi (nome + comune).
    """
    if not raw.ragione_sociale or not raw.comune:
        return None

    # Build slug
    slug_base = (raw.brand_name or raw.ragione_sociale).lower()
    slug_base = re.sub(r"[^\w\s-]", "", slug_base)
    slug_base = re.sub(r"\s+", "-", slug_base)
    slug = f"{slug_base}-{raw.comune.lower().replace(' ', '-')}"

    # Map tassonomia to slugs
    metodologie_slugs = [_map_name(m, METODOLOGIE_MAP) for m in raw.metodologie]
    metodologie_slugs = [s for s in metodologie_slugs if s]

    discipline_slugs = [_map_name(d, DISCIPLINE_MAP) for d in raw.discipline]
    discipline_slugs = [s for s in discipline_slugs if s]

    infrastrutture_slugs = [_map_name(i, INFRASTRUTTURE_MAP) for i in raw.infrastrutture]
    infrastrutture_slugs = [s for s in infrastrutture_slugs if s]

    affiliazioni_slugs = [_map_name(a, AFFILIAZIONI_MAP) for a in raw.affiliazioni]
    affiliazioni_slugs = [s for s in affiliazioni_slugs if s]

    # Costruisci il record
    record: dict[str, Any] = {
        "ragione_sociale": raw.ragione_sociale,
        "brand_name": raw.brand_name or raw.ragione_sociale,
        "slug": slug,
        "indirizzo": raw.indirizzo,
        "comune": raw.comune,
        "cap": raw.cap,
        "provincia_sigla": raw.provincia,
        "coordinate_gps": raw.coordinate_gps,
        "telefono": raw.telefono,
        "email": raw.email,
        "sito_web": raw.sito_web,
        "social_links": raw.social_links,
        "descrizione": raw.descrizione,
        "metodologie": metodologie_slugs,
        "discipline": discipline_slugs,
        "infrastrutture": infrastrutture_slugs,
        "affiliazioni": affiliazioni_slugs,
        # Metadata per auditing
        "fonte": raw.fonte,
        "fonte_url": raw.fonte_url,
    }

    return record


# ══════════════════════════════════════════════════════════════════
# DEDUPLICA & MERGE
# ══════════════════════════════════════════════════════════════════

def deduplicate(results: list[dict]) -> list[dict]:
    """Deduplica per slug + merge dati complementari."""
    merged: dict[str, dict] = {}
    for record in results:
        if record is None:
            continue
        slug = record.get("slug", "")
        if slug in merged:
            # Merge: prendi il non-null quando il precedente è null
            existing = merged[slug]
            for key in record:
                if key in ("metodologie", "discipline", "infrastrutture", "affiliazioni"):
                    # Union di liste
                    existing_set = set(existing.get(key, []))
                    new_items = set(record.get(key, []))
                    existing[key] = sorted(existing_set | new_items)
                elif key == "social_links":
                    existing[key] = {**existing.get(key, {}), **record.get(key, {})}
                elif not existing.get(key) and record.get(key):
                    existing[key] = record[key]
        else:
            merged[slug] = record
    return list(merged.values())
