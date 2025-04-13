import logging
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
import json

import psycopg2
from psycopg2.extras import RealDictCursor

from models.feedback import Feedback
from services.analytics_service import AnalyticsService
from config import settings

logger = logging.getLogger("retrieval")

class FeedbackService:
    def __init__(self):
        # 连接到PostgreSQL数据库
        try:
            self.conn = psycopg2.connect(
                dbname=settings.POSTGRES_DB,
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT
            )
            logger.info(f"Connected to PostgreSQL at {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
            
            # 确保必要的表存在
            self._ensure_tables()
            
            # 初始化分析服务
            self.analytics_service = AnalyticsService()
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}", exc_info=True)
            # 如果连接失败，使用内存存储作为备用
            self.conn = None
            self.feedbacks = []
            
    def _ensure_tables(self):
        """确保必要的数据库表存在"""
        try:
            with self.conn.cursor() as cur:
                # 创建反馈表
                cur.execute("""
                CREATE TABLE IF NOT EXISTS feedbacks (
                    id VARCHAR(36) PRIMARY KEY,
                    result_id VARCHAR(36) NOT NULL,
                    feedback_type VARCHAR(20) NOT NULL,
                    rating FLOAT,
                    comment TEXT,
                    user_id VARCHAR(36),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                self.conn.commit()
                logger.info("Feedback table ensured")
                
        except Exception as e:
            logger.error(f"Ensure tables error: {str(e)}", exc_info=True)
            self.conn.rollback()
    
    async def save_feedback(self, result_id: str, feedback_type: str, user_id: Optional[str] = None) -> Feedback:
        """保存简单反馈（点赞/踩）"""
        try:
            # 创建反馈对象
            feedback_id = str(uuid.uuid4())
            created_at = datetime.now()
            
            feedback = Feedback(
                id=feedback_id,
                result_id=result_id,
                feedback_type=feedback_type,
                user_id=user_id,
                created_at=created_at
            )
            
            # 保存反馈到PostgreSQL数据库
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO feedbacks (id, result_id, feedback_type, user_id, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    """, (feedback_id, result_id, feedback_type, user_id, created_at))
                    self.conn.commit()
            else:
                # 如果数据库连接失败，使用内存存储作为备用
                self.feedbacks.append(feedback)
            
            # 记录分析数据
            await self.analytics_service.log_feedback(
                feedback_id=feedback_id,
                result_id=result_id,
                feedback_type=feedback_type,
                user_id=user_id
            )
            
            logger.info(f"Saved feedback: {feedback_type} for result {result_id}")
            return feedback
            
        except Exception as e:
            logger.error(f"Save feedback error: {str(e)}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            raise
    
    async def save_detailed_feedback(self, result_id: str, rating: float, feedback_type: str, comment: Optional[str] = None, user_id: Optional[str] = None) -> Feedback:
        """保存详细反馈（评分、类型和评论）"""
        try:
            # 创建反馈对象
            feedback_id = str(uuid.uuid4())
            created_at = datetime.now()
            
            feedback = Feedback(
                id=feedback_id,
                result_id=result_id,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                user_id=user_id,
                created_at=created_at
            )
            
            # 保存反馈到PostgreSQL数据库
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO feedbacks (id, result_id, feedback_type, rating, comment, user_id, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (feedback_id, result_id, feedback_type, rating, comment, user_id, created_at))
                    self.conn.commit()
            else:
                # 如果数据库连接失败，使用内存存储作为备用
                self.feedbacks.append(feedback)
            
            # 记录分析数据
            await self.analytics_service.log_feedback(
                feedback_id=feedback_id,
                result_id=result_id,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                user_id=user_id
            )
            
            logger.info(f"Saved detailed feedback: {feedback_type} with rating {rating} for result {result_id}")
            return feedback
            
        except Exception as e:
            logger.error(f"Save detailed feedback error: {str(e)}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            raise
    
    async def get_feedback(self, result_id: str) -> List[Feedback]:
        """获取特定结果的所有反馈"""
        try:
            # 从PostgreSQL数据库查询
            if self.conn:
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                    SELECT * FROM feedbacks
                    WHERE result_id = %s
                    ORDER BY created_at DESC
                    """, (result_id,))
                    
                    rows = cur.fetchall()
                    return [Feedback(**row) for row in rows]
            else:
                # 如果数据库连接失败，使用内存存储作为备用
                return [f for f in self.feedbacks if f.result_id == result_id]
            
        except Exception as e:
            logger.error(f"Get feedback error: {str(e)}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            raise
    
    async def get_feedback_stats(self, result_id: str) -> Dict[str, Any]:
        """获取特定结果的反馈统计信息"""
        try:
            if self.conn:
                with self.conn.cursor() as cur:
                    # 获取总数和正面/负面反馈数
                    cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN feedback_type IN ('like', 'relevant', 'partially') THEN 1 ELSE 0 END) as positive,
                        SUM(CASE WHEN feedback_type IN ('dislike', 'irrelevant', 'outdated', 'incomplete') THEN 1 ELSE 0 END) as negative,
                        AVG(rating) as avg_rating
                    FROM feedbacks
                    WHERE result_id = %s
                    """, (result_id,))
                    
                    result = cur.fetchone()
                    total = result[0] or 0
                    positive = result[1] or 0
                    negative = result[2] or 0
                    avg_rating = result[3]
                    
                    return {
                        "total": total,
                        "positive": positive,
                        "negative": negative,
                        "positive_rate": positive / total if total > 0 else 0,
                        "avg_rating": avg_rating
                    }
            else:
                # 如果数据库连接失败，使用内存存储作为备用
                feedbacks = await self.get_feedback(result_id)
                
                # 计算统计信息
                total = len(feedbacks)
                positive = sum(1 for f in feedbacks if f.feedback_type in ["like", "relevant", "partially"])
                negative = sum(1 for f in feedbacks if f.feedback_type in ["dislike", "irrelevant", "outdated", "incomplete"])
                avg_rating = sum(f.rating for f in feedbacks if f.rating is not None) / sum(1 for f in feedbacks if f.rating is not None) if any(f.rating is not None for f in feedbacks) else None
                
                return {
                    "total": total,
                    "positive": positive,
                    "negative": negative,
                    "positive_rate": positive / total if total > 0 else 0,
                    "avg_rating": avg_rating
                }
            
        except Exception as e:
            logger.error(f"Get feedback stats error: {str(e)}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            raise
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """删除反馈"""
        try:
            # 从PostgreSQL数据库删除
            if self.conn:
                with self.conn.cursor() as cur:
                    cur.execute("""
                    DELETE FROM feedbacks
                    WHERE id = %s
                    RETURNING id
                    """, (feedback_id,))
                    
                    deleted = cur.fetchone()
                    self.conn.commit()
                    return deleted is not None
            else:
                # 如果数据库连接失败，使用内存存储作为备用
                initial_count = len(self.feedbacks)
                self.feedbacks = [f for f in self.feedbacks if f.id != feedback_id]
                return len(self.feedbacks) < initial_count
            
        except Exception as e:
            logger.error(f"Delete feedback error: {str(e)}", exc_info=True)
            if self.conn:
                self.conn.rollback()
            raise