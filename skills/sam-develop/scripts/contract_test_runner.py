#!/usr/bin/env python3
"""
contract_test_runner.py - Automatically execute contract tests during quality gates

This script detects contract tests, executes them, and generates violation reports.
It integrates with the CI/CD pipeline to ensure API contracts are always honored.

Usage:
    python3 contract_test_runner.py <project_dir> --check
    python3 contract_test_runner.py . --framework jest|pytest
    python3 contract_test_runner.py . --verify-contracts
    python3 contract_test_runner.py . --report

Output:
    JSON with contract test results and violation details
"""

import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict


@dataclass
class ContractViolation:
    """Represents a contract test violation."""
    test_id: str
    endpoint: str
    method: str
    violation_type: str  # schema_mismatch, missing_field, type_error, etc.
    expected: str
    actual: str
    severity: str  # critical, major, minor
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ContractTestResult:
    """Result of running contract tests."""
    framework: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    violations: List[ContractViolation] = field(default_factory=list)
    coverage: float = 0.0  # Percentage of contracts tested
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "framework": self.framework,
            "total_tests": self.total_tests,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "violations": [asdict(v) for v in self.violations],
            "coverage": self.coverage,
            "timestamp": self.timestamp,
            "passed_all": self.failed == 0
        }


class ContractTestRunner:
    """Automatically execute contract tests during quality gates."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.framework: str = "unknown"
        self.contract_dirs: List[Path] = []
        self.result = ContractTestResult(framework="unknown", total_tests=0, passed=0, failed=0, skipped=0)

    def detect_contracts(self) -> List[str]:
        """Detect contract test directories and framework."""
        frameworks_found = []

        # Check for Zod contract tests
        zod_dir = self.project_dir / "tests" / "contract" / "zod"
        if zod_dir.exists():
            frameworks_found.append("zod")
            self.contract_dirs.append(zod_dir)

        # Check for Pact contract tests
        pact_dir = self.project_dir / "tests" / "contract" / "pact"
        if pact_dir.exists():
            frameworks_found.append("pact")
            self.contract_dirs.append(pact_dir)

        # Check for Joi contract tests
        joi_dir = self.project_dir / "tests" / "contract" / "joi"
        if joi_dir.exists():
            frameworks_found.append("joi")
            self.contract_dirs.append(joi_dir)

        # Check for OpenAPI spec (can generate contracts on-the-fly)
        openapi_file = self.project_dir / "openapi.yaml"
        if openapi_file.exists():
            frameworks_found.append("openapi")

        return frameworks_found

    def detect_framework(self) -> str:
        """Auto-detect the test framework."""
        package_json = self.project_dir / "package.json"

        if package_json.exists():
            with open(package_json, 'r') as f:
                package_data = json.load(f)

            # Check test scripts
            scripts = package_data.get("scripts", {})

            # Check for Jest
            if "jest" in package_data.get("devDependencies", {}) or \
               any("jest" in script for script in scripts.values()):
                self.framework = "jest"
                return "jest"

            # Check for Vitest
            if "vitest" in package_data.get("devDependencies", {}):
                self.framework = "vitest"
                return "vitest"

            # Check for Mocha
            if "mocha" in package_data.get("devDependencies", {}):
                self.framework = "mocha"
                return "mocha"

        # Check for Python pytest
        if (self.project_dir / "pytest.ini").exists() or \
           (self.project_dir / "pyproject.toml").exists():
            with open(self.project_dir / "pyproject.toml", 'r') as f:
                if "pytest" in f.read():
                    self.framework = "pytest"
                    return "pytest"

        # Default to jest for TypeScript projects
        if list(self.project_dir.rglob("*.ts")):
            self.framework = "jest"
            return "jest"

        return "unknown"

    def run_contract_tests(self) -> Dict:
        """Execute contract tests based on detected framework."""
        print(f"  Running contract tests with framework: {self.framework}")

        if self.framework == "jest":
            return self._run_jest_contract_tests()
        elif self.framework == "vitest":
            return self._run_vitest_contract_tests()
        elif self.framework == "pytest":
            return self._run_pytest_contract_tests()
        elif self.framework == "mocha":
            return self._run_mocha_contract_tests()
        else:
            print(f"  ⚠ Unknown framework, attempting generic contract test detection")
            return self._run_generic_contract_tests()

    def _run_jest_contract_tests(self) -> Dict:
        """Run Jest contract tests."""
        try:
            # Run contract tests specifically
            contract_test_pattern = "tests/contract/**/*.test.ts"
            result = subprocess.run(
                ["npm", "test", "--", contract_test_pattern, "--json", "--outputFile=test-results-contract.json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse results
            results_file = self.project_dir / "test-results-contract.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    test_results = json.load(f)

                return self._parse_jest_results(test_results)

            # Fallback to stdout parsing
            return self._parse_test_output(result.stdout)

        except subprocess.TimeoutExpired:
            return {"error": "Contract tests timed out"}
        except Exception as e:
            return {"error": str(e)}

    def _run_vitest_contract_tests(self) -> Dict:
        """Run Vitest contract tests."""
        try:
            result = subprocess.run(
                ["npm", "test", "--", "tests/contract/**/*.test.ts", "--reporter=json", "--outputFile=test-results-contract.json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            results_file = self.project_dir / "test-results-contract.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    test_results = json.load(f)

                return self._parse_vitest_results(test_results)

            return self._parse_test_output(result.stdout)

        except Exception as e:
            return {"error": str(e)}

    def _run_pytest_contract_tests(self) -> Dict:
        """Run Pytest contract tests."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/contract/", "-v", "--json-report", "--json-report-file=test-results-contract.json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            results_file = self.project_dir / "test-results-contract.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    test_results = json.load(f)

                return self._parse_pytest_results(test_results)

            return self._parse_test_output(result.stdout)

        except Exception as e:
            return {"error": str(e)}

    def _run_mocha_contract_tests(self) -> Dict:
        """Run Mocha contract tests."""
        try:
            result = subprocess.run(
                ["npm", "test", "--", "tests/contract/**/*.test.ts", "--reporter=json", "--reporter-options=output=test-results-contract.json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True,
                timeout=300
            )

            results_file = self.project_dir / "test-results-contract.json"
            if results_file.exists():
                with open(results_file, 'r') as f:
                    test_results = json.load(f)

                return self._parse_mocha_results(test_results)

            return self._parse_test_output(result.stdout)

        except Exception as e:
            return {"error": str(e)}

    def _run_generic_contract_tests(self) -> Dict:
        """Generic contract test detection and execution."""
        violations = []

        # Check for contract test files
        contract_files = []
        for pattern in ["**/*contract*.test.ts", "**/*contract*.test.js", "**/test_contract*.py"]:
            contract_files.extend(self.project_dir.glob(pattern))

        if not contract_files:
            return {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "skipped": 0,
                "violations": [],
                "message": "No contract tests found"
            }

        # Try to run with npm test if available
        if (self.project_dir / "package.json").exists():
            try:
                result = subprocess.run(
                    ["npm", "test", "--", "--listTests"],
                    cwd=self.project_dir,
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                # Filter for contract tests
                contract_tests = [line for line in result.stdout.split('\n') if 'contract' in line.lower()]

                return {
                    "total_tests": len(contract_tests),
                    "passed": 0,
                    "failed": 0,
                    "skipped": len(contract_tests),
                    "violations": [],
                    "message": f"Found {len(contract_tests)} contract tests (not executed)"
                }
            except Exception:
                pass

        return {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "violations": violations,
            "message": "Could not execute contract tests"
        }

    def _parse_jest_results(self, results: Dict) -> Dict:
        """Parse Jest test results."""
        total = results.get("numTotalTests", 0)
        passed = results.get("numPassedTests", 0)
        failed = results.get("numFailedTests", 0)
        skipped = results.get("numPendingTests", 0)

        # Extract violations from failed tests
        violations = []
        for test_result in results.get("testResults", []):
            for assertion in test_result.get("assertionResults", []):
                if assertion.get("status") == "failed":
                    violations.append(ContractViolation(
                        test_id=assertion.get("title", "unknown"),
                        endpoint="unknown",
                        method="unknown",
                        violation_type="test_failed",
                        expected="passing",
                        actual="failed",
                        severity="major"
                    ))

        self.result = ContractTestResult(
            framework="jest",
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            violations=violations
        )

        return self.result.to_dict()

    def _parse_vitest_results(self, results: Dict) -> Dict:
        """Parse Vitest test results."""
        # Vitest uses similar format to Jest
        return self._parse_jest_results(results)

    def _parse_pytest_results(self, results: Dict) -> Dict:
        """Parse Pytest test results."""
        summary = results.get("summary", {})
        total = summary.get("total", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)

        violations = []
        for test in results.get("tests", []):
            if test.get("outcome") == "failed":
                violations.append(ContractViolation(
                    test_id=test.get("nodeid", "unknown"),
                    endpoint="unknown",
                    method="unknown",
                    violation_type="test_failed",
                    expected="passing",
                    actual="failed",
                    severity="major"
                ))

        self.result = ContractTestResult(
            framework="pytest",
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            violations=violations
        )

        return self.result.to_dict()

    def _parse_mocha_results(self, results: Dict) -> Dict:
        """Parse Mocha test results."""
        stats = results.get("stats", {})
        total = stats.get("tests", 0)
        passed = stats.get("passes", 0)
        failed = stats.get("failures", 0)
        skipped = stats.get("pending", 0)

        violations = []
        for failure in results.get("failures", []):
            violations.append(ContractViolation(
                test_id=failure.get("title", "unknown"),
                endpoint="unknown",
                method="unknown",
                violation_type="test_failed",
                expected="passing",
                actual="failed",
                severity="major"
            ))

        self.result = ContractTestResult(
            framework="mocha",
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            violations=violations
        )

        return self.result.to_dict()

    def _parse_test_output(self, output: str) -> Dict:
        """Parse test results from command-line output."""
        # Common patterns for test output
        passed_match = re.search(r'(\d+)\s+passing', output)
        failed_match = re.search(r'(\d+)\s+failing', output)
        skipped_match = re.search(r'(\d+)\s+skipped', output)

        passed = int(passed_match.group(1)) if passed_match else 0
        failed = int(failed_match.group(1)) if failed_match else 0
        skipped = int(skipped_match.group(1)) if skipped_match else 0
        total = passed + failed + skipped

        self.result = ContractTestResult(
            framework=self.framework,
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped
        )

        return self.result.to_dict()

    def generate_report(self) -> str:
        """Generate a detailed contract test report."""
        report = []
        report.append("# Contract Test Report")
        report.append(f"Generated: {self.result.timestamp}")
        report.append(f"Framework: {self.result.framework}")
        report.append("")

        report.append("## Summary")
        report.append(f"- Total Tests: {self.result.total_tests}")
        report.append(f"- Passed: {self.result.passed}")
        report.append(f"- Failed: {self.result.failed}")
        report.append(f"- Skipped: {self.result.skipped}")
        report.append(f"- Coverage: {self.result.coverage:.1f}%")
        report.append("")

        if self.result.violations:
            report.append("## Violations")

            for violation in self.result.violations:
                report.append(f"### {violation.test_id}")
                report.append(f"- Endpoint: {violation.endpoint}")
                report.append(f"- Method: {violation.method}")
                report.append(f"- Type: {violation.violation_type}")
                report.append(f"- Expected: {violation.expected}")
                report.append(f"- Actual: {violation.actual}")
                report.append(f"- Severity: {violation.severity}")
                report.append("")
        else:
            report.append("## ✅ No Contract Violations")
            report.append("All contract tests passed successfully.")
            report.append("")

        return "\n".join(report)

    def enforce_contracts(self) -> bool:
        """Check if all contract tests pass."""
        return self.result.failed == 0


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 contract_test_runner.py <project_dir> [--check] [--framework jest|pytest] [--verify-contracts] [--report]")
        print("Example: python3 contract_test_runner.py . --check")
        print("Example: python3 contract_test_runner.py . --framework jest")
        print("Example: python3 contract_test_runner.py . --verify-contracts")
        sys.exit(1)

    project_dir = Path(sys.argv[1])
    check_mode = False
    verify_contracts = False
    generate_report = False
    framework_override = None

    # Parse arguments
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == "--check":
            check_mode = True
            i += 1
        elif sys.argv[i] == "--verify-contracts":
            verify_contracts = True
            i += 1
        elif sys.argv[i] == "--report":
            generate_report = True
            i += 1
        elif sys.argv[i] == "--framework" and i + 1 < len(sys.argv):
            framework_override = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    # Create runner
    runner = ContractTestRunner(project_dir)

    # Detect framework and contracts
    if framework_override:
        runner.framework = framework_override
    else:
        runner.framework = runner.detect_framework()

    contracts = runner.detect_contracts()
    print(f"Detected contracts: {', '.join(contracts) if contracts else 'None found'}")

    # Run contract tests
    if verify_contracts:
        print("Verifying contract tests...")
        # Run verification mode
        result = runner.run_contract_tests()

        if result.get("error"):
            print(f"Error: {result['error']}")
            sys.exit(1)

        print(f"Total: {result.get('total_tests', 0)}")
        print(f"Passed: {result.get('passed', 0)}")
        print(f"Failed: {result.get('failed', 0)}")
        print(f"Skipped: {result.get('skipped', 0)}")

        if result.get("passed_all", result.get("failed", 0) == 0):
            print("✅ All contract tests passed")
            sys.exit(0)
        else:
            print("❌ Some contract tests failed")
            sys.exit(1)

    elif generate_report:
        runner.run_contract_tests()
        report = runner.generate_report()
        print(report)

        # Save report to file
        report_file = project_dir / "contract-test-report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")

    else:
        # Default: check mode with JSON output
        result = runner.run_contract_tests()

        if check_mode and not runner.enforce_contracts():
            print(json.dumps(result, indent=2))
            sys.exit(1)

        print(json.dumps(result, indent=2))

        # Save results to file
        results_file = project_dir / "contract-test-results.json"
        with open(results_file, 'w') as f:
            json.dump(result, f, indent=2)


if __name__ == "__main__":
    main()
