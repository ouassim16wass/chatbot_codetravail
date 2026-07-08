"""Gestion de la base vectorielle : creation, persistance et rechargement."""


def build_database(documents):
    """Construit la base vectorielle a partir des documents et la persiste
    sur disque avec leurs metadonnees (numero d'article, section, source)."""
    # TODO: encoder les chunks avec le modele d'embedding et les stocker
    # dans ChromaDB, en tracant le nom du modele utilise
    raise NotImplementedError


def load_database():
    """Recharge la base vectorielle existante sans reindexer."""
    # TODO: ouvrir la collection persistee et verifier le modele d'embedding
    raise NotImplementedError


def search(query, k=5):
    """Recherche les k chunks les plus proches de la question."""
    # TODO: encoder la question et interroger la collection
    raise NotImplementedError
