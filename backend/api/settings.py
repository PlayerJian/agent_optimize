from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging

from services.settings_service import SettingsService
from models.settings import RetrievalSettings, CacheSettings, CrossKbSettings

router = APIRouter()
logger = logging.getLogger("retrieval")

# 获取服务实例
def get_settings_service():
    return SettingsService()

@router.get("/retrieval", response_model=RetrievalSettings)
async def get_retrieval_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """获取检索设置"""
    try:
        return await settings_service.get_retrieval_settings()
    except Exception as e:
        logger.error(f"Get retrieval settings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取检索设置失败: {str(e)}")

@router.put("/retrieval", response_model=RetrievalSettings)
async def update_retrieval_settings(
    settings: RetrievalSettings,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """更新检索设置"""
    try:
        return await settings_service.update_retrieval_settings(settings)
    except Exception as e:
        logger.error(f"Update retrieval settings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新检索设置失败: {str(e)}")

@router.get("/cache", response_model=CacheSettings)
async def get_cache_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """获取缓存设置"""
    try:
        return await settings_service.get_cache_settings()
    except Exception as e:
        logger.error(f"Get cache settings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取缓存设置失败: {str(e)}")

@router.put("/cache", response_model=CacheSettings)
async def update_cache_settings(
    settings: CacheSettings,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """更新缓存设置"""
    try:
        return await settings_service.update_cache_settings(settings)
    except Exception as e:
        logger.error(f"Update cache settings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新缓存设置失败: {str(e)}")

@router.get("/cross-kb", response_model=CrossKbSettings)
async def get_cross_kb_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """获取跨库检索设置"""
    try:
        return await settings_service.get_cross_kb_settings()
    except Exception as e:
        logger.error(f"Get cross-kb settings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取跨库检索设置失败: {str(e)}")

@router.put("/cross-kb", response_model=CrossKbSettings)
async def update_cross_kb_settings(
    settings: CrossKbSettings,
    settings_service: SettingsService = Depends(get_settings_service)
):
    """更新跨库检索设置"""
    try:
        return await settings_service.update_cross_kb_settings(settings)
    except Exception as e:
        logger.error(f"Update cross-kb settings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"更新跨库检索设置失败: {str(e)}")

@router.post("/reset", response_model=Dict[str, Any])
async def reset_settings(
    settings_service: SettingsService = Depends(get_settings_service)
):
    """重置所有设置为默认值"""
    try:
        await settings_service.reset_settings()
        return {"success": True, "message": "所有设置已重置为默认值"}
    except Exception as e:
        logger.error(f"Reset settings error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重置设置失败: {str(e)}")