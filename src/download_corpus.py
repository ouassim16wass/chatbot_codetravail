import re
import tarfile
import urllib.request
from pathlib import Path

SERVEUR = "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"
ARCHIVE_URL = SERVEUR + "Freemium_legi_global_20250713-140000.tar.gz"
DATE_CORPUS = "2025-07-13"

CODE_TRAVAIL_ID = "LEGITEXT000006072050"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
ETAT = RAW_DIR / "derniere_synchro.txt"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    scannes = 0
    extraits = 0
    requete = urllib.request.Request(
        ARCHIVE_URL, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(requete, timeout=120) as flux:
        with tarfile.open(fileobj=flux, mode="r|gz") as archive:
            for membre in archive:
                scannes += 1
                if scannes % 100000 == 0:
                    print(f"{scannes} fichiers scannes, {extraits} extraits")
                if CODE_TRAVAIL_ID in membre.name and membre.isfile():
                    archive.extract(membre, path=RAW_DIR)
                    extraits += 1
    ETAT.write_text(re.search(r"(\d{8}-\d{6})", ARCHIVE_URL).group(1))
    print(f"Termine : {extraits} fichiers du Code du travail dans {RAW_DIR}")


if __name__ == "__main__":
    main()
