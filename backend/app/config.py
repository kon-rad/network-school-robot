from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://robot_user:robot_password@localhost:5432/network_school_robot"
    robot_connection_mode: str = "auto"
    robot_host: str = "reachy-mini.local"
    robot_auto_connect: bool = True
    robot_auto_execute_actions: bool = True
    anthropic_api_key: str = ""
    deepgram_api_key: str = ""
    robot_voice_enabled: bool = True
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Voice Control Settings
    voice_control_enabled: bool = True
    voice_control_auto_start: bool = False
    voice_control_wake_words: str = "hey claude,claude code,claude"
    voice_control_listening_timeout: float = 10.0  # seconds
    voice_control_stt_model: str = "nova-2"
    voice_control_tts_voice: str = "aura-asteria-en"

    @property
    def wake_words_list(self) -> list[str]:
        return [w.strip().lower() for w in self.voice_control_wake_words.split(",")]

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
