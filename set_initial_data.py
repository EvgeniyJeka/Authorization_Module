import logging
import sqlalchemy as db
import hashlib


class SetInitialData:

    @staticmethod
    def hash_string(input_: str):
        plaintext = input_.encode()

        # call the sha256(...) function returns a hash object
        d = hashlib.sha256(plaintext)

        # generate human readable hash of "hello" string
        hash = d.hexdigest()
        return hash

    @staticmethod
    def set_initial_data(cursor, engine):

        table_name = "users"
        column_names = ["id", "username", "password", "jwt_token", "key", "token_creation_time", "allowed_actions"]
        table_data = [['101', 'Greg Bradly', SetInitialData.hash_string("Pigs"), "", "", "", "1 2"],
                      ['202', 'Joe Anderson', SetInitialData.hash_string("Truth"), "", "", "", "1 3"],
                      ['103', 'Mary Poppins', SetInitialData.hash_string("Journey"), "", "", "", "1 2"],
                      ['304', 'Andrew Levi', SetInitialData.hash_string("Pass"), "", "", "", "1 3"]]

        tables = engine.table_names()

        # Creating new table to store the file content if not exist.
        if table_name not in tables:
            logging.info(f"{table_name} table is missing! Creating the {table_name} table")
            metadata = db.MetaData()

            # Creating table - column names are provided in a tuple
            columns_list = [db.Column(x, db.String(255)) for x in column_names]

            # SQL Alchemy table instance is passed to the "fill_table" method
            table_emp = db.Table(table_name, metadata, *columns_list, extend_existing=True)
            metadata.create_all(engine)

            logging.info(f"Authorization: Filling the table '{table_name}' with an initial data")

            added_values = []

            for row in table_data:
                element = {}
                for column_number in range(0, len(column_names)):
                    element[column_names[column_number]] = row[column_number]

                added_values.append(element)

            query = table_emp.insert().values([*added_values])
            cursor.execute(query)

            return {"response": "DB was successfully updated"}