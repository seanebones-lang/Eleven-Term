"""
Disk-based cache utilities for grok_agent
Uses SQLite for persistent cache storage
"""
import sqlite3
import json
import time
import os
from pathlib import Path
from typing import Optional, Any, Dict
from collections import OrderedDict

# Cache database location
CACHE_DB_PATH = Path.home() / ".grok_terminal" / "cache.db"

def init_cache_db() -> sqlite3.Connection:
    """Initialize SQLite cache database"""
    cache_dir = CACHE_DB_PATH.parent
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(CACHE_DB_PATH), timeout=10.0)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
    conn.commit()
    return conn

class DiskCache:
    """Disk-based cache with LRU eviction"""
    
    def __init__(self, max_size: int = 100, ttl: float = 300.0):
        """Initialize disk cache
        
        Args:
            max_size: Maximum number of entries
            ttl: Time-to-live in seconds
        """
        self.max_size = max_size
        self.ttl = ttl
        self._conn = init_cache_db()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if valid, None otherwise
        """
        cursor = self._conn.execute(
            "SELECT value, timestamp FROM cache WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        
        if row:
            value_str, timestamp = row
            if time.time() - timestamp < self.ttl:
                # Update timestamp (LRU behavior)
                self._conn.execute(
                    "UPDATE cache SET timestamp = ? WHERE key = ?",
                    (time.time(), key)
                )
                self._conn.commit()
                self._stats["hits"] += 1
                return json.loads(value_str)
            else:
                # Expired, remove
                self._conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                self._conn.commit()
        
        self._stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache with LRU eviction
        
        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
        """
        value_str = json.dumps(value)
        timestamp = time.time()
        
        # Check if key exists (update) or insert
        cursor = self._conn.execute(
            "SELECT key FROM cache WHERE key = ?",
            (key,)
        )
        if cursor.fetchone():
            self._conn.execute(
                "UPDATE cache SET value = ?, timestamp = ? WHERE key = ?",
                (value_str, timestamp, key)
            )
        else:
            self._conn.execute(
                "INSERT INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                (key, value_str, timestamp)
            )
        
        # Evict oldest entries if cache is full
        cursor = self._conn.execute("SELECT COUNT(*) FROM cache")
        count = cursor.fetchone()[0]
        
        while count > self.max_size:
            # Delete oldest entry
            cursor = self._conn.execute(
                "SELECT key FROM cache ORDER BY timestamp ASC LIMIT 1"
            )
            old_key = cursor.fetchone()
            if old_key:
                self._conn.execute("DELETE FROM cache WHERE key = ?", (old_key[0],))
                self._stats["evictions"] += 1
            count -= 1
        
        self._conn.commit()
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self._conn.execute("DELETE FROM cache")
        self._conn.commit()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics
        
        Returns:
            Dict with cache statistics
        """
        cursor = self._conn.execute("SELECT COUNT(*) FROM cache")
        size = cursor.fetchone()[0]
        
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "size": size,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }
    
    def close(self) -> None:
        """Close database connection"""
        self._conn.close()

# Global disk cache instance
_disk_cache: Optional[DiskCache] = None

def get_disk_cache(max_size: int = 100, ttl: float = 300.0) -> DiskCache:
    """Get or create global disk cache instance"""
    global _disk_cache
    if _disk_cache is None:
        _disk_cache = DiskCache(max_size=max_size, ttl=ttl)
    return _disk_cache