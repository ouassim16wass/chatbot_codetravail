"""Decoupage du corpus en chunks (strategie de la question 1 du README).

Un chunk par article, dont le texte a embedder est prefixe du theme et du
numero d'article ("Duree du travail - Article L3121-27 : ..."). Les rares
articles tres longs sont decoupes en plusieurs parties, a la frontiere des
phrases, et chaque partie garde le prefixe complet.
"""

import re

# Au-dela de cette taille (en caracteres), un article est decoupe :
# un chunk trop long donne un embedding dilue et noie le contexte du LLM
TAILLE_MAX = 1500


def decouper_texte(texte):
    """Decoupe un texte long en morceaux d'au plus TAILLE_MAX caracteres,
    sans jamais couper au milieu d'une phrase."""
    phrases = re.split(r"(?<=[.;:]) ", texte)
    morceaux = []
    courant = ""
    for phrase in phrases:
        if courant and len(courant) + len(phrase) + 1 > TAILLE_MAX:
            morceaux.append(courant)
            courant = phrase
        else:
            courant = f"{courant} {phrase}".strip()
    if courant:
        morceaux.append(courant)
    return morceaux


def make_chunks(documents):
    """Transforme les documents du corpus en chunks prets a indexer.

    Chaque chunk porte un identifiant unique, le texte a embedder et ses
    metadonnees (numero d'article, theme, section, date d'entree en
    vigueur) qui serviront a l'affichage fiable des sources.
    """
    chunks = []
    for doc in documents:
        prefixe = f"{doc['theme']} - Article {doc['numero']} : "
        morceaux = decouper_texte(doc["texte"])
        for i, morceau in enumerate(morceaux, start=1):
            # id unique : "L3121-27" ou "L1233-58#2" pour une 2e partie
            suffixe = f"#{i}" if len(morceaux) > 1 else ""
            chunks.append({
                "id": doc["numero"] + suffixe,
                "texte": prefixe + morceau,
                "metadonnees": {
                    "numero": doc["numero"],
                    "theme": doc["theme"],
                    "section": doc["section"],
                    "date_debut": doc["date_debut"],
                },
            })
    return chunks
