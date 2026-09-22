from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bitrix_webhook_url: str
    bitrix_outgoing_token: str = ""


settings = Settings()
