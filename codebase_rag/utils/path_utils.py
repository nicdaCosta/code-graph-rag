import re
import subprocess
from functools import lru_cache
from pathlib import Path

from loguru import logger

from .. import constants as cs
from .. import logs as ls

_GLOB_META = frozenset("*?[")


def _is_glob_pattern(pattern: str) -> bool:
    """True if *pattern* contains glob metacharacters."""
    return any(c in _GLOB_META for c in pattern)


@lru_cache(maxsize=256)
def _compile_glob(pattern: str) -> re.Pattern[str]:
    """Compile a gitignore-style glob pattern to an anchored regex.

    Supported syntax:
      * ``*``    — any sequence of characters except ``/``
      * ``**``   — any number of path segments (including zero)
      * ``?``    — any single character except ``/``
      * ``[abc]`` / ``[a-z]`` — character class, ``[!...]`` for negation

    Semantics mirror gitignore:
      * patterns containing ``/`` are anchored to the relative-path root
      * patterns without ``/`` match against *any* path component
    """
    i, n = 0, len(pattern)
    parts: list[str] = []
    while i < n:
        c = pattern[i]
        if c == "*":
            if i + 1 < n and pattern[i + 1] == "*":
                # '**' matches any number of path segments.
                i += 2
                if i < n and pattern[i] == "/":
                    # '**/' — zero or more path segments, trailing slash included.
                    parts.append("(?:.*/|)")
                    i += 1
                else:
                    parts.append(".*")
            else:
                parts.append("[^/]*")
                i += 1
        elif c == "?":
            parts.append("[^/]")
            i += 1
        elif c == "[":
            j = i + 1
            if j < n and pattern[j] == "!":
                parts.append("[^")
                j += 1
            else:
                parts.append("[")
            while j < n and pattern[j] != "]":
                parts.append(pattern[j])
                j += 1
            parts.append("]")
            i = j + 1
        else:
            parts.append(re.escape(c))
            i += 1
    regex = "".join(parts)
    if "/" not in pattern:
        regex = r"(?:.*/|)" + regex
    return re.compile(r"\A" + regex + r"\Z")


def _matches_any_glob(patterns: tuple[str, ...], rel_path_str: str) -> bool:
    """True if *rel_path_str* (or any ancestor path) matches any glob.

    Matching ancestors means a directory-targeting pattern like
    ``**/__mocks__`` also excludes everything inside it, mirroring
    literal-directory behaviour and gitignore semantics.
    """
    compiled = [_compile_glob(p) for p in patterns]
    candidate = rel_path_str
    while True:
        if any(rx.match(candidate) for rx in compiled):
            return True
        parent, sep, _ = candidate.rpartition("/")
        if not sep:
            return False
        candidate = parent


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
        glob_excludes = tuple(p for p in exclude_paths if _is_glob_pattern(p))
        if (
            not literal_excludes.isdisjoint(dir_parts)
            or rel_path_str in literal_excludes
            or any(rel_path_str.startswith(f"{p}/") for p in literal_excludes)
            or (glob_excludes and _matches_any_glob(glob_excludes, rel_path_str))
        ):
            return True

    if unignore_paths:
        literal_unignores = frozenset(
            p for p in unignore_paths if not _is_glob_pattern(p)
        )
        glob_unignores = tuple(p for p in unignore_paths if _is_glob_pattern(p))
        if (
            any(
                rel_path_str == p or rel_path_str.startswith(f"{p}/")
                for p in literal_unignores
            )
            or (glob_unignores and _matches_any_glob(glob_unignores, rel_path_str))
        ):
            return False

    return not cs.IGNORE_PATTERNS.isdisjoint(dir_parts)
