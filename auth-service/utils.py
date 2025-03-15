from passlib.context import CryptContext
import string
import secrets
import time


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY_AUTH = None
SECRET_KEY_CSRF = None


def hash_pass(password):
    return pwd_context.hash(password)


def verify_password(password_to_be_checked, hashed_correct_password):
    return pwd_context.verify(password_to_be_checked, hashed_correct_password)


def _generate_secret_key(length=32):
    alphabets = string.ascii_letters + string.digits
    secret_key = ''.join(secrets.choice(alphabets) for _ in range(length))
    return secret_key      


def _rotate_secret_key():
    global SECRET_KEY_AUTH, SECRET_KEY_CSRF
    SECRET_KEY_AUTH = _generate_secret_key()
    SECRET_KEY_CSRF = _generate_secret_key()

    
def schedule_key_rotation(rotation_interval_in_seconds=60):
    while True:
        _rotate_secret_key()
        time.sleep(rotation_interval_in_seconds)
        

def get_secret_key_auth():
    return SECRET_KEY_AUTH


def get_secret_key_csrf() -> str:
    return SECRET_KEY_CSRF