"""
Core engine dello scraper: HTTP fetcher anti-detection, normalizzazione, deduplica.
Robots.txt deliberatamente ignorato — i dati sono pubblici.
"""

from __future__ import annotations

import json, logging, random, re, time
from dataclasses import dataclass, field
from typing import Any

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("scraper")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:133.0) Gecko/20100101 Firefox/133.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

DEFAULT_HEADERS = {
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

def _random_ua():
    return random.choice(USER_AGENTS)

def _build_headers(referer=None):
    h = dict(DEFAULT_HEADERS)
    h["User-Agent"] = _random_ua()
    if referer:
        h["Referer"] = referer
    return h

def _parse_html(html):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")

class Fetcher:
    def __init__(self, min_delay=2.0, max_delay=6.0, timeout=30, max_retries=3):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self._last_request = 0.0

    def _delay(self):
        elapsed = time.time() - self._last_request
        if elapsed < self.min_delay:
            sleep_time = (self.min_delay - elapsed) + random.uniform(0, self.max_delay - self.min_delay)
            logger.debug("Sleeping %.1fs", sleep_time)
            time.sleep(sleep_time)
        self._last_request = time.time()

    def get(self, url, referer=None, **kwargs):
        # robots.txt ignorato — i dati sono pubblici
        self._delay()
        headers = _build_headers(referer)
        if "headers" in kwargs:
            headers.update(kwargs.pop("headers"))
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, headers=headers, timeout=self.timeout, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status == 429:
                    time.sleep(10 * attempt)
                elif status >= 500:
                    time.sleep(2 * attempt)
                elif status in (403, 404):
                    logger.info("HTTP %s on %s, skipping", status, url)
                    return None
                else:
                    logger.error("HTTP %s on %s", status, url)
                    return None
            except requests.RequestException as e:
                logger.warning("Request failed on %s (attempt %d): %s", url, attempt, e)
                time.sleep(2 * attempt)
        return None

    def get_soup(self, url, referer=None):
        resp = self.get(url, referer)
        return _parse_html(resp.text) if resp else None

    def get_json(self, url, referer=None, **kwargs):
        kwargs.setdefault("headers", {}).setdefault("Accept", "application/json")
        resp = self.get(url, referer, **kwargs)
        if resp is None:
            return None
        try:
            return resp.json()
        except Exception:
            return None

# ── Regex contatti ──
RE_TEL = re.compile(r"([\+0]\d[\d\s\.\-\(\)/]{7,18})")
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+", re.I)
RE_SOCIAL = {
    "facebook": re.compile(r"(?:https?://)?(?:www\.)?facebook\.com/[A-Za-z0-9._\-]+", re.I),
    "instagram": re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/[A-Za-z0-9._\-]+", re.I),
    "tiktok": re.compile(r"(?:https?://)?(?:www\.)?tiktok\.com/@[A-Za-z0-9._\-]+", re.I),
    "youtube": re.compile(r"(?:https?://)?(?:www\.)?youtube\.com/@[A-Za-z0-9._\-]+", re.I),
}

def _normalize_phone(tel):
    if not tel:
        return None
    c = re.sub(r"[^\d+]", "", tel)
    if c.startswith("3") and len(c) >= 9:
        c = "+39 " + c
    return c

def extract_contacts(text):
    r = {}
    tm = RE_TEL.search(text)
    if tm:
        r["telefono"] = _normalize_phone(tm.group(1))
    em = RE_EMAIL.search(text)
    if em:
        r["email"] = em.group(0).lower()
    social = {}
    for p, rx in RE_SOCIAL.items():
        m = rx.search(text)
        if m:
            url = m.group(0)
            if not url.startswith("http"):
                url = "https://" + url.lstrip("/")
            social[p] = url
    if social:
        r["social_links"] = social
    return r

# ── Tassonomia map ──
METODOLOGIE_MAP = {"cognitivo-relazionale":"cognitivo-relazionale","cognitivo relazionale":"cognitivo-relazionale","relazionale":"cognitivo-relazionale","gentile":"gentile","rinforzo positivo":"gentile","positivo":"gentile","tradizionale":"tradizionale","utilitaristico":"tradizionale","misto":"non-specificato"}
DISCIPLINE_MAP = {"agility":"agility-dog","agility dog":"agility-dog","rally":"rally-o","rally-o":"rally-o","rally obedience":"rally-o","hoopers":"hoopers","nosework":"nosework","ricerca olfattiva":"nosework","olfattiva":"nosework","propriocezione":"propriocezione","mobilita":"propriocezione","socializzazione":"socializzazione","recupero comportamentale":"recupero-comportamentale","recupero":"recupero-comportamentale","educazione base":"educazione-base","cuccioli":"educazione-base","obbedienza":"educazione-base"}
INFRASTRUTTURE_MAP = {"campo coperto":"campo-coperto","indoor":"campo-coperto","campo recintato":"campo-recintato","recintato":"campo-recintato","campo":"campo-recintato","piscina":"piscina","asilo":"asilo-diurno","pensione":"asilo-diurno"}
AFFILIAZIONI_MAP = {"enci":"enci","opes":"opes-cinofilia","opes cinofilia":"opes-cinofilia","ficss":"ficss","csen":"csen","fisc":"fisc","asc":"asc"}

def _map_name(name, mapping):
    if not name:
        return None
    key = name.strip().lower()
    if key in mapping:
        return mapping[key]
    for pat, slug in mapping.items():
        if pat in key or key in pat:
            return slug
    return None

@dataclass
class CentroRaw:
    ragione_sociale: str | None = None
    brand_name: str | None = None
    indirizzo: str | None = None
    comune: str | None = None
    cap: str | None = None
    provincia: str | None = None
    regione: str | None = None
    coordinate_gps: str | None = None
    telefono: str | None = None
    email: str | None = None
    sito_web: str | None = None
    social_links: dict = field(default_factory=dict)
    descrizione: str | None = None
    metodologie: list = field(default_factory=list)
    discipline: list = field(default_factory=list)
    infrastrutture: list = field(default_factory=list)
    affiliazioni: list = field(default_factory=list)
    fonte: str | None = None
    fonte_url: str | None = None

def normalize(raw):
    if not raw.ragione_sociale or not raw.comune:
        return None
    slug_base = re.sub(r"[^\w\s-]", "", (raw.brand_name or raw.ragione_sociale).lower())
    slug = re.sub(r"\s+", "-", slug_base) + "-" + raw.comune.lower().replace(" ", "-")
    return {
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
        "metodologie": [s for s in [_map_name(m, METODOLOGIE_MAP) for m in raw.metodologie] if s],
        "discipline": [s for s in [_map_name(d, DISCIPLINE_MAP) for d in raw.discipline] if s],
        "infrastrutture": [s for s in [_map_name(i, INFRASTRUTTURE_MAP) for i in raw.infrastrutture] if s],
        "affiliazioni": [s for s in [_map_name(a, AFFILIAZIONI_MAP) for a in raw.affiliazioni] if s],
        "fonte": raw.fonte,
        "fonte_url": raw.fonte_url,
    }

def deduplicate(results):
    merged = {}
    for rec in results:
        if rec is None:
            continue
        s = rec.get("slug", "")
        if s in merged:
            ex = merged[s]
            for k in rec:
                if k in ("metodologie","discipline","infrastrutture","affiliazioni"):
                    ex[k] = sorted(set(ex.get(k,[])) | set(rec.get(k,[])))
                elif k == "social_links":
                    ex[k] = {**ex.get(k,{}), **rec.get(k,{})}
                elif not ex.get(k) and rec.get(k):
                    ex[k] = rec[k]
        else:
            merged[s] = rec
    return list(merged.values())