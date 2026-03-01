from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr
import os
import datetime

LOG_FILE_ENCODING = "utf-8"
LOG_FILE_PATH = "./logs/log "+(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S"))+".log"

class Settings(BaseSettings):
    bot_token: SecretStr
    ai_token: SecretStr
    dev_key: SecretStr
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), "../.env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

config = Settings()