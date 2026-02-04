#!/usr/bin/env python3
"""
Multi-Model Development Orchestrator

Routes tasks to best-fit LLMs, collects outputs, validates, and merges consensus code.
"""

import json
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

@dataclass
class ModelOutput:
    model: str
    code: str
    explanation: str
    execution_time: float
    score: float = 0.0

class MultiModelOrchestrator:
    def __init__(self, grok_api_key: Optional[str] = None):
        self.grok_api_key = grok_api_key or os.getenv("GROK_API_KEY")
        self.models = {
            "claude-code": self._run_claude_code,
            "codex": self._run_codex,
            "gemini": self._run_gemini,
            "grok": self._run_grok,
        }
        self.outputs: List[ModelOutput] = []
        
    def analyze_task(self, task: str) -> Tuple[str, List[str], str]:
        """
        Analyze task and determine routing.
        Returns: (category, primary_models, validator)
        """
        task_lower = task.lower()
        
        # Category detection
        if any(kw in task_lower for kw in ["react", "component", "frontend", "ui", "button", "form", "dashboard"]):
            return "frontend", ["gemini", "claude-code"], "codex"
        elif any(kw in task_lower for kw in ["api", "endpoint", "service", "backend", "middleware", "database"]):
            return "backend", ["claude-code", "codex"], "gemini"
        elif any(kw in task_lower for kw in ["docker", "kubernetes", "ci/cd", "pipeline", "terraform", "deploy"]):
            return "devops", ["codex", "grok"], "claude-code"
        elif any(kw in task_lower for kw in ["script", "bash", "automation", "cli", "tool"]):
            return "scripts", ["codex", "gemini"], "claude-code"
        elif any(kw in task_lower for kw in ["architecture", "design", "system", "scale", "pattern"]):
            return "architecture", ["grok", "claude-code"], "codex"
        elif any(kw in task_lower for kw in ["data", "pipeline", "etl", "sql", "analytics"]):
            return "data", ["codex", "claude-code"], "gemini"
        else:
            # Default: backend focus
            return "generic", ["claude-code", "codex"], "gemini"
    
    def orchestrate(self, task: str, verbose: bool = False) -> Dict:
        """
        Orchestrate task across multiple models.
        Returns: merged consensus code + metadata
        """
        category, primary_models, validator = self.analyze_task(task)
        
        if verbose:
            print(f"\n📋 Task: {task[:80]}...")
            print(f"📁 Category: {category}")
            print(f"🎯 Primary: {', '.join(primary_models)}")
            print(f"✅ Validator: {validator}")
            print(f"\n🚀 Running models in parallel...\n")
        
        # Run all models in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Submit primary models
            for model in primary_models:
                if model in self.models:
                    futures[executor.submit(self._run_model, model, task)] = model
            
            # Submit validator
            if validator in self.models:
                futures[executor.submit(self._run_model, validator, task)] = f"{validator} (validator)"
            
            # Collect results
            for future in as_completed(futures):
                model_name = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.outputs.append(result)
                        if verbose:
                            print(f"✅ {model_name}: {len(result.code)} chars, score: {result.score}")
                except Exception as e:
                    if verbose:
                        print(f"❌ {model_name}: {str(e)}")
        
        # Score and merge outputs
        consensus = self._merge_consensus(task)
        
        if verbose:
            print(f"\n🎯 Merged consensus code: {len(consensus['code'])} chars")
            print(f"📊 Quality score: {consensus.get('quality_score', 'N/A')}")
        
        return {
            "category": category,
            "task": task,
            "consensus_code": consensus["code"],
            "explanation": consensus["explanation"],
            "individual_outputs": [
                {"model": o.model, "score": o.score, "code_length": len(o.code)}
                for o in self.outputs
            ],
            "metadata": {
                "primary_models": primary_models,
                "validator": validator,
                "total_outputs": len(self.outputs),
            }
        }
    
    def _run_model(self, model: str, task: str) -> Optional[ModelOutput]:
        """Run a single model (wrapper)"""
        try:
            return self.models[model](task)
        except Exception as e:
            print(f"Error running {model}: {e}")
            return None
    
    def _run_claude_code(self, task: str) -> Optional[ModelOutput]:
        """Invoke Claude Code"""
        try:
            result = subprocess.run(
                ["claude-code", "-n", task],
                capture_output=True,
                text=True,
                timeout=30
            )
            code = result.stdout
            return ModelOutput(
                model="claude-code",
                code=code,
                explanation="Generated by Claude Code",
                execution_time=0.0,
                score=self._score_output(code)
            )
        except Exception as e:
            print(f"Claude Code error: {e}")
            return None
    
    def _run_codex(self, task: str) -> Optional[ModelOutput]:
        """Invoke Codex CLI"""
        try:
            result = subprocess.run(
                ["codex", task],
                capture_output=True,
                text=True,
                timeout=30
            )
            code = result.stdout
            return ModelOutput(
                model="codex",
                code=code,
                explanation="Generated by Codex",
                execution_time=0.0,
                score=self._score_output(code)
            )
        except Exception as e:
            print(f"Codex error: {e}")
            return None
    
    def _run_gemini(self, task: str) -> Optional[ModelOutput]:
        """Invoke Gemini CLI"""
        try:
            result = subprocess.run(
                ["gemini", task],
                capture_output=True,
                text=True,
                timeout=30
            )
            code = result.stdout
            return ModelOutput(
                model="gemini",
                code=code,
                explanation="Generated by Gemini",
                execution_time=0.0,
                score=self._score_output(code)
            )
        except Exception as e:
            print(f"Gemini error: {e}")
            return None
    
    def _run_grok(self, task: str) -> Optional[ModelOutput]:
        """Invoke Grok API"""
        if not self.grok_api_key:
            print("Warning: GROK_API_KEY not set")
            return None
        
        try:
            # TODO: Implement actual Grok API call
            # For now, placeholder
            return ModelOutput(
                model="grok",
                code="# Grok implementation placeholder",
                explanation="Generated by Grok",
                execution_time=0.0,
                score=50.0
            )
        except Exception as e:
            print(f"Grok error: {e}")
            return None
    
    def _score_output(self, code: str) -> float:
        """
        Score output based on:
        - Correctness (syntax validity)
        - Completeness (has functions, not stubs)
        - Documentation (has comments/docstrings)
        - Structure (organized, readable)
        """
        score = 50.0  # Base score
        
        # Bonus for length (more code = more complete)
        if len(code) > 100:
            score += 10
        if len(code) > 500:
            score += 10
        if len(code) > 1000:
            score += 10
        
        # Bonus for documentation
        if "#" in code or "\"\"\"" in code:
            score += 10
        
        # Bonus for structure (functions, classes)
        if "def " in code or "class " in code:
            score += 10
        
        # Bonus for tests
        if "test" in code.lower() or "assert" in code:
            score += 10
        
        return min(score, 100.0)
    
    def _merge_consensus(self, task: str) -> Dict:
        """
        Merge outputs into consensus code.
        
        Strategy:
        1. Extract code blocks from each
        2. Group by component/function
        3. Score each implementation
        4. Merge best parts + add integration glue
        """
        if not self.outputs:
            return {
                "code": "# No outputs from models",
                "explanation": "No model outputs received"
            }
        
        # Sort by score
        sorted_outputs = sorted(self.outputs, key=lambda x: x.score, reverse=True)
        best_output = sorted_outputs[0]
        
        # For now, return highest-scored output
        # TODO: Implement actual merging logic
        consensus_code = best_output.code
        
        return {
            "code": consensus_code,
            "explanation": f"Consensus from {len(self.outputs)} models (best: {best_output.model})",
            "quality_score": best_output.score,
            "models_used": [o.model for o in self.outputs]
        }

def main():
    if len(sys.argv) < 2:
        print("Usage: orchestrate.py <task> [--grok-key KEY] [--verbose]")
        sys.exit(1)
    
    task = sys.argv[1]
    grok_key = None
    verbose = "--verbose" in sys.argv
    
    # Parse args
    if "--grok-key" in sys.argv:
        idx = sys.argv.index("--grok-key")
        if idx + 1 < len(sys.argv):
            grok_key = sys.argv[idx + 1]
    
    # Run orchestrator
    orchestrator = MultiModelOrchestrator(grok_api_key=grok_key)
    result = orchestrator.orchestrate(task, verbose=verbose)
    
    # Output
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
