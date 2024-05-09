from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def get_id(self):
        return str(self.id)

def load_user(user_id):
    try:
        with open('users.txt', 'r') as file:
            users = [line.strip().split(',') for line in file.readlines()]
            print(f"Users data: {users}")  # Add this print statement

        for user in users:
            if user[0] == user_id:
                print(f"Found user with id {user_id}: {user}")  # Add this print statement
                return User(user[0], user[1], user[2])
    except FileNotFoundError:
        print("users.txt file not found.")  # Add this print statement
        pass

    print(f"No user found with id {user_id}")  # Add this print statement
    return None

def get_user_by_username(username):
    try:
        with open('users.txt', 'r') as file:
            users = [line.strip().split(',') for line in file.readlines()]
            print(f"Users data: {users}")  # Add this print statement

        for user in users:
            if user[1] == username:
                print(f"Found user with username {username}: {user}")  # Add this print statement
                return User(user[0], user[1], user[2])
    except FileNotFoundError:
        print("users.txt file not found.")  # Add this print statement
        pass

    print(f"No user found with username {username}")  # Add this print statement
    return None