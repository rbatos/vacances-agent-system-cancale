"""Generate a printable Cancale stay booklet from the confirmed JSON data."""

import argparse
import html
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "vacances_data.json"
OUTPUT_FILE = ROOT_DIR / "carnet_cancale.html"


def load_data(data_file=DATA_FILE):
    with open(data_file, "r", encoding="utf-8-sig") as source:
        return json.load(source)


def escape(value):
    return html.escape(str(value)) if value is not None else ""


def render_booklet(data):
    voyage = data.get("voyage", {})
    famille = voyage.get("famille", {})
    budget = voyage.get("budget", {})
    children = famille.get("enfants", [])
    child_ages = ", ".join(str(child.get("age")) for child in children if child.get("age") is not None)
    family_text = f"{famille.get('adultes', 0)} adultes et {len(children)} enfants"
    if child_ages:
        family_text += f" (âges indiqués : {child_ages} ans)"

    accommodation_items = []
    for stay in data.get("hebergements", []):
        name = escape(stay.get("nom") or "Hébergement")
        dates = escape(stay.get("nuit"))
        status = escape(stay.get("statut") or "Statut non renseigné")
        accommodation_items.append(f"<li><strong>{name}</strong> — {dates} <span>({status})</span></li>")
    accommodation_html = "<ul>" + "".join(accommodation_items) + "</ul>" if accommodation_items else "<p>Hébergement non renseigné.</p>"

    steps_html = []
    for step in data.get("etapes", []):
        day_value = step.get("date")
        if not day_value:
            day_value = f"Jour {step['jour']}" if step.get("jour") is not None else "À planifier"
        day = escape(day_value)
        title = escape(step.get("titre") or "Sortie")
        activity = step.get("activite_principale") or {}
        sections = [f"<h3>{day} — {title}</h3>"]
        if activity:
            sections.append(f"<p><strong>{escape(activity.get('nom'))}</strong></p>")
            if activity.get("horaires"):
                sections.append(f"<p>Horaires : {escape(activity['horaires'])}</p>")
            if activity.get("description"):
                sections.append(f"<p>{escape(activity['description'])}</p>")
        route = step.get("trajet") or {}
        route_parts = [route.get("depart"), route.get("arrivee")]
        route_text = " → ".join(escape(part) for part in route_parts if part)
        if route_text:
            sections.append(f"<p>Trajet : {route_text}</p>")
        if step.get("plan_b"):
            sections.append(f"<p><strong>Alternative à vérifier :</strong> {escape(step['plan_b'])}</p>")
        steps_html.append("\n".join(sections))

    if steps_html:
        itinerary_html = "\n".join(steps_html)
    else:
        itinerary_html = (
            "<p>Aucune sortie n'est encore validée. "
            "Les idées proposées par les agents seront ajoutées ici après validation familiale.</p>"
        )

    envelope_min = budget.get("total_estime_min")
    envelope_max = budget.get("total_estime_max")
    if envelope_min is not None and envelope_max is not None:
        envelope_text = f"Enveloppe cible sur place : {envelope_min} à {envelope_max} EUR pour la famille."
    else:
        envelope_text = "Enveloppe cible : 300 à 500 EUR de dépenses sur place pour la famille."

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Carnet de séjour à Cancale</title>
  <style>
    body {{ font-family: 'Segoe UI', sans-serif; line-height: 1.45; color: #24323a; max-width: 21cm; margin: auto; padding: 24px; }}
    h1 {{ color: #145b65; border-bottom: 2px solid #145b65; padding-bottom: 8px; }}
    h2 {{ color: #145b65; margin-top: 24px; }}
    h3 {{ margin-top: 18px; }}
    .summary {{ background: #f0f6f5; padding: 12px 16px; border-left: 4px solid #145b65; }}
    li {{ margin: 6px 0; }}
    @media print {{ body {{ padding: 0; }} h1, h2, h3 {{ page-break-after: avoid; }} }}
    @page {{ margin: 1.5cm; }}
  </style>
</head>
<body>
  <h1>{escape(voyage.get('titre') or 'Séjour en famille à Cancale')}</h1>
  <div class="summary">
    <p>{escape(voyage.get('sous_titre') or 'Hébergement fixe et sorties en étoile depuis Cancale')}</p>
    <p><strong>Dates :</strong> {escape(voyage.get('dates'))}</p>
    <p><strong>Famille :</strong> {escape(family_text)}</p>
    <p><strong>Point fixe :</strong> Cancale</p>
    <p><strong>Déplacements :</strong> maximum 2 h de conduite cumulée aller-retour par sortie.</p>
    <p><strong>Budget :</strong> {escape(envelope_text)} Hébergement et trajet jusqu'à Cancale exclus.</p>
  </div>
  <h2>Hébergement</h2>
  {accommodation_html}
  <h2>Sorties validées</h2>
  {itinerary_html}
</body>
</html>
"""


def generate_print(data, output_file=OUTPUT_FILE):
    output_file = Path(output_file)
    output_file.write_text(render_booklet(data), encoding="utf-8")
    return output_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_FILE, help="JSON du séjour")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Fichier HTML généré")
    args = parser.parse_args()
    output = generate_print(load_data(args.data), args.output)
    print(f"Carnet de séjour généré : {output}")


if __name__ == "__main__":
    main()
