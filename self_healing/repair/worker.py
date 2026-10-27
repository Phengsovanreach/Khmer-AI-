"""
Khmer Translator AI — Controlled Repair Worker.
Creates isolated repair branches, applies minimal code fixes, enforces security boundaries,
runs test validation, and rejects unsafe repairs.
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

from ..config import Config, redact_secrets
from ..models import DiagnosticReport, Incident, IncidentStatus, RepairProposal

logger = logging.getLogger(__name__)


class RepairWorker:
    def __init__(self, repo_dir: Optional[Path] = None):
        self.repo_dir = repo_dir or Config.BASE_DIR
        self.lock_file = self.repo_dir / ".self_healing_repair.lock"

    def acquire_lock(self) -> bool:
        """Acquires a concurrency lock to prevent overlapping repair jobs."""
        if self.lock_file.exists():
            # Check if stale lock (older than 10 minutes)
            try:
                mtime = self.lock_file.stat().st_mtime
                import time
                if time.time() - mtime > 600:
                    self.lock_file.unlink(missing_ok=True)
                else:
                    return False
            except Exception:
                return False
        try:
            self.lock_file.write_text(f"pid={os.getpid()}", encoding="utf-8")
            return True
        except Exception:
            return False

    def release_lock(self) -> None:
        """Releases the repair concurrency lock."""
        self.lock_file.unlink(missing_ok=True)

    def execute_repair_proposal(
        self,
        incident: Incident,
        diagnosis: DiagnosticReport,
        target_file_rel: str,
        proposed_code: str,
        validation_command: str = "pytest -q self_healing/tests",
    ) -> tuple[bool, Optional[RepairProposal], str]:
        """
        Executes a targeted, isolated repair cycle:
        1. Checks concurrency lock and retry limits.
        2. Validates security policies (rejects protected files and excessive diffs).
        3. Spawns an isolated branch: ai-repair/{incident_id}-{short_desc}.
        4. Applies code modification.
        5. Runs regression tests.
        6. Returns (success, proposal, message).
        """
        if not self.acquire_lock():
            return False, None, "Repair aborted: Another repair job holds the lock."

        try:
            # Check retry limit
            if incident.repair_attempts >= Config.MAX_REPAIR_ATTEMPTS:
                return False, None, f"Max repair attempts ({Config.MAX_REPAIR_ATTEMPTS}) reached for incident {incident.incident_id}."

            # Security boundary check: Forbidden paths
            for forbidden in Config.FORBIDDEN_REPAIR_PATHS:
                if target_file_rel.startswith(forbidden) or forbidden in target_file_rel:
                    return False, None, f"Security violation: Modification of '{target_file_rel}' is strictly forbidden."

            # Validate target file exists
            target_path = (self.repo_dir / target_file_rel).resolve()
            if not target_path.exists():
                return False, None, f"Target file '{target_file_rel}' does not exist."

            incident.repair_attempts += 1
            branch_name = f"{Config.REPAIR_BRANCH_PREFIX}{incident.incident_id.lower()}-fix"

            # Create and switch to isolated branch from current HEAD
            self._run_git(["checkout", "-b", branch_name])

            # Backup original file content
            original_content = target_path.read_text(encoding="utf-8")

            # Apply modification
            target_path.write_text(proposed_code, encoding="utf-8")

            # Validate diff size
            diff_output = self._run_git(["diff", target_file_rel])
            diff_lines = len(diff_output.splitlines())
            if diff_lines > Config.MAX_DIFF_LINES:
                # Revert change
                target_path.write_text(original_content, encoding="utf-8")
                self._run_git(["checkout", "-f", Config.PRODUCTION_BRANCH])
                self._run_git(["branch", "-D", branch_name])
                return False, None, f"Diff exceeded safe threshold ({diff_lines} > {Config.MAX_DIFF_LINES} lines). Fix rejected."

            # Run test validation
            test_success, test_log = self._run_test_suite(validation_command)
            if not test_success:
                # Revert change and discard branch
                target_path.write_text(original_content, encoding="utf-8")
                self._run_git(["checkout", "-f", Config.PRODUCTION_BRANCH])
                self._run_git(["branch", "-D", branch_name])
                return False, None, f"Validation test failed:\n{redact_secrets(test_log[:400])}"

            # Tests passed! Commit changes to the repair branch
            self._run_git(["add", target_file_rel])
            commit_msg = f"fix(self-healing): targeted fix for incident {incident.incident_id}"
            self._run_git(["commit", "-m", commit_msg])

            proposal = RepairProposal(
                incident_id=incident.incident_id,
                branch_name=branch_name,
                target_files=[target_file_rel],
                diff_content=diff_output,
                validation_commands=[validation_command],
                pr_title=f"🤖 [Self-Healing] Automated Repair for {incident.incident_id}",
                pr_body=self._build_pr_body(incident, diagnosis, diff_output, test_log),
                tests_passed=True,
            )

            # Switch back safely to original branch
            self._run_git(["checkout", Config.PRODUCTION_BRANCH])
            return True, proposal, "Repair validated successfully on isolated branch."

        finally:
            self.release_lock()

    def _run_git(self, args: list[str]) -> str:
        """Executes a git command in the repository."""
        res = subprocess.run(
            ["git"] + args,
            cwd=str(self.repo_dir),
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            logger.warning("Git command '%s' returned %d: %s", " ".join(args), res.returncode, res.stderr)
        return res.stdout

    def _run_test_suite(self, command: str) -> tuple[bool, str]:
        """Runs the validation command and captures results."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                cwd=str(self.repo_dir),
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = res.stdout + "\n" + res.stderr
            return res.returncode == 0, output
        except Exception as exc:
            return False, str(exc)

    @staticmethod
    def _build_pr_body(
        incident: Incident,
        diagnosis: DiagnosticReport,
        diff: str,
        test_log: str,
    ) -> str:
        return f"""## 🚨 Autonomous Self-Healing Incident Report

**Incident ID:** `{incident.incident_id}`  
**Affected Component:** `{incident.service.value}`  
**Detected At:** `{incident.last_detected_cambodia}`  
**Severity:** `CRITICAL`  
**Root Cause:** {diagnosis.probable_root_cause}  
**Confidence:** {diagnosis.confidence * 100:.0f}%  

---

### 🔍 Diagnostic Evidence
```
{diagnosis.evidence[:400]}
```

---

### 🛠️ Proposed Solution
{diagnosis.proposed_fix}

### 🧪 Automated Validation Results
- **Status:** ✅ All validation tests PASSED
- **Test Output Summary:**
```
{test_log[-500:]}
```

---

### ⚠️ Reviewer Checklist (Human Approval Required)
- [ ] Review diff to ensure no unintended side effects.
- [ ] Confirm the production issue is addressed.
- [ ] Merge to production branch when ready.
- **Rollback Procedure:** If needed, run `git revert <commit-sha>` or close this PR.

*Generated autonomously by Khmer Translator AI Self-Healing System.*
"""
