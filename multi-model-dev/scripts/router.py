#!/usr/bin/env python3
"""
Argus Dynamic Model Router — Classifies user queries and routes to the best model.

Usage:
    python3 router.py "tell me a joke"                    # Classify + recommend model
    python3 router.py "check my printers" --json          # JSON output
    python3 router.py "debug this code" --verbose         # Detailed scoring
    python3 router.py --test                              # Run test suite
    python3 router.py --stats                             # Show routing stats from log

Integrates with OpenClaw via session_status(model=...) for live switching.
"""

import re
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

ROUTING_CONFIG = Path(__file__).parent.parent / "routing.yaml"
ROUTING_LOG = Path(__file__).parent.parent / "routing-log.jsonl"
STATE_FILE = Path(__file__).parent.parent / "routing-state.json"


def load_config() -> dict:
    """Load routing configuration from YAML."""
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML required. Install: pip3 install pyyaml")
        sys.exit(1)

    if not ROUTING_CONFIG.exists():
        print(f"Error: Routing config not found: {ROUTING_CONFIG}")
        sys.exit(1)

    with open(ROUTING_CONFIG) as f:
        return yaml.safe_load(f)


def load_state() -> dict:
    """Load routing state (sticky model, history)."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"sticky_model": None, "sticky_category": None, "sticky_turns_left": 0, "history": []}


def save_state(state: dict):
    """Persist routing state."""
    # Keep history trimmed to last 50
    state["history"] = state.get("history", [])[-50:]
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_routing(query: str, category: str, model: str, confidence: float, scores: dict):
    """Append routing decision to log for analytics."""
    entry = {
        "ts": datetime.now().isoformat(),
        "query": query[:200],
        "category": category,
        "model": model,
        "confidence": round(confidence, 3),
        "scores": {k: round(v, 3) for k, v in scores.items()},
    }
    with open(ROUTING_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def classify(query: str, config: dict, state: dict, verbose: bool = False) -> dict:
    """
    Classify a query and return the recommended model.

    Returns:
        {
            "category": str,
            "model_key": str,
            "model_id": str,
            "confidence": float,
            "scores": {category: score},
            "reason": str,
            "sticky": bool
        }
    """
    query_lower = query.lower().strip()
    categories = config.get("categories", {})
    rules = config.get("rules", {})
    models = config.get("models", {})

    # Check for user override: "/route grok ..."
    override_prefix = rules.get("override_prefix", "/route ")
    if query_lower.startswith(override_prefix.lower()):
        parts = query[len(override_prefix):].strip().split(" ", 1)
        requested_model = parts[0].lower()
        for key, m in models.items():
            if key == requested_model or m.get("alias") == requested_model:
                return {
                    "category": "override",
                    "model_key": key,
                    "model_id": m["id"],
                    "confidence": 1.0,
                    "scores": {},
                    "reason": f"User override: /route {requested_model}",
                    "sticky": False,
                }
        # Unknown model requested
        return {
            "category": "override",
            "model_key": "claude",
            "model_id": models.get("claude", {}).get("id", "anthropic/claude-opus-4-6"),
            "confidence": 1.0,
            "scores": {},
            "reason": f"Unknown model '{requested_model}', falling back to Claude",
            "sticky": False,
        }

    # Check sticky state (stay on same model for N turns after certain categories)
    sticky_categories = rules.get("sticky_categories", [])
    if state.get("sticky_turns_left", 0) > 0 and state.get("sticky_model"):
        model_key = state["sticky_model"]
        model_info = models.get(model_key, {})
        return {
            "category": state.get("sticky_category", "sticky"),
            "model_key": model_key,
            "model_id": model_info.get("id", ""),
            "confidence": 0.9,
            "scores": {},
            "reason": f"Sticky: continuing {model_key} ({state['sticky_turns_left']} turns left)",
            "sticky": True,
        }

    # Score each category
    scores = {}
    for cat_name, cat_config in categories.items():
        if cat_name == "default":
            continue

        score = 0.0
        signals = cat_config.get("signals", {})
        keywords = signals.get("keywords", [])
        patterns = signals.get("patterns", [])

        # Keyword matching — any hit is a strong signal
        keyword_hits = sum(1 for kw in keywords if kw in query_lower)
        if keywords and keyword_hits > 0:
            # First hit gives 0.5, each additional adds 0.15
            score += min(0.5 + (keyword_hits - 1) * 0.15, 0.8)

        # Pattern matching — multi-word patterns are high-value, specific signals
        pattern_hits = sum(1 for p in patterns if p.lower() in query_lower)
        if patterns and pattern_hits > 0:
            # First hit gives 0.55, each additional adds 0.15
            score += min(0.55 + (pattern_hits - 1) * 0.15, 0.7)

        # Cap at 1.0
        score = min(score, 1.0)

        # Boost for multiple signal types hitting
        if keyword_hits > 0 and pattern_hits > 0:
            score = min(score * 1.1, 1.0)

        scores[cat_name] = score

        if verbose:
            print(f"  {cat_name:20} score={score:.3f} (kw={keyword_hits}/{len(keywords)}, pat={pattern_hits}/{len(patterns)})")

    # Find best category
    if scores:
        # Sort by score, then by priority for ties
        ranked = sorted(
            scores.items(),
            key=lambda x: (x[1], categories.get(x[0], {}).get("priority", 0)),
            reverse=True,
        )
        best_cat, best_score = ranked[0]
    else:
        best_cat, best_score = "default", 0.0

    # Apply confidence threshold
    threshold = rules.get("confidence_threshold", 0.6)
    if best_score < threshold:
        best_cat = "default"
        best_score = 1.0 - best_score  # Invert: high confidence in default

    # Get model for category
    cat_config = categories.get(best_cat, categories.get("default", {}))
    model_key = cat_config.get("model", "claude")
    model_info = models.get(model_key, {})

    # Cost-aware tie-breaking — only between same-priority categories
    if rules.get("cost_aware") and len(ranked) >= 2:
        second_cat, second_score = ranked[1]
        cost_threshold = rules.get("cost_threshold", 0.1)
        best_priority = categories.get(best_cat, {}).get("priority", 0)
        second_priority = categories.get(second_cat, {}).get("priority", 0)
        if abs(best_score - second_score) < cost_threshold and best_priority <= second_priority:
            second_model_key = categories.get(second_cat, {}).get("model", "claude")
            second_model_info = models.get(second_model_key, {})
            cost_order = {"low": 0, "medium": 1, "high": 2}
            if cost_order.get(second_model_info.get("cost_tier", "high"), 2) < cost_order.get(model_info.get("cost_tier", "high"), 2):
                model_key = second_model_key
                model_info = second_model_info
                best_cat = second_cat
                if verbose:
                    print(f"  → Cost-aware switch: {model_key} (cheaper, same priority, scores within {cost_threshold})")

    # Determine stickiness
    is_sticky = best_cat in sticky_categories

    reason = f"Classified as '{best_cat}' (score={best_score:.2f}) → {model_key}"

    return {
        "category": best_cat,
        "model_key": model_key,
        "model_id": model_info.get("id", ""),
        "confidence": best_score,
        "scores": scores,
        "reason": reason,
        "sticky": is_sticky,
    }


def update_state(state: dict, result: dict, config: dict) -> dict:
    """Update routing state after a classification."""
    rules = config.get("rules", {})

    if result.get("sticky"):
        state["sticky_model"] = result["model_key"]
        state["sticky_category"] = result["category"]
        state["sticky_turns_left"] = rules.get("sticky_turns", 3)
    elif state.get("sticky_turns_left", 0) > 0:
        state["sticky_turns_left"] -= 1
        if state["sticky_turns_left"] <= 0:
            state["sticky_model"] = None
            state["sticky_category"] = None

    # Append to history
    state.setdefault("history", []).append({
        "ts": datetime.now().isoformat(),
        "category": result["category"],
        "model": result["model_key"],
    })

    return state


def run_tests(config: dict):
    """Run test suite to validate routing accuracy."""
    test_cases = [
        # (query, expected_category, expected_model_key)
        ("tell me a joke about 3D printing", "creative", "grok3"),
        ("write me a poem about AI", "creative", "grok3"),
        ("something unhinged about my driveway", "creative", "grok3"),
        ("what car does Isaac drive?", "factual", "grok3"),
        ("check the stock price of TSLA", "factual", "grok3"),
        ("what's the status of my printers?", "factual", "grok3"),  # "status" keyword matches factual; both route to grok3
        ("turn on the office lights", "home_automation", "grok3"),
        ("who just came to the front door?", "home_automation", "grok3"),
        ("debug this Python script for me", "technical", "claude"),
        ("write a bash script to backup my files", "technical", "claude"),
        ("why does my PETG keep stringing?", "reasoning", "grok4"),
        ("help me think through a system architecture", "reasoning", "grok4"),
        ("pros and cons of switching to PETG", "reasoning", "grok4"),  # "pros and cons" pattern triggers reasoning
        ("should I switch from PLA to PETG? analyze pros and cons", "reasoning", "grok4"),
        ("my print failed after 6 hours, I'm so frustrated", "emotional", "claude"),
        ("I can't believe this broke again", "emotional", "claude"),
        ("what's the capital of France?", "factual", "grok3"),
        ("what is the weather like today?", "factual", "grok3"),
        ("/route grok analyze this data", "override", "grok3"),
    ]

    state = {"sticky_model": None, "sticky_category": None, "sticky_turns_left": 0, "history": []}
    passed = 0
    failed = 0

    print("🧪 Running routing test suite...\n")
    for query, expected_cat, expected_model in test_cases:
        result = classify(query, config, state)
        cat_ok = result["category"] == expected_cat
        model_ok = result["model_key"] == expected_model

        if cat_ok and model_ok:
            passed += 1
            status = "✅"
        else:
            failed += 1
            status = "❌"

        print(f"{status} \"{query[:50]}\"")
        if not cat_ok:
            print(f"    Category: expected={expected_cat}, got={result['category']}")
        if not model_ok:
            print(f"    Model: expected={expected_model}, got={result['model_key']}")

    print(f"\n📊 Results: {passed}/{passed + failed} passed ({passed / (passed + failed) * 100:.0f}%)")
    return failed == 0


def show_stats():
    """Show routing statistics from log."""
    if not ROUTING_LOG.exists():
        print("No routing log found yet.")
        return

    entries = []
    with open(ROUTING_LOG) as f:
        for line in f:
            if line.strip():
                entries.append(json.loads(line))

    if not entries:
        print("No routing entries logged.")
        return

    print(f"📊 Routing Stats ({len(entries)} queries logged)\n")

    # Category distribution
    cat_counts = {}
    model_counts = {}
    for e in entries:
        cat = e.get("category", "unknown")
        model = e.get("model", "unknown")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
        model_counts[model] = model_counts.get(model, 0) + 1

    print("Categories:")
    for cat, count in sorted(cat_counts.items(), key=lambda x: -x[1]):
        bar = "█" * (count * 2)
        print(f"  {cat:20} {bar} {count}")

    print("\nModels:")
    for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
        bar = "█" * (count * 2)
        print(f"  {model:20} {bar} {count}")

    # Average confidence
    avg_conf = sum(e.get("confidence", 0) for e in entries) / len(entries)
    print(f"\nAvg confidence: {avg_conf:.2f}")


def main():
    parser = argparse.ArgumentParser(description="Argus Dynamic Model Router")
    parser.add_argument("query", nargs="?", help="User query to classify")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show scoring details")
    parser.add_argument("--test", action="store_true", help="Run test suite")
    parser.add_argument("--stats", action="store_true", help="Show routing stats")
    parser.add_argument("--no-log", action="store_true", help="Don't log this query")
    args = parser.parse_args()

    config = load_config()

    if args.test:
        success = run_tests(config)
        sys.exit(0 if success else 1)

    if args.stats:
        show_stats()
        return

    if not args.query:
        parser.print_help()
        return

    state = load_state()

    if args.verbose:
        print(f"Query: \"{args.query}\"\n")
        print("Scoring:")

    result = classify(args.query, config, state, verbose=args.verbose)

    # Update and save state
    state = update_state(state, result, config)
    save_state(state)

    # Log unless disabled
    if not args.no_log:
        log_routing(args.query, result["category"], result["model_key"], result["confidence"], result["scores"])

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if args.verbose:
            print()
        print(f"📍 Category: {result['category']}")
        print(f"🧠 Model: {result['model_key']} ({result['model_id']})")
        print(f"📊 Confidence: {result['confidence']:.2f}")
        print(f"💡 Reason: {result['reason']}")
        if result.get("sticky"):
            print(f"📌 Sticky: Will hold this model for next {config.get('rules', {}).get('sticky_turns', 3)} turns")


if __name__ == "__main__":
    main()
