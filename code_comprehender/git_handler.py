"""Git handler for accessing and cloning GitHub repositories."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from code_comprehender.logger import (
    get_logger,
    log_error,
    log_progress,
    log_success,
    log_warning,
)


class GitHandler:
    """Handles GitHub repository operations."""

    def __init__(self, github_token: Optional[str] = None):
        self.logger = get_logger(self.__class__.__name__)
        self.github_token = github_token
        self.temp_dir = None
        self.repo_dir = None

    def clone_repository(
        self, github_url: str, target_dir: Optional[str] = None
    ) -> str:
        """Clone a GitHub repository.

        Args:
            github_url: GitHub repository URL (https://github.com/user/repo format)
            target_dir: Directory to clone into (uses temp dir if None)

        Returns:
            Path to the cloned repository
        """
        # Validate and normalize URL
        repo_url = self._normalize_github_url(github_url)

        # Determine target directory
        if target_dir:
            self.repo_dir = os.path.abspath(target_dir)
            os.makedirs(self.repo_dir, exist_ok=True)
        else:
            self.temp_dir = tempfile.mkdtemp(prefix="codecomprehender_repo_")
            self.repo_dir = self.temp_dir

        self.logger.info(f"Cloning repository: {github_url}")
        self.logger.info(f"Target directory: {self.repo_dir}")

        # Prepare git command
        cmd = ["git", "clone"]

        # Add authentication if token is provided
        if self.github_token:
            # Insert token into URL for authentication
            parsed = urlparse(repo_url)
            auth_url = f"https://{self.github_token}@{parsed.netloc}{parsed.path}"
            cmd.append(auth_url)
        else:
            cmd.append(repo_url)

        cmd.append(self.repo_dir)

        try:
            # Execute git clone
            log_progress("Cloning repository", 1, 1)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip()
                raise RuntimeError(f"Git clone failed: {error_msg}")

            log_success(f"Repository cloned successfully to: {self.repo_dir}")
            return self.repo_dir

        except subprocess.TimeoutExpired:
            raise RuntimeError("Git clone timed out after 5 minutes")
        except Exception as e:
            raise RuntimeError(f"Failed to clone repository: {e}")

    def find_java_files(self, repo_path: str) -> List[str]:
        """Find all Java files in the repository.

        Args:
            repo_path: Path to the repository

        Returns:
            List of paths to Java files
        """
        java_files = []
        repo_path = Path(repo_path)

        if not repo_path.exists():
            log_error(f"Repository path does not exist: {repo_path}")
            return java_files

        self.logger.info(f"Searching for Java files in: {repo_path}")

        # Recursively find all .java files
        for java_file in repo_path.rglob("*.java"):
            # Skip files in common directories that shouldn't be processed
            relative_path = java_file.relative_to(repo_path)
            path_parts = relative_path.parts

            # Skip test directories, build directories, etc.
            skip_dirs = {
                ".git",
                "target",
                "build",
                "bin",
                "out",
                "node_modules",
                ".gradle",
                ".mvn",
                ".github",
            }

            should_skip = any(part in skip_dirs for part in path_parts)

            if not should_skip:
                java_files.append(str(java_file))

        self.logger.info(f"Found {len(java_files)} Java files")

        return java_files

    def get_repository_info(
        self, repo_path: str, original_url: str = None
    ) -> Dict[str, Any]:
        """Get information about the cloned repository.

        Args:
            repo_path: Path to the repository
            original_url: Original GitHub URL used for cloning

        Returns:
            Dictionary containing repository information
        """
        info = {
            "path": repo_path,
            "name": self._extract_repo_name_from_url(original_url)
            if original_url
            else Path(repo_path).name,
            "java_files": [],
            "java_file_count": 0,
        }

        try:
            # Get Java files
            info["java_files"] = self.find_java_files(repo_path)
            info["java_file_count"] = len(info["java_files"])

        except Exception as e:
            log_warning(f"Error getting repository info: {e}")

        return info

    def _extract_repo_name_from_url(self, url: str) -> str:
        """Extract repository name from GitHub URL.

        Args:
            url: GitHub URL

        Returns:
            Repository name (e.g., 'kitchensink' from 'https://github.com/user/kitchensink')
        """
        if not url:
            return "unknown"

        # Remove tree/branch part if present
        if "/tree/" in url:
            url = url.split("/tree/")[0]

        # Extract repo name from URL
        # https://github.com/user/repo or https://github.com/user/repo.git
        parts = url.rstrip("/").split("/")
        if len(parts) >= 2:
            repo_name = parts[-1]
            # Remove .git extension if present
            if repo_name.endswith(".git"):
                repo_name = repo_name[:-4]
            return repo_name

        return "unknown"

    def cleanup(self):
        """Clean up temporary files and directories."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                self.logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                log_warning(f"Failed to cleanup temporary directory: {e}")
            finally:
                self.temp_dir = None
                self.repo_dir = None

    def _normalize_github_url(self, url: str) -> str:
        """Normalize GitHub URL to HTTPS format.

        Args:
            url: GitHub URL (https://github.com/user/repo format)

        Returns:
            Normalized HTTPS URL

        Raises:
            ValueError: If URL is not a valid GitHub URL
        """
        url = url.strip()

        # Only handle HTTPS GitHub URLs
        if not url.startswith("https://github.com/"):
            raise ValueError(f"Only HTTPS GitHub URLs are supported: {url}")

        # Handle tree/branch URLs like: https://github.com/user/repo/tree/main
        if "/tree/" in url:
            url = url.split("/tree/")[0]

        # Add .git extension if not present
        if not url.endswith(".git"):
            url += ".git"

        return url

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.cleanup()
