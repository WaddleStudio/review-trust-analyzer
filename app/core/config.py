from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/review_trust_db"
    SERPAPI_KEY: str = ""
    OLLAMA_URL: str = "http://localhost:11434"

    class Config:
        env_file = ".env"


settings = Settings()
