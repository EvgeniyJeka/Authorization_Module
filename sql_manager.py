import logging

import sqlalchemy
from sqlalchemy import exc
import configparser
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import sqlalchemy as db

import objects_mapped_
from sqlalchemy.orm import sessionmaker


from constants import USERS_TABLE_NAME, ROLES_TABLE_NAME, ACTIONS_TABLE_NAME, ACTIONS_BY_ROLES_TABLE_NAME
from tools import Tools


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
            self.cursor = self.connect_me(hst, usr, pwd, db_name)

            logging.info(f"SQL Manager: Connected to DB {db_name}")

        except TypeError as e:
            logging.critical(f"SQL DB - Failed to connect, please verify SQL DB container is running - {e}")
            raise e

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
            self.engine = engine

            # Create database if it does not exist.
            if not database_exists(engine.url):
                create_database(engine.url)
                cursor = engine.connect()

                # Initiating a session
                Session = sessionmaker(bind=self.engine)
                self.session = Session()
                self.set_initial_data()

                return cursor
            else:
                # Connect the database if exists.
                cursor = engine.connect()
                return cursor

        # Wrong Credentials error
        except sqlalchemy.exc.OperationalError as e:
            logging.critical("SQL DB -  Can't connect, verify credentials and host, verify the server is available")
            logging.critical(e)

        # General error
        except Exception as e:
            logging.critical(f"SQL DB - Failed to connect, reason is unclear - {e}")
            logging.critical(e)

    def set_initial_data(self):

        tables = self.engine.table_names()

        # Creating the 'users' table if it doesn't exist.
        if USERS_TABLE_NAME not in tables:
            logging.info(f"{USERS_TABLE_NAME} table is missing! Creating the {USERS_TABLE_NAME} table")
            objects_mapped_.Base.metadata.create_all(self.engine)

            # Inserting the default test users
            default_users = [objects_mapped_.UsersMapped(id='101',
                                                         username='Greg Bradly',
                                                         password=Tools.hash_string("Pigs"),
                                                         jwt_token="",
                                                         key="",
                                                         token_creation_time="",
                                                         allowed_actions="1 2"),
                             objects_mapped_.UsersMapped(id='202',
                                                         username='Joe Anderson',
                                                         password=Tools.hash_string("Truth"),
                                                         jwt_token="",
                                                         key="",
                                                         token_creation_time="",
                                                         allowed_actions="1 3"),
                             objects_mapped_.UsersMapped(id='304',
                                                         username='Andrew Levi',
                                                         password=Tools.hash_string("Pass"),
                                                         jwt_token="",
                                                         key="",
                                                         token_creation_time="",
                                                         allowed_actions="1 2"),
                             objects_mapped_.UsersMapped(id='103',
                                                         username='Mary Poppins',
                                                         password=Tools.hash_string("Journey"),
                                                         jwt_token="",
                                                         key="",
                                                         token_creation_time="",
                                                         allowed_actions="1 3"),
                             ]

            self.session.add_all(default_users)
            self.session.commit()

        if ROLES_TABLE_NAME not in tables:
            logging.info(f"{ROLES_TABLE_NAME} table is missing! Creating the {ROLES_TABLE_NAME} table")

            default_roles = [objects_mapped_.RolesMapped(role_id=1, role="Borrower"),
                             objects_mapped_.RolesMapped(role_id=2, role="Lender"),
                             objects_mapped_.RolesMapped(role_id=3, role="Admin")]

            self.session.add_all(default_roles)
            self.session.commit()

        if ACTIONS_TABLE_NAME not in tables:
            logging.info(f"{ACTIONS_TABLE_NAME} table is missing! Creating the {ACTIONS_TABLE_NAME} table")

            default_actions = [objects_mapped_.ActionsMapped(action_id=1, action="place bid"),
                               objects_mapped_.ActionsMapped(action_id=2, action="place offer"),
                               objects_mapped_.ActionsMapped(action_id=3, action="cancel bid"),
                               objects_mapped_.ActionsMapped(action_id=4, action="cancel offer")]

            self.session.add_all(default_actions)
            self.session.commit()

        if ACTIONS_BY_ROLES_TABLE_NAME not in tables:
            logging.info(f"{ACTIONS_BY_ROLES_TABLE_NAME} table is missing! Creating the {ACTIONS_BY_ROLES_TABLE_NAME} table")

            actions_mapping = [objects_mapped_.ActionsToRolesMapped(role_id=1, allowed_actions_id='2 4'),
                               objects_mapped_.ActionsToRolesMapped(role_id=2, allowed_actions_id='1 3'),
                               objects_mapped_.ActionsToRolesMapped(role_id=3, allowed_actions_id='1 2 3 4')]

            self.session.add_all(actions_mapping)
            self.session.commit()

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

# if __name__ == '__main__':
#     manager = SqlManager("./config.ini")
#     # a = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiTWFyeSBQb3BwaW5zIiwicGFzc3dvcmQiOiJKb3VybmV5In0." \
#     #     "hfrAiOrzNyFzgyawCnxYRKPHSByInZ2TqIZfDNblgdA"
#     # print(manager.get_token_creation_time(a))
