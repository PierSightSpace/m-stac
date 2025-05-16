# Imports
# Standard Library Imports
import os

# Third-Party Imports
import duckdb

# Local Imports
from dotenv import load_dotenv

load_dotenv()

def duckdb_connection():
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
    S3_SECRET_KEY = os.getenv('S3_SECRET_KEY')

    conn = duckdb.connect(database=':memory:', read_only=False)
    conn.execute("""
        INSTALL httpfs;
        LOAD httpfs;
        INSTALL spatial;
        LOAD spatial;
        SET s3_region='ap-south-1';
        SET s3_access_key_id={access_key};
        SET s3_secret_access_key={secret_key};
    """.format(access_key=S3_ACCESS_KEY, secret_key=S3_SECRET_KEY))
    return conn