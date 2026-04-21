import subprocess
from functools import lru_cache
from pathlib import Path

from loguru import logger
from pathspec import PathSpec

from .. import constants as cs
from .. import logs as ls

_GLOB_META = frozenset("*?[")


def _is_glob_pattern(pattern: str) -> bool:
    """True if *pattern* contains glob metacharacters."""
    return any(c in _GLOB_META for c in pattern)


@lru_cache(maxsize=64)
def _compile_pathspec(patterns: tuple[str, ...]) -> PathSpec:
    """Compile a tuple of gitignore-style patterns into a PathSpec.

    The call-site passes a sorted tuple so the cache is stable across
    identical pattern sets (a full index may call ``should_skip_path``
    many thousands of times).
    """
    return PathSpec.from_lines("gitignore", patterns)


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
    rel_path_str = rel_path.as_posix()
    dir_parts = rel_path.parent.parts if path.is_file() else rel_path.parts

    if exclude_paths:
        literal_excludes = frozenset(
            p for p in exclude_paths if not _is_glob_pattern(p)
        )
        glob_excludes = tuple(
            sorted(p for p in exclude_paths if _is_glob_pattern(p))
        )
        if (
            not literal_excludes.isdisjoint(dir_parts)
            or rel_path_str in literal_excludes
            or any(rel_path_str.startswith(f"{p}/") for p in literal_excludes)
            or (
                glob_excludes
                and _compile_pathspec(glob_excludes).match_file(rel_path_str)
            )
        ):
            return True

    if unignore_paths:
        literal_unignores = frozenset(
            p for p in unignore_paths if not _is_glob_pattern(p)
        )
        glob_unignores = tuple(
            sorted(p for p in unignore_paths if _is_glob_pattern(p))
        )
        if (
            any(
                rel_path_str == p or rel_path_str.startswith(f"{p}/")
                for p in literal_unignores
            )
            or (
                glob_unignores
                and _compile_pathspec(glob_unignores).match_file(rel_path_str)
            )
        ):
            return False

    return not cs.IGNORE_PATTERNS.isdisjoint(dir_parts)
