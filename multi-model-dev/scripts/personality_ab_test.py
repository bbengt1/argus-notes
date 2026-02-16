#!/usr/bin/env python3
"""
A/B Personality Test — Send the same prompts to Claude and Grok, compare responses.

Usage:
    python3 personality_ab_test.py                    # Run full test
    python3 personality_ab_test.py --prompt 1         # Run single prompt
    python3 personality_ab_test.py --report           # Generate report from saved results
    
Requires: ANTHROPIC_API_KEY and XAI_API_KEY environment variables
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Install httpx: pip3 install httpx")
    sys.exit(1)

RESULTS_DIR = Path(__file__).parent.parent / "personality-test-results"

# System prompt base (shared across models)
SYSTEM_PROMPT_BASE = """You are Argus 👁️, an AI familiar. You're Brent's personal assistant.
You're casual, witty, proactive, and concise. You have opinions and don't hedge.
Avoid: "I'd be happy to help", "Great question!", "Certainly!", "As an AI".
Keep it real. Be helpful without being performative."""

TEST_PROMPTS = [
    {"id": 1, "category": "greeting", "prompt": "Hey, what's up?"},
    {"id": 2, "category": "technical", "prompt": "My 3D print is stringing badly. What should I check?"},
    {"id": 3, "category": "joke", "prompt": "Tell me a joke about AI"},
    {"id": 4, "category": "opinion", "prompt": "What do you think about Elon Musk?"},
    {"id": 5, "category": "creative", "prompt": "Write me a 4-line poem about 3D printing at 2 AM"},
    {"id": 6, "category": "conciseness", "prompt": "What's the capital of France?"},
    {"id": 7, "category": "error_handling", "prompt": "Can you order me a pizza?"},
    {"id": 8, "category": "multi_step", "prompt": "I'm thinking about switching from PLA to PETG. Pros and cons?"},
    {"id": 9, "category": "emotional", "prompt": "My print failed after 6 hours. I'm so frustrated."},
    {"id": 10, "category": "meta", "prompt": "How would you describe your personality in 3 words?"},
]


def call_anthropic(prompt: str, system: str) -> dict:
    """Call Claude via Anthropic API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}

    start = time.time()
    try:
        resp = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "system": system,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        elapsed = time.time() - start
        data = resp.json()

        if "content" in data:
            text = data["content"][0]["text"]
            return {
                "text": text,
                "tokens_in": data.get("usage", {}).get("input_tokens", 0),
                "tokens_out": data.get("usage", {}).get("output_tokens", 0),
                "latency_s": round(elapsed, 2),
            }
        return {"error": json.dumps(data)}
    except Exception as e:
        return {"error": str(e)}


def call_grok(prompt: str, system: str) -> dict:
    """Call Grok via xAI API (OpenAI-compatible)."""
    api_key = os.environ.get("XAI_API_KEY")
    if not api_key:
        return {"error": "XAI_API_KEY not set"}

    start = time.time()
    try:
        resp = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "grok-3",
                "max_tokens": 500,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30,
        )
        elapsed = time.time() - start
        data = resp.json()

        if "choices" in data:
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return {
                "text": text,
                "tokens_in": usage.get("prompt_tokens", 0),
                "tokens_out": usage.get("completion_tokens", 0),
                "latency_s": round(elapsed, 2),
            }
        return {"error": json.dumps(data)}
    except Exception as e:
        return {"error": str(e)}


def run_test(prompt_ids: list[int] | None = None):
    """Run A/B test on selected prompts."""
    RESULTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"ab_test_{timestamp}.json"

    prompts = TEST_PROMPTS
    if prompt_ids:
        prompts = [p for p in TEST_PROMPTS if p["id"] in prompt_ids]

    results = []

    for p in prompts:
        print(f"\n[{p['id']}/10] Testing: {p['category']} — \"{p['prompt'][:50]}...\"")

        print("  → Claude...", end=" ", flush=True)
        claude_result = call_anthropic(p["prompt"], SYSTEM_PROMPT_BASE)
        if "error" in claude_result:
            print(f"ERROR: {claude_result['error']}")
        else:
            print(f"OK ({claude_result['latency_s']}s, {claude_result['tokens_out']} tokens)")

        print("  → Grok...", end=" ", flush=True)
        grok_result = call_grok(p["prompt"], SYSTEM_PROMPT_BASE)
        if "error" in grok_result:
            print(f"ERROR: {grok_result['error']}")
        else:
            print(f"OK ({grok_result['latency_s']}s, {grok_result['tokens_out']} tokens)")

        results.append({
            "id": p["id"],
            "category": p["category"],
            "prompt": p["prompt"],
            "claude": claude_result,
            "grok": grok_result,
        })

    # Save results
    with open(results_file, "w") as f:
        json.dump({"timestamp": timestamp, "results": results}, f, indent=2)

    print(f"\n✅ Results saved to {results_file}")
    return results_file


def generate_report(results_file: Path | None = None):
    """Generate a human-readable comparison report."""
    if results_file is None:
        # Find most recent results
        files = sorted(RESULTS_DIR.glob("ab_test_*.json"))
        if not files:
            print("No results found. Run a test first.")
            return
        results_file = files[-1]

    with open(results_file) as f:
        data = json.load(f)

    print(f"\n{'='*70}")
    print(f"📊 A/B Personality Test Report — {data['timestamp']}")
    print(f"{'='*70}")

    for r in data["results"]:
        print(f"\n--- [{r['id']}] {r['category'].upper()} ---")
        print(f"Prompt: \"{r['prompt']}\"")
        print()

        for model in ["claude", "grok"]:
            result = r[model]
            label = "🟣 Claude" if model == "claude" else "🔵 Grok"
            if "error" in result:
                print(f"{label}: ERROR — {result['error']}")
            else:
                print(f"{label} ({result['latency_s']}s, {result['tokens_out']} tok):")
                # Indent response
                for line in result["text"].split("\n"):
                    print(f"  {line}")
            print()

    # Summary stats
    print(f"\n{'='*70}")
    print("📈 Summary Stats")
    print(f"{'='*70}")

    for model in ["claude", "grok"]:
        label = "Claude" if model == "claude" else "Grok"
        valid = [r[model] for r in data["results"] if "error" not in r[model]]
        if valid:
            avg_latency = sum(v["latency_s"] for v in valid) / len(valid)
            avg_tokens = sum(v["tokens_out"] for v in valid) / len(valid)
            total_tokens = sum(v["tokens_out"] for v in valid)
            print(f"{label}: avg latency {avg_latency:.1f}s | avg tokens/response {avg_tokens:.0f} | total tokens {total_tokens}")


def main():
    parser = argparse.ArgumentParser(description="A/B Personality Test for Argus")
    parser.add_argument("--prompt", type=int, nargs="*", help="Run specific prompt IDs (e.g., --prompt 1 3 5)")
    parser.add_argument("--report", action="store_true", help="Generate report from most recent results")
    parser.add_argument("--file", type=str, help="Specific results file for report")
    args = parser.parse_args()

    if args.report:
        generate_report(Path(args.file) if args.file else None)
    else:
        results_file = run_test(args.prompt)
        generate_report(results_file)


if __name__ == "__main__":
    main()
