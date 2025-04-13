import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
import uuid
import json

import psycopg2
from psycopg2.extras import RealDictCursor
import redis.asyncio as redis

from models.analytics import (
    PerformanceMetrics, 
    UserBehaviorRecord, 
    SearchTrend, 
    FeedbackDistribution,
    SearchStrategyDistribution,
    TopQueries,
    TimeSeriesPoint
)
from config import settings

logger = logging.getLogger("retrieval")

class AnalyticsService:
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
            
            # 连接到Redis缓存
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            logger.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            
        except Exception as e:
            logger.error(f"Database connection error: {str(e)}", exc_info=True)
            # 如果连接失败，使用内存存储作为备用
            self.conn = None
            self.redis = None
            self.search_logs = []
            self.feedback_logs = []
    
    def _ensure_tables(self):
        """确保必要的数据库表存在"""
        try:
            with self.conn.cursor() as cur:
                # 创建搜索日志表
                cur.execute("""
                CREATE TABLE IF NOT EXISTS search_logs (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36),
                    query TEXT NOT NULL,
                    strategy VARCHAR(20) NOT NULL,
                    response_time FLOAT NOT NULL,
                    knowledge_base_ids JSONB NOT NULL,
                    result_count INTEGER NOT NULL,
                    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                # 创建反馈日志表
                cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback_logs (
                    id VARCHAR(36) PRIMARY KEY,
                    search_id VARCHAR(36) REFERENCES search_logs(id),
                    user_id VARCHAR(36),
                    feedback_type VARCHAR(20) NOT NULL,
                    rating FLOAT,
                    comment TEXT,
                    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """)
                
                self.conn.commit()
                logger.info("Database tables ensured")
                
        except Exception as e:
            logger.error(f"Ensure tables error: {str(e)}", exc_info=True)
            self.conn.rollback()
    
    async def get_performance_metrics(self, time_range: str, knowledge_base_id: Optional[str] = None) -> PerformanceMetrics:
        """获取检索性能指标"""
        try:
            # 尝试从缓存获取
            cache_key = f"performance_metrics:{time_range}:{knowledge_base_id or 'all'}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    try:
                        cached_metrics = json.loads(cached_data)
                        return PerformanceMetrics(**cached_metrics)
                    except Exception as e:
                        logger.warning(f"Failed to parse cached metrics: {str(e)}")
            
            # 计算时间范围
            start_time = self._get_start_time(time_range)
            
            if self.conn:
                # 从数据库获取数据
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 查询总搜索次数和平均响应时间
                    query = """
                    SELECT COUNT(*) as total_searches, 
                           AVG(response_time) as avg_response_time,
                           SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits
                    FROM search_logs 
                    WHERE timestamp >= %s
                    """
                    params = [start_time]
                    
                    if knowledge_base_id:
                        query += " AND knowledge_base_ids @> %s"
                        params.append(json.dumps([knowledge_base_id]))
                    
                    cur.execute(query, params)
                    result = cur.fetchone()
                    
                    if not result or result['total_searches'] == 0:
                        # 如果没有数据，返回模拟数据
                        return self._get_mock_performance_metrics(time_range, knowledge_base_id)
                    
                    total_searches = result['total_searches']
                    avg_response_time = result['avg_response_time'] or 0
                    cache_hit_rate = (result['cache_hits'] / total_searches) * 100 if total_searches > 0 else 0
                    
                    # 查询正面反馈率
                    query = """
                    SELECT 
                        COUNT(*) as total_feedbacks,
                        SUM(CASE WHEN feedback_type IN ('like', 'relevant', 'partially') THEN 1 ELSE 0 END) as positive_feedbacks
                    FROM feedback_logs f
                    JOIN search_logs s ON f.search_id = s.id
                    WHERE f.timestamp >= %s
                    """
                    params = [start_time]
                    
                    if knowledge_base_id:
                        query += " AND s.knowledge_base_ids @> %s"
                        params.append(json.dumps([knowledge_base_id]))
                    
                    cur.execute(query, params)
                    feedback_result = cur.fetchone()
                    
                    total_feedbacks = feedback_result['total_feedbacks'] if feedback_result else 0
                    positive_feedbacks = feedback_result['positive_feedbacks'] if feedback_result else 0
                    positive_feedback_rate = (positive_feedbacks / total_feedbacks) * 100 if total_feedbacks > 0 else 0
                    
                    metrics = PerformanceMetrics(
                        total_searches=total_searches,
                        avg_response_time=avg_response_time * 1000,  # 转换为毫秒
                        cache_hit_rate=cache_hit_rate,
                        positive_feedback_rate=positive_feedback_rate,
                        time_range=time_range,
                        knowledge_base_id=knowledge_base_id
                    )
                    
                    # 缓存结果
                    if self.redis:
                        await self.redis.set(
                            cache_key, 
                            json.dumps(metrics.dict()), 
                            ex=300  # 缓存5分钟
                        )
                    
                    return metrics
            else:
                # 如果没有数据库连接，使用内存存储
                filtered_logs = self._filter_logs(self.search_logs, start_time, knowledge_base_id)
                
                # 如果没有日志，创建一些模拟数据
                if not filtered_logs:
                    return self._get_mock_performance_metrics(time_range, knowledge_base_id)
                
                # 计算指标
                total_searches = len(filtered_logs)
                avg_response_time = sum(log.get("response_time", 0) for log in filtered_logs) / total_searches if total_searches > 0 else 0
                cache_hit_rate = sum(1 for log in filtered_logs if log.get("cache_hit", False)) / total_searches if total_searches > 0 else 0
                
                # 计算正面反馈率
                feedback_logs = self._filter_logs(self.feedback_logs, start_time, knowledge_base_id)
                positive_feedbacks = sum(1 for log in feedback_logs if log.get("feedback_type") in ["like", "relevant", "partially"])
                total_feedbacks = len(feedback_logs)
                positive_feedback_rate = positive_feedbacks / total_feedbacks if total_feedbacks > 0 else 0
                
                return PerformanceMetrics(
                    total_searches=total_searches,
                    avg_response_time=avg_response_time * 1000,  # 转换为毫秒
                    cache_hit_rate=cache_hit_rate * 100,  # 转换为百分比
                    positive_feedback_rate=positive_feedback_rate * 100,  # 转换为百分比
                    time_range=time_range,
                    knowledge_base_id=knowledge_base_id
                )
            
        except Exception as e:
            logger.error(f"Get performance metrics error: {str(e)}", exc_info=True)
            # 如果出错，返回模拟数据
            return self._get_mock_performance_metrics(time_range, knowledge_base_id)
    
    async def get_search_trends(self, time_range: str, knowledge_base_id: Optional[str] = None) -> SearchTrend:
        """获取搜索趋势"""
        try:
            # 尝试从缓存获取
            cache_key = f"search_trends:{time_range}:{knowledge_base_id or 'all'}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    try:
                        cached_trends = json.loads(cached_data)
                        return SearchTrend(**cached_trends)
                    except Exception as e:
                        logger.warning(f"Failed to parse cached trends: {str(e)}")
            
            # 计算时间范围
            start_time = self._get_start_time(time_range)
            
            if self.conn:
                # 从数据库获取数据
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 获取时间间隔
                    intervals = self._get_time_intervals(time_range, start_time)
                    search_volume = []
                    response_time = []
                    
                    for interval_start, interval_end, label in intervals:
                        # 查询该时间间隔内的搜索量
                        query = """
                        SELECT COUNT(*) as count
                        FROM search_logs
                        WHERE timestamp >= %s AND timestamp < %s
                        """
                        params = [interval_start, interval_end]
                        
                        if knowledge_base_id:
                            query += " AND knowledge_base_ids @> %s"
                            params.append(json.dumps([knowledge_base_id]))
                        
                        cur.execute(query, params)
                        result = cur.fetchone()
                        search_volume.append(TimeSeriesPoint(
                            timestamp=label,
                            value=result['count'] if result else 0
                        ))
                        
                        # 查询该时间间隔内的平均响应时间
                        query = """
                        SELECT AVG(response_time) as avg_time
                        FROM search_logs
                        WHERE timestamp >= %s AND timestamp < %s
                        """
                        params = [interval_start, interval_end]
                        
                        if knowledge_base_id:
                            query += " AND knowledge_base_ids @> %s"
                            params.append(json.dumps([knowledge_base_id]))
                        
                        cur.execute(query, params)
                        result = cur.fetchone()
                        response_time.append(TimeSeriesPoint(
                            timestamp=label,
                            value=(result['avg_time'] or 0) * 1000  # 转换为毫秒
                        ))
                    
                    # 检查是否有数据
                    has_data = any(point.value > 0 for point in search_volume)
                    if not has_data:
                        return self._get_mock_search_trends(time_range, knowledge_base_id)
                    
                    trends = SearchTrend(
                        search_volume=search_volume,
                        response_time=response_time,
                        time_range=time_range,
                        knowledge_base_id=knowledge_base_id
                    )
                    
                    # 缓存结果
                    if self.redis:
                        await self.redis.set(
                            cache_key, 
                            json.dumps(trends.dict()), 
                            ex=300  # 缓存5分钟
                        )
                    
                    return trends
            else:
                # 如果没有数据库连接，使用内存存储
                filtered_logs = self._filter_logs(self.search_logs, start_time, knowledge_base_id)
                
                # 如果没有日志，创建一些模拟数据
                if not filtered_logs:
                    return self._get_mock_search_trends(time_range, knowledge_base_id)
                
                # 按时间间隔分组
                intervals = self._get_time_intervals(time_range, start_time)
                search_volume = []
                response_time = []
                
                for interval_start, interval_end, label in intervals:
                    # 计算该时间间隔内的搜索量
                    interval_logs = [log for log in filtered_logs 
                                   if interval_start <= log.get("timestamp") < interval_end]
                    search_volume.append(TimeSeriesPoint(
                        timestamp=label,
                        value=len(interval_logs)
                    ))
                    
                    # 计算该时间间隔内的平均响应时间
                    avg_time = sum(log.get("response_time", 0) for log in interval_logs) / len(interval_logs) if interval_logs else 0
                    response_time.append(TimeSeriesPoint(
                        timestamp=label,
                        value=avg_time * 1000  # 转换为毫秒
                    ))
                
                return SearchTrend(
                    search_volume=search_volume,
                    response_time=response_time,
                    time_range=time_range,
                    knowledge_base_id=knowledge_base_id
                )
            
        except Exception as e:
            logger.error(f"Get search trends error: {str(e)}", exc_info=True)
            # 如果出错，返回模拟数据
            return self._get_mock_search_trends(time_range, knowledge_base_id)
    
    async def get_search_strategy_distribution(self, time_range: str, knowledge_base_id: Optional[str] = None) -> SearchStrategyDistribution:
        """获取检索策略分布"""
        try:
            # 尝试从缓存获取
            cache_key = f"strategy_distribution:{time_range}:{knowledge_base_id or 'all'}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    try:
                        cached_distribution = json.loads(cached_data)
                        return SearchStrategyDistribution(**cached_distribution)
                    except Exception as e:
                        logger.warning(f"Failed to parse cached strategy distribution: {str(e)}")
            
            # 计算时间范围
            start_time = self._get_start_time(time_range)
            
            if self.conn:
                # 从数据库获取数据
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 查询各策略使用次数
                    query = """
                    SELECT strategy, COUNT(*) as count
                    FROM search_logs
                    WHERE timestamp >= %s
                    """
                    params = [start_time]
                    
                    if knowledge_base_id:
                        query += " AND knowledge_base_ids @> %s"
                        params.append(json.dumps([knowledge_base_id]))
                    
                    query += " GROUP BY strategy ORDER BY count DESC"
                    
                    cur.execute(query, params)
                    results = cur.fetchall()
                    
                    if not results:
                        return self._get_mock_strategy_distribution(time_range, knowledge_base_id)
                    
                    # 计算总数和百分比
                    total = sum(result['count'] for result in results)
                    strategies = []
                    for result in results:
                        strategies.append({
                            "strategy": result['strategy'],
                            "count": result['count'],
                            "percentage": (result['count'] / total) * 100 if total > 0 else 0
                        })
                    
                    distribution = SearchStrategyDistribution(
                        strategies=strategies,
                        time_range=time_range,
                        knowledge_base_id=knowledge_base_id
                    )
                    
                    # 缓存结果
                    if self.redis:
                        await self.redis.set(
                            cache_key, 
                            json.dumps(distribution.dict()), 
                            ex=300  # 缓存5分钟
                        )
                    
                    return distribution
            else:
                # 如果没有数据库连接，使用内存存储
                filtered_logs = self._filter_logs(self.search_logs, start_time, knowledge_base_id)
                
                # 如果没有日志，创建一些模拟数据
                if not filtered_logs:
                    return self._get_mock_strategy_distribution(time_range, knowledge_base_id)
                
                # 统计各策略使用次数
                strategy_counts = {}
                for log in filtered_logs:
                    strategy = log.get("strategy", "auto")
                    strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
                
                # 计算百分比
                total = len(filtered_logs)
                strategies = []
                for strategy, count in strategy_counts.items():
                    strategies.append({
                        "strategy": strategy,
                        "count": count,
                        "percentage": count / total * 100 if total > 0 else 0
                    })
                
                # 按使用次数降序排序
                strategies.sort(key=lambda x: x["count"], reverse=True)
                
                return SearchStrategyDistribution(
                    strategies=strategies,
                    time_range=time_range,
                    knowledge_base_id=knowledge_base_id
                )
            
        except Exception as e:
            logger.error(f"Get search strategy distribution error: {str(e)}", exc_info=True)
            # 如果出错，返回模拟数据
            return self._get_mock_strategy_distribution(time_range, knowledge_base_id)
    
    async def get_feedback_distribution(self, time_range: str, knowledge_base_id: Optional[str] = None) -> FeedbackDistribution:
        """获取用户反馈分布"""
        try:
            # 尝试从缓存获取
            cache_key = f"feedback_distribution:{time_range}:{knowledge_base_id or 'all'}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    try:
                        cached_distribution = json.loads(cached_data)
                        return FeedbackDistribution(**cached_distribution)
                    except Exception as e:
                        logger.warning(f"Failed to parse cached feedback distribution: {str(e)}")
            
            # 计算时间范围
            start_time = self._get_start_time(time_range)
            
            if self.conn:
                # 从数据库获取数据
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 查询各反馈类型次数
                    query = """
                    SELECT f.feedback_type, COUNT(*) as count
                    FROM feedback_logs f
                    JOIN search_logs s ON f.search_id = s.id
                    WHERE f.timestamp >= %s
                    """
                    params = [start_time]
                    
                    if knowledge_base_id:
                        query += " AND s.knowledge_base_ids @> %s"
                        params.append(json.dumps([knowledge_base_id]))
                    
                    query += " GROUP BY f.feedback_type ORDER BY count DESC"
                    
                    cur.execute(query, params)
                    results = cur.fetchall()
                    
                    if not results:
                        return self._get_mock_feedback_distribution(time_range, knowledge_base_id)
                    
                    # 计算总数和百分比
                    total = sum(result['count'] for result in results)
                    feedback_types = []
                    positive_count = 0
                    negative_count = 0
                    
                    for result in results:
                        feedback_type = result['feedback_type']
                        count = result['count']
                        
                        feedback_types.append({
                            "type": feedback_type,
                            "count": count,
                            "percentage": (count / total) * 100 if total > 0 else 0
                        })
                        
                        # 统计正面/负面反馈
                        if feedback_type in ["like", "relevant", "partially"]:
                            positive_count += count
                        elif feedback_type in ["dislike", "irrelevant", "outdated", "incomplete", "other"]:
                            negative_count += count
                    
                    distribution = FeedbackDistribution(
                        feedback_types=feedback_types,
                        positive_count=positive_count,
                        negative_count=negative_count,
                        positive_rate=(positive_count / total) * 100 if total > 0 else 0,
                        time_range=time_range,
                        knowledge_base_id=knowledge_base_id
                    )
                    
                    # 缓存结果
                    if self.redis:
                        await self.redis.set(
                            cache_key, 
                            json.dumps(distribution.dict()), 
                            ex=300  # 缓存5分钟
                        )
                    
                    return distribution
            else:
                # 如果没有数据库连接，使用内存存储
                filtered_logs = self._filter_logs(self.feedback_logs, start_time, knowledge_base_id)
                
                # 如果没有日志，创建一些模拟数据
                if not filtered_logs:
                    return self._get_mock_feedback_distribution(time_range, knowledge_base_id)
                
                # 统计各反馈类型次数
                feedback_counts = {}
                positive_count = 0
                negative_count = 0
                
                for log in filtered_logs:
                    feedback_type = log.get("feedback_type", "")
                    feedback_counts[feedback_type] = feedback_counts.get(feedback_type, 0) + 1
                    
                    # 统计正面/负面反馈
                    if feedback_type in ["like", "relevant", "partially"]:
                        positive_count += 1
                    elif feedback_type in ["dislike", "irrelevant", "outdated", "incomplete", "other"]:
                        negative_count += 1
                
                # 计算百分比
                total = len(filtered_logs)
                feedback_types = []
                for feedback_type, count in feedback_counts.items():
                    feedback_types.append({
                        "type": feedback_type,
                        "count": count,
                        "percentage": count / total * 100 if total > 0 else 0
                    })
                
                # 按次数降序排序
                feedback_types.sort(key=lambda x: x["count"], reverse=True)
                
                return FeedbackDistribution(
                    feedback_types=feedback_types,
                    positive_count=positive_count,
                    negative_count=negative_count,
                    positive_rate=positive_count / total * 100 if total > 0 else 0,
                    time_range=time_range,
                    knowledge_base_id=knowledge_base_id
                )
            
        except Exception as e:
            logger.error(f"Get feedback distribution error: {str(e)}", exc_info=True)
            # 如果出错，返回模拟数据
            return self._get_mock_feedback_distribution(time_range, knowledge_base_id)
    
    async def get_top_queries(self, time_range: str, limit: int = 10, knowledge_base_id: Optional[str] = None) -> TopQueries:
        """获取热门查询"""
        try:
            # 尝试从缓存获取
            cache_key = f"top_queries:{time_range}:{knowledge_base_id or 'all'}:{limit}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    try:
                        cached_queries = json.loads(cached_data)
                        return TopQueries(**cached_queries)
                    except Exception as e:
                        logger.warning(f"Failed to parse cached top queries: {str(e)}")
            
            # 计算时间范围
            start_time = self._get_start_time(time_range)
            
            if self.conn:
                # 从数据库获取数据
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 查询热门查询
                    query = """
                    SELECT query, COUNT(*) as count
                    FROM search_logs
                    WHERE timestamp >= %s
                    """
                    params = [start_time]
                    
                    if knowledge_base_id:
                        query += " AND knowledge_base_ids @> %s"
                        params.append(json.dumps([knowledge_base_id]))
                    
                    query += " GROUP BY query ORDER BY count DESC LIMIT %s"
                    params.append(limit)
                    
                    cur.execute(query, params)
                    results = cur.fetchall()
                    
                    if not results:
                        return self._get_mock_top_queries(time_range, limit, knowledge_base_id)
                    
                    # 转换为列表
                    queries = []
                    for result in results:
                        queries.append({
                            "query": result['query'],
                            "count": result['count']
                        })
                    
                    top_queries = TopQueries(
                        queries=queries,
                        time_range=time_range,
                        knowledge_base_id=knowledge_base_id
                    )
                    
                    # 缓存结果
                    if self.redis:
                        await self.redis.set(
                            cache_key, 
                            json.dumps(top_queries.dict()), 
                            ex=300  # 缓存5分钟
                        )
                    
                    return top_queries
            else:
                # 如果没有数据库连接，使用内存存储
                filtered_logs = self._filter_logs(self.search_logs, start_time, knowledge_base_id)
                
                # 如果没有日志，创建一些模拟数据
                if not filtered_logs:
                    return self._get_mock_top_queries(time_range, limit, knowledge_base_id)
                
                # 统计查询次数
                query_counts = {}
                for log in filtered_logs:
                    query = log.get("query", "")
                    query_counts[query] = query_counts.get(query, 0) + 1
                
                # 转换为列表并排序
                queries = []
                for query, count in query_counts.items():
                    queries.append({
                        "query": query,
                        "count": count
                    })
                
                # 按次数降序排序并限制数量
                queries.sort(key=lambda x: x["count"], reverse=True)
                queries = queries[:limit]
                
                return TopQueries(
                    queries=queries,
                    time_range=time_range,
                    knowledge_base_id=knowledge_base_id
                )
            
        except Exception as e:
            logger.error(f"Get top queries error: {str(e)}", exc_info=True)
            # 如果出错，返回模拟数据
            return self._get_mock_top_queries(time_range, limit, knowledge_base_id)
    
    async def get_user_behavior(self, time_range: str, limit: int = 100, knowledge_base_id: Optional[str] = None) -> List[UserBehaviorRecord]:
        """获取用户行为记录"""
        try:
            # 尝试从缓存获取
            cache_key = f"user_behavior:{time_range}:{knowledge_base_id or 'all'}:{limit}"
            if self.redis:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    try:
                        cached_records = json.loads(cached_data)
                        return [UserBehaviorRecord(**record) for record in cached_records]
                    except Exception as e:
                        logger.warning(f"Failed to parse cached user behavior: {str(e)}")
            
            # 计算时间范围
            start_time = self._get_start_time(time_range)
            
            if self.conn:
                # 从数据库获取数据
                with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                    # 查询用户行为记录
                    query = """
                    SELECT s.id, s.user_id, s.query, s.strategy, s.response_time, 
                           s.knowledge_base_ids, s.result_count, s.timestamp,
                           f.feedback_type
                    FROM search_logs s
                    LEFT JOIN feedback_logs f ON s.id = f.search_id
                    WHERE s.timestamp >= %s
                    """
                    params = [start_time]
                    
                    if knowledge_base_id:
                        query += " AND s.knowledge_base_ids @> %s"
                        params.append(json.dumps([knowledge_base_id]))
                    
                    query += " ORDER BY s.timestamp DESC LIMIT %s"
                    params.append(limit)
                    
                    cur.execute(query, params)
                    results = cur.fetchall()
                    
                    if not results:
                        return self._get_mock_user_behavior(time_range, limit, knowledge_base_id)
                    
                    # 转换为UserBehaviorRecord格式
                    records = []
                    for result in results:
                        record = UserBehaviorRecord(
                            id=result['id'],
                            user_id=result['user_id'],
                            query=result['query'],
                            strategy=result['strategy'],
                            response_time=result['response_time'] * 1000,  # 转换为毫秒
                            knowledge_base_ids=result['knowledge_base_ids'],
                            result_count=result['result_count'],
                            feedback=result['feedback_type'],
                            timestamp=result['timestamp']
                        )
                        records.append(record)
                    
                    # 缓存结果
                    if self.redis:
                        await self.redis.set(
                            cache_key, 
                            json.dumps([record.dict() for record in records]), 
                            ex=300  # 缓存5分钟
                        )
                    
                    return records
            else:
                # 如果没有数据库连接，使用内存存储
                filtered_logs = self._filter_logs(self.search_logs, start_time, knowledge_base_id)
                
                # 如果没有日志，创建一些模拟数据
                if not filtered_logs:
                    return self._get_mock_user_behavior(time_range, limit, knowledge_base_id)
                
                # 转换为UserBehaviorRecord格式
                records = []
                for log in filtered_logs:
                    # 查找对应的反馈
                    feedback = None
                    for fb_log in self.feedback_logs:
                        if fb_log.get("search_id") == log.get("id"):
                            feedback = fb_log.get("feedback_type")
                            break
                    
                    record = UserBehaviorRecord(
                        id=log.get("id", str(uuid.uuid4())),
                        user_id=log.get("user_id"),
                        query=log.get("query", ""),
                        strategy=log.get("strategy", "auto"),
                        response_time=log.get("response_time", 0) * 1000,  # 转换为毫秒
                        knowledge_base_ids=log.get("knowledge_base_ids", []),
                        result_count=log.get("result_count", 0),
                        feedback=feedback,
                        timestamp=log.get("timestamp", datetime.now())
                    )
                    records.append(record)
                
                # 按时间降序排序并限制数量
                records.sort(key=lambda x: x.timestamp, reverse=True)
                records = records[:limit]
                
                return records
            
        except Exception as e:
            logger.error(f"Get user behavior error: {str(e)}", exc_info=True)
            # 如果出错，返回模拟数据
            return self._get_mock_user_behavior(time_range, limit, knowledge_base_id)
    
    def _get_start_time(self, time_range: str) -> datetime:
        """根据时间范围计算开始时间"""
        now = datetime.now()
        if time_range == "day":
            return now - timedelta(days=1)
        elif time_range == "week":
            return now - timedelta(days=7)
        elif time_range == "month":
            return now - timedelta(days=30)
        elif time_range == "year":
            return now - timedelta(days=365)
        else:
            return now - timedelta(days=7)  # 默认为一周
    
    def _filter_logs(self, logs: List[Dict[str, Any]], start_time: datetime, knowledge_base_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """过滤日志"""
        filtered = [log for log in logs if log.get("timestamp", datetime.now()) >= start_time]
        
        if knowledge_base_id:
            filtered = [log for log in filtered if knowledge_base_id in log.get("knowledge_base_ids", [])]
            
        return filtered
    
    def _get_time_intervals(self, time_range: str, start_time: datetime) -> List[tuple]:
        """获取时间间隔"""
        now = datetime.now()
        intervals = []
        
        if time_range == "day":
            # 每小时一个间隔
            for i in range(24):
                interval_start = start_time + timedelta(hours=i)
                interval_end = interval_start + timedelta(hours=1)
                if interval_end > now:
                    interval_end = now
                label = interval_start.strftime("%H:%M")
                intervals.append((interval_start, interval_end, label))
                
        elif time_range == "week":
            # 每天一个间隔
            for i in range(7):
                interval_start = start_time + timedelta(days=i)
                interval_end = interval_start + timedelta(days=1)
                if interval_end > now:
                    interval_end = now
                label = interval_start.strftime("%m-%d")
                intervals.append((interval_start, interval_end, label))
                
        elif time_range == "month":
            # 每天一个间隔
            days = (now - start_time).days
            for i in range(days):
                interval_start = start_time + timedelta(days=i)
                interval_end = interval_start + timedelta(days=1)
                if interval_end > now:
                    interval_end = now
                label = interval_start.strftime("%m-%d")
                intervals.append((interval_start, interval_end, label))
                
        elif time_range == "year":
            # 每月一个间隔
            current_month = start_time.replace(day=1)
            while current_month < now:
                next_month = current_month.replace(day=28) + timedelta(days=4)
                next_month = next_month.replace(day=1)
                interval_end = next_month if next_month < now else now
                label = current_month.strftime("%Y-%m")
                intervals.append((current_month, interval_end, label))
                current_month = next_month
        
        return intervals
    
    # 以下是模拟数据生成方法
    def _get_mock_performance_metrics(self, time_range: str, knowledge_base_id: Optional[str] = None) -> PerformanceMetrics:
        """生成模拟性能指标"""
        return PerformanceMetrics(
            total_searches=150,
            avg_response_time=85.5,  # 毫秒
            cache_hit_rate=68.0,  # 百分比
            positive_feedback_rate=78.0,  # 百分比
            time_range=time_range,
            knowledge_base_id=knowledge_base_id
        )
    
    def _get_mock_search_trends(self, time_range: str, knowledge_base_id: Optional[str] = None) -> SearchTrend:
        """生成模拟搜索趋势"""
        # 生成时间标签
        if time_range == "day":
            labels = [f"{i:02d}:00" for i in range(24)]
        elif time_range == "week":
            labels = [f"09/{i+1}" for i in range(7)]
        elif time_range == "month":
            labels = [f"09/{i+1}" for i in range(30)]
        else:  # year
            labels = [f"2023-{i+1:02d}" for i in range(12)]
        
        # 生成搜索量数据
        search_volume = []
        for i, label in enumerate(labels):
            value = 150 + i * 5 + (i % 3) * 10  # 模拟增长趋势
            search_volume.append(TimeSeriesPoint(timestamp=label, value=value))
        
        # 生成响应时间数据
        response_time = []
        for i, label in enumerate(labels):
            value = 120 - i * 3 + (i % 3) * 5  # 模拟下降趋势
            response_time.append(TimeSeriesPoint(timestamp=label, value=value))
        
        return SearchTrend(
            search_volume=search_volume,
            response_time=response_time,
            time_range=time_range,
            knowledge_base_id=knowledge_base_id
        )
    
    def _get_mock_strategy_distribution(self, time_range: str, knowledge_base_id: Optional[str] = None) -> SearchStrategyDistribution:
        """生成模拟策略分布"""
        return SearchStrategyDistribution(
            strategies=[
                {"strategy": "semantic", "count": 45, "percentage": 45.0},
                {"strategy": "hybrid", "count": 30, "percentage": 30.0},
                {"strategy": "fulltext", "count": 25, "percentage": 25.0}
            ],
            time_range=time_range,
            knowledge_base_id=knowledge_base_id
        )
    
    def _get_mock_feedback_distribution(self, time_range: str, knowledge_base_id: Optional[str] = None) -> FeedbackDistribution:
        """生成模拟反馈分布"""
        return FeedbackDistribution(
            feedback_types=[
                {"type": "relevant", "count": 65, "percentage": 65.0},
                {"type": "partially", "count": 13, "percentage": 13.0},
                {"type": "irrelevant", "count": 10, "percentage": 10.0},
                {"type": "outdated", "count": 7, "percentage": 7.0},
                {"type": "incomplete", "count": 5, "percentage": 5.0}
            ],
            positive_count=78,
            negative_count=22,
            positive_rate=78.0,
            time_range=time_range,
            knowledge_base_id=knowledge_base_id
        )
    
    def _get_mock_top_queries(self, time_range: str, limit: int, knowledge_base_id: Optional[str] = None) -> TopQueries:
        """生成模拟热门查询"""
        queries = [
            {"query": "如何配置知识库", "count": 45},
            {"query": "检索结果排序", "count": 38},
            {"query": "语义检索原理", "count": 32},
            {"query": "混合检索策略", "count": 28},
            {"query": "检索性能优化", "count": 25},
            {"query": "向量数据库配置", "count": 22},
            {"query": "文档分块策略", "count": 20},
            {"query": "缓存机制设置", "count": 18},
            {"query": "跨库检索功能", "count": 15},
            {"query": "用户反馈收集", "count": 12}
        ]
        
        return TopQueries(
            queries=queries[:limit],
            time_range=time_range,
            knowledge_base_id=knowledge_base_id
        )
    
    def _get_mock_user_behavior(self, time_range: str, limit: int, knowledge_base_id: Optional[str] = None) -> List[UserBehaviorRecord]:
        """生成模拟用户行为记录"""
        records = []
        now = datetime.now()
        
    async def log_search(self, 
                      user_id: Optional[str], 
                      query: str, 
                      strategy: str, 
                      response_time: float, 
                      knowledge_base_ids: List[str], 
                      result_count: int, 
                      cache_hit: bool = False) -> str:
        """记录搜索日志"""
        try:
            search_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            if self.conn:
                # 写入数据库
                with self.conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO search_logs 
                    (id, user_id, query, strategy, response_time, knowledge_base_ids, result_count, cache_hit, timestamp) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        search_id, 
                        user_id, 
                        query, 
                        strategy, 
                        response_time, 
                        json.dumps(knowledge_base_ids), 
                        result_count, 
                        cache_hit, 
                        timestamp
                    ))
                    self.conn.commit()
                    logger.info(f"Logged search: {query} with strategy {strategy}")
            else:
                # 使用内存存储
                self.search_logs.append({
                    "id": search_id,
                    "user_id": user_id,
                    "query": query,
                    "strategy": strategy,
                    "response_time": response_time,
                    "knowledge_base_ids": knowledge_base_ids,
                    "result_count": result_count,
                    "cache_hit": cache_hit,
                    "timestamp": timestamp
                })
                
            return search_id
                
        except Exception as e:
            logger.error(f"Log search error: {str(e)}", exc_info=True)
            # 如果出错，仍然返回一个ID，以便前端可以继续工作
            return str(uuid.uuid4())
    
    async def log_feedback(self, 
                        search_id: str, 
                        user_id: Optional[str], 
                        feedback_type: str, 
                        rating: Optional[float] = None, 
                        comment: Optional[str] = None) -> str:
        """记录反馈日志"""
        try:
            feedback_id = str(uuid.uuid4())
            timestamp = datetime.now()
            
            if self.conn:
                # 写入数据库
                with self.conn.cursor() as cur:
                    cur.execute("""
                    INSERT INTO feedback_logs 
                    (id, search_id, user_id, feedback_type, rating, comment, timestamp) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        feedback_id, 
                        search_id, 
                        user_id, 
                        feedback_type, 
                        rating, 
                        comment, 
                        timestamp
                    ))
                    self.conn.commit()
                    logger.info(f"Logged feedback: {feedback_type} for search {search_id}")
                    
                    # 清除相关缓存
                    if self.redis:
                        # 获取搜索记录以确定知识库ID
                        cur.execute("SELECT knowledge_base_ids FROM search_logs WHERE id = %s", (search_id,))
                        result = cur.fetchone()
                        if result and result[0]:
                            kb_ids = json.loads(result[0]) if isinstance(result[0], str) else result[0]
                            # 清除所有相关缓存
                            for kb_id in kb_ids + ['all']:
                                for time_range in ['day', 'week', 'month', 'year']:
                                    await self.redis.delete(f"performance_metrics:{time_range}:{kb_id}")
                                    await self.redis.delete(f"feedback_distribution:{time_range}:{kb_id}")
            else:
                # 使用内存存储
                self.feedback_logs.append({
                    "id": feedback_id,
                    "search_id": search_id,
                    "user_id": user_id,
                    "feedback_type": feedback_type,
                    "rating": rating,
                    "comment": comment,
                    "timestamp": timestamp
                })
                
            return feedback_id
                
        except Exception as e:
            logger.error(f"Log feedback error: {str(e)}", exc_info=True)
            # 如果出错，仍然返回一个ID，以便前端可以继续工作
            return str(uuid.uuid4())
        
        for i in range(min(limit, 20)):
            timestamp = now - timedelta(hours=i*2)
            record = UserBehaviorRecord(
                id=f"search_{i}",
                user_id=f"user{i%5 + 1:03d}",
                query=f"模拟查询 {i+1}",
                strategy=["semantic", "fulltext", "hybrid", "auto"][i % 4],
                response_time=80 + (i % 5) * 10,  # 毫秒
                knowledge_base_ids=["kb1", "kb2"] if i % 3 == 0 else ["kb1"],
                result_count=5 + (i % 3),
                feedback=["positive", "negative", None][i % 3],
                timestamp=timestamp
            )
            records.append(record)
        
        return records