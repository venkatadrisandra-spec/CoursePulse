import os

from dotenv import load_dotenv

load_dotenv()


def _get_int_env(name, default):
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY") or "dev-only-change-me"
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///course_feedback_dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MIN_REPORT_RESPONSES = _get_int_env("MIN_REPORT_RESPONSES", 5)
