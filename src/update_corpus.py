import json
import re
import tarfile
import urllib.request

from src.chunking import make_chunks
from src.config import DATA_DIR
from src.download_corpus import CODE_TRAVAIL_ID, ETAT, RAW_DIR, SERVEUR
from src.extract_corpus import main as extraire
from src.vector_db import update_database


def archives_disponibles():
    requete = urllib.request.Request(SERVEUR, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(requete, timeout=60) as reponse:
        page = reponse.read().decode("utf-8", errors="replace")
    return sorted(set(re.findall(r"LEGI_(\d{8}-\d{6})\.tar\.gz", page)))


def appliquer(horodatage):
    url = f"{SERVEUR}LEGI_{horodatage}.tar.gz"
    requete = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    fichiers = 0
    with urllib.request.urlopen(requete, timeout=300) as flux:
        with tarfile.open(fileobj=flux, mode="r|gz") as archive:
            for membre in archive:
                if not membre.isfile() or CODE_TRAVAIL_ID not in membre.name:
                    continue
                position = membre.name.find("legi/")
                if position < 0:
                    continue
                cible = RAW_DIR / membre.name[position:]
                cible.parent.mkdir(parents=True, exist_ok=True)
                cible.write_bytes(archive.extractfile(membre).read())
                fichiers += 1
    return fichiers


def main():
    depuis = ETAT.read_text().strip()
    archives = [h for h in archives_disponibles() if h > depuis]
    print(f"{len(archives)} archives incrementales a appliquer (etat : {depuis})")
    total = 0
    for horodatage in archives:
        fichiers = appliquer(horodatage)
        ETAT.write_text(horodatage)
        total += fichiers
        if fichiers:
            print(f"  {horodatage} : {fichiers} fichiers", flush=True)
    print(f"{total} fichiers du Code du travail mis a jour")

    extraire()

    corpus = json.loads((DATA_DIR / "corpus.json").read_text(encoding="utf-8"))
    chunks = make_chunks(corpus["documents"])
    bilan = update_database(chunks, corpus["date_corpus"])
    print(
        f"Indexation : {bilan['encodes']} encodes, {bilan['inchanges']} inchanges, "
        f"{bilan['supprimes']} supprimes | base : {bilan['total']} chunks "
        f"(corpus du {corpus['date_corpus']})"
    )


if __name__ == "__main__":
    main()
