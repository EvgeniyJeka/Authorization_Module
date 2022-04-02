import logging

import sqlalchemy
from sqlalchemy import exc
import configparser
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import sqlalchemy as db
from sqlalchemy import exc


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
            self.set_initial_data()

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
            engine = create_engine(url, echo=True)

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


    def set_initial_data(self):

        table_name = "users"
        column_names = ["id", "username", "password", "jwt_token", "key", "token_creation_time", "allowed_actions"]
        table_data = [['101', 'Greg Bradly', hash("Pigs"), "", "", "", "1 2"],
                      ['202', 'Joe Anderson', hash("Truth"), "", "", "1 3"],
                      ['103', 'Mary Poppins', hash("Journey"), "", "", "1 2"]]


        tables = self.engine.table_names()

        # Creating new table to store the file content if not exist.
        if table_name not in tables:
            logging.info(f"{table_name} table is missing! Creating the {table_name} table")
            metadata = db.MetaData()

            # Creating table - column names are provided in a tuple
            columns_list = [db.Column(x, db.String(255)) for x in column_names]

            # SQL Alchemy table instance is passed to the "fill_table" method
            table_emp = db.Table(table_name, metadata, *columns_list, extend_existing=True)
            metadata.create_all(self.engine)

            self.fill_table(table_name, table_data, table_emp, column_names)

    def fill_table(self, file_name, table_data, table_emp, column_names):
        """
         This method can be used to fill a table with data
        :param file_name:  Table name, str
        :param table_data: a list - each element will become a record in the table
        :param table_emp: Sql alchemy instance that represents the table
        :param column_names: Table columns list
        :return:
        """

        logging.info(f"Executer: Filling the table '{file_name}' with data")

        added_values = []

        for row in table_data:
            element = {}
            for column_number in range(0, len(column_names)):
                element[column_names[column_number]] = row[column_number]

            added_values.append(element)

        query = table_emp.insert().values([*added_values])
        self.cursor.execute(query)

        return {"response": "DB was successfully updated"}

    def get_users(self)-> set:
        return {"JustMe", "JustYou"}

    def get_all_tokens(self)->set:
        return {"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiSnVzdE1lIiwicGFzc3dvcmQiOiJNeVBh"
                "c3N3b3JkIn0.Rq500BSVurkKXmwjsu-_dskPeS7VezfpF-C0qovipv8"}

    def save_jwt_key_time(self, encoded_jwt, key, token_creation_time):
        return True

    def get_password_by_username(self, username):
        return hash("MyPassword")

    def get_data_by_token(self, token):
        return "tempKey", 1648743766.707471

    def get_allowed_actions_by_token(self, token):
        return [1, 2, 3]

# DB TABLE should contain the following rows: user ID, username, password (hashed),
# JWT generation key, JWT generation time

if __name__ == '__main__':
    manager = SqlManager("./config.ini")
