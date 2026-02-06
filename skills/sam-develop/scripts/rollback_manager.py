#!/usr/bin/env python3
"""
rollback_manager.py - Automatic rollback for failed parallel task batches

This script provides rollback capability for the sam-develop workflow when
parallel task execution fails partway through. It tracks git commits before
each parallel batch and can automatically rollback to the batch start point.

Usage:
    python3 skills/sam-develop/scripts/rollback_manager.py .sam/{feature} --create-checkpoint
    python3 skills/sam-develop/scripts/rollback_manager.py .sam/{feature} --rollback
    python3 skills/sam-develop/scripts/rollback_manager.py .sam/{feature} --list-checkpoints

Output:
    Manages rollback checkpoints for parallel task execution
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict


@dataclass
class RollbackCheckpoint:
    """Rollback checkpoint information."""
    checkpoint_id: str
    timestamp: str
    git_commit: str
    git_branch: str
    batch_description: str
    task_ids: List[str] = field(default_factory=list)
    feature_dir: str = ""


class RollbackManager:
    """Manage rollback checkpoints for parallel task execution."""

    def __init__(self, feature_dir: Path):
        self.feature_dir = feature_dir
        self.checkpoints_file = feature_dir / ".rollback" / "checkpoints.json"
        self.checkpoints_file.parent.mkdir(parents=True, exist_ok=True)

    def get_current_git_state(self) -> Dict[str, str]:
        """Get current git state."""
        try:
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            return {"commit": commit, "branch": branch}
        except subprocess.CalledProcessError:
            return {"commit": "unknown", "branch": "unknown"}

    def create_checkpoint(
        self,
        batch_description: str,
        task_ids: List[str]
    ) -> RollbackCheckpoint:
        """
        Create a rollback checkpoint before executing a parallel batch.

        Args:
            batch_description: Description of the batch being executed
            task_ids: List of task IDs in this batch

        Returns:
            RollbackCheckpoint object
        """
        git_state = self.get_current_git_state()

        checkpoint = RollbackCheckpoint(
            checkpoint_id=f"{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            git_commit=git_state["commit"],
            git_branch=git_state["branch"],
            batch_description=batch_description,
            task_ids=task_ids,
            feature_dir=str(self.feature_dir.name)
        )

        # Load existing checkpoints
        checkpoints = self._load_checkpoints()
        checkpoints.append(checkpoint)

        # Keep only last 10 checkpoints
        checkpoints = checkpoints[-10:]

        # Save checkpoints
        self._save_checkpoints(checkpoints)

        # Also update TASKS.json with checkpoint reference
        self._update_tasks_json_checkpoint(checkpoint)

        return checkpoint

    def rollback_to_checkpoint(self, checkpoint_id: Optional[str] = None) -> bool:
        """
        Rollback to a specific checkpoint (or most recent if not specified).

        Args:
            checkpoint_id: Specific checkpoint to rollback to, or None for most recent

        Returns:
            True if rollback successful, False otherwise
        """
        checkpoints = self._load_checkpoints()

        if not checkpoints:
            print("❌ No checkpoints found")
            return False

        # Find the target checkpoint
        target_checkpoint = None
        if checkpoint_id:
            for cp in checkpoints:
                if cp.checkpoint_id == checkpoint_id:
                    target_checkpoint = cp
                    break
        else:
            # Use most recent checkpoint
            target_checkpoint = checkpoints[-1]

        if not target_checkpoint:
            print(f"❌ Checkpoint not found: {checkpoint_id}")
            return False

        # Verify we're on the same branch
        current_branch = self.get_current_git_state()["branch"]
        if target_checkpoint.git_branch != current_branch:
            print(f"⚠️  Warning: Checkpoint was on branch '{target_checkpoint.git_branch}'")
            print(f"   Current branch is '{current_branch}'")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return False

        # Perform git reset
        try:
            print(f"🔄 Rolling back to checkpoint: {target_checkpoint.checkpoint_id}")
            print(f"   Batch: {target_checkpoint.batch_description}")
            print(f"   Git commit: {target_checkpoint.git_commit}")
            print(f"   Timestamp: {target_checkpoint.timestamp}")
            print()

            confirm = input("Confirm rollback? This will discard uncommitted changes. (y/N): ")
            if confirm.lower() != 'y':
                print("❌ Rollback cancelled")
                return False

            # Reset to the commit
            subprocess.run(
                ["git", "reset", "--hard", target_checkpoint.git_commit],
                check=True,
                capture_output=True
            )

            print(f"✅ Rollback complete!")
            print(f"   Reset to commit: {target_checkpoint.git_commit}")
            print(f"   Affected tasks: {', '.join(target_checkpoint.task_ids)}")

            return True

        except subprocess.CalledProcessError as e:
            print(f"❌ Rollback failed: {e}")
            print(f"   Error output: {e.stderr.decode() if e.stderr else 'Unknown'}")
            return False

    def list_checkpoints(self) -> List[RollbackCheckpoint]:
        """
        List all available checkpoints.

        Returns:
            List of RollbackCheckpoint objects
        """
        return self._load_checkpoints()

    def _load_checkpoints(self) -> List[RollbackCheckpoint]:
        """Load checkpoints from file."""
        if not self.checkpoints_file.exists():
            return []

        try:
            with open(self.checkpoints_file, 'r') as f:
                data = json.load(f)
                return [RollbackCheckpoint(**cp) for cp in data]
        except (json.JSONDecodeError, TypeError):
            return []

    def _save_checkpoints(self, checkpoints: List[RollbackCheckpoint]) -> None:
        """Save checkpoints to file."""
        with open(self.checkpoints_file, 'w') as f:
            json.dump([asdict(cp) for cp in checkpoints], f, indent=2)

    def _update_tasks_json_checkpoint(self, checkpoint: RollbackCheckpoint) -> None:
        """Update TASKS.json with checkpoint reference."""
        tasks_file = self.feature_dir / "TASKS.json"

        if not tasks_file.exists():
            return

        try:
            with open(tasks_file, 'r') as f:
                data = json.load(f)

            # Add or update checkpoint info
            if "checkpoint" not in data:
                data["checkpoint"] = {}

            data["checkpoint"]["rollback_checkpoint_id"] = checkpoint.checkpoint_id
            data["checkpoint"]["rollback_git_commit"] = checkpoint.git_commit
            data["checkpoint"]["rollback_timestamp"] = checkpoint.timestamp
            data["checkpoint"]["rollback_batch"] = checkpoint.batch_description

            with open(tasks_file, 'w') as f:
                json.dump(data, f, indent=2)

        except (json.JSONDecodeError, IOError):
            pass  # Don't fail if we can't update TASKS.json

    def cleanup_old_checkpoints(self, keep_count: int = 10) -> None:
        """
        Remove old checkpoints, keeping only the most recent ones.

        Args:
            keep_count: Number of checkpoints to keep
        """
        checkpoints = self._load_checkpoints()

        if len(checkpoints) > keep_count:
            checkpoints = checkpoints[-keep_count:]
            self._save_checkpoints(checkpoints)
            print(f"✓ Cleaned up old checkpoints (kept {keep_count} most recent)")


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python3 rollback_manager.py <feature_dir> <command> [options]")
        print()
        print("Commands:")
        print("  --create-checkpoint  Create a new rollback checkpoint")
        print("  --rollback [id]      Rollback to checkpoint (or most recent)")
        print("  --list-checkpoints   List all available checkpoints")
        print("  --cleanup            Remove old checkpoints")
        print()
        print("Examples:")
        print("  python3 rollback_manager.py .sam/001_user_auth --create-checkpoint")
        print("  python3 rollback_manager.py .sam/001_user_auth --rollback")
        print("  python3 rollback_manager.py .sam/001_user_auth --rollback 20250206_143000")
        print("  python3 rollback_manager.py .sam/001_user_auth --list-checkpoints")
        sys.exit(1)

    feature_dir = Path(sys.argv[1])

    if not feature_dir.exists():
        print(f"Error: Feature directory not found: {feature_dir}")
        sys.exit(1)

    manager = RollbackManager(feature_dir)

    command = sys.argv[2] if len(sys.argv) > 2 else None

    if command == "--create-checkpoint":
        # Parse additional options
        batch_desc = "Manual checkpoint"
        task_ids = []

        i = 3
        while i < len(sys.argv):
            if sys.argv[i] == "--description" and i + 1 < len(sys.argv):
                batch_desc = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == "--tasks" and i + 1 < len(sys.argv):
                task_ids = sys.argv[i + 1].split(',')
                i += 2
            else:
                i += 1

        checkpoint = manager.create_checkpoint(batch_desc, task_ids)
        print(f"✓ Created checkpoint: {checkpoint.checkpoint_id}")
        print(f"  Git commit: {checkpoint.git_commit}")
        print(f"  Branch: {checkpoint.git_branch}")
        print(f"  Description: {batch_desc}")
        if task_ids:
            print(f"  Tasks: {', '.join(task_ids)}")

    elif command == "--rollback":
        checkpoint_id = sys.argv[3] if len(sys.argv) > 3 else None
        success = manager.rollback_to_checkpoint(checkpoint_id)
        sys.exit(0 if success else 1)

    elif command == "--list-checkpoints":
        checkpoints = manager.list_checkpoints()

        if not checkpoints:
            print("No checkpoints found")
        else:
            print(f"Found {len(checkpoints)} checkpoint(s):\n")
            for idx, cp in enumerate(checkpoints, 1):
                print(f"{idx}. {cp.checkpoint_id}")
                print(f"   Batch: {cp.batch_description}")
                print(f"   Commit: {cp.git_commit}")
                print(f"   Timestamp: {cp.timestamp}")
                if cp.task_ids:
                    print(f"   Tasks: {', '.join(cp.task_ids)}")
                print()

    elif command == "--cleanup":
        keep_count = 10
        if len(sys.argv) > 3 and sys.argv[3].isdigit():
            keep_count = int(sys.argv[3])
        manager.cleanup_old_checkpoints(keep_count)

    else:
        print(f"Error: Unknown command: {command}")
        print("Use --create-checkpoint, --rollback, --list-checkpoints, or --cleanup")
        sys.exit(1)


if __name__ == "__main__":
    main()
