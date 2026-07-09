import json

from src.config import BASE_DIR
from src.vector_db import load_database

SORTIE = BASE_DIR / "webapp" / "site" / "data" / "base.json"


def main():
    collection, _ = load_database()
    tout = collection.get(include=["documents", "metadatas", "embeddings"])
    elements = []
    for identifiant, document, metadonnees, vecteur in zip(
        tout["ids"], tout["documents"], tout["metadatas"], tout["embeddings"]
    ):
        elements.append({
            "id": identifiant,
            "numero": metadonnees["numero"],
            "texte": document,
            "vecteur": [round(float(v), 4) for v in vecteur],
        })
    donnees = {
        "date_corpus": collection.metadata["date_corpus"],
        "modele": collection.metadata["embedding_model"],
        "elements": elements,
    }
    SORTIE.parent.mkdir(parents=True, exist_ok=True)
    SORTIE.write_text(json.dumps(donnees, ensure_ascii=False), encoding="utf-8")
    print(f"{len(elements)} chunks exportes vers {SORTIE}")


if __name__ == "__main__":
    main()
