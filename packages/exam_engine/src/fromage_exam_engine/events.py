"""Events the caller feeds the engine.

Every event carries `at`, the caller's clock in seconds. The engine never reads a wall clock,
so a test can play a whole Session in no time. Times must not go backwards.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChoseItem:
    """The Candidate keeps one Item of a Draw."""

    at: float
    part: str
    item_id: str


@dataclass(frozen=True)
class Ready:
    """The Candidate says they are ready, which ends Prep Time early."""

    at: float


@dataclass(frozen=True)
class CandidateTurn:
    """The Candidate sent a turn (a typed message)."""

    at: float
    text: str


@dataclass(frozen=True)
class CandidateActivity:
    """The Candidate is typing. Relance measures silence as time without this or a turn."""

    at: float


@dataclass(frozen=True)
class CandidateDone:
    """The Candidate says they have finished their monologue."""

    at: float


@dataclass(frozen=True)
class ExaminerDone:
    """The Examiner finished asking its question. Relance counts silence from this moment."""

    at: float


@dataclass(frozen=True)
class Tick:
    """Time has passed. Send one whenever `ExamEngine.next_deadline` is reached."""

    at: float


Event = ChoseItem | Ready | CandidateTurn | CandidateActivity | CandidateDone | ExaminerDone | Tick
