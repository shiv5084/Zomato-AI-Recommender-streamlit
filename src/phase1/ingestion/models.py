from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Restaurant:
    """Canonical restaurant model for milestone 1."""

    restaurant_id: str
    name: str
    location: str
    cuisines: list[str] = field(default_factory=list)
    cost: float | None = None
    rating: float | None = None
