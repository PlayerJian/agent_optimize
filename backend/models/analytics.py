from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PerformanceMetrics(BaseModel):
    """性能指标模型"""
    total_searches: int = Field(..., description="总搜索次数")
    avg_response_time: float = Field(..., description="平均响应时间(毫秒)")
    cache_hit_rate: float = Field(..., description="缓存命中率(%)")
    positive_feedback_rate: float = Field(..., description="正面反馈率(%)")
    time_range: str = Field(..., description="时间范围")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")

class TimeSeriesPoint(BaseModel):
    """时间序列数据点"""
    timestamp: str = Field(..., description="时间点")
    value: float = Field(..., description="数值")

class SearchTrend(BaseModel):
    """搜索趋势模型"""
    search_volume: List[TimeSeriesPoint] = Field(..., description="搜索量趋势")
    response_time: List[TimeSeriesPoint] = Field(..., description="响应时间趋势")
    time_range: str = Field(..., description="时间范围")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")

class StrategyUsage(BaseModel):
    """检索策略使用情况"""
    strategy: str = Field(..., description="检索策略")
    count: int = Field(..., description="使用次数")
    percentage: float = Field(..., description="使用百分比")

class SearchStrategyDistribution(BaseModel):
    """检索策略分布模型"""
    strategies: List[StrategyUsage] = Field(..., description="策略使用情况列表")
    time_range: str = Field(..., description="时间范围")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")

class FeedbackType(BaseModel):
    """反馈类型统计"""
    type: str = Field(..., description="反馈类型")
    count: int = Field(..., description="数量")
    percentage: float = Field(..., description="百分比")

class FeedbackDistribution(BaseModel):
    """反馈分布模型"""
    feedback_types: List[FeedbackType] = Field(..., description="反馈类型统计列表")
    positive_count: int = Field(..., description="正面反馈总数")
    negative_count: int = Field(..., description="负面反馈总数")
    positive_rate: float = Field(..., description="正面反馈率(%)")
    time_range: str = Field(..., description="时间范围")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")

class QueryCount(BaseModel):
    """查询次数统计"""
    query: str = Field(..., description="查询内容")
    count: int = Field(..., description="查询次数")

class TopQueries(BaseModel):
    """热门查询模型"""
    queries: List[QueryCount] = Field(..., description="查询次数统计列表")
    time_range: str = Field(..., description="时间范围")
    knowledge_base_id: Optional[str] = Field(None, description="知识库ID")

class UserBehaviorRecord(BaseModel):
    """用户行为记录模型"""
    id: str = Field(..., description="记录ID")
    user_id: Optional[str] = Field(None, description="用户ID")
    query: str = Field(..., description="查询内容")
    strategy: str = Field(..., description="检索策略")
    response_time: float = Field(..., description="响应时间(毫秒)")
    knowledge_base_ids: List[str] = Field(..., description="查询的知识库ID列表")
    result_count: int = Field(..., description="结果数量")
    feedback: Optional[str] = Field(None, description="反馈类型")
    timestamp: datetime = Field(..., description="时间戳")