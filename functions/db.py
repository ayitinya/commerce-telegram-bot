"""Database module for the bot."""

from data.DatabaseInterface import DBInterface
from media_handler import MediaHandler  # pylint: disable = import-error


def get_db(db: DBInterface, *args, **kwargs) -> DBInterface:
    """Returns a DB object

    Returns:
        DB: A DB object
    """
    return db(*args, **kwargs)


def get_media_handler(handler: MediaHandler):
    """Returns a media handler object

    Returns:
        MediaHandler: A media handler object
    """
    return handler()
