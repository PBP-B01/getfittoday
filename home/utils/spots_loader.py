# home/utils/spots_loader.py
from __future__ import annotations
import json
from collections import defaultdict
from functools import lru_cache
from typing import Dict, List, Tuple
from django.contrib.staticfiles import finders

GRID_ORIGIN_LAT = -6.8
GRID_ORIGIN_LNG = 106.5
GRID_CELL_SIZE_DEG = 0.09

SPOT_FILES = [
    "home/data/Jakarta_fitness_spots_full.json",
    "home/data/Bekasi_fitness_spots_full.json",
    "home/data/Depok_fitness_spots_full.json",
    "home/data/Bogor_fitness_spots_full.json",
    "home/data/Tangerang_fitness_spots_full.json",
]

def _grid_id_for(lat: float, lng: float) -> str | None:
    if lat < GRID_ORIGIN_LAT or lng < GRID_ORIGIN_LNG:
        return None
    row = int((lat - GRID_ORIGIN_LAT) // GRID_CELL_SIZE_DEG)
    col = int((lng - GRID_ORIGIN_LNG) // GRID_CELL_SIZE_DEG)
    return f"{row}-{col}"

def _normalize(raw: dict) -> dict | None:
    loc = raw.get("location") or {}
    try:
        lat = float(loc.get("latitude"))
        lng = float(loc.get("longitude"))
    except (TypeError, ValueError):
        return None
    return {
        "place_id": raw.get("id") or f"{lat},{lng}",
        "name": (raw.get("displayName") or {}).get("text") or "Tidak bernama",
        "address": raw.get("formattedAddress") or "",
        "latitude": lat,
        "longitude": lng,
        "rating": raw.get("rating"),
        "rating_count": raw.get("userRatingCount"),
        "types": raw.get("types") or [],
        "website": raw.get("website"),
        "phone_number": raw.get("phone"),
    }

@lru_cache(maxsize=1)
def load_all_spots() -> List[dict]:
    items: List[dict] = []
    for rel in SPOT_FILES:
        path = finders.find(rel)
        if not path:
            continue
        with open(path, encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
        for raw in data:
            s = _normalize(raw)
            if s:
                items.append(s)
    dedup: Dict[str, dict] = {}
    for s in items:
        dedup[s["place_id"]] = s
    return list(dedup.values())

@lru_cache(maxsize=1)
def build_index_and_bounds() -> Tuple[Dict[str, List[dict]], dict]:
    spots = load_all_spots()
    idx: Dict[str, List[dict]] = defaultdict(list)
    north, south, east, west = -90.0, 90.0, -180.0, 180.0
    for s in spots:
        lat, lng = s["latitude"], s["longitude"]
        gid = _grid_id_for(lat, lng)
        if gid:
            idx[gid].append(s)
        north = max(north, lat); south = min(south, lat)
        east = max(east, lng);   west  = min(west,  lng)
    return idx, {"north": north, "south": south, "east": east, "west": west}