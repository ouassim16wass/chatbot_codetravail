from src.moderateur import MESSAGES_BLOCAGE, moderer
from src.rag import REPONSE_HORS_CORPUS, generate_answer
from src.segmentation import rechercher
from src.vector_db import load_database

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
        verdict = moderer(question)
        if verdict != "legitime":
            print("\n" + MESSAGES_BLOCAGE[verdict])
            continue
        chunks, sous_questions = rechercher(collection, modele, question)
        if len(sous_questions) > 1:
            print("\nQuestion decomposee pour la recherche :")
            for sous_question in sous_questions:
                print(f"  - {sous_question}")
        resultat = generate_answer(question, chunks, date_corpus)
        afficher(resultat)
    print("Au revoir.")


if __name__ == "__main__":
    main()
