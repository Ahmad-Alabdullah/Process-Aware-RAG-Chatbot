from app.core.models.askModel import AskBody


def build_prompt(
    style: str,
    body: AskBody,
    context_text: str,
    gating_hint: str,
) -> str:
    """
    Erzeugt den finalen Prompt abhängig vom Prompt-Stil.
    """
    base_intro = "Beantworte die Frage basierend auf dem Kontext."

    if style == "no_gating":
        gating_block = ""
    else:
        gating_block = gating_hint

    if style == "baseline":
        return f"""{base_intro}
        {gating_block}

        Frage: {body.query}

        Kontext aus Prozessdokumenten:
        {context_text}

        Antwort (auf Deutsch und mit Belegen und Zitaten aus dem Kontext. Falls die Zitatpflicht nicht erfüllbar ist, mache dies deutlich und erfinde keine Belege oder Informationen aus deinem internen Wissen):
        """

    if style == "fewshot":
        # TODO: Bessere Few-Shot Beispiele
        return f"""Du bist ein Assistent für Prozessdokumente der Hochschule.

        Beispiel:
        Frage: Welche Rolle genehmigt eine Dienstreise?
        Kontext:
        [1] (Quelle: Dienstreiserichtlinie) ...
        Beispielantwort:
        Die Dienstreise wird in der Regel von ... genehmigt [1].

        Jetzt kommt eine neue Frage des Nutzers.

        {gating_block}

        Frage: {body.query}

        Kontext aus Prozessdokumenten:
        {context_text}

        Antworte im Stil des Beispiels: klar, knapp, mit Zitaten in eckigen Klammern.
        """

    if style == "cot":
        return f"""{base_intro}
        {gating_block}

        Frage: {body.query}

        Kontext aus Prozessdokumenten:
        {context_text}

        Denke intern Schritt für Schritt über Prozess, Rolle und Kontext nach.
        Gib dem Nutzer am Ende nur eine klare, strukturierte Antwort auf Deutsch mit Zitaten aus dem Kontext.
        """

    # Fallback
    return build_prompt("baseline", body, context_text, gating_hint)
