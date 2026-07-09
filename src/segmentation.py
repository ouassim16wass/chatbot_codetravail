import re

import anthropic

from src.config import ANTHROPIC_API_KEY, LLM_MODEL
from src.vector_db import search

PROMPT_SEGMENTATION = """Tu prepares des questions pour un moteur de recherche documentaire sur le Code du travail francais.
On te donne la question brute d'un utilisateur. Nettoie-la et restructure-la :
- supprime les formules de politesse et les mots parasites (bonjour, svp, euh, voila, en fait...)
- corrige les fautes et retablis les accents
- reformule clairement, SANS changer le sens de la question et SANS ajouter d'informations
- traduis les mots courants en vocabulaire du Code du travail (exemples : se faire virer -> licenciement ; quitter son emploi -> demission)
- si la question porte sur la rupture ou le preavis d'un CDI sans preciser le cas, decoupe en deux sous-questions : le preavis de licenciement et le preavis de demission, sans mentionner CDI ni contrat dans les sous-questions
- si la question porte sur un seul sujet, renvoie une seule question reformulee
- si elle combine plusieurs sujets ou compare plusieurs notions, decoupe-la en 2 ou 3 sous-questions simples et autonomes
Renvoie uniquement la ou les questions, une par ligne, sans numerotation ni commentaire."""

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def decomposer(question):
    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=300,
        temperature=0,
        system=PROMPT_SEGMENTATION,
        messages=[{"role": "user", "content": question}],
    )
    texte = "".join(b.text for b in message.content if b.type == "text")
    lignes = [l.strip() for l in texte.splitlines() if l.strip()]
    return lignes[:3] if lignes else [question]


MOTS_VIDES = {
    "quelle", "quelles", "quels", "comment", "combien", "pendant", "apres",
    "avant", "entre", "cette", "votre", "notre", "salarie", "salariee",
    "employeur", "travail", "contrat", "france", "conditions", "regles",
}


def mots_cles(texte):
    mots = re.findall(r"[a-zà-ÿ]{6,}", texte.lower())
    return [m for m in mots if m not in MOTS_VIDES][:4]


def numeros_cites(question):
    return [
        "L" + m.group(1)
        for m in re.finditer(r"[Ll]\.?\s*(\d{3,4}-\d+(?:-\d+)*)", question)
    ]


def chunks_cites(collection, numeros):
    if not numeros:
        return []
    resultat = collection.get(
        where={"numero": {"$in": numeros}}, include=["documents", "metadatas"]
    )
    return [
        {"texte": document, "metadonnees": metadonnees, "score": 1.0}
        for document, metadonnees in zip(
            resultat["documents"], resultat["metadatas"]
        )
    ]


def rechercher(collection, modele, question, k=5):
    sous_questions = decomposer(question)
    par_numero = {}
    for article in chunks_cites(collection, numeros_cites(question)):
        par_numero[article["metadonnees"]["numero"]] = article
    for sous_question in sous_questions:
        candidats = list(search(collection, modele, sous_question, k=4))
        for mot in mots_cles(sous_question):
            candidats.extend(
                search(collection, modele, sous_question, k=2, contient=mot)
            )
        for article in candidats:
            numero = article["metadonnees"]["numero"]
            if (
                numero not in par_numero
                or article["score"] > par_numero[numero]["score"]
            ):
                par_numero[numero] = article
    classes = sorted(par_numero.values(), key=lambda a: -a["score"])
    limite = 8 if len(sous_questions) > 1 else k
    return classes[:limite], sous_questions
