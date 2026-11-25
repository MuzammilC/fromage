import json
import re
from dataclasses import dataclass
from typing import Protocol

DEFAULT_MODEL = "claude-haiku-5-5"
MAX_TOKENS = 500

SYSTEM = """Tu relis un Item (un sujet) pour un simulateur d'examen oral de français, niveau CECRL A2.
Réponds uniquement avec un objet JSON :
{"a2_level": true|false, "playable": true|false, "comments": "..."}
- a2_level : la langue de la consigne est-elle de niveau A2 (vocabulaire et structures simples) ?
- playable : un candidat et un examinateur peuvent-ils jouer cet Item tel quel, sans information manquante ni contradiction ?
- comments : une ou deux phrases en français, vides si tout va bien."""


class Checker(Protocol):
    def complete(self, system: str, user: str) -> str: ...


@dataclass(frozen=True)
class LevelVerdict:
    a2_level: bool
    playable: bool
    comments: str


class AnthropicChecker:
    def __init__(self, model: str = DEFAULT_MODEL):
        import anthropic

        self.model = model
        self._client = anthropic.Anthropic()

    def complete(self, system: str, user: str) -> str:
        message = self._client.messages.create(
            model=self.model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in message.content if block.type == "text")


def check_level(text: str, llm: Checker) -> LevelVerdict | None:
    """Asks a second model whether the Item is A2 and playable. None when it gives no usable answer."""
    try:
        raw = llm.complete(SYSTEM, f"Item :\n{text}")
        stripped = raw.strip()
        fenced = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", stripped, re.DOTALL)
        data = json.loads(fenced.group(1) if fenced else stripped)
        a2, playable = data["a2_level"], data["playable"]
        if not isinstance(a2, bool) or not isinstance(playable, bool):
            return None
        return LevelVerdict(a2, playable, str(data.get("comments") or ""))
    except Exception:  # noqa: BLE001 - advisory check: any failure just means no verdict
        return None
