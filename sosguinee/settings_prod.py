import os

os.environ.setdefault("ENVIRONMENT", "production")
os.environ.setdefault("DEBUG", "False")

from .settings import *  # noqa: F401,F403
