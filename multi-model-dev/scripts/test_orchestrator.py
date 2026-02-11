#!/usr/bin/env python3
"""
Orchestrator Integration Test

Tests all components of the multi-model orchestrator:
1. Router - task categorization, complexity, language detection
2. Merger - code block parsing, AST analysis, consensus merging
3. Validator - cross-model validation
4. Orchestrator - full pipeline integration

Run with:
    python test_orchestrator.py              # All tests with mocks
    python test_orchestrator.py --live       # Include live Grok API test
    python test_orchestrator.py --verbose    # Detailed output
"""

import asyncio
import json
import sys
from dataclasses import dataclass
from typing import List, Tuple
import os

# Test result tracking
@dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    details: str = ""

class TestRunner:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []
    
    def test(self, name: str):
        """Decorator for test functions."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    if result is True or result is None:
                        self.results.append(TestResult(name, True, "PASS"))
                        self._print_result(name, True, "")
                    elif isinstance(result, tuple):
                        passed, msg = result
                        self.results.append(TestResult(name, passed, "PASS" if passed else "FAIL", msg))
                        self._print_result(name, passed, msg)
                    else:
                        self.results.append(TestResult(name, False, "FAIL", str(result)))
                        self._print_result(name, False, str(result))
                except Exception as e:
                    self.results.append(TestResult(name, False, "ERROR", str(e)))
                    self._print_result(name, False, f"Exception: {e}")
            return wrapper
        return decorator
    
    def _print_result(self, name: str, passed: bool, msg: str):
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")
        if msg and self.verbose:
            for line in msg.split('\n'):
                print(f"      {line}")
    
    def summary(self):
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        print(f"\n{'='*60}")
        print(f"RESULTS: {passed}/{total} tests passed")
        print(f"{'='*60}")
        
        if passed < total:
            print("\nFailed tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ❌ {r.name}: {r.details}")
        
        return passed == total


# =============================================================================
# SAMPLE DATA
# =============================================================================

SAMPLE_OUTPUTS = {
    "claude-code": '''
Here's a production-ready REST API endpoint:

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid

app = FastAPI(title="User API", version="1.0.0")


class UserCreate(BaseModel):
    """Request model for user creation."""
    name: str
    email: EmailStr
    
    class Config:
        json_schema_extra = {
            "example": {"name": "John Doe", "email": "john@example.com"}
        }


class UserResponse(BaseModel):
    """Response model for user data."""
    id: str
    name: str
    email: str


# In-memory storage (replace with database in production)
users_db: dict = {}


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate) -> UserResponse:
    """
    Create a new user.
    
    Args:
        user: User data with name and email
        
    Returns:
        Created user with generated ID
        
    Raises:
        HTTPException: If email already exists
    """
    # Check for duplicate email
    for existing in users_db.values():
        if existing["email"] == user.email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
    
    # Create user
    user_id = str(uuid.uuid4())
    users_db[user_id] = {"id": user_id, "name": user.name, "email": user.email}
    
    return UserResponse(**users_db[user_id])
```
''',
    
    "codex": '''
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

app = FastAPI()

class User(BaseModel):
    name: str
    email: str

users = {}

@app.post("/users")
def create_user(user: User):
    user_id = str(uuid.uuid4())
    users[user_id] = {"id": user_id, **user.dict()}
    return users[user_id]
```
''',

    "gemini": '''
Here's a React-style approach to the API:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator
from typing import Dict
import re
import uuid

app = FastAPI()

class UserInput(BaseModel):
    name: str
    email: str
    
    @validator('email')
    def validate_email(cls, v):
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', v):
            raise ValueError('Invalid email format')
        return v

database: Dict[str, dict] = {}

@app.post("/users")
async def create_user(user: UserInput):
    """Create user with email validation."""
    user_id = str(uuid.uuid4())
    database[user_id] = {
        "id": user_id,
        "name": user.name,
        "email": user.email
    }
    return database[user_id]
```
'''
}


# =============================================================================
# TESTS
# =============================================================================

def run_tests(verbose: bool = False, live: bool = False):
    """Run all orchestrator tests."""
    
    runner = TestRunner(verbose=verbose)
    
    print("="*60)
    print("MULTI-MODEL ORCHESTRATOR TEST SUITE")
    print("="*60)
    
    # -------------------------------------------------------------------------
    # Router Tests
    # -------------------------------------------------------------------------
    print("\n📋 Router Tests")
    
    @runner.test("Router: Backend task categorization")
    def test_router_backend():
        from router import TaskRouter, TaskCategory
        router = TaskRouter()
        decision = router.route("Build a REST API endpoint for user management")
        assert decision.category == TaskCategory.BACKEND, f"Got {decision.category}"
        return True, f"Category: {decision.category.value}, Confidence: {decision.confidence:.0%}"
    
    @runner.test("Router: Frontend task categorization")
    def test_router_frontend():
        from router import TaskRouter, TaskCategory
        router = TaskRouter()
        decision = router.route("Create a React dashboard component with charts")
        assert decision.category == TaskCategory.FRONTEND, f"Got {decision.category}"
        return True, f"Category: {decision.category.value}"
    
    @runner.test("Router: DevOps task categorization")
    def test_router_devops():
        from router import TaskRouter, TaskCategory
        router = TaskRouter()
        decision = router.route("Write a Dockerfile for a Node.js application")
        assert decision.category == TaskCategory.DEVOPS, f"Got {decision.category}"
        return True, f"Category: {decision.category.value}"
    
    @runner.test("Router: Complexity estimation")
    def test_router_complexity():
        from router import TaskRouter, Complexity
        router = TaskRouter()
        
        simple = router.route("Write a simple helper function")
        complex = router.route("Build a complete enterprise microservices platform")
        
        assert simple.complexity.level in [Complexity.TRIVIAL, Complexity.SIMPLE], f"Simple got {simple.complexity.level}"
        assert complex.complexity.level in [Complexity.COMPLEX, Complexity.LARGE], f"Complex got {complex.complexity.level}"
        
        return True, f"Simple: {simple.complexity.level.value}, Complex: {complex.complexity.level.value}"
    
    @runner.test("Router: Language detection")
    def test_router_language():
        from router import TaskRouter
        router = TaskRouter()
        
        py = router.route("Build a FastAPI backend service in Python")
        ts = router.route("Create a TypeScript React component")
        
        assert py.language and py.language.language == "python", f"Python got {py.language}"
        assert ts.language and ts.language.language in ["typescript", "react"], f"TS got {ts.language}"
        
        return True, f"Python: {py.language.language}, TS: {ts.language.language}"
    
    @runner.test("Router: Model routing")
    def test_router_routing():
        from router import TaskRouter
        router = TaskRouter()
        decision = router.route("Build a REST API")
        
        assert len(decision.primary_models) >= 1, "No primary models"
        assert all(m in ["claude-code", "codex", "gemini", "grok"] for m in decision.primary_models)
        
        return True, f"Primary: {decision.primary_models}, Validators: {decision.validators}"
    
    test_router_backend()
    test_router_frontend()
    test_router_devops()
    test_router_complexity()
    test_router_language()
    test_router_routing()
    
    # -------------------------------------------------------------------------
    # Merger Tests
    # -------------------------------------------------------------------------
    print("\n🔀 Merger Tests")
    
    @runner.test("Merger: Code block extraction")
    def test_merger_blocks():
        from merger import CodeBlockParser
        parser = CodeBlockParser()
        
        output = '''Here's code:
```python
def hello():
    return "world"
```
And more:
```javascript
console.log("hi");
```
'''
        blocks = parser.parse(output, "test-model")
        assert len(blocks) == 2, f"Expected 2 blocks, got {len(blocks)}"
        assert blocks[0].language == "python"
        assert blocks[1].language == "javascript"
        
        return True, f"Found {len(blocks)} blocks: {[b.language for b in blocks]}"
    
    @runner.test("Merger: Python component parsing")
    def test_merger_components():
        from merger import PythonComponentParser, ComponentType
        parser = PythonComponentParser()
        
        code = '''
import os
from typing import List

MAX_SIZE = 100

class MyClass:
    def __init__(self):
        pass

def my_function(x: int) -> int:
    return x * 2
'''
        components = parser.parse(code, "test")
        
        types = [c.type for c in components]
        assert ComponentType.IMPORT in types, "Missing imports"
        assert ComponentType.CLASS in types, "Missing class"
        assert ComponentType.FUNCTION in types, "Missing function"
        assert ComponentType.CONSTANT in types, "Missing constant"
        
        return True, f"Found: {[c.type.value for c in components]}"
    
    @runner.test("Merger: Quality scoring")
    def test_merger_scoring():
        from merger import QualityScorer, CodeComponent, ComponentType
        scorer = QualityScorer()
        
        good_code = CodeComponent(
            type=ComponentType.FUNCTION,
            name="process_data",
            code='''
def process_data(items: List[str]) -> List[str]:
    """Process and filter data items."""
    try:
        return [item.strip() for item in items if item]
    except Exception as e:
        raise ValueError(f"Processing failed: {e}")
''',
            source_model="test"
        )
        
        bad_code = CodeComponent(
            type=ComponentType.FUNCTION,
            name="x",
            code="def x(a,b,c,d,e,f): return a+b",
            source_model="test"
        )
        
        good_score = scorer.score(good_code)
        bad_score = scorer.score(bad_code)
        
        assert good_score.total_score > bad_score.total_score, \
            f"Good ({good_score.total_score}) should beat bad ({bad_score.total_score})"
        
        return True, f"Good: {good_score.total_score}, Bad: {bad_score.total_score}"
    
    @runner.test("Merger: Consensus merge")
    def test_merger_consensus():
        from merger import ConsensusMerger
        merger = ConsensusMerger()
        
        result = merger.merge(SAMPLE_OUTPUTS, task="REST API endpoint")
        
        assert result.merged_code, "No merged code"
        assert result.validation_passed, f"Validation failed: {result.validation_errors}"
        assert len(result.components_used) > 0, "No components tracked"
        
        return True, f"Merged {len(result.components_used)} components, score: {result.total_score:.0f}"
    
    @runner.test("Merger: Syntax validation")
    def test_merger_validation():
        from merger import SyntaxValidator
        validator = SyntaxValidator()
        
        valid_code = "def foo(): return 42"
        invalid_code = "def foo( return 42"
        
        v1, e1 = validator.validate(valid_code)
        v2, e2 = validator.validate(invalid_code)
        
        assert v1 == True, f"Valid code failed: {e1}"
        assert v2 == False, "Invalid code should fail"
        
        return True, f"Valid: {v1}, Invalid: {v2} (errors: {e2})"
    
    test_merger_blocks()
    test_merger_components()
    test_merger_scoring()
    test_merger_consensus()
    test_merger_validation()
    
    # -------------------------------------------------------------------------
    # Validator Tests
    # -------------------------------------------------------------------------
    print("\n✅ Validator Tests")
    
    @runner.test("Validator: Selection logic")
    def test_validator_selection():
        from validator import select_validator
        
        # Claude + Codex should get Gemini
        v1 = select_validator(["claude-code", "codex"])
        assert v1 == "gemini", f"Expected gemini, got {v1}"
        
        # Gemini + Claude should get Codex
        v2 = select_validator(["gemini", "claude-code"])
        assert v2 == "codex", f"Expected codex, got {v2}"
        
        return True, f"claude+codex→{v1}, gemini+claude→{v2}"
    
    @runner.test("Validator: Escalation triggers")
    def test_validator_escalation():
        from validator import ValidationResult, ValidationStatus, OutputAnalysis, should_escalate
        
        # Low confidence should escalate
        low_conf = ValidationResult(
            task="test",
            validator_model="test",
            status=ValidationStatus.NEEDS_REVIEW,
            confidence=0.75,
            analyses={},
            merge_recommendation=[],
            merge_strategy="use_best",
            concerns=[],
            needs_human_review=False,
            review_reasons=[],
            summary=""
        )
        
        should, reasons = should_escalate(low_conf)
        assert should == True, "Low confidence should escalate"
        assert any("confidence" in r.lower() for r in reasons)
        
        return True, f"Escalation reasons: {reasons}"
    
    test_validator_selection()
    test_validator_escalation()
    
    # -------------------------------------------------------------------------
    # Orchestrator Integration Tests
    # -------------------------------------------------------------------------
    print("\n🎼 Orchestrator Integration Tests")
    
    @runner.test("Orchestrator: Task analysis")
    def test_orch_analysis():
        from orchestrator import analyze_task, ExecutionMode
        
        cat, mode = analyze_task("Build a simple REST API endpoint")
        
        assert cat in ["backend", "generic"], f"Unexpected category: {cat}"
        assert isinstance(mode, ExecutionMode)
        
        return True, f"Category: {cat}, Mode: {mode.value}"
    
    @runner.test("Orchestrator: Routing integration")
    def test_orch_routing():
        from orchestrator import get_routing, ExecutionMode
        
        primaries, validators = get_routing("backend", ExecutionMode.MEDIUM, "Build a REST API")
        
        assert len(primaries) >= 1, "No primary models"
        assert len(validators) >= 0, "Validators check failed"
        
        return True, f"Primary: {primaries}, Validators: {validators}"
    
    @runner.test("Orchestrator: Scoring function")
    def test_orch_scoring():
        from orchestrator import score_output, ModelOutput
        
        good = ModelOutput(
            model="test",
            code='''
def process(data: List[str]) -> List[str]:
    """Process data items."""
    try:
        return [d.strip() for d in data]
    except Exception as e:
        raise ValueError(str(e))
''',
            explanation="test",
            execution_time=1.0,
            success=True
        )
        
        bad = ModelOutput(
            model="test",
            code="x=1",
            explanation="test",
            execution_time=1.0,
            success=True
        )
        
        good_score = score_output(good, "test task")
        bad_score = score_output(bad, "test task")
        
        assert good_score > bad_score, f"Good ({good_score}) should beat bad ({bad_score})"
        
        return True, f"Good: {good_score}, Bad: {bad_score}"
    
    @runner.test("Orchestrator: Merge with sample outputs")
    def test_orch_merge():
        from orchestrator import merge_outputs, ModelOutput
        
        outputs = [
            ModelOutput(
                model="claude-code",
                code=SAMPLE_OUTPUTS["claude-code"],
                raw_output=SAMPLE_OUTPUTS["claude-code"],
                explanation="",
                execution_time=1.0,
                success=True,
                score=85
            ),
            ModelOutput(
                model="codex",
                code=SAMPLE_OUTPUTS["codex"],
                raw_output=SAMPLE_OUTPUTS["codex"],
                explanation="",
                execution_time=1.0,
                success=True,
                score=75
            )
        ]
        
        merged_code, explanation = merge_outputs(outputs, "REST API")
        
        assert merged_code, "No merged code"
        assert "def" in merged_code or "class" in merged_code, "No code structure"
        
        return True, f"Merged {len(merged_code)} chars: {explanation[:50]}..."
    
    test_orch_analysis()
    test_orch_routing()
    test_orch_scoring()
    test_orch_merge()
    
    # -------------------------------------------------------------------------
    # Live Grok API Test (optional)
    # -------------------------------------------------------------------------
    if live:
        print("\n🌐 Live API Tests")
        
        @runner.test("Grok API: Connection")
        def test_grok_connection():
            api_key = os.getenv("GROK_API_KEY")
            if not api_key:
                return False, "GROK_API_KEY not set"
            
            from grok_client import GrokClient
            client = GrokClient(api_key=api_key)
            response = client.chat("Say 'test successful' in exactly those words.")
            
            assert response.content, "No response"
            assert response.total_tokens > 0, "No tokens used"
            
            return True, f"Response: {response.content[:50]}... ({response.total_tokens} tokens)"
        
        @runner.test("Grok API: Code generation")
        def test_grok_code():
            api_key = os.getenv("GROK_API_KEY")
            if not api_key:
                return False, "GROK_API_KEY not set"
            
            from grok_client import GrokClient
            client = GrokClient(api_key=api_key)
            response = client.code_task("Write a Python function to check if a number is prime")
            
            assert response.content, "No response"
            code = response.first_code_block or response.content
            assert "def" in code, "No function in response"
            
            return True, f"Generated {len(code)} chars of code"
        
        test_grok_connection()
        test_grok_code()
    
    # -------------------------------------------------------------------------
    # Benchmark Tests
    # -------------------------------------------------------------------------
    print("\n📊 Benchmark Tests")
    
    @runner.test("Benchmark: Task suite loaded")
    def test_benchmark_tasks():
        from benchmark import BENCHMARK_TASKS
        
        assert len(BENCHMARK_TASKS) > 0, "No benchmark tasks"
        
        categories = set(t.category.value for t in BENCHMARK_TASKS)
        assert len(categories) >= 3, f"Only {len(categories)} categories"
        
        return True, f"{len(BENCHMARK_TASKS)} tasks across {len(categories)} categories"
    
    @runner.test("Benchmark: Scoring criteria")
    def test_benchmark_scoring():
        from benchmark import SCORING_CRITERIA
        
        total_weight = sum(c["weight"] for c in SCORING_CRITERIA.values())
        assert total_weight == 100, f"Weights sum to {total_weight}, expected 100"
        
        return True, f"6 criteria, {total_weight} total points"
    
    test_benchmark_tasks()
    test_benchmark_scoring()
    
    # -------------------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------------------
    return runner.summary()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Orchestrator Test Suite")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--live", "-l", action="store_true", help="Include live API tests")
    
    args = parser.parse_args()
    
    success = run_tests(verbose=args.verbose, live=args.live)
    sys.exit(0 if success else 1)
