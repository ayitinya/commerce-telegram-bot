"""This module contains functions to handle media files saved on cloudinary storage"""

import config

import cloudinary
if config.ENV == "development":
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET,
    )
else:
    # proxies are required for cloudinary to work in production on pythonanywhere
    cloudinary.config(
        cloud_name=config.CLOUDINARY_CLOUD_NAME,
        api_key=config.CLOUDINARY_API_KEY,
        api_secret=config.CLOUDINARY_API_SECRET,
        api_proxy='http://proxy.server:3128'
    )

import cloudinary.api
import cloudinary.uploader


def upload_image(image, public_id):
    """Uploads an image to cloudinary storage

    Args:
        image: The image to be uploaded
        public_id (str): filename of the image, usually the product name

    Returns:
        dict: The response from cloudinary
    """
    if config.ENV == "development":
        return cloudinary.uploader.upload(image, folder='dev-ecommerce-bot', public_id=public_id, overwrite=True)
    return cloudinary.uploader.upload(image, folder='ecommerce-bot', public_id=public_id, overwrite=True)


def delete_image(public_id):
    """Deletes an image from cloudinary storage

    Args:
        public_id (str): filename of the image, usually the product name

    Returns:
        dict: The response from cloudinary
    """
    return cloudinary.uploader.destroy(public_id, invalidate=True)
