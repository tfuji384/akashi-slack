from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String

from .db import Base, engine


class UserToken(Base):
    __tablename__ = 'user_tokens'
    id = Column(Integer, primary_key=True)
    user_id = Column(String(16), nullable=False, unique=True)
    token = Column(String(36), nullable=False)
    expires_at = Column(DateTime, index=True, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.now)

    def __init__(self, user_id: str, token: str, expires_at: Optional[datetime] = None):
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.created_at = datetime.now()


Base.metadata.create_all(engine)
