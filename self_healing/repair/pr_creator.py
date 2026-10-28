"""
Khmer Translator AI — GitHub Pull Request Creator.
Submits validated repair branches as Pull Requests requiring human review.
"""
from __future__ import annotations

import json
import logging
import subprocess
import urllib.error
import urllib.request
from typing import Optional

from ..config import Config, redact_secrets
from ..models import RepairProposal

logger = logging.getLogger(__name__)


class PullRequestCreator:
    def __init__(self, token: Optional[str] = None, repository: Optional[str] = None):
        self.token = token or Config.GITHUB_TOKEN
        self.repository = repository or Config.GITHUB_REPOSITORY

    @property
    def is_configured(self) -> bool:
        return bool(self.token and self.token.strip())

    def create_pull_request(
        self,
        proposal: RepairProposal,
        base_branch: Optional[str] = None,
    ) -> Optional[str]:
        """
        Pushes repair branch and creates a GitHub Pull Request:
        1. Pushes `proposal.branch_name` to origin.
        2. Calls GitHub REST API /repos/{repo}/pulls.
        3. Returns the resulting PR html_url.
        """
        target_base = base_branch or Config.PRODUCTION_BRANCH

        # 1. Push branch to GitHub
        try:
            push_res = subprocess.run(
                ["git", "push", "-u", "origin", proposal.branch_name],
                cwd=str(Config.BASE_DIR),
                capture_output=True,
                text=True,
                timeout=30,
            )
            if push_res.returncode != 0:
                logger.error("Failed to push repair branch %s: %s", proposal.branch_name, push_res.stderr)
                return None
        except Exception as exc:
            logger.error("Error executing git push for repair branch: %s", redact_secrets(str(exc)))
            return None

        # 2. Check if GitHub token is present for API call
        if not self.is_configured:
            logger.info("GitHub PR creation skipped: GITHUB_TOKEN not configured. Pushed branch: %s", proposal.branch_name)
            mock_url = f"https://github.com/{self.repository}/pull/new/{proposal.branch_name}"
            proposal.pull_request_url = mock_url
            return mock_url

        # 3. Call GitHub API to open Pull Request
        api_url = f"https://api.github.com/repos/{self.repository}/pulls"
        payload = {
            "title": proposal.pr_title,
            "body": proposal.pr_body,
            "head": proposal.branch_name,
            "base": target_base,
            "draft": False,
        }

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "KhmerTranslatorSelfHealing/2.0",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                pr_url = data.get("html_url")
                proposal.pull_request_url = pr_url
                logger.info("Created GitHub Pull Request: %s", pr_url)
                return pr_url
        except urllib.error.HTTPError as exc:
            raw_err = exc.read().decode("utf-8", errors="ignore")
            logger.error("GitHub API PR creation failed (HTTP %s): %s", exc.code, redact_secrets(raw_err))
        except Exception as exc:
            logger.error("Unexpected error creating PR: %s", redact_secrets(str(exc)))

        return None
