#!/usr/bin/env python3
"""
Task Routing Engine

Intelligent task routing that selects optimal models based on:
- Task category (backend, frontend, devops, etc.)
- Complexity estimation (LOC prediction)
- Language/framework detection
- Performance requirements

Usage:
    from router import TaskRouter, RoutingDecision
    
    router = TaskRouter()
    decision = router.route("Build a REST API endpoint in Python")
    
    print(f"Category: {decision.category}")
    print(f"Primary models: {decision.primary_models}")
    print(f"Validators: {decision.validators}")
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum


# =============================================================================
# ENUMS & DATA CLASSES
# =============================================================================

class TaskCategory(Enum):
    """Task categories for routing."""
    BACKEND = "backend"
    FRONTEND = "frontend"
    DEVOPS = "devops"
    SCRIPTS = "scripts"
    DATA = "data"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    TESTING = "testing"
    GENERIC = "generic"


class Complexity(Enum):
    """Estimated task complexity."""
    TRIVIAL = "trivial"      # <20 LOC
    SIMPLE = "simple"        # 20-50 LOC
    MEDIUM = "medium"        # 50-200 LOC
    COMPLEX = "complex"      # 200-500 LOC
    LARGE = "large"          # >500 LOC


class PerformanceRequirement(Enum):
    """Performance sensitivity."""
    REALTIME = "realtime"    # <100ms latency critical
    FAST = "fast"            # Seconds OK
    NORMAL = "normal"        # Minutes OK
    BATCH = "batch"          # Hours OK


@dataclass
class LanguageDetection:
    """Detected programming language/framework."""
    language: str
    confidence: float
    framework: Optional[str] = None
    
    
@dataclass
class ComplexityEstimate:
    """Complexity estimation result."""
    level: Complexity
    estimated_loc: int
    confidence: float
    factors: List[str] = field(default_factory=list)


@dataclass
class RoutingDecision:
    """Complete routing decision."""
    task: str
    category: TaskCategory
    complexity: ComplexityEstimate
    language: Optional[LanguageDetection]
    performance: PerformanceRequirement
    primary_models: List[str]
    validators: List[str]
    confidence: float
    reasoning: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "task": self.task[:100] + "..." if len(self.task) > 100 else self.task,
            "category": self.category.value,
            "complexity": {
                "level": self.complexity.level.value,
                "estimated_loc": self.complexity.estimated_loc,
                "confidence": self.complexity.confidence
            },
            "language": {
                "language": self.language.language,
                "framework": self.language.framework,
                "confidence": self.language.confidence
            } if self.language else None,
            "performance": self.performance.value,
            "primary_models": self.primary_models,
            "validators": self.validators,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


# =============================================================================
# KEYWORD CLASSIFIER
# =============================================================================

CATEGORY_KEYWORDS: Dict[TaskCategory, Dict[str, float]] = {
    TaskCategory.BACKEND: {
        "api": 1.0, "endpoint": 1.0, "rest": 0.9, "graphql": 0.9,
        "service": 0.8, "server": 0.8, "backend": 1.0,
        "middleware": 0.9, "database": 0.7, "crud": 0.8,
        "authentication": 0.7, "authorization": 0.7,
        "microservice": 0.9, "webhook": 0.8, "websocket": 0.8
    },
    TaskCategory.FRONTEND: {
        "react": 1.0, "vue": 1.0, "angular": 1.0, "svelte": 1.0,
        "component": 0.9, "frontend": 1.0, "ui": 0.8, "ux": 0.7,
        "button": 0.6, "form": 0.7, "page": 0.5, "dashboard": 0.8,
        "responsive": 0.7, "css": 0.6, "tailwind": 0.8, "styled": 0.7,
        "modal": 0.7, "navigation": 0.6, "layout": 0.6
    },
    TaskCategory.DEVOPS: {
        "docker": 1.0, "kubernetes": 1.0, "k8s": 1.0, "helm": 0.9,
        "ci/cd": 1.0, "cicd": 1.0, "pipeline": 0.9, "jenkins": 0.9,
        "terraform": 1.0, "ansible": 0.9, "deploy": 0.8, "deployment": 0.8,
        "aws": 0.7, "gcp": 0.7, "azure": 0.7, "cloud": 0.6,
        "infrastructure": 0.9, "iac": 0.9, "github actions": 1.0
    },
    TaskCategory.SCRIPTS: {
        "script": 1.0, "automation": 0.9, "automate": 0.9,
        "bash": 0.9, "shell": 0.8, "cli": 0.9, "command": 0.6,
        "tool": 0.7, "utility": 0.8, "cron": 0.8, "scheduled": 0.7,
        "batch": 0.6, "migrate": 0.7, "convert": 0.6
    },
    TaskCategory.DATA: {
        "data": 0.7, "pipeline": 0.6, "etl": 1.0,
        "analytics": 0.9, "analysis": 0.8, "sql": 0.8,
        "pandas": 0.9, "dataframe": 0.9, "spark": 0.9,
        "transform": 0.7, "aggregate": 0.7, "report": 0.6,
        "csv": 0.6, "json": 0.5, "parquet": 0.8
    },
    TaskCategory.ARCHITECTURE: {
        "architecture": 1.0, "design": 0.7, "system": 0.6,
        "scale": 0.8, "scalable": 0.8, "pattern": 0.7,
        "microservices": 0.9, "monolith": 0.8, "distributed": 0.9,
        "event-driven": 0.9, "cqrs": 0.9, "saga": 0.8,
        "high availability": 0.9, "fault tolerant": 0.9
    },
    TaskCategory.SECURITY: {
        "security": 1.0, "secure": 0.8, "vulnerability": 0.9,
        "authentication": 0.8, "authorization": 0.8, "oauth": 0.9,
        "jwt": 0.8, "encryption": 0.9, "decrypt": 0.8,
        "sanitize": 0.8, "xss": 0.9, "csrf": 0.9, "injection": 0.9,
        "firewall": 0.8, "ssl": 0.7, "tls": 0.7
    },
    TaskCategory.TESTING: {
        "test": 0.9, "testing": 1.0, "unittest": 1.0, "pytest": 1.0,
        "jest": 1.0, "mocha": 0.9, "spec": 0.7,
        "mock": 0.8, "stub": 0.8, "fixture": 0.8,
        "integration test": 1.0, "e2e": 0.9, "coverage": 0.8
    }
}


def classify_category(task: str) -> Tuple[TaskCategory, float, List[str]]:
    """
    Classify task into a category using keyword matching.
    
    Returns: (category, confidence, matched_keywords)
    """
    task_lower = task.lower()
    
    scores: Dict[TaskCategory, Tuple[float, List[str]]] = {}
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        total_score = 0.0
        matched = []
        
        for keyword, weight in keywords.items():
            if keyword in task_lower:
                total_score += weight
                matched.append(keyword)
        
        if matched:
            scores[category] = (total_score, matched)
    
    if not scores:
        return TaskCategory.GENERIC, 0.5, []
    
    # Get highest scoring category
    best_category = max(scores.keys(), key=lambda c: scores[c][0])
    best_score, best_matches = scores[best_category]
    
    # Normalize confidence (max ~3-4 keywords typically)
    confidence = min(best_score / 3.0, 1.0)
    
    return best_category, confidence, best_matches


# =============================================================================
# COMPLEXITY ESTIMATOR
# =============================================================================

COMPLEXITY_INDICATORS = {
    Complexity.TRIVIAL: {
        "keywords": ["simple", "basic", "quick", "small", "tiny", "single", "one"],
        "loc_range": (0, 20),
        "base_score": 0
    },
    Complexity.SIMPLE: {
        "keywords": ["function", "helper", "util", "wrapper", "short"],
        "loc_range": (20, 50),
        "base_score": 1
    },
    Complexity.MEDIUM: {
        "keywords": ["class", "module", "service", "component", "handler"],
        "loc_range": (50, 200),
        "base_score": 2
    },
    Complexity.COMPLEX: {
        "keywords": ["full", "complete", "system", "integration", "multiple", "several"],
        "loc_range": (200, 500),
        "base_score": 3
    },
    Complexity.LARGE: {
        "keywords": ["enterprise", "platform", "framework", "comprehensive", "extensive"],
        "loc_range": (500, 2000),
        "base_score": 4
    }
}

# Complexity modifiers
COMPLEXITY_MODIFIERS = {
    # Increases complexity
    "with tests": 1.5,
    "with documentation": 1.2,
    "with error handling": 1.2,
    "production ready": 1.3,
    "scalable": 1.4,
    "multi-tenant": 1.5,
    "real-time": 1.3,
    
    # Decreases complexity
    "prototype": 0.7,
    "proof of concept": 0.6,
    "minimal": 0.6,
    "basic": 0.7,
    "skeleton": 0.5
}


def estimate_complexity(task: str, category: TaskCategory) -> ComplexityEstimate:
    """
    Estimate task complexity and predicted LOC.
    
    Returns: ComplexityEstimate with level, LOC, confidence, and factors
    """
    task_lower = task.lower()
    factors = []
    
    # Base score from keywords
    best_match = Complexity.MEDIUM
    best_score = 0
    
    for complexity, config in COMPLEXITY_INDICATORS.items():
        score = sum(1 for kw in config["keywords"] if kw in task_lower)
        if score > best_score:
            best_score = score
            best_match = complexity
            
    if best_score > 0:
        factors.append(f"Keyword match: {best_match.value}")
    
    # Apply modifiers
    modifier = 1.0
    for phrase, mult in COMPLEXITY_MODIFIERS.items():
        if phrase in task_lower:
            modifier *= mult
            factors.append(f"Modifier: {phrase} ({mult}x)")
    
    # Adjust based on modifier
    complexity_order = [Complexity.TRIVIAL, Complexity.SIMPLE, Complexity.MEDIUM, 
                       Complexity.COMPLEX, Complexity.LARGE]
    idx = complexity_order.index(best_match)
    
    if modifier > 1.3:
        idx = min(idx + 1, len(complexity_order) - 1)
    elif modifier < 0.7:
        idx = max(idx - 1, 0)
    
    final_complexity = complexity_order[idx]
    
    # Estimate LOC
    loc_range = COMPLEXITY_INDICATORS[final_complexity]["loc_range"]
    estimated_loc = (loc_range[0] + loc_range[1]) // 2
    estimated_loc = int(estimated_loc * modifier)
    
    # Confidence based on number of factors
    confidence = min(0.5 + (len(factors) * 0.1) + (best_score * 0.1), 0.95)
    
    return ComplexityEstimate(
        level=final_complexity,
        estimated_loc=estimated_loc,
        confidence=confidence,
        factors=factors
    )


# =============================================================================
# LANGUAGE DETECTION
# =============================================================================

LANGUAGE_PATTERNS = {
    "python": {
        "keywords": ["python", "django", "flask", "fastapi", "pandas", "numpy", "pytest"],
        "extensions": [".py"],
        "frameworks": {"django": "Django", "flask": "Flask", "fastapi": "FastAPI"}
    },
    "javascript": {
        "keywords": ["javascript", "js", "node", "nodejs", "express", "npm"],
        "extensions": [".js", ".mjs"],
        "frameworks": {"express": "Express", "node": "Node.js", "next": "Next.js"}
    },
    "typescript": {
        "keywords": ["typescript", "ts", "nestjs", "angular", "deno"],
        "extensions": [".ts", ".tsx"],
        "frameworks": {"nestjs": "NestJS", "angular": "Angular", "next": "Next.js"}
    },
    "react": {
        "keywords": ["react", "jsx", "tsx", "nextjs", "gatsby", "redux"],
        "extensions": [".jsx", ".tsx"],
        "frameworks": {"nextjs": "Next.js", "gatsby": "Gatsby", "redux": "Redux"}
    },
    "go": {
        "keywords": ["go", "golang", "gin", "echo", "fiber"],
        "extensions": [".go"],
        "frameworks": {"gin": "Gin", "echo": "Echo", "fiber": "Fiber"}
    },
    "rust": {
        "keywords": ["rust", "cargo", "tokio", "actix", "rocket"],
        "extensions": [".rs"],
        "frameworks": {"actix": "Actix", "rocket": "Rocket", "tokio": "Tokio"}
    },
    "java": {
        "keywords": ["java", "spring", "springboot", "maven", "gradle"],
        "extensions": [".java"],
        "frameworks": {"spring": "Spring Boot", "quarkus": "Quarkus"}
    },
    "sql": {
        "keywords": ["sql", "mysql", "postgresql", "postgres", "sqlite", "query"],
        "extensions": [".sql"],
        "frameworks": {}
    },
    "terraform": {
        "keywords": ["terraform", "hcl", "tf", "infrastructure as code"],
        "extensions": [".tf", ".tfvars"],
        "frameworks": {}
    },
    "bash": {
        "keywords": ["bash", "shell", "sh", "zsh", "script"],
        "extensions": [".sh", ".bash"],
        "frameworks": {}
    }
}


def detect_language(task: str) -> Optional[LanguageDetection]:
    """
    Detect programming language and framework from task description.
    
    Returns: LanguageDetection or None
    """
    task_lower = task.lower()
    
    best_match = None
    best_score = 0
    best_framework = None
    
    for language, config in LANGUAGE_PATTERNS.items():
        score = sum(1 for kw in config["keywords"] if kw in task_lower)
        
        if score > best_score:
            best_score = score
            best_match = language
            
            # Check for framework
            for fw_key, fw_name in config["frameworks"].items():
                if fw_key in task_lower:
                    best_framework = fw_name
                    score += 0.5  # Boost for framework match
    
    if best_match and best_score > 0:
        confidence = min(best_score / 2.0, 1.0)
        return LanguageDetection(
            language=best_match,
            confidence=confidence,
            framework=best_framework
        )
    
    return None


# =============================================================================
# ROUTING LOGIC
# =============================================================================

# Model routing by category
CATEGORY_ROUTING: Dict[TaskCategory, Tuple[List[str], str]] = {
    TaskCategory.BACKEND: (["claude-code", "codex"], "gemini"),
    TaskCategory.FRONTEND: (["gemini", "claude-code"], "codex"),
    TaskCategory.DEVOPS: (["codex", "grok"], "claude-code"),
    TaskCategory.SCRIPTS: (["codex", "gemini"], "claude-code"),
    TaskCategory.DATA: (["codex", "claude-code"], "gemini"),
    TaskCategory.ARCHITECTURE: (["grok", "claude-code"], "codex"),
    TaskCategory.SECURITY: (["claude-code", "grok"], "codex"),
    TaskCategory.TESTING: (["claude-code", "codex"], "gemini"),
    TaskCategory.GENERIC: (["claude-code", "codex"], "gemini")
}

# Language-specific routing overrides
LANGUAGE_ROUTING: Dict[str, Tuple[List[str], str]] = {
    "python": (["codex", "claude-code"], "gemini"),
    "javascript": (["gemini", "codex"], "claude-code"),
    "typescript": (["gemini", "claude-code"], "codex"),
    "react": (["gemini", "claude-code"], "codex"),
    "go": (["claude-code", "codex"], "grok"),
    "rust": (["claude-code", "codex"], "grok"),
    "terraform": (["grok", "codex"], "claude-code"),
    "bash": (["codex", "grok"], "claude-code"),
}

# Performance-based adjustments
PERFORMANCE_ROUTING: Dict[PerformanceRequirement, List[str]] = {
    PerformanceRequirement.REALTIME: ["codex", "grok"],      # Fast, pragmatic
    PerformanceRequirement.FAST: ["codex", "claude-code"],   # Balanced
    PerformanceRequirement.NORMAL: ["claude-code", "codex"], # Quality focus
    PerformanceRequirement.BATCH: ["claude-code", "gemini"]  # Thorough
}


def detect_performance_requirement(task: str) -> PerformanceRequirement:
    """Detect performance requirements from task."""
    task_lower = task.lower()
    
    if any(kw in task_lower for kw in ["realtime", "real-time", "low latency", "millisecond", "<100ms"]):
        return PerformanceRequirement.REALTIME
    elif any(kw in task_lower for kw in ["fast", "quick", "responsive", "performance"]):
        return PerformanceRequirement.FAST
    elif any(kw in task_lower for kw in ["batch", "background", "scheduled", "async"]):
        return PerformanceRequirement.BATCH
    
    return PerformanceRequirement.NORMAL


# =============================================================================
# TASK ROUTER
# =============================================================================

class TaskRouter:
    """
    Intelligent task router that selects optimal models.
    """
    
    def __init__(self, custom_routing: Optional[Dict] = None):
        """
        Args:
            custom_routing: Override default routing rules
        """
        self.category_routing = {**CATEGORY_ROUTING, **(custom_routing or {})}
    
    def route(self, task: str) -> RoutingDecision:
        """
        Analyze task and determine optimal model routing.
        
        Args:
            task: Task description
            
        Returns:
            RoutingDecision with models, validators, and reasoning
        """
        reasoning = []
        
        # 1. Classify category
        category, cat_confidence, cat_matches = classify_category(task)
        reasoning.append(f"Category: {category.value} (confidence: {cat_confidence:.0%})")
        if cat_matches:
            reasoning.append(f"  Keywords: {', '.join(cat_matches[:5])}")
        
        # 2. Estimate complexity
        complexity = estimate_complexity(task, category)
        reasoning.append(f"Complexity: {complexity.level.value} (~{complexity.estimated_loc} LOC)")
        
        # 3. Detect language
        language = detect_language(task)
        if language:
            reasoning.append(f"Language: {language.language}" + 
                          (f" ({language.framework})" if language.framework else ""))
        
        # 4. Detect performance requirements
        performance = detect_performance_requirement(task)
        if performance != PerformanceRequirement.NORMAL:
            reasoning.append(f"Performance: {performance.value}")
        
        # 5. Determine routing
        primary_models, validators = self._determine_routing(
            category, complexity, language, performance, reasoning
        )
        
        # 6. Calculate overall confidence
        confidence = (cat_confidence + complexity.confidence) / 2
        if language:
            confidence = (confidence + language.confidence) / 2
        
        return RoutingDecision(
            task=task,
            category=category,
            complexity=complexity,
            language=language,
            performance=performance,
            primary_models=primary_models,
            validators=validators,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _determine_routing(
        self,
        category: TaskCategory,
        complexity: ComplexityEstimate,
        language: Optional[LanguageDetection],
        performance: PerformanceRequirement,
        reasoning: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Determine model routing based on all factors."""
        
        # Start with category-based routing
        base_primaries, base_validator = self.category_routing.get(
            category, self.category_routing[TaskCategory.GENERIC]
        )
        primaries = list(base_primaries)
        validators = [base_validator]
        
        # Apply language override if confident
        if language and language.confidence > 0.7:
            lang_routing = LANGUAGE_ROUTING.get(language.language)
            if lang_routing:
                primaries = list(lang_routing[0])
                validators = [lang_routing[1]]
                reasoning.append(f"  → Language override: {language.language}")
        
        # Adjust for performance requirements
        if performance in [PerformanceRequirement.REALTIME, PerformanceRequirement.FAST]:
            perf_models = PERFORMANCE_ROUTING[performance]
            # Prioritize performance-optimal models
            primaries = [m for m in perf_models if m in primaries] + \
                       [m for m in primaries if m not in perf_models]
            reasoning.append(f"  → Performance adjusted for {performance.value}")
        
        # Adjust for complexity
        if complexity.level == Complexity.TRIVIAL:
            # Single model, no validator
            primaries = primaries[:1]
            validators = []
            reasoning.append("  → Trivial: single model, no validator")
        elif complexity.level == Complexity.SIMPLE:
            # Two models, no validator
            primaries = primaries[:2]
            validators = []
            reasoning.append("  → Simple: two models, no validator")
        elif complexity.level in [Complexity.COMPLEX, Complexity.LARGE]:
            # Add second validator
            all_models = ["claude-code", "codex", "gemini", "grok"]
            available = [m for m in all_models if m not in primaries and m not in validators]
            if available:
                validators.append(available[0])
                reasoning.append(f"  → Complex: added second validator ({available[0]})")
        
        return primaries, validators
    
    def explain(self, task: str) -> str:
        """Get a human-readable explanation of routing decision."""
        decision = self.route(task)
        
        lines = [
            "# Routing Decision",
            "",
            f"**Task:** {decision.task[:80]}...",
            "",
            "## Analysis",
        ]
        
        for reason in decision.reasoning:
            lines.append(f"- {reason}")
        
        lines.extend([
            "",
            "## Routing",
            f"**Primary models:** {', '.join(decision.primary_models)}",
            f"**Validators:** {', '.join(decision.validators) if decision.validators else 'None'}",
            f"**Confidence:** {decision.confidence:.0%}",
        ])
        
        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Task Routing Engine")
    parser.add_argument("task", nargs="?", help="Task to route")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    parser.add_argument("--explain", "-e", action="store_true", help="Show explanation")
    
    args = parser.parse_args()
    
    if not args.task:
        # Demo mode
        demo_tasks = [
            "Build a REST API endpoint for user authentication",
            "Create a React dashboard component with charts",
            "Write a Terraform module for AWS ECS deployment",
            "Simple Python script to parse CSV files",
            "Design a scalable microservices architecture for e-commerce",
        ]
        
        router = TaskRouter()
        print("Task Routing Demo\n" + "=" * 60)
        
        for task in demo_tasks:
            decision = router.route(task)
            print(f"\n📋 {task[:50]}...")
            print(f"   Category: {decision.category.value}")
            print(f"   Complexity: {decision.complexity.level.value}")
            print(f"   Models: {decision.primary_models} → {decision.validators}")
    else:
        router = TaskRouter()
        decision = router.route(args.task)
        
        if args.json:
            print(json.dumps(decision.to_dict(), indent=2))
        elif args.explain:
            print(router.explain(args.task))
        else:
            print(f"Category: {decision.category.value}")
            print(f"Complexity: {decision.complexity.level.value} (~{decision.complexity.estimated_loc} LOC)")
            if decision.language:
                print(f"Language: {decision.language.language}")
            print(f"Primary: {', '.join(decision.primary_models)}")
            print(f"Validators: {', '.join(decision.validators) if decision.validators else 'None'}")
            print(f"Confidence: {decision.confidence:.0%}")
