import os
from dotenv import load_dotenv

load_dotenv()

APP_HOST = os.environ["APP_HOST"]
APP_PORT = os.environ["APP_PORT"]
APP_STATE = True if os.environ["APP_STATE"] == "DEV" else False