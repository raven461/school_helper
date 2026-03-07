from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
import os

class Settings(BaseSettings):
    #API tokens
    bot_token: SecretStr
    ai_token: SecretStr
    #email config
    email_login:SecretStr
    email_password: SecretStr
    #admin feathures
    dev_key: SecretStr
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../.env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )


config = Settings()