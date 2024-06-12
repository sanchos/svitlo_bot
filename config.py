from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Settings class to manage environment variables for the application.

    Attributes:
        BASE_URL (str): The base URL for the API.
        CLIENT_ID (str): The client ID for the API.
        SECRET (str): The secret key for the API.
        DEVICE_ID (str): The device ID for the API.
        DB_FILE (str): The file path for the SQLite database.
        BOT_TOKEN (str): The token for the Telegram bot.
        CHANNEL_ID (str): The chat ID for the Telegram channel.
        SCHEDULE_TIME (float): The schedule time for periodic tasks.
    """

    BASE_URL: str
    CLIENT_ID: str
    SECRET: str
    DEVICE_ID: str
    DB_FILE: str
    BOT_TOKEN: str
    CHANNEL_ID: str
    SCHEDULE_TIME: float

    class Config:
        env_file = ".env"


settings = Settings()
