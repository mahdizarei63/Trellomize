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
            console.print("\n1. Add member to project\n2. Remove member from project\n3. Delete project\n4. Project details\n5. Back\n")
            choice = input("Enter choice: ")
            if choice == '1':
                selected_project.add_member(input("Enter username to add: "))
            elif choice == '2':
                selected_project.remove_member(input("Enter username to remove: "))
            elif choice == '3':
                selected_project.delete()
                break
            elif choice == '4':
                selected_project.display_details()
            elif choice == '5':
                break
            else:
                console.print("Invalid choice!", style="bold red")
        else:
            console.print("\n1. Project details\n2. Back\n")
            choice = input("Enter choice: ")
            if choice == '1':
                selected_project.display_details()
            elif choice == '2':
                break
            else:
                console.print("Invalid choice!", style="bold red")
