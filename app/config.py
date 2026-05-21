from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI PR Review Assistant"
    openai_api_key: str = ""
    github_token: str = ""
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()
