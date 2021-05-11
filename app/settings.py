from os import environ
from typing import Optional

from pydantic import BaseSettings


class Settings(BaseSettings):
    AKASHI_COMPANY_ID: Optional[str] = environ.get('AKASHI_COMPANY_ID')
    SLACK_BOT_TOKEN: Optional[str] = environ.get('SLACK_BOT_TOKEN')
    SLACK_CHANNEL_ID: Optional[str] = environ.get('SLACK_CHANNEL_ID')
    SLACK_SIGNING_SECRET: Optional[str] = environ.get('SLACK_SIGNING_SECRET')


class DataBaseSettings(BaseSettings):
    DATABASE_URL: Optional[str] = environ.get('DATABASE_URL', 'sqlite:///./app.db')


settings = Settings()
db_settings = DataBaseSettings()
