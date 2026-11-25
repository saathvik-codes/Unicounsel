"""Live university, cost and currency data for the app (the one module app.py imports).

All reads go through adapters.cache: answers come from memory or the committed snapshot immediately, and fresh
data is fetched in the background, so a page never waits on an outside API. See adapters/ for the sources.
"""
from adapters import cache, sources

HOUR, DAY = 3600, 86400
EMPTY = {"total": 0, "page": 1, "results": []}


def countries():
    """[{code, name, universities}] for every country that has universities."""
    return cache.get("countries", sources.openalex_countries, DAY) or []


def totals():
    c = countries()
    return {"universities": sum(x["universities"] for x in c), "countries": len(c)}


def price_levels():
    """{ISO2: price level, US = 100}. Real World Bank data; higher means everyday costs are higher."""
    return cache.get("price_levels", sources.worldbank_price_levels, DAY) or {}


def price_level(country_code):
    return price_levels().get((country_code or "").upper())


def rates():
    return cache.get("fx", sources.fx_rates, HOUR) or {}


def convert(amount, src, dst):
    r = rates()
    s, d = r.get(src.upper()), r.get(dst.upper())
    return round(float(amount) / s * d, 2) if s and d else None


def universities(country=None, q=None, page=1, per_page=25, sort="research"):
    """{total, page, results}; each result also carries its country's price level."""
    key = f"unis|{country}|{q}|{page}|{per_page}|{sort}"
    # the default first page ships in the snapshot, so the explorer paints instantly on a cold start
    snap_key = "unis_default" if (not country and not q and int(page) == 1 and sort == "research") else None
    data = cache.get(key, lambda: sources.openalex_universities(country, q, page, per_page, sort), 1800, snap_key)
    if not data:
        return EMPTY
    levels = price_levels()
    return {**data, "results": [{**u, "price_level": levels.get((u.get("country_code") or "").upper())} for u in data["results"]]}


def university(uni_id):
    u = cache.get(f"uni|{uni_id}", lambda: sources.openalex_university(uni_id), DAY)
    return {**u, "price_level": price_level(u.get("country_code"))} if u else None


def warm():
    """Called once at startup: fill the cache in the background."""
    cache.warm([("countries", sources.openalex_countries, DAY), ("price_levels", sources.worldbank_price_levels, DAY),
                ("fx", sources.fx_rates, HOUR)])
