#!/usr/bin/env python3
"""Comprehensive test suite for the refactored project management system."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from models import Project, Task, User
from utils import backup_data, get_next_project_id, get_next_task_id, get_next_user_id, load_data, save_data


class TestTaskEntity:
    """Test Task entity."""

    def test_task_creation(self):
        task = Task(id="T-001", title="Test", description="Desc")
        assert task.id == "T-001"
        assert task.title == "Test"
        assert task.status == "Open"

    def test_task_from_dict(self):
        data = {"id": "T-001", "title": "Task", "description": "Desc", "status": "In Progress", "priority": "High"}
        task = Task.from_dict(data)
        assert task.status == "In Progress"
        assert task.priority == "High"

    def test_task_to_dict(self):
        task = Task(id="T-001", title="Task", description="Desc")
        result = task.to_dict()
        assert result["id"] == "T-001"
        assert result["title"] == "Task"


class TestProjectEntity:
    """Test Project entity."""

    def test_project_creation(self):
        project = Project(id="P-001", name="Project")
        assert project.id == "P-001"
        assert project.tasks == []

    def test_project_add_task(self):
        project = Project(id="P-001", name="Project")
        task = Task(id="T-001", title="Task", description="")
        project.add_task(task)
        assert len(project.tasks) == 1
        assert project.tasks[0].title == "Task"

    def test_project_get_task(self):
        project = Project(id="P-001", name="Project")
        task = Task(id="T-001", title="Task", description="")
        project.add_task(task)
        found = project.get_task("T-001")
        assert found == task

    def test_project_remove_task(self):
        project = Project(id="P-001", name="Project")
        task = Task(id="T-001", title="Task", description="")
        project.add_task(task)
        project.remove_task("T-001")
        assert len(project.tasks) == 0

    def test_project_from_dict(self):
        data = {
            "id": "P-001",
            "name": "Project",
            "description": "Desc",
            "tasks": [{"id": "T-001", "title": "Task", "description": "", "status": "Open", "priority": "Normal", "due_date": ""}],
        }
        project = Project.from_dict(data)
        assert len(project.tasks) == 1

    def test_project_to_dict(self):
        project = Project(id="P-001", name="Project", description="Desc")
        result = project.to_dict()
        assert result["id"] == "P-001"
        assert result["name"] == "Project"


class TestUserEntity:
    """Test User entity."""

    def test_user_creation(self):
        user = User(id="U-001", name="John", email="john@example.com")
        assert user.id == "U-001"
        assert user.projects == []

    def test_user_add_project(self):
        user = User(id="U-001", name="John")
        project = Project(id="P-001", name="Project")
        user.add_project(project)
        assert len(user.projects) == 1

    def test_user_get_project(self):
        user = User(id="U-001", name="John")
        project = Project(id="P-001", name="Project")
        user.add_project(project)
        found = user.get_project("P-001")
        assert found == project

    def test_user_remove_project(self):
        user = User(id="U-001", name="John")
        project = Project(id="P-001", name="Project")
        user.add_project(project)
        user.remove_project("P-001")
        assert len(user.projects) == 0

    def test_user_from_dict(self):
        data = {
            "id": "U-001",
            "name": "John",
            "email": "john@example.com",
            "projects": [{"id": "P-001", "name": "Project", "description": "", "tasks": []}],
        }
        user = User.from_dict(data)
        assert len(user.projects) == 1

    def test_user_to_dict(self):
        user = User(id="U-001", name="John", email="john@example.com")
        result = user.to_dict()
        assert result["id"] == "U-001"
        assert result["name"] == "John"


class TestIdGeneration:
    """Test ID generation utilities."""

    def test_get_next_user_id(self):
        result = get_next_user_id([])
        assert result == "U-001"

    def test_get_next_project_id(self):
        result = get_next_project_id(["P-001", "P-002"])
        assert result == "P-003"

    def test_get_next_task_id(self):
        result = get_next_task_id(["T-001"])
        assert result == "T-002"


class TestPersistence:
    """Test file persistence."""

    def test_load_data_empty(self):
        with patch("utils.storage.DATA_FILE", Path(tempfile.gettempdir()) / "nonexistent.json"):
            result = load_data()
            assert result == {"users": []}

    def test_save_and_load_data(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = Path(f.name)

        try:
            with patch("utils.storage.DATA_FILE", temp_file):
                user = User(id="U-001", name="John")
                project = Project(id="P-001", name="Project")
                task = Task(id="T-001", title="Task", description="")
                project.add_task(task)
                user.add_project(project)
                data = {"users": [user]}

                assert save_data(data)
                loaded = load_data()
                assert len(loaded["users"]) == 1
                assert len(loaded["users"][0].projects) == 1
        finally:
            temp_file.unlink(missing_ok=True)

    def test_load_corrupted_json(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json {")
            temp_file = Path(f.name)

        try:
            with patch("utils.storage.DATA_FILE", temp_file):
                result = load_data()
                assert result == {"users": []}
        finally:
            temp_file.unlink(missing_ok=True)

    def test_save_data_io_error(self):
        with patch("utils.storage.DATA_FILE", Path("/invalid/path/file.json")):
            result = save_data({"users": []})
            assert result is False

    def test_backup_data(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"users": []}')
            temp_file = Path(f.name)

        try:
            with patch("utils.storage.DATA_FILE", temp_file):
                assert backup_data()
                backup_file = temp_file.with_suffix(".backup.json")
                assert backup_file.exists()
                backup_file.unlink()
        finally:
            temp_file.unlink(missing_ok=True)


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_user_list_empty(self, capsys):
        from core.cli import user_list

        data = {"users": []}
        user_list(None, data)
        captured = capsys.readouterr()
        assert "No users found" in captured.out

    def test_project_list_empty(self, capsys):
        from core.cli import project_list

        data = {"users": [User(id="U-001", name="John")]}
        project_list(None, data)
        captured = capsys.readouterr()
        assert "No projects found" in captured.out

    def test_task_list_empty(self, capsys):
        from core.cli import task_list
        import argparse

        project = Project(id="P-001", name="Project")
        user = User(id="U-001", name="John")
        user.add_project(project)
        data = {"users": [user]}

        args = argparse.Namespace(project_id="P-001")
        task_list(args, data)
        captured = capsys.readouterr()
        assert "No tasks in project" in captured.out

    def test_create_project(self, capsys):
        from core.cli import project_create
        import argparse

        data = {"users": [User(id="U-001", name="John")]}
        args = argparse.Namespace(name="New Project", description="Description")

        project_create(args, data)
        captured = capsys.readouterr()
        assert "Created project" in captured.out
        assert len(data["users"][0].projects) == 1

    def test_create_task(self, capsys):
        from core.cli import task_create
        import argparse

        project = Project(id="P-001", name="Project")
        user = User(id="U-001", name="John")
        user.add_project(project)
        data = {"users": [user]}

        args = argparse.Namespace(
            project_id="P-001",
            title="New Task",
            description="Desc",
            priority="High",
            due_date="2026-06-15",
        )

        task_create(args, data)
        captured = capsys.readouterr()
        assert "Created task" in captured.out
        assert len(project.tasks) == 1

    def test_update_task_status(self, capsys):
        from core.cli import task_status
        import argparse

        task = Task(id="T-001", title="Task", description="")
        project = Project(id="P-001", name="Project", tasks=[task])
        user = User(id="U-001", name="John", projects=[project])
        data = {"users": [user]}

        args = argparse.Namespace(project_id="P-001", task_id="T-001", status="Completed")

        task_status(args, data)
        captured = capsys.readouterr()
        assert "Updated task" in captured.out
        assert task.status == "Completed"

    def test_delete_task(self, capsys):
        from core.cli import task_delete
        import argparse

        task = Task(id="T-001", title="Task", description="")
        project = Project(id="P-001", name="Project", tasks=[task])
        user = User(id="U-001", name="John", projects=[project])
        data = {"users": [user]}

        args = argparse.Namespace(project_id="P-001", task_id="T-001")

        task_delete(args, data)
        captured = capsys.readouterr()
        assert "Deleted task" in captured.out
        assert len(project.tasks) == 0