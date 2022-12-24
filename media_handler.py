import config

import cloudinary
import cloudinary.api
import cloudinary.uploader

cloudinary.config(
    cloud_name=config.CLOUDINARY_CLOUD_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True
)


def upload_image(image, public_id):
    return cloudinary.uploader.upload(image, folder='ecommerce-bot', public_id=public_id, overwrite=True)
