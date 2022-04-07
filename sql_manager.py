import logging

import sqlalchemy
from sqlalchemy import exc
import configparser
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import sqlalchemy as db

from constants import USERS_TABLE_NAME
from set_initial_data import SetInitialData


class SqlManager(object):

    def __init__(self, config_file_path):

        # Reading DB name, host and credentials from config
        config = configparser.ConfigParser()
        config.read(config_file_path)
        hst = config.get("SQL_DB", "host")
        usr = config.get("SQL_DB", "user")
        pwd = config.get("SQL_DB", "password")
        db_name = config.get("SQL_DB", "db_name")

        try:
            self.cursor, self.engine = self.connect_me(hst, usr, pwd, db_name)
            SetInitialData.set_initial_data(self.cursor, self.engine)

        except TypeError:
            logging.critical("SQL DB - Failed to connect, please verify SQL DB container is running")

    # Connect to DB
    def connect_me(self, hst, usr, pwd, db_name):
        """
        This method is used to establish a connection to MySQL DB.
        Credentials , host and DB name are taken from "config.ini" file.

        :param hst: host
        :param usr: user
        :param pwd: password
        :param db_name: DB name
        :return: SqlAlchemy connection (cursor)
        """

        try:

            url = f'mysql+pymysql://{usr}:{pwd}@{hst}:3306/{db_name}'

            # Create an engine object.
            engine = create_engine(url, echo=False)

            # Create database if it does not exist.
            if not database_exists(engine.url):
                create_database(engine.url)
                cursor = engine.connect()
                return cursor, engine
            else:
                # Connect the database if exists.
                cursor = engine.connect()
                return cursor, engine

        # Wrong Credentials error
        except sqlalchemy.exc.OperationalError as e:
            logging.critical("SQL DB -  Can't connect, verify credentials and host, verify the server is available")
            logging.critical(e)

        # General error
        except Exception as e:
            logging.critical("SQL DB - Failed to connect, reason is unclear")
            logging.critical(e)

    def get_users(self)-> set:
        result = set()

        metadata = db.MetaData()
        table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

        query = db.select([table_])
        ResultProxy = self.cursor.execute(query)
        fetched_data = ResultProxy.fetchall()

        for row in fetched_data:
            result.add(row[1])

        return result

    def get_all_tokens(self)->set:
        result = set()

        metadata = db.MetaData()
        table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

        query = db.select([table_])
        ResultProxy = self.cursor.execute(query)
        fetched_data = ResultProxy.fetchall()

        for row in fetched_data:
            result.add(row[3])

        return result

    def get_token_creation_time(self, jwt):
        metadata = db.MetaData()
        table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

        query = db.select([table_]).where(table_.columns.jwt_token == jwt)
        ResultProxy = self.cursor.execute(query)
        fetched_data = ResultProxy.fetchall()
        if fetched_data:
            return fetched_data[0][5]

        return -1

    def save_jwt_key_time(self, username, encoded_jwt, key, token_creation_time):

        try:
            metadata = db.MetaData()
            table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

            query = db.update(table_).\
                values(jwt_token=encoded_jwt, key=key, token_creation_time=token_creation_time)\
                .where(table_.columns.username == username)

            self.cursor.execute(query)
            return True

        except Exception as e:
            logging.critical(f"Authorization: Failed to insert the JWT token to SQL DB: {e}")
            return False

    def terminate_token(self, token):
        try:
            metadata = db.MetaData()
            table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

            query = db.update(table_).\
                values(token_creation_time=0)\
                .where(table_.columns.jwt_token == token)

            self.cursor.execute(query)
            return {"Token Termination": "Confirmed"}

        except Exception as e:
            logging.critical(f"Authorization: Failed to insert the JWT token to SQL DB: {e}")
            return {"error": "Token Termination failed"}


    def get_password_by_username(self, username):
        metadata = db.MetaData()
        table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

        query = db.select([table_]).where(table_.columns.username == username)
        ResultProxy = self.cursor.execute(query)
        fetched_data = ResultProxy.fetchall()
        return fetched_data[0][2]

    def get_data_by_token(self, token):
        metadata = db.MetaData()
        table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

        query = db.select([table_]).where(table_.columns.jwt_token == token)
        ResultProxy = self.cursor.execute(query)
        fetched_data = ResultProxy.fetchall()

        return fetched_data[0][4], float(fetched_data[0][5])

    def get_allowed_actions_by_token(self, token):
        metadata = db.MetaData()
        table_ = db.Table(USERS_TABLE_NAME, metadata, autoload=True, autoload_with=self.engine)

        query = db.select([table_]).where(table_.columns.jwt_token == token)
        ResultProxy = self.cursor.execute(query)
        fetched_data = ResultProxy.fetchall()
        return [int(x) for x in fetched_data[0][6].split(" ")]

# DB TABLE should contain the following rows: user ID, username, password (hashed),
# JWT generation key, JWT generation time

if __name__ == '__main__':
    manager = SqlManager("./config.ini")
    a = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiTWFyeSBQb3BwaW5zIiwicGFzc3dvcmQiOiJKb3VybmV5In0." \
        "hfrAiOrzNyFzgyawCnxYRKPHSByInZ2TqIZfDNblgdA"
    print(manager.get_token_creation_time(a))
