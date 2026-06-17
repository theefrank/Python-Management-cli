#!/usr/bin/env python3
"""
Project Manager - because Jira is overkill

I got tired of spreadsheets so here's a CLI thingy.
Tasks, projects, users. Saves to data.json.
"""

import json
import sys
import os
from datetime import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

# Try to make things pretty, but I don't really care that much
try:
    from tabulate import tabulate
except ImportError:
    print("Hey, run 'pip install tabulate' first")
    sys.exit(1)

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    # Meh, no colors then
    Fore = type('Fore', (), {'RED': '', 'GREEN': '', 'YELLOW': '', 'CYAN': '', 'RESET': ''})
    Style = type('Style', (), {'BRIGHT': '', 'RESET_ALL': ''})

DATA_FILE = Path(__file__).parent / "data.json"
STATUSES = ["Open", "In Progress", "Completed", "Blocked"]
PRIORITIES = ["Low", "Normal", "High"]


@dataclass
class Task:
    """A task. You know, stuff to do."""
    id: str
    title: str
    description: str = ""
    status: str = "Open"
    priority: str = "Normal"
    due_date: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description", ""),
            status=data.get("status", "Open"),
            priority=data.get("priority", "Normal"),
            due_date=data.get("due_date", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )

    def to_dict(self):
        return asdict(self)

    def is_late(self):
        """Did we miss the deadline?"""
        if not self.due_date or self.status == "Completed":
            return False
        try:
            due = datetime.strptime(self.due_date, "%Y-%m-%d")
            return due < datetime.now()
        except:
            return False  # Bad date format? Not my problem


@dataclass
class Project:
    """A bucket for tasks."""
    id: str
    name: str
    description: str = ""
    tasks: List[Task] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_dict(cls, data):
        tasks = [Task.from_dict(t) for t in data.get("tasks", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            tasks=tasks,
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat())
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def stats(self):
        """Give me the numbers."""
        return {
            "total": len(self.tasks),
            "open": sum(1 for t in self.tasks if t.status == "Open"),
            "doing": sum(1 for t in self.tasks if t.status == "In Progress"),
            "done": sum(1 for t in self.tasks if t.status == "Completed"),
            "stuck": sum(1 for t in self.tasks if t.status == "Blocked"),
            "late": sum(1 for t in self.tasks if t.is_late())
        }


@dataclass
class User:
    """Someone using this thing."""
    id: str
    name: str
    email: str = ""
    projects: List[Project] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @classmethod
    def from_dict(cls, data):
        projects = [Project.from_dict(p) for p in data.get("projects", [])]
        return cls(
            id=data["id"],
            name=data["name"],
            email=data.get("email", ""),
            projects=projects,
            created_at=data.get("created_at", datetime.now().isoformat())
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "projects": [p.to_dict() for p in self.projects],
            "created_at": self.created_at
        }


class App:
    """The main thing. Runs everything."""
    
    def __init__(self):
        self.data_file = DATA_FILE
        self.users = self._load()
        self.current = None
        self._dirty = False  # Changed but not saved?
    
    def _load(self):
        """Load from disk. Or don't."""
        if not self.data_file.exists():
            return []
        
        try:
            with open(self.data_file, 'r') as f:
                raw = json.load(f)
                return [User.from_dict(u) for u in raw.get("users", [])]
        except:
            print("Hmm, data file is messed up. Starting fresh.")
            return []
    
    def _save(self):
        """Save to disk. Pray it works."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump({"users": [u.to_dict() for u in self.users]}, f, indent=2)
            return True
        except:
            print("Failed to save. Check permissions or something.")
            return False
    
    def _next_id(self, prefix, existing):
        """Generate IDs like P-001, T-042, etc. Because numbers are boring."""
        nums = []
        for x in existing:
            if x.startswith(prefix) and '-' in x:
                try:
                    nums.append(int(x.split('-')[1]))
                except:
                    pass
        next_num = max(nums, default=0) + 1
        return f"{prefix}-{next_num:03d}"
    
    def _show_table(self, headers, rows, title=None):
        """Pretty table. Sometimes with a title."""
        if title:
            print(f"\n{Fore.CYAN}{title}{Fore.RESET}")
            print('-' * len(title))
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print()
    
    def _new_user(self):
        """Make a new user. Please don't use fake emails."""
        print(f"\n{Fore.CYAN}New User{Fore.RESET}")
        
        name = input("Name: ").strip()
        if not name:
            print(f"{Fore.RED}Name required.{Fore.RESET}")
            return None
        
        email = input("Email (optional): ").strip()
        
        # Annoying but helpful check
        if email and any(u.email == email for u in self.users):
            print(f"{Fore.YELLOW}That email exists. Continue anyway?{Fore.RESET}")
            if input("(y/N): ").lower() != 'y':
                return None
        
        user = User(
            id=self._next_id("U", [u.id for u in self.users]),
            name=name,
            email=email
        )
        self.users.append(user)
        self._dirty = True
        
        self._show_table(["ID", "Name", "Email"], [[user.id, user.name, user.email or "-"]], "✓ User created")
        return user
    
    def _pick_user(self):
        """Choose who's using this thing."""
        while True:
            if not self.users:
                print(f"\n{Fore.YELLOW}No users. Let's make one.{Fore.RESET}")
                user = self._new_user()
                if user:
                    self.current = user
                    break
            else:
                print(f"\n{Fore.CYAN}Users:{Fore.RESET}")
                rows = [[i+1, u.id, u.name, u.email or "-", len(u.projects)] 
                       for i, u in enumerate(self.users)]
                self._show_table(["#", "ID", "Name", "Email", "Projects"], rows)
                
                print("Options: [number] to select, [n] new user, [q] quit")
                choice = input("> ").strip().lower()
                
                if choice == 'q':
                    sys.exit(0)
                elif choice == 'n':
                    user = self._new_user()
                    if user:
                        self.current = user
                        break
                else:
                    try:
                        idx = int(choice) - 1
                        if 0 <= idx < len(self.users):
                            self.current = self.users[idx]
                            print(f"{Fore.GREEN}Hi {self.current.name}!{Fore.RESET}")
                            break
                    except:
                        print(f"{Fore.RED}Wut?{Fore.RESET}")
    
    def _list_projects(self):
        """Show all my projects."""
        if not self.current.projects:
            print(f"\n{Fore.YELLOW}No projects yet. Make one.{Fore.RESET}")
            return
        
        rows = []
        for p in self.current.projects:
            s = p.stats()
            desc = (p.description[:40] + '...') if len(p.description) > 40 else (p.description or '-')
            rows.append([
                p.id, p.name, desc, s['total'], 
                f"{Fore.GREEN}{s['done']}{Fore.RESET}",
                f"{Fore.CYAN}{s['doing']}{Fore.RESET}",
                s['late']
            ])
        
        self._show_table(
            ["ID", "Name", "Description", "Tasks", "Done", "Doing", "Late"],
            rows,
            f"{self.current.name}'s Projects"
        )
    
    def _new_project(self):
        """Create a new project."""
        print(f"\n{Fore.CYAN}New Project{Fore.RESET}")
        
        name = input("Name: ").strip()
        if not name:
            print(f"{Fore.RED}Name needed.{Fore.RESET}")
            return
        
        desc = input("Description (optional): ").strip()
        
        p = Project(
            id=self._next_id("P", [p.id for p in self.current.projects]),
            name=name,
            description=desc
        )
        self.current.projects.append(p)
        self._dirty = True
        
        self._show_table(["ID", "Name"], [[p.id, p.name]], "✓ Project created")
    
    def _delete_project(self):
        """Remove a project and everything in it."""
        if not self.current.projects:
            print(f"{Fore.YELLOW}Nothing to delete.{Fore.RESET}")
            return
        
        self._list_projects()
        pid = input("\nProject ID to delete (or cancel): ").strip()
        if pid.lower() == 'cancel':
            return
        
        p = next((p for p in self.current.projects if p.id == pid), None)
        if not p:
            print(f"{Fore.RED}Not found.{Fore.RESET}")
            return
        
        if p.tasks:
            print(f"{Fore.YELLOW}This project has {len(p.tasks)} tasks. Delete anyway?{Fore.RESET}")
            if input("(y/N): ").lower() != 'y':
                return
        
        self.current.projects = [proj for proj in self.current.projects if proj.id != pid]
        self._dirty = True
        print(f"{Fore.GREEN}Deleted {p.name}{Fore.RESET}")
    
    def _list_tasks(self):
        """Show tasks in a project."""
        if not self.current.projects:
            print(f"{Fore.YELLOW}No projects.{Fore.RESET}")
            return
        
        self._list_projects()
        pid = input("\nProject ID: ").strip()
        if pid.lower() == 'cancel':
            return
        
        p = next((p for p in self.current.projects if p.id == pid), None)
        if not p:
            print(f"{Fore.RED}Not found.{Fore.RESET}")
            return
        
        if not p.tasks:
            print(f"{Fore.YELLOW}No tasks in {p.name}{Fore.RESET}")
            return
        
        rows = [[t.id, t.title[:40], t.status, t.priority, t.due_date or '-'] for t in p.tasks]
        self._show_table(["ID", "Title", "Status", "Priority", "Due"], rows, f"Tasks: {p.name}")
    
    def _add_task(self):
        """Add a new task to a project."""
        if not self.current.projects:
            print(f"{Fore.YELLOW}Need a project first.{Fore.RESET}")
            return
        
        self._list_projects()
        pid = input("\nProject ID: ").strip()
        if pid.lower() == 'cancel':
            return
        
        p = next((p for p in self.current.projects if p.id == pid), None)
        if not p:
            print(f"{Fore.RED}Not found.{Fore.RESET}")
            return
        
        print(f"\n{Fore.CYAN}New task in {p.name}{Fore.RESET}")
        
        title = input("Title: ").strip()
        if not title:
            print(f"{Fore.RED}Title required.{Fore.RESET}")
            return
        
        desc = input("Description (optional): ").strip()
        
        print(f"Priority: {', '.join(PRIORITIES)}")
        pri = input("Priority [Normal]: ").strip()
        if pri not in PRIORITIES:
            pri = "Normal"
        
        due = input("Due date (YYYY-MM-DD, optional): ").strip()
        if due:
            try:
                datetime.strptime(due, "%Y-%m-%d")
            except:
                print(f"{Fore.YELLOW}Bad date. Ignoring.{Fore.RESET}")
                due = ""
        
        t = Task(
            id=self._next_id("T", [t.id for t in p.tasks]),
            title=title,
            description=desc,
            priority=pri,
            due_date=due
        )
        p.tasks.append(t)
        self._dirty = True
        
        self._show_table(["ID", "Title", "Priority"], [[t.id, t.title, t.priority]], "✓ Task added")
    
    def _update_status(self):
        """Change task status."""
        if not self.current.projects:
            print(f"{Fore.YELLOW}No projects.{Fore.RESET}")
            return
        
        self._list_projects()
        pid = input("\nProject ID: ").strip()
        if pid.lower() == 'cancel':
            return
        
        p = next((p for p in self.current.projects if p.id == pid), None)
        if not p or not p.tasks:
            print(f"{Fore.RED}No tasks here.{Fore.RESET}")
            return
        
        # Quick task list
        rows = [[t.id, t.title[:35], t.status] for t in p.tasks]
        self._show_table(["ID", "Title", "Status"], rows, f"Tasks in {p.name}")
        
        tid = input("\nTask ID: ").strip()
        if tid.lower() == 'cancel':
            return
        
        t = next((t for t in p.tasks if t.id == tid), None)
        if not t:
            print(f"{Fore.RED}Not found.{Fore.RESET}")
            return
        
        print(f"Statuses: {', '.join(STATUSES)}")
        print(f"Current: {t.status}")
        new = input("New status: ").strip()
        
        if new not in STATUSES:
            print(f"{Fore.RED}Invalid.{Fore.RESET}")
            return
        
        t.status = new
        t.updated_at = datetime.now().isoformat()
        self._dirty = True
        print(f"{Fore.GREEN}{t.title} -> {new}{Fore.RESET}")
    
    def _delete_task(self):
        """Remove a task."""
        if not self.current.projects:
            print(f"{Fore.YELLOW}No projects.{Fore.RESET}")
            return
        
        self._list_projects()
        pid = input("\nProject ID: ").strip()
        if pid.lower() == 'cancel':
            return
        
        p = next((p for p in self.current.projects if p.id == pid), None)
        if not p or not p.tasks:
            print(f"{Fore.RED}No tasks.{Fore.RESET}")
            return
        
        rows = [[t.id, t.title[:40], t.status] for t in p.tasks]
        self._show_table(["ID", "Title", "Status"], rows, f"Tasks in {p.name}")
        
        tid = input("\nTask ID to delete: ").strip()
        if tid.lower() == 'cancel':
            return
        
        t = next((t for t in p.tasks if t.id == tid), None)
        if not t:
            print(f"{Fore.RED}Not found.{Fore.RESET}")
            return
        
        if input(f"Delete '{t.title}'? (y/N): ").lower() != 'y':
            return
        
        p.tasks = [task for task in p.tasks if task.id != tid]
        self._dirty = True
        print(f"{Fore.GREEN}Deleted{Fore.RESET}")
    
    def _switch_user(self):
        """Log out, log in as someone else."""
        self.current = None
        self._pick_user()
    
    def _exit(self, save=True):
        """Quit. Maybe save first."""
        if save and self._dirty:
            if self._save():
                print(f"{Fore.GREEN}Saved.{Fore.RESET}")
            else:
                print(f"{Fore.RED}Save failed!{Fore.RESET}")
        elif self._dirty:
            print(f"{Fore.YELLOW}Changes lost. Oh well.{Fore.RESET}")
        
        print("Bye!")
        sys.exit(0)
    
    def run(self):
        """The main loop. Where the magic happens."""
        print(f"\n{Fore.GREEN}{'='*40}{Fore.RESET}")
        print(f"{Fore.GREEN}   Project Manager {Fore.RESET}")
        print(f"{Fore.GREEN}{'='*40}{Fore.RESET}")
        
        self._pick_user()
        
        menu = """
{cyan}--- Menu ---{reset}
1) List projects
2) New project
3) Delete project
4) Add task
5) List tasks
6) Update status
7) Delete task
8) Switch user
9) Save & quit
10) Quit (no save)

{cyan}Current: {green}{user}{reset}
        """.format(
            cyan=Fore.CYAN, reset=Fore.RESET, green=Fore.GREEN,
            user=f"{self.current.name} ({self.current.id})"
        )
        
        while True:
            print(menu)
            choice = input("> ").strip()
            
            actions = {
                '1': self._list_projects,
                '2': self._new_project,
                '3': self._delete_project,
                '4': self._add_task,
                '5': self._list_tasks,
                '6': self._update_status,
                '7': self._delete_task,
                '8': self._switch_user,
                '9': lambda: self._exit(save=True),
                '10': lambda: self._exit(save=False),
            }
            
            if choice in actions:
                actions[choice]()
                # Update the user name in menu after switching
                if choice == '8':
                    menu = menu.replace(
                        f"{self.current.name} ({self.current.id})" if 'user' in menu else '',
                        f"{self.current.name} ({self.current.id})"
                    )
            else:
                print(f"{Fore.RED}Huh? Pick 1-10{Fore.RESET}")


def main():
    try:
        App().run()
    except KeyboardInterrupt:
        print("\n\nLater!")
        sys.exit(0)


if __name__ == "__main__":
    main()