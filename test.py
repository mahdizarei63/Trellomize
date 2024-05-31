import json
import os
import uuid
import re
import hashlib
from datetime import datetime, timedelta
from enum import Enum
from rich.console import Console
from rich.table import Table
from getpass import getpass
import unittest
from unittest.mock import patch


ADMIN_FILE = 'admin.json'
USERS_FILE = 'users.json'
PROJECTS_FILE = 'projects.json'
LOG_FILE = 'log.log'
console = Console()

def log_message(message):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{message}\n")

def load_data(file):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return []

def save_data(data, file):
    with open(file, 'w') as f:
        json.dump(data, f, indent=4)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def is_valid_email(email):
    email_regex = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    return re.match(email_regex, email) is not None


class Priority(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Status(Enum):
    BACKLOG = "BACKLOG"
    TODO = "TODO"
    DOING = "DOING"
    DONE = "DONE"
    ARCHIVED = "ARCHIVED"


class User:
    def __init__(self, username, email, password, role='user', active=True):
        self.username = username
        self.email = email
        self.password = hash_password(password)
        self.role = role
        self.active = active

    def to_dict(self):
        return {
            'username': self.username,
            'email': self.email,
            'password': self.password,
            'role': self.role,
            'active': self.active
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            role=data['role'],
            active=data['active']
        )

    @classmethod
    def register(cls):
        users = load_data(USERS_FILE)
        
        while True:
            email = input("Email: ")
            if not is_valid_email(email):
                console.print("Invalid email format!", style="bold red")
                continue

            username = input("Username: ")
            password = getpass("Password: ")

            if any(user['email'] == email for user in users):
                console.print("Email already exists!", style="bold red")
                continue
            if any(user['username'] == username for user in users):
                console.print("Username already exists!", style="bold red")
                continue

            user = cls(username, email, password)
            users.append(user.to_dict())
            save_data(users, USERS_FILE)
            log_message(f"User registered with username: {username}")
            console.print(f"User {username} registered successfully!", style="bold green")
            break

    @classmethod
    def login(cls):
        while True:
            users = load_data(USERS_FILE)
            admins = load_data(ADMIN_FILE)
            username = input("Username: ")

            all_users = users + admins

            user_data = next((user for user in all_users if user['username'] == username), None)
            if user_data is None:
                console.print("Username not found!", style="bold red")
                log_message(f"Failed login attempt with non-existent username: {username}")
                continue

            password = getpass("Password: ")
            hashed_password = hash_password(password)

            if user_data['password'] != hashed_password:
                console.print("Incorrect password!", style="bold red")
                log_message(f"Failed login attempt for username: {username} with incorrect password")
                continue

            if not user_data['active']:
                console.print("Account is inactive. Contact admin.", style="bold red")
                log_message(f"Failed login attempt for inactive user: {username}")
                return None

            user = cls.from_dict(user_data)
            console.print(f"Welcome {username}! (role: {user.role})", style="bold green")
            log_message(f"User {username} logged in successfully with role: {user.role}")
            return user

class Admin(User):
    def __init__(self, username, email, password, role='admin', active=True):
        super().__init__(username, email, password, role, active)

    @classmethod
    def register_admin(cls):
        admins = load_data(ADMIN_FILE)
        
        while True:
            username = input("Admin Username: ")
            password = getpass("Admin Password: ")

            if any(admin['username'] == username for admin in admins):
                console.print("Admin username already exists!", style="bold red")
                continue

            new_admin = cls(username, '', password)
            admins.append(new_admin.to_dict())
            save_data(admins, ADMIN_FILE)
            log_message(f"Admin registered with username: {username}")
            console.print(f"Admin {username} registered successfully!", style="bold green")
            break

    @classmethod
    def deactivate_user(cls, username):
        users = load_data(USERS_FILE)
        for user in users:
            if user['username'] == username:
                user['active'] = False
                save_data(users, USERS_FILE)
                log_message(f"User {username} deactivated by admin")
                console.print(f"User {username} deactivated successfully!", style="bold green")
                return
        console.print("User not found!", style="bold red")

    @classmethod
    def activate_user(cls, username):
        users = load_data(USERS_FILE)
        for user in users:
            if user['username'] == username:
                user['active'] = True
                save_data(users, USERS_FILE)
                log_message(f"User {username} activated by admin")
                console.print(f"User {username} activated successfully!", style="bold green")
                return
        console.print("User not found!", style="bold red")

    @classmethod
    def purge_data(cls):
        confirm = input("Are you sure you want to delete all data? (yes/no): ")
        if confirm.lower() == 'yes':
            for file in [USERS_FILE, PROJECTS_FILE, LOG_FILE]:
                if os.path.exists(file):
                    os.remove(file)
            console.print("All data purged!", style="bold green")
        else:
            console.print("Purge cancelled.", style="bold red")

class Task:
    def __init__(self, title, description, status=Status.BACKLOG, priority=Priority.MEDIUM):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.comments = []
        self.assignees = []
        self.history = []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.name,
            'priority': self.priority.name,
            'comments': self.comments,
            'assignees': self.assignees,
            'history': self.history
        }

    @classmethod
    def from_dict(cls, data):
        task = cls(
            title=data['title'],
            description=data['description'],
            status=Status[data['status']],
            priority=Priority[data['priority']]
        )
        task.id = data['id']
        task.comments = data['comments']
        task.assignees = data['assignees']
        task.history = data['history']
        return task

    def change_status(self, username, new_status):
        self.status = new_status
        self._log_history(username, f"Changed status to {new_status.name}")
        log_message(f"{username} changed status of {self.title} to {new_status.name}")

    def change_priority(self, username, new_priority):
        self.priority = new_priority
        self._log_history(username, f"Changed priority to {new_priority.name}")
        log_message(f"{username} changed priority of {self.title} to {new_priority.name}")

    def add_comment(self, username, comment):
        self.comments.append({
            'username': username,
            'content': comment,
            'timestamp': datetime.now().isoformat()
        })
        self._log_history(username, f"Added comment: {comment}")
        log_message(f"{username} added comment to {self.title}")

    def assign_user(self, username, assignee):
        if assignee not in self.assignees:
            self.assignees.append(assignee)
            log_message(f"{username} assigned {assignee} to {self.title}")
            self._log_history(username, f"Assigned {assignee} to task")

    def unassign_user(self, username, assignee):
        if assignee in self.assignees:
            self.assignees.remove(assignee)
            log_message(f"{username} unassigned {assignee} from {self.title}")
            self._log_history(username, f"Unassigned {assignee} from task")

    def _log_history(self, username, action):
        self.history.append({
            'username': username,
            'action': action,
            'timestamp': datetime.now().isoformat()
        })

class Project:
    def __init__(self, name, description, start_date=None, end_date=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.start_date = start_date if start_date else datetime.now().isoformat()
        self.end_date = end_date
        self.tasks = []

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'tasks': [task.to_dict() for task in self.tasks]
        }

    @classmethod
    def from_dict(cls, data):
        project = cls(
            name=data['name'],
            description=data['description'],
            start_date=data['start_date'],
            end_date=data['end_date']
        )
        project.id = data['id']
        project.tasks = [Task.from_dict(task_data) for task_data in data['tasks']]
        return project

    def add_task(self, task):
        self.tasks.append(task)
        log_message(f"Task {task.title} added to project {self.name}")

    def remove_task(self, task_id):
        self.tasks = [task for task in self.tasks if task.id != task_id]
        log_message(f"Task with id {task_id} removed from project {self.name}")

    def get_tasks_by_status(self, status):
        return [task for task in self.tasks if task.status == status]

class TestTaskManager(unittest.TestCase):

    def setUp(self):
        for file in [USERS_FILE, ADMIN_FILE, PROJECTS_FILE, LOG_FILE]:
            if os.path.exists(file):
                os.remove(file)

        self.test_user = User('testuser', 'testuser@example.com', 'password')
        self.test_admin = Admin('testadmin', 'testadmin@example.com', 'password')
        self.test_project = Project('Test Project', 'This is a test project')
        self.test_task = Task('Test Task', 'This is a test task')

    @patch('builtins.input', side_effect=['testuser@example.com', 'testuser', 'password'])
    @patch('getpass.getpass', return_value='password')
    def test_user_registration(self, mock_getpass, mock_input):
        User.register()
        users = load_data(USERS_FILE)
        self.assertEqual(len(users), 1, "Test failed: User not registered")
        self.assertEqual(users[0]['username'], 'testuser', "Test failed: Incorrect username")

    @patch('builtins.input', side_effect=['testuser', 'wrongpassword'])
    @patch('getpass.getpass', return_value='wrongpassword')
    def test_user_login_wrong_password(self, mock_getpass, mock_input):
        users = [self.test_user.to_dict()]
        save_data(users, USERS_FILE)
        with self.assertRaises(SystemExit):  
            user = User.login()
            self.assertIsNone(user, "Test failed: User should not be logged in with wrong password")

    @patch('builtins.input', side_effect=['testuser', 'password'])
    @patch('getpass.getpass', return_value='password')
    def test_user_login_correct_password(self, mock_getpass, mock_input):
        users = [self.test_user.to_dict()]
        save_data(users, USERS_FILE)
        user = User.login()
        self.assertIsNotNone(user, "Test failed: User not logged in")
        self.assertEqual(user.username, 'testuser', "Test failed: Incorrect username after login")

    @patch('builtins.input', side_effect=['testadmin', 'password'])
    @patch('getpass.getpass', return_value='password')
    def test_admin_registration(self, mock_getpass, mock_input):
        Admin.register_admin()
        admins = load_data(ADMIN_FILE)
        self.assertEqual(len(admins), 1, "Test failed: Admin not registered")
        self.assertEqual(admins[0]['username'], 'testadmin', "Test failed: Incorrect admin username")

    @patch('builtins.input', side_effect=['testuser@example.com', 'testuser', 'password'])
    @patch('getpass.getpass', return_value='password')
    def test_user_deactivation_activation(self, mock_getpass, mock_input):
        User.register()
        Admin.deactivate_user('testuser')
        users = load_data(USERS_FILE)
        self.assertFalse(users[0]['active'], "Test failed: User not deactivated")
        Admin.activate_user('testuser')
        users = load_data(USERS_FILE)
        self.assertTrue(users[0]['active'], "Test failed: User not activated")

    @patch('builtins.input', side_effect=['yes'])
    def test_data_purge(self, mock_input):
        User.register()
        Admin.register_admin()
        users = load_data(USERS_FILE)
        admins = load_data(ADMIN_FILE)
        self.assertEqual(len(users), 1, "Test failed: User not registered")
        self.assertEqual(len(admins), 1, "Test failed: Admin not registered")
        Admin.purge_data()
        users = load_data(USERS_FILE)
        admins = load_data(ADMIN_FILE)
        self.assertEqual(len(users), 0, "Test failed: User data not purged")
        self.assertEqual(len(admins), 0, "Test failed: Admin data not purged")

    def test_project_add_remove_task(self):
        self.test_project.add_task(self.test_task)
        self.assertEqual(len(self.test_project.tasks), 1, "Test failed: Task not added to project")
        self.test_project.remove_task(self.test_task.id)
        self.assertEqual(len(self.test_project.tasks), 0, "Test failed: Task not removed from project")

    def test_task_change_status_priority(self):
        new_status = Status.DONE
        self.test_task.change_status(self.test_user.username, new_status)
        self.assertEqual(self.test_task.status, new_status, "Test failed: Task status not changed")

        new_priority = Priority.HIGH
        self.test_task.change_priority(self.test_user.username, new_priority)
        self.assertEqual(self.test_task.priority, new_priority, "Test failed: Task priority not changed")

    def test_add_comment(self):
        comment = 'This is a test comment.'
        self.test_task.add_comment(self.test_user.username, comment)
        self.assertEqual(self.test_task.comments[0]['content'], comment, "Test failed: Comment not added")

    def test_assign_unassign_user(self):
        assignee = 'member1'
        self.test_task.assign_user(self.test_user.username, assignee)
        self.assertIn(assignee, self.test_task.assignees, "Test failed: User not assigned")

        self.test_task.unassign_user(self.test_user.username, assignee)
        self.assertNotIn(assignee, self.test_task.assignees, "Test failed: User not unassigned")

    def test_task_to_dict_and_back(self):
        task_dict = self.test_task.to_dict()
        new_task = Task.from_dict(task_dict)
        self.assertEqual(new_task.title, self.test_task.title, "Test failed: Task conversion to/from dict")

if __name__ == '__main__':
    unittest.main()
