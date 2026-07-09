import hashlib

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import DB_DIR, EMBEDDING_MODEL

NOM_COLLECTION = "code_travail"


def empreinte(texte):
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def update_database(chunks, date_corpus):
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_or_create_collection(
        NOM_COLLECTION,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": EMBEDDING_MODEL,
            "date_corpus": date_corpus,
        },
    )

    existants = collection.get(include=["metadatas"])
    anciens = dict(zip(existants["ids"], existants["metadatas"]))

    ids_corpus = set()
    a_encoder = []
    for chunk in chunks:
        chunk["metadonnees"]["empreinte"] = empreinte(chunk["texte"])
        ids_corpus.add(chunk["id"])
        ancien = anciens.get(chunk["id"])
        if ancien is None or ancien.get("empreinte") != chunk["metadonnees"]["empreinte"]:
            a_encoder.append(chunk)

    a_supprimer = sorted(set(anciens) - ids_corpus)

    if a_encoder:
        modele = SentenceTransformer(EMBEDDING_MODEL)
        embeddings = modele.encode(
            [c["texte"] for c in a_encoder], show_progress_bar=True
        )
        collection.upsert(
            ids=[c["id"] for c in a_encoder],
            embeddings=embeddings.tolist(),
            documents=[c["texte"] for c in a_encoder],
            metadatas=[c["metadonnees"] for c in a_encoder],
        )
    if a_supprimer:
        collection.delete(ids=a_supprimer)

    metadonnees = {
        cle: valeur
        for cle, valeur in collection.metadata.items()
        if not cle.startswith("hnsw:")
    }
    metadonnees["embedding_model"] = EMBEDDING_MODEL
    metadonnees["date_corpus"] = date_corpus
    collection.modify(metadata=metadonnees)

    return {
        "encodes": len(a_encoder),
        "inchanges": len(ids_corpus) - len(a_encoder),
        "supprimes": len(a_supprimer),
        "total": collection.count(),
    }


def load_database():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(NOM_COLLECTION)
    nom_modele = collection.metadata["embedding_model"]
    return collection, SentenceTransformer(nom_modele)


def search(collection, modele, question, k=5):
    vecteur = modele.encode([question])
    resultats = collection.query(
        query_embeddings=vecteur.tolist(), n_results=k * 3
    )
    articles = []
    numeros_vus = set()
    for document, metadonnees, distance in zip(
        resultats["documents"][0],
        resultats["metadatas"][0],
        resultats["distances"][0],
    ):
        numero = metadonnees["numero"]
        if numero in numeros_vus:
            continue
        numeros_vus.add(numero)
        articles.append({
            "texte": document,
            "metadonnees": metadonnees,
            "score": 1 - distance,
        })
        if len(articles) == k:
            break
    return articles
