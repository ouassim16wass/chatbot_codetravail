AVERTISSEMENT = (
    "Cet assistant ne fournit pas de conseil juridique. Consultez un avocat "
    "ou l'inspection du travail pour votre situation personnelle."
)


def build_prompt(question, chunks):
    raise NotImplementedError


def generate_answer(question, chunks):
    raise NotImplementedError
