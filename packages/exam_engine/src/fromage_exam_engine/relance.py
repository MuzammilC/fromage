"""Relance thresholds: how long the Candidate may be silent before each step (CONTEXT.md: Relance).

Silence is time without Candidate activity (no typing, no message). Every offset counts from the
last activity, or from the question if there has been none since. Thresholds belong to the Medium,
so voice can use other values than text without any change to the engine.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from enum import Enum


class Medium(Enum):
    TEXT = "text"
    VOICE = "voice"


@dataclass(frozen=True)
class RelanceThresholds:
    """Seconds of silence after which each Relance step happens."""

    repeat_after: float = 6.0
    """Step 1: repeat the question word for word."""
    simplify_after: float = 9.0
    """Step 2: repeat it more simply."""
    reformulate_after: float = 12.0
    """Step 3: ask the Examiner to reformulate it."""
    move_on_after: float = 15.0
    """Step 4: move on and record that the question went unanswered."""
    listening_end_after: float = 30.0
    """Silence that ends the listen-only stretch of a monologue. There is no Relance there."""

    def __post_init__(self) -> None:
        steps = self.steps
        if steps[0] <= 0 or any(a >= b for a, b in itertools.pairwise(steps)):
            raise ValueError(f"Relance thresholds must be positive and increasing, got {steps}")
        if self.listening_end_after <= 0:
            raise ValueError(
                f"listening_end_after must be positive, got {self.listening_end_after}"
            )

    @property
    def steps(self) -> tuple[float, float, float, float]:
        return (self.repeat_after, self.simplify_after, self.reformulate_after, self.move_on_after)


DEFAULT_RELANCE: dict[Medium, RelanceThresholds] = {
    Medium.TEXT: RelanceThresholds(),
    Medium.VOICE: RelanceThresholds(),
}
