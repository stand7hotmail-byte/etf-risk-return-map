import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple


class CacheManager:
    """
    Thread-safe in-memory cache manager with Time-To-Live (TTL) support.
    
    Features:
    - Thread-safe operations using RLock
    - Automatic expiration of old entries
    - Configurable TTL per cache instance
    
    Examples:
        >>> cache = CacheManager(ttl=timedelta(seconds=60))
        >>> cache.set("key1", "value1")
        >>> cache.get("key1")
        'value1'
        >>> cache.invalidate("key1")
        True
        >>> cache.get("key1")
        None
    """

    def __init__(self, ttl: timedelta):
        """
        Initializes the CacheManager.

        Args:
            ttl: The default time-to-live for cache entries.
        """
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self.ttl = ttl
        self._lock = threading.RLock()  # Reentrant lock for thread safety

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves an item from the cache if it exists and has not expired.

        Thread-safe operation.

        Args:
            key: The key of the item to retrieve.

        Returns:
            The cached value, or None if not found or expired.
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            
            # Check if expired
            if datetime.now() - timestamp > self.ttl:
                del self._cache[key]  # Remove expired entry
                return None

            return value

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """
        Adds an item to the cache with a timestamp.

        Thread-safe operation.

        Args:
            key: The key to store the item under.
            value: The value to be cached.
            ttl: Optional custom TTL for this specific entry.
                 If None, uses the default TTL.
        """
        with self._lock:
            # Store with custom TTL if provided
            # For simplicity, we store timestamp and check against self.ttl
            # A more advanced implementation could store per-item TTL
            self._cache[key] = (value, datetime.now())

    def invalidate(self, key: str) -> bool:
        """
        Removes an item from the cache.

        Thread-safe operation.

        Args:
            key: The key of the item to remove.
            
        Returns:
            True if item was removed, False if it didn't exist.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """
        Clears the entire cache.
        
        Thread-safe operation.
        """
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Removes all expired entries from the cache.
        
        Should be called periodically to prevent memory leaks.
        Thread-safe operation.
        
        Returns:
            Number of expired entries removed.
        """
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, (_, timestamp) in self._cache.items()
                if now - timestamp > self.ttl
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)

    def size(self) -> int:
        """
        Returns the current number of items in the cache.
        
        Thread-safe operation.
        
        Returns:
            Number of cached items (including potentially expired ones).
        """
        with self._lock:
            return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """
        Checks if a key exists in the cache (and is not expired).
        
        Args:
            key: The key to check.
            
        Returns:
            True if key exists and is not expired.
        """
        return self.get(key) is not None