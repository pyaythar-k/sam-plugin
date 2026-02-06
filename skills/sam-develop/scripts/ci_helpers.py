#!/usr/bin/env python3
"""
ci_helpers.py - Utilities for CI environment detection, artifact upload, and status reporting

This script provides utilities for CI/CD integration including environment detection,
artifact management, coverage badge generation, and TASKS.json checkpoint updates.

Usage:
    python3 ci_helpers.py --detect-env
    python3 ci_helpers.py --generate-report --input-dir results/ --output report.md
    python3 ci_helpers.py --update-checkpoint --feature-dir .sam/001_feature --ci github
    python3 ci_helpers.py --upload-artifact --file coverage.json --name coverage-report
    python3 ci_helpers.py --generate-badge --metrics coverage.json --output badge.svg

Output:
    Environment information, CI status reports, and checkpoint updates
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field, asdict


@dataclass
class CIEnvironment:
    """CI environment detection and configuration."""
    environment: str = "local"  # github, gitlab, local
    is_ci: bool = False
    job_id: Optional[str] = None
    workflow_id: Optional[str] = None
    run_id: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None
    actor: Optional[str] = None

    @classmethod
    def detect(cls) -> 'CIEnvironment':
        """Detect the current CI environment."""
        env = cls()

        # Check GitHub Actions
        if os.environ.get('GITHUB_ACTIONS') == 'true':
            env.environment = "github"
            env.is_ci = True
            env.job_id = os.environ.get('GITHUB_JOB')
            env.workflow_id = os.environ.get('GITHUB_WORKFLOW')
            env.run_id = os.environ.get('GITHUB_RUN_ID')
            env.branch = os.environ.get('GITHUB_REF_NAME')
            env.commit_sha = os.environ.get('GITHUB_SHA')
            env.actor = os.environ.get('GITHUB_ACTOR')

        # Check GitLab CI
        elif os.environ.get('GITLAB_CI') == 'true':
            env.environment = "gitlab"
            env.is_ci = True
            env.job_id = os.environ.get('CI_JOB_ID')
            env.workflow_id = os.environ.get('CI_PIPELINE_ID')
            env.run_id = os.environ.get('CI_PIPELINE_ID')
            env.branch = os.environ.get('CI_COMMIT_REF_NAME')
            env.commit_sha = os.environ.get('CI_COMMIT_SHA')
            env.actor = os.environ.get('GITLAB_USER_NAME')

        # Check Jenkins
        elif os.environ.get('JENKINS_HOME'):
            env.environment = "jenkins"
            env.is_ci = True
            env.job_id = os.environ.get('JOB_NAME')
            env.workflow_id = os.environ.get('BUILD_ID')
            env.run_id = os.environ.get('BUILD_NUMBER')
            env.branch = os.environ.get('GIT_BRANCH')
            env.commit_sha = os.environ.get('GIT_COMMIT')

        # Check Azure Pipelines
        elif os.environ.get('TF_BUILD'):
            env.environment = "azure"
            env.is_ci = True
            env.job_id = os.environ.get('AGENT_JOBNAME')
            env.workflow_id = os.environ.get('BUILD_BUILDNUMBER')

        # Local development
        else:
            env.environment = "local"
            env.is_ci = False

        return env

    def get_var(self, name: str, default: Any = None) -> Any:
        """Get environment variable with fallback."""
        # Try CI-specific prefixes first
        if self.environment == "github":
            prefix = "GITHUB_"
        elif self.environment == "gitlab":
            prefix = "CI_"
        elif self.environment == "jenkins":
            prefix = ""  # Jenkins doesn't use a prefix
        else:
            prefix = ""

        # Try with prefix
        value = os.environ.get(f"{prefix}{name}")
        if value is not None:
            return value

        # Try without prefix
        return os.environ.get(name, default)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class ArtifactUploader:
    """Handle artifact upload to CI services."""
    project_dir: Path
    ci_env: CIEnvironment

    def upload_coverage_report(self, report_path: Path) -> bool:
        """Upload coverage report to appropriate service."""
        if not report_path.exists():
            print(f"⚠ Coverage report not found: {report_path}")
            return False

        if self.ci_env.environment == "github":
            return self._upload_to_github_artifacts(report_path)
        elif self.ci_env.environment == "gitlab":
            return self._upload_to_gitlab_artifacts(report_path)
        else:
            print("⚠ Artifact upload only supported in CI environments")
            return False

    def upload_test_results(self, results_path: Path) -> bool:
        """Upload test results to appropriate service."""
        if not results_path.exists():
            print(f"⚠ Test results not found: {results_path}")
            return False

        if self.ci_env.environment == "github":
            return self._upload_to_github_artifacts(results_path)
        elif self.ci_env.environment == "gitlab":
            return self._upload_to_gitlab_artifacts(results_path)
        else:
            print("⚠ Artifact upload only supported in CI environments")
            return False

    def _upload_to_github_artifacts(self, file_path: Path) -> bool:
        """Upload to GitHub Actions artifacts (via GitHub Actions step)."""
        # In GitHub Actions, artifacts are uploaded via the action itself
        # This method prepares the file for upload
        print(f"✓ Artifact ready for GitHub upload: {file_path}")
        return True

    def _upload_to_gitlab_artifacts(self, file_path: Path) -> bool:
        """Upload to GitLab CI artifacts."""
        # In GitLab CI, artifacts are defined in .gitlab-ci.yml
        # This method prepares the file for upload
        print(f"✓ Artifact ready for GitLab upload: {file_path}")
        return True


@dataclass
class BadgeGenerator:
    """Generate coverage and quality badges for CI/CD."""
    coverage: float
    threshold: float
    label: str = "coverage"

    def generate_svg(self) -> str:
        """Generate SVG badge."""
        # Determine color based on coverage
        if self.coverage >= self.threshold:
            color = "#4c1"  # Bright green
        elif self.coverage >= self.threshold * 0.8:
            color = "#dfb317"  # Yellow
        elif self.coverage >= self.threshold * 0.6:
            color = "#fe7d37"  # Orange
        else:
            color = "#e05d44"  # Red

        width = 100 + len(f"{self.coverage:.0f}%") * 8
        label_width = len(self.label) * 8 + 20

        badge = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <mask id="a">
    <rect width="{width}" height="20" rx="3" fill="#fff"/>
  </mask>
  <g mask="url(#a)">
    <path fill="#555" d="M0 0h{label_width}v20H0z"/>
    <path fill="{color}" d="M{label_width} 0h{width - label_width}v20H{label_width}z"/>
    <path fill="url(#b)" d="M0 0h{width}v20H0z"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="DejaVu Sans,Verdana,Geneva,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{self.label}</text>
    <text x="{label_width / 2}" y="14">{self.label}</text>
    <text x="{label_width + (width - label_width) / 2}" y="15" fill="#010101" fill-opacity=".3">{self.coverage:.0f}%</text>
    <text x="{label_width + (width - label_width) / 2}" y="14">{self.coverage:.0f}%</text>
  </g>
</svg>'''

        return badge

    def generate_shields_io_url(self) -> str:
        """Generate shields.io badge URL."""
        color = "brightgreen" if self.coverage >= self.threshold else "red"
        return f"https://img.shields.io/badge/{self.label}-{self.coverage:.0f}%25-{color}"


@dataclass
class StatusReporter:
    """Report CI status to various outputs."""
    ci_env: CIEnvironment

    def report_success(self, message: str) -> None:
        """Report success status."""
        if self.ci_env.environment == "github":
            self._set_github_output("status", "success")
            self._set_github_output("message", message)
            print(f"✅ {message}")
        elif self.ci_env.environment == "gitlab":
            print(f"✅ {message}")
        else:
            print(f"✅ {message}")

    def report_failure(self, message: str, details: Optional[Dict] = None) -> None:
        """Report failure status."""
        if self.ci_env.environment == "github":
            self._set_github_output("status", "failure")
            self._set_github_output("message", message)
            if details:
                self._set_github_output("details", json.dumps(details))
            print(f"❌ {message}")
        elif self.ci_env.environment == "gitlab":
            print(f"❌ {message}")
        else:
            print(f"❌ {message}")

    def set_output(self, name: str, value: str) -> None:
        """Set CI output variable."""
        if self.ci_env.environment == "github":
            self._set_github_output(name, value)
        elif self.ci_env.environment == "gitlab":
            # GitLab uses env files for outputs
            self._set_gitlab_output(name, value)

    def _set_github_output(self, name: str, value: str) -> None:
        """Set GitHub Actions output."""
        # GitHub Actions output file
        output_file = os.environ.get('GITHUB_OUTPUT')
        if output_file:
            with open(output_file, 'a') as f:
                f.write(f"{name}={value}\n")

    def _set_gitlab_output(self, name: str, value: str) -> None:
        """Set GitLab CI output."""
        # GitLab CI uses env files
        output_file = os.environ.get('CI_OUTPUT_FILE')
        if output_file:
            with open(output_file, 'a') as f:
                f.write(f"{name}={value}\n")


@dataclass
class CheckpointUpdater:
    """Update TASKS.json with CI metadata."""
    feature_dir: Path
    ci_env: CIEnvironment

    def update_checkpoint(
        self,
        job_id: str,
        workflow: str,
        status: str
    ) -> bool:
        """Update TASKS.json checkpoint with CI metadata."""
        tasks_file = self.feature_dir / "TASKS.json"

        if not tasks_file.exists():
            print(f"⚠ TASKS.json not found: {tasks_file}")
            return False

        try:
            # Read existing TASKS.json
            with open(tasks_file, 'r') as f:
                tasks_data = json.load(f)

            # Get or create checkpoint
            checkpoint = tasks_data.setdefault("checkpoint", {})

            # Add CI metadata
            checkpoint["last_ci_run"] = datetime.now().isoformat()
            checkpoint["ci_environment"] = self.ci_env.environment
            checkpoint["ci_job_id"] = job_id
            checkpoint["ci_workflow"] = workflow
            checkpoint["ci_status"] = status

            # Add detailed CI info
            checkpoint["ci_metadata"] = {
                "branch": self.ci_env.branch,
                "commit_sha": self.ci_env.commit_sha,
                "actor": self.ci_env.actor,
                "timestamp": datetime.now().isoformat()
            }

            # Write back
            with open(tasks_file, 'w') as f:
                json.dump(tasks_data, f, indent=2)

            print(f"✓ Updated TASKS.json checkpoint with CI metadata")
            return True

        except (json.JSONDecodeError, IOError) as e:
            print(f"✗ Failed to update TASKS.json: {e}")
            return False


def generate_ci_report(input_dir: Path, output_file: Path) -> bool:
    """Generate comprehensive CI status report from artifacts."""
    if not input_dir.exists():
        print(f"⚠ Input directory not found: {input_dir}")
        return False

    report = []
    report.append("# CI Status Report")
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")

    # Detect environment
    ci_env = CIEnvironment.detect()
    report.append(f"## Environment")
    report.append(f"- Platform: {ci_env.environment}")
    report.append(f"- Job ID: {ci_env.job_id or 'N/A'}")
    report.append(f"- Workflow: {ci_env.workflow_id or 'N/A'}")
    report.append(f"- Branch: {ci_env.branch or 'N/A'}")
    report.append("")

    # Collect all results
    results = {}

    for artifact_file in input_dir.rglob("*.json"):
        try:
            with open(artifact_file, 'r') as f:
                data = json.load(f)
                results[artifact_file.stem] = data
        except (json.JSONDecodeError, IOError):
            continue

    # Quality gate results
    if "quality-gate-final" in results:
        report.append("## Quality Gate")
        qg = results["quality-gate-final"]
        report.append(f"- Overall: {qg.get('overall', 'unknown').upper()}")
        if "quality_gate" in qg:
            for check, status in qg["quality_gate"].items():
                if check not in ["timestamp", "overall"]:
                    icon = "✅" if status == "passed" else "❌"
                    report.append(f"- {icon} {check}: {status}")
        report.append("")

    # Coverage results
    if "coverage-result" in results:
        report.append("## Coverage")
        cov = results["coverage-result"]
        if "coverage" in cov:
            coverage = cov["coverage"]
            report.append(f"- Overall: {coverage.get('overall', 0):.1f}%")
            report.append(f"- Threshold: {cov.get('threshold', 80)}%")
            report.append(f"- Status: {'✅ PASSED' if cov.get('passed', False) else '❌ FAILED'}")
        report.append("")

    # Test results
    if "test-results" in results:
        report.append("## Tests")
        test = results["test-results"]
        report.append(f"- Total: {test.get('total', 0)}")
        report.append(f"- Passed: {test.get('passed', 0)}")
        report.append(f"- Failed: {test.get('failed', 0)}")
        report.append("")

    # Security results
    if "security-results" in results:
        report.append("## Security")
        report.append("Security scan completed")
        report.append("")

    # Write report
    report_content = "\n".join(report)
    with open(output_file, 'w') as f:
        f.write(report_content)

    print(f"✓ CI report generated: {output_file}")
    return True


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ci_helpers.py --detect-env")
        print("  python3 ci_helpers.py --generate-report --input-dir <dir> --output <file>")
        print("  python3 ci_helpers.py --update-checkpoint --feature-dir <dir> --ci-env <github|gitlab> --job-id <id> --workflow <name> --status <status>")
        print("  python3 ci_helpers.py --generate-badge --coverage <pct> --threshold <pct> --output <file>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "--detect-env":
        ci_env = CIEnvironment.detect()
        print(json.dumps(ci_env.to_dict(), indent=2))

    elif command == "--generate-report":
        input_dir = None
        output_file = None

        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--input-dir" and i + 1 < len(sys.argv):
                input_dir = Path(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
                output_file = Path(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        if not input_dir or not output_file:
            print("Error: --input-dir and --output are required")
            sys.exit(1)

        success = generate_ci_report(input_dir, output_file)
        sys.exit(0 if success else 1)

    elif command == "--update-checkpoint":
        feature_dir = None
        ci_env_name = None
        job_id = None
        workflow = None
        status = None

        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--feature-dir" and i + 1 < len(sys.argv):
                feature_dir = Path(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--ci-environment" and i + 1 < len(sys.argv):
                ci_env_name = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--ci-env" and i + 1 < len(sys.argv):
                ci_env_name = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--job-id" and i + 1 < len(sys.argv):
                job_id = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--workflow" and i + 1 < len(sys.argv):
                workflow = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--status" and i + 1 < len(sys.argv):
                status = sys.argv[i + 1]
                i += 2
            else:
                i += 1

        if not feature_dir or not ci_env_name or not job_id or not workflow or not status:
            print("Error: --feature-dir, --ci-environment, --job-id, --workflow, and --status are required")
            sys.exit(1)

        # Create CI environment
        ci_env = CIEnvironment()
        ci_env.environment = ci_env_name

        updater = CheckpointUpdater(feature_dir, ci_env)
        success = updater.update_checkpoint(job_id, workflow, status)
        sys.exit(0 if success else 1)

    elif command == "--generate-badge":
        coverage = 80
        threshold = 80
        output_file = None

        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == "--coverage" and i + 1 < len(sys.argv):
                coverage = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--threshold" and i + 1 < len(sys.argv):
                threshold = float(sys.argv[i + 1])
                i += 2
            elif sys.argv[i] == "--output" and i + 1 < len(sys.argv):
                output_file = Path(sys.argv[i + 1])
                i += 2
            else:
                i += 1

        generator = BadgeGenerator(coverage=coverage, threshold=threshold)
        badge = generator.generate_svg()

        if output_file:
            with open(output_file, 'w') as f:
                f.write(badge)
            print(f"✓ Badge generated: {output_file}")
        else:
            print(badge)

    else:
        print(f"Error: Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
