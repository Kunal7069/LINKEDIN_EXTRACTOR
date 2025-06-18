import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    RAPIDAPI_KEY: str = os.getenv("RAPIDAPI_KEY")
    RAPIDAPI_HOST: str = os.getenv("RAPIDAPI_HOST", "linkedin-data-api.p.rapidapi.com")

settings = Settings()
