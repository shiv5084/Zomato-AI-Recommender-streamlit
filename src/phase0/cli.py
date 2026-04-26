import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

from phase1.ingestion import load_restaurants
from phase2.preferences import ValidationError, allowed_cities_from_restaurants, preferences_from_mapping
from phase3.integration import build_integration_output
from phase4.llm import recommend_with_groq
from phase5.output import render_recommendations, render_empty_state, TelemetryTracker


def _handle_info() -> int:
    print("Milestone 1 - Project Diagnostics")
    print("Project: ZomatoUseCase")
    print("Phase: 0 (Scope and Foundations)")
    print(f"Python: {platform.python_version()}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print(f"Working directory: {Path.cwd()}")
    print("Next target: Phase 1 (Data ingestion and canonical model)")
    return 0


def _check_env_var(name: str) -> tuple[bool, str]:
    value = os.getenv(name)
    if not value:
        return False, f"{name} is not set"
    return True, f"{name} is set"


def _check_file(path: Path) -> tuple[bool, str]:
    if path.exists():
        return True, f"{path.name} exists"
    return False, f"{path.name} is missing"


def _check_command(name: str) -> tuple[bool, str]:
    if shutil.which(name):
        return True, f"'{name}' is available"
    return False, f"'{name}' is not found in PATH"


def _print_check(label: str, ok: bool, message: str) -> None:
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}: {message}")


def _handle_doctor() -> int:
    checks = []
    checks.append(("python>=3.10", sys.version_info >= (3, 10), "Current interpreter checked"))
    checks.append(("git", *_check_command("git")))
    checks.append((".env.example", *_check_file(Path(".env.example"))))
    checks.append(("OPENAI_API_KEY", *_check_env_var("OPENAI_API_KEY")))
    checks.append(("HF_DATASET_ID", *_check_env_var("HF_DATASET_ID")))

    failed = 0
    for label, ok, message in checks:
        _print_check(label, ok, message)
        if not ok:
            failed += 1

    if failed:
        print(f"\nDoctor found {failed} failing check(s).")
        return 1

    print("\nAll doctor checks passed.")
    return 0


def _handle_ingest_smoke(limit: int, split: str, dataset_id: str | None, revision: str | None) -> int:
    try:
        restaurants = load_restaurants(
            dataset_id=dataset_id,
            split=split,
            revision=revision,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] ingestion smoke failed: {exc}")
        return 1

    if not restaurants:
        print("[FAIL] ingestion returned zero valid restaurants.")
        return 1

    print(f"[OK] Loaded {len(restaurants)} restaurant(s).")
    sample = restaurants[0]
    print("Sample canonical record:")
    print(f"- id: {sample.restaurant_id}")
    print(f"- name: {sample.name}")
    print(f"- location: {sample.location}")
    print(f"- cuisines: {', '.join(sample.cuisines) if sample.cuisines else 'N/A'}")
    print(f"- cost: {sample.cost if sample.cost is not None else 'N/A'}")
    print(f"- rating: {sample.rating if sample.rating is not None else 'N/A'}")
    return 0


def _handle_prefs_parse(args: argparse.Namespace) -> int:
    payload: dict[str, object] = {
        "location": args.location,
        "budget_band": args.budget_band,
        "cuisines": args.cuisines,
        "minimum_rating": args.minimum_rating,
        "additional_preferences": args.additional_preferences,
    }

    allowed_city_names: set[str] | None = None
    if args.validate_location_from_dataset:
        try:
            restaurants = load_restaurants(limit=args.city_limit)
            allowed_city_names = allowed_cities_from_restaurants(restaurants)
        except Exception as exc:  # noqa: BLE001
            print(f"failed to load dataset for location validation: {exc}", file=sys.stderr)
            return 1

    try:
        preferences = preferences_from_mapping(payload, allowed_city_names=allowed_city_names)
    except ValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(preferences.to_dict(), indent=2))
    return 0


def _handle_prompt_build(args: argparse.Namespace) -> int:
    payload: dict[str, object] = {
        "location": args.location,
        "budget_band": args.budget_band,
        "cuisines": args.cuisines,
        "minimum_rating": args.minimum_rating,
        "additional_preferences": args.additional_preferences,
    }

    try:
        preferences = preferences_from_mapping(payload)
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1
        
    try:
        restaurants = load_restaurants(limit=args.limit)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load dataset: {exc}", file=sys.stderr)
        return 1

    result = build_integration_output(restaurants, preferences, top_n=args.top_n)
    print(json.dumps(result["prompt_payload"], indent=2))
    return 0


def _handle_recommend(args: argparse.Namespace) -> int:
    payload: dict[str, object] = {
        "location": args.location,
        "budget_band": args.budget_band,
        "cuisines": args.cuisines,
        "minimum_rating": args.minimum_rating,
        "additional_preferences": args.additional_preferences,
    }

    try:
        preferences = preferences_from_mapping(payload)
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1
        
    try:
        restaurants = load_restaurants(limit=args.limit)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load dataset: {exc}", file=sys.stderr)
        return 1

    # Phase 3 integration
    integration_result = build_integration_output(restaurants, preferences, top_n=args.top_n)
    
    # Phase 4 recommendation
    try:
        rankings = recommend_with_groq(integration_result["prompt_payload"], integration_result["candidates"], top_n=args.top_n)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
        
    print(json.dumps(rankings, indent=2))
    return 0


def _handle_recommend_run(args: argparse.Namespace) -> int:
    tracker = TelemetryTracker()
    tracker.start_timer("total_runtime")
    
    payload: dict[str, object] = {
        "location": args.location,
        "budget_band": args.budget_band,
        "cuisines": args.cuisines,
        "minimum_rating": args.minimum_rating,
        "additional_preferences": args.additional_preferences,
    }

    try:
        preferences = preferences_from_mapping(payload)
    except ValidationError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        return 1
        
    tracker.start_timer("data_ingestion")
    try:
        restaurants = load_restaurants(limit=args.limit)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to load dataset: {exc}", file=sys.stderr)
        return 1
    tracker.stop_timer("data_ingestion")
    tracker.record_count("total_restaurants_loaded", len(restaurants))

    tracker.start_timer("integration_filtering")
    integration_result = build_integration_output(restaurants, preferences, top_n=args.top_n)
    candidates = integration_result["candidates"]
    tracker.stop_timer("integration_filtering")
    tracker.record_count("candidates_after_filtering", len(candidates))
    
    if not candidates:
        print(render_empty_state("no_candidates"))
        tracker.stop_timer("total_runtime")
        tracker.flush()
        return 0

    tracker.start_timer("llm_recommendation")
    try:
        rankings = recommend_with_groq(integration_result["prompt_payload"], candidates, top_n=args.top_n)
    except ImportError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    tracker.stop_timer("llm_recommendation")
    tracker.record_count("final_recommendations", len(rankings))
        
    print(render_recommendations(rankings))
    
    tracker.stop_timer("total_runtime")
    tracker.flush()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="milestone1",
        description="CLI diagnostics for ZomatoUseCase milestone 1.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("info", help="Print milestone and environment overview.")
    subparsers.add_parser("doctor", help="Run setup and environment checks.")
    ingest_parser = subparsers.add_parser("ingest-smoke", help="Smoke test ingestion and canonical mapping.")
    ingest_parser.add_argument("--limit", type=int, default=5, help="Max restaurants to load.")
    ingest_parser.add_argument("--split", default="train", help="Dataset split to use (default: train).")
    ingest_parser.add_argument("--dataset-id", default=None, help="Override dataset id.")
    ingest_parser.add_argument("--revision", default=None, help="Override dataset revision.")
    prefs_parser = subparsers.add_parser("prefs-parse", help="Parse and validate user preferences.")
    prefs_parser.add_argument("--location", required=True, help="Preferred city/locality.")
    prefs_parser.add_argument(
        "--budget-band",
        default="medium",
        help="Budget band: low|medium|high (default: medium).",
    )
    prefs_parser.add_argument(
        "--cuisines",
        default="",
        help="Cuisine list as comma-separated text (example: Italian,Chinese).",
    )
    prefs_parser.add_argument(
        "--minimum-rating",
        default=0.0,
        type=float,
        help="Minimum rating between 0 and 5 (default: 0).",
    )
    prefs_parser.add_argument(
        "--additional-preferences",
        default="",
        help="Optional additional user preferences.",
    )
    prefs_parser.add_argument(
        "--validate-location-from-dataset",
        action="store_true",
        help="Enable location validation using ingested dataset locations.",
    )
    prefs_parser.add_argument(
        "--city-limit",
        default=5000,
        type=int,
        help="Rows to load when dataset location validation is enabled.",
    )
    
    prompt_parser = subparsers.add_parser("prompt-build", help="Build LLM prompt payload from user preferences.")
    prompt_parser.add_argument("--location", required=True, help="Preferred city/locality.")
    prompt_parser.add_argument("--budget-band", default="medium", help="Budget band: low|medium|high (default: medium).")
    prompt_parser.add_argument("--cuisines", default="", help="Cuisine list as comma-separated text.")
    prompt_parser.add_argument("--minimum-rating", default=0.0, type=float, help="Minimum rating between 0 and 5.")
    prompt_parser.add_argument("--additional-preferences", default="", help="Optional additional user preferences.")
    prompt_parser.add_argument("--limit", type=int, default=1000, help="Max restaurants to load for filtering.")
    prompt_parser.add_argument("--top-n", type=int, default=15, help="Number of candidates to include in the prompt.")
    
    recommend_parser = subparsers.add_parser("recommend", help="Run end-to-end LLM recommendation via Groq.")
    recommend_parser.add_argument("--location", required=True, help="Preferred city/locality.")
    recommend_parser.add_argument("--budget-band", default="medium", help="Budget band: low|medium|high (default: medium).")
    recommend_parser.add_argument("--cuisines", default="", help="Cuisine list as comma-separated text.")
    recommend_parser.add_argument("--minimum-rating", default=0.0, type=float, help="Minimum rating between 0 and 5.")
    recommend_parser.add_argument("--additional-preferences", default="", help="Optional additional user preferences.")
    recommend_parser.add_argument("--limit", type=int, default=1000, help="Max restaurants to load for filtering.")
    recommend_parser.add_argument("--top-n", type=int, default=5, help="Number of top recommendations to return (default: 5).")
    
    recommend_run_parser = subparsers.add_parser("recommend-run", help="Run end-to-end recommendation and render readable output with telemetry.")
    recommend_run_parser.add_argument("--location", required=True, help="Preferred city/locality.")
    recommend_run_parser.add_argument("--budget-band", default="medium", help="Budget band: low|medium|high (default: medium).")
    recommend_run_parser.add_argument("--cuisines", default="", help="Cuisine list as comma-separated text.")
    recommend_run_parser.add_argument("--minimum-rating", default=0.0, type=float, help="Minimum rating between 0 and 5.")
    recommend_run_parser.add_argument("--additional-preferences", default="", help="Optional additional user preferences.")
    recommend_run_parser.add_argument("--limit", type=int, default=1000, help="Max restaurants to load for filtering.")
    recommend_run_parser.add_argument("--top-n", type=int, default=5, help="Number of top recommendations to return (default: 5).")
    
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "info":
        return _handle_info()
    if args.command == "doctor":
        return _handle_doctor()
    if args.command == "ingest-smoke":
        return _handle_ingest_smoke(
            limit=args.limit,
            split=args.split,
            dataset_id=args.dataset_id,
            revision=args.revision,
        )
    if args.command == "prefs-parse":
        return _handle_prefs_parse(args)
    if args.command == "prompt-build":
        return _handle_prompt_build(args)
    if args.command == "recommend":
        return _handle_recommend(args)
    if args.command == "recommend-run":
        return _handle_recommend_run(args)

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
