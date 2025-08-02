"""
缓存服务
用于缓存Tushare数据，提升策略执行性能
"""

import asyncio
import json
import time
from typing import Any, Optional, Dict
import logging
import pickle
import hashlib

logger = logging.getLogger(__name__)


class CacheService:
    """内存缓存服务"""
    
    def __init__(self, max_size: int = 1000, default_expire: int = 3600):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.default_expire = default_expire
        
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            if key in self.cache:
                item = self.cache[key]
                
                # 检查是否过期
                if item['expire_time'] > time.time():
                    logger.debug(f"缓存命中: {key}")
                    return item['value']
                else:
                    # 删除过期项
                    del self.cache[key]
                    logger.debug(f"缓存过期: {key}")
            
            return None
            
        except Exception as e:
            logger.error(f"获取缓存失败: {key}, 错误: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """设置缓存值"""
        try:
            expire_time = time.time() + (expire or self.default_expire)
            
            # 如果缓存已满，删除最旧的项
            if len(self.cache) >= self.max_size:
                await self._evict_oldest()
            
            self.cache[key] = {
                'value': value,
                'expire_time': expire_time,
                'created_time': time.time()
            }
            
            logger.debug(f"缓存设置: {key}")
            return True
            
        except Exception as e:
            logger.error(f"设置缓存失败: {key}, 错误: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"缓存删除: {key}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"删除缓存失败: {key}, 错误: {str(e)}")
            return False
    
    async def clear(self) -> bool:
        """清空所有缓存"""
        try:
            self.cache.clear()
            logger.info("缓存已清空")
            return True
            
        except Exception as e:
            logger.error(f"清空缓存失败: {str(e)}")
            return False
    
    async def _evict_oldest(self):
        """删除最旧的缓存项"""
        if not self.cache:
            return
        
        oldest_key = min(self.cache.keys(), 
                        key=lambda k: self.cache[k]['created_time'])
        del self.cache[oldest_key]
        logger.debug(f"删除最旧缓存: {oldest_key}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        valid_items = 0
        expired_items = 0
        
        for item in self.cache.values():
            if item['expire_time'] > current_time:
                valid_items += 1
            else:
                expired_items += 1
        
        return {
            'total_items': len(self.cache),
            'valid_items': valid_items,
            'expired_items': expired_items,
            'max_size': self.max_size,
            'usage_ratio': len(self.cache) / self.max_size
        }
    
    async def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []
        
        for key, item in self.cache.items():
            if item['expire_time'] <= current_time:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"清理过期缓存: {len(expired_keys)}项")


# 全局缓存实例
cache_service = CacheService()