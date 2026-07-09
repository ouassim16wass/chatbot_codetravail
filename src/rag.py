import anthropic

from src.config import ANTHROPIC_API_KEY, LLM_MODEL

AVERTISSEMENT = (
    "Cet assistant ne fournit pas de conseil juridique. Consultez un avocat "
    "ou l'inspection du travail pour votre situation personnelle."
)

REPONSE_HORS_CORPUS = "Je ne trouve pas cette information dans ma base."

SEUIL_CONFIANCE = 0.5

PROMPT_SYSTEME = f"""Tu es un assistant juridique specialise dans le Code du travail francais.

Tu recois des extraits numerotes du Code du travail puis une question. Regles :
- Reponds uniquement a partir des extraits fournis, jamais de tes propres connaissances.
- Rattache chaque affirmation au numero de l'article dont elle provient, par exemple : selon l'article L3121-27, ...
- Ne cite jamais un numero d'article absent des extraits fournis.
- Si les extraits ne permettent pas de repondre a la question, reponds exactement : {REPONSE_HORS_CORPUS}
- Si la reponse depend de la convention collective, de l'anciennete ou de la taille de l'entreprise, donne la regle generale du Code du travail puis precise explicitement de quoi elle depend.
- Si la question demande de juger une situation personnelle, expose la regle generale, refuse de te prononcer sur le cas particulier et oriente vers un avocat ou l'inspection du travail.
- Reponds en francais, de facon claire et concise."""

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def build_context(chunks):
    blocs = []
    for i, chunk in enumerate(chunks, start=1):
        numero = chunk["metadonnees"]["numero"]
        blocs.append(f"Extrait {i} (article {numero}) :\n{chunk['texte']}")
    return "\n\n".join(blocs)


def generate_answer(question, chunks, date_corpus):
    message = client.messages.create(
        model=LLM_MODEL,
        max_tokens=1024,
        temperature=0.2,
        system=PROMPT_SYSTEME,
        messages=[
            {
                "role": "user",
                "content": f"{build_context(chunks)}\n\nQuestion : {question}",
            }
        ],
    )
    texte = "".join(bloc.text for bloc in message.content if bloc.type == "text")
    return {
        "reponse": texte.strip(),
        "sources": [
            f"{c['metadonnees']['numero']} (en vigueur depuis le "
            f"{c['metadonnees']['date_debut']}, pertinence {c['score']:.2f})"
            for c in chunks
        ],
        "confiance": max((c["score"] for c in chunks), default=0.0),
        "date_corpus": date_corpus,
        "avertissement": AVERTISSEMENT,
    }
