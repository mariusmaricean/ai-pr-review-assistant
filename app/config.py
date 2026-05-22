from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "AI PR Review Assistant"
    openai_api_key: str = ""
    github_token: str = ""
    redis_url: str = "redis://localhost:6379/0"
    review_idempotency_ttl_seconds: int = 60 * 60
    github_app_id: str = ""
    github_private_key_path: str = ""
    github_webhook_secret: str = ""
    admin_api_token: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
