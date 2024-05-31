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

     
  class Project:
    def __init__(self, title, leader):
        self.id = str(uuid.uuid4())
        self.title = title
        self.leader = leader
        self.members = [leader]
        self.tasks = []

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'leader': self.leader,
            'members': self.members,
            'tasks': self.tasks
        }

   @classmethod
    def from_dict(cls, data):
        project = cls(data['title'], data['leader'])
        project.id = data['id']
        project.members = data['members']
        project.tasks = data['tasks']
        return project

    @classmethod
    def create_project(cls, user):
        projects = load_data(PROJECTS_FILE)
        title = input("Project title: ")
        project = cls(title, user.username)
        projects.append(project.to_dict())
        save_data(projects, PROJECTS_FILE)
        log_message(f"Project created with ID: {project.id} by user: {user.username}")
        console.print(f"Project {title} created successfully with ID: {project.id}", style="bold green")

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

        users = load_data(USERS_FILE)
        admins = load_data(ADMIN_FILE)
        all_users = users + admins

        user_to_add = next((usr for usr in all_users if usr['username'] == username), None)
        if not user_to_add:
            console.print("User not found!", style="bold red")
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

        self.members.append(username)
        self._update_project()
        log_message(f"User {username} added to project {self.id} by {self.leader}")
        console.print(f"User {username} added to project {self.id} successfully!", style="bold green")

def delete(self):
        projects = load_data(PROJECTS_FILE)
        projects = [proj for proj in projects if proj['id'] != self.id]
        save_data(projects, PROJECTS_FILE)
        log_message(f"Project {self.id} deleted by user {self.leader}")
        console.print(f"Project {self.id} deleted successfully!", style="bold green")

