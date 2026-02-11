#!/usr/bin/env python3
"""
Consensus Merger

Combines the best parts from multiple model outputs into a single solution:
- Code block parsing for each model format
- Component/function grouping
- Quality scoring
- AST-based merging
- Syntax validation

Usage:
    from merger import ConsensusMerger, MergeResult
    
    merger = ConsensusMerger()
    result = merger.merge(outputs, task="Build REST API")
    
    print(result.merged_code)
    print(f"Score: {result.total_score}")
"""

import ast
import re
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any
from enum import Enum
import textwrap


# =============================================================================
# DATA CLASSES
# =============================================================================

class ComponentType(Enum):
    """Types of code components."""
    IMPORT = "import"
    CLASS = "class"
    FUNCTION = "function"
    CONSTANT = "constant"
    TYPE_DEF = "type_def"
    DECORATOR = "decorator"
    MAIN = "main"
    OTHER = "other"


@dataclass
class CodeBlock:
    """Extracted code block from model output."""
    content: str
    language: str
    source_model: str
    start_line: int = 0
    end_line: int = 0
    
    @property
    def hash(self) -> str:
        """Content hash for deduplication."""
        normalized = re.sub(r'\s+', ' ', self.content.strip())
        return hashlib.md5(normalized.encode()).hexdigest()[:8]


@dataclass
class CodeComponent:
    """A parsed component (function, class, import, etc.)."""
    type: ComponentType
    name: str
    code: str
    source_model: str
    dependencies: Set[str] = field(default_factory=set)
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def signature(self) -> str:
        """Unique signature for matching similar components."""
        if self.type == ComponentType.FUNCTION:
            # Extract function signature
            match = re.match(r'(async\s+)?def\s+(\w+)\s*\(([^)]*)\)', self.code)
            if match:
                return f"func:{match.group(2)}"
        elif self.type == ComponentType.CLASS:
            match = re.match(r'class\s+(\w+)', self.code)
            if match:
                return f"class:{match.group(1)}"
        elif self.type == ComponentType.IMPORT:
            return f"import:{self.code.strip()}"
        return f"{self.type.value}:{self.name}"


@dataclass
class ScoredComponent:
    """Component with quality scores."""
    component: CodeComponent
    scores: Dict[str, int]
    total_score: int
    issues: List[str] = field(default_factory=list)


@dataclass
class MergeResult:
    """Result of consensus merge."""
    merged_code: str
    total_score: float
    components_used: Dict[str, str]  # component_name -> source_model
    merge_log: List[str]
    validation_passed: bool
    validation_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "merged_code_length": len(self.merged_code),
            "total_score": self.total_score,
            "components_used": self.components_used,
            "validation_passed": self.validation_passed,
            "validation_errors": self.validation_errors
        }


# =============================================================================
# CODE BLOCK PARSER
# =============================================================================

class CodeBlockParser:
    """Parse code blocks from model outputs."""
    
    # Markdown code block pattern
    CODE_BLOCK_PATTERN = re.compile(
        r'```(\w*)\n(.*?)```',
        re.DOTALL
    )
    
    # Language aliases
    LANGUAGE_ALIASES = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "tsx": "typescript",
        "jsx": "javascript",
        "sh": "bash",
        "shell": "bash",
        "yml": "yaml"
    }
    
    def parse(self, output: str, source_model: str) -> List[CodeBlock]:
        """
        Extract all code blocks from model output.
        
        Args:
            output: Raw model output
            source_model: Name of the source model
            
        Returns:
            List of CodeBlock objects
        """
        blocks = []
        
        for match in self.CODE_BLOCK_PATTERN.finditer(output):
            language = match.group(1).lower() or "text"
            language = self.LANGUAGE_ALIASES.get(language, language)
            content = match.group(2).strip()
            
            if content:
                blocks.append(CodeBlock(
                    content=content,
                    language=language,
                    source_model=source_model,
                    start_line=output[:match.start()].count('\n') + 1,
                    end_line=output[:match.end()].count('\n') + 1
                ))
        
        # If no code blocks found, treat entire output as code
        if not blocks and output.strip():
            blocks.append(CodeBlock(
                content=output.strip(),
                language="text",
                source_model=source_model
            ))
        
        return blocks
    
    def deduplicate(self, blocks: List[CodeBlock]) -> List[CodeBlock]:
        """Remove duplicate code blocks based on content hash."""
        seen = set()
        unique = []
        
        for block in blocks:
            if block.hash not in seen:
                seen.add(block.hash)
                unique.append(block)
        
        return unique


# =============================================================================
# COMPONENT PARSER (Python AST)
# =============================================================================

class PythonComponentParser:
    """Parse Python code into components using AST."""
    
    def parse(self, code: str, source_model: str) -> List[CodeComponent]:
        """
        Parse Python code into components.
        
        Args:
            code: Python source code
            source_model: Name of the source model
            
        Returns:
            List of CodeComponent objects
        """
        components = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Return as single component if parsing fails
            return [CodeComponent(
                type=ComponentType.OTHER,
                name="unparsed",
                code=code,
                source_model=source_model
            )]
        
        lines = code.split('\n')
        
        for node in ast.iter_child_nodes(tree):
            component = self._node_to_component(node, lines, source_model)
            if component:
                components.append(component)
        
        return components
    
    def _node_to_component(
        self, 
        node: ast.AST, 
        lines: List[str],
        source_model: str
    ) -> Optional[CodeComponent]:
        """Convert AST node to CodeComponent."""
        
        if isinstance(node, ast.Import):
            code = f"import {', '.join(a.name for a in node.names)}"
            return CodeComponent(
                type=ComponentType.IMPORT,
                name=node.names[0].name,
                code=code,
                source_model=source_model
            )
        
        elif isinstance(node, ast.ImportFrom):
            names = ', '.join(a.name for a in node.names)
            code = f"from {node.module or ''} import {names}"
            return CodeComponent(
                type=ComponentType.IMPORT,
                name=f"{node.module}.{node.names[0].name}",
                code=code,
                source_model=source_model
            )
        
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            code = self._get_source(node, lines)
            deps = self._extract_dependencies(node)
            return CodeComponent(
                type=ComponentType.FUNCTION,
                name=node.name,
                code=code,
                source_model=source_model,
                dependencies=deps,
                metadata={
                    "args": [a.arg for a in node.args.args],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "decorators": [self._get_decorator_name(d) for d in node.decorator_list],
                    "has_docstring": ast.get_docstring(node) is not None
                }
            )
        
        elif isinstance(node, ast.ClassDef):
            code = self._get_source(node, lines)
            deps = self._extract_dependencies(node)
            return CodeComponent(
                type=ComponentType.CLASS,
                name=node.name,
                code=code,
                source_model=source_model,
                dependencies=deps,
                metadata={
                    "bases": [self._get_name(b) for b in node.bases],
                    "methods": [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                    "has_docstring": ast.get_docstring(node) is not None
                }
            )
        
        elif isinstance(node, ast.Assign):
            # Constants (uppercase names)
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    code = self._get_source(node, lines)
                    return CodeComponent(
                        type=ComponentType.CONSTANT,
                        name=target.id,
                        code=code,
                        source_model=source_model
                    )
        
        return None
    
    def _get_source(self, node: ast.AST, lines: List[str]) -> str:
        """Extract source code for an AST node."""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            start = node.lineno - 1
            end = node.end_lineno
            return '\n'.join(lines[start:end])
        return ""
    
    def _get_decorator_name(self, node: ast.AST) -> str:
        """Get decorator name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._get_decorator_name(node.func)
        return "unknown"
    
    def _get_name(self, node: ast.AST) -> str:
        """Get name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return "unknown"
    
    def _extract_dependencies(self, node: ast.AST) -> Set[str]:
        """Extract names used within a node."""
        deps = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Name):
                deps.add(child.id)
            elif isinstance(child, ast.Attribute):
                deps.add(self._get_name(child))
        return deps


# =============================================================================
# QUALITY SCORER
# =============================================================================

class QualityScorer:
    """Score code components based on quality criteria."""
    
    CRITERIA = {
        "correctness": 20,    # Valid syntax, no obvious bugs
        "structure": 20,      # Well-organized, modular
        "performance": 15,    # Efficient patterns
        "best_practices": 20, # Follows conventions
        "documentation": 15,  # Comments, docstrings
        "testing": 10         # Error handling, test hints
    }
    
    def score(self, component: CodeComponent) -> ScoredComponent:
        """
        Score a code component.
        
        Args:
            component: CodeComponent to score
            
        Returns:
            ScoredComponent with detailed scores
        """
        code = component.code
        scores = {}
        issues = []
        
        # Correctness (20 pts)
        correctness = 15  # Base
        try:
            if component.type != ComponentType.IMPORT:
                ast.parse(code)
            correctness += 5
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            correctness = 5
        scores["correctness"] = correctness
        
        # Structure (20 pts)
        structure = 10
        if component.type == ComponentType.FUNCTION:
            # Check function length
            lines = code.count('\n') + 1
            if lines < 30:
                structure += 5
            elif lines > 100:
                structure -= 5
                issues.append("Function too long (>100 lines)")
            # Check for single responsibility (rough heuristic)
            if code.count('def ') <= 1:
                structure += 3
            # Check for return statement
            if 'return' in code:
                structure += 2
        elif component.type == ComponentType.CLASS:
            # Check class organization
            if '__init__' in code:
                structure += 5
            if code.count('def ') > 1:
                structure += 3
        scores["structure"] = min(structure, 20)
        
        # Performance (15 pts)
        performance = 10
        # Check for common anti-patterns
        if 'time.sleep' in code and 'async' not in code:
            performance -= 3
            issues.append("Blocking sleep in sync code")
        if re.search(r'for.*in.*range.*len\(', code):
            performance -= 2
            issues.append("Using range(len()) instead of enumerate")
        if '+ ""' in code or "+ ''" in code:
            performance -= 2
        scores["performance"] = max(performance, 0)
        
        # Best Practices (20 pts)
        best_practices = 10
        # Type hints
        if ': ' in code and '->' in code:
            best_practices += 5
        # Constants (uppercase)
        if component.type == ComponentType.CONSTANT:
            if component.name.isupper():
                best_practices += 3
        # Naming conventions
        if component.type == ComponentType.FUNCTION:
            if re.match(r'^[a-z_][a-z0-9_]*$', component.name):
                best_practices += 3
            else:
                issues.append("Function name not snake_case")
        elif component.type == ComponentType.CLASS:
            if re.match(r'^[A-Z][a-zA-Z0-9]*$', component.name):
                best_practices += 3
            else:
                issues.append("Class name not PascalCase")
        scores["best_practices"] = min(best_practices, 20)
        
        # Documentation (15 pts)
        documentation = 5
        if '"""' in code or "'''" in code:
            documentation += 8
        if '#' in code:
            documentation += 2
        # Check metadata for docstring
        if component.metadata.get("has_docstring"):
            documentation += 2
        scores["documentation"] = min(documentation, 15)
        
        # Testing/Error Handling (10 pts)
        testing = 3
        if 'try:' in code or 'except' in code:
            testing += 4
        if 'raise' in code:
            testing += 2
        if 'assert' in code or 'test' in component.name.lower():
            testing += 3
        scores["testing"] = min(testing, 10)
        
        total = sum(scores.values())
        
        return ScoredComponent(
            component=component,
            scores=scores,
            total_score=total,
            issues=issues
        )


# =============================================================================
# COMPONENT GROUPER
# =============================================================================

class ComponentGrouper:
    """Group similar components from different models."""
    
    def group(
        self, 
        components: List[CodeComponent]
    ) -> Dict[str, List[CodeComponent]]:
        """
        Group components by their signature.
        
        Args:
            components: List of components from all models
            
        Returns:
            Dict mapping signature to list of implementations
        """
        groups: Dict[str, List[CodeComponent]] = {}
        
        for comp in components:
            sig = comp.signature
            if sig not in groups:
                groups[sig] = []
            groups[sig].append(comp)
        
        return groups
    
    def find_best(
        self, 
        group: List[CodeComponent],
        scorer: QualityScorer
    ) -> CodeComponent:
        """
        Find the best component from a group.
        
        Args:
            group: List of similar components
            scorer: QualityScorer instance
            
        Returns:
            Best scoring component
        """
        if len(group) == 1:
            return group[0]
        
        scored = [(comp, scorer.score(comp).total_score) for comp in group]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[0][0]


# =============================================================================
# CODE MERGER
# =============================================================================

class CodeMerger:
    """Merge code components into final output."""
    
    def merge(
        self,
        components: List[CodeComponent],
        language: str = "python"
    ) -> str:
        """
        Merge components into single code file.
        
        Args:
            components: Ordered list of components to merge
            language: Target language
            
        Returns:
            Merged code string
        """
        if language == "python":
            return self._merge_python(components)
        else:
            # Generic merge - just concatenate
            return '\n\n'.join(c.code for c in components)
    
    def _merge_python(self, components: List[CodeComponent]) -> str:
        """Merge Python components with proper ordering."""
        
        # Group by type
        imports = []
        constants = []
        classes = []
        functions = []
        other = []
        main = []
        
        for comp in components:
            if comp.type == ComponentType.IMPORT:
                imports.append(comp)
            elif comp.type == ComponentType.CONSTANT:
                constants.append(comp)
            elif comp.type == ComponentType.CLASS:
                classes.append(comp)
            elif comp.type == ComponentType.FUNCTION:
                functions.append(comp)
            elif comp.type == ComponentType.MAIN:
                main.append(comp)
            else:
                other.append(comp)
        
        # Deduplicate imports
        seen_imports = set()
        unique_imports = []
        for imp in imports:
            normalized = re.sub(r'\s+', ' ', imp.code.strip())
            if normalized not in seen_imports:
                seen_imports.add(normalized)
                unique_imports.append(imp)
        
        # Build output
        sections = []
        
        # Imports (sorted)
        if unique_imports:
            import_lines = sorted(set(i.code.strip() for i in unique_imports))
            # Separate stdlib from third-party
            stdlib = [i for i in import_lines if not i.startswith('from ') or 
                     i.split()[1].split('.')[0] in {'os', 'sys', 're', 'json', 'time', 
                                                     'datetime', 'typing', 'pathlib', 
                                                     'collections', 'functools', 'asyncio'}]
            third_party = [i for i in import_lines if i not in stdlib]
            
            if stdlib:
                sections.append('\n'.join(stdlib))
            if third_party:
                sections.append('\n'.join(third_party))
        
        # Constants
        if constants:
            sections.append('\n'.join(c.code for c in constants))
        
        # Classes
        for cls in classes:
            sections.append(cls.code)
        
        # Functions
        for func in functions:
            sections.append(func.code)
        
        # Other
        for o in other:
            sections.append(o.code)
        
        # Main block
        if main:
            sections.append('\n'.join(m.code for m in main))
        
        return '\n\n\n'.join(sections)


# =============================================================================
# SYNTAX VALIDATOR
# =============================================================================

class SyntaxValidator:
    """Validate merged code syntax."""
    
    def validate(self, code: str, language: str = "python") -> Tuple[bool, List[str]]:
        """
        Validate code syntax.
        
        Args:
            code: Code to validate
            language: Programming language
            
        Returns:
            (is_valid, list of errors)
        """
        if language == "python":
            return self._validate_python(code)
        else:
            # For other languages, just check it's not empty
            return bool(code.strip()), []
    
    def _validate_python(self, code: str) -> Tuple[bool, List[str]]:
        """Validate Python syntax."""
        errors = []
        
        try:
            ast.parse(code)
            return True, []
        except SyntaxError as e:
            errors.append(f"Line {e.lineno}: {e.msg}")
            return False, errors


# =============================================================================
# CONSENSUS MERGER
# =============================================================================

class ConsensusMerger:
    """
    Main merger class that orchestrates the consensus process.
    """
    
    def __init__(self):
        self.block_parser = CodeBlockParser()
        self.component_parser = PythonComponentParser()
        self.scorer = QualityScorer()
        self.grouper = ComponentGrouper()
        self.code_merger = CodeMerger()
        self.validator = SyntaxValidator()
    
    def merge(
        self,
        outputs: Dict[str, str],
        task: str = "",
        language: str = "python"
    ) -> MergeResult:
        """
        Merge multiple model outputs into consensus code.
        
        Args:
            outputs: Dict mapping model name to output
            task: Original task (for context)
            language: Target language
            
        Returns:
            MergeResult with merged code and metadata
        """
        merge_log = []
        components_used = {}
        
        # 1. Parse code blocks from all outputs
        all_blocks = []
        for model, output in outputs.items():
            blocks = self.block_parser.parse(output, model)
            all_blocks.extend(blocks)
            merge_log.append(f"Parsed {len(blocks)} blocks from {model}")
        
        # Deduplicate blocks
        unique_blocks = self.block_parser.deduplicate(all_blocks)
        merge_log.append(f"After dedup: {len(unique_blocks)} unique blocks")
        
        # 2. Parse components from Python blocks
        all_components = []
        for block in unique_blocks:
            if block.language in ["python", "text"]:
                components = self.component_parser.parse(block.content, block.source_model)
                all_components.extend(components)
        
        merge_log.append(f"Parsed {len(all_components)} components")
        
        if not all_components:
            # No parseable components - use best raw block
            if unique_blocks:
                best_block = max(unique_blocks, key=lambda b: len(b.content))
                return MergeResult(
                    merged_code=best_block.content,
                    total_score=50.0,
                    components_used={"raw": best_block.source_model},
                    merge_log=merge_log + ["Using raw block (no parseable components)"],
                    validation_passed=True
                )
            return MergeResult(
                merged_code="",
                total_score=0.0,
                components_used={},
                merge_log=merge_log + ["No code found"],
                validation_passed=False,
                validation_errors=["No code to merge"]
            )
        
        # 3. Group similar components
        groups = self.grouper.group(all_components)
        merge_log.append(f"Grouped into {len(groups)} component groups")
        
        # 4. Select best from each group
        selected = []
        for sig, group in groups.items():
            best = self.grouper.find_best(group, self.scorer)
            selected.append(best)
            components_used[best.name] = best.source_model
            
            if len(group) > 1:
                models = [c.source_model for c in group]
                merge_log.append(f"  {sig}: chose {best.source_model} from {models}")
        
        # 5. Order components by dependency
        ordered = self._order_by_dependency(selected)
        
        # 6. Merge into final code
        merged_code = self.code_merger.merge(ordered, language)
        
        # 7. Validate syntax
        is_valid, errors = self.validator.validate(merged_code, language)
        
        if not is_valid:
            merge_log.append(f"Validation failed: {errors}")
            # Try to fix common issues
            merged_code = self._attempt_fix(merged_code, errors)
            is_valid, errors = self.validator.validate(merged_code, language)
        
        # 8. Calculate total score
        total_score = sum(self.scorer.score(c).total_score for c in selected) / len(selected) if selected else 0
        
        return MergeResult(
            merged_code=merged_code,
            total_score=total_score,
            components_used=components_used,
            merge_log=merge_log,
            validation_passed=is_valid,
            validation_errors=errors
        )
    
    def _order_by_dependency(self, components: List[CodeComponent]) -> List[CodeComponent]:
        """Order components so dependencies come first."""
        # Simple ordering: imports, constants, classes, functions, other
        order = {
            ComponentType.IMPORT: 0,
            ComponentType.CONSTANT: 1,
            ComponentType.TYPE_DEF: 2,
            ComponentType.CLASS: 3,
            ComponentType.FUNCTION: 4,
            ComponentType.DECORATOR: 5,
            ComponentType.MAIN: 6,
            ComponentType.OTHER: 7
        }
        return sorted(components, key=lambda c: order.get(c.type, 99))
    
    def _attempt_fix(self, code: str, errors: List[str]) -> str:
        """Attempt to fix common syntax issues."""
        # Common fixes
        fixes = [
            # Remove trailing commas in function calls
            (r',\s*\)', ')'),
            # Fix unclosed strings (very basic)
            (r'(["\'])([^"\']*?)$', r'\1\2\1'),
        ]
        
        fixed = code
        for pattern, replacement in fixes:
            fixed = re.sub(pattern, replacement, fixed, flags=re.MULTILINE)
        
        return fixed


# =============================================================================
# CLI
# =============================================================================

if __name__ == "__main__":
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Consensus Merger")
    parser.add_argument("--demo", action="store_true", help="Run demo")
    parser.add_argument("--file", "-f", nargs="+", help="Files to merge (model:file)")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if args.demo:
        # Demo with sample outputs
        outputs = {
            "claude-code": '''
Here's a REST API endpoint:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class User(BaseModel):
    """User model for API."""
    name: str
    email: str

@app.post("/users")
async def create_user(user: User):
    """Create a new user."""
    try:
        # Validate email format
        if "@" not in user.email:
            raise HTTPException(status_code=400, detail="Invalid email")
        return {"id": 1, "name": user.name, "email": user.email}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```
''',
            "codex": '''
```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    email: str

@app.post("/users")
def create_user(user: User):
    return {"id": 1, **user.dict()}
```
'''
        }
        
        merger = ConsensusMerger()
        result = merger.merge(outputs, task="REST API endpoint")
        
        print("=" * 60)
        print("MERGE LOG")
        print("=" * 60)
        for log in result.merge_log:
            print(f"  {log}")
        
        print("\n" + "=" * 60)
        print("MERGED CODE")
        print("=" * 60)
        print(result.merged_code)
        
        print("\n" + "=" * 60)
        print("RESULT")
        print("=" * 60)
        print(f"Score: {result.total_score:.1f}")
        print(f"Valid: {result.validation_passed}")
        print(f"Components: {result.components_used}")
    
    elif args.file:
        outputs = {}
        for spec in args.file:
            model, filepath = spec.split(":", 1)
            with open(filepath) as f:
                outputs[model] = f.read()
        
        merger = ConsensusMerger()
        result = merger.merge(outputs)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(result.merged_code)
    
    else:
        parser.print_help()
