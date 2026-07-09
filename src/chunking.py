import re

TAILLE_MAX = 1500


def decouper_texte(texte):
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
    chunks = []
    for doc in documents:
        prefixe = f"{doc['theme']} - Article {doc['numero']} : "
        morceaux = decouper_texte(doc["texte"])
        for i, morceau in enumerate(morceaux, start=1):
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
