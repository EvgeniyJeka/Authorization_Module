from flask import request, Flask
import logging

from authorization import Authorization
from constants import *

logging.basicConfig(level=logging.INFO)

# Specifications for Auth. module

# Assuming - DB that contains user's ID, email (user name) and password (hashed)
#
# Flask API contains 2 methods: sign_in and perform_action.
#
# The Gateway module (gateway.py) contains the API entry points
# The Authorization module (authorization.py) contains the core logic.
# SQL Manager module (sql_manager.py) contains the methods used for interaction with MySQL DB
#
# Sign in method - verifies provided user credentials, generates JWT basing on random KEY
# Generated JWT , the KEY and the exact time are saved in SQL DB.
#
# Sign out method - modifies the JWT creation time in SQL DB, sets it to 0 (the token expires)
#
# Perform Action methods - receives JWT and action type (ID).
# Verifies the JWT exists in SQL DB.
# Extracts the credentials from JWT, verifies them against DB (key is taken from the DB as well).
# Verifies the token hasn't expired (current time - JWT generation time < JWT Life Time)
# Providing given user has the permission to perform the requested action type a confirmation is returned
# to the calling method ( {"authorization":"confirmed"}).
# Relevant error will be returned otherwise.
#
# Errors list:
# "The user lacks the permission to perform this action" (generic, can be updated)
# "Wrong credentials" (JWT not in DB)
# "Expired Token" (The token has expired)

# Consider to add API method that would return JWT TTL


app = Flask(__name__)
authorization = Authorization(CONFIG_FILE_PATH)


@app.route(REST_API_SIGN_IN, methods=['POST'])
def sign_in():
    try:
        data = request.get_json()
        username, password = data['username'], data['password']
        logging.info(f"Authorization: Sign In request received, username {username} password {password}")

        produced_token = authorization.generate_token(username, password)

        if 'JWT' in produced_token.keys():
            return {"Token": produced_token['JWT']}

        elif 'error' in produced_token.keys():
            return {"Error": produced_token['error']}

    except (KeyError, TypeError) as e:
        logging.error(f"Sign In method called - credentials weren't provided: {e}")
        return {"Error": "Authorization: please provide valid credentials in request"}


@app.route(REST_API_SIGN_OUT, methods=['POST'])
def sign_out():
    try:
        data = request.get_json()
        token = data['token']
        logging.info(f"Authorization: Sign Out request received, JWT in request: {token}")

        sign_out_performed = authorization.sign_out(token)

        if 'error' not in sign_out_performed.keys():
            return {"Authorization": "Sign out confirmed", "Token": token}

        return sign_out_performed

    except (KeyError, TypeError) as e:
        logging.error(f"Sign Out method called - invalid request: {e}")
        return {"Error": "Authorization: please provide valid credentials in request"}


@app.route(REST_API_PERFORM_ACTION, methods=['POST'])
def perform_action():
    try:
        data = request.get_json()
        auth_token, action_id = data['auth_token'], data['action_id']
        logging.info(f"Authorization: User {auth_token} tries to perform action {action_id}, "
                     f"addressing the Authorization module")

        if auth_token == "":
            return {"error": f"Wrong credentials"}

        permissions_verification_result = authorization.verify_token(auth_token, action_id)

        if 'Confirmed' in permissions_verification_result.keys():
            return {"result": f"Action {action_id} was successfully performed"}

        elif 'error' in permissions_verification_result.keys():
            return {"Error": permissions_verification_result['error']}

    except (KeyError, TypeError) as e:
        logging.error(f"Perform Action method called - missing: {e}")
        return {"Error": "Authorization: please provide valid action ID and JWT in request"}


@app.route(REST_API_TOKEN_TTL, methods=['GET'])
def get_token_ttl(jwt):
    logging.info(f"Authorization: request for {jwt} token TTL received")

    token_ttl_checked = authorization.jwt_token_ttl_remains(jwt)

    if isinstance(token_ttl_checked, dict) and 'error' in token_ttl_checked.keys():
        return {"Error": token_ttl_checked['error']}

    return {f"JWT": f"{jwt}", "TTL": token_ttl_checked}


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
