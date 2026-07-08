"""Extraction du corpus depuis les fichiers XML LEGI (jalon 1).

Parcourt les fichiers XML d'articles du Code du travail, ne garde que les
versions en vigueur appartenant aux themes du sujet, nettoie le texte et
produit data/corpus.json : une liste homogene de documents avec identifiant,
texte et metadonnees (numero d'article, theme, section, source).
"""

import json
import random
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from download_corpus import DATE_CORPUS

BASE_DIR = Path(__file__).resolve().parent.parent
ARTICLES_DIR = (
    BASE_DIR / "data" / "raw" / "legi" / "global" / "code_et_TNC_en_vigueur"
    / "code_en_vigueur" / "LEGI" / "TEXT" / "00" / "00" / "06" / "07" / "20"
    / "LEGITEXT000006072050" / "article"
)
SORTIE = BASE_DIR / "data" / "corpus.json"

# Themes du sujet : (nom, premier article, dernier article).
# Un numero comme "L1237-14" est compare sous la forme (1237, 14).
# L'ordre est important : la rupture conventionnelle (L1237-11 a 19) est
# incluse dans la plage du licenciement, elle-meme incluse dans celle du
# contrat de travail ; on teste donc du plus specifique au plus large.
THEMES = [
    ("Rupture conventionnelle", (1237, 11), (1237, 19)),
    ("Licenciement", (1231, 1), (1237, 20)),
    ("Contrat de travail (CDI, CDD)", (1221, 1), (1248, 11)),
    ("Harcelement et discrimination", (1152, 1), (1155, 2)),
    ("Representation du personnel", (2311, 1), (2316, 26)),
    ("Duree du travail et heures supplementaires", (3121, 1), (3121, 36)),
    ("Conges payes", (3141, 1), (3141, 32)),
    ("Salaire minimum (SMIC)", (3231, 1), (3232, 9)),
]


def cle_numero(numero):
    """Transforme "L1237-14" en (1237, 14) pour comparer des plages.
    Retourne None si le numero n'a pas cette forme (annexes, tables...)."""
    m = re.match(r"^L(\d+)-(\d+)", numero)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)))


def theme_de(numero):
    """Retourne le theme du sujet auquel appartient l'article, sinon None."""
    cle = cle_numero(numero)
    if cle is None:
        return None
    for nom, debut, fin in THEMES:
        if debut <= cle <= fin:
            return nom
    return None


def nettoyer(texte):
    """Supprime les espaces multiples et les restes de mise en forme."""
    return re.sub(r"\s+", " ", texte).strip()


def lire_article(chemin):
    """Lit un fichier XML d'article. Retourne un document (dict) si l'article
    est en vigueur et appartient a un theme retenu, sinon None."""
    racine = ET.parse(chemin).getroot()

    etat = racine.findtext(".//META_ARTICLE/ETAT")
    if etat != "VIGUEUR":
        return None

    numero = (racine.findtext(".//META_ARTICLE/NUM") or "").strip()
    theme = theme_de(numero)
    if theme is None:
        return None

    # Texte de l'article : itertext() recupere le texte en ignorant les
    # balises de mise en forme (<p>, <br/>) heritees de Legifrance
    contenu = racine.find(".//BLOC_TEXTUEL/CONTENU")
    if contenu is None:
        return None
    texte = nettoyer(" ".join(contenu.itertext()))
    if not texte:
        return None

    # Section de rattachement : les titres dont la date de fin est 2999
    # sont ceux actuellement en vigueur ; le dernier est le plus precis
    titres = [
        nettoyer(t.text or "")
        for t in racine.iter("TITRE_TM")
        if t.get("fin") == "2999-01-01"
    ]
    section = titres[-1] if titres else ""

    return {
        "id": racine.findtext(".//META_COMMUN/ID"),
        "numero": numero,
        "theme": theme,
        "section": section,
        "date_debut": racine.findtext(".//META_ARTICLE/DATE_DEBUT"),
        "texte": texte,
    }


def main():
    documents = {}
    for chemin in ARTICLES_DIR.rglob("*.xml"):
        doc = lire_article(chemin)
        if doc is None:
            continue
        # Securite : si deux versions d'un meme article se disent en vigueur,
        # on garde la plus recente
        existant = documents.get(doc["numero"])
        if existant is None or doc["date_debut"] > existant["date_debut"]:
            documents[doc["numero"]] = doc

    docs = sorted(documents.values(), key=lambda d: cle_numero(d["numero"]))

    corpus = {
        "source": "Code du travail - base LEGI (DILA / data.gouv.fr)",
        "date_corpus": DATE_CORPUS,
        "nb_documents": len(docs),
        "documents": docs,
    }
    SORTIE.write_text(
        json.dumps(corpus, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    # Bilan par theme : le sujet exige au moins 5 themes couverts
    print(f"{len(docs)} articles en vigueur extraits vers {SORTIE.name}\n")
    for nom, _, _ in THEMES:
        n = sum(1 for d in docs if d["theme"] == nom)
        print(f"  {nom} : {n} articles")

    # Controle qualite du jalon 1 : relire dix documents au hasard
    print("\n--- Dix documents au hasard, a relire ---")
    for doc in random.sample(docs, min(10, len(docs))):
        print(f"\n[{doc['numero']}] ({doc['theme']}) {doc['section']}")
        print(f"  {doc['texte'][:200]}")


if __name__ == "__main__":
    main()
