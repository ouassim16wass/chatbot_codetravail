"""Telechargement des donnees brutes du Code du travail (option B du sujet).

L'archive LEGI de la DILA (~1,1 Go) contient tous les codes francais au
format XML. Elle est lue en flux, sans etre stockee : seuls les fichiers
du Code du travail (identifiant LEGITEXT000006072050) sont ecrits sur
disque, dans data/raw/.
"""

import tarfile
import urllib.request
from pathlib import Path

# Archive globale publiee par la DILA sur echanges.dila.gouv.fr
ARCHIVE_URL = (
    "https://echanges.dila.gouv.fr/OPENDATA/LEGI/"
    "Freemium_legi_global_20250713-140000.tar.gz"
)
# Date de la photo du droit contenue dans l'archive (pour la question 3)
DATE_CORPUS = "2025-07-13"

CODE_TRAVAIL_ID = "LEGITEXT000006072050"

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    scannes = 0
    extraits = 0
    requete = urllib.request.Request(
        ARCHIVE_URL, headers={"User-Agent": "Mozilla/5.0"}
    )
    with urllib.request.urlopen(requete, timeout=120) as flux:
        # mode "r|gz" : lecture en flux, l'archive n'est jamais stockee entiere
        with tarfile.open(fileobj=flux, mode="r|gz") as archive:
            for membre in archive:
                scannes += 1
                if scannes % 100000 == 0:
                    print(f"{scannes} fichiers scannes, {extraits} extraits")
                if CODE_TRAVAIL_ID in membre.name and membre.isfile():
                    archive.extract(membre, path=RAW_DIR)
                    extraits += 1
    print(f"Termine : {extraits} fichiers du Code du travail dans {RAW_DIR}")


if __name__ == "__main__":
    main()
