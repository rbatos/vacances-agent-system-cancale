"""Generate a self-contained dashboard from the current Cancale stay data."""

import argparse
import html
import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "vacances_data.json"
OUTPUT_FILE = ROOT_DIR / "dashboard.html"


def load_data(data_file=DATA_FILE):
    with open(data_file, "r", encoding="utf-8-sig") as source:
        return json.load(source)


def escape(value):
    return html.escape(str(value)) if value is not None else ""


def format_duration(value):
    if value is None:
        return "Non renseigné"
    hours, minutes = divmod(int(value), 60)
    if hours and minutes:
        return f"{hours} h {minutes} min"
    if hours:
        return f"{hours} h"
    return f"{minutes} min"


def render_steps(steps):
    if not steps:
        return '<p class="empty">Aucune sortie retenue pour le moment.</p>'

    cards = []
    for step in steps:
        title = escape(step.get("titre") or "Sortie")
        activity = step.get("activite_principale") or {}
        route = step.get("trajet") or {}
        date = step.get("date") or (
            f"Jour {step['jour']}" if step.get("jour") is not None else "À planifier"
        )
        route_url = route.get("maps_url")
        route_link = ""
        if isinstance(route_url, str) and route_url.startswith("https://"):
            route_link = (
                f'<a class="button secondary" href="{escape(route_url)}" '
                'target="_blank" rel="noopener">Voir le lieu</a>'
            )

        durations = []
        for label, key in (
            ("Aller", "duree_aller_minutes_estimee"),
            ("Retour", "duree_retour_minutes_estimee"),
            ("A/R", "duree_totale_minutes_estimee"),
        ):
            value = route.get(key)
            if value is not None:
                durations.append(f"<span>{label} : {format_duration(value)}</span>")
        duration_html = (
            '<div class="duration-row">' + "".join(durations) + "</div>"
            if durations
            else ""
        )
        route_description = escape(activity.get("description"))
        activity_name = escape(activity.get("nom"))
        route_text = " → ".join(
            escape(part) for part in (route.get("depart"), route.get("arrivee")) if part
        )
        cards.append(
            f"""
            <article class="activity-card">
              <div class="activity-top">
                <span class="badge">{escape(date)}</span>
                <span class="status">Retenue · à planifier</span>
              </div>
              <h3>{title}</h3>
              {f'<p class="activity-name">{activity_name}</p>' if activity_name else ""}
              {f'<p>{route_description}</p>' if route_description else ""}
              {f'<p class="route-text">{route_text}</p>' if route_text else ""}
              {duration_html}
              {route_link}
            </article>
            """
        )
    return "\n".join(cards)


def render_accommodations(stays):
    if not stays:
        return '<p class="empty">Aucun hébergement renseigné.</p>'
    return "\n".join(
        f"""
        <article class="simple-card">
          <h3>{escape(stay.get('nom') or 'Hébergement')}</h3>
          <p>{escape(stay.get('nuit') or '')}</p>
          <p class="muted">{escape(stay.get('avantages') or '')}</p>
          <span class="badge">{escape(stay.get('statut') or 'Statut non renseigné')}</span>
        </article>
        """
        for stay in stays
    )


def render_budget(data):
    budget = data.get("voyage", {}).get("budget", {})
    posts = budget.get("postes", [])
    minimum = budget.get("total_estime_min")
    maximum = budget.get("total_estime_max")
    ceiling = budget.get("plafond_max")
    envelope = (
        f"{escape(minimum)}–{escape(maximum)} €"
        if minimum is not None and maximum is not None
        else f"Jusqu’à {escape(ceiling)} €" if ceiling is not None
        else "Non renseignée"
    )
    if not posts:
        rows = (
            '<tr><td colspan="4" class="empty-cell">'
            "Aucun poste détaillé ni aucune dépense enregistrée.</td></tr>"
        )
        chart = '<p class="empty">La répartition sera affichée lorsque des postes seront renseignés.</p>'
    else:
        rows_list = []
        for post in posts:
            amount = post.get("montant")
            amount_text = f"{escape(amount)} €" if amount is not None else "Non renseigné"
            rows_list.append(
                "<tr>"
                f"<td>{escape(post.get('nom') or post.get('id') or 'Poste')}</td>"
                f"<td>{amount_text}</td>"
                f"<td>{escape(post.get('statut') or 'Non renseigné')}</td>"
                f"<td>{escape(post.get('details') or '')}</td>"
                "</tr>"
            )
        rows = "\n".join(rows_list)
        chart = '<p class="muted">Les postes ci-dessus proviennent du fichier de séjour.</p>'
    return envelope, rows, chart


def render_checklists(checklists):
    groups = (
        ("ados", "Enfants"),
        ("parents", "Parents"),
        ("voiture", "Voiture"),
    )
    sections = []
    for key, title in groups:
        items = checklists.get(key, [])
        if not items:
            content = '<p class="empty">Aucun élément renseigné.</p>'
        else:
            entries = []
            for index, item in enumerate(items):
                if isinstance(item, dict):
                    text = item.get("texte") or item.get("nom") or ""
                    item_id = item.get("id") or f"{key}-{index}"
                else:
                    text = str(item)
                    item_id = f"{key}-{index}"
                entries.append(
                    f'<label class="check-item"><input type="checkbox" '
                    f'data-check-id="{escape(item_id)}"> <span>{escape(text)}</span></label>'
                )
            content = "\n".join(entries)
        sections.append(f'<section class="check-group"><h3>{title}</h3>{content}</section>')
    return "\n".join(sections)


def render_map_links(steps):
    links = []
    for step in steps:
        route = step.get("trajet") or {}
        url = route.get("maps_url")
        if isinstance(url, str) and url.startswith("https://"):
            links.append(
                f'<li><a href="{escape(url)}" target="_blank" rel="noopener">'
                f'{escape(step.get("titre") or "Destination")}</a></li>'
            )
    if not links:
        return '<p class="empty">Aucune destination à afficher.</p>'
    return "<ul class=\"destination-list\">" + "".join(links) + "</ul>"


def render_dashboard(data):
    voyage = data.get("voyage", {})
    family = voyage.get("famille", {})
    children = family.get("enfants", [])
    ages = " et ".join(str(child["age"]) for child in children if child.get("age") is not None)
    family_summary = f"{family.get('adultes', 0)} adultes"
    if children:
        family_summary += f" + {len(children)} enfants"
        if ages:
            family_summary += f" (âges : {ages} ans)"
    budget_envelope, budget_rows, budget_chart = render_budget(data)
    steps = data.get("etapes", [])
    plan_b = data.get("jokers_plans_b", [])
    plan_b_content = (
        "\n".join(f'<article class="simple-card">{escape(item)}</article>' for item in plan_b)
        if plan_b
        else '<p class="empty">Aucun Plan B n’est enregistré.</p>'
    )

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(voyage.get('titre') or 'Séjour à Cancale')} — Dashboard</title>
  <style>
    :root {{ color-scheme: dark; --bg:#0b1220; --panel:#121d2d; --panel2:#172438;
      --text:#edf4fb; --muted:#a7b5c7; --line:#26364a; --cyan:#67d5e8;
      --orange:#ffb36b; --green:#74d6a0; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; color:var(--text); background:radial-gradient(ellipse at 80% 0,#17314b,var(--bg) 55%);
      font:15px/1.55 "Segoe UI",Arial,sans-serif; }}
    .shell {{ max-width:1320px; margin:auto; padding:24px; }}
    header {{ display:flex; justify-content:space-between; align-items:center; gap:20px;
      padding:22px 26px; border:1px solid var(--line); border-radius:20px;
      background:rgba(18,29,45,.92); }}
    h1,h2,h3,p {{ margin-top:0; }}
    h1 {{ margin-bottom:4px; font-size:clamp(22px,3vw,32px); }}
    h2 {{ font-size:21px; }}
    h3 {{ font-size:17px; }}
    .muted,.subtitle {{ color:var(--muted); }}
    .tabs {{ display:flex; gap:8px; overflow-x:auto; padding:14px 0; }}
    .tab-button,.button {{ cursor:pointer; border:1px solid var(--line); border-radius:10px;
      padding:9px 14px; color:var(--text); background:var(--panel2); text-decoration:none; }}
    .tab-button.active {{ color:#06131d; background:var(--cyan); border-color:var(--cyan); font-weight:700; }}
    .tab-panel {{ display:none; }} .tab-panel.active {{ display:block; }}
    .stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:14px; margin:10px 0 20px; }}
    .stat,.panel,.activity-card,.simple-card,.check-group {{ background:rgba(18,29,45,.9);
      border:1px solid var(--line); border-radius:16px; padding:19px; }}
    .stat strong {{ display:block; font-size:23px; color:var(--cyan); }}
    .stat span {{ color:var(--muted); font-size:13px; }}
    .grid {{ display:grid; grid-template-columns:minmax(0,1.5fr) minmax(280px,1fr); gap:18px; }}
    .stack {{ display:grid; gap:18px; align-content:start; }}
    .activity-list {{ display:grid; gap:12px; }}
    .activity-card h3 {{ margin:12px 0 4px; }}
    .activity-card p {{ margin:8px 0; }}
    .activity-name {{ color:var(--orange); font-weight:700; }}
    .activity-top,.duration-row {{ display:flex; flex-wrap:wrap; justify-content:space-between; gap:8px; }}
    .badge,.status {{ display:inline-block; border-radius:999px; padding:4px 9px; font-size:12px; }}
    .badge {{ color:var(--cyan); background:#153347; }}
    .status {{ color:var(--orange); background:#3a2b1e; }}
    .duration-row {{ justify-content:flex-start; margin:12px 0; color:var(--muted); font-size:13px; }}
    .duration-row span {{ padding:4px 8px; border-radius:8px; background:var(--panel2); }}
    .button.secondary {{ display:inline-block; font-size:13px; }}
    .empty {{ color:var(--muted); font-style:italic; }}
    .budget-summary {{ border-left:4px solid var(--green); padding:12px 16px; background:#132a29; border-radius:8px; }}
    table {{ width:100%; border-collapse:collapse; margin-top:16px; }}
    th,td {{ text-align:left; padding:10px; border-bottom:1px solid var(--line); vertical-align:top; }}
    th {{ color:var(--cyan); }} .empty-cell {{ color:var(--muted); text-align:center; }}
    .check-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:14px; }}
    .check-item {{ display:flex; gap:9px; margin:10px 0; color:var(--muted); }}
    .destination-list {{ padding-left:20px; }} .destination-list li {{ margin:9px 0; }}
    a {{ color:var(--cyan); }} .route-text {{ color:var(--muted); font-size:13px; }}
    .map-frame {{ width:100%; height:560px; border:1px solid var(--line); border-radius:14px; background:#fff; }}
    footer {{ color:var(--muted); font-size:12px; padding:20px 0; }}
    @media(max-width:800px) {{ .shell {{ padding:14px; }} header {{ align-items:flex-start; flex-direction:column; }}
      .grid {{ grid-template-columns:1fr; }} table {{ font-size:13px; }} th,td {{ padding:7px; }} }}
    @media print {{ body {{ color:#17202b; background:white; }} .shell {{ max-width:none; padding:0; }}
      header,.stat,.panel,.activity-card,.simple-card,.check-group {{ color:#17202b; background:white; border-color:#bbb; }}
      .tabs,.button {{ display:none; }} .tab-panel {{ display:block !important; margin:18px 0; }}
      .muted,.subtitle,.empty,.route-text {{ color:#444; }} .map-frame {{ display:none; }} }}
  </style>
</head>
<body>
  <main class="shell">
    <header>
      <div><h1>{escape(voyage.get('titre') or 'Séjour en famille à Cancale')}</h1>
        <p class="subtitle">{escape(voyage.get('sous_titre') or '')}</p>
        <span class="badge">{escape(voyage.get('dates') or '')} · {escape(voyage.get('statut') or 'En préparation')}</span>
      </div>
      <button class="button" type="button" onclick="window.print()">Imprimer</button>
    </header>

    <section class="stats" aria-label="Résumé du séjour">
      <div class="stat"><strong>{len(steps)}</strong><span>sorties retenues, à planifier</span></div>
      <div class="stat"><strong>{escape(family.get('total', 0))}</strong><span>{escape(family_summary)}</span></div>
      <div class="stat"><strong>{budget_envelope}</strong><span>enveloppe sur place · logement et trajet vers Cancale exclus</span></div>
      <div class="stat"><strong>2 h A/R</strong><span>maximum de conduite visé par sortie</span></div>
    </section>

    <nav class="tabs" aria-label="Sections du dashboard">
      <button class="tab-button active" data-tab="itinerary">Séjour</button>
      <button class="tab-button" data-tab="map">Carte & destinations</button>
      <button class="tab-button" data-tab="budget">Budget</button>
      <button class="tab-button" data-tab="checklists">Checklists</button>
    </nav>

    <section class="tab-panel active" id="itinerary">
      <div class="grid">
        <div class="panel"><h2>Sorties retenues</h2>
          <p class="muted">Aucune date ni réservation n’est déduite des choix. Les temps de trajet sont des estimations à vérifier le jour du déplacement.</p>
          <div class="activity-list">{render_steps(steps)}</div>
        </div>
        <div class="stack">
          <section class="panel"><h2>Hébergement fixe</h2>{render_accommodations(data.get('hebergements', []))}</section>
          <section class="panel"><h2>Plans B</h2>{plan_b_content}</section>
        </div>
      </div>
    </section>

    <section class="tab-panel" id="map">
      <div class="panel"><h2>Carte de la zone</h2>
        <p class="muted">La carte ci-dessous affiche Cancale et les points d’intérêt géolocalisés par le générateur de carte. Les emplacements approximatifs ou introuvables sont signalés; le point de Cancale situe la commune, pas l’adresse de l’hébergement. Le fond OpenStreetMap nécessite une connexion Internet.</p>
        <iframe class="map-frame" title="Carte des points d’intérêt du séjour" loading="lazy"
          src="carte_cancale.html"></iframe>
        <h3>Destinations sélectionnées</h3>{render_map_links(steps)}
      </div>
    </section>

    <section class="tab-panel" id="budget">
      <div class="panel"><h2>Budget sur place</h2>
        <div class="budget-summary"><strong>Enveloppe cible : {budget_envelope}</strong><br>
          <span>Ce montant est une cible, pas un total engagé ou dépensé. Hébergement et trajet jusqu’à Cancale exclus.</span></div>
        <table><thead><tr><th>Poste</th><th>Montant</th><th>Statut</th><th>Détails</th></tr></thead>
          <tbody>{budget_rows}</tbody></table>
        <div class="muted">{budget_chart}</div>
      </div>
    </section>

    <section class="tab-panel" id="checklists">
      <div class="panel"><h2>Checklists</h2>
        <p class="muted">Les cases cochées sont mémorisées dans ce navigateur uniquement; la liste provient du fichier de séjour.</p>
        <div class="check-grid">{render_checklists(data.get('checklists', {}))}</div>
      </div>
    </section>
    <footer>Dashboard généré depuis vacances_data.json. Les idées retenues restent à planifier; vérifiez horaires, tarifs, météo et trajets avant chaque sortie.</footer>
  </main>
  <script>
    document.querySelectorAll('.tab-button').forEach(button => button.addEventListener('click', () => {{
      document.querySelectorAll('.tab-button').forEach(item => item.classList.toggle('active', item === button));
      document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.toggle('active', panel.id === button.dataset.tab));
    }}));
    const storageKey = 'cancale-dashboard-checks';
    const savedChecks = JSON.parse(localStorage.getItem(storageKey) || '{{}}');
    document.querySelectorAll('[data-check-id]').forEach(input => {{
      const id = input.dataset.checkId;
      input.checked = Boolean(savedChecks[id]);
      input.addEventListener('change', () => {{
        savedChecks[id] = input.checked;
        localStorage.setItem(storageKey, JSON.stringify(savedChecks));
      }});
    }});
  </script>
</body>
</html>
"""


def generate_dashboard(data, output_file=OUTPUT_FILE):
    output_file = Path(output_file)
    output_file.write_text(render_dashboard(data), encoding="utf-8")
    return output_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_FILE, help="JSON du séjour")
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE, help="Dashboard HTML généré")
    args = parser.parse_args()
    output = generate_dashboard(load_data(args.data), args.output)
    print(f"Dashboard généré : {output}")


if __name__ == "__main__":
    main()
