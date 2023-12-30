"""
App configuration
"""
from os import getenv
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = getenv('API_KEY')
ENV = getenv('ENV')
WEBHOOK_URL = getenv('WEBHOOK_URL')
ADMIN_PASSWORD = getenv('ADMIN_PASSWORD')
CLOUDINARY_API_KEY = getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = getenv('CLOUDINARY_API_SECRET')
CLOUDINARY_CLOUD_NAME = getenv('CLOUDINARY_CLOUD_NAME')

FIREBASE_BUCKET_NAME = getenv('FIRESTORE_BUCKET_NAME')

DB_TYPE = getenv('DB_TYPE', "sql")

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

SENTRY_DSN = getenv('SENTRY_DSN')


def get_config():
    """
    Retrieves the configuration values from environment variables.

    Returns:
        dict: A dictionary containing the configuration values.
    """
    config = {
        'API_KEY': API_KEY,
        'ENV': ENV,
        'WEBHOOK_URL': WEBHOOK_URL,
        'ADMIN_PASSWORD': ADMIN_PASSWORD,
        'CLOUDINARY_API_KEY': CLOUDINARY_API_KEY,
        'CLOUDINARY_API_SECRET': CLOUDINARY_API_SECRET,
        'CLOUDINARY_CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'FIREBASE_BUCKET_NAME': FIREBASE_BUCKET_NAME,
        'DB_TYPE': DB_TYPE,
        'ROOT_DIR': ROOT_DIR,
        'SENTRY_DSN': SENTRY_DSN
    }
    return config
