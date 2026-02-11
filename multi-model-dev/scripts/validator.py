#!/usr/bin/env python3
"""
Validator Model Pattern

Implements cross-perspective review where a different model validates
primary outputs, catching blind spots and suggesting optimal merges.

Usage:
    from validator import Validator, ValidationResult
    
    validator = Validator()
    result = validator.validate(
        task="Build a REST API endpoint",
        outputs={"claude-code": code1, "codex": code2},
        validator_model="gemini"
    )
    
    if result.needs_human_review:
        print("Human review required:", result.concerns)
    else:
        print("Recommended merge:", result.merge_recommendation)
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class ValidationStatus(Enum):
    """Validation outcome status."""
    APPROVED = "approved"           # All outputs acceptable, can auto-merge
    NEEDS_REVIEW = "needs_review"   # Human review recommended
    REJECTED = "rejected"           # Outputs have critical issues
    PARTIAL = "partial"             # Some outputs acceptable


@dataclass
class OutputAnalysis:
    """Analysis of a single model's output."""
    model: str
    score: int                      # 0-100
    strengths: List[str]
    weaknesses: List[str]
    issues: List[str]               # Critical issues found
    merge_worthy: bool              # Include in merge?
    notes: str = ""


@dataclass
class ValidationResult:
    """Complete validation result."""
    task: str
    validator_model: str
    status: ValidationStatus
    confidence: float               # 0.0-1.0
    analyses: Dict[str, OutputAnalysis]
    merge_recommendation: List[str]  # Ordered list of models to merge from
    merge_strategy: str             # How to merge (use_best, combine, sequential)
    concerns: List[str]             # Issues requiring attention
    needs_human_review: bool
    review_reasons: List[str]
    summary: str
    raw_validation: str = ""        # Raw validator output
    
    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "validator_model": self.validator_model,
            "status": self.status.value,
            "confidence": self.confidence,
            "analyses": {k: {
                "model": v.model,
                "score": v.score,
                "strengths": v.strengths,
                "weaknesses": v.weaknesses,
                "issues": v.issues,
                "merge_worthy": v.merge_worthy,
                "notes": v.notes
            } for k, v in self.analyses.items()},
            "merge_recommendation": self.merge_recommendation,
            "merge_strategy": self.merge_strategy,
            "concerns": self.concerns,
            "needs_human_review": self.needs_human_review,
            "review_reasons": self.review_reasons,
            "summary": self.summary
        }


# =============================================================================
# VALIDATOR PROMPT TEMPLATES
# =============================================================================

VALIDATOR_SYSTEM_PROMPT = """You are an expert code reviewer performing cross-model validation.

Your role:
1. Review outputs from multiple AI models for the same task
2. Identify strengths and weaknesses in each approach
3. Catch blind spots that individual models missed
4. Recommend which outputs (or parts) to use in the final merge
5. Flag any concerns that require human review

Be objective and thorough. Your fresh perspective is valuable for catching issues
the primary models may have overlooked."""

VALIDATOR_PROMPT_TEMPLATE = """## Task
{task}

## Model Outputs to Validate

{outputs_section}

## Your Validation Tasks

1. **Score each output** (0-100) based on:
   - Correctness (does it work?)
   - Structure (well-organized?)
   - Best practices (idiomatic code?)
   - Completeness (handles edge cases?)

2. **Identify for each output**:
   - Key strengths (what it does well)
   - Weaknesses (what could be better)
   - Critical issues (bugs, security problems, etc.)

3. **Recommend merge strategy**:
   - Which outputs should be used?
   - How should they be combined?
   - What order of preference?

4. **Flag concerns** that need human review

## Response Format

Respond with a JSON object:
```json
{{
  "analyses": {{
    "model_name": {{
      "score": 85,
      "strengths": ["strength1", "strength2"],
      "weaknesses": ["weakness1"],
      "issues": ["critical issue if any"],
      "merge_worthy": true,
      "notes": "Additional observations"
    }}
  }},
  "merge_recommendation": ["model1", "model2"],
  "merge_strategy": "combine|use_best|sequential",
  "concerns": ["concern1", "concern2"],
  "confidence": 0.95,
  "summary": "Brief summary of validation findings"
}}
```

Only include models that were provided. Be specific in your analysis."""


def format_outputs_section(outputs: Dict[str, str]) -> str:
    """Format model outputs for the validator prompt."""
    sections = []
    for model, output in outputs.items():
        # Truncate very long outputs
        truncated = output[:8000] + "\n...[truncated]" if len(output) > 8000 else output
        sections.append(f"### {model.upper()}\n```\n{truncated}\n```")
    return "\n\n".join(sections)


# =============================================================================
# VALIDATOR SELECTION LOGIC
# =============================================================================

VALIDATOR_SELECTION = {
    # Primary pair -> Recommended validator
    frozenset(["claude-code", "codex"]): "gemini",
    frozenset(["gemini", "claude-code"]): "codex",
    frozenset(["codex", "grok"]): "claude-code",
    frozenset(["grok", "claude-code"]): "codex",
    frozenset(["gemini", "codex"]): "claude-code",
    frozenset(["gemini", "grok"]): "claude-code",
}


def select_validator(primary_models: List[str]) -> str:
    """
    Select the best validator model based on primary models used.
    
    Validator should offer a different perspective than primaries.
    """
    primary_set = frozenset(primary_models)
    
    # Check for known good pairings
    if primary_set in VALIDATOR_SELECTION:
        return VALIDATOR_SELECTION[primary_set]
    
    # Default logic: pick model not in primaries
    all_models = ["claude-code", "codex", "gemini", "grok"]
    available = [m for m in all_models if m not in primary_models]
    
    if available:
        # Prefer claude-code as default validator (thorough)
        if "claude-code" in available:
            return "claude-code"
        return available[0]
    
    # All models were primaries, use claude-code
    return "claude-code"


# =============================================================================
# CONFIDENCE & ESCALATION
# =============================================================================

CONFIDENCE_THRESHOLD = 0.90  # Below this, require human review

ESCALATION_TRIGGERS = [
    "security",
    "vulnerability", 
    "unsafe",
    "critical",
    "dangerous",
    "injection",
    "authentication",
    "authorization",
    "password",
    "secret",
    "key",
    "token",
    "production",
    "database",
    "delete",
    "drop",
]


def should_escalate(result: ValidationResult) -> Tuple[bool, List[str]]:
    """
    Determine if validation result should be escalated to human review.
    
    Returns (should_escalate, reasons).
    """
    reasons = []
    
    # Low confidence
    if result.confidence < CONFIDENCE_THRESHOLD:
        reasons.append(f"Validator confidence {result.confidence:.0%} below threshold {CONFIDENCE_THRESHOLD:.0%}")
    
    # Explicit concerns
    if result.concerns:
        reasons.append(f"Validator flagged {len(result.concerns)} concerns")
    
    # Critical issues in any output
    for model, analysis in result.analyses.items():
        if analysis.issues:
            reasons.append(f"{model} has {len(analysis.issues)} critical issues")
    
    # Security-sensitive content
    all_text = result.summary.lower() + " ".join(result.concerns).lower()
    triggered = [t for t in ESCALATION_TRIGGERS if t in all_text]
    if triggered:
        reasons.append(f"Security-sensitive keywords: {', '.join(triggered)}")
    
    # No merge-worthy outputs
    merge_worthy = [m for m, a in result.analyses.items() if a.merge_worthy]
    if not merge_worthy:
        reasons.append("No outputs deemed merge-worthy")
    
    return len(reasons) > 0, reasons


# =============================================================================
# VALIDATOR CLASS
# =============================================================================

class Validator:
    """
    Cross-perspective validator for multi-model outputs.
    """
    
    def __init__(self, model_runner=None):
        """
        Args:
            model_runner: Callable(model_name, prompt) -> str
                         Function to run a model and get output.
                         If None, uses default implementation.
        """
        self.model_runner = model_runner or self._default_runner
    
    def _default_runner(self, model: str, prompt: str) -> str:
        """Default model runner - tries to use available integrations."""
        # Try Grok client
        if model in ["grok", "grok-3"]:
            try:
                from grok_client import GrokClient
                client = GrokClient()
                response = client.chat(prompt, system_prompt=VALIDATOR_SYSTEM_PROMPT)
                return response.content
            except Exception as e:
                print(f"Grok validation failed: {e}")
        
        # Placeholder for other models
        raise NotImplementedError(
            f"No runner configured for {model}. "
            f"Pass a model_runner to Validator() or implement integration."
        )
    
    def validate(
        self,
        task: str,
        outputs: Dict[str, str],
        validator_model: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate outputs from multiple models.
        
        Args:
            task: Original task description
            outputs: Dict mapping model name to output
            validator_model: Model to use for validation (auto-selected if None)
            
        Returns:
            ValidationResult with analysis and recommendations
        """
        # Select validator if not specified
        if validator_model is None:
            validator_model = select_validator(list(outputs.keys()))
        
        # Build validation prompt
        outputs_section = format_outputs_section(outputs)
        prompt = VALIDATOR_PROMPT_TEMPLATE.format(
            task=task,
            outputs_section=outputs_section
        )
        
        # Run validation
        raw_output = self.model_runner(validator_model, prompt)
        
        # Parse response
        result = self._parse_validation_response(
            raw_output, task, validator_model, outputs
        )
        
        # Check for escalation
        needs_review, review_reasons = should_escalate(result)
        result.needs_human_review = needs_review
        result.review_reasons = review_reasons
        result.raw_validation = raw_output
        
        return result
    
    def _parse_validation_response(
        self,
        raw_output: str,
        task: str,
        validator_model: str,
        outputs: Dict[str, str]
    ) -> ValidationResult:
        """Parse the validator's JSON response."""
        
        # Extract JSON from response
        json_match = re.search(r'```json\s*(.*?)\s*```', raw_output, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
            json_str = json_match.group(0) if json_match else "{}"
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            # Return low-confidence result if parsing fails
            return ValidationResult(
                task=task,
                validator_model=validator_model,
                status=ValidationStatus.NEEDS_REVIEW,
                confidence=0.5,
                analyses={
                    model: OutputAnalysis(
                        model=model, score=50,
                        strengths=[], weaknesses=[],
                        issues=["Validation parsing failed"],
                        merge_worthy=True, notes=""
                    ) for model in outputs
                },
                merge_recommendation=list(outputs.keys()),
                merge_strategy="use_best",
                concerns=["Failed to parse validator response"],
                needs_human_review=True,
                review_reasons=["Validation parsing failed"],
                summary="Validation response could not be parsed"
            )
        
        # Build analyses
        analyses = {}
        for model, analysis_data in data.get("analyses", {}).items():
            if model in outputs:
                analyses[model] = OutputAnalysis(
                    model=model,
                    score=analysis_data.get("score", 50),
                    strengths=analysis_data.get("strengths", []),
                    weaknesses=analysis_data.get("weaknesses", []),
                    issues=analysis_data.get("issues", []),
                    merge_worthy=analysis_data.get("merge_worthy", True),
                    notes=analysis_data.get("notes", "")
                )
        
        # Fill in missing models
        for model in outputs:
            if model not in analyses:
                analyses[model] = OutputAnalysis(
                    model=model, score=50,
                    strengths=[], weaknesses=[],
                    issues=[], merge_worthy=True, notes=""
                )
        
        confidence = data.get("confidence", 0.7)
        concerns = data.get("concerns", [])
        
        # Determine status
        if confidence >= CONFIDENCE_THRESHOLD and not concerns:
            status = ValidationStatus.APPROVED
        elif any(a.issues for a in analyses.values()):
            status = ValidationStatus.PARTIAL
        else:
            status = ValidationStatus.NEEDS_REVIEW
        
        return ValidationResult(
            task=task,
            validator_model=validator_model,
            status=status,
            confidence=confidence,
            analyses=analyses,
            merge_recommendation=data.get("merge_recommendation", list(outputs.keys())),
            merge_strategy=data.get("merge_strategy", "use_best"),
            concerns=concerns,
            needs_human_review=False,  # Will be set by should_escalate
            review_reasons=[],
            summary=data.get("summary", "Validation complete")
        )
    
    def format_review_request(self, result: ValidationResult) -> str:
        """Format a human-readable review request."""
        lines = [
            "# Human Review Required",
            "",
            f"**Task:** {result.task}",
            f"**Validator:** {result.validator_model}",
            f"**Confidence:** {result.confidence:.0%}",
            "",
            "## Why Review Needed",
            ""
        ]
        for reason in result.review_reasons:
            lines.append(f"- {reason}")
        
        lines.extend(["", "## Concerns", ""])
        for concern in result.concerns:
            lines.append(f"- {concern}")
        
        lines.extend(["", "## Model Analyses", ""])
        for model, analysis in result.analyses.items():
            lines.append(f"### {model} (Score: {analysis.score})")
            if analysis.strengths:
                lines.append(f"**Strengths:** {', '.join(analysis.strengths)}")
            if analysis.weaknesses:
                lines.append(f"**Weaknesses:** {', '.join(analysis.weaknesses)}")
            if analysis.issues:
                lines.append(f"**⚠️ Issues:** {', '.join(analysis.issues)}")
            lines.append("")
        
        lines.extend([
            "## Recommendation",
            f"**Strategy:** {result.merge_strategy}",
            f"**Merge order:** {' → '.join(result.merge_recommendation)}",
            "",
            "---",
            "*Please review and approve/reject the merge.*"
        ])
        
        return "\n".join(lines)


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Cross-model validator")
    parser.add_argument("--demo", action="store_true", help="Run demo validation")
    
    args = parser.parse_args()
    
    if args.demo:
        print("Validator Demo")
        print("=" * 40)
        
        # Demo outputs
        demo_outputs = {
            "claude-code": '''
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b
''',
            "codex": '''
def add(a, b):
    return a + b
'''
        }
        
        print("\nModel outputs:")
        for model, output in demo_outputs.items():
            print(f"\n{model}:\n{output}")
        
        print("\nTo run actual validation, configure a model runner:")
        print("  validator = Validator(model_runner=my_runner)")
        print("  result = validator.validate(task, outputs)")
    else:
        parser.print_help()
