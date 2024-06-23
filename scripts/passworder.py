import os
import socket
import uuid
import hashlib
from cryptography.fernet import Fernet
import base64

credentials_file_path = ''

def generate_machine_user_specific_key():
    # Get machine and user-specific information
    hostname = socket.gethostname()
    username = os.getlogin()
    mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
    
    # Combine these details to form a unique identifier
    unique_string = hostname + "!#$%&'()*+,-./:;<=>>" + username + "?@[\\]^_`{|}~" +  mac + 'g9G(i32nOi3#&*)'

    # Create a hash of this unique string
    hash_object = hashlib.sha256(unique_string.encode())
    key = hash_object.digest()[:32]  # Fernet keys must be 32 bytes
    print(key)
    return Fernet(base64.urlsafe_b64encode(key))

cipher_suite = generate_machine_user_specific_key()

def save_encrypted_password(username, password):
    encrypted_password = cipher_suite.encrypt(password.encode())
    with open('credentials.txt', 'wb') as file:
        file.write(username.encode() + b'\n')
        file.write(encrypted_password)
    print("Credentials saved successfully.")

def load_credentials():
    with open('credentials.txt', 'rb') as file:
        username = file.readline().strip().decode()
        encrypted_password = file.readline().strip()
        password = cipher_suite.decrypt(encrypted_password).decode()
    return username, password

def get_credentials():
    import tkinter as tk
    from tkinter import messagebox
    
    def on_submit():
        username = username_entry.get()
        password = password_entry.get()
        save_encrypted_password(username, password)
        root.destroy()

    root = tk.Tk()
    root.title("Enter Credentials")

    tk.Label(root, text="Username:").grid(row=0)
    tk.Label(root, text="Password:").grid(row=1)

    username_entry = tk.Entry(root)
    password_entry = tk.Entry(root, show='*')

    username_entry.grid(row=0, column=1)
    password_entry.grid(row=1, column=1)

    submit_button = tk.Button(root, text="Submit", command=on_submit)
    submit_button.grid(row=2, column=1)

    root.mainloop()

# Example usage
if __name__ == "__main__":
    get_credentials()
    username, password = load_credentials()
    print("Loaded credentials:")
    print(f"Username: {username}")
    print(f"Password: {password}")  # For demonstration purposes; avoid printing passwords in real applications
