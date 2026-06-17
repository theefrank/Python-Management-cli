"""Command-line interface for the project management system using argparse."""

from __future__ import annotations

import argparse
import sys
from typing import Any

from models.entities import Project, Task, User
from utils import get_next_project_id, get_next_task_id, get_next_user_id, load_data, save_data
from utils.storage import backup_data

STATUS_OPTIONS = ["Open", "In Progress", "Completed", "Blocked"]
PRIORITY_OPTIONS = ["Low", "Normal", "High"]


def get_or_create_current_user(data: dict[str, Any]) -> User:
    """Get or create the default current user."""
    if not data["users"]:
        user_id = get_next_user_id([])
        user = User(id=user_id, name="Default User", email="user@example.com")
        data["users"].append(user)
    return data["users"][0]


def user_list(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """List all users."""
    if not data["users"]:
        print("No users found.")
        return

    print("\n=== Users ===\n")
    for user in data["users"]:
        print(f"• {user.name} ({user.id})")
        if user.email:
            print(f"  Email: {user.email}")
        print(f"  Projects: {len(user.projects)}\n")


def user_create(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """Create a new user."""
    existing_ids = [u.id for u in data["users"]]
    user_id = get_next_user_id(existing_ids)
    user = User(id=user_id, name=args.name, email=args.email or "")
    data["users"].append(user)
    print(f"✓ Created user '{user.name}' ({user.id})")


def project_list(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """List all projects for current user."""
    user = get_or_create_current_user(data)

    if not user.projects:
        print("No projects found.")
        return

    print("\n=== Projects ===\n")
    for project in user.projects:
        print(f"• {project.name} ({project.id})")
        if project.description:
            print(f"  {project.description}")
        print(f"  Tasks: {len(project.tasks)}\n")


def project_create(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """Create a new project."""
    user = get_or_create_current_user(data)
    existing_ids = [p.id for p in user.projects]
    project_id = get_next_project_id(existing_ids)
    project = Project(id=project_id, name=args.name, description=args.description or "")
    user.add_project(project)
    print(f"✓ Created project '{project.name}' ({project.id})")


def project_delete(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """Delete a project."""
    user = get_or_create_current_user(data)
    project = user.get_project(args.project_id)
    if not project:
        print(f"✗ Project {args.project_id} not found.")
        return

    if user.remove_project(args.project_id):
        print(f"✓ Deleted project '{project.name}' ({project.id})")
    else:
        print(f"✗ Failed to delete project.")


def task_list(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """List tasks in a project."""
    user = get_or_create_current_user(data)
    project = user.get_project(args.project_id)
    if not project:
        print(f"✗ Project {args.project_id} not found.")
        return

    if not project.tasks:
        print(f"No tasks in project '{project.name}'.")
        return

    print(f"\n=== Tasks in {project.name} ===\n")
    for i, task in enumerate(project.tasks, 1):
        print(f"{i}. {task.title} ({task.id})")
        print(f"   Status: {task.status} | Priority: {task.priority}")
        if task.due_date:
            print(f"   Due: {task.due_date}")
        if task.description:
            print(f"   {task.description}")
        print()


def task_create(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """Create a new task."""
    user = get_or_create_current_user(data)
    project = user.get_project(args.project_id)
    if not project:
        print(f"✗ Project {args.project_id} not found.")
        return

    existing_ids = [t.id for t in project.tasks]
    task_id = get_next_task_id(existing_ids)
    task = Task(
        id=task_id,
        title=args.title,
        description=args.description or "",
        priority=args.priority or "Normal",
        due_date=args.due_date or "",
    )
    project.add_task(task)
    print(f"✓ Created task '{task.title}' ({task.id}) in project {args.project_id}")


def task_status(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """Update task status."""
    user = get_or_create_current_user(data)
    project = user.get_project(args.project_id)
    if not project:
        print(f"✗ Project {args.project_id} not found.")
        return

    task = project.get_task(args.task_id)
    if not task:
        print(f"✗ Task {args.task_id} not found.")
        return

    if args.status not in STATUS_OPTIONS:
        print(f"✗ Invalid status. Options: {', '.join(STATUS_OPTIONS)}")
        return

    old_status = task.status
    task.status = args.status
    print(f"✓ Updated task '{task.title}': {old_status} → {args.status}")


def task_delete(args: argparse.Namespace, data: dict[str, Any]) -> None:
    """Delete a task."""
    user = get_or_create_current_user(data)
    project = user.get_project(args.project_id)
    if not project:
        print(f"✗ Project {args.project_id} not found.")
        return

    task = project.get_task(args.task_id)
    if not task:
        print(f"✗ Task {args.task_id} not found.")
        return

    project.remove_task(args.task_id)
    print(f"✓ Deleted task '{task.title}' ({task.id})")


def main() -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Project Management CLI - Organize your projects and tasks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python main.py project list\n  python main.py task create --project P-001 --title 'My Task'\n  python main.py task status --project P-001 --task T-001 --status 'Completed'",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # User commands
    user_parser = subparsers.add_parser("user", help="User management commands")
    user_subparsers = user_parser.add_subparsers(dest="user_cmd")
    user_subparsers.add_parser("list", help="List all users")
    user_create_parser = user_subparsers.add_parser("create", help="Create a new user")
    user_create_parser.add_argument("name", help="User name")
    user_create_parser.add_argument("--email", help="User email")

    # Project commands
    project_parser = subparsers.add_parser("project", help="Project management commands")
    project_subparsers = project_parser.add_subparsers(dest="project_cmd")
    project_subparsers.add_parser("list", help="List all projects")
    project_create_parser = project_subparsers.add_parser("create", help="Create a new project")
    project_create_parser.add_argument("name", help="Project name")
    project_create_parser.add_argument("--desc", dest="description", help="Project description")
    project_delete_parser = project_subparsers.add_parser("delete", help="Delete a project")
    project_delete_parser.add_argument("project_id", help="Project ID to delete")

    # Task commands
    task_parser = subparsers.add_parser("task", help="Task management commands")
    task_subparsers = task_parser.add_subparsers(dest="task_cmd")

    task_list_parser = task_subparsers.add_parser("list", help="List tasks in a project")
    task_list_parser.add_argument("project_id", help="Project ID")

    task_create_parser = task_subparsers.add_parser("create", help="Create a new task")
    task_create_parser.add_argument("--project", dest="project_id", required=True, help="Project ID")
    task_create_parser.add_argument("--title", required=True, help="Task title")
    task_create_parser.add_argument("--desc", dest="description", help="Task description")
    task_create_parser.add_argument("--priority", choices=PRIORITY_OPTIONS, help="Task priority")
    task_create_parser.add_argument("--due", dest="due_date", help="Due date (YYYY-MM-DD)")

    task_status_parser = task_subparsers.add_parser("status", help="Update task status")
    task_status_parser.add_argument("--project", dest="project_id", required=True, help="Project ID")
    task_status_parser.add_argument("--task", dest="task_id", required=True, help="Task ID")
    task_status_parser.add_argument("--status", required=True, choices=STATUS_OPTIONS, help="New status")

    task_delete_parser = task_subparsers.add_parser("delete", help="Delete a task")
    task_delete_parser.add_argument("--project", dest="project_id", required=True, help="Project ID")
    task_delete_parser.add_argument("--task", dest="task_id", required=True, help="Task ID")

    args = parser.parse_args()

    # Load data
    data = load_data()

    # Dispatch to command handlers
    try:
        if args.command == "user":
            if args.user_cmd == "list":
                user_list(args, data)
            elif args.user_cmd == "create":
                user_create(args, data)
            else:
                user_parser.print_help()
                return 1

        elif args.command == "project":
            if args.project_cmd == "list":
                project_list(args, data)
            elif args.project_cmd == "create":
                project_create(args, data)
            elif args.project_cmd == "delete":
                project_delete(args, data)
            else:
                project_parser.print_help()
                return 1

        elif args.command == "task":
            if args.task_cmd == "list":
                task_list(args, data)
            elif args.task_cmd == "create":
                task_create(args, data)
            elif args.task_cmd == "status":
                task_status(args, data)
            elif args.task_cmd == "delete":
                task_delete(args, data)
            else:
                task_parser.print_help()
                return 1

        else:
            parser.print_help()
            return 1

        # Save data
        if save_data(data):
            return 0
        else:
            print("✗ Failed to save data")
            return 1

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1