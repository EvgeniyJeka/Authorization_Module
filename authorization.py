import jwt
import time


class Authorization(object):

    def generate_token(self, username, password):

        # MOCK DATA - TEMPORARY.
        user = "JustMe"
        password_hash = hash("MyPassword")

        # Check if given username exists in SQL DB, if it doesn't - return an error

        if hash(password) == password_hash:
            key = "tempKey"  # The key will be generated on random basis
            encoded_jwt = jwt.encode({"user": username, "password": password}, key, algorithm="HS256")
            token_creation_time = time.time()

            # Save the created JWT, KEY and token creation time to SQL

            return {"JWT": encoded_jwt}

        else:
            return {"error": "Wrong credentials"}




