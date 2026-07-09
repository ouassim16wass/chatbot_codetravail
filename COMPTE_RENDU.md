# Compte rendu — Assistant Code du travail (RAG)

## Démarche

J'ai suivi les jalons du sujet dans l'ordre, une branche et une pull request
par étape (16 PR au total). Corpus récupéré par l'option B : les XML officiels
de la base LEGI, dont j'ai écrit l'extraction moi-même. Chaque brique du
pipeline (chunking, embeddings, base vectorielle, prompt, appel LLM) est un
module séparé de quelques dizaines de lignes.

## Difficultés rencontrées

L'archive LEGI fait 1,1 Go et contient tous les codes français : je l'ai lue
en flux, sans la stocker, en ne gardant que le Code du travail — il a fallu
traverser environ 4 millions de fichiers de textes abrogés avant d'atteindre
les bons dossiers. Deuxième piège : les plages d'articles des thèmes du sujet
sont imbriquées (la rupture conventionnelle est incluse dans la plage du
licenciement, elle-même dans celle du contrat de travail) ; il faut tester du
plus spécifique au plus large, sinon les thèmes sont faux. Troisième
difficulté : le modèle d'embedding est sensible aux accents (« duree legale »
cherche moins bien que « durée légale ») — la reformulation automatique des
questions corrige ça. Enfin, le jeu d'évaluation du jalon 3 a révélé deux
vrais défauts : les articles longs, découpés en plusieurs chunks, occupaient
plusieurs places du top-5 (corrigé par une déduplication par article, score
passé de 5/6 à 6/6), et la recherche par sens ne retrouvait pas un article
demandé par son numéro (corrigé par la recherche hybride).

## Décisions de conception

Un chunk par article, préfixé du thème et du numéro, pour une citation
précise sans perdre le contexte. Les garanties critiques sont dans le code,
pas dans le prompt : la liste des articles sources vient des métadonnées du
retrieval, l'avertissement juridique et la date du corpus sont ajoutés par le
programme à chaque réponse. J'utilise l'API Anthropic (claude-haiku-4-5,
température 0,2) plutôt que Groq : même principe d'appel, et le pipeline
étant découpé en briques, changer de fournisseur ne toucherait qu'une seule
fonction. L'indexation est incrémentale (empreinte de texte par chunk) et le
corpus se synchronise avec les lois récentes par les archives incrémentales
quotidiennes de la DILA, en une commande.

## Améliorations réalisées (jalon 6)

Quatre améliorations de la liste du sujet : un agent modérateur qui bloque
les prompt injections et les questions hors sujet avant le pipeline ; la
reformulation des questions familières ; le mode comparaison (une question
comparative est découpée en sous-questions et les extraits des deux notions
sont fusionnés) ; la recherche hybride par numéro d'article. Une campagne de
dix questions, documentée dans le README avec les réponses obtenues, note le
système à 7,5/10 : aucune invention constatée, le système préfère refuser
que d'inventer.

## Avec plus de temps

Étendre le corpus aux 11 000 articles du Code du travail entier ; améliorer
le retrieval sur le vocabulaire du préavis (la question « préavis en CDI »
remonte la période d'essai, car son préfixe de thème contient « CDI ») ;
afficher un score de confiance calibré ; ajouter l'historique de conversation
pour les questions de suivi.
