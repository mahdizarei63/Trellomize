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
   
