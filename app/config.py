from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI PR Review Assistant"
    openai_api_key: str = ""
    github_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
