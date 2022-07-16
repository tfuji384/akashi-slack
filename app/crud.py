from datetime import datetime
from typing import Optional, Union

from sqlalchemy import or_
from sqlalchemy.orm import Session

from .models import UserToken


def fetch(db: Session, user_id: str) -> Union[UserToken, None]:
    return db.query(UserToken).filter(UserToken.user_id == user_id).one_or_none()


def fetch_all(db: Session) -> list[UserToken]:
    return db.query(UserToken).all()


def fetch_by_expires_at(db: Session, expires_at_lt: datetime) -> list[UserToken]:
    return db.query(UserToken).filter(or_(UserToken.expires_at == None, UserToken.expires_at < expires_at_lt)).all()


def create(db: Session, user_id: str, token: str, expires_at: Optional[datetime] = None) -> UserToken:
    instance = UserToken(user_id=user_id, token=token, expires_at=expires_at)
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def update(
    db: Session,
    instance: UserToken,
    token: Optional[str] = None,
    expires_at: Optional[datetime] = None,
) -> UserToken:
    instance.token = token or instance.token
    instance.expires_at = expires_at or instance.expires_at
    db.commit()
    return instance


def update_or_create(db: Session,
                     user_id: str,
                     token: Optional[str] = None,
                     expires_at: Optional[datetime] = None) -> UserToken:
    instance = fetch(db, user_id)
    if instance:
        return update(db, instance, token, expires_at)
    if not token:
        raise Exception
    return create(db, user_id, token, expires_at)


def delete(db: Session, instance: UserToken):
    db.delete(instance)
    db.commit()


class UserTokenDoesNotExtsts(Exception):
    ...
