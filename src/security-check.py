import subprocess


def create_user(username):
    try:
        # Create user with home directory
        subprocess.run(['sudo', 'useradd', '-m', '-s', '/bin/bash', username])
        print(f"User '{username}' created successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error creating user '{username}': {e}")


def delete_user(username):
    try:
        # Delete user and remove home directory
        subprocess.run(['sudo', 'userdel', '-r', username])
        print(f"User '{username}' deleted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error deleting user '{username}': {e}")


if __name__ == "__main__":
    sample_user = "testuser"

    # Create sample user
    create_user(sample_user)

    # Delete sample user
    delete_user(sample_user)
