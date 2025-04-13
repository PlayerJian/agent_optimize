from typing import Dict, Any, Optional
from datetime import datetime
import logging
import json
import os

from models.settings import RetrievalSettings, CacheSettings, CrossKbSettings

logger = logging.getLogger("settings")

class SettingsService:
    """
    设置服务
    
    负责管理系统各项设置，包括检索设置、缓存设置和跨库检索设置等
    """
    
    def __init__(self):
        self.settings_file = os.path.join(os.path.dirname(__file__), "../data/settings.json")
        self._ensure_settings_file()
    
    def _ensure_settings_file(self):
        """
        确保设置文件存在，如果不存在则创建默认设置
        """
        os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
        
        if not os.path.exists(self.settings_file):
            # 创建默认设置
            default_settings = {
                "retrieval": RetrievalSettings().dict(),
                "cache": CacheSettings().dict(),
                "cross_kb": CrossKbSettings().dict()
            }
            
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(default_settings, f, ensure_ascii=False, indent=2)
    
    async def _load_settings(self) -> Dict[str, Any]:
        """
        加载设置文件
        """
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load settings: {str(e)}", exc_info=True)
            # 返回默认设置
            return {
                "retrieval": RetrievalSettings().dict(),
                "cache": CacheSettings().dict(),
                "cross_kb": CrossKbSettings().dict()
            }
    
    async def _save_settings(self, settings: Dict[str, Any]):
        """
        保存设置到文件
        """
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save settings: {str(e)}", exc_info=True)
            raise Exception(f"保存设置失败: {str(e)}")
    
    async def get_retrieval_settings(self) -> RetrievalSettings:
        """
        获取检索设置
        """
        settings = await self._load_settings()
        return RetrievalSettings(**settings.get("retrieval", {}))
    
    async def update_retrieval_settings(self, new_settings: RetrievalSettings) -> RetrievalSettings:
        """
        更新检索设置
        """
        settings = await self._load_settings()
        
        # 更新设置
        new_settings_dict = new_settings.dict()
        new_settings_dict["updated_at"] = datetime.now().isoformat()
        settings["retrieval"] = new_settings_dict
        
        # 保存设置
        await self._save_settings(settings)
        
        return RetrievalSettings(**new_settings_dict)
    
    async def get_cache_settings(self) -> CacheSettings:
        """
        获取缓存设置
        """
        settings = await self._load_settings()
        return CacheSettings(**settings.get("cache", {}))
    
    async def update_cache_settings(self, new_settings: CacheSettings) -> CacheSettings:
        """
        更新缓存设置
        """
        settings = await self._load_settings()
        
        # 更新设置
        new_settings_dict = new_settings.dict()
        new_settings_dict["updated_at"] = datetime.now().isoformat()
        settings["cache"] = new_settings_dict
        
        # 保存设置
        await self._save_settings(settings)
        
        return CacheSettings(**new_settings_dict)
    
    async def get_cross_kb_settings(self) -> CrossKbSettings:
        """
        获取跨库检索设置
        """
        settings = await self._load_settings()
        return CrossKbSettings(**settings.get("cross_kb", {}))
    
    async def update_cross_kb_settings(self, new_settings: CrossKbSettings) -> CrossKbSettings:
        """
        更新跨库检索设置
        """
        settings = await self._load_settings()
        
        # 更新设置
        new_settings_dict = new_settings.dict()
        new_settings_dict["updated_at"] = datetime.now().isoformat()
        settings["cross_kb"] = new_settings_dict
        
        # 保存设置
        await self._save_settings(settings)
        
        return CrossKbSettings(**new_settings_dict)
    
    async def reset_settings(self):
        """
        重置所有设置为默认值
        """
        default_settings = {
            "retrieval": RetrievalSettings().dict(),
            "cache": CacheSettings().dict(),
            "cross_kb": CrossKbSettings().dict()
        }
        
        # 添加更新时间
        now = datetime.now().isoformat()
        default_settings["retrieval"]["updated_at"] = now
        default_settings["cache"]["updated_at"] = now
        default_settings["cross_kb"]["updated_at"] = now
        
        # 保存设置
        await self._save_settings(default_settings)
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含缓存统计信息的字典
        """
        # 这里应该实现从缓存服务获取统计信息的逻辑
        # 目前返回模拟数据
        return {
            "total_entries": 325,
            "hit_rate": 0.68,
            "miss_rate": 0.32,
            "avg_response_time": 15.3,  # ms
            "memory_usage": 42.5,  # MB
            "oldest_entry": "2023-09-15T10:23:45",
            "newest_entry": "2023-09-16T14:56:12"
        }
    
    async def clear_cache(self):
        """
        清空缓存
        """
        # 这里应该实现清空缓存的逻辑
        # 目前只是记录日志
        logger.info("Cache cleared")
        return True