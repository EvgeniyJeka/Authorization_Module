import jwt
import time
import logging
from sql_manager import SqlManager

sql_manager = SqlManager()

# 1648743766.707471

token_ttl = 10000000


class Authorization(object):

    def generate_token(self, username: str, password: str):

        key = "tempKey"  # The key will be generated on random basis and saved to DB

        # Check if given username exists in SQL DB, if it doesn't - return an error
        if not sql_manager.get_users().__contains__(username):
            return {"error": f"Wrong credentials"}

        password_hash = sql_manager.get_password_by_username(username)

        if hash(password) == password_hash:
            encoded_jwt = jwt.encode({"user": username, "password": password}, key, algorithm="HS256")
            token_creation_time = time.time()

            # Save the created JWT, KEY and token creation time to SQL
            if not sql_manager.save_jwt_key_time(encoded_jwt, key, token_creation_time):
                return {"error": "Token creation failed due to system issues"}

            return {"JWT": encoded_jwt}

        else:
            return {"error": "Wrong credentials"}

    def verify_token(self, token: str, action_id: int):

        key, token_creation_time = sql_manager.get_data_by_token(token)

        try:
            parsed_token = jwt.decode(token, key, algorithms="HS256")

        except jwt.exceptions.InvalidSignatureError:
            logging.error(f"Authorization: Invalid JWT received {token}")
            return {"error": "Invalid token provided"}

        username, password = parsed_token['user'], parsed_token['password']

        logging.info(f"Authorization: parsed JWT {token}, username: {username}, password: {password}, "
                     f"requested action type: {action_id}")

        # Verify against SQL DB if such user exists.
        if not sql_manager.get_users().__contains__(username):
            return {"error": f"Wrong credentials"}

        # Verify against SQL if the password is correct (the password belongs to that user)
        hashed_password = sql_manager.get_password_by_username(username)
        if not hashed_password == hash(password):
            return {"error": "Wrong credentials"}

        # Verify against SQL if the token is valid (not expired)
        #                                   - fetch the creation time and subtract it from the current time
        if not time.time() - token_creation_time < token_ttl:
            return {"error": "Token has expired"}

        # Bring the action types of all actions that current user is allowed to perform from SQL.
        # If the action types list contains the provided action type - return a confirmation.
        # Otherwise - return an error message.
        if not action_id in sql_manager.get_allowed_actions_by_user(username):
            return {"error": "Forbidden action"}

        return {"Confirmed": "Permissions verified"}




