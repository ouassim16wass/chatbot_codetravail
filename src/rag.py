"""Pipeline RAG : assemblage du contexte, prompt systeme et appel au LLM."""

AVERTISSEMENT = (
    "Cet assistant ne fournit pas de conseil juridique. Consultez un avocat "
    "ou l'inspection du travail pour votre situation personnelle."
)


def build_prompt(question, chunks):
    """Assemble le prompt systeme : contexte numerote avec metadonnees,
    obligation de citer les articles, interdiction d'inventer."""
    # TODO: numeroter les chunks avec leur numero d'article et construire
    # le prompt (refus si l'information n'est pas dans le contexte)
    raise NotImplementedError


def generate_answer(question, chunks):
    """Appelle le LLM a temperature basse et retourne la reponse
    accompagnee des articles sources et de l'avertissement juridique."""
    # TODO: appel Groq, verification des citations, ajout de AVERTISSEMENT
    raise NotImplementedError
