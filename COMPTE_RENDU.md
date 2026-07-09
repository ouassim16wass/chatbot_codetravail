# Compte rendu — Assistant Code du travail (RAG)

## Ce que j'ai fait

J'ai suivi les jalons du sujet dans l'ordre, avec une branche et une pull
request par étape. Le corpus vient de l'option B : les fichiers XML officiels
de la base LEGI, et j'ai écrit l'extraction moi-même. Chaque brique du
pipeline est un petit module séparé : découpage, embeddings, base
vectorielle, prompt, appel au LLM.

## Les difficultés

L'archive LEGI fait 1,1 Go et contient tous les codes de France. Je l'ai lue
en flux pour ne garder que le Code du travail (366 Mo de XML).

Les plages d'articles des thèmes se chevauchent : la rupture conventionnelle
est incluse dans la plage du licenciement. Il faut tester du plus précis au
plus large, sinon les thèmes sont faux.

Le modèle d'embedding cherche mal quand la question n'a pas d'accents. La
reformulation automatique des questions corrige ça.

Les tests ont montré deux vrais problèmes. Un article long prenait plusieurs
places du top 5 : corrigé en gardant un seul extrait par article. Et une
question comme « que dit l'article L3121-27 ? » échouait : corrigé par une
recherche directe par numéro.

## Mes choix

Un chunk par article, avec le thème et le numéro écrits au début du texte.

Les garanties importantes sont dans le code, pas dans le prompt : les
sources affichées viennent des métadonnées, et l'avertissement juridique et
la date du corpus sont ajoutés à chaque réponse par le programme.

J'utilise l'API Anthropic (claude-haiku-4-5, température 0,2) au lieu de
Groq : même principe d'appel, et changer de fournisseur ne toucherait qu'une
seule fonction.

Nombre d'extraits envoyés au LLM : 5 pour une question simple, 6 maximum
pour une question découpée en sous-questions. Les articles sont courts, donc
ça suffit pour bien répondre. Avec moins, il manque souvent le bon article.
Avec plus, le modèle se perd et chaque question coûte plus cher. Le jeu de
test du jalon 3 valide ce choix (6/6).

La mise à jour du corpus se fait en une commande : elle télécharge les
petites archives publiées chaque jour par l'État et ne réencode que les
articles modifiés.

## Les améliorations (jalon 6)

Quatre de la liste du sujet : un modérateur qui bloque les injections et le
hors sujet, la reformulation des questions familières, le mode comparaison
(la question est découpée en sous-questions), et la recherche par numéro
d'article. Plus un score de confiance affiché avec chaque réponse.

Une campagne de dix questions est documentée dans le README, avec une note
de 7,5/10. Le système n'a jamais inventé : quand il ne sait pas, il refuse.

## Avec plus de temps

Étendre le corpus à tout le Code du travail. Améliorer la recherche sur le
vocabulaire du préavis. Ajouter l'historique de conversation pour les
questions de suivi.
