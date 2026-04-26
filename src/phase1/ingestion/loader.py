import os
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from .models import Restaurant
from .normalization import normalize_cost, normalize_cuisines, normalize_location, normalize_rating, normalize_text
from .schema import assert_row_matches_mapping, build_field_mapping


@dataclass(slots=True)
class IngestionStats:
    total_rows: int = 0
    yielded_rows: int = 0
    rejected_rows: int = 0


def _iter_hf_rows(dataset_id: str, split: str, revision: str | None) -> Iterable[Mapping[str, object]]:
    try:
        from datasets import load_dataset  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "Hugging Face 'datasets' package is required for ingestion. "
            "Install it with: python -m pip install datasets"
        ) from exc

    kwargs: dict[str, object] = {"split": split}
    if revision:
        kwargs["revision"] = revision
    dataset = load_dataset(dataset_id, **kwargs)
    for row in dataset:
        yield row


def _coerce_restaurant(row: Mapping[str, object], mapping: dict[str, str], index: int) -> Restaurant | None:
    assert_row_matches_mapping(row, mapping)
    name = normalize_text(row.get(mapping["name"]))
    location = normalize_location(row.get(mapping["location"]))
    cuisines = normalize_cuisines(row.get(mapping["cuisines"]))
    cost = normalize_cost(row.get(mapping["cost"]))
    rating = normalize_rating(row.get(mapping["rating"]))

    if not name or not location:
        return None

    restaurant_id_source = mapping.get("id")
    if restaurant_id_source:
        restaurant_id = normalize_text(row.get(restaurant_id_source))
    else:
        restaurant_id = ""
    if not restaurant_id:
        restaurant_id = f"generated-{index}"

    return Restaurant(
        restaurant_id=restaurant_id,
        name=name,
        location=location,
        cuisines=cuisines,
        cost=cost,
        rating=rating,
    )


def iter_restaurants(
    dataset_id: str | None = None,
    split: str = "train",
    revision: str | None = None,
) -> Iterator[Restaurant]:
    chosen_dataset_id = dataset_id or os.getenv("HF_DATASET_ID", "ManikaSaini/zomato-restaurant-recommendation")
    chosen_revision = revision if revision is not None else os.getenv("HF_DATASET_REVISION")

    iterator = iter(_iter_hf_rows(dataset_id=chosen_dataset_id, split=split, revision=chosen_revision))
    first = next(iterator, None)
    if first is None:
        return

    columns = list(first.keys())
    mapping = build_field_mapping(columns)

    first_restaurant = _coerce_restaurant(first, mapping=mapping, index=0)
    if first_restaurant:
        yield first_restaurant

    for index, row in enumerate(iterator, start=1):
        restaurant = _coerce_restaurant(row, mapping=mapping, index=index)
        if restaurant:
            yield restaurant


def load_restaurants(
    dataset_id: str | None = None,
    split: str = "train",
    revision: str | None = None,
    limit: int | None = None,
) -> list[Restaurant]:
    restaurants: list[Restaurant] = []
    for restaurant in iter_restaurants(dataset_id=dataset_id, split=split, revision=revision):
        restaurants.append(restaurant)
        if limit is not None and len(restaurants) >= limit:
            break
    return restaurants
