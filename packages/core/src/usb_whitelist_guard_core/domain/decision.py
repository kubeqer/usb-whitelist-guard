from dataclasses import dataclass
from enum import StrEnum


class Decision(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"


@dataclass(frozen=True, slots=True)
class Verdict:
    decision: Decision
    reason: str

    @classmethod
    def allow(cls, reason: str) -> Verdict:
        return cls(Decision.ALLOW, reason)

    @classmethod
    def block(cls, reason: str) -> Verdict:
        return cls(Decision.BLOCK, reason)
