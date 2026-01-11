#!/usr/bin/env python3
"""
Tests for cache functionality
"""

import pytest
import time
from unittest.mock import patch, MagicMock
from collections import OrderedDict
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import grok_agent


class TestCacheFunctions:
    """Test cache functions"""
    
    def test_get_cache_stats_empty(self, patch_default_config):
        """Test cache statistics when cache is empty"""
        grok_agent.reset_cache()
        stats = grok_agent.get_cache_stats()
        
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
        assert stats["size"] == 0
        assert stats["hit_rate"] == 0.0
        assert stats["total_requests"] == 0
    
    def test_get_cache_stats_with_data(self, patch_default_config):
        """Test cache statistics with cache hits and misses"""
        grok_agent.reset_cache()
        
        # Simulate cache operations
        cache_key = "test_key"
        grok_agent._response_cache[cache_key] = (time.time(), "test_response")
        grok_agent._cache_stats["hits"] = 5
        grok_agent._cache_stats["misses"] = 10
        
        stats = grok_agent.get_cache_stats()
        
        assert stats["hits"] == 5
        assert stats["misses"] == 10
        assert stats["size"] == 1
        assert stats["hit_rate"] == 5.0 / 15.0
        assert stats["total_requests"] == 15
    
    def test_reset_cache(self, patch_default_config):
        """Test cache reset function"""
        # Add data to cache
        grok_agent._response_cache["key1"] = (time.time(), "response1")
        grok_agent._response_cache["key2"] = (time.time(), "response2")
        grok_agent._cache_stats["hits"] = 10
        grok_agent._cache_stats["misses"] = 5
        grok_agent._cache_stats["evictions"] = 2
        
        # Reset cache
        grok_agent.reset_cache()
        
        # Verify cache is empty and stats are reset
        assert len(grok_agent._response_cache) == 0
        assert grok_agent._cache_stats["hits"] == 0
        assert grok_agent._cache_stats["misses"] == 0
        assert grok_agent._cache_stats["evictions"] == 0
    
    def test_check_cache_hit(self, patch_default_config):
        """Test cache check with hit"""
        grok_agent.reset_cache()
        
        cache_key = "test_key"
        response_data = {"choices": [{"message": {"content": "test"}}]}
        grok_agent._response_cache[cache_key] = (time.time(), response_data)
        
        result = grok_agent._check_cache(cache_key, ttl=300)
        
        assert result == response_data
        assert grok_agent._cache_stats["hits"] == 1
        assert grok_agent._cache_stats["misses"] == 0
    
    def test_check_cache_miss(self, patch_default_config):
        """Test cache check with miss"""
        grok_agent.reset_cache()
        
        cache_key = "nonexistent_key"
        result = grok_agent._check_cache(cache_key, ttl=300)
        
        assert result is None
        assert grok_agent._cache_stats["hits"] == 0
        assert grok_agent._cache_stats["misses"] == 1
    
    def test_check_cache_expired(self, patch_default_config):
        """Test cache check with expired entry"""
        grok_agent.reset_cache()
        
        cache_key = "expired_key"
        # Add entry with old timestamp (expired)
        grok_agent._response_cache[cache_key] = (time.time() - 400, "expired_response")
        
        result = grok_agent._check_cache(cache_key, ttl=300)
        
        assert result is None
        assert cache_key not in grok_agent._response_cache  # Expired entry removed
        assert grok_agent._cache_stats["misses"] == 1
    
    def test_update_cache_below_limit(self, patch_default_config):
        """Test cache update when below size limit"""
        grok_agent.reset_cache()
        
        cache_key = "test_key"
        response_data = {"choices": [{"message": {"content": "test"}}]}
        grok_agent._update_cache(cache_key, response_data, max_size=100)
        
        assert cache_key in grok_agent._response_cache
        assert grok_agent._cache_stats["evictions"] == 0
    
    def test_update_cache_eviction(self, patch_default_config):
        """Test cache eviction when at size limit"""
        grok_agent.reset_cache()
        
        # Fill cache to limit
        for i in range(3):
            grok_agent._update_cache(f"key_{i}", f"response_{i}", max_size=3)
        
        assert len(grok_agent._response_cache) == 3
        assert "key_0" in grok_agent._response_cache
        
        # Add 4th item - should evict oldest
        grok_agent._update_cache("key_3", "response_3", max_size=3)
        
        assert len(grok_agent._response_cache) == 3
        assert "key_0" not in grok_agent._response_cache  # Oldest evicted
        assert "key_3" in grok_agent._response_cache  # Newest added
        assert grok_agent._cache_stats["evictions"] == 1
    
    def test_update_cache_lru_behavior(self, patch_default_config):
        """Test LRU behavior - accessed items move to end"""
        grok_agent.reset_cache()
        
        # Add items
        grok_agent._update_cache("key_0", "response_0", max_size=3)
        grok_agent._update_cache("key_1", "response_1", max_size=3)
        grok_agent._update_cache("key_2", "response_2", max_size=3)
        
        # Access key_0 (should move to end - most recently used)
        grok_agent._check_cache("key_0", ttl=300)
        
        # Add 4th item - should evict key_1 (least recently used, not key_0)
        grok_agent._update_cache("key_3", "response_3", max_size=3)
        
        assert "key_1" not in grok_agent._response_cache  # Least recently used evicted
        assert "key_0" in grok_agent._response_cache  # Recently accessed, kept
        assert "key_3" in grok_agent._response_cache  # Newest, kept
    
    def test_semantic_hash_normalization(self, patch_default_config):
        """Test semantic hash normalizes queries"""
        messages1 = [{"role": "user", "content": "Test Query"}]
        messages2 = [{"role": "user", "content": "test query"}]
        messages3 = [{"role": "user", "content": "Test  Query"}]
        
        hash1 = grok_agent._semantic_hash(messages1, "grok-4.1-fast", 0.1)
        hash2 = grok_agent._semantic_hash(messages2, "grok-4.1-fast", 0.1)
        hash3 = grok_agent._semantic_hash(messages3, "grok-4.1-fast", 0.1)
        
        # All should produce same hash (normalized)
        assert hash1 == hash2 == hash3
    
    def test_semantic_hash_different_temperature(self, patch_default_config):
        """Test semantic hash includes temperature"""
        messages = [{"role": "user", "content": "test"}]
        
        hash1 = grok_agent._semantic_hash(messages, "grok-4.1-fast", 0.1)
        hash2 = grok_agent._semantic_hash(messages, "grok-4.1-fast", 0.5)
        
        # Different temperature should produce different hash
        assert hash1 != hash2
    
    def test_semantic_hash_different_model(self, patch_default_config):
        """Test semantic hash includes model"""
        messages = [{"role": "user", "content": "test"}]
        
        hash1 = grok_agent._semantic_hash(messages, "grok-4.1-fast", 0.1)
        hash2 = grok_agent._semantic_hash(messages, "grok-2", 0.1)
        
        # Different model should produce different hash
        assert hash1 != hash2
