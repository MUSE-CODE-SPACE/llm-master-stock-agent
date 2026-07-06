"""Config from env / .env. / 환경변수·.env 설정."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    provider: str = "openai"            # openai | anthropic | ollama
    llm_model: str = "gpt-4o-mini"      # anthropic: claude-haiku-4-5 · ollama: qwen2.5:7b
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434/v1"
    db_path: str = "./stock_agent.db"
    max_steps: int = 6
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
