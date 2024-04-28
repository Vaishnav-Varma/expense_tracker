import json
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    try:
        with open('users.json', 'r') as file:
            users = json.load(file)['users']
    except (FileNotFoundError, json.JSONDecodeError):
        users = []
    return users

def save_users(users):
    data = {'users': users}
    with open('users.json', 'w') as file:
        json.dump(data, file, indent=2)

def register_user(username, password, email):
    users = load_users()
    for user in users:
        if user['username'] == username:
            print(f"Username '{username}' already exists.")
            return False

    hashed_password = hash_password(password)
    new_user = {'username': username, 'password': hashed_password, 'email': email}
    users.append(new_user)
    save_users(users)
    return True

def authenticate_user(username, password):
    users = load_users()
    for user in users:
        if user['username'] == username:
            hashed_password = user['password']
            entered_password = hash_password(password)
            print(f"Entered password hash: {entered_password}")
            print(f"Stored password hash: {hashed_password}")
            if hashed_password == entered_password:
                return True
    print(f"User '{username}' not found or incorrect password.")
    return False