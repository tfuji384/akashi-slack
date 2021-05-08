import string
from uuid import uuid4

from factory import Sequence
from factory.alchemy import SQLAlchemyModelFactory
from rstr import rstr

from app.models import UserToken
from tests.helpers import session


class UserTokenFactory(SQLAlchemyModelFactory):
    user_id = Sequence(lambda x: rstr(string.ascii_letters, 11))
    token = Sequence(lambda x: str(uuid4()))

    class Meta:
        model = UserToken
        sqlalchemy_session = session
        sqlalchemy_session_persistence = 'commit'
