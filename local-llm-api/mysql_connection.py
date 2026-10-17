import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


class MySQLConnection:
    @staticmethod
    def get_connection(connection_timeout: int = 5):
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST"),
            port=int(os.getenv("MYSQL_PORT")),
            user=os.getenv("MYSQL_USER"),
            password=os.getenv("MYSQL_PASSWORD"),
            database=os.getenv("MYSQL_DATABASE"),
            connection_timeout=connection_timeout,
        )
