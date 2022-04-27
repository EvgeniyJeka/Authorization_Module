
import sqlalchemy as db
from sqlalchemy import create_engine, or_, and_
from sqlalchemy_utils import database_exists, create_database
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class UsersMapped(Base):
    __tablename__ = 'users'

    id = Column('id', db.BIGINT, primary_key=True)
    username = Column('username', db.String(255))
    password = Column('password', db.String(255))

    jwt_token = Column('jwt_token', db.String(255))
    key = Column('key', db.String(255))
    token_creation_time = Column('token_creation_time', db.String(255))

    #allowed_actions = Column('allowed_actions', db.String(255))
    role_id = Column('role_id', db.String(255))


class RolesMapped(Base):
    __tablename__ = 'roles'

    role_id = Column('id', db.BIGINT, primary_key=True)
    role = Column('role', db.String(255))


class ActionsMapped(Base):
    __tablename__ = 'actions'

    action_id = Column('id', db.BIGINT, primary_key=True)
    action = Column('action', db.String(255))


class ActionsToRolesMapped(Base):
    __tablename__ = 'actions_by_roles'

    role_id = Column('role_id', db.BIGINT, primary_key=True)
    allowed_actions_id = Column('allowed_actions_id', db.String(255))



