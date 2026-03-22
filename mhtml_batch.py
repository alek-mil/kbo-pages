"""
mhtml_batch.py
Konvertuje sve .mhtml fajlove iz new_mhtml/ foldera u HTML
i stavlja ih u games/ folder.

Pokretanje:
    python mhtml_batch.py

Struktura:
    kbo-pages/
        mhtml_batch.py
        new_mhtml/       <-- ovdje staviš nove .mhtml fajlove
        games/           <-- ovdje se pojavljuju konvertovani .html fajlovi
        schedules.html
"""

import email
import base64
import re
from pathlib import Path
from datetime import datetime

INPUT_DIR  = Path("new_mhtml")
OUTPUT_DIR = Path("games")

TEAM_MAP = {
    "kia":     "Kia-Tigers",
    "hanwha":  "Hanwha-Eagles",
    "lg":      "LG-Twins",
    "ssg":     "SSG-Landers",
    "kt":      "KT-Wiz",
    "lotte":   "Lotte-Giants",
    "samsung": "Samsung-Lions",
    "doosan":  "Doosan-Bears",
    "kiwoom":  "Kiwoom-Heroes",
    "nc":      "NC-Dinos",
}

def slugify(filename: str) -> str:
    """
    Pretvara naziv MHTML fajla u čist slug.
    Npr:
    'Kia Tigers vs. Hanwha Eagles - March 19, 2026 1_00_pm KST at Daejeon _ MyKBO Stats.mhtml'
    -> 'Kia-Tigers-vs-Hanwha-Eagles-20260319'
    """
    name = filename.replace(".mhtml", "")

    # Izvuci timove i datum
    match = re.match(r"^(.+?)\s+-\s+(\w+ \d+,\s*\d{4})", name)
    if match:
        teams_raw = match.group(1).strip()
        date_raw  = match.group(2).strip()

        # Pretvori datum
        try:
            dt = datetime.strptime(date_raw, "%B %d, %Y")
            date_str = dt.strftime("%Y%m%d")
        except ValueError:
            date_str = re.sub(r"[^0-9]", "", date_raw)

        # Očisti timove: "Kia Tigers vs. Hanwha Eagles" -> "Kia-Tigers-vs-Hanwha-Eagles"
        teams_clean = re.sub(r"\s+vs\.?\s+", " vs ", teams_raw, flags=re.IGNORECASE)
        teams_slug  = re.sub(r"[^a-zA-Z0-9 ]", "", teams_clean).strip()
        teams_slug  = re.sub(r"\s+", "-", teams_slug)

        return f"{teams_slug}-{date_str}"

    # Fallback: generički slug
    clean = re.sub(r"[^a-zA-Z0-9]", "-", name)
    clean = re.sub(r"-+", "-", clean).strip("-")
    return clean[:80]


def convert(mhtml_path: Path, out_path: Path) -> bool:
    try:
        with open(mhtml_path, "rb") as f:
            msg = email.message_from_bytes(f.read())

        parts = {}
        html_content = None

        for part in msg.walk():
            ct      = part.get_content_type()
            cid     = part.get("Content-ID", "").strip("<>")
            loc     = part.get("Content-Location", "")
            payload = part.get_payload(decode=True)

            if payload is None:
                continue

            if ct == "text/html" and html_content is None:
                html_content = payload.decode("utf-8", errors="replace")

            elif ct == "text/css":
                css = payload.decode("utf-8", errors="replace")
                if cid: parts[f"cid:{cid}"] = ("text/css", css)
                if loc:  parts[loc]          = ("text/css", css)

            elif ct.startswith("image/"):
                uri = f"data:{ct};base64,{base64.b64encode(payload).decode()}"
                if cid: parts[f"cid:{cid}"] = (ct, uri)
                if loc:  parts[loc]          = (ct, uri)

        if html_content is None:
            return False

        # Inline CSS
        def replace_css(m):
            href = m.group(1)
            if href in parts and parts[href][0] == "text/css":
                return f"<style>{parts[href][1]}</style>"
            return m.group(0)

        html_content = re.sub(r'<link[^>]+href="([^"]+)"[^>]*>', replace_css, html_content)

        # Inline slike
        def replace_src(m):
            src = m.group(1)
            return f'src="{parts[src][1]}"' if src in parts else m.group(0)

        html_content = re.sub(r'src="(cid:[^"]+)"', replace_src, html_content)

        out_path.write_text(html_content, encoding="utf-8")
        return True

    except Exception as e:
        print(f"   ⚠️  Greška: {e}")
        return False


def main():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    mhtml_files = list(INPUT_DIR.glob("*.mhtml"))

    if not mhtml_files:
        print(f"⚠️  Nema .mhtml fajlova u '{INPUT_DIR}/' folderu.")
        return

    print(f"📂 Pronađeno {len(mhtml_files)} fajlova u '{INPUT_DIR}/'")
    print("-" * 50)

    ok = 0
    fail = 0

    for mhtml_path in sorted(mhtml_files):
        slug     = slugify(mhtml_path.name)
        out_path = OUTPUT_DIR / f"{slug}.html"

        if out_path.exists():
            print(f"⏭️  Već postoji: {slug}.html")
            continue

        print(f"⬇️  Konvertujem: {mhtml_path.name}")
        print(f"   → {out_path}")

        if convert(mhtml_path, out_path):
            size = out_path.stat().st_size // 1024
            print(f"   ✅ OK ({size} KB)")
            ok += 1
        else:
            print(f"   ❌ Neuspješno")
            fail += 1

    print("-" * 50)
    print(f"✅ Konvertovano: {ok}  |  ❌ Greška: {fail}  |  ⏭️  Preskočeno: {len(mhtml_files) - ok - fail}")
    if ok > 0:
        print(f"\n➡️  Sada pokreni:")
        print(f"   python generate_schedules.py")
        print(f"   git add .")
        print(f'   git commit -m "nove utakmice"')
        print(f"   git push")


if __name__ == "__main__":
    main()
