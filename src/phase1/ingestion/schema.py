from collections.abc import Mapping

REQUIRED_CANONICAL_FIELDS = ("name", "location", "cuisines", "cost", "rating")

FIELD_CANDIDATES = {
    "name": ("name", "restaurant_name", "restaurant", "res_name", "title"),
    "location": ("location", "city", "locality", "listed_in(city)", "address"),
    "cuisines": ("cuisines", "cuisine", "category", "categories"),
    "cost": (
        "cost",
        "average_cost",
        "average_cost_for_two",
        "approx_cost(for two people)",
        "cost_for_two",
        "price",
    ),
    "rating": ("rating", "aggregate_rating", "user_rating", "rate", "score"),
    "id": ("restaurant_id", "res_id", "id", "_id"),
}


def build_field_mapping(column_names: list[str]) -> dict[str, str]:
    lowered = {column.lower(): column for column in column_names}
    mapping: dict[str, str] = {}
    for canonical in REQUIRED_CANONICAL_FIELDS:
        chosen = None
        for candidate in FIELD_CANDIDATES[canonical]:
            if candidate.lower() in lowered:
                chosen = lowered[candidate.lower()]
                break
        if not chosen:
            raise ValueError(
                f"Could not map required field '{canonical}'. "
                f"Columns available: {', '.join(column_names)}"
            )
        mapping[canonical] = chosen

    for candidate in FIELD_CANDIDATES["id"]:
        if candidate.lower() in lowered:
            mapping["id"] = lowered[candidate.lower()]
            break
    return mapping


def assert_row_matches_mapping(row: Mapping[str, object], mapping: dict[str, str]) -> None:
    missing_source_fields = [source for source in mapping.values() if source not in row]
    if missing_source_fields:
        raise ValueError(f"Row is missing mapped fields: {missing_source_fields}")
