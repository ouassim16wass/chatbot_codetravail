# Assistant Code du travail (RAG)

Chatbot de questions-réponses sur le droit du travail français, avec citation
systématique des articles utilisés.

Projet final M2 MD5 — Data & IA.

## Objectif

Construire un système RAG complet, sans framework tout-en-un : ingestion des
textes de loi, découpage en chunks, base vectorielle persistée, génération de
réponses avec citation des numéros d'articles et refus de répondre hors corpus.

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env   # puis renseigner la clé API
```

## Utilisation

```bash
python index.py   # construit la base vectorielle depuis le corpus (une seule fois)
python ask.py     # lance la boucle de questions-réponses
```

L'indexation ne se fait qu'une fois : `ask.py` recharge la base persistée
sans jamais réindexer. Dans la boucle, tapez votre question puis Entrée ;
`quit` pour sortir. Chaque réponse affiche les articles sources (issus des
métadonnées du retrieval, pas du LLM), la date du corpus et l'avertissement
juridique.

## Récupération du corpus

Le corpus prêt à l'emploi (`data/corpus.json`, 812 articles, 8 thèmes) est
fourni dans le dépôt. Pour le reconstruire depuis la source officielle
(option B du sujet — base LEGI de la DILA) :

```bash
python src/download_corpus.py   # lit l'archive LEGI (~1,1 Go) en flux, n'écrit que le Code du travail (366 Mo de XML)
python src/extract_corpus.py    # filtre les versions en vigueur des 8 thèmes, nettoie, produit data/corpus.json
python -m src.eval_retrieval    # valide le retrieval sur le jeu de questions test
```

## Choix du LLM

Le sujet propose l'API Groq ; nous utilisons l'API Anthropic (modèle
claude-haiku-4-5), qui repose sur le même principe : une bibliothèque
« brique élémentaire » qui envoie la question et le contexte à un LLM hébergé
et récupère la réponse, à température basse (0.2) pour limiter les
inventions. Le pipeline étant écrit brique par brique, changer de fournisseur
ne modifie qu'une seule fonction (`generate_answer` dans `src/rag.py`) : la
recherche, le prompt et l'assemblage de la réponse restent identiques. La clé
API est lue depuis `.env`, jamais versionnée.

## Questions de réflexion

### 1. Granularité du chunking

Indexer par section produit des chunks trop longs : l'embedding est dilué et la
citation d'un article précis devient difficile. Indexer chaque article seul est
précis, mais un article isolé perd le contexte de sa section (renvois, sigles).
Nous retenons une approche hybride : un chunk par article, dont le texte
embeddé est préfixé du thème de la section et du numéro d'article
(« Durée du travail — Article L3121-27 : ... »). Le chunk reste court et
précis tout en portant son contexte. Les rares articles très longs sont
découpés en plusieurs chunks qui conservent chacun le numéro d'article.

### 2. Traçabilité des numéros d'articles

Le numéro d'article est stocké aux deux endroits : dans le texte embeddé (une
question comme « que dit l'article L3121-1 ? » retrouve ainsi la bonne fiche)
et dans les métadonnées (numéro, thème, source). Trois garde-fous contre les
citations inventées : le contexte fourni au LLM est numéroté avec les vrais
numéros d'articles ; le prompt interdit de citer un numéro absent du contexte ;
et surtout la liste des articles sources affichée sous chaque réponse est
générée par le code à partir des métadonnées du retrieval, pas par le LLM.
La garantie est donc technique et non confiée au modèle.

### 3. Fraîcheur du corpus

La date d'extraction du corpus est enregistrée dans les métadonnées de la base
vectorielle lors de l'indexation, à côté du nom du modèle d'embedding. Le code
ajoute à chaque réponse la mention « Corpus à jour au [date] — le droit du
travail évolue, vérifiez sur legifrance.gouv.fr ». Cette ligne étant ajoutée
par le programme, elle ne peut pas être omise.

### 4. Réponses conditionnelles

Beaucoup de réponses dépendent de la convention collective, de l'ancienneté ou
de la taille de l'entreprise. Le prompt demande au LLM de donner la règle
générale du Code du travail (le socle légal) en nommant explicitement les
paramètres dont la réponse dépend, et de renvoyer vers la convention collective
applicable. Une question de clarification interactive est envisageable comme
amélioration (jalon 6, avec historique de conversation), mais la réponse
générale assortie de réserves est plus robuste pour la v1.

### 5. Frontière du conseil juridique

Une question factuelle (« combien de jours de congés par an ? ») trouve sa
réponse directement dans le Code : le système répond en citant les articles.
Une question d'interprétation (« mon licenciement est-il abusif ? ») demande de
qualifier une situation personnelle : le système expose ce que dit la loi en
général, refuse explicitement de juger le cas particulier et oriente vers un
avocat ou l'inspection du travail. Dans tous les cas, l'avertissement
juridique obligatoire est concaténé à la réponse par le code qui l'assemble,
et non par le prompt : il est donc présent dans 100 % des réponses.
