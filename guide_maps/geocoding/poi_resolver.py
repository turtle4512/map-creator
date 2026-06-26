"""Resolve user-provided POI names to stable, reviewable coordinates."""

from __future__ import annotations

from difflib import SequenceMatcher

from .coordinate_transform import amap_to_wgs84
from .schemas import AMapPOICandidate, ResolvedPOI


class POIResolver:
    def __init__(self, client, source: str = "amap"):
        self.client = client
        self.source = source

    def resolve_many(self, names: list[str], city: str, limit: int = 5) -> list[ResolvedPOI]:
        return [self.resolve_one(name, city=city, limit=limit) for name in names]

    def resolve_category(self, category: str, city: str, top_n: int = 8) -> list[ResolvedPOI]:
        """#1240 B-mode: expand a category keyword (咖啡店/酒馆/书店…) into the
        top-N real POIs. Unlike resolve_one (one best match per name), every AMap
        result becomes its own POI, then far-suburb outliers are trimmed so the
        bbox stays in the main urban core."""
        candidates = self.client.search_text(category, city=city)
        resolved: list[ResolvedPOI] = []
        for candidate in candidates:
            lng_wgs84, lat_wgs84 = amap_to_wgs84(candidate.lng_gcj02, candidate.lat_gcj02)
            resolved.append(
                ResolvedPOI(
                    input_name=candidate.name,
                    resolved_name=candidate.name,
                    source=self.source,
                    poi_id=candidate.poi_id,
                    address=candidate.address,
                    province=candidate.province,
                    city=candidate.city,
                    district=candidate.district,
                    type=candidate.type,
                    typecode=candidate.typecode,
                    lng_gcj02=candidate.lng_gcj02,
                    lat_gcj02=candidate.lat_gcj02,
                    lng_wgs84=lng_wgs84,
                    lat_wgs84=lat_wgs84,
                    confidence=1.0,
                    status="resolved",
                    needs_review=False,
                    candidates=[],
                )
            )
        return _keep_urban_core(resolved, top_n)

    def resolve_one(self, input_name: str, city: str, limit: int = 5) -> ResolvedPOI:
        candidates = self.client.search_text(input_name, city=city)
        ranked = sorted(
            ((self._score(input_name, city, candidate), candidate) for candidate in candidates),
            key=lambda item: item[0],
            reverse=True,
        )
        if not ranked:
            return ResolvedPOI(input_name, None, self.source, None, None, None, None, None, None, None, None, None, None, 0.0, "not_found", True, [])

        confidence, best = ranked[0]
        lng_wgs84, lat_wgs84 = amap_to_wgs84(best.lng_gcj02, best.lat_gcj02)
        ambiguous = len(ranked) > 1 and ranked[0][0] - ranked[1][0] < 0.08
        needs_review = confidence < 0.78 or ambiguous
        status = "resolved_review" if needs_review else "resolved"
        return ResolvedPOI(
            input_name=input_name,
            resolved_name=best.name,
            source=self.source,
            poi_id=best.poi_id,
            address=best.address,
            province=best.province,
            city=best.city,
            district=best.district,
            type=best.type,
            typecode=best.typecode,
            lng_gcj02=best.lng_gcj02,
            lat_gcj02=best.lat_gcj02,
            lng_wgs84=lng_wgs84,
            lat_wgs84=lat_wgs84,
            confidence=round(confidence, 3),
            status=status,
            needs_review=needs_review,
            candidates=[self._candidate_summary(candidate, score) for score, candidate in ranked[:limit]],
        )

    def _score(self, input_name: str, city: str, candidate: AMapPOICandidate) -> float:
        query = _normalize(input_name)
        name = _normalize(candidate.name)
        address = _normalize(candidate.address)
        candidate_city = _normalize(candidate.city)
        expected_city = _normalize(city)
        name_score = SequenceMatcher(None, query, name).ratio()
        contains_score = 0.18 if query in name or name in query else 0.0
        city_score = 0.35 if expected_city in candidate_city or expected_city in address else -0.60
        type_score = 0.08 if any(word in _normalize(candidate.type) for word in ("酒吧", "餐饮", "咖啡", "茶", "娱乐", "风景", "景点")) else 0.0
        address_score = 0.04 if address else 0.0
        return max(0.0, min(1.0, name_score + contains_score + city_score + type_score + address_score))

    def _candidate_summary(self, candidate: AMapPOICandidate, score: float) -> dict:
        return {
            "score": round(score, 3),
            "poi_id": candidate.poi_id,
            "name": candidate.name,
            "address": candidate.address,
            "city": candidate.city,
            "district": candidate.district,
            "type": candidate.type,
            "lng_gcj02": candidate.lng_gcj02,
            "lat_gcj02": candidate.lat_gcj02,
        }


def _keep_urban_core(pois: list[ResolvedPOI], top_n: int) -> list[ResolvedPOI]:
    """#1240: drop far-suburb outliers and cap at top_n. Ranks by distance to the
    median center (robust to a lone far branch), so e.g. a single 都江堰 shop won't
    stretch the map across the whole prefecture."""
    valid = [p for p in pois if p.lat_wgs84 is not None and p.lng_wgs84 is not None]
    if len(valid) <= top_n:
        return valid
    lats = sorted(p.lat_wgs84 for p in valid)
    lngs = sorted(p.lng_wgs84 for p in valid)
    center_lat = lats[len(valid) // 2]
    center_lng = lngs[len(valid) // 2]
    valid.sort(key=lambda p: (p.lat_wgs84 - center_lat) ** 2 + (p.lng_wgs84 - center_lng) ** 2)
    return valid[:top_n]


def _normalize(value: str) -> str:
    return "".join(str(value).lower().split())
