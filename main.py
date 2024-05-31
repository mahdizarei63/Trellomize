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
