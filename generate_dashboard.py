"""Generate a self-contained dashboard from the current Cancale stay data."""

import argparse
import html
import json
import re
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "vacances_data.json"
OUTPUT_FILE = ROOT_DIR / "dashboard.html"
MAX_DRIVE_MINUTES = 180
ACTIVITY_BUDGET_IDS = {
    "Ferme Marine de Cancale": "activite-ferme-marine",
    "Micro Zoo de Saint-Malo": "activite-micro-zoo",
    "Saint-Suliac": "activite-saint-suliac",
    "Dol-de-Bretagne et Cathédraloscope": "activite-cathedraloscope",
    "Dinan, centre historique": "activite-dinan",
    "Château et lac de Combourg": "activite-combourg",
    "Alligator Bay": "activite-alligator-bay",
    "Journée à Rennes — activités à choisir, sans planning horaire": "activite-rennes",
    "Village de la Route du Rhum 2026 — port de Saint-Malo": "activite-route-du-rhum-village",
    "Départ de la Route du Rhum — dimanche 1er novembre à confirmer": "activite-route-du-rhum-depart",
    "Parc zoologique de la Bourbansais": "activite-bourbansais",
    "Guernesey — excursion à confirmer": "activite-iles-guernesey",
    "Jersey — excursion à confirmer": "activite-iles-jersey",
    "Chausey — excursion à confirmer": "activite-iles-chausey",
    "Saint-Briac-sur-Mer — balade côtière à confirmer": "activite-saint-briac",
    "Fréhel / Cap Fréhel — courte découverte à confirmer": "activite-cap-frehel",
    "Saint-Brieuc — centre-ville à confirmer": "activite-saint-brieuc",
}


def load_data(data_file=DATA_FILE):
    with open(data_file, "r", encoding="utf-8-sig") as source:
        return json.load(source)


def escape(value):
    return html.escape(str(value)) if value is not None else ""


def render_details(value):
    text = str(value or "")
    parts = re.split(r"(https://[^\s]+)", text)
    rendered = []
    for part in parts:
        if not part:
            continue
        if part.startswith("https://"):
            url = part.rstrip(".,;:)")
            suffix = part[len(url):]
            safe_url = html.escape(url, quote=True)
            rendered.append(
                f'<a href="{safe_url}" target="_blank" rel="noopener">{html.escape(url)}</a>'
                f"{html.escape(suffix)}"
            )
        else:
            rendered.append(html.escape(part))
    return "".join(rendered)


def format_euros(value):
    return f"{value:,.2f}".replace(",", " ").replace(".", ",") + " €"


def format_duration(value):
    if value is None:
        return "Non renseigné"
    hours, minutes = divmod(int(value), 60)
    if hours and minutes:
        return f"{hours} h {minutes} min"
    if hours:
        return f"{hours} h"
    return f"{minutes} min"


def render_steps(steps, budget_posts=None):
    if not steps:
        return '<p class="empty">Aucune sortie retenue pour le moment.</p>'

    budget_by_id = {
        post.get("id"): post
        for post in (budget_posts or [])
        if post.get("id") in ACTIVITY_BUDGET_IDS.values()
    }
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
        route_description = render_details(activity.get("description"))
        activity_name = escape(activity.get("nom"))
        route_text = " → ".join(
            escape(part) for part in (route.get("depart"), route.get("arrivee")) if part
        )
        status = escape(step.get("statut") or "Retenue · à planifier")
        budget_post_id = ACTIVITY_BUDGET_IDS.get(step.get("titre"))
        budget_post = budget_by_id.get(budget_post_id)
        budget_html = ""
        if budget_post:
            amount = budget_post.get("montant")
            amount_min = budget_post.get("montant_min")
            amount_max = budget_post.get("montant_max")
            if isinstance(amount, (int, float)):
                amount_text = format_euros(amount)
            elif isinstance(amount_min, (int, float)) and isinstance(amount_max, (int, float)):
                amount_text = f"{format_euros(amount_min)}–{format_euros(amount_max)}"
            else:
                amount_text = "À confirmer"
            budget_id = str(budget_post.get("id", ""))
            if budget_id.startswith("activite-iles-"):
                budget_label = "Provision partielle (hors traversée) : "
            elif budget_id in {
                "activite-saint-briac",
                "activite-cap-frehel",
                "activite-saint-brieuc",
            }:
                budget_label = "Budget partiel indicatif : "
            else:
                budget_label = "Billets indicatifs : "
            budget_html = (
                '<div class="activity-budget">'
                f'<strong>{budget_label}{amount_text}</strong>'
                f'<span>{escape(budget_post.get("statut") or "Statut non renseigné")}</span>'
                f'<p>{render_details(budget_post.get("details"))}</p>'
                "</div>"
            )
        cards.append(
            f"""
            <article class="activity-card">
              <div class="activity-top">
                <span class="badge">{escape(date)}</span>
                <span class="status">{status}</span>
              </div>
              <h3>{title}</h3>
              {f'<p class="activity-name">{activity_name}</p>' if activity_name else ""}
              {f'<p>{route_description}</p>' if route_description else ""}
              {budget_html}
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
        f"{format_euros(minimum)}–{format_euros(maximum)}"
        if minimum is not None and maximum is not None
        else f"Jusqu’à {format_euros(ceiling)}" if ceiling is not None
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
        forecast_posts = []
        activity_posts = []
        for post in posts:
            amount = post.get("montant")
            amount_min = post.get("montant_min")
            amount_max = post.get("montant_max")
            if str(post.get("id", "")).startswith("activite-"):
                activity_posts.append(post)
            if isinstance(amount_min, (int, float)) and isinstance(amount_max, (int, float)):
                amount_text = f"{format_euros(amount_min)}–{format_euros(amount_max)}"
                if (
                    str(post.get("statut", "")).casefold().startswith("prévisionnel")
                    and not str(post.get("id", "")).startswith("activite-")
                ):
                    forecast_posts.append(post)
            else:
                amount_text = format_euros(amount) if amount is not None else "À confirmer"
            rows_list.append(
                "<tr>"
                f"<td>{escape(post.get('nom') or post.get('id') or 'Poste')}</td>"
                f"<td>{amount_text}</td>"
                f"<td>{escape(post.get('statut') or 'Non renseigné')}</td>"
                f"<td>{render_details(post.get('details'))}</td>"
                "</tr>"
            )
        rows = "\n".join(rows_list)
        if forecast_posts:
            forecast_min = sum(post["montant_min"] for post in forecast_posts)
            forecast_max = sum(post["montant_max"] for post in forecast_posts)
            paid_activity_total = sum(
                post["montant"]
                for post in activity_posts
                if isinstance(post.get("montant"), (int, float)) and post["montant"] > 0
            )
            chart = (
                f'<p><strong>Prévision hors billets d’activités : '
                f'{format_euros(forecast_min)}–{format_euros(forecast_max)}</strong> '
                "(repas, déplacements locaux et marge; estimations non vérifiées, non engagées "
                "et non dépensées).</p>"
                f'<p><strong>Somme des montants calculés/conditionnels affichés pour les activités payantes : '
                f'{format_euros(paid_activity_total)}</strong> si toutes ces options étaient choisies. '
                "Ce n’est pas un programme ni un total familial complet : plusieurs tarifs du moins "
                "de 3 ans et certaines catégories d’âge restent à confirmer; Rennes et les activités "
                "de la Route du Rhum ne sont pas comprises dans cette somme. Les provisions partielles "
                "repas/collations des îles ne sont pas des coûts totaux et ne s’ajoutent pas sans ajustement "
                "à la provision générale des repas. "
                "Pour la Bourbansais, la visite guidée facultative ajoute 15,00 € pour les deux adultes "
                "et l’enfant de 7 ans si le supplément enfant lui est applicable.</p>"
            )
        else:
            chart = '<p class="muted">Les postes ci-dessus proviennent du fichier de séjour.</p>'
    return envelope, rows, chart


def render_checklists(checklists):
    sections = (
        ("documents", "Documents et réservations à confirmer"),
        ("vetements", "Vêtements d’automne"),
        ("enfants", "Affaires des enfants"),
        ("sorties", "Sorties et sécurité"),
        ("voiture", "Véhicule et trajets"),
    )
    legacy_sections = {
        "ados": "enfants",
        "parents": "documents",
        "voiture": "voiture",
    }
    items_by_section = {key: [] for key, _ in sections}
    for legacy_key, items in checklists.items():
        default_section = legacy_sections.get(legacy_key, "sorties")
        for index, item in enumerate(items):
            section_key = (
                item.get("section", default_section)
                if isinstance(item, dict)
                else default_section
            )
            if section_key not in items_by_section:
                section_key = default_section
            text = (
                item.get("texte") or item.get("nom") or ""
                if isinstance(item, dict)
                else str(item)
            )
            item_id = (
                item.get("id") or f"{legacy_key}-{index}"
                if isinstance(item, dict)
                else f"{legacy_key}-{index}"
            )
            items_by_section[section_key].append((item_id, text))

    rendered_sections = []
    for key, title in sections:
        items = items_by_section[key]
        if not items:
            content = '<p class="empty">Aucun élément renseigné.</p>'
        else:
            entries = []
            for item_id, text in items:
                entries.append(
                    f'<label class="check-item"><input type="checkbox" '
                    f'data-check-id="{escape(item_id)}"> <span>{escape(text)}</span></label>'
                )
            content = "\n".join(entries)
        rendered_sections.append(f'<section class="check-group"><h3>{title}</h3>{content}</section>')
    return "\n".join(rendered_sections)


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


def render_rennes_route_rhum(steps, budget_posts):
    special_titles = {
        "Journée à Rennes — activités à choisir, sans planning horaire",
        "Village de la Route du Rhum 2026 — port de Saint-Malo",
        "Départ de la Route du Rhum — dimanche 1er novembre à confirmer",
    }
    selected_steps = [step for step in steps if step.get("titre") in special_titles]
    cards = render_steps(selected_steps, budget_posts)
    return f"""
      <div class="panel">
        <h2>Rennes — vendredi 30 octobre 2026</h2>
        <p><strong>Journée fixée par la famille.</strong> Activités, restaurant et transport ci-dessous proposés, non réservés. Deux adultes, enfants de 7 ans et 2 ans. Sources consultées le 29 octobre 2026 par le Scout, le Navigateur, le Trésorier et la Sentinelle.</p>
        <h3>Déroulé conseillé, sans obligation horaire</h3>
        <ol>
          <li><strong>Viser une arrivée vers 10 h–10 h 30.</strong> Adapter le départ au trafic et au transport retenu; prévoir la marge parking, métro, toilettes et collation, non comprise dans les durées de conduite.</li>
          <li><strong>Vers 10 h 30 : Musée de Bretagne, 30–45 min proposées.</strong> Quelques objets et un livret 7–12 ans pour le grand; observation libre accompagnée pour le petit. Permanent gratuit. Ne pas imposer une visite complète.</li>
          <li><strong>Vers 11 h 30–12 h : déjeuner dans le centre, puis vraie pause.</strong> Choisir un restaurant ci-dessous. Compter une marche supplémentaire depuis les Champs Libres; ne pas enchaîner une séance réservée juste après. Demander le délai avant de commander, chaise haute et place poussette.</li>
          <li><strong>Après la pause : Thabor facultatif, 30–45 min proposées.</strong> Allées, volière et aire de jeux selon les âges affichés; entrée Saint-Melaine ou Palestine, pas le grand escalier rue de Paris. Le parc peut être fermé pour intempéries.</li>
          <li><strong>Centre ancien en petit complément seulement.</strong> Choisir Champ-Jacquet ou rue du Chapitre, 20–30 min proposées pour regarder les maisons à pans de bois. Pavés, pentes et traversées : poussette utile mais inconfort possible. Supprimer le centre ou le parc si fatigue et rentrer sans dernier objectif à terminer.</li>
        </ol>
        <p class="muted">Horaires et durées du déroulé conseillés, pas des rendez-vous officiels. Les traversées à pied entre les secteurs s'ajoutent; ne pas chercher à tout faire. Prévoir eau, collation, rechange, vêtements chauds en couches et pause toilettes avant le retour.</p>
        <h3>Activités : choix communs et alternatives par âge</h3>
        <ul>
          <li><strong>Musée de Bretagne :</strong> exposition permanente gratuite pour quatre. Champs Libres, 10 cours des Alliés; horaires vacances vendredi <strong>10 h–19 h</strong>. Livret 7–12 ans disponible; à 2 ans, visite accompagnée courte plutôt qu'animation spécifique. <a href="https://www.leschampslibres.fr/au-programme/vacances" target="_blank" rel="noopener">Programme Toussaint 2026</a> · <a href="https://www.leschampslibres.fr/les-champs-libres/musee-de-bretagne/visite-a-votre-rythme" target="_blank" rel="noopener">Visite et livrets</a>.</li>
          <li><strong>Bibliothèque « Chez les enfants » :</strong> gratuite, espace 0–11 ans, albums et coins lecture; 20–40 min proposées, librement écourtables. Meilleur repli calme commun; pas un espace de sieste garanti. <a href="https://www.leschampslibres.fr/les-champs-libres/bibliotheque/la-bibliotheque-en-un-coup-doeil" target="_blank" rel="noopener">Espaces de la bibliothèque</a>.</li>
          <li><strong>Thabor :</strong> promenade gratuite, ouverture normale d'octobre <strong>7 h 30–18 h 30</strong>, sauf fermeture météo; toilettes publiques annoncées, change non confirmé. Allées accessibles à privilégier, ne pas parcourir tout le parc. <a href="https://www.tourisme-rennes.com/decouvrir-rennes/parcs-jardins/parc-du-thabor/" target="_blank" rel="noopener">Accès et horaires</a>.</li>
          <li><strong>Fourmis, Espace des sciences :</strong> exposition tout public, créneaux vacances <strong>10 h, 12 h 15, 14 h 30, 16 h 45</strong>, durée officielle de créneau 2 h. Proposer seulement 45–60 min selon l'attention et confirmer la sortie anticipée. Tarif publié famille : <strong>22 EUR</strong> (8 + 8 + 6 + gratuit moins de 5 ans), billet expositions Fourmis/Cerveau; cela ne rend pas Cerveau adapté au petit (annoncé dès 8 ans). Places non vérifiées. <a href="https://www.leschampslibres.fr/au-programme/fourmis" target="_blank" rel="noopener">Fourmis</a> · <a href="https://www.espace-sciences.org/rennes/vous-etes/famille" target="_blank" rel="noopener">Tarifs</a>.</li>
          <li><strong>Laboratoire de Merlin :</strong> séance libre du vendredi 30 à <strong>12 h 30, 1 h, dès 6 ans</strong>, intéressante pour le grand mais pas une activité commune garantie pour 2 ans. L'accueil éventuel du petit doit être confirmé; ne pas confondre gratuité et âge adapté. <a href="https://www.leschampslibres.fr/au-programme/laboratoire-de-merlin-seance-libre-sans-animation/49646" target="_blank" rel="noopener">Séance datée</a>.</li>
          <li><strong>Planétarium : pas de séance commune aux deux âges.</strong> Petit Spationaute strictement 2–5 ans, environ 45 min, vendredi vacances 10 h 30 et 11 h 45; le 30 à 10 h 30 est annoncé, places inconnues. 6 EUR par personne, soit 12 EUR pour un adulte et le petit; arriver 20 min avant. Le 7 ans n'est pas admis dans cette tranche d'âge. Pour le grand : Système solaire le 30 à 16 h, 1 h, dès 5 ans (14 EUR adulte + enfant), pas pour le petit. Options seulement si vous acceptez de vous séparer; aucune réservation. <a href="https://www.espace-sciences.org/rennes/planetarium/seance/le-petit-spationaute" target="_blank" rel="noopener">Petit Spationaute</a> · <a href="https://www.leschampslibres.fr/au-programme/a-la-decouverte-du-systeme-solaire/48500" target="_blank" rel="noopener">Système solaire</a>.</li>
        </ul>
        <p><strong>Poussette :</strong> accueil accessible aux Champs Libres, mais <strong>poussettes interdites dans les expositions de l'Espace des sciences et au planétarium, sans dépôt à l'accueil</strong>. Confirmer une solution avant de choisir Fourmis ou une séance. Sanitaires, table à langer et matériel accepté à confirmer : Champs Libres 02 23 40 66 00. <a href="https://www.espace-sciences.org/rennes/infos-pratiques" target="_blank" rel="noopener">Conditions d'accès spécifiques</a>.</p>
        <h3>Déjeuner : quatre possibilités, aucune réservée</h3>
        <p>Déjeuner tôt, choisir un plat simple et demander le délai réel avant de s'installer. Ces adresses sont dans le centre ancien, pas au pied des Champs Libres. Aucune durée de service, chaise haute, table disponible ou accessibilité poussette n'est garantie.</p>
        <ul>
          <li><strong>La Rozell — premier choix économique à confirmer sur place.</strong> 14 rue de Penhoët; vendredi 11 h–22 h 30. Complète 8,50 EUR, super complète 11,50 EUR, beurre-sucre 3,50 EUR, chocolat 6,50 EUR : <strong>prix publiés dans les rubriques à emporter/livraison, pas confirmés en salle</strong>. Exemple arithmétique 4 complètes + 4 beurre-sucre = 48 EUR hors boissons, pas une quantité conseillée au petit. Menu enfant non trouvé. Viser 11 h 30 si cet horaire vous convient. <a href="https://www.larozell.fr/" target="_blank" rel="noopener">Horaires/adresse</a> · <a href="https://www.larozell.fr/carte-la-rozell-restaurant-rennes" target="_blank" rel="noopener">Carte et prix</a>.</li>
          <li><strong>Les Fils à Maman — option explicitement familiale.</strong> 11 rue du Champ-Jacquet; vendredi midi 12 h–14 h. Accueil « kids friendly » annoncé; prix et menu enfant non vérifiés, carte automne 2026 publiée mais non lisible par l'outil. Demander le coût avant de choisir : ce n'est pas une option économique certifiée. <a href="https://www.lesfilsamaman.com/restaurants/rennes/" target="_blank" rel="noopener">Restaurant, horaires et carte</a>.</li>
          <li><strong>La Saint-Georges — alternative crêperie.</strong> 11 rue du Chapitre; vendredi 12 h–14 h. Galettes et crêpes; prix et menu enfant inconnus dans les contenus consultés. Confirmer tarifs et délai avant installation. <a href="https://www.creperie-saintgeorges.fr/rue-du-chapitre-rennes.html" target="_blank" rel="noopener">Adresse et horaires</a> · <a href="https://www.creperie-saintgeorges.fr/galettes-crepes.html" target="_blank" rel="noopener">Carte</a>.</li>
          <li><strong>Poutinebros — option restauration rapide / à emporter.</strong> 17–19 rue de Penhoët; click &amp; collect vendredi 12 h–23 h, horaires de salle non distingués. Burgers et poutines, accueil famille annoncé; prix, menu enfant et temps de préparation non vérifiés. <a href="https://www.poutinebros.com/nos-poutineries/rennes/" target="_blank" rel="noopener">Infos et commande</a>.</li>
        </ul>
        <p><strong>Provision déjeuner proposée : 40–60 EUR pour quatre</strong>, objectif de budget non garanti par les cartes, hors transport et visite. Aucun repas gratuit pour le 2 ans supposé. Solution d'écourtage : repas simple à emporter si adapté et lieu abrité disponible; pas de table ni de coin pique-nique couvert garanti.</p>
        <h3>Transport à choisir et budget de la journée</h3>
        <ul>
          <li><strong>Compromis conseillé : Cancale → parc relais Cesson–ViaSilva → métro b.</strong> Estimation OSRM hors trafic : <strong>61 min aller, 58 min retour, 119 min cumul</strong>, vers repères approximatifs; ajouter métro, marche et pauses. Métro b vers Gares pour les Champs Libres ou Sainte-Anne pour le centre. La Poterie reste une alternative (65 + 64 = 129 min hors trafic), pas nécessairement la plus courte depuis Cancale.</li>
          <li><strong>STAR :</strong> parc relais gratuit pour usagers sous conditions, vendredi 5 h–2 h le lendemain; titre à valider dans une autre station moins d'une heure avant la sortie. Trajet 1 h : <strong>1,70 EUR par voyageur payant</strong>. 2 ans gratuit sans titre; 7 ans gratuit seulement avec KorriGo et titre enfant gratuit chargé, sinon payant. Aller-retour simple à trois payants : <strong>10,20 EUR</strong> (6,80 EUR si le grand a réellement son titre gratuit), hors support éventuel et trajets supplémentaires. PASS Pluriel non valable ce vendredi. Vérifier les ascenseurs le matin; pas d'escalator avec enfant en poussette. <a href="https://www.star.fr/reseau-star/parc-relais/fonctionnement" target="_blank" rel="noopener">Parcs relais</a> · <a href="https://www.star.fr/star-et-moi/parent-eleve-etudiant/gratuite-enfants" target="_blank" rel="noopener">Enfants</a> · <a href="https://www.star.fr/titres-et-tarifs/trouver-mon-tarif/1-voyage" target="_blank" rel="noopener">Tarif</a> · <a href="https://www.star.fr/actualites/travaux-ascenseurs" target="_blank" rel="noopener">Ascenseurs</a>.</li>
          <li><strong>Alternative voiture au centre : De Gaulle–Gare.</strong> Estimation 64 min aller, 63 min retour, <strong>127 min cumul</strong> hors trafic; parking publié 8,40 EUR/4 h ou 12,40 EUR/6 h, places non garanties. Plus simple pour retrouver la voiture près des Champs Libres. <a href="https://www.c-park.fr/parking/parking-de-gaulle-gare/" target="_blank" rel="noopener">Parking</a>. Dol + TER reste possible mais horaires aller-retour et prix famille non vérifiés : pas une solution confirmée pour demain.</li>
          <li><strong>Repère de budget, non engagé :</strong> musée/bibliothèque/Thabor gratuits + repas 40–60 EUR + STAR à trois payants A/R 10,20 EUR = <strong>50,20–70,20 EUR hors carburant</strong>, support éventuel et métro supplémentaire. Avec Fourmis : 72,20–92,20 EUR selon les mêmes hypothèses. En voiture au centre pour 6 h : 52,40–72,40 EUR hors carburant pour le scénario gratuit. Ne pas cumuler mécaniquement parking centre et parc relais.</li>
        </ul>
        <p class="muted">Sources routage : OSRM/OpenStreetMap, calculs du Navigateur le 29 octobre, sans trafic réel. <a href="https://router.project-osrm.org/route/v1/driving/-1.8497693,48.6749696;-1.624,48.136?overview=false" target="_blank" rel="noopener">ViaSilva aller</a> · <a href="https://router.project-osrm.org/route/v1/driving/-1.624,48.136;-1.8497693,48.6749696?overview=false" target="_blank" rel="noopener">retour</a>. Cible 3 h de conduite A/R respectée par ces seules estimations, pas garantie avec le trafic.</p>
        <h3>Météo, repli et vérifications du matin</h3>
        <p>Prévision <a href="https://meteofrance.com/previsions-meteo-france/rennes/35000" target="_blank" rel="noopener">Météo-France Rennes</a> consultée par la Sentinelle : bulletin du 29 octobre à 15 h pour le 30, soleil annoncé, matin frais (environ 5 °C vers 7 h), environ 14 °C vers 13 h et vent faible. Prévision à actualiser, rafales non établies. La <a href="https://vigilance.meteofrance.fr/fr/ille-et-vilaine/demain" target="_blank" rel="noopener">vigilance pour demain</a> est datée mais ses couleurs n'ont pas été lisibles : niveau inconnu, pas « aucune alerte ».</p>
        <p><strong>Pluie ou fatigue :</strong> musée + bibliothèque, puis retour; ne pas acheter une séance supplémentaire pour remplir la journée. Avant départ : trafic, météo/vigilance, ouverture parc, ascenseurs STAR; si activité payante, places et poussette; si restaurant assis, tarifs en salle, délai et accueil enfants. Sanitaires/ change à demander à l'accueil, jamais supposés disponibles.</p>
      </div>
      <div class="panel">
        <h2>Route du Rhum — village et départ</h2>
        <p class="muted">Les spécialistes n'ont pas pu vérifier en direct les publications 2026. Dates/heures, programme, tarifs, accès et restrictions restent à confirmer auprès de l'organisateur et des autorités; ces pistes ne sont pas des réservations ni un programme officiel.</p>
        <h3>Au village du port de Saint-Malo</h3>
        <ul>
          <li>Commencer par observer les voiliers depuis les espaces publics autorisés; suivre le parcours visiteurs et les consignes de l'organisation.</li>
          <li>Parcourir quelques stands à un rythme lent, puis choisir une seule animation annoncée comme adaptée aux deux enfants. Ne pas présumer qu'on peut monter à bord, que les animations sont gratuites ou que toutes conviennent à un enfant de moins de 3 ans.</li>
          <li>Prévoir une pause et un point de rendez-vous facile à reconnaître; garder le tout-petit près d'un adulte dans la foule. Poussette, sanitaires, change, accès et stationnement sont à confirmer.</li>
          <li>Le repère routier existant vers Porte Saint-Vincent est une estimation ordinaire de 22 min aller / 23 min retour (45 min A/R), pas une mesure jusqu'à l'entrée du village le jour de l'événement; fermetures, stationnement et navettes peuvent modifier le trajet.</li>
        </ul>
        <h3>Départ du dimanche 1er novembre — Pointe du Meinga ?</h3>
        <ul>
          <li>Confirmer d'abord la date et l'heure du départ et la liste officielle des sites d'observation. La Pointe du Meinga n'est ni confirmée comme point officiel, ni comme offrant une vue dégagée; vérifier son orthographe et l'accès exact.</li>
          <li>Si les autorités confirment l'accès, évaluer séparément conduite aller, retour et cumul (maximum visé 3 h), stationnement, marche, état du sentier, foule, sanitaires et possibilité de repartir. Signaler tout dépassement; sans confirmation, ne pas en faire le point de rendez-vous.</li>
          <li>Contrôler météo, vent, visibilité, état de mer et marée le jour même; tenir les enfants éloignés des falaises et du bord. Prévoir vêtements chauds, imperméables et possibilité de renoncer rapidement.</li>
          <li>Repli : rejoindre le village uniquement si son accès est confirmé, choisir une activité couverte dont l'ouverture est vérifiée, ou rentrer se reposer à Cancale.</li>
        </ul>
        <p><strong>Prix :</strong> inconnus pour l'entrée éventuelle, les animations, les visites de bateaux, le transport et le stationnement. Une sortie en bateau pour suivre la course serait une activité distincte, à ne prévoir qu'après confirmation officielle du tarif, des places, des âges acceptés et de la météo.</p>
        <p class="muted">Sources officielles à vérifier : <a href="https://www.routedurhum.com/" target="_blank" rel="noopener">Route du Rhum</a>, <a href="https://www.saint-malo.fr/" target="_blank" rel="noopener">Ville de Saint-Malo</a>, <a href="https://www.saintcoulomb.com/" target="_blank" rel="noopener">Mairie de Saint-Coulomb</a>, <a href="https://meteofrance.com/" target="_blank" rel="noopener">Météo-France</a> et <a href="https://maree.shom.fr/" target="_blank" rel="noopener">SHOM (marées)</a>. Liens fournis comme points de vérification; informations 2026 non vérifiées indépendamment ici.</p>
      </div>
      <div class="activity-list">{cards}</div>
    """


def render_island_options():
    return """
      <div class="panel">
        <h2>Avant de choisir une île : conditions de faisabilité</h2>
        <p class="muted">Les îles sont ajoutées ici comme pistes de découverte, pas comme sorties retenues, réservées ou inscrites à l’itinéraire. Au 20 octobre 2026, ni les moteurs de réservation ni les calendriers officiels n’ont pu être consultés dans cette session. Les traversées, horaires, prix, accès, ouvertures et disponibilités du 25 octobre au 1er novembre restent donc non vérifiés. Ne partez pas sans confirmation datée auprès de l’opérateur.</p>
        <ul>
          <li><strong>Une île par journée.</strong> Guernesey et Jersey exigent une traversée maritime depuis Saint-Malo si une liaison est offerte à la date choisie; vérifier départ et retour le même jour, durée à terre, heure limite de présentation, contrôles et conditions de retard ou d’annulation.</li>
          <li><strong>Conduite : maximum visé de 3 h A/R depuis Cancale.</strong> Le temps en bateau ne compte pas dans ce plafond. Les durées Cancale–terminal exactes, parking et marche jusqu’à l’embarquement ne sont pas vérifiés ici : faire deux calculs routiers datés vers l’adresse exacte du terminal avant de retenir Jersey ou Guernesey. L’estimation non vérifiée pour Chausey (environ 2 h 20–2 h 40 A/R) serait dans ce maximum si elle se confirme, mais doit être recalculée.</li>
          <li><strong>Âges et documents.</strong> La famille compte un enfant de 7 ans et un enfant de 2 ans (moins de 3 ans pendant le séjour). Vérifier les règles tarifaires du transporteur pour chacun, les pièces d’identité et exigences d’entrée applicables à chaque voyageur auprès des autorités officielles; ne pas présumer d’une gratuité ou qu’une carte d’identité suffit.</li>
          <li><strong>Journée longue et peu écourtable.</strong> Prévoir une seule activité principale, collations, eau, pauses, temps calme/sieste et vêtements coupe-vent/imperméables. Confirmer toilettes et change au terminal, à bord et sur l’île, politique poussette, bagages et possibilité réelle de modifier le retour. Un retour imposé par le bateau limite l’écourtage.</li>
          <li><strong>Repli.</strong> Si le bateau, la mer, les horaires ou l’état de fatigue rendent la journée incertaine, renoncer avant le départ. Une activité couverte à Saint-Malo ne remplace pas une traversée annulée; le repos à Cancale est le repli le plus sûr.</li>
        </ul>
        <p><strong>Sources tarifaires officielles à consulter — aucun prix 2026 vérifié :</strong>
          <a href="https://www.condorferries.co.uk/" target="_blank" rel="noopener">Condor Ferries, horaires et réservation Jersey/Guernesey</a>;
          <a href="https://www.vedettesjoliefrance.com/destinations/granville-les-iles-chausey/visiter-les-iles-chausey/" target="_blank" rel="noopener">Vedettes Jolie France — visiter Chausey, tarifs et traversées</a> (lien signalé par la famille); et
          <a href="https://www.vedettesdechausey.com/" target="_blank" rel="noopener">Vedettes de Chausey</a> (Chausey);
          <a href="https://www.gov.uk/foreign-travel-advice/jersey/entry-requirements" target="_blank" rel="noopener">conseils officiels d’entrée pour Jersey</a> et
          <a href="https://www.gov.uk/foreign-travel-advice/guernsey/entry-requirements" target="_blank" rel="noopener">pour Guernesey</a>;
          <a href="https://meteofrance.com/" target="_blank" rel="noopener">Météo-France</a> et
          <a href="https://maree.shom.fr/" target="_blank" rel="noopener">SHOM</a> (météo et marées). Ces liens sont des pistes de vérification, pas des tarifs consultés ou confirmés.</p>
      </div>
      <div class="activity-list">
        <article class="activity-card">
          <div class="activity-top"><span class="badge">Option à vérifier — aucune date fixée</span><span class="status">Non validée</span></div>
          <h3>Guernesey — Saint-Pierre-Port en découverte courte</h3>
          <p class="activity-name">Port et centre-ville, sans programme chargé</p>
          <p><strong>Accès :</strong> vérifier auprès de Condor Ferries si une traversée Saint-Malo–Guernesey et un retour le même jour sont proposés pendant les dates du séjour. Aucune durée de bateau, heure de départ, heure de retour ni liaison effective n’est confirmée ici. Conduite Cancale–terminal maritime de Saint-Malo : aller, retour et cumul à calculer pour le jour prévu; la limite de 2 h n’est pas encore démontrée.</p>
          <p><strong>Idée sur place :</strong> si les horaires laissent assez de temps, faire une courte promenade au port et dans Saint-Pierre-Port, avec une seule visite intérieure éventuelle à choisir après confirmation de l’ouverture, de l’âge admis, du prix et de l’accessibilité. Ce sont des idées à vérifier, pas des horaires ou visites confirmés.</p>
          <p><strong>Avec les enfants :</strong> viser un parcours bref, pauses assises et toilettes identifiées; vérifier pentes, pavés, poussette et change. Prévoir porte-bébé en complément si utile, eau, collation et temps calme pour l’enfant de 2 ans. Près du port et du littoral, surveillance rapprochée et pas de marche côtière exposée par vent/pluie.</p>
          <div class="activity-budget"><strong>Provision partielle : 40–70 €</strong><span>Repas et collations uniquement; traversée et total famille à chiffrer</span><p>Provision hypothétique pour une journée à quatre, pas un tarif local vérifié. Obtenir un devis aller-retour daté pour les 2 adultes et les enfants de 7 ans et 2 ans; ajouter parking, déplacements locaux et éventuelle visite. Le tarif du moins de 3 ans reste inconnu. Source tarifaire à consulter : <a href="https://www.condorferries.co.uk/" target="_blank" rel="noopener">Condor Ferries</a>.</p></div>
          <p><strong>Avant achat :</strong> horaires et temps d’enregistrement; pièces d’identité/exigences d’entrée de tous les voyageurs; horaires de retour et règles de modification; bagages et poussette; sanitaires à bord/à terre; stationnement et tarif; météo marine et alertes de l’opérateur.</p>
          <p><a href="https://www.condorferries.co.uk/" target="_blank" rel="noopener">Condor Ferries</a> · <a href="https://www.visitguernsey.com/" target="_blank" rel="noopener">Visit Guernsey (idées de visite à vérifier)</a></p>
        </article>
        <article class="activity-card">
          <div class="activity-top"><span class="badge">Option à vérifier — aucune date fixée</span><span class="status">Non validée</span></div>
          <h3>Jersey — Saint-Hélier en découverte courte</h3>
          <p class="activity-name">Centre-ville et front de mer, avec un seul temps fort</p>
          <p><strong>Accès :</strong> vérifier auprès de Condor Ferries qu’un aller-retour Saint-Malo–Jersey le même jour circule réellement du 25 octobre au 1er novembre 2026. Horaires, durée de navigation, heures à terre et disponibilité sont inconnus ici. Le trajet routier Cancale–terminal : aller, retour et cumul sont à vérifier séparément et doivent rester au plus à 2 h de conduite A/R.</p>
          <p><strong>Idée sur place :</strong> choisir une courte boucle dans Saint-Hélier et au port; en cas d’ouverture confirmée, envisager le Jersey Museum ou une autre visite intérieure plutôt qu’un programme dispersé. Vérifier ouverture automnale, tarifs, âge conseillé, durée, accès poussette et sanitaires avant de décider.</p>
          <p><strong>Avec les enfants :</strong> une journée avec route, contrôles, bateau et visite peut être fatigante; prévoir pauses, collation, eau, sieste et retour sans courir. Limiter la marche et les pavés, garder une solution de portage si nécessaire, identifier les toilettes et les espaces de repos. Une activité côtière ne convient que si météo, vent et état du sol le permettent.</p>
          <div class="activity-budget"><strong>Provision partielle : 40–70 €</strong><span>Repas et collations uniquement; traversée et total famille à chiffrer</span><p>Provision hypothétique pour une journée à quatre, pas un tarif local vérifié. Relever un devis daté aller-retour pour les 2 adultes et les enfants de 7 ans et 2 ans; ajouter parking, déplacements locaux et éventuels billets. Les catégories d’âge et le tarif du moins de 3 ans restent à confirmer. Source tarifaire à consulter : <a href="https://www.condorferries.co.uk/" target="_blank" rel="noopener">Condor Ferries</a>.</p></div>
          <p><strong>Avant achat :</strong> confirmer les traversées et marge d’embarquement, conditions de retard/annulation, documents de voyage individuels, stationnement, bagages/poussette, toilettes à bord et sur place, et possibilité de retour anticipé (ne pas la présumer).</p>
          <p><a href="https://www.condorferries.co.uk/" target="_blank" rel="noopener">Condor Ferries</a> · <a href="https://www.gov.je/Travel/Pages/default.aspx" target="_blank" rel="noopener">Gouvernement de Jersey — informations de voyage</a> · <a href="https://www.jerseyheritage.org/" target="_blank" rel="noopener">Jersey Heritage (musées et ouvertures à vérifier)</a></p>
        </article>
        <article class="activity-card">
          <div class="activity-top"><span class="badge">Option à vérifier — conduite probablement hors limite</span><span class="status">Non conforme en l’état</span></div>
          <h3>Chausey — une courte découverte de la Grande Île</h3>
          <p class="activity-name">Nature et bord de mer, uniquement si trajet et bateaux sont compatibles</p>
          <p><strong>Accès :</strong> les traversées partent de Granville; vérifier l’opérateur, l’aller-retour disponible à la date choisie, les horaires publiés et le temps à terre. L’estimation du Scout de 1 h 10–1 h 20 de conduite par sens depuis Cancale (environ 2 h 20–2 h 40 A/R) n’est pas vérifiée, mais dépasse déjà la limite de 2 h si elle est juste. Ne pas retenir cette sortie sans calcul routier fiable montrant un aller-retour inférieur ou égal à 120 minutes; sinon l’écarter de ce séjour.</p>
          <p><strong>Idée sur place :</strong> seulement si les horaires de bateau et la marée permettent une marge sûre, préférer une petite promenade sur la Grande Île plutôt qu’une grande boucle. Les horaires de bateau priment; ne pas s’aventurer sur l’estran ou les sentiers exposés en fonction d’une heure de marée générique.</p>
          <p><strong>Avec les enfants :</strong> chemins potentiellement naturels, humides ou irréguliers; ne pas compter sur la poussette comme équipement unique. Chaussures adhérentes et porte-bébé à envisager. Vérifier avant le départ les toilettes, point d’eau, restauration, abri, possibilités de pause et les conditions de retour. La météo, le vent et la marée peuvent imposer de renoncer; surveiller les enfants près de l’eau et rester sur les chemins autorisés.</p>
          <div class="activity-budget"><strong>Provision partielle : 40–70 €</strong><span>Repas et collations uniquement; bateau et total famille à chiffrer</span><p>Provision hypothétique pour une journée à quatre, pas un tarif local vérifié. Demander le prix bateau aller-retour daté pour les 2 adultes et les enfants de 7 ans et 2 ans; ajouter route et parking. Le tarif du moins de 3 ans, les horaires et les conditions liées aux marées restent inconnus. Source tarifaire à consulter : <a href="https://www.vedettesjoliefrance.com/destinations/granville-les-iles-chausey/visiter-les-iles-chausey/" target="_blank" rel="noopener">Vedettes Jolie France — visiter Chausey</a> (lien fourni par la famille).</p></div>
          <p><strong>Avant achat :</strong> vérifier le temps routier A/R; horaire réel du bateau et temps de présentation au port; horaire de retour; dépendance aux marées; annulations; météo marine; sanitaires et services ouverts; chaussures et portage adaptés.</p>
          <p><a href="https://www.vedettesjoliefrance.com/" target="_blank" rel="noopener">Vedettes Jolie France</a> · <a href="https://www.vedettesdechausey.com/" target="_blank" rel="noopener">Vedettes de Chausey</a> · <a href="https://www.tourisme-granville-terre-mer.com/" target="_blank" rel="noopener">Office de tourisme Granville Terre et Mer</a></p>
        </article>
      </div>
      <div class="panel">
        <h2>Avis des spécialistes — informations et inconnues</h2>
        <ul>
          <li><strong>Scout famille :</strong> Guernesey/Jersey seraient des journées entières si les ferries sont disponibles; fatigue, sieste du plus jeune, marche, poussette, sanitaires et retour peu flexible sont à anticiper. Chausey paraît dépasser le plafond routier selon une estimation non vérifiée.</li>
          <li><strong>Navigateur :</strong> aucun temps de conduite, horaire de bateau ou service aux dates du séjour n’a pu être vérifié. Il faut confirmer séparément conduite A/R, terminal, enregistrement et traversée; aucun parcours ne peut être déclaré conforme pour l’instant.</li>
          <li><strong>Trésorier :</strong> prix non vérifiables en direct; tarif famille, parking, déplacements locaux et billets d’entrée sont inconnus. Ne pas présumer la gratuité pour l’enfant de 2 ans.</li>
          <li><strong>Sentinelle météo :</strong> aucune prévision ou marée opérationnelle vérifiée. Recontrôler les prévisions et alertes opérateur à J−3/J−2 puis le jour même; pour Chausey, respecter le programme du bateau et les marées. Renoncer si mer, vent ou fatigue posent problème.</li>
        </ul>
        <p class="muted"><strong>Recommandation :</strong> vérifier d’abord Jersey ou Guernesey, une seule destination, uniquement si une traversée aller-retour datée est disponible, les documents sont conformes et la route vers Saint-Malo respecte bien 2 h A/R. Chausey vient après le contrôle de conduite et paraît exclue au vu de l’estimation actuelle. Il ne reste que peu de temps avant les dates du séjour : ne bâtir aucun programme sur des horaires ou prix non publiés/confirmés.</p>
      </div>
    """


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
    budget_posts = voyage.get("budget", {}).get("postes", [])
    special_program = render_rennes_route_rhum(steps, budget_posts)
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
    .activity-budget {{ margin:12px 0; padding:10px 12px; border-left:3px solid var(--green);
      border-radius:7px; background:#132a29; }}
    .activity-budget strong,.activity-budget span {{ display:block; }}
    .activity-budget span,.activity-budget p {{ color:var(--muted); font-size:12px; }}
    .activity-budget p {{ margin:5px 0 0; }}
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
      <div class="stat"><strong>{len(steps)}</strong><span>sorties et options à planifier ou confirmer</span></div>
      <div class="stat"><strong>{escape(family.get('total', 0))}</strong><span>{escape(family_summary)}</span></div>
      <div class="stat"><strong>{budget_envelope}</strong><span>enveloppe sur place · logement et trajet vers Cancale exclus</span></div>
      <div class="stat"><strong>{format_duration(MAX_DRIVE_MINUTES)} A/R</strong><span>maximum de conduite visé par sortie</span></div>
    </section>

    <nav class="tabs" aria-label="Sections du dashboard">
      <button class="tab-button active" data-tab="itinerary">Séjour</button>
      <button class="tab-button" data-tab="rennes-rhum">Rennes & Route du Rhum</button>
      <button class="tab-button" data-tab="iles">Guernesey, Jersey & Chausey</button>
      <button class="tab-button" data-tab="map">Carte & destinations</button>
      <button class="tab-button" data-tab="budget">Budget</button>
      <button class="tab-button" data-tab="checklists">Checklists</button>
    </nav>

    <section class="tab-panel active" id="itinerary">
      <div class="grid">
        <div class="panel"><h2>Sorties et options</h2>
          <p class="muted">Les idées Route du Rhum sont conditionnelles : date, accès, horaires, tarifs et restrictions restent à confirmer. Aucune réservation n’est déduite. Les temps de trajet sont des estimations à vérifier le jour du déplacement.</p>
          <div class="activity-list">{render_steps(steps, budget_posts)}</div>
        </div>
        <div class="stack">
          <section class="panel"><h2>Hébergement fixe</h2>{render_accommodations(data.get('hebergements', []))}</section>
          <section class="panel"><h2>Plans B</h2>{plan_b_content}</section>
        </div>
      </div>
    </section>

    <section class="tab-panel" id="rennes-rhum">
      <div class="stack">
        {special_program}
      </div>
    </section>

    <section class="tab-panel" id="iles">
      <div class="stack">
        {render_island_options()}
      </div>
    </section>

    <section class="tab-panel" id="map">
      <div class="panel"><h2>Carte de la zone</h2>
        <p class="muted">La carte ci-dessous affiche les points d’intérêt du séjour, dont Guernesey, Jersey, Chausey et les secteurs Route du Rhum. Les marqueurs des îles, ports et sites événementiels sont des repères géographiques approximatifs; ils ne confirment ni terminal exact, ni accès autorisé, ni réservation. Le point de Cancale situe la commune, pas l'adresse de l'hébergement. Le fond cartographique Esri nécessite une connexion Internet.</p>
        <iframe class="map-frame" title="Carte des points d’intérêt du séjour" loading="lazy"
          src="carte_cancale.html"></iframe>
        <h3>Destinations sélectionnées</h3>{render_map_links(steps)}
        <p class="muted">Les liens de destination sont des repères, pas des confirmations de traversée ou d’accès. Les points d’embarquement doivent être vérifiés auprès des opérateurs.</p>
      </div>
    </section>

    <section class="tab-panel" id="budget">
      <div class="panel"><h2>Budget sur place</h2>
        <div class="budget-summary"><strong>Enveloppe cible : {budget_envelope}</strong><br>
          <span>Ce montant est une cible, pas un total engagé ou dépensé. Hébergement et trajet jusqu’à Cancale exclus.</span></div>
        <table><thead><tr><th>Poste / activité</th><th>Prix / provision famille</th><th>Statut</th><th>Détails</th></tr></thead>
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
