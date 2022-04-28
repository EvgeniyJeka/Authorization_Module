from flask import request, Flask
import logging

from authorization import Authorization

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

# Move hard-code to constants / config
# Consider to add API method that would return JWT TTL

app = Flask(__name__)

authorization = Authorization("./config.ini")


@app.route('/sign_in', methods=['POST'])
def sign_in():
    try:
        # Headers parsing
        username = request.headers.get('username')
        password = request.headers.get('password')

        if not (username and password):
            logging.warning("Credentials missing in request headers")
            return {"Authorization": "Credentials missing in request headers"}

        logging.info(f"Authorization: Sign In request received, username {username} password {password}")

        produced_token = authorization.generate_token(username, password)

        if 'JWT' in produced_token.keys():
            return {"Token": produced_token['JWT']}

        elif 'error' in produced_token.keys():
            return {"Error": produced_token['error']}

    except (KeyError, TypeError) as e:
        logging.error(f"Sign In method called - credentials weren't provided: {e}")
        return {"Error": "Authorization: please provide valid credentials in request"}


@app.route('/sign_out', methods=['POST'])
def sign_out():
    try:
        # Headers parsing
        token = request.headers.get('jwt')

        if not token:
            logging.warning("Credentials missing in request headers")
            return {"Authorization": "Credentials missing in request headers"}

        logging.info(f"Authorization: Sign Out request received, JWT in request: {token}")

        sign_out_performed = authorization.sign_out(token)

        if 'error' not in sign_out_performed.keys():
            return {"Authorization": "Sign out confirmed", "Token": token}

        return sign_out_performed

    except (KeyError, TypeError) as e:
        logging.error(f"Sign Out method called - invalid request: {e}")
        return {"Error": "Authorization: please provide valid credentials in request"}


@app.route('/perform_action', methods=['POST'])
def perform_action():
    try:
        # Headers parsing
        auth_token = request.headers.get('jwt')
        action_id = request.headers.get('action_id')

        if not (auth_token and action_id):
            logging.warning("JWT or Action ID missing in request headers")
            return {"Authorization": "JWT or Action ID missing in request headers"}

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

@app.route("/place_offer", methods=['POST'])
def place_offer():
    """
    This API method can be used to place new offers.
    Offer is placed only if it passes validation.
    Expecting for a POST request with JSON body, example:
    {
    "type":"offer",
    "owner_id":1200,
    "sum":110000,
    "duration":12,
    "offered_interest":0.09,
    "allow_partial_fill":0
    }
    """
    offer = request.get_json()
    logging.info(f"Gateway: Offer received: {offer}")
    action_id = 2 # Place Offer

    auth_token = request.headers.get('jwt')

    if not auth_token:
        logging.warning("JWT is missing in request headers")
        return {"Authorization": "JWT is missing in request headers"}

    logging.info(f"Authorization: User {auth_token} tries to perform action {action_id}, "
                 f"addressing the Authorization module")

    if auth_token == "":
        return {"error": f"Wrong credentials"}

    permissions_verification_result = authorization.verify_token(auth_token, action_id)

    if 'error' in permissions_verification_result.keys():
        return {"Error": permissions_verification_result['error']}


    return {"result": f"Action {action_id} was successfully performed"}

    # next_id = uuid.uuid4().int & (1 << ConfigParams.generated_uuid_length.value)-1
    #
    # logging.info("Validating offer placement request")
    # response = reporter.validate_offer(offer, ConfigParams.verified_offer_params.value)
    #
    # if 'error' in response.keys():
    #     logging.warning(f"Offer {next_id} has failed validation and was rejected")
    #     return response
    #
    # # In future versions it is possible that the offer will be converted to Google Proto message
    # placed_offer = Offer.Offer(next_id, offer['owner_id'], offer['sum'], offer['duration'], offer['offered_interest'],
    #                      offer['allow_partial_fill'])
    #
    # # Offer - serializing to proto
    # offer_to_producer = proto_handler.serialize_offer_to_proto(placed_offer)
    #
    # # Handling invalid user input -  provided data can't be used to create a valid Bid and serialize it to proto
    # if not offer_to_producer:
    #     return {"error": f"Failed to place a new offer, invalid data in request"}
    #
    # offer_record_headers = [("type", bytes('offer', encoding='utf8'))]
    #
    # logging.info(f"Using Producer instance to send the offer to Kafka topic 'offers': {offer_to_producer} ")
    # producer.produce_message(offer_to_producer, 'offers', offer_record_headers)
    #
    # return {"result": f"Added new offer, ID {next_id} assigned", "offer_id": next_id}

@app.route("/place_bid", methods=['POST'])
def place_bid():
    """
    This API method can be used to place new bids on existing offer.
    Bid is placed only if it passes validation.
    Expecting for a POST request with JSON body, example:
    {
    "type":"bid",
    "owner_id":"2032",
    "bid_interest":0.061,
    "target_offer_id":2,
    "partial_only":0
    }
    """
    bid = request.get_json()
    logging.info(f"Gateway: Bid received {bid}")

    action_id = 1  # Place Bid

    auth_token = request.headers.get('jwt')

    if not auth_token:
        logging.warning("JWT is missing in request headers")
        return {"Authorization": "JWT is missing in request headers"}

    logging.info(f"Authorization: User {auth_token} tries to perform action {action_id}, "
                 f"addressing the Authorization module")

    if auth_token == "":
        return {"error": f"Wrong credentials"}

    permissions_verification_result = authorization.verify_token(auth_token, action_id)

    if 'error' in permissions_verification_result.keys():
        return {"Error": permissions_verification_result['error']}

    return {"result": f"Action {action_id} was successfully performed"}

    # next_id = uuid.uuid4().int & (1 << ConfigParams.generated_uuid_length.value)-1
    #
    # logging.info("Validating target offer with provided ID is OPEN, validating Bid interest against target offer")
    # response = reporter.validate_bid(bid, ConfigParams.verified_bid_params.value)
    #
    # if 'error' in response.keys():
    #     logging.warning(f"Bid {next_id} has failed validation and was rejected")
    #     return response
    #
    # if bid['partial_only'] == 1:
    #     placed_bid = Bid.Bid(next_id, bid['owner_id'], bid['bid_interest'],
    #                          bid['target_offer_id'], bid['partial_only'], bid['partial_sum'])
    #
    # else:
    #     placed_bid = Bid.Bid(next_id, bid['owner_id'], bid['bid_interest'], bid['target_offer_id'], bid['partial_only'])
    #
    # # Bid - serializing to proto
    # bid_to_producer = proto_handler.serialize_bid_to_proto(placed_bid)
    #
    # # Handling invalid user input -  provided data can't be used to create a valid Bid and serialize it to proto
    # if not bid_to_producer:
    #     return {"error": f"Failed to place a new bid, invalid data in request"}
    #
    # bid_record_headers = [("type", bytes('bid', encoding='utf8'))]
    #
    # logging.info(f"Using Producer instance to send the bid to Kafka topic 'bids': {bid_to_producer} ")
    # producer.produce_message(bid_to_producer, 'bids', bid_record_headers)
    #
    # return {"result": f"Added new bid, ID {next_id} assigned", "bid_id": next_id}


@app.route("/get_all_my_bids", methods=['GET'])
def get_my_bids():
    """
    This API method can be used to get all bids placed by customer with provided customer ID.
    :return: JSON
    """

    action_id = 5  # View private bids
    auth_token = request.headers.get('jwt')

    if not auth_token:
        logging.warning("JWT is missing in request headers")
        return {"Authorization": "JWT is missing in request headers"}

    logging.info(f"Authorization: User {auth_token} tries to perform action {action_id}, "
                 f"addressing the Authorization module")

    if auth_token == "":
        return {"error": f"Wrong credentials"}

    permissions_verification_result = authorization.verify_token(auth_token, action_id)

    if 'error' in permissions_verification_result.keys():
        return {"Error": permissions_verification_result['error']}

    lender_id = authorization.get_user_data_by_jwt(auth_token)

    return {"result": f"Action {action_id} was successfully performed"}

    # logging.info(f"Gateway: get all my bids, lender token validated: {token}")
    # return simplejson.dumps(reporter.get_bids_by_lender(lender_id))


@app.route("/get_all_my_offers", methods=['GET'])
def get_my_offers():
    """
    This API method can be used to get all offers placed by customer with provided customer ID.

    """
    action_id = 6  # View private offers
    auth_token = request.headers.get('jwt')

    if not auth_token:
        logging.warning("JWT is missing in request headers")
        return {"Authorization": "JWT is missing in request headers"}

    logging.info(f"Authorization: User {auth_token} tries to perform action {action_id}, "
                 f"addressing the Authorization module")

    if auth_token == "":
        return {"error": f"Wrong credentials"}

    permissions_verification_result = authorization.verify_token(auth_token, action_id)

    if 'error' in permissions_verification_result.keys():
        return {"Error": permissions_verification_result['error']}

    borrower_id = authorization.get_user_data_by_jwt(auth_token)

    return {"result": f"Action {action_id} was successfully performed"}

    #
    # logging.info(f"Gateway: get all my offers, borrower token validated: {token}")
    # return simplejson.dumps(reporter.get_offers_by_borrower(borrower_id))


@app.route("/get_all_my_matches", methods=['GET'])
def get_my_matches():
    """
    This API method can be used to get all matches related to given customer ID.
    :return: JSON

    """
    action_id = 7  # View private matches
    auth_token = request.headers.get('jwt')

    if not auth_token:
        logging.warning("JWT is missing in request headers")
        return {"Authorization": "JWT is missing in request headers"}

    logging.info(f"Authorization: User {auth_token} tries to perform action {action_id}, "
                 f"addressing the Authorization module")

    if auth_token == "":
        return {"error": f"Wrong credentials"}

    permissions_verification_result = authorization.verify_token(auth_token, action_id)

    if 'error' in permissions_verification_result.keys():
        return {"Error": permissions_verification_result['error']}

    owner_id = authorization.get_user_data_by_jwt(auth_token)

    # logging.info(f"Gateway: get all my matches, customer's token validated: {token}")
    # return simplejson.dumps(reporter.get_matches_by_owner(owner_id))



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
