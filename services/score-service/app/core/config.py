from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "score-service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Set DATA_MODE=csv (default) to run without Postgres using the mock CSV.
    # Set DATA_MODE=db to use the relational database defined in DATABASE_URL.
    DATA_MODE: str = "csv"

    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/score_db"

    # Path to mock CSV dataset – relative to repo root, or absolute.
    CSV_DATA_PATH: str = "data/mock/student_score_dataset.csv"
    # Maximum total attendance sessions (lectures + labs) for computing attendance_rate.
    MAX_SESSIONS: int = 20

    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_OPENSSL_RAND_HEX_32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    STUDENT_SERVICE_URL: str = "http://student-service:8000"
    NOTIFICATION_SERVICE_URL: str = "http://notification-service:8003"

    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
