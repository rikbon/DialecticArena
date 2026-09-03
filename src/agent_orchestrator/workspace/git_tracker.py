"""
Git versioning tracker for the dialectic arena workspace.
Allows automatic commits per round or turn to track conceptual diffs.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Optional


class GitTracker:
    """Tracks workspace changes in Git with semantic commit messages."""

    def __init__(self, workspace_dir: Path, enabled: bool = True):
        self.workspace_dir = workspace_dir.resolve()
        self.enabled = enabled
        self._git_bin = shutil.which("git")

    def is_available(self) -> bool:
        """Check if git is installed and workspace is inside a git repo."""
        if not self.enabled or not self._git_bin:
            return False
        try:
            res = subprocess.run(
                [self._git_bin, "rev-parse", "--is-inside-work-tree"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    def init_repo_if_needed(self) -> bool:
        """Initialize a git repo inside workspace if not already tracked."""
        if not self._git_bin or not self.enabled:
            return False
        if self.is_available():
            return True
        try:
            res = subprocess.run(
                [self._git_bin, "init"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            return False

    def commit_turn(
        self,
        agent_name: str,
        turn_num: int,
        step_label: str = "Thesis",
        summary: str = "",
        files: Optional[list[Path]] = None,
        round_num: Optional[int] = None,
    ) -> Optional[str]:
        """Stage files and commit with a descriptive turn message."""
        if not self.is_available():
            return None

        # Resolve interaction turn number
        t_num = turn_num or round_num or 1

        try:
            # Stage files
            if files:
                rel_paths = [str(f.resolve().relative_to(self.workspace_dir)) for f in files if f.exists()]
                if not rel_paths:
                    return None
                cmd_add = [self._git_bin, "add"] + rel_paths
            else:
                cmd_add = [self._git_bin, "add", "."]

            subprocess.run(cmd_add, cwd=self.workspace_dir, capture_output=True, check=True)

            # Check if there are staged changes
            diff_res = subprocess.run(
                [self._git_bin, "diff", "--cached", "--quiet"],
                cwd=self.workspace_dir,
                capture_output=True,
                check=False,
            )
            if diff_res.returncode == 0:
                # Nothing changed
                return None

            # Commit
            label = f" | {step_label}" if step_label else ""
            commit_msg = f"[Turn {t_num}{label}] {agent_name}: {summary[:80]}"
            res = subprocess.run(
                [self._git_bin, "commit", "-m", commit_msg],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=True,
            )

            # Extract short commit hash
            rev_res = subprocess.run(
                [self._git_bin, "rev-parse", "--short", "HEAD"],
                cwd=self.workspace_dir,
                capture_output=True,
                text=True,
                check=False,
            )
            return rev_res.stdout.strip() if rev_res.returncode == 0 else "committed"

        except Exception:
            return None

    def get_last_diff(self, file_path: Optional[Path] = None) -> str:
        """Get the diff of the last commit."""
        if not self.is_available():
            return ""
        try:
            cmd = [self._git_bin, "diff", "HEAD~1", "HEAD"]
            if file_path and file_path.exists():
                rel_path = str(file_path.resolve().relative_to(self.workspace_dir))
                cmd.extend(["--", rel_path])
            res = subprocess.run(cmd, cwd=self.workspace_dir, capture_output=True, text=True, check=False)
            return res.stdout.strip() if res.returncode == 0 else ""
        except Exception:
            return ""
