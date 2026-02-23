import subprocess
from pathlib import Path

from loguru import logger

from .. import constants as cs
from .. import logs as ls


def discover_repo_files(repo_path: Path) -> list[Path]:
    git_check = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=False,
    )
    if git_check.returncode == 0:
        logger.debug(ls.SCAN_DISCOVERY_GIT)
        result = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        files = [
            repo_path / line for line in result.stdout.splitlines() if line.strip()
        ]
    else:
        logger.debug(ls.SCAN_DISCOVERY_RGLOB)
        files = [p for p in repo_path.rglob("*") if p.is_file()]
    logger.debug(ls.SCAN_DISCOVERED.format(count=len(files)))
    return files


def should_skip_path(
    path: Path,
    repo_path: Path,
    exclude_paths: frozenset[str] | None = None,
    unignore_paths: frozenset[str] | None = None,
) -> bool:
    if path.is_file() and path.suffix in cs.IGNORE_SUFFIXES:
        return True
    rel_path = path.relative_to(repo_path)
    rel_path_str = str(rel_path)
    dir_parts = rel_path.parent.parts if path.is_file() else rel_path.parts
    if exclude_paths and (
        not exclude_paths.isdisjoint(dir_parts)
        or rel_path_str in exclude_paths
        or any(rel_path_str.startswith(f"{p}/") for p in exclude_paths)
    ):
        return True
    if unignore_paths and any(
        rel_path_str == p or rel_path_str.startswith(f"{p}/") for p in unignore_paths
    ):
        return False
    return not cs.IGNORE_PATTERNS.isdisjoint(dir_parts)
