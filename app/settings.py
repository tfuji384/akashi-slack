from os import environ
from typing import Union

from pydantic import BaseSettings


class Settings(BaseSettings):
    AKASHI_COMPANY_ID: str = environ.get('AKASHI_COMPANY_ID')
    SLACK_BOT_TOKEN: str = environ.get('SLACK_BOT_TOKEN')
    SLACK_CHANNEL_ID: Union[str, None] = environ.get('SLACK_CHANNEL_ID')
    SLACK_SIGNING_SECRET: str = environ.get('SLACK_SIGNING_SECRET')


class DataBaseSettings(BaseSettings):
    DATABASE_URL = environ.get('DATABASE_URL', 'sqlite:///./app.db')


settings = Settings()
db_settings = DataBaseSettings()
