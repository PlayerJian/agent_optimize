from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime, timedelta

from services.analytics_service import AnalyticsService
from models.analytics import (
    PerformanceMetrics, 
    UserBehaviorRecord, 
    SearchTrend, 
    FeedbackDistribution,
    SearchStrategyDistribution,
    TopQueries
)

router = APIRouter()
logger = logging.getLogger("retrieval")

# 获取服务实例
def get_analytics_service():
    return AnalyticsService()

@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    time_range: str = Query("week", description="时间范围: day, week, month, year"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID，不提供则查询所有知识库"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取检索性能指标
    
    返回指定时间范围内的检索性能指标，包括搜索量、平均响应时间、缓存命中率等
    """
    try:
        return await analytics_service.get_performance_metrics(time_range, knowledge_base_id)
    except Exception as e:
        logger.error(f"Get performance metrics error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")

@router.get("/search-trends", response_model=SearchTrend)
async def get_search_trends(
    time_range: str = Query("week", description="时间范围: day, week, month, year"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID，不提供则查询所有知识库"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取搜索趋势
    
    返回指定时间范围内的搜索量和响应时间趋势数据
    """
    try:
        return await analytics_service.get_search_trends(time_range, knowledge_base_id)
    except Exception as e:
        logger.error(f"Get search trends error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取搜索趋势失败: {str(e)}")

@router.get("/search-strategies", response_model=SearchStrategyDistribution)
async def get_search_strategy_distribution(
    time_range: str = Query("week", description="时间范围: day, week, month, year"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID，不提供则查询所有知识库"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取检索策略分布
    
    返回指定时间范围内各检索策略的使用比例
    """
    try:
        return await analytics_service.get_search_strategy_distribution(time_range, knowledge_base_id)
    except Exception as e:
        logger.error(f"Get search strategy distribution error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取检索策略分布失败: {str(e)}")

@router.get("/feedback", response_model=FeedbackDistribution)
async def get_feedback_distribution(
    time_range: str = Query("week", description="时间范围: day, week, month, year"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID，不提供则查询所有知识库"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取用户反馈分布
    
    返回指定时间范围内用户反馈的分布情况
    """
    try:
        return await analytics_service.get_feedback_distribution(time_range, knowledge_base_id)
    except Exception as e:
        logger.error(f"Get feedback distribution error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取用户反馈分布失败: {str(e)}")

@router.get("/top-queries", response_model=TopQueries)
async def get_top_queries(
    time_range: str = Query("week", description="时间范围: day, week, month, year"),
    limit: int = Query(10, description="返回结果数量"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID，不提供则查询所有知识库"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取热门查询
    
    返回指定时间范围内的热门查询及其次数
    """
    try:
        return await analytics_service.get_top_queries(time_range, limit, knowledge_base_id)
    except Exception as e:
        logger.error(f"Get top queries error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取热门查询失败: {str(e)}")

@router.get("/user-behavior", response_model=List[UserBehaviorRecord])
async def get_user_behavior(
    time_range: str = Query("day", description="时间范围: day, week, month"),
    limit: int = Query(100, description="返回结果数量"),
    knowledge_base_id: Optional[str] = Query(None, description="知识库ID，不提供则查询所有知识库"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """获取用户行为记录
    
    返回指定时间范围内的用户搜索和反馈行为记录
    """
    try:
        return await analytics_service.get_user_behavior(time_range, limit, knowledge_base_id)
    except Exception as e:
        logger.error(f"Get user behavior error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取用户行为记录失败: {str(e)}")