from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from services.search_service import SearchService
from services.cache_service import CacheService
from models.search import SearchRequest, SearchResponse, SearchResult
from utils.metrics import record_search_metrics
from config import settings

router = APIRouter()
logger = logging.getLogger("retrieval")

# 获取服务实例
def get_search_service():
    return SearchService()

def get_cache_service():
    return CacheService()

@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    search_service: SearchService = Depends(get_search_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """执行知识库检索
    
    根据查询和参数执行知识库检索，支持多种检索策略和结果优化
    """
    start_time = datetime.now()
    query = request.query.strip()
    
    if not query:
        raise HTTPException(status_code=400, detail="查询内容不能为空")
    
    # 尝试从缓存获取结果
    if settings.REDIS_CACHE_EXPIRE > 0:
        cache_key = f"search:{query}:{request.strategy}:{','.join(request.knowledge_base_ids)}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for query: {query}")
            # 记录指标
            record_search_metrics(
                query=query,
                strategy=request.strategy,
                knowledge_base_ids=request.knowledge_base_ids,
                result_count=len(cached_result.results),
                response_time=(datetime.now() - start_time).total_seconds(),
                cache_hit=True
            )
            return cached_result
    
    # 执行检索
    try:
        results = await search_service.search(
            query=query,
            knowledge_base_ids=request.knowledge_base_ids,
            strategy=request.strategy,
            semantic_weight=request.semantic_weight,
            fulltext_weight=request.fulltext_weight,
            max_results=request.max_results,
            min_score=request.min_score,
            use_reranking=request.use_reranking,
            use_clustering=request.use_clustering
        )
        
        # 构建响应
        response = SearchResponse(
            query=query,
            results=results,
            strategy_used=search_service.strategy_used,
            total_found=len(results),
            clusters=search_service.clusters if request.use_clustering else [],
            response_time=(datetime.now() - start_time).total_seconds()
        )
        
        # 缓存结果
        if settings.REDIS_CACHE_EXPIRE > 0:
            await cache_service.set(cache_key, response, settings.REDIS_CACHE_EXPIRE)
        
        # 记录指标
        record_search_metrics(
            query=query,
            strategy=request.strategy,
            knowledge_base_ids=request.knowledge_base_ids,
            result_count=len(results),
            response_time=response.response_time,
            cache_hit=False
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检索失败: {str(e)}")

@router.get("/strategies", response_model=Dict[str, str])
async def get_search_strategies():
    """获取可用的检索策略"""
    return {
        "auto": "智能选择",
        "semantic": "语义检索",
        "fulltext": "全文检索",
        "hybrid": "混合检索"
    }