"""Gestion de la base vectorielle : creation, persistance et rechargement.

La base ChromaDB est sauvegardee sur disque (dossier chroma_db/) avec, dans
ses metadonnees, le nom du modele d'embedding et la date du corpus. Au
redemarrage, load_database() recharge l'existant sans jamais reindexer.
"""

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import DB_DIR, EMBEDDING_MODEL

NOM_COLLECTION = "code_travail"


def build_database(chunks, date_corpus):
    """Encode tous les chunks et les persiste dans une base neuve.
    A n'executer que via index.py : c'est la seule etape couteuse."""
    client = chromadb.PersistentClient(path=str(DB_DIR))
    try:
        client.delete_collection(NOM_COLLECTION)
    except Exception:
        pass  # aucune base existante, rien a supprimer
    collection = client.create_collection(
        NOM_COLLECTION,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": EMBEDDING_MODEL,
            "date_corpus": date_corpus,
        },
    )

    modele = SentenceTransformer(EMBEDDING_MODEL)
    textes = [c["texte"] for c in chunks]
    embeddings = modele.encode(textes, show_progress_bar=True)

    collection.add(
        ids=[c["id"] for c in chunks],
        embeddings=embeddings.tolist(),
        documents=textes,
        metadatas=[c["metadonnees"] for c in chunks],
    )
    return collection


def load_database():
    """Recharge la base persistee sans reindexer (contrainte du sujet).
    Retourne la collection et le modele d'embedding, dont le nom est lu
    dans les metadonnees de la base pour garantir la coherence."""
    client = chromadb.PersistentClient(path=str(DB_DIR))
    collection = client.get_collection(NOM_COLLECTION)
    nom_modele = collection.metadata["embedding_model"]
    return collection, SentenceTransformer(nom_modele)


def search(collection, modele, question, k=5):
    """Retourne les k chunks les plus proches de la question, avec leurs
    metadonnees et un score de similarite entre 0 et 1."""
    vecteur = modele.encode([question])
    resultats = collection.query(
        query_embeddings=vecteur.tolist(), n_results=k
    )
    return [
        {
            "texte": document,
            "metadonnees": metadonnees,
            "score": 1 - distance,  # distance cosinus -> similarite
        }
        for document, metadonnees, distance in zip(
            resultats["documents"][0],
            resultats["metadatas"][0],
            resultats["distances"][0],
        )
    ]
