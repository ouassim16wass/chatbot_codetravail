import json

from src.chunking import make_chunks
from src.config import DATA_DIR
from src.vector_db import update_database


def main():
    corpus = json.loads((DATA_DIR / "corpus.json").read_text(encoding="utf-8"))
    chunks = make_chunks(corpus["documents"])
    print(f"{corpus['nb_documents']} articles -> {len(chunks)} chunks")
    bilan = update_database(chunks, corpus["date_corpus"])
    print(
        f"Encodes (nouveaux ou modifies) : {bilan['encodes']} | "
        f"inchanges : {bilan['inchanges']} | supprimes : {bilan['supprimes']}"
    )
    print(f"Base : {bilan['total']} chunks (corpus du {corpus['date_corpus']})")


if __name__ == "__main__":
    main()
