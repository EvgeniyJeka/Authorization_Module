# Authotization_Module
An autonomous authorization module wrapped with Flask based API.  Generated JWT tokens used to identify addressing customers and check permissions.  Uses MySQL to store data.

Assuming - DB that contains user's ID, email (user name) and password (hashed)

Flask API contains 2 methods: sign_in and perform_action.

The Gateway module (gateway.py) contains the API entry points
The Authorization module (authorization.py) contains the core logic.
SQL Manager module (sql_manager.py) contains the methods used for interaction with MySQL DB

Sign in method - verifies provided user credentials, generates JWT basing on random KEY
Generated JWT , the KEY and the exact time are saved in SQL DB.

Perform Action methods - receives JWT and action type (ID).
Verifies the JWT exists in SQL DB.
Extracts the credentials from JWT, verifies them against DB (key is taken from the DB as well).
Verifies the token hasn't expired (current time - JWT generation time < JWT Life Time)
Providing given user has the permission to perform the requested action type a confirmation is returned
to the calling method ( {"authorization":"confirmed"}).
Relevant error will be returned otherwise.

Errors list:
"The user lacks the permission to perform this action" (generic, can be updated)
"Wrong credentials" (JWT not in DB)
"Expired Token" (The token has expired)