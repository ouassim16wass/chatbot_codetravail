# Assistant Code du travail (RAG)

Chatbot de questions-reponses sur le droit du travail francais, avec citation
systematique des articles utilises.

Projet final M2 MD5 — Data & IA.

## Objectif

Construire un systeme RAG complet, sans framework tout-en-un : ingestion des
textes de loi, decoupage en chunks, base vectorielle persistee, generation de
reponses avec citation des numeros d'articles et refus de repondre hors corpus.

## Installation

```bash
pip install -r requirements.txt
cp .env.example .env   # puis renseigner la cle API
```

## Utilisation

```bash
python index.py   # construit la base vectorielle depuis le corpus
python ask.py     # lance la boucle de questions-reponses
```

## Questions de reflexion

A completer avant l'implementation du pipeline :

1. Granularite du chunking
2. Tracabilite des numeros d'articles
3. Fraicheur du corpus
4. Reponses conditionnelles
5. Frontiere du conseil juridique
