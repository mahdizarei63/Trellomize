import json
import os
import uuid
import re
import hashlib
from datetime import datetime , timedelta
from enum import Enum
from rich.console import Console
from rich.table import Table
from getpass import getpass



# Constants
ADMIN_FILE = 'admin.json'
USERS_FILE = 'users.json'
PROJECTS_FILE = 'projects.json'
LOG_FILE = 'log.log'
console = Console()

# Utility Functions
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

# Enumerations
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

# Classes
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
    def __init__(self, title="", description="", assignees=None, priority=Priority.LOW, status=Status.BACKLOG):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.start_time = datetime.now()
        self.end_time = self.start_time + timedelta(hours=24)
        self.assignees = assignees if assignees is not None else []
        self.priority = priority
        self.status = status
        self.history = []
        self.comments = []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'assignees': self.assignees,
            'priority': self.priority.value,
            'status': self.status.value,
            'history': self.history,
            'comments': self.comments
        }

    @classmethod
    def from_dict(cls, data):
        task = cls(
            title=data['title'],
            description=data['description'],
            assignees=data['assignees'],
            priority=Priority[data['priority']],
            status=Status[data['status']]
        )
        task.id = data['id']
        task.start_time = datetime.fromisoformat(data['start_time'])
        task.end_time = datetime.fromisoformat(data['end_time'])
        task.history = data['history']
        task.comments = data['comments']
        return task

    def add_comment(self, username, content):
        comment = {
            'username': username,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        self.comments.append(comment)
        log_message(f"{username} added a comment to {self.title}: {content}")
        self._log_history(username, f"Comment added: {content}")

    def change_status(self, username, new_status):
        old_status = self.status
        self.status = new_status
        log_message(f"{username} changed status of {self.title} from {old_status} to {new_status}")
        self._log_history(username, f"Status changed from {old_status} to {new_status}")

    def change_priority(self, username, new_priority):
        old_priority = self.priority
        self.priority = new_priority
        log_message(f"{username} changed priority of {self.title} from {old_priority} to {new_priority}")
        self._log_history(username, f"Priority changed from {old_priority} to {new_priority}")

    def assign_user(self, username, assignee):
        if assignee not in self.assignees:
            self.assignees.append(assignee)
            log_message(f"{username} assigned {assignee} to {self.title}")
            self._log_history(username, f"User {assignee} assigned to task")

    def unassign_user(self, username, assignee):
        if assignee in self.assignees:
            self.assignees.remove(assignee)
            log_message(f"{username} unassigned {assignee} from {self.title}")
            self._log_history(username, f"User {assignee} unassigned from task")

    def _log_history(self, username, change):
        self.history.append({
            'username': username,
            'change': change,
            'timestamp': datetime.now().isoformat()
        })

class Project:
    def __init__(self, id, title, leader, members=None, tasks=None):
        self.id = id
        self.title = title
        self.leader = leader
        self.members = members if members is not None else []
        self.tasks = tasks if tasks is not None else []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'leader': self.leader,
            'members': self.members,
            'tasks': [task.to_dict() for task in self.tasks]
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data['id'],
            title=data['title'],
            leader=data['leader'],
            members=data['members'],
            tasks=[Task.from_dict(task) for task in data['tasks']]
        )

    @classmethod
    def create_project(cls, user):
        title = input("Project title: ")
        project_id = str(uuid.uuid4())
        project = cls(project_id, title, user.username)
        project.members.append(user.username)

        projects = load_data(PROJECTS_FILE)
        projects.append(project.to_dict())
        save_data(projects, PROJECTS_FILE)
        log_message(f"Project {project_id} created by user {user.username}")
        console.print(f"Project {project_id} created successfully!", style="bold green")

    @classmethod
    def list_projects(cls, user):
        projects = load_data(PROJECTS_FILE)
        user_projects = [cls.from_dict(proj) for proj in projects if user.username in proj['members']]

        if not user_projects:
            console.print("No projects found!", style="bold red")
            return None

        table = Table(title="Projects", show_lines=True)
        table.add_column("Index", style="yellow")
        table.add_column("Title", style="magenta")
        table.add_column("ID", style="green")
        table.add_column("Role", style="red")
        table.add_column("Leader", style="blue")
        table.add_column("Members", style="cyan")

        for index, project in enumerate(user_projects, start=1):
            members = ", ".join(project.members)
            role = "Leader" if user.username == project.leader else "Member"
            table.add_row(str(index), project.title, project.id, role, project.leader, members)

        console.print(table)
        return user_projects

    def add_member(self, username):
        if username in self.members:
            console.print("User already a member of the project!", style="bold red")
            return
        
        self.members.append(username)
        self._update_project()
        log_message(f"User {username} added to project {self.id} by {self.leader}")
        console.print(f"User {username} added to project {self.id} successfully!", style="bold green")

    def remove_member(self, username):
        if username not in self.members:
            console.print("User not a member of the project!", style="bold red")
            return

        self.members.remove(username)
        self._update_project()
        log_message(f"User {username} removed from project {self.id} by {self.leader}")
        console.print(f"User {username} removed from project {self.id} successfully!", style="bold green")

    def delete(self):
        projects = load_data(PROJECTS_FILE)
        projects = [proj for proj in projects if proj['id'] != self.id]
        save_data(projects, PROJECTS_FILE)
        log_message(f"Project {self.id} deleted by user {self.leader}")
        console.print(f"Project {self.id} deleted successfully!", style="bold green")

    def create_task(self, user):
       title = input("Task title: ")
       description = input("Task description: ")
       priority = Priority.LOW
       status = Status.BACKLOG

       task = Task(title=title, description=description, priority=priority, status=status)
       self.tasks.append(task)
       self._update_project()
       log_message(f"Task {task.id} created by user {user.username} in project {self.id}")
       console.print(f"Task {task.id} created successfully!", style="bold green")
       self.edit_task_info(task.id, user.username)

    def list_tasks(self, user):
        table = Table(title="Tasks", show_lines=True)
        table.add_column("ID", style="cyan")
        table.add_column("Title", style="magenta")
        table.add_column("Description", style="magenta")
        table.add_column("Priority", style="magenta")
        table.add_column("Status", style="magenta")

        for task in self.tasks:
            table.add_row(task.id, task.title, task.description, task.priority.value, task.status.value)

        console.print(table)

    def _update_project(self):
        projects = load_data(PROJECTS_FILE)
        for i, project in enumerate(projects):
            if project['id'] == self.id:
                projects[i] = self.to_dict()
                break
        save_data(projects, PROJECTS_FILE)

    def display_details(self):
        table = Table(title="Project Details", show_lines=True)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="magenta")

        table.add_row("ID", self.id)
        table.add_row("Title", self.title)
        table.add_row("Leader", self.leader)
        table.add_row("Members", ", ".join(self.members))
        console.print(table)

    def edit_task_info(self, task_id, username):
        task = next((task for task in self.tasks if task.id == task_id), None)
        if not task:
            console.print("Task not found!", style="bold red")
            return

        while True:
            console.print("\n1. Edit Name\n2. Edit Description\n3. Edit Start Time\n4. Edit End Time\n5. Edit Assignees\n6. Edit Priority\n7. Edit Status\n8. View History\n9. Add Comment\n10. Delete Task\n11. Back\n")
            choice = input("Enter choice: ")
    
            try:
                if choice == '1':
                    new_name = input("Enter new task name: ")
                    task.title = new_name
                    task._log_history(username, f"Task name changed to {new_name}")
                    log_message(f"Task name of {task_id} changed to {new_name} by {username}")
                elif choice == '2':
                    new_description = input("Enter new task description: ")
                    task.description = new_description
                    task._log_history(username, f"Task description changed to {new_description}")
                    log_message(f"Task description of {task_id} changed to {new_description} by {username}")
                elif choice == '3':
                    new_start_time = input("Enter new start time (YYYY-MM-DD HH:MM:SS): ")
                    task.start_time = datetime.strptime(new_start_time, "%Y-%m-%d %H:%M:%S")
                    task._log_history(username, f"Task start time changed to {new_start_time}")
                    log_message(f"Task start time of {task_id} changed to {new_start_time} by {username}")
                elif choice == '4':
                    new_end_time = input("Enter new end time (YYYY-MM-DD HH:MM:SS): ")
                    task.end_time = datetime.strptime(new_end_time, "%Y-%m-%d %H:%M:%S")
                    task._log_history(username, f"Task end time changed to {new_end_time}")
                    log_message(f"Task end time of {task_id} changed to {new_end_time} by {username}")
                elif choice == '5':
                    assignee_action = input("Add or Remove assignee (a/r): ")
                    assignee_username = input("Enter assignee username: ")
                    if assignee_action == 'a':
                        task.assign_user(username, assignee_username)
                    elif assignee_action == 'r':
                        task.unassign_user(username, assignee_username)
                elif choice == '6':
                    new_priority = input("Enter new priority (CRITICAL/HIGH/MEDIUM/LOW): ").upper()
                    if new_priority not in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                        raise ValueError("Invalid priority! Priority must be one of: CRITICAL, HIGH, MEDIUM, LOW")
                    task.change_priority(username, Priority[new_priority])
                    log_message(f"Task priority of {task_id} changed to {new_priority} by {username}")
                elif choice == '7':
                    new_status = input("Enter new status (BACKLOG/TODO/DOING/DONE/ARCHIVED): ").upper()
                    if new_status not in ["BACKLOG", "TODO", "DOING", "DONE", "ARCHIVED"]:
                        raise ValueError("Invalid status! Status must be one of: BACKLOG, TODO, DOING, DONE, ARCHIVED")
                    task.change_status(username, Status[new_status])
                    log_message(f"Task status of {task_id} changed to {new_status} by {username}")
                elif choice == '8':
                    for entry in task.history:
                        console.print(f"{entry['timestamp']} - {entry['username']}: {entry['change']}", style="bold blue")
                elif choice == '9':
                    comment_content = input("Enter comment: ")
                    task.add_comment(username, comment_content)
                elif choice == '10':
                    self.tasks = [t for t in self.tasks if t.id != task_id]
                    self._update_project()
                    log_message(f"Task {task_id} deleted by {username} in project {self.id}")
                    console.print(f"Task {task_id} deleted successfully!", style="bold green")
                    break
                elif choice == '11':
                    break
                else:
                    console.print("Invalid choice!", style="bold red")

                self._update_project()
    
            except ValueError as e:
                console.print(f"Error: {e}", style="bold red")
            except Exception as e:
                console.print(f"An error occurred: {e}", style="bold red")



def view_task(selected_project):
    while True:
        task_id = input("Enter task ID to view (or 0 to go back): ")
        if task_id == '0':
            return

        try:
            task = next((t for t in selected_project.tasks if t.id == task_id), None)
            if task:
                console.print("\nTask Details", style="bold underline")
                console.print(f"NAME: {task.title}")
                console.print(f"DESCRIPTION: {task.description}")
                console.print(f"START TIME: {task.start_time}")
                console.print(f"END TIME: {task.end_time}")
                console.print(f"ASSIGNEES: {', '.join(task.assignees)}")
                console.print(f"PRIORITY: {task.priority}")
                console.print(f"STATUS: {task.status}")
                console.print(f"HISTORY: {task.history}")
                console.print(f"COMMENTS: {task.comments}")

                input("\nPress 'Enter' to go back to task ID input.")
            else:
                console.print("Task not found!", style="bold red")
        except Exception as e:
            console.print(f"An error occurred: {e}", style="bold red")


def task_table(user, selected_project):
    while True:
        try:
            # وضعیت‌های مختلف تسک‌ها
            allstat = ["BACKLOG", "TODO", "DOING", "DONE", "ARCHIVED"]

            task_list = []
            for t in allstat:
             task_list.append(list(map(lambda x: x.title, filter(lambda i: str(i.status).split('.')[-1] == t, selected_project.tasks))))
            mm = len(max(task_list, key=len))
            task_list.append(range(1, mm + 1))
            for i in task_list:
             while len(i) < mm:
                i.append('')

            table = Table(title="Tasks", show_lines=True)
            table.add_column("Index",style="cyan")
            table.add_column("BACKLOG",style="yellow")
            table.add_column("TODO", style="green")
            table.add_column("DOING", style="magenta")
            table.add_column("DONE", style="blue")
            table.add_column("ARCHIVED", style="red")
            for a, b, c, d, e, i in zip(*task_list):
                table.add_row(str(i), a, b, c, d, e)
            console.print(table)

            task_name = input("\nEnter task name to select (or 0 to go back): ")
            if task_name == '0':
                return

            task = next((t for t in selected_project.tasks if t.title == task_name), None)
            if not task:
                console.print("Task not found!", style="bold red")
                continue

            while True:
                console.print("\n1. View task details\n2. Edit task info\n3. Back\n")
                choice = input("Enter choice: ")
                if choice == '1':
                    console.print("\nTask Details", style="bold underline")
                    console.print(f"NAME: {task.title}")
                    console.print(f"DESCRIPTION: {task.description}")
                    console.print(f"START TIME: {task.start_time}")
                    console.print(f"END TIME: {task.end_time}")
                    console.print(f"ASSIGNEES: {', '.join(task.assignees)}")
                    console.print(f"PRIORITY: {task.priority}")
                    console.print(f"STATUS: {task.status}")
                    console.print(f"HISTORY: {task.history}")
                    console.print(f"COMMENTS: {task.comments}")

                    input("\nPress 'Enter' to go back to task options.")
                elif choice == '2':
                    if user.username == selected_project.leader or user.username in task.assignees:
                        selected_project.edit_task_info(task.id, user.username)
                        break  # بعد از ویرایش تسک، بازگشت به منوی task_table
                    else:
                        console.print("You are not assigned to this task!", style="bold red")
                elif choice == '3':
                    break
                else:
                    console.print("Invalid choice!", style="bold red")

        except Exception as e:
            console.print(f"An error occurred: {e}", style="bold red")






def main_menu(user):
    while True:
        console.print("\n1. Create project\n2. Projects\n3. Logout\n")
        choice = input("Enter choice: ")

        if choice == '1':
            Project.create_project(user)
        elif choice == '2':
            user_projects = Project.list_projects(user)
            if user_projects:
                while True:
                    try:
                        project_choice = int(input("Select project index: ")) - 1
                        if project_choice < 0 or project_choice >= len(user_projects):
                            raise ValueError
                        selected_project = user_projects[project_choice]
                        project_menu(user, selected_project)
                        break
                    except (ValueError, IndexError):
                        console.print("Invalid selection!", style="bold red")
        elif choice == '3':
            break
        else:
            console.print("Invalid choice!", style="bold red")

def project_menu(user, selected_project):
    while True:
        role = "Leader" if user.username == selected_project.leader else "Member"
        console.print(f"\nProject: {selected_project.title} (Role: {role})", style="bold green")

        if role == "Leader":
            console.print("\n1. Add member to project\n2. Remove member from project\n3. Delete project\n4. Create task\n5. Edit task\n6. List tasks\n7. View task\n8. Task table\n9. Project details\n10. Back\n")
            choice = input("Enter choice: ")
            if choice == '1':
                selected_project.add_member(input("Enter username to add: "))
            elif choice == '2':
                selected_project.remove_member(input("Enter username to remove: "))
            elif choice == '3':
                selected_project.delete()
                break
            elif choice == '4':
                selected_project.create_task(user)
            elif choice == '5':
                task_id = input("Enter task ID to edit: ")
                selected_project.edit_task_info(task_id, user.username)
            elif choice == '6':
                selected_project.list_tasks(user)
            elif choice == '7':
                view_task(selected_project)
            elif choice == '8':
                task_table(user, selected_project)
            elif choice == '9':
                selected_project.display_details()
            elif choice == '10':
                break
            else:
                console.print("Invalid choice!", style="bold red")
        else:
            console.print("\n1. List tasks\n2. View task\n3. Edit task\n4. Task table\n5. Project details\n6. Back\n")
            choice = input("Enter choice: ")
            if choice == '1':
                selected_project.list_tasks(user)
            elif choice == '2':
                view_task(selected_project)
            elif choice == '3':
                task_id = input("Enter task ID to edit: ")
                task = next((t for t in selected_project.tasks if t.id == task_id), None)
                if task:
                    if any(assignee == user.username for assignee in task.assignees):
                        selected_project.edit_task_info(task_id, user.username)
                    else:
                        console.print("You are not assigned to this task!", style="bold red")
                else:
                    console.print("Task not found!", style="bold red")
            elif choice == '4':
                task_table(user, selected_project)
            elif choice == '5':
                selected_project.display_details()
            elif choice == '6':
                break
            else:
                console.print("Invalid choice!", style="bold red")





def admin_menu(user):
    while True:
        console.print("\n1. Create project\n2. Projects\n3. Deactivate user\n4. Activate user\n5. Register new admin\n6. Purge data\n7. Logout\n")
        choice = input("Enter choice: ")

        if choice == '1':
            Project.create_project(user)
        elif choice == '2':
            user_projects = Project.list_projects(user)
            if user_projects:
                while True:
                    try:
                        project_choice = int(input("Select project index: ")) - 1
                        if project_choice < 0 or project_choice >= len(user_projects):
                            raise ValueError
                        selected_project = user_projects[project_choice]
                        project_menu(user, selected_project)
                        break
                    except (ValueError, IndexError):
                        console.print("Invalid selection!", style="bold red")
        elif choice == '3':
            Admin.deactivate_user(input("Enter username to deactivate: "))
        elif choice == '4':
            Admin.activate_user(input("Enter username to activate: "))
        elif choice == '5':
            Admin.register_admin()
        elif choice == '6':
            Admin.purge_data()
        elif choice == '7':
            break
        else:
            console.print("Invalid choice!", style="bold red")

def main():
    while True:
        console.print("\n1. Register\n2. Login\n3. Exit\n")
        choice = input("Enter choice: ")

        if choice == '1':
            User.register()
        elif choice == '2':
            user = User.login()
            if user:
                if user.role == 'admin':
                    admin_menu(user)
                else:
                    main_menu(user)
        elif choice == '3':
            break
        else:
            console.print("Invalid choice!", style="bold red")

if __name__ == "__main__":
    main()
