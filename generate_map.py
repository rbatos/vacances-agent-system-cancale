"""Generate a map for the current Cancale stay data."""

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
    "Village Route du Rhum Port Saint-Malo": ["Port de Saint-Malo, France"],
    "Pointe du Meinga": ["Pointe du Meinga, Saint-Coulomb, France"],
    "Guernsey": ["Guernsey, Channel Islands"],
    "Jersey": ["Jersey, Channel Islands"],
    "Chausey": ["Îles Chausey, France"],
}
DIRECT_COORDINATES = {
    "Village Route du Rhum Port Saint-Malo": (48.6489, -2.0248),
    "Pointe du Meinga": (48.6995, -1.9690),
    "Guernsey": (49.4558, -2.5354),
    "Jersey": (49.1853, -2.1158),
    "Chausey": (48.8730, -1.8230),
}
DIRECT_COORDINATE_NOTES = {
    "Village Route du Rhum Port Saint-Malo": "Repère approximatif du port; emplacement exact du village et accès événementiel à confirmer.",
    "Pointe du Meinga": "Repère géographique indicatif uniquement; site d'observation officiel et accès non confirmés.",
    "Guernsey": "Repère indicatif de Saint-Pierre-Port; arrivée de ferry à confirmer.",
    "Jersey": "Repère indicatif de Saint-Hélier; arrivée de ferry à confirmer.",
    "Chausey": "Repère approximatif de la Grande Île; accès et traversée à confirmer.",
}
FERRY_PORTS = (
    ("Guernsey", "Port ferry de Saint-Malo (repère approximatif)", (48.6441, -2.0234)),
    ("Jersey", "Port ferry de Saint-Malo (repère approximatif)", (48.6441, -2.0234)),
    ("Chausey", "Port de Granville (repère approximatif)", (48.8373, -1.5980)),
)


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
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Street_Map/MapServer/tile/{z}/{y}/{x}"
        ),
        attr=(
            "Tiles &copy; Esri — Sources: Esri, HERE, Garmin, "
            "&copy; OpenStreetMap contributors, and the GIS User Community"
        ),
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
    selected_islands = set()

    for step in steps:
        activity = step.get("activite_principale", {})
        title = activity.get("nom") or step.get("titre") or "Sortie retenue"
        route = step.get("trajet", {})
        maps_url = route.get("maps_url", "")
        maps_query = parse_qs(urlparse(maps_url).query).get("query", [route.get("arrivee", title)])[0]
        safe_title = html.escape(str(title))
        if maps_query in DIRECT_COORDINATES:
            selected_islands.add(maps_query)

        coordinates = DIRECT_COORDINATES.get(maps_query)
        if coordinates is None:
            place_queries = list(dict.fromkeys((
                *GEOCODE_QUERY_ALIASES.get(maps_query, []),
                maps_query,
                f"{title}, France",
                route.get("arrivee", ""),
            )))
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
            coordinate_note = DIRECT_COORDINATE_NOTES.get(maps_query)
            if coordinate_note:
                marker_popup += "<br>" + html.escape(coordinate_note)
                marker_tooltip += " (repère approximatif)"
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

    added_ports = set()
    for island, port_title, coordinates in FERRY_PORTS:
        if island not in selected_islands:
            continue
        if coordinates in added_ports:
            continue
        added_ports.add(coordinates)
        safe_port_title = html.escape(port_title)
        folium.Marker(
            location=coordinates,
            tooltip=safe_port_title,
            popup=f"{safe_port_title}<br>Point d’embarquement à confirmer auprès de l’opérateur.",
            icon=folium.Icon(color="darkpurple", icon="ship", prefix="fa"),
        ).add_to(map_view)
        marker_locations.append(coordinates)
        port_query = "Port de Granville" if island == "Chausey" else "Gare Maritime du Naye Saint-Malo"
        port_url = "https://www.google.com/maps/search/?api=1&query=" + port_query.replace(" ", "+")
        if port_url not in links:
            links.append(
                f'<li><a href="{html.escape(port_url, quote=True)}" target="_blank" '
                f'rel="noopener">{safe_port_title}</a></li>'
            )

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
