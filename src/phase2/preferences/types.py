from dataclasses import asdict, dataclass, field
from typing import Literal

BudgetBand = Literal["low", "medium", "high"]


class ValidationError(ValueError):
    """Raised when user preferences cannot be validated."""


@dataclass(frozen=True, slots=True)
class UserPreferences:
    location: str
    budget_band: BudgetBand
    cuisines: list[str] = field(default_factory=list)
    minimum_rating: float = 0.0
    additional_preferences: str | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
