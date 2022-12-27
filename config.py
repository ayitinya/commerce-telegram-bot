from os import getenv
from dotenv import load_dotenv

load_dotenv()

API_KEY = getenv('API_KEY')
ENV = getenv('ENV')
WEBHOOK_URL = getenv('WEBHOOK_URL')
ADMIN_PASSWORD = getenv('ADMIN_PASSWORD')
CLOUDINARY_API_KEY = getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = getenv('CLOUDINARY_API_SECRET')
CLOUDINARY_CLOUD_NAME = getenv('CLOUDINARY_CLOUD_NAME')
