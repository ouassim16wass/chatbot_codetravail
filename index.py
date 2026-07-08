import json

from src.chunking import make_chunks
from src.config import DATA_DIR
from src.vector_db import build_database


def main():
    corpus = json.loads(
        (DATA_DIR / "corpus.json").read_text(encoding="utf-8")
    )
    chunks = make_chunks(corpus["documents"])
    print(f"{corpus['nb_documents']} articles -> {len(chunks)} chunks")

    collection = build_database(chunks, corpus["date_corpus"])
    print(f"Base persistee : {collection.count()} chunks indexes")

    apercu = collection.get(limit=3, include=["documents", "metadatas"])
    for texte, meta in zip(apercu["documents"], apercu["metadatas"]):
        print(f"\n[{meta['numero']}] ({meta['theme']}) {meta['section']}")
        print(f"  {texte[:200]}")


if __name__ == "__main__":
    main()
