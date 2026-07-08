"""Validation du retrieval (jalon 3).

Avant tout appel au LLM, on verifie que pour des questions dont on connait
l'article attendu, cet article remonte dans le top-k de la recherche. Si ce
n'est pas le cas, le probleme vient du chunking, de l'embedding ou du
corpus — pas du LLM, qui n'est pas encore branche. Ces questions sont
conservees comme jeu d'evaluation permanent du projet.
"""

from src.vector_db import load_database, search

TOP_K = 5

# Jeu de test : (question, articles acceptes dans le top-k).
# Les questions sont ecrites avec leurs accents : le modele d'embedding y
# est sensible (constat fait au jalon 2). Pour les questions larges,
# plusieurs articles d'une meme section sont des reponses valables : le
# test reussit si au moins l'un d'eux remonte.
JEU_DE_TEST = [
    ("Quelle est la durée légale de travail par semaine ?",
     {"L3121-27"}),
    ("Combien d'heures maximum peut-on travailler par semaine ?",
     {"L3121-20"}),
    ("Combien de jours de congés payés gagne-t-on par mois de travail ?",
     {"L3141-3"}),
    ("Comment fonctionne la rupture conventionnelle ?",
     {"L1237-11", "L1237-12", "L1237-13"}),
    ("Qu'est-ce que le harcèlement moral au travail ?",
     {"L1152-1"}),
    ("Quelle est la durée maximale de la période d'essai d'un CDI ?",
     {"L1221-19"}),
]


def main():
    collection, modele = load_database()
    reussites = 0
    for question, acceptes in JEU_DE_TEST:
        resultats = search(collection, modele, question, k=TOP_K)
        numeros = [r["metadonnees"]["numero"] for r in resultats]
        trouve = bool(acceptes & set(numeros))
        reussites += trouve
        print(f"{'OK  ' if trouve else 'RATE'}  {question}")
        print(f"      attendu : {' ou '.join(sorted(acceptes))} | "
              f"top-{TOP_K} : {', '.join(numeros)}")
    print(f"\nBilan : {reussites}/{len(JEU_DE_TEST)} questions trouvent "
          f"un article attendu dans le top-{TOP_K}")


if __name__ == "__main__":
    main()
