"""Fixed French lines the Examiner says at transitions. The LLM never writes these.

The line announcing a Part is part of the Exam Definition (`announcement`).
"""

from fromage_exam_definition.generated import Part

PART_FALLBACK = "Nous passons à la partie suivante."
DRAW_INTRO = "Pour chaque partie, regardez les deux sujets et choisissez-en un."
PREP_ENDED = "Le temps de préparation est terminé. Nous commençons l'épreuve."
SESSION_ENDED = "Merci, l'épreuve est terminée. Au revoir."


def part_announcement(part: Part) -> str:
    """The line the Exam Definition gives the Part, or a generic one."""
    return part.announcement or PART_FALLBACK


def prep_started(seconds: int) -> str:
    minutes, rest = divmod(seconds, 60)
    if rest == 0:
        spoken = f"{minutes} minute{'s' if minutes > 1 else ''}"
    else:
        spoken = f"{seconds} secondes"
    return f"Vous avez {spoken} pour préparer vos sujets."
