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
    '''Hashes the password before saving into database'''
    return pwd_context.hash(password)


def verify_password(password_to_be_checked, hashed_correct_password):
    '''Verfies the password for authentication'''
    return pwd_context.verify(password_to_be_checked, hashed_correct_password)


def _generate_secret_key(length=32):
    '''Generates the secret key for the csrf protection'''
    alphabets = string.ascii_letters + string.digits
    secret_key = ''.join(secrets.choice(alphabets) for _ in range(length))
    return secret_key      


def _rotate_secret_key():
    '''Rotates the CSRF secrte key by generating new one'''
    global SECRET_KEY_CSRF
    with lock:
        SECRET_KEY_CSRF = _generate_secret_key()

    
def schedule_key_rotation(rotation_interval_in_seconds=24*60*60):
    '''Runs an infinite loop to rotate the CSRF secret key at a fixed interval'''
    while not stop_rotation.is_set():
        _rotate_secret_key()
        time.sleep(rotation_interval_in_seconds)


def get_secret_key_csrf():
    '''Retrieves the current CSRF secret key in a thread-safe manner'''
    with lock:
        return SECRET_KEY_CSRF