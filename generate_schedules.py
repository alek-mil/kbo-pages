"""
generate_schedules.py
Automatski čita sve .html fajlove iz games/ foldera
i generiše schedules.html grupisan po datumu.

Pokretanje:
    python generate_schedules.py
"""

import os
import re
from pathlib import Path
from datetime import datetime
from collections import defaultdict

GAMES_DIR = Path("games")
OUTPUT_FILE = Path("schedules.html")

# Mapiranje stadiona po timu (gost određuje stadion)
VENUES = {
    "Busan-Sajik": ["Lotte"],
    "Changwon-Masan": ["NC"],
    "Changwon": ["NC"],
    "Gwangju": ["Kia"],
    "Daejeon": ["Hanwha"],
    "Icheon": ["Doosan"],
    "Suwon": ["KT"],
    "Incheon-Munhak": ["SSG"],
    "Jamsil": ["LG", "Doosan"],
    "Gocheok": ["Kiwoom"],
    "Daegu": ["Samsung"],
}

def get_venue(home_team):
    for venue, teams in VENUES.items():
        for t in teams:
            if t.lower() in home_team.lower():
                return venue
    return ""

def parse_filename(filename):
    """
    Parsira filename kao:
    TeamA-vs-TeamB-YYYYMMDD.html
    Vraća (date, team_a, team_b, venue)
    """
    name = filename.replace(".html", "")
    # Izvuci datum (zadnjih 8 cifara)
    date_match = re.search(r"-(\d{8})$", name)
    if not date_match:
        return None
    date_str = date_match.group(1)
    try:
        date = datetime.strptime(date_str, "%Y%m%d")
    except ValueError:
        return None

    # Izvuci timove
    teams_part = name[:date_match.start()]
    vs_match = re.search(r"-vs-", teams_part, re.IGNORECASE)
    if not vs_match:
        return None

    team_a = teams_part[:vs_match.start()].replace("-", " ").strip()
    team_b = teams_part[vs_match.end():].replace("-", " ").strip()
    venue = get_venue(team_b)  # domaći tim je drugi (home)

    return date, team_a, team_b, venue


def generate():
    if not GAMES_DIR.exists():
        print(f"❌ Folder '{GAMES_DIR}' ne postoji. Pokreni skriptu iz kbo-pages/ foldera.")
        return

    html_files = sorted(GAMES_DIR.glob("*.html"))
    if not html_files:
        print("❌ Nema HTML fajlova u games/ folderu.")
        return

    # Grupiši po datumu
    by_date = defaultdict(list)
    skipped = []

    for f in html_files:
        result = parse_filename(f.name)
        if result:
            date, team_a, team_b, venue = result
            by_date[date].append((team_a, team_b, venue, f.name))
        else:
            skipped.append(f.name)

    if skipped:
        print(f"⚠️  Preskočeni fajlovi (ne odgovaraju formatu): {skipped}")

    # Generiši HTML
    day_blocks = ""
    for date in sorted(by_date.keys()):
        formatted = date.strftime("%B %d, %Y")
        games_html = ""
        for team_a, team_b, venue, fname in by_date[date]:
            games_html += f"""
      <li><a href="games/{fname}">
        <span class="teams">{team_a} vs. {team_b}</span>
        <span class="venue">{venue} <span class="arrow">▶</span></span>
      </a></li>"""

        day_blocks += f"""
  <div class="day-block">
    <div class="day-header">📅 {formatted}</div>
    <ul class="game-list">{games_html}
    </ul>
  </div>
"""

    total = sum(len(v) for v in by_date.values())
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>KBO Schedule</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f1117; color: #e0e0e0; padding: 32px 16px; }}
    h1 {{ text-align: center; font-size: 1.8rem; color: #ffffff; margin-bottom: 8px; letter-spacing: 1px; }}
    .subtitle {{ text-align: center; color: #888; font-size: 0.9rem; margin-bottom: 40px; }}
    .day-block {{ max-width: 700px; margin: 0 auto 32px auto; }}
    .day-header {{ background: #1e2130; border-left: 4px solid #e63946; padding: 10px 16px; font-size: 1rem; font-weight: 700; color: #ffffff; border-radius: 4px 4px 0 0; }}
    .game-list {{ list-style: none; }}
    .game-list li {{ border-bottom: 1px solid #1e2130; }}
    .game-list li:last-child {{ border-bottom: none; border-radius: 0 0 4px 4px; overflow: hidden; }}
    .game-list a {{ display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #161a26; color: #c9d1e0; text-decoration: none; font-size: 0.95rem; transition: background 0.15s; }}
    .game-list a:hover {{ background: #1f2537; color: #ffffff; }}
    .teams {{ font-weight: 600; color: #ffffff; }}
    .venue {{ font-size: 0.8rem; color: #666; text-align: right; }}
    .arrow {{ color: #e63946; margin-left: 12px; font-size: 0.8rem; }}
  </style>
</head>
<body>
  <h1>⚾ KBO Schedule</h1>
  <p class="subtitle">Ukupno {total} utakmica — klikni za statistiku</p>
{day_blocks}
</body>
</html>"""

    OUTPUT_FILE.write_text(html, encoding="utf-8")
    print(f"✅ Generisan schedules.html — {total} utakmica, {len(by_date)} dana")


if __name__ == "__main__":
    generate()
