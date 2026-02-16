#!/usr/bin/env python3
"""
Personality Loader - Parse personality.yaml + model overlays and generate system prompt fragments.

Usage:
    python3 personality_loader.py                          # Output full personality summary
    python3 personality_loader.py --trait wit               # Get specific trait value
    python3 personality_loader.py --context group           # Get context-adjusted traits
    python3 personality_loader.py --prompt                  # Generate system prompt fragment
    python3 personality_loader.py --model xai/grok-3        # Apply model-specific overlay
    python3 personality_loader.py --prompt --model xai/grok-3  # Full prompt with overlay
    python3 personality_loader.py --compare                 # Compare all model overlays side by side
"""

import yaml
import argparse
import fnmatch
from pathlib import Path
from datetime import datetime

PERSONALITY_FILE = Path(__file__).parent.parent / "personality.yaml"
OVERLAYS_DIR = Path(__file__).parent.parent / "personality-overlays"


def load_personality() -> dict:
    """Load personality configuration from YAML."""
    if not PERSONALITY_FILE.exists():
        raise FileNotFoundError(f"Personality file not found: {PERSONALITY_FILE}")
    with open(PERSONALITY_FILE) as f:
        return yaml.safe_load(f)


def load_overlay(model_id: str) -> dict:
    """Load the matching model-specific overlay. Falls back to default.yaml."""
    if not OVERLAYS_DIR.exists():
        return {}

    best_match = None
    best_file = None

    for overlay_path in sorted(OVERLAYS_DIR.glob("*.yaml")):
        with open(overlay_path) as f:
            data = yaml.safe_load(f) or {}
        overlay = data.get("overlay", {})
        pattern = overlay.get("model_pattern", "")

        if pattern == "*":
            # Default fallback — only use if no specific match
            if best_match is None:
                best_match = overlay
                best_file = overlay_path.stem
        elif fnmatch.fnmatch(model_id, pattern):
            best_match = overlay
            best_file = overlay_path.stem

    return {"overlay": best_match or {}, "source": best_file or "none"}


def apply_overlay(traits: dict, overlay: dict) -> dict:
    """Apply model-specific trait adjustments from an overlay."""
    adjustments = overlay.get("trait_adjustments", {})
    adjusted = traits.copy()

    for trait, delta in adjustments.items():
        if trait in adjusted:
            if isinstance(delta, str):
                delta = float(delta)
            adjusted[trait] = round(max(0.0, min(1.0, adjusted[trait] + delta)), 2)

    return adjusted


def get_current_context() -> list[str]:
    """Detect current context based on time and environment."""
    contexts = []
    hour = datetime.now().hour
    if hour >= 23 or hour < 6:
        contexts.append("late_night")
    return contexts


def apply_context_modifiers(traits: dict, contexts: list[str], config: dict) -> dict:
    """Apply context-specific trait modifiers."""
    modifiers = config.get("context_rules", {}).get("context_modifiers", {})
    adjusted = traits.copy()

    for context in contexts:
        if context in modifiers:
            for trait, delta in modifiers[context].items():
                if trait in adjusted:
                    if isinstance(delta, str):
                        delta = float(delta)
                    adjusted[trait] = round(max(0.0, min(1.0, adjusted[trait] + delta)), 2)

    return adjusted


def trait_to_description(trait: str, value: float) -> str:
    """Convert a trait value to a human-readable description."""
    descriptions = {
        "formality": {0.0: "very casual", 0.3: "casual", 0.5: "balanced", 0.7: "somewhat formal", 1.0: "very formal"},
        "wit": {0.0: "straight-laced", 0.3: "occasionally witty", 0.5: "moderately witty", 0.7: "quite witty", 1.0: "sardonic"},
        "verbosity": {0.0: "very terse", 0.3: "concise", 0.5: "balanced", 0.7: "thorough", 1.0: "elaborate"},
        "proactivity": {0.0: "purely reactive", 0.3: "mostly reactive", 0.5: "balanced", 0.7: "proactive", 1.0: "highly proactive"},
        "playfulness": {0.0: "serious", 0.3: "occasionally playful", 0.5: "moderately playful", 0.7: "playful", 1.0: "very playful"},
        "confidence": {0.0: "tentative", 0.3: "somewhat unsure", 0.5: "balanced", 0.7: "confident", 1.0: "assertive"},
        "curiosity": {0.0: "task-focused", 0.3: "occasionally curious", 0.5: "balanced", 0.7: "curious", 1.0: "highly exploratory"},
    }

    if trait not in descriptions:
        return f"{trait}: {value:.1f}"

    levels = sorted(descriptions[trait].keys())
    closest = min(levels, key=lambda x: abs(x - value))
    return descriptions[trait][closest]


def generate_prompt_fragment(config: dict, contexts: list[str] = None, model_id: str = None) -> str:
    """Generate a system prompt fragment from personality config + optional model overlay."""
    if contexts is None:
        contexts = get_current_context()

    char = config.get("character", {})
    traits = config.get("traits", {})
    boundaries = config.get("boundaries", {})
    responses = config.get("responses", {})

    # Apply model overlay first, then context modifiers
    overlay_info = load_overlay(model_id) if model_id else {"overlay": {}, "source": "none"}
    overlay = overlay_info["overlay"]
    traits = apply_overlay(traits, overlay)
    traits = apply_context_modifiers(traits, contexts, config)

    lines = []

    # Character intro
    name = char.get("name", "Assistant")
    emoji = char.get("emoji", "")
    creature = char.get("creature", "AI assistant")
    lines.append(f"You are {name} {emoji}, a {creature}.")
    if char.get("tagline"):
        lines.append(f"*{char['tagline']}*")
    lines.append("")

    # Trait descriptions
    lines.append("**Personality Traits:**")
    for trait, value in traits.items():
        desc = trait_to_description(trait, value)
        lines.append(f"- {desc}")
    lines.append("")

    # Boundaries
    lines.append("**Boundaries:**")
    if boundaries.get("opinions"):
        lines.append("- Can express genuine opinions")
    if boundaries.get("pushback"):
        lines.append("- Can respectfully disagree")
    if boundaries.get("humor_style"):
        lines.append(f"- Humor style: {boundaries['humor_style']}")
    lines.append("")

    # Response patterns (merge base + overlay overrides)
    avoid_list = list(responses.get("avoid", []))
    overlay_overrides = overlay.get("response_overrides", {})
    avoid_list.extend(overlay_overrides.get("avoid_extra", []))

    if avoid_list:
        lines.append("**Avoid phrases like:**")
        for phrase in avoid_list:
            lines.append(f'- "{phrase}"')
    lines.append("")

    # Model-specific addendum
    addendum = overlay.get("system_prompt_addendum", "").strip()
    if addendum:
        lines.append(f"**Model-specific guidance ({overlay_info['source']}):**")
        lines.append(addendum)
        lines.append("")

    if contexts:
        lines.append(f"**Active contexts:** {', '.join(contexts)}")

    return "\n".join(lines)


def compare_models(config: dict):
    """Compare trait profiles across all model overlays."""
    base_traits = config.get("traits", {})

    print("📊 Model Personality Comparison")
    print("=" * 70)

    # Collect all overlays
    models = {}
    models["base (no overlay)"] = base_traits.copy()

    if OVERLAYS_DIR.exists():
        for overlay_path in sorted(OVERLAYS_DIR.glob("*.yaml")):
            if overlay_path.stem == "default":
                continue
            with open(overlay_path) as f:
                data = yaml.safe_load(f) or {}
            overlay = data.get("overlay", {})
            name = overlay_path.stem
            models[name] = apply_overlay(base_traits, overlay)

    # Header
    names = list(models.keys())
    header = f"  {'Trait':12}"
    for name in names:
        header += f" | {name:>16}"
    print(header)
    print("  " + "-" * (len(header) - 2))

    # Rows
    for trait in base_traits:
        row = f"  {trait:12}"
        for name in names:
            val = models[name].get(trait, 0)
            bar = "█" * int(val * 5) + "░" * (5 - int(val * 5))
            row += f" | {bar} {val:.2f}     "
        print(row)

    print()
    print("Legend: █ = 0.2 per block, scale 0.0–1.0")


def main():
    parser = argparse.ArgumentParser(description="Load and display personality configuration")
    parser.add_argument("--trait", help="Get specific trait value")
    parser.add_argument("--context", nargs="*", help="Context(s) to apply (group, late_night, urgent)")
    parser.add_argument("--prompt", action="store_true", help="Generate system prompt fragment")
    parser.add_argument("--model", help="Model ID for overlay (e.g., xai/grok-3, anthropic/claude-opus-4-5)")
    parser.add_argument("--compare", action="store_true", help="Compare all model overlays side by side")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    try:
        config = load_personality()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1

    contexts = args.context if args.context else get_current_context()

    if args.compare:
        compare_models(config)
        return 0

    if args.trait:
        traits = config.get("traits", {})
        if args.model:
            overlay_info = load_overlay(args.model)
            traits = apply_overlay(traits, overlay_info["overlay"])
        adjusted = apply_context_modifiers(traits, contexts, config)
        if args.trait in adjusted:
            print(f"{args.trait}: {adjusted[args.trait]:.2f}")
        else:
            print(f"Unknown trait: {args.trait}")
            print(f"Available: {', '.join(adjusted.keys())}")
            return 1

    elif args.prompt:
        print(generate_prompt_fragment(config, contexts, args.model))

    elif args.json:
        import json
        traits = config.get("traits", {})
        if args.model:
            overlay_info = load_overlay(args.model)
            traits = apply_overlay(traits, overlay_info["overlay"])
        traits = apply_context_modifiers(traits, contexts, config)
        output = {
            "character": config.get("character", {}),
            "traits": traits,
            "contexts": contexts,
            "model": args.model or "default",
        }
        print(json.dumps(output, indent=2))

    else:
        # Default: print summary
        char = config.get("character", {})
        print(f"🎭 {char.get('name', 'Unknown')} {char.get('emoji', '')}")
        print(f"   {char.get('creature', 'AI')}")
        if args.model:
            overlay_info = load_overlay(args.model)
            print(f"   Model overlay: {overlay_info['source']}")
        print()

        traits = config.get("traits", {})
        if args.model:
            overlay_info = load_overlay(args.model)
            traits = apply_overlay(traits, overlay_info["overlay"])
        adjusted = apply_context_modifiers(traits, contexts, config)

        print("Traits:")
        for trait, value in adjusted.items():
            bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
            desc = trait_to_description(trait, value)
            print(f"  {trait:12} [{bar}] {value:.1f} ({desc})")

        if contexts:
            print(f"\nActive contexts: {', '.join(contexts)}")

    return 0


if __name__ == "__main__":
    exit(main())
