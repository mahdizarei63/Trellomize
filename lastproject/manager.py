import argparse
import json
import os
from hashlib import sha256
from getpass import getpass

ADMIN_FILE = 'admin.json'
USERS_FILE = 'users.json'
PROJECTS_FILE = 'projects.json'
LOG_FILE = 'log.txt'



############ class file managing 


class FileManager:
    @staticmethod
    def load_data(file):
        if os.path.exists(file):
            with open(file, 'r') as f:
                return json.load(f)
        return []
######### saving data 

    @staticmethod
    def save_data(data, file):
        with open(file, 'w') as f:
            json.dump(data, f, indent=4)
############### class haye admin taghriban moshabehe main 

class Logger:
    @staticmethod
    def log_message(message):
        with open(LOG_FILE, 'a') as f:
            f.write(f"{message}\n")
############### class  user taghriban moshabehe main 

class User:
    def __init__(self, username, password, email, role, active=True):
        self.username = username
        self.password = sha256(password.encode()).hexdigest()
        self.email = email
        self.role = role
        self.active = active

    def deactivate(self):
        self.active = False

    def activate(self):
        self.active = True

    @staticmethod
    def find_user(users, username):
        for user in users:
            if user['username'] == username:
                return user
        return None

    @staticmethod
    def hash_password(password):
        return sha256(password.encode()).hexdigest()
############### class haye admin taghriban moshabehe main 

class Admin(User):
    def __init__(self, username, password, email=''):
        super().__init__(username, password, email, 'admin')

    def create_admin(self):
        admins = FileManager.load_data(ADMIN_FILE)

        if User.find_user(admins, self.username):
            print("Admin already exists!")
            Logger.log_message(f"Attempt to create an existing admin: {self.username}")
            return

        admin_data = {
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'role': self.role,
            'active': self.active
        }
        admins.append(admin_data)
        FileManager.save_data(admins, ADMIN_FILE)
        Logger.log_message(f"Admin created with username: {self.username}")
        print(f"Admin created with username: {self.username}")
############### deactive and active baraye user 

    @staticmethod
    def deactivate_user(username):
        users = FileManager.load_data(USERS_FILE)
        user = User.find_user(users, username)
        if user:
            user['active'] = False
            FileManager.save_data(users, USERS_FILE)
            Logger.log_message(f"User {username} deactivated by admin")
            print(f"User {username} deactivated successfully!")
        else:
            print("User not found!")

    @staticmethod
    def activate_user(username):
        users = FileManager.load_data(USERS_FILE)
        user = User.find_user(users, username)
        if user:
            user['active'] = True
            FileManager.save_data(users, USERS_FILE)
            Logger.log_message(f"User {username} activated by admin")
            print(f"User {username} activated successfully!")
        else:
            print("User not found!")

            ############### purge data  bara admin 

    @staticmethod
    def purge_data():
        confirm = input("Are you sure you want to delete all data? (yes/no): ")
        if confirm.lower() == 'yes':
            for file in [ADMIN_FILE, USERS_FILE, PROJECTS_FILE, LOG_FILE]:
                if os.path.exists(file):
                    os.remove(file)
            print("All data purged!")
        else:
            print("Purge cancelled.")
############### main  

def main():
    parser = argparse.ArgumentParser(description="Manage system admin and data.")
    subparsers = parser.add_subparsers(dest='command')

    create_admin_parser = subparsers.add_parser('create-admin')
    create_admin_parser.add_argument('--username', required=True, help='Admin username')
    create_admin_parser.add_argument('--password', required=True, help='Admin password')

    deactivate_user_parser = subparsers.add_parser('deactivate-user')
    deactivate_user_parser.add_argument('--username', required=True, help='Username to deactivate')

    activate_user_parser = subparsers.add_parser('activate-user')
    activate_user_parser.add_argument('--username', required=True, help='Username to activate')

    purge_data_parser = subparsers.add_parser('purge-data')

    args = parser.parse_args()
    if args.command == 'create-admin':
        admin = Admin(args.username, args.password)
        admin.create_admin()
    elif args.command == 'deactivate-user':
        Admin.deactivate_user(args.username)
    elif args.command == 'activate-user':
        Admin.activate_user(args.username)
    elif args.command == 'purge-data':
        Admin.purge_data()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
