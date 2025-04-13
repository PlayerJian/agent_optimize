import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

logger = logging.getLogger("metrics")

def record_search_metrics(
    query: str,
    strategy: str,
    knowledge_base_ids: List[str],
    result_count: int,
    response_time: Optional[float] = None,
    cache_hit: bool = False,
    user_id: Optional[str] = None
):
    """
    记录搜索指标
    
    Args:
        query: 查询内容
        strategy: 检索策略
        knowledge_base_ids: 知识库ID列表
        result_count: 结果数量
        response_time: 响应时间(毫秒)
        cache_hit: 是否命中缓存
        user_id: 用户ID
    """
    try:
        # 这里可以实现将指标记录到数据库、日志或监控系统
        # 例如记录到日志
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "search",
            "query": query,
            "strategy": strategy,
            "knowledge_base_ids": knowledge_base_ids,
            "result_count": result_count,
            "response_time": response_time,
            "cache_hit": cache_hit,
            "user_id": user_id
        }
        
        logger.info(f"Search metrics: {log_data}")
        
        # TODO: 实现将指标发送到监控系统或存储到数据库
        
    except Exception as e:
        logger.error(f"Failed to record search metrics: {str(e)}", exc_info=True)

def record_feedback_metrics(
    result_id: str,
    feedback_type: str,
    user_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """
    记录反馈指标
    
    Args:
        result_id: 结果ID
        feedback_type: 反馈类型 (positive/negative)
        user_id: 用户ID
        details: 详细反馈信息
    """
    try:
        # 这里可以实现将反馈指标记录到数据库、日志或监控系统
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": "feedback",
            "result_id": result_id,
            "feedback_type": feedback_type,
            "user_id": user_id,
            "details": details
        }
        
        logger.info(f"Feedback metrics: {log_data}")
        
        # TODO: 实现将指标发送到监控系统或存储到数据库
        
    except Exception as e:
        logger.error(f"Failed to record feedback metrics: {str(e)}", exc_info=True)