"""Utility helper functions for the project management system."""

from __future__ import annotations


def next_id(prefix: str, existing: list[str]) -> str:
    """Generate the next sequential ID with given prefix."""
    numbers = [
        int(value.split("-")[1])
        for value in existing
        if value.startswith(prefix)
        and len(value.split("-")) == 2
        and value.split("-")[1].isdigit()
    ]
    next_number = max(numbers, default=0) + 1
    return f"{prefix}-{next_number:03d}"


def get_next_user_id(existing_ids: list[str]) -> str:
    """Generate the next user ID."""
    return next_id("U", existing_ids)


def get_next_project_id(existing_ids: list[str]) -> str:
    """Generate the next project ID."""
    return next_id("P", existing_ids)


def get_next_task_id(existing_ids: list[str]) -> str:
    """Generate the next task ID."""
    return next_id("T", existing_ids)