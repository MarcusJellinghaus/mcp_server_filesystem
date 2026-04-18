"""Parent branch detection via merge-base analysis."""

# Maximum commits between merge-base and candidate branch HEAD to consider
# the candidate as the parent branch. Higher values are more permissive but
# risk selecting wrong branches; lower values may miss valid parents that
# have moved forward since branching.
from pathlib import Path
from typing import Optional

from git.exc import GitCommandError, InvalidGitRepositoryError

from .core import _safe_repo_context, logger
from .repository_status import is_git_repository

MERGE_BASE_DISTANCE_THRESHOLD = 20


def detect_parent_branch_via_merge_base(
    project_dir: Path,
    current_branch: str,
    distance_threshold: int = MERGE_BASE_DISTANCE_THRESHOLD,
) -> Optional[str]:
    """Detect parent branch using git merge-base.

    For each local and remote branch (candidate), find the merge-base with
    current branch. The parent is the branch whose HEAD is closest to the
    merge-base (smallest distance).

    Args:
        project_dir: Path to git repository
        current_branch: Current branch name
        distance_threshold: Maximum commits between merge-base and candidate
            branch HEAD to consider the candidate as the parent branch.
            Defaults to MERGE_BASE_DISTANCE_THRESHOLD (20).

    Returns:
        Branch name if found within threshold, None otherwise
    """
    logger.debug(
        "Detecting parent branch for '%s' via merge-base (threshold=%d)",
        current_branch,
        distance_threshold,
    )

    if not is_git_repository(project_dir):
        logger.debug("Not a git repository: %s", project_dir)
        return None

    try:
        with _safe_repo_context(project_dir) as repo:
            # Get current branch commit
            try:
                current_commit = repo.heads[current_branch].commit
            except (IndexError, KeyError) as e:
                logger.debug(
                    "Failed to get commit for branch '%s': %s", current_branch, e
                )
                return None

            candidates_passing: list[tuple[str, int]] = []
            checked_branch_names: set[str] = set()

            # Check local branches
            for branch in repo.heads:
                if branch.name == current_branch:
                    continue

                try:
                    merge_base_list = repo.merge_base(current_commit, branch.commit)
                    if not merge_base_list:
                        logger.debug(
                            "No merge-base found for local branch '%s'", branch.name
                        )
                        continue

                    merge_base = merge_base_list[0]
                    # Count commits from merge-base to branch HEAD
                    distance = sum(
                        1
                        for _ in repo.iter_commits(
                            f"{merge_base.hexsha}..{branch.commit.hexsha}"
                        )
                    )
                    logger.debug(
                        "Local branch '%s': merge-base distance = %d",
                        branch.name,
                        distance,
                    )

                    # Early exit: distance=0 means ideal parent (branch HEAD is merge-base)
                    if distance == 0:
                        logger.debug(
                            "Detected parent branch from merge-base: '%s' (distance=0)",
                            branch.name,
                        )
                        return branch.name

                    if distance <= distance_threshold:
                        candidates_passing.append((branch.name, distance))
                        checked_branch_names.add(branch.name)

                except GitCommandError as e:
                    logger.debug(
                        "Git error checking local branch '%s': %s", branch.name, e
                    )
                    continue

            # Check remote branches (origin/*)
            try:
                if "origin" in [r.name for r in repo.remotes]:
                    for ref in repo.remotes.origin.refs:
                        # Extract branch name without "origin/" prefix
                        branch_name = ref.name.replace("origin/", "", 1)

                        # Skip current branch, HEAD, and already-checked branches
                        if branch_name in (current_branch, "HEAD"):
                            continue
                        if branch_name in checked_branch_names:
                            continue

                        try:
                            merge_base_list = repo.merge_base(
                                current_commit, ref.commit
                            )
                            if not merge_base_list:
                                logger.debug(
                                    "No merge-base found for remote branch '%s'",
                                    branch_name,
                                )
                                continue

                            merge_base = merge_base_list[0]
                            # Count commits from merge-base to remote branch HEAD
                            distance = sum(
                                1
                                for _ in repo.iter_commits(
                                    f"{merge_base.hexsha}..{ref.commit.hexsha}"
                                )
                            )
                            logger.debug(
                                "Remote branch '%s': merge-base distance = %d",
                                branch_name,
                                distance,
                            )

                            # Early exit: distance=0 means ideal parent
                            if distance == 0:
                                logger.debug(
                                    "Detected parent branch from merge-base: '%s' (distance=0)",
                                    branch_name,
                                )
                                return branch_name

                            if distance <= distance_threshold:
                                candidates_passing.append((branch_name, distance))
                                checked_branch_names.add(branch_name)

                        except GitCommandError as e:
                            logger.debug(
                                "Git error checking remote branch '%s': %s",
                                branch_name,
                                e,
                            )
                            continue
            except (
                Exception
            ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow to GitCommandError
                logger.debug("Error checking remote branches: %s", e)

            # Return smallest distance candidate
            if candidates_passing:
                candidates_passing.sort(key=lambda x: x[1])
                winner = candidates_passing[0]
                logger.debug(
                    "Detected parent branch from merge-base: '%s' (distance=%d)",
                    winner[0],
                    winner[1],
                )
                return winner[0]

            logger.debug("No candidate branches found within threshold")
            return None

    except InvalidGitRepositoryError:
        logger.debug("Invalid git repository: %s", project_dir)
        return None
    except (
        Exception
    ) as e:  # pylint: disable=broad-exception-caught  # TODO: narrow to GitCommandError
        logger.debug("Failed to detect parent branch: %s", e)
        return None
