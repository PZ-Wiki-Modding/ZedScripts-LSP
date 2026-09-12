import datetime
import logging
import requests_cache

from .. import ZEDSCRIPT_CACHE_DIR




_default_expire_after = datetime.timedelta(hours=12)
def get_session(expire_after: datetime.timedelta | float = _default_expire_after) -> requests_cache.CachedSession:
    """
    Get a cached HTTP session with the specified expiration time.

    Args:
        expire_after (datetime.timedelta | float, optional): The duration after which the cache expires. Defaults to datetime.timedelta(days=1).

    Returns:
        requests_cache.CachedSession: A cached HTTP session with the specified expiration time.
    """
    session = requests_cache.CachedSession(
        cache_name=str(ZEDSCRIPT_CACHE_DIR / "http_cache"), 
        expire_after=expire_after,
    )
    return session

def load_json(url: str, expire_after: datetime.timedelta | float = _default_expire_after) -> dict:
    """
    Load JSON data from the specified URL using a cached HTTP session.

    Args:
        url (str): The URL to load JSON data from.
        expire_after (datetime.timedelta | float, optional): The duration after which the cache expires. Defaults to _default_expire_after.

    Returns:
        dict: The JSON data loaded from the specified URL.
    """
    session = get_session(expire_after=expire_after)
    response = session.get(url)
    is_cached = getattr(response, 'from_cache', False)
    logging.debug(f"Loading {url} - from_cache: {is_cached}")
    response.raise_for_status()
    return response.json()

def clear_cache():
    """Resets the session cache."""
    session = get_session()
    session.cache.clear()
    logging.debug("HTTP cache cleared.")
