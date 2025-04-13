from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FeedbackRequest(BaseModel):
    """反馈请求模型"""
    result_id: str = Field(..., description="搜索结果ID")
    feedback_type: str = Field(..., description="反馈类型: like, dislike")
    user_id: Optional[str] = Field(None, description="用户ID")

class DetailedFeedbackRequest(BaseModel):
    """详细反馈请求模型"""
    result_id: str = Field(..., description="搜索结果ID")
    rating: float = Field(..., description="评分 (1-5)")
    feedback_type: str = Field(..., description="反馈类型: relevant, partially, irrelevant, outdated, incomplete, other")
    comment: Optional[str] = Field(None, description="评论")
    user_id: Optional[str] = Field(None, description="用户ID")

class FeedbackResponse(BaseModel):
    """反馈响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    feedback_id: Optional[str] = Field(None, description="反馈ID")

class Feedback(BaseModel):
    """反馈模型"""
    id: str = Field(..., description="反馈ID")
    result_id: str = Field(..., description="搜索结果ID")
    feedback_type: str = Field(..., description="反馈类型")
    rating: Optional[float] = Field(None, description="评分 (1-5)")
    comment: Optional[str] = Field(None, description="评论")
    user_id: Optional[str] = Field(None, description="用户ID")
    created_at: datetime = Field(..., description="创建时间")