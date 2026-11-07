import os

from dotenv import load_dotenv

load_dotenv()


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def required_int(name: str) -> int:
    return int(required(name))


def required_int_list(name: str) -> list[int]:
    return [int(value.strip()) for value in required(name).split(",")]


BOT_TOKEN: str = required("BOT_TOKEN")
ALLOWED_DISCORD_SERVERS: list[int] = required_int_list("ALLOWED_DISCORD_SERVERS")
SEASONS_ANNOUNCEMENT_CHANNEL_ID: int = required_int("SEASONS_ANNOUNCEMENT_CHANNEL_ID")
RECORDS_CHANNEL_ID: int = required_int("RECORDS_CHANNEL_ID")
GENERAL_CHANNEL_ID: int = required_int("GENERAL_CHANNEL_ID")
MASTERY_CHANNEL_ID: int = required_int("MASTERY_CHANNEL_ID")
