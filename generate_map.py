"""Generate a map for the confirmed Cancale stay data."""

import argparse
import html
import json
from pathlib import Path
import time
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

import folium
from branca.element import Element


ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "vacances_data.json"
OUTPUT_FILE = ROOT_DIR / "carte_cancale.html"
GEOCODE_CACHE_FILE = ROOT_DIR / "geocode_cache.local.json"

# OpenStreetMap administrative centroid for Cancale, not the lodging address.
CANCALE_CENTER = (48.6771721, -1.8506953)
GEOCODE_QUERY_ALIASES = {
    "Micro Zoo Saint-Malo": ["Porte Saint-Vincent, Saint-Malo, France"],
    "Parc zoologique de la Bourbansais": ["La Bourbansais, Pleugueneuc, France"],
}


def load_data(data_file=DATA_FILE):
    with open(data_file, "r", encoding="utf-8-sig") as source:
        return json.load(source)


def load_geocode_cache():
    try:
        with GEOCODE_CACHE_FILE.open("r", encoding="utf-8") as source:
            return json.load(source)
    except (OSError, json.JSONDecodeError):
        return {}


def geocode_place(query, cache, last_request_at):
    cached_coordinates = cache.get(query)
    if cached_coordinates:
        return tuple(cached_coordinates), last_request_at

    if last_request_at is not None:
        wait_seconds = 1.1 - (time.monotonic() - last_request_at)
        if wait_seconds > 0:
            time.sleep(wait_seconds)

    request_url = "https://nominatim.openstreetmap.org/search?" + urlencode(
        {"q": query, "format": "jsonv2", "limit": 1}
    )
    request = Request(
        request_url,
        headers={
            "User-Agent": "CancaleFamilyMap/1.0 (public destination map)",
            "Accept-Language": "fr",
        },
    )
    request_started_at = time.monotonic()

    try:
        with urlopen(request, timeout=8) as response:
            results = json.load(response)
        if not results:
            return None, request_started_at
        coordinates = (float(results[0]["lat"]), float(results[0]["lon"]))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"Géocodage indisponible pour {query} : {error}")
        return None, request_started_at

    cache[query] = coordinates
    return coordinates, request_started_at


def generate_map(data, output_file=OUTPUT_FILE):
    map_view = folium.Map(
        location=CANCALE_CENTER,
        zoom_start=13,
        tiles="OpenStreetMap",
    )
    folium.Marker(
        location=CANCALE_CENTER,
        tooltip="Cancale (centre communal, repère approximatif)",
        popup=(
            "Cancale — repère communal approximatif. "
            "L'adresse exacte de l'hébergement n'est pas enregistrée."
        ),
    ).add_to(map_view)

    steps = data.get("etapes", [])
    links = []
    geocode_cache = load_geocode_cache()
    last_request_at = None
    marker_locations = [CANCALE_CENTER]
    unmapped_titles = []

    for step in steps:
        activity = step.get("activite_principale", {})
        title = activity.get("nom") or step.get("titre") or "Sortie retenue"
        route = step.get("trajet", {})
        maps_url = route.get("maps_url", "")
        maps_query = parse_qs(urlparse(maps_url).query).get("query", [route.get("arrivee", title)])[0]
        safe_title = html.escape(str(title))

        place_queries = list(dict.fromkeys((
            maps_query,
            *GEOCODE_QUERY_ALIASES.get(maps_query, []),
            f"{title}, France",
            route.get("arrivee", ""),
        )))
        coordinates = None
        for place_query in place_queries:
            if not place_query or "repère" in place_query.casefold():
                continue
            coordinates, last_request_at = geocode_place(
                place_query, geocode_cache, last_request_at
            )
            if coordinates:
                break

        if coordinates:
            is_access_reference = "repère" in route.get("arrivee", "").casefold()
            marker_popup = safe_title
            marker_tooltip = safe_title
            if is_access_reference:
                marker_popup += "<br>Repère d'accès; emplacement exact du lieu à confirmer."
                marker_tooltip += " (repère d'accès)"
            folium.Marker(
                location=coordinates,
                tooltip=marker_tooltip,
                popup=marker_popup,
            ).add_to(map_view)
            marker_locations.append(coordinates)
        else:
            print(f"Destination introuvable sur la carte : {title}")
            unmapped_titles.append(title)

        if maps_url.startswith(("https://www.google.com/maps/", "https://maps.google.com/")):
            safe_url = html.escape(maps_url, quote=True)
            links.append(f'<li><a href="{safe_url}" target="_blank" rel="noopener">{safe_title}</a></li>')
        else:
            links.append(f"<li>{safe_title} (lien de trajet non renseigné)</li>")

    if geocode_cache:
        GEOCODE_CACHE_FILE.write_text(
            json.dumps(geocode_cache, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if len(marker_locations) > 1:
        map_view.fit_bounds(marker_locations, padding=(30, 30))

    if not steps:
        items_html = "<p>Aucune sortie n'est encore validée.</p>"
    else:
        items_html = "<ul>" + "".join(links) + "</ul>"
    if unmapped_titles:
        unmapped_items = "".join(
            f"<li>{html.escape(str(title))}</li>" for title in unmapped_titles
        )
        items_html += (
            "<p>Sans repère cartographique :</p><ul>"
            + unmapped_items
            + "</ul>"
        )

    panel_html = f"""
    <div style="position:fixed;top:12px;left:60px;z-index:9999;background:white;
                padding:12px 16px;border:1px solid #bbb;border-radius:4px;
                max-width:340px;font:14px/1.4 sans-serif;">
      <strong>Séjour familial à Cancale</strong>
      <p>Le repère de carte situe la commune, pas l'hébergement exact.</p>
      {items_html}
    </div>
    """
    map_view.get_root().html.add_child(Element(panel_html))

    output_file = Path(output_file)
    map_view.save(str(output_file))
    return output_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_FILE, help="JSON du séjour")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Fichier HTML généré")
    args = parser.parse_args()
    output = generate_map(load_data(args.data), args.output)
    print(f"Carte générée : {output}")


if __name__ == "__main__":
    main()
