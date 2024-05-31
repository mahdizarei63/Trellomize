import unittest
import os
import json
from hashlib import sha256
from manager1 import FileManager, Logger, User, Admin, ADMIN_FILE, USERS_FILE, PROJECTS_FILE, LOG_FILE

class TestFileManager(unittest.TestCase):

    def setUp(self):
        self.test_admin_file = 'test_admin.json'
        self.test_users_file = 'test_users.json'
        self.test_projects_file = 'test_projects.json'
        self.test_log_file = 'test_log.txt'

        for file in [self.test_admin_file, self.test_users_file, self.test_projects_file, self.test_log_file]:
            with open(file, 'w') as f:
                json.dump([], f)

    def tearDown(self):
        for file in [self.test_admin_file, self.test_users_file, self.test_projects_file, self.test_log_file]:
            if os.path.exists(file):
                os.remove(file)

    def test_1_load_data_empty_file(self):
        data = FileManager.load_data(self.test_admin_file)
        self.assertEqual(data, [], "Test 1: Failed to load data from an empty file")

    def test_2_save_data(self):
        data = [{'key': 'value'}]
        FileManager.save_data(data, self.test_admin_file)
        loaded_data = FileManager.load_data(self.test_admin_file)
        self.assertEqual(loaded_data, data, "Test 2: Failed to save and load data correctly")

class TestLogger(unittest.TestCase):

    def setUp(self):
        self.test_log_file = 'test_log.txt'
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def tearDown(self):
        if os.path.exists(self.test_log_file):
            os.remove(self.test_log_file)

    def test_3_log_message(self):
        message = "Test log message"
        Logger.log_message(message)
        with open(self.test_log_file, 'r') as f:
            logs = f.read().strip()
        self.assertEqual(logs, message, "Test 3: Failed to log message correctly")

class TestUser(unittest.TestCase):

    def setUp(self):
        self.username = "testuser"
        self.password = "testpass"
        self.email = "test@example.com"
        self.role = "user"
        self.user = User(self.username, self.password, self.email, self.role)

    def test_4_password_hashing(self):
        hashed_password = sha256(self.password.encode()).hexdigest()
        self.assertEqual(self.user.password, hashed_password, "Test 4: Password hashing failed")

    def test_5_find_user(self):
        users = [{'username': 'testuser'}, {'username': 'anotheruser'}]
        user = User.find_user(users, 'testuser')
        self.assertIsNotNone(user, "Test 5: Failed to find existing user")
        user = User.find_user(users, 'nonexistent')
        self.assertIsNone(user, "Test 5: Found non-existent user")

class TestAdmin(unittest.TestCase):

    def setUp(self):
        self.username = "admin"
        self.password = "adminpass"
        self.email = "admin@example.com"
        self.admin = Admin(self.username, self.password, self.email)

        self.test_admin_file = 'test_admin.json'
        if os.path.exists(self.test_admin_file):
            os.remove(self.test_admin_file)
        with open(self.test_admin_file, 'w') as f:
            json.dump([], f)

        self.test_users_file = 'test_users.json'
        if os.path.exists(self.test_users_file):
            os.remove(self.test_users_file)
        with open(self.test_users_file, 'w') as f:
            json.dump([], f)

    def tearDown(self):
        if os.path.exists(self.test_admin_file):
            os.remove(self.test_admin_file)
        if os.path.exists(self.test_users_file):
            os.remove(self.test_users_file)

    def test_6_create_admin(self):
        self.admin.create_admin()
        admins = FileManager.load_data(self.test_admin_file)
        self.assertEqual(len(admins), 1, "Test 6: Failed to create admin")
        self.assertEqual(admins[0]['username'], self.username, "Test 7: Admin username does not match")

    def test_8_deactivate_user(self):
        users = [{'username': 'testuser', 'active': True}]
        FileManager.save_data(users, self.test_users_file)
        Admin.deactivate_user('testuser')
        updated_users = FileManager.load_data(self.test_users_file)
        self.assertFalse(updated_users[0]['active'], "Test 8: Failed to deactivate user")

    def test_9_activate_user(self):
        users = [{'username': 'testuser', 'active': False}]
        FileManager.save_data(users, self.test_users_file)
        Admin.activate_user('testuser')
        updated_users = FileManager.load_data(self.test_users_file)
        self.assertTrue(updated_users[0]['active'], "Test 9: Failed to activate user")

    def test_10_purge_data(self):
        for file in [self.test_admin_file, self.test_users_file, self.test_projects_file, self.test_log_file]:
            with open(file, 'w') as f:
                json.dump([{"sample": "data"}], f)
        
        # Mock the input function to simulate user confirmation for data purge
        input_mock = unittest.mock.patch('builtins.input', return_value='yes')
        with input_mock:
            Admin.purge_data()

        for file in [self.test_admin_file, self.test_users_file, self.test_projects_file, self.test_log_file]:
            self.assertFalse(os.path.exists(file), f"Test 10: Failed to purge data from {file}")

if __name__ == '__main__':
    unittest.main()
