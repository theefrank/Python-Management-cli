"""Domain entity models for the project management system."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """Represents a task within a project."""

    id: str
    title: str
    description: str
    status: str = "Open"
    priority: str = "Normal"
    due_date: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Task:
        """Create a Task from a dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "Open"),
            priority=data.get("priority", "Normal"),
            due_date=data.get("due_date", ""),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Task to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date,
        }


@dataclass
class Project:
    """Represents a project containing multiple tasks."""

    id: str
    name: str
    description: str = ""
    tasks: list[Task] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        """Create a Project from a dictionary."""
        tasks = [Task.from_dict(task_data) for task_data in data.get("tasks", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            tasks=tasks,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert Project to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": [task.to_dict() for task in self.tasks],
        }

    def add_task(self, task: Task) -> None:
        """Add a task to this project."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if successful."""
        self.tasks = [t for t in self.tasks if t.id != task_id]
        return len(self.tasks) < len([t for t in self.tasks if t.id != task_id])

    def get_task(self, task_id: str) -> Task | None:
        """Get a task by ID."""
        return next((t for t in self.tasks if t.id == task_id), None)


@dataclass
class User:
    """Represents a user with multiple projects."""

    id: str
    name: str
    email: str = ""
    projects: list[Project] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> User:
        """Create a User from a dictionary."""
        projects = [Project.from_dict(proj_data) for proj_data in data.get("projects", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            email=data.get("email", ""),
            projects=projects,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert User to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "projects": [proj.to_dict() for proj in self.projects],
        }

    def add_project(self, project: Project) -> None:
        """Add a project to this user."""
        self.projects.append(project)

    def remove_project(self, project_id: str) -> bool:
        """Remove a project by ID."""
        initial_count = len(self.projects)
        self.projects = [p for p in self.projects if p.id != project_id]
        return len(self.projects) < initial_count

    def get_project(self, project_id: str) -> Project | None:
        """Get a project by ID."""
        return next((p for p in self.projects if p.id == project_id), None)