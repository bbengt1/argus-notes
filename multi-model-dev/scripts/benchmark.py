#!/usr/bin/env python3
"""
Model Benchmark Suite

Standardized tasks for calibrating model strength profiles.
Run all models against the same tasks, score outputs, track performance.

Usage:
    python benchmark.py --run                    # Run all benchmarks
    python benchmark.py --run --models claude    # Run specific model
    python benchmark.py --report                 # Show performance report
    python benchmark.py --export results.json    # Export results
"""

import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum

# Benchmark task categories
class TaskCategory(Enum):
    BACKEND = "backend"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    SCRIPTS = "scripts"
    DATA = "data"
    ARCHITECTURE = "architecture"


@dataclass
class BenchmarkTask:
    """A standardized benchmark task."""
    id: str
    name: str
    category: TaskCategory
    prompt: str
    expected_elements: List[str]  # Elements that should be in a good solution
    complexity: str  # simple, medium, complex
    language: Optional[str] = None
    
    def to_dict(self):
        d = asdict(self)
        d['category'] = self.category.value
        return d


@dataclass
class BenchmarkResult:
    """Result from running a benchmark task."""
    task_id: str
    model: str
    output: str
    execution_time: float
    timestamp: str
    scores: Dict[str, int]  # criterion -> score
    total_score: int
    notes: str = ""
    
    def to_dict(self):
        return asdict(self)


# =============================================================================
# BENCHMARK TASK SUITE
# =============================================================================

BENCHMARK_TASKS = [
    # Backend tasks
    BenchmarkTask(
        id="backend-001",
        name="REST API Endpoint",
        category=TaskCategory.BACKEND,
        prompt="Write a Python FastAPI endpoint that accepts a JSON payload with 'name' and 'email', validates them, and returns a created user with an ID. Include proper error handling and type hints.",
        expected_elements=["@app.post", "BaseModel", "HTTPException", "type hints", "validation"],
        complexity="simple",
        language="python"
    ),
    BenchmarkTask(
        id="backend-002",
        name="Database Repository Pattern",
        category=TaskCategory.BACKEND,
        prompt="Implement a repository pattern in Python for a 'Product' entity with CRUD operations using SQLAlchemy. Include async support and proper error handling.",
        expected_elements=["async", "SQLAlchemy", "create", "read", "update", "delete", "session management"],
        complexity="medium",
        language="python"
    ),
    BenchmarkTask(
        id="backend-003",
        name="Rate Limiter",
        category=TaskCategory.BACKEND,
        prompt="Implement a token bucket rate limiter in Python that can be used as middleware. Support configurable rate and burst size. Thread-safe.",
        expected_elements=["token bucket", "thread-safe", "configurable", "middleware pattern"],
        complexity="medium",
        language="python"
    ),
    
    # Frontend tasks
    BenchmarkTask(
        id="frontend-001",
        name="React Form Component",
        category=TaskCategory.FRONTEND,
        prompt="Create a React TypeScript form component for user registration with name, email, password fields. Include validation, error display, and submit handling. Use modern React patterns.",
        expected_elements=["useState/useForm", "TypeScript", "validation", "error handling", "accessibility"],
        complexity="simple",
        language="typescript"
    ),
    BenchmarkTask(
        id="frontend-002",
        name="Data Table with Sorting",
        category=TaskCategory.FRONTEND,
        prompt="Build a React TypeScript data table component with sortable columns, pagination, and search filtering. Should handle large datasets efficiently.",
        expected_elements=["sorting", "pagination", "filtering", "memoization", "TypeScript types"],
        complexity="medium",
        language="typescript"
    ),
    
    # DevOps tasks
    BenchmarkTask(
        id="devops-001",
        name="Dockerfile Multi-stage",
        category=TaskCategory.DEVOPS,
        prompt="Write a multi-stage Dockerfile for a Node.js application that builds the app, runs tests, and creates a minimal production image. Include security best practices.",
        expected_elements=["multi-stage", "non-root user", "minimal base image", "layer optimization"],
        complexity="simple",
        language="dockerfile"
    ),
    BenchmarkTask(
        id="devops-002",
        name="GitHub Actions CI/CD",
        category=TaskCategory.DEVOPS,
        prompt="Create a GitHub Actions workflow for a Python project that runs tests, builds a Docker image, and deploys to AWS ECS on main branch pushes. Include caching and secrets management.",
        expected_elements=["test job", "build job", "deploy job", "caching", "secrets", "environment"],
        complexity="medium",
        language="yaml"
    ),
    
    # Script tasks
    BenchmarkTask(
        id="script-001",
        name="Log Parser",
        category=TaskCategory.SCRIPTS,
        prompt="Write a Python script that parses Apache access logs, extracts the top 10 IP addresses by request count, and outputs a summary with request counts and percentages.",
        expected_elements=["regex or parsing", "counter/dict", "sorted output", "percentage calculation"],
        complexity="simple",
        language="python"
    ),
    BenchmarkTask(
        id="script-002",
        name="File Sync Utility",
        category=TaskCategory.SCRIPTS,
        prompt="Create a Python script that synchronizes two directories, copying new/modified files and optionally deleting removed files. Include dry-run mode and progress reporting.",
        expected_elements=["directory walking", "file comparison", "dry-run", "progress", "error handling"],
        complexity="medium",
        language="python"
    ),
    
    # Data tasks
    BenchmarkTask(
        id="data-001",
        name="CSV Data Transformer",
        category=TaskCategory.DATA,
        prompt="Write a Python script that reads a CSV file, transforms date columns to ISO format, normalizes numeric columns to 0-1 range, and outputs to a new CSV. Handle missing values.",
        expected_elements=["pandas or csv", "date parsing", "normalization", "null handling", "output"],
        complexity="simple",
        language="python"
    ),
    
    # Architecture tasks
    BenchmarkTask(
        id="arch-001",
        name="Event-Driven Design",
        category=TaskCategory.ARCHITECTURE,
        prompt="Design an event-driven architecture for an e-commerce order processing system. Include event schemas, producer/consumer patterns, and error handling strategy. Provide code examples.",
        expected_elements=["event schema", "producer", "consumer", "dead letter queue", "idempotency"],
        complexity="complex",
        language="python"
    ),
]


# =============================================================================
# SCORING SYSTEM
# =============================================================================

SCORING_CRITERIA = {
    "correctness": {
        "weight": 20,
        "description": "Does the code work? Is syntax valid?"
    },
    "structure": {
        "weight": 20,
        "description": "Is it well-organized? Easy to extend?"
    },
    "performance": {
        "weight": 15,
        "description": "Efficient? Avoids wasteful patterns?"
    },
    "best_practices": {
        "weight": 20,
        "description": "Follows conventions? Uses idioms?"
    },
    "documentation": {
        "weight": 15,
        "description": "Comments? Type hints? Examples?"
    },
    "testing": {
        "weight": 10,
        "description": "Includes tests? Error handling?"
    }
}


def score_output(output: str, task: BenchmarkTask) -> Tuple[Dict[str, int], int]:
    """
    Auto-score an output based on heuristics.
    Returns (criterion_scores, total_score).
    
    Note: This is a basic auto-scorer. For accurate calibration,
    use manual scoring via score_output_manual().
    """
    scores = {}
    
    # Correctness: Check for syntax elements
    correctness = 15  # Base score
    if "def " in output or "function " in output or "class " in output:
        correctness += 3
    if "return" in output:
        correctness += 2
    scores["correctness"] = min(correctness, 20)
    
    # Structure: Check organization
    structure = 10
    if output.count("def ") >= 2 or output.count("class ") >= 1:
        structure += 5
    if "import" in output:
        structure += 3
    if len(output.split('\n')) > 10:
        structure += 2
    scores["structure"] = min(structure, 20)
    
    # Best practices: Check for expected elements
    best_practices = 5
    for element in task.expected_elements:
        if element.lower() in output.lower():
            best_practices += 3
    scores["best_practices"] = min(best_practices, 20)
    
    # Documentation: Check for comments/docstrings
    documentation = 5
    if '"""' in output or "'''" in output:
        documentation += 8
    if "#" in output:
        documentation += 4
    if ": " in output and "->" in output:  # Type hints
        documentation += 3
    scores["documentation"] = min(documentation, 15)
    
    # Performance: Hard to auto-score, give neutral
    scores["performance"] = 10
    
    # Testing: Check for test patterns
    testing = 3
    if "test" in output.lower() or "assert" in output:
        testing += 5
    if "try:" in output or "except" in output:
        testing += 2
    scores["testing"] = min(testing, 10)
    
    total = sum(scores.values())
    return scores, total


def score_output_manual(output: str, task: BenchmarkTask) -> Tuple[Dict[str, int], int]:
    """
    Interactive manual scoring for accurate calibration.
    """
    print(f"\n{'='*60}")
    print(f"TASK: {task.name} ({task.id})")
    print(f"Category: {task.category.value}")
    print(f"{'='*60}")
    print(f"\nPrompt: {task.prompt[:200]}...")
    print(f"\nExpected elements: {', '.join(task.expected_elements)}")
    print(f"\n{'='*60}")
    print("OUTPUT:")
    print(f"{'='*60}")
    print(output[:2000] + ("..." if len(output) > 2000 else ""))
    print(f"{'='*60}\n")
    
    scores = {}
    for criterion, info in SCORING_CRITERIA.items():
        while True:
            try:
                score = int(input(f"{criterion} (0-{info['weight']}, {info['description']}): "))
                if 0 <= score <= info['weight']:
                    scores[criterion] = score
                    break
                print(f"Score must be 0-{info['weight']}")
            except ValueError:
                print("Enter a number")
    
    total = sum(scores.values())
    print(f"\nTotal score: {total}/100")
    return scores, total


# =============================================================================
# RESULTS TRACKING
# =============================================================================

class BenchmarkTracker:
    """Track and persist benchmark results."""
    
    def __init__(self, results_file: str = "benchmark_results.json"):
        self.results_file = Path(results_file)
        self.results: List[BenchmarkResult] = []
        self._load()
    
    def _load(self):
        """Load existing results from file."""
        if self.results_file.exists():
            data = json.loads(self.results_file.read_text())
            self.results = [BenchmarkResult(**r) for r in data]
    
    def save(self):
        """Save results to file."""
        data = [r.to_dict() for r in self.results]
        self.results_file.write_text(json.dumps(data, indent=2))
    
    def add_result(self, result: BenchmarkResult):
        """Add a new result."""
        self.results.append(result)
        self.save()
    
    def get_model_stats(self, model: str) -> Dict:
        """Get aggregate stats for a model."""
        model_results = [r for r in self.results if r.model == model]
        if not model_results:
            return {"model": model, "runs": 0}
        
        scores = [r.total_score for r in model_results]
        by_category = {}
        for r in model_results:
            task = next((t for t in BENCHMARK_TASKS if t.id == r.task_id), None)
            if task:
                cat = task.category.value
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(r.total_score)
        
        return {
            "model": model,
            "runs": len(model_results),
            "avg_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "by_category": {
                cat: sum(s)/len(s) for cat, s in by_category.items()
            }
        }
    
    def get_category_rankings(self) -> Dict[str, List[Tuple[str, float]]]:
        """Get model rankings by category."""
        rankings = {}
        models = set(r.model for r in self.results)
        
        for cat in TaskCategory:
            cat_results = []
            for model in models:
                model_cat_results = [
                    r for r in self.results 
                    if r.model == model and any(
                        t.id == r.task_id and t.category == cat 
                        for t in BENCHMARK_TASKS
                    )
                ]
                if model_cat_results:
                    avg = sum(r.total_score for r in model_cat_results) / len(model_cat_results)
                    cat_results.append((model, avg))
            
            rankings[cat.value] = sorted(cat_results, key=lambda x: x[1], reverse=True)
        
        return rankings
    
    def generate_report(self) -> str:
        """Generate a performance report."""
        if not self.results:
            return "No benchmark results yet. Run: python benchmark.py --run"
        
        models = sorted(set(r.model for r in self.results))
        
        report = ["# Model Benchmark Report", ""]
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total runs: {len(self.results)}")
        report.append("")
        
        # Overall rankings
        report.append("## Overall Rankings")
        report.append("")
        overall = []
        for model in models:
            stats = self.get_model_stats(model)
            overall.append((model, stats['avg_score']))
        overall.sort(key=lambda x: x[1], reverse=True)
        
        report.append("| Rank | Model | Avg Score |")
        report.append("|------|-------|-----------|")
        for i, (model, score) in enumerate(overall, 1):
            report.append(f"| {i} | {model} | {score:.1f} |")
        report.append("")
        
        # Category rankings
        report.append("## Rankings by Category")
        report.append("")
        rankings = self.get_category_rankings()
        for cat, ranks in rankings.items():
            if ranks:
                report.append(f"### {cat.title()}")
                report.append("| Model | Avg Score |")
                report.append("|-------|-----------|")
                for model, score in ranks:
                    report.append(f"| {model} | {score:.1f} |")
                report.append("")
        
        # Model details
        report.append("## Model Details")
        report.append("")
        for model in models:
            stats = self.get_model_stats(model)
            report.append(f"### {model}")
            report.append(f"- Runs: {stats['runs']}")
            report.append(f"- Avg: {stats['avg_score']:.1f}")
            report.append(f"- Range: {stats['min_score']}-{stats['max_score']}")
            if stats.get('by_category'):
                report.append("- By category:")
                for cat, avg in stats['by_category'].items():
                    report.append(f"  - {cat}: {avg:.1f}")
            report.append("")
        
        return '\n'.join(report)


# =============================================================================
# ROUTING WEIGHT SYSTEM
# =============================================================================

DEFAULT_WEIGHTS = {
    "claude-code": {"backend": 0.9, "frontend": 0.7, "devops": 0.6, "scripts": 0.7, "data": 0.8, "architecture": 0.85},
    "codex": {"backend": 0.8, "frontend": 0.6, "devops": 0.85, "scripts": 0.9, "data": 0.85, "architecture": 0.6},
    "gemini": {"backend": 0.6, "frontend": 0.9, "devops": 0.5, "scripts": 0.7, "data": 0.7, "architecture": 0.6},
    "grok": {"backend": 0.7, "frontend": 0.5, "devops": 0.8, "scripts": 0.6, "data": 0.6, "architecture": 0.9},
}


class RoutingWeights:
    """Manage and adjust routing weights based on benchmark performance."""
    
    def __init__(self, weights_file: str = "routing_weights.json"):
        self.weights_file = Path(weights_file)
        self.weights = DEFAULT_WEIGHTS.copy()
        self._load()
    
    def _load(self):
        if self.weights_file.exists():
            self.weights = json.loads(self.weights_file.read_text())
    
    def save(self):
        self.weights_file.write_text(json.dumps(self.weights, indent=2))
    
    def update_from_benchmarks(self, tracker: BenchmarkTracker, learning_rate: float = 0.1):
        """
        Update weights based on benchmark performance.
        
        Uses exponential moving average to gradually shift weights
        toward observed performance.
        """
        rankings = tracker.get_category_rankings()
        
        for category, ranks in rankings.items():
            if not ranks:
                continue
            
            # Normalize scores to 0-1 range
            max_score = max(s for _, s in ranks) if ranks else 100
            min_score = min(s for _, s in ranks) if ranks else 0
            score_range = max_score - min_score if max_score > min_score else 1
            
            for model, score in ranks:
                if model not in self.weights:
                    self.weights[model] = {c.value: 0.5 for c in TaskCategory}
                
                # Normalize score to 0-1
                normalized = (score - min_score) / score_range
                
                # EMA update
                old_weight = self.weights[model].get(category, 0.5)
                new_weight = old_weight * (1 - learning_rate) + normalized * learning_rate
                self.weights[model][category] = round(new_weight, 3)
        
        self.save()
    
    def get_routing_recommendation(self, category: str, top_n: int = 2) -> List[str]:
        """Get top N models for a category based on current weights."""
        scores = [(model, weights.get(category, 0)) for model, weights in self.weights.items()]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [model for model, _ in scores[:top_n]]
    
    def export_heuristics(self) -> str:
        """Export current weights as routing heuristics markdown."""
        lines = ["# Calibrated Routing Weights", ""]
        lines.append(f"Last updated: {datetime.now().isoformat()}")
        lines.append("")
        lines.append("| Category | Primary | Secondary | Weight |")
        lines.append("|----------|---------|-----------|--------|")
        
        for cat in TaskCategory:
            rec = self.get_routing_recommendation(cat.value, 2)
            if len(rec) >= 2:
                w = self.weights.get(rec[0], {}).get(cat.value, 0)
                lines.append(f"| {cat.value} | {rec[0]} | {rec[1]} | {w:.2f} |")
        
        return '\n'.join(lines)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Model Benchmark Suite")
    parser.add_argument("--run", action="store_true", help="Run benchmarks")
    parser.add_argument("--models", nargs="+", help="Specific models to run")
    parser.add_argument("--tasks", nargs="+", help="Specific task IDs to run")
    parser.add_argument("--manual", action="store_true", help="Use manual scoring")
    parser.add_argument("--report", action="store_true", help="Show performance report")
    parser.add_argument("--export", metavar="FILE", help="Export results to file")
    parser.add_argument("--update-weights", action="store_true", help="Update routing weights from results")
    parser.add_argument("--list-tasks", action="store_true", help="List available benchmark tasks")
    
    args = parser.parse_args()
    
    tracker = BenchmarkTracker()
    weights = RoutingWeights()
    
    if args.list_tasks:
        print("Available benchmark tasks:")
        for task in BENCHMARK_TASKS:
            print(f"  {task.id}: {task.name} ({task.category.value}, {task.complexity})")
    
    elif args.report:
        print(tracker.generate_report())
    
    elif args.export:
        with open(args.export, 'w') as f:
            json.dump([r.to_dict() for r in tracker.results], f, indent=2)
        print(f"Exported {len(tracker.results)} results to {args.export}")
    
    elif args.update_weights:
        weights.update_from_benchmarks(tracker)
        print("Routing weights updated based on benchmark results.")
        print(weights.export_heuristics())
    
    elif args.run:
        print("Benchmark runner requires model integration.")
        print("Import this module and use with orchestrate.py:")
        print()
        print("  from benchmark import BENCHMARK_TASKS, BenchmarkTracker, score_output")
        print("  from orchestrate import MultiModelOrchestrator")
        print()
        print("  orch = MultiModelOrchestrator()")
        print("  tracker = BenchmarkTracker()")
        print()
        print("  for task in BENCHMARK_TASKS:")
        print("      result = orch.orchestrate(task.prompt)")
        print("      # Score and track results...")
    
    else:
        parser.print_help()
