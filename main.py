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
