from datetime import datetime, timedelta
from typing import Any, Dict, Tuple

class CacheManager:
    """
    A simple in-memory cache manager with Time-To-Live (TTL) support.
    """

    def __init__(self, ttl: timedelta):
        """
        Initializes the CacheManager.

        Args:
            ttl: The default time-to-live for cache entries.
        """
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self.ttl = ttl

    def get(self, key: str) -> Any | None:
        """
        Retrieves an item from the cache if it exists and has not expired.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The cached value, or None if the item is not found or has expired.
        """
        if key not in self._cache:
            return None

        value, timestamp = self._cache[key]
        if datetime.now() - timestamp > self.ttl:
            # Item has expired, so remove it and return None
            self.invalidate(key)
            return None

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Adds an item to the cache with a new timestamp.

        Args:
            key: The key to store the item under.
            value: The value to be cached.
        """
        self._cache[key] = (value, datetime.now())

    def invalidate(self, key: str) -> None:
        """
        Removes an item from the cache.

        Args:
            key: The key of the item to remove.
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """
        Clears the entire cache.
        """
        self._cache.clear()
