# Imports
# Standard Library Imports
import time
import string

# Third-Party Imports
from passlib.context import CryptContext
import secrets
import threading



# Initializing password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


SECRET_KEY_CSRF = None


# Event and Lock for thread synchronization
stop_rotation = threading.Event();
lock = threading.Lock()


############################################################################################################
# Utility Functions
############################################################################################################
def hash_pass(password):
    """
    Hashes a password before saving it to the database.

    Parameters:
        password: The plain-text password to be hashed.

    Returns:
        The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(password_to_be_checked, hashed_correct_password):
    """
    Verifies a password for authentication.

    Parameters:
        password_to_be_checked: The plain-text password to check.
        hashed_correct_password: The correct hashed password to verify against.

    Returns:
        True if the password matches, otherwise False.
    """
    return pwd_context.verify(password_to_be_checked, hashed_correct_password)


def _generate_secret_key(length=32):
    """
    Generates a secret key for CSRF protection.

    Parameters:
        length: The length of the secret key to generate.

    Returns:
        The generated secret key as a string.
    """
    alphabets = string.ascii_letters + string.digits
    secret_key = ''.join(secrets.choice(alphabets) for _ in range(length))
    return secret_key      


def _rotate_secret_key():
    """
    Rotates the CSRF secret key by generating a new one.

    This function is thread-safe and updates the global secret key.
    """
    global SECRET_KEY_CSRF
    with lock:
        SECRET_KEY_CSRF = _generate_secret_key()

    
def schedule_key_rotation(rotation_interval_in_seconds=24*60*60):
    """
    Runs an infinite loop to rotate the CSRF secret key at a fixed interval.

    Parameters:
        rotation_interval_in_seconds: The interval (in seconds) between key rotations.
    """
    while not stop_rotation.is_set():
        _rotate_secret_key()
        time.sleep(rotation_interval_in_seconds)


def get_secret_key_csrf():
    """
    Retrieves the current CSRF secret key in a thread-safe manner.

    Returns:
        The current CSRF secret key.
    """
    with lock:
        return SECRET_KEY_CSRF