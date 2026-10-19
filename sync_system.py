"""Regenerate the Cancale map and printable booklet from confirmed JSON data."""

import argparse
import json
from pathlib import Path

from generate_map import generate_map
from generate_dashboard import generate_dashboard
from generate_print import generate_print


ROOT_DIR = Path(__file__).resolve().parent
DATA_FILE = ROOT_DIR / "vacances_data.json"
MAP_FILE = ROOT_DIR / "carte_cancale.html"
BOOKLET_FILE = ROOT_DIR / "carnet_cancale.html"


def load_data(data_file=DATA_FILE):
    with open(data_file, "r", encoding="utf-8-sig") as source:
        return json.load(source)


def sync(data_file=DATA_FILE, map_file=MAP_FILE, booklet_file=BOOKLET_FILE, dashboard_file=None):
    data = load_data(data_file)
    generated_map = generate_map(data, map_file)
    generated_booklet = generate_print(data, booklet_file)
    generated_dashboard = generate_dashboard(data, dashboard_file or ROOT_DIR / "dashboard.html")
    return generated_map, generated_booklet, generated_dashboard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_FILE, help="JSON du séjour")
    parser.add_argument("--map-output", type=Path, default=MAP_FILE, help="Carte HTML générée")
    parser.add_argument("--booklet-output", type=Path, default=BOOKLET_FILE, help="Carnet HTML généré")
    parser.add_argument("--dashboard-output", type=Path, default=ROOT_DIR / "dashboard.html", help="Dashboard HTML généré")
    args = parser.parse_args()

    generated_map, generated_booklet, generated_dashboard = sync(
        args.data, args.map_output, args.booklet_output, args.dashboard_output
    )
    print(f"Carte générée : {generated_map}")
    print(f"Carnet généré : {generated_booklet}")
    print(f"Dashboard généré : {generated_dashboard}")


if __name__ == "__main__":
    main()
