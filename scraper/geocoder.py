"""
Geocoding gratuito via Nominatim (OpenStreetMap).

API: https://nominatim.openstreetmap.org/search
Gratuita, no API key. Limite: 1 richiesta/secondo (User-Agent obbligatorio).
"""

import json
import logging
import time
from typing import Optional
from urllib.parse import quote_plus

import requests

logger = logging.getLogger("scraper.geocoder")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "IrisCentriCinofiliScraper/1.0 (iris@webemento.com)"


class Geocoder:
    """Geocoder Nominatim con rate-limit rispettoso (1 req/sec) e cache."""

    def __init__(self, cache_path: str | None = None):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._last_request = 0.0
        self._cache: dict[str, Optional[list]] = {}
        if cache_path:
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except FileNotFoundError:
                pass

    def _save_cache(self, cache_path: str) -> None:
        if cache_path:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)

    def _respect_rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < 1.1:
            time.sleep(1.1 - elapsed)
        self._last_request = time.time()

    def geocode(self, address: str, country: str = "Italy", cache_path: str | None = None) -> Optional[tuple[float, float]]:
        """Restituisce (lat, lon) per un indirizzo, o None."""
        key = f"{address}|{country}".lower().strip()
        if key in self._cache:
            cached = self._cache[key]
            return None if cached is None else tuple(cached)

        self._respect_rate_limit()

        # Build query: prefer address + country, fallback handled by caller
        query = f"{address}, {country}" if country else address
        params = {"q": query, "format": "json", "limit": 1, "addressdetails": 0}

        try:
            r = self.session.get(NOMINATIM_URL, params=params, timeout=15)
            if r.status_code == 200:
                results = r.json()
                if results:
                    lat = float(results[0]["lat"])
                    lon = float(results[0]["lon"])
                    self._cache[key] = [lat, lon]
                    logger.debug("Geocoded: %s -> %s,%s", address, lat, lon)
                    self._save_cache(cache_path)
                    return (lat, lon)
            elif r.status_code == 429:
                logger.warning("Nominatim rate-limited, waiting 2s")
                time.sleep(2)
                return self.geocode(address, country, cache_path)
        except Exception as e:
            logger.warning("Geocoding failed for '%s': %s", address, e)

        self._cache[key] = None
        self._save_cache(cache_path)
        return None


def format_wkt(lon: float, lat: float) -> str:
    """Formato WKT PostGIS: POINT(lon lat) con precisione a 6 decimali (~11cm)."""
    return f"POINT({lon:.6f} {lat:.6f})"


def geocode_record(rec: dict, geocoder: Geocoder, cache_path: str | None = None) -> bool:
    """Geocoda un singolo record. Ritorna True se ha aggiunto coordinate_gps."""
    if rec.get("coordinate_gps"):
        return False

    indirizzo = rec.get("indirizzo") or ""
    comune = rec.get("comune") or ""
    provincia = rec.get("provincia_sigla") or ""

    if not comune:
        return False

    # Prova prima con indirizzo completo, poi fallback solo con comune+provincia
    queries = []
    if indirizzo:
        queries.append(f"{indirizzo}, {comune} {provincia}")
    queries.append(f"{comune} {provincia}")
    queries.append(comune)

    for q in queries:
        result = geocoder.geocode(q, cache_path=cache_path)
        if result:
            lat, lon = result
            rec["coordinate_gps"] = format_wkt(lon, lat)
            return True

    return False
