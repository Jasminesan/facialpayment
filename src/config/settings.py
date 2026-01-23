import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    _cred_file = os.getenv("FIREBASE_CREDENTIALS", "serviceAccountKey.json")
    FIREBASE_KEY_PATH = os.path.join(os.getcwd(), _cred_file)
    
    # App Mode
    IS_DEV = os.getenv("IS_DEV", "True") == "True"