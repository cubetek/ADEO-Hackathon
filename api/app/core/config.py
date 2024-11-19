from pydantic import BaseModel

class Settings(BaseModel):
    APP_NAME: str = "FastAPI File Upload"
    DEBUG: bool = True
    TEMP_DIR: str = "temp_files/"
    REDIS_URL: str = "redis://localhost"

    class Config:
        env_file = ".env"

settings = Settings()
