"""Data sources behind small functions. Each returns plain dicts and raises on failure (the cache handles that).

- OpenAlex    : universities and countries                     https://api.openalex.org
- World Bank  : price level of each country, US = 100          https://api.worldbank.org
- open.er-api : currency exchange rates                        https://open.er-api.com
"""
import os

import requests

TIMEOUT = 20
HEADERS = {"User-Agent": "UniCounsel/1.0"}
_MAILTO = os.environ.get("OPENALEX_MAILTO", "")


def _json(url, params=None):
    p = dict(params or {})
    if _MAILTO and "openalex" in url:
        p["mailto"] = _MAILTO
    r = requests.get(url, params=p, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    return r.json()


# ---- OpenAlex -------------------------------------------------------------------------------------------------
def openalex_countries():
    data = _json("https://api.openalex.org/institutions",
                 {"filter": "type:education", "group-by": "country_code", "per-page": 200})
    out = [{"code": g["key"].rsplit("/", 1)[-1], "name": g.get("key_display_name"), "universities": g["count"]}
           for g in data.get("group_by", [])]
    return sorted([c for c in out if c["code"] and c["name"] and c["code"] != "unknown"], key=lambda c: c["name"])


def _shape(i):
    geo = i.get("geo") or {}
    return {
        "id": (i.get("id") or "").rsplit("/", 1)[-1], "name": i.get("display_name"),
        "country_code": i.get("country_code"), "country": geo.get("country"), "city": geo.get("city"),
        "region": geo.get("region"), "lat": geo.get("latitude"), "lon": geo.get("longitude"),
        "website": i.get("homepage_url"), "papers": i.get("works_count"), "citations": i.get("cited_by_count"),
        "ror": i.get("ror"),
    }


def openalex_universities(country=None, q=None, page=1, per_page=25, sort="research"):
    flt = "type:education"
    if country:
        flt += f",country_code:{country.upper()}"
    if q:
        flt += f",display_name.search:{q}"
    data = _json("https://api.openalex.org/institutions", {
        "filter": flt, "per-page": max(1, min(int(per_page), 100)), "page": max(1, int(page)),
        "select": "id,display_name,country_code,geo,homepage_url,works_count,cited_by_count,ror",
        "sort": "cited_by_count:desc" if sort == "research" else "display_name"})
    return {"total": data["meta"]["count"], "page": data["meta"]["page"], "results": [_shape(i) for i in data["results"]]}


def openalex_university(uni_id):
    return _shape(_json(f"https://api.openalex.org/institutions/{uni_id}"))


# ---- World Bank -----------------------------------------------------------------------------------------------
def _wb_indicator(code):
    d = _json(f"https://api.worldbank.org/v2/country/all/indicator/{code}", {"format": "json", "per_page": 1000, "mrnev": 1})
    return {x["countryiso3code"]: x["value"] for x in (d[1] if len(d) > 1 and d[1] else []) if x["value"] and x["countryiso3code"]}


def worldbank_price_levels():
    """{ISO2: price level, US = 100}: consumption PPP factor divided by the official exchange rate."""
    ppp, fx = _wb_indicator("PA.NUS.PRVT.PP"), _wb_indicator("PA.NUS.FCRF")
    ratio = {k: ppp[k] / fx[k] for k in ppp if k in fx}
    us = ratio.get("USA")
    if not us:
        return {}
    iso = _json("https://api.worldbank.org/v2/country", {"format": "json", "per_page": 400})[1]
    to2 = {c["id"]: c["iso2Code"] for c in iso}
    return {to2[k]: round(v / us * 100, 1) for k, v in ratio.items() if k in to2}


# ---- Exchange rates -------------------------------------------------------------------------------------------
def fx_rates():
    d = _json("https://open.er-api.com/v6/latest/USD")
    return d["rates"] if d.get("result") == "success" else {}
