import logging
import sqlalchemy as db
import hashlib
from constants import USERS_TABLE_NAME

import objects_mapped_
#from .objects_mapped_ import UsersMapped
from sqlalchemy.orm import sessionmaker


class Tools:

    @staticmethod
    def hash_string(input_: str):
        plaintext = input_.encode()

        # call the sha256(...) function returns a hash object
        d = hashlib.sha256(plaintext)

        # generate human readable hash of "hello" string
        hash = d.hexdigest()
        return hash

