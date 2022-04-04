import jwt
import time
import logging

from constants import *
from sql_manager import SqlManager
import hashlib
import configparser
import random

sql_manager = SqlManager(CONFIG_FILE_PATH)


class Authorization(object):

    def __init__(self, config_file_path):

        # Reading DB name, host and credentials from config
        config = configparser.ConfigParser()
        config.read(config_file_path)
        self.token_ttl = int(config.get("APP_SETTINGS", "token_ttl"))

    def hash_string(self, input_: str):
        plaintext = input_.encode()

        # call the sha256(...) function returns a hash object
        d = hashlib.sha256(plaintext)

        # generate human readable hash of "hello" string
        hash = d.hexdigest()
        return hash

    def sign_out(self, token):
        # Check for provided token in SQL DB
        if not sql_manager.get_all_tokens().__contains__(token):
            return {"error": f"Wrong credentials"}

        return sql_manager.terminate_token(token)

    def key_gen(self):
        return "key" + str(random.randint(1000, 10000))

    def generate_token(self, username: str, password: str):
        """
        This method is used to generate a JWT basing on provided credentials. JWT is generated after creds are verified
        :param username: str
        :param password: str
        :return: JWT on success
        """

        key = self.key_gen()  # The key will be generated on random basis and saved to DB

        # Check if given username exists in SQL DB, if it doesn't - return an error
        if not sql_manager.get_users().__contains__(username):
            return {"error": f"Wrong credentials"}

        password_hash = sql_manager.get_password_by_username(username)

        if self.hash_string(password) == password_hash:
            encoded_jwt = jwt.encode({"user": username, "password": password}, key, algorithm="HS256")
            token_creation_time = time.time()

            # Save the created JWT, KEY and token creation time to SQL
            if not sql_manager.save_jwt_key_time(username, encoded_jwt, key, token_creation_time):
                return {"error": "Token creation failed due to system issues"}

            return {"JWT": encoded_jwt}

        else:
            return {"error": "Wrong credentials"}

    def verify_token(self, token: str, action_id: int):
        """
        This method is used to verify JWT (without decoding it). Also verifies that given user has permissions
        required to perform the requested action
        :param token: str
        :param action_id: int
        :return: dict (confirmation on success)
        """

        # Check for provided token in SQL DB
        if not sql_manager.get_all_tokens().__contains__(token):
            return {"error": f"Wrong credentials"}

        _, token_creation_time = sql_manager.get_data_by_token(token)

        # Verify against SQL if the token is valid (not expired)
        #                                   - fetch the creation time and subtract it from the current time
        if not time.time() - token_creation_time < self.token_ttl:
            logging.error(f"Token TTL: {self.token_ttl}, current age: {time.time() - token_creation_time}")
            return {"error": "Token has expired"}

        # Bring the action types of all actions that current user is allowed to perform from SQL.
        # If the action types list contains the provided action type - return a confirmation.
        # Otherwise - return an error message.
        if action_id not in sql_manager.get_allowed_actions_by_token(token):
            return {"error": "Forbidden action"}

        return {"Confirmed": "Permissions verified"}

    def decode_token(self, token):
        """
        This method can be used to decode a JWT if the former is saved in SQL DB
        :param token: valid JWT
        :return: dict, decoded JWT
        """
        # Check for provided token in SQL DB
        if not sql_manager.get_all_tokens().__contains__(token):
            return {"error": f"Unlisted token"}

        secret_key, _ = sql_manager.get_data_by_token(token)

        try:
            return jwt.decode(token, secret_key, algorithms="HS256")

        except jwt.exceptions.InvalidSignatureError:
            logging.error(f"Authorization: Invalid JWT received {token}")
            return {"error": "Invalid token provided"}



if __name__ == '__main__':
    mod = Authorization("./config.ini")
    cc = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiTWFyeSBQb3BwaW5zIiwicGFzc3dvcmQiOiJKb3VybmV5In0.VgPvaawMbCuoq5hBkFhNfubq-mTm5dkR2FG1lEDDhOg3"
    a = mod.sign_out(cc)
    print(a)








