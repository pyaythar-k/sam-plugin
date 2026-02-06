#!/usr/bin/env python3
"""
coverage_enforcer.py - Auto-detect test framework and enforce coverage thresholds

This script detects the test framework, runs coverage analysis, enforces
thresholds, generates badges, tracks trends, and updates TASKS.json with
coverage metrics.

Usage:
    python3 skills/sam-develop/scripts/coverage_enforcer.py . --check
    python3 skills/sam-develop/scripts/coverage_enforcer.py . --threshold 80 --json-output
    python3 skills/sam-develop/scripts/coverage_enforcer.py . --badge > coverage_badge.svg
    python3 skills/sam-develop/scripts/coverage_enforcer.py . --trend

Output:
    JSON with coverage metrics, pass/fail status, and timestamp
    SVG badge (with --badge flag)
    Updates TASKS.json checkpoint with coverage data
"""

import sys
import json
import re
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
import xml.etree.ElementTree as ET


@dataclass
class CoverageMetrics:
    """Coverage metrics for different code categories."""
    statements: float = 0.0
    branches: float = 0.0
    functions: float = 0.0
    lines: float = 0.0
    overall: float = 0.0

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class CoverageReport:
    """Complete coverage report with metadata."""
    metrics: CoverageMetrics = field(default_factory=CoverageMetrics)
    threshold: float = 80.0
    passed: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    framework: str = "unknown"
    uncovered_files: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "coverage": self.metrics.to_dict(),
            "threshold": self.threshold,
            "passed": self.passed,
            "timestamp": self.timestamp,
            "framework": self.framework,
            "uncovered_files": self.uncovered_files,
            "recommendations": self.recommendations
        }


class CoverageEnforcer:
    """Auto-detect test framework and enforce coverage thresholds."""

    def __init__(self, project_dir: Path, threshold: float = 80.0, ci_environment: str = "local"):
        self.project_dir = project_dir
        self.threshold = threshold
        self.framework: str = "unknown"
        self.ci_environment = ci_environment
        self.report: CoverageReport = CoverageReport(threshold=threshold)

        # Look for feature directory for TASKS.json updates
        self.feature_dir = self._find_feature_dir()

    def _find_feature_dir(self) -> Optional[Path]:
        """Find the .sam feature directory."""
        # Check if project_dir is a .sam feature directory
        if (self.project_dir / "TASKS.json").exists():
            return self.project_dir

        # Check parent directories
        for parent in [self.project_dir] + list(self.project_dir.parents):
            if (parent / "TASKS.json").exists():
                return parent

        return None

    def detect_framework(self) -> str:
        """Auto-detect the test framework from package configuration."""
        # Check for package.json (Node.js/TypeScript)
        package_json = self.project_dir / "package.json"
        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)

            # Check for Jest configuration
            if "jest" in package_data.get("devDependencies", {}) or \
               "jest" in package_data.get("dependencies", {}):
                self.framework = "jest"
                return "jest"

            # Check for Vitest configuration
            if "vitest" in package_data.get("devDependencies", {}):
                self.framework = "vitest"
                return "vitest"

            # Check for Mocha
            if "mocha" in package_data.get("devDependencies", {}):
                self.framework = "mocha"
                return "mocha"

        # Check for Python project
        pyproject = self.project_dir / "pyproject.toml"
        setup_py = self.project_dir / "setup.py"
        requirements = self.project_dir / "requirements.txt"

        if pyproject.exists() or setup_py.exists() or requirements.exists():
            # Check for pytest
            if requirements.exists():
                with open(requirements, 'r') as f:
                    if "pytest" in f.read():
                        self.framework = "pytest"
                        return "pytest"

            # Check pyproject.toml for pytest
            if pyproject.exists():
                with open(pyproject, 'r') as f:
                    if "pytest" in f.read():
                        self.framework = "pytest"
                        return "pytest"

        # Default assumption based on common patterns
        # If TypeScript files present, assume Jest/Vitest
        if list(self.project_dir.rglob("*.ts")) or list(self.project_dir.rglob("*.tsx")):
            self.framework = "jest"
            return "jest"

        # If Python files present, assume Pytest
        if list(self.project_dir.rglob("*.py")):
            self.framework = "pytest"
            return "pytest"

        return "unknown"

    def run_coverage(self) -> Dict:
        """Run coverage analysis based on detected framework."""
        print(f"  Detected framework: {self.framework}")

        if self.framework == "jest":
            return self._run_jest_coverage()
        elif self.framework == "vitest":
            return self._run_vitest_coverage()
        elif self.framework == "pytest":
            return self._run_pytest_coverage()
        else:
            raise ValueError(f"Unsupported framework: {self.framework}")

    def _run_jest_coverage(self) -> Dict:
        """Run Jest coverage collection."""
        try:
            # Run Jest with coverage
            result = subprocess.run(
                ["npm", "test", "--", "--coverage", "--coverageReporters=json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse coverage output
            coverage_file = self.project_dir / "coverage" / "coverage-final.json"
            if coverage_file.exists():
                return self._parse_jest_coverage(coverage_file)

            # Fallback: try to extract from stdout
            return self._parse_coverage_from_output(result.stdout)

        except subprocess.TimeoutExpired:
            return {"error": "Coverage run timed out"}
        except FileNotFoundError:
            return {"error": "npm not found"}
        except Exception as e:
            return {"error": str(e)}

    def _run_vitest_coverage(self) -> Dict:
        """Run Vitest coverage collection."""
        try:
            result = subprocess.run(
                ["npm", "test", "--", "--coverage"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Vitest uses the same output format as Jest
            coverage_file = self.project_dir / "coverage" / "coverage-final.json"
            if coverage_file.exists():
                return self._parse_jest_coverage(coverage_file)

            return self._parse_coverage_from_output(result.stdout)

        except Exception as e:
            return {"error": str(e)}

    def _run_pytest_coverage(self) -> Dict:
        """Run Pytest coverage collection."""
        try:
            # Run pytest with coverage plugin
            result = subprocess.run(
                ["python", "-m", "pytest", "--cov=.", "--cov-report=json", "--cov-report=term"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse coverage.json output
            coverage_file = self.project_dir / "coverage.json"
            if coverage_file.exists():
                return self._parse_python_coverage(coverage_file)

            return self._parse_coverage_from_output(result.stdout)

        except subprocess.TimeoutExpired:
            return {"error": "Coverage run timed out"}
        except FileNotFoundError:
            return {"error": "pytest or pytest-cov not found"}
        except Exception as e:
            return {"error": str(e)}

    def _parse_jest_coverage(self, coverage_file: Path) -> Dict:
        """Parse Jest coverage JSON output."""
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)

        # Calculate overall coverage
        total_statements = 0
        covered_statements = 0
        total_branches = 0
        covered_branches = 0
        total_functions = 0
        covered_functions = 0
        total_lines = 0
        covered_lines = 0

        uncovered_files = []

        for file_path, file_data in coverage_data.items():
            if file_path == "total":
                continue

            # Check for uncovered files
            file_statements = file_data.get("s", {})
            file_statements_total = len(file_statements)
            file_statements_covered = sum(1 for v in file_statements.values() if v > 0)

            total_statements += file_statements_total
            covered_statements += file_statements_covered

            # Track files with low coverage
            if file_statements_total > 0:
                file_coverage = (file_statements_covered / file_statements_total) * 100
                if file_coverage < self.threshold:
                    uncovered_files.append(f"{file_path}: {file_coverage:.1f}%")

            # Branches
            file_branches = file_data.get("b", {})
            for branch_data in file_branches.values():
                if isinstance(branch_data, list):
                    total_branches += len(branch_data)
                    covered_branches += sum(1 for v in branch_data if v > 0)

            # Functions
            file_functions = file_data.get("f", {})
            total_functions += len(file_functions)
            covered_functions += sum(1 for v in file_functions.values() if v > 0)

            # Lines
            file_lines = file_data.get("l", {})
            total_lines += len(file_lines)
            covered_lines += sum(1 for v in file_lines.values() if v > 0)

        # Calculate percentages
        metrics = CoverageMetrics(
            statements=(covered_statements / total_statements * 100) if total_statements > 0 else 0,
            branches=(covered_branches / total_branches * 100) if total_branches > 0 else 0,
            functions=(covered_functions / total_functions * 100) if total_functions > 0 else 0,
            lines=(covered_lines / total_lines * 100) if total_lines > 0 else 0
        )

        # Calculate overall
        metrics.overall = (
            metrics.statements + metrics.branches + metrics.functions + metrics.lines
        ) / 4

        return {
            "metrics": asdict(metrics),
            "uncovered_files": uncovered_files
        }

    def _parse_python_coverage(self, coverage_file: Path) -> Dict:
        """Parse Python coverage JSON output."""
        with open(coverage_file, 'r') as f:
            coverage_data = json.load(f)

        files = coverage_data.get("files", {})
        totals = coverage_data.get("totals", {})

        # Extract summary from totals
        metrics = CoverageMetrics(
            statements=totals.get("covered_lines", 0) / max(totals.get("num_statements", 1), 1) * 100,
            branches=0.0,  # Python coverage may not separate branches
            functions=0.0,
            lines=totals.get("covered_lines", 0) / max(totals.get("num_statements", 1), 1) * 100
        )

        # Calculate overall
        metrics.overall = metrics.lines  # Python primarily uses line coverage

        # Find uncovered files
        uncovered_files = []
        for file_path, file_data in files.items():
            summary = file_data.get("summary", {})
            total = summary.get("num_statements", 0)
            covered = summary.get("covered_lines", 0)
            if total > 0:
                coverage_pct = (covered / total) * 100
                if coverage_pct < self.threshold:
                    uncovered_files.append(f"{file_path}: {coverage_pct:.1f}%")

        return {
            "metrics": asdict(metrics),
            "uncovered_files": uncovered_files
        }

    def _parse_coverage_from_output(self, output: str) -> Dict:
        """Parse coverage from command-line output."""
        # Look for coverage percentage patterns
        # Example: "Statements: 85.5% | Branches: 78.2% | Functions: 92.1% | Lines: 84.8%"

        metrics = CoverageMetrics()

        # Parse statements
        stmt_match = re.search(r'Statements:\s+(\d+\.?\d*)%', output)
        if stmt_match:
            metrics.statements = float(stmt_match.group(1))

        # Parse branches
        branch_match = re.search(r'Branches:\s+(\d+\.?\d*)%', output)
        if branch_match:
            metrics.branches = float(branch_match.group(1))

        # Parse functions
        func_match = re.search(r'Functions:\s+(\d+\.?\d*)%', output)
        if func_match:
            metrics.functions = float(func_match.group(1))

        # Parse lines
        line_match = re.search(r'Lines:\s+(\d+\.?\d*)%', output)
        if line_match:
            metrics.lines = float(line_match.group(1))

        # Calculate overall
        if any([metrics.statements, metrics.branches, metrics.functions, metrics.lines]):
            metrics.overall = (
                metrics.statements + metrics.branches + metrics.functions + metrics.lines
            ) / 4
        else:
            # Try to find a single coverage percentage
            coverage_match = re.search(r'Coverage:\s+(\d+\.?\d*)%', output)
            if coverage_match:
                metrics.overall = float(coverage_match.group(1))
                metrics.statements = metrics.overall
                metrics.lines = metrics.overall

        return {
            "metrics": asdict(metrics),
            "uncovered_files": []
        }

    def parse_coverage_report(self, report_path: Path) -> Dict:
        """Parse an existing coverage report file."""
        if report_path.suffix == ".json":
            with open(report_path, 'r') as f:
                return json.load(f)
        elif report_path.suffix in [".xml", ".lcov"]:
            return self._parse_xml_coverage(report_path)
        else:
            raise ValueError(f"Unsupported report format: {report_path.suffix}")

    def _parse_xml_coverage(self, report_path: Path) -> Dict:
        """Parse XML coverage report (e.g., Cobertura format)."""
        tree = ET.parse(report_path)
        root = tree.getroot()

        metrics = CoverageMetrics()

        # Extract metrics from XML
        for element in root.iter():
            if element.tag.endswith("coverage"):
                metrics.lines = float(element.get("line-rate", "0")) * 100
                metrics.branches = float(element.get("branch-rate", "0")) * 100

        metrics.overall = (metrics.lines + metrics.branches) / 2
        metrics.statements = metrics.lines
        metrics.functions = metrics.lines  # Approximation

        return {
            "metrics": asdict(metrics)
        }

    def enforce_threshold(self, coverage: float) -> bool:
        """Check if coverage meets the threshold."""
        passed = coverage >= self.threshold
        self.report.passed = passed

        if not passed:
            self.report.recommendations.append(
                f"Coverage ({coverage:.2f}%) is below threshold ({self.threshold}%)"
            )

        return passed

    def generate_badge(self, coverage: float) -> str:
        """Generate an SVG coverage badge."""
        color = "#4c1" if coverage >= self.threshold else "#e05d44"

        badge = f'''<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="120" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h55v20H0z"/>
    <path fill="{color}" d="M55 0h65v20H55z"/>
    <path fill="url(#b)" d="M0 0h120v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="27.5" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="27.5" y="14">coverage</text>
    <text x="87.5" y="15" fill="#010101" fill-opacity=".3">{coverage:.0f}%</text>
    <text x="87.5" y="14">{coverage:.0f}%</text>
  </g>
</svg>'''

        return badge

    def generate_ci_badge(self) -> str:
        """Generate badge for CI/CD systems."""
        if self.ci_environment == "github":
            return self._generate_github_status()
        elif self.ci_environment == "gitlab":
            return self._generate_gitlab_badge()
        else:
            return self.generate_badge(self.report.metrics.overall)

    def _generate_github_status(self) -> str:
        """Generate GitHub Actions status compatible output."""
        if self.report.passed:
            return f"✅ Coverage: {self.report.metrics.overall:.1f}% (passed)"
        else:
            return f"❌ Coverage: {self.report.metrics.overall:.1f}% (below {self.threshold}%)"

    def _generate_gitlab_badge(self) -> str:
        """Generate GitLab CI badge URL format."""
        coverage = self.report.metrics.overall
        if coverage >= self.threshold:
            color = "brightgreen"
        else:
            color = "red"
        return f"![coverage](https://img.shields.io/badge/coverage-{coverage:.0f}%25-{color})"

    def track_trend(self) -> List[Dict]:
        """Load historical coverage data and track trends."""
        if not self.feature_dir:
            return []

        # Try to load TASKS.json
        tasks_file = self.feature_dir / "TASKS.json"
        if not tasks_file.exists():
            return []

        with open(tasks_file, 'r') as f:
            tasks_data = json.load(f)

        checkpoint = tasks_data.get("checkpoint", {})
        existing_trend = checkpoint.get("coverage_trend", [])

        # Add current coverage to trend
        existing_trend.append({
            "timestamp": self.report.timestamp,
            "coverage": self.report.metrics.overall,
            "threshold": self.threshold,
            "passed": self.report.passed
        })

        # Keep only last 10 entries
        if len(existing_trend) > 10:
            existing_trend = existing_trend[-10:]

        return existing_trend

    def update_tasks_json(self, coverage: Dict) -> None:
        """Update TASKS.json checkpoint with coverage data."""
        if not self.feature_dir:
            return

        tasks_file = self.feature_dir / "TASKS.json"
        if not tasks_file.exists():
            return

        with open(tasks_file, 'r') as f:
            tasks_data = json.load(f)

        # Get or create checkpoint
        checkpoint = tasks_data.setdefault("checkpoint", {})

        # Update coverage fields
        checkpoint["coverage_last_checked"] = self.report.timestamp
        checkpoint["coverage_percentage"] = coverage.get("metrics", {}).get("overall", 0)

        # Track trend
        trend = self.track_trend()
        checkpoint["coverage_trend"] = trend

        # Write back
        with open(tasks_file, 'w') as f:
            json.dump(tasks_data, f, indent=2)

        print(f"  ✓ Updated TASKS.json checkpoint with coverage data")


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 coverage_enforcer.py <project_dir> [--check] [--threshold N] [--json-output] [--badge] [--trend]")
        print("Example: python3 coverage_enforcer.py . --check")
        print("Example: python3 coverage_enforcer.py . --threshold 80 --json-output")
        print("Example: python3 coverage_enforcer.py . --badge > coverage_badge.svg")
        print("Example: python3 coverage_enforcer.py . --trend")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    threshold = 80.0
    check_only = False
    json_output = False
    generate_badge = False
    show_trend = False

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--check":
            check_only = True
            i += 1
        elif sys.argv[i] == "--threshold" and i + 1 < len(sys.argv):
            threshold = float(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--json-output":
            json_output = True
            i += 1
        elif sys.argv[i] == "--badge":
            generate_badge = True
            i += 1
        elif sys.argv[i] == "--trend":
            show_trend = True
            i += 1
        else:
            i += 1

    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    # Create enforcer
    enforcer = CoverageEnforcer(project_dir, threshold)

    # Detect framework
    framework = enforcer.detect_framework()
    print(f"Framework: {framework}")

    # Run coverage
    coverage_result = enforcer.run_coverage()

    # Parse metrics
    if "error" in coverage_result:
        print(f"Error running coverage: {coverage_result['error']}")
        sys.exit(1)

    metrics_dict = coverage_result.get("metrics", {})
    metrics = CoverageMetrics(**{k: float(v) for k, v in metrics_dict.items()})
    enforcer.report.metrics = metrics
    enforcer.report.framework = framework
    enforcer.report.uncovered_files = coverage_result.get("uncovered_files", [])

    # Generate recommendations
    if metrics.overall < threshold:
        if enforcer.report.uncovered_files:
            enforcer.report.recommendations.append(
                f"Focus on files with lowest coverage: {', '.join(enforcer.report.uncovered_files[:3])}"
            )

    # Enforce threshold
    passed = enforcer.enforce_threshold(metrics.overall)

    # Output results
    if generate_badge:
        badge = enforcer.generate_badge(metrics.overall)
        print(badge)
    elif show_trend:
        trend = enforcer.track_trend()
        print(json.dumps(trend, indent=2))
    elif json_output:
        print(json.dumps(enforcer.report.to_dict(), indent=2))
    else:
        print(f"\nCoverage Report:")
        print(f"  Statements: {metrics.statements:.2f}%")
        print(f"  Branches: {metrics.branches:.2f}%")
        print(f"  Functions: {metrics.functions:.2f}%")
        print(f"  Lines: {metrics.lines:.2f}%")
        print(f"  Overall: {metrics.overall:.2f}%")
        print(f"  Threshold: {threshold}%")
        print(f"  Status: {'✓ PASSED' if passed else '✗ FAILED'}")

        if enforcer.report.uncovered_files:
            print(f"\nFiles below threshold:")
            for file in enforcer.report.uncovered_files[:5]:
                print(f"  - {file}")

        if enforcer.report.recommendations:
            print(f"\nRecommendations:")
            for rec in enforcer.report.recommendations:
                print(f"  - {rec}")

    # Update TASKS.json
    if not generate_badge and not show_trend:
        enforcer.update_tasks_json(enforcer.report.to_dict())

    # Exit with appropriate code
    if check_only and not passed:
        sys.exit(1)
    elif not passed:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
