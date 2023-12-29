"""This module contains functions to handle media files saved on cloudinary storage"""

from abc import ABC, abstractmethod
from typing import Type
import config

from google.cloud import storage

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
    print(public_id)
    return cloudinary.uploader.destroy(public_id, invalidate=True)


class MediaHandler(ABC):
    """Abstract class for media handlers"""

    @abstractmethod
    def upload(self, file: str, filename: str):
        """Uploads media to cloud storage

        Args:
            file (str): The file to be uploaded
            filename (str): The filename of the file to be uploaded

        Returns:
            dict: The response from upload
        """
        raise NotImplementedError

    @abstractmethod
    def download(self, filename: str) -> bytes:
        """Downloads media from cloud storage

        Args:
            filename (str): The filename of the media to be downloaded

        Returns:
            str: The downloaded media
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, filename: str):
        """Deletes media from cloud storage

        Returns:
            dict: The response from cloud
        """
        raise NotImplementedError


class FirebaseStorage(MediaHandler):
    """Class for handling media files on firebase storage"""

    def __init__(self):
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(config.FIREBASE_BUCKET_NAME)

    def upload(self, file: str, filename: str):
        blob = self.bucket.blob(filename)
        blob.upload_from_string(file)

    def download(self, filename: str) -> bytes:
        return self.bucket.blob(filename).download_as_string()

    def delete(self, filename: str):
        blob = self.bucket.blob(filename)
        blob.reload()
        generation_match_precondition = blob.generation

        blob.delete(if_generation_match=generation_match_precondition)


class MediaHandlerFactory:
    """Factory class for creating media handlers"""

    def __init__(self, handler_type: Type[MediaHandler]):
        self.handler_type = handler_type

    def get_handler(self) -> MediaHandler:
        """
        Args:
            handler_type (str): The type of handler to be created

        Returns:
            MediaHandler: The created handler
        """
        return self.handler_type()

