from src.rag import REPONSE_HORS_CORPUS, generate_answer
from src.vector_db import load_database, search

COMMANDES_SORTIE = {"quit", "exit", "q"}


def afficher(resultat):
    print()
    print(resultat["reponse"])
    if not resultat["reponse"].startswith(REPONSE_HORS_CORPUS):
        print()
        print("Articles sources : " + ", ".join(resultat["sources"]))
    print()
    print(
        f"Corpus a jour au {resultat['date_corpus']} - le droit du travail "
        "evolue, verifiez sur legifrance.gouv.fr"
    )
    print(resultat["avertissement"])


def main():
    print("Chargement de la base...")
    collection, modele = load_database()
    date_corpus = collection.metadata["date_corpus"]
    print(f"Assistant Code du travail (corpus du {date_corpus})")
    print("Posez votre question, ou tapez 'quit' pour sortir.")
    while True:
        try:
            question = input("\nQuestion > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not question:
            continue
        if question.lower() in COMMANDES_SORTIE:
            break
        chunks = search(collection, modele, question, k=5)
        resultat = generate_answer(question, chunks, date_corpus)
        afficher(resultat)
    print("Au revoir.")


if __name__ == "__main__":
    main()
