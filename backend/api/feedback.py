from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from services.feedback_service import FeedbackService
from models.feedback import FeedbackRequest, FeedbackResponse, DetailedFeedbackRequest
from utils.metrics import record_feedback_metrics

router = APIRouter()
logger = logging.getLogger("retrieval")

# 获取服务实例
def get_feedback_service():
    return FeedbackService()

@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(
    request: FeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """提交搜索结果反馈
    
    用户对搜索结果提交简单的点赞/踩反馈
    """
    try:
        result = await feedback_service.save_feedback(
            result_id=request.result_id,
            feedback_type=request.feedback_type,
            user_id=request.user_id
        )
        
        # 记录反馈指标
        record_feedback_metrics(
            result_id=request.result_id,
            feedback_type=request.feedback_type,
            user_id=request.user_id
        )
        
        return FeedbackResponse(
            success=True,
            message="反馈已保存",
            feedback_id=result.id
        )
        
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存反馈失败: {str(e)}")

@router.post("/detailed", response_model=FeedbackResponse)
async def submit_detailed_feedback(
    request: DetailedFeedbackRequest,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """提交详细反馈
    
    用户对搜索结果提交详细的反馈，包括评分、反馈类型和评论
    """
    try:
        result = await feedback_service.save_detailed_feedback(
            result_id=request.result_id,
            rating=request.rating,
            feedback_type=request.feedback_type,
            comment=request.comment,
            user_id=request.user_id
        )
        
        # 记录反馈指标
        record_feedback_metrics(
            result_id=request.result_id,
            feedback_type=request.feedback_type,
            user_id=request.user_id,
            rating=request.rating,
            has_comment=bool(request.comment)
        )
        
        return FeedbackResponse(
            success=True,
            message="详细反馈已保存",
            feedback_id=result.id
        )
        
    except Exception as e:
        logger.error(f"Detailed feedback error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"保存详细反馈失败: {str(e)}")

@router.get("/types", response_model=Dict[str, str])
async def get_feedback_types():
    """获取可用的反馈类型"""
    return {
        "relevant": "相关且有帮助",
        "partially": "部分相关",
        "irrelevant": "不相关",
        "outdated": "信息过时",
        "incomplete": "信息不完整",
        "other": "其他问题"
    }