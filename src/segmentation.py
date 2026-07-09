import anthropic

from src.config import ANTHROPIC_API_KEY, LLM_MODEL
from src.vector_db import search

PROMPT_SEGMENTATION = """Tu prepares des questions pour un moteur de recherche documentaire sur le Code du travail francais.
On te donne la question d'un utilisateur.
- Si elle porte sur un seul sujet, renvoie-la telle quelle (reformulee clairement si elle est familiere).
- Si elle combine plusieurs sujets ou compare plusieurs notions, decoupe-la en 2 ou 3 sous-questions simples et autonomes.
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


def rechercher(collection, modele, question, k=5):
    sous_questions = decomposer(question)
    par_numero = {}
    for sous_question in sous_questions:
        for article in search(collection, modele, sous_question, k=4):
            numero = article["metadonnees"]["numero"]
            if (
                numero not in par_numero
                or article["score"] > par_numero[numero]["score"]
            ):
                par_numero[numero] = article
    classes = sorted(par_numero.values(), key=lambda a: -a["score"])
    limite = 6 if len(sous_questions) > 1 else k
    return classes[:limite], sous_questions
