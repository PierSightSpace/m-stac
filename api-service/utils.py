# Imports
# Standard Library Imports
from datetime import datetime


def convert_to_datetime(time_in_str):
    """
    Converts a string in ISO 8601 format to a datetime object.

    Parameters:
        time_in_str: String representing the date and time in the format 'YYYY-MM-DDTHH:MM:SSZ'.

    Returns:
        A datetime object if conversion is successful, otherwise None.
    """
    if time_in_str:
        try:
            return datetime.strptime(time_in_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            print(str(e))
    return None