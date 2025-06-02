# Imports
# Third-Party Imports
from passlib.context import CryptContext


# Initializing password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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