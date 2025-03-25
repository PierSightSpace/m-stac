# Imports
# Standard Library Imports
from datetime import datetime


def convert_to_datetime(time_in_str):
    if time_in_str:
        try:
            return datetime.strptime(time_in_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError as e:
            print(str(e))
    return None