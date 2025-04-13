import logging
from typing import List, Dict, Any, Optional, Tuple
import time
import numpy as np
from datetime import datetime
import uuid
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity

from models.search import SearchResult, ClusterInfo
from services.vector_service import VectorService
from services.fulltext_service import FulltextService
from services.reranking_service import RerankingService
from services.analytics_service import AnalyticsService
from config import settings

logger = logging.getLogger("retrieval")

class SearchService:
    def __init__(self):
        self.vector_service = VectorService()
        self.fulltext_service = FulltextService()
        self.reranking_service = RerankingService()
        self.analytics_service = AnalyticsService()
        self.strategy_used = "auto"
        self.clusters = []
    
    async def search(self, 
                     query: str, 
                     knowledge_base_ids: List[str],
                     strategy: str = "auto",
                     semantic_weight: float = 0.7,
                     fulltext_weight: float = 0.3,
                     max_results: int = 10,
                     min_score: float = 0.7,
                     use_reranking: bool = True,
                     use_clustering: bool = True) -> List[SearchResult]:
        """执行知识库检索
        
        支持多种检索策略：自动选择、语义检索、全文检索和混合检索
        """
        start_time = time.time()
        
        # 确定检索策略
        if strategy == "auto":
            # 自动选择策略：根据查询特征选择最合适的策略
            strategy = await self._determine_best_strategy(query)
            logger.info(f"Auto selected strategy: {strategy} for query: {query}")
        
        self.strategy_used = strategy
        
        # 根据策略执行检索
        if strategy == "semantic":
            results = await self._semantic_search(query, knowledge_base_ids, max_results * 2, min_score)
        elif strategy == "fulltext":
            results = await self._fulltext_search(query, knowledge_base_ids, max_results * 2, min_score)
        elif strategy == "hybrid":
            results = await self._hybrid_search(query, knowledge_base_ids, semantic_weight, fulltext_weight, max_results * 2, min_score)
        else:
            raise ValueError(f"不支持的检索策略: {strategy}")
        
        # 结果重排序
        if use_reranking and len(results) > 1:
            results = await self._rerank_results(query, results)
        
        # 结果聚类
        if use_clustering and len(results) > 1:
            results, clusters = await self._cluster_results(results)
            self.clusters = clusters
        
        # 限制结果数量
        results = results[:max_results]
        
        # 计算响应时间
        response_time = time.time() - start_time
        
        # 记录搜索日志
        await self.analytics_service.log_search(
            user_id=None,  # 实际应用中应从请求中获取用户ID
            query=query,
            strategy=strategy,
            response_time=response_time,
            knowledge_base_ids=knowledge_base_ids,
            result_count=len(results),
            cache_hit=False  # 实际应用中应根据缓存情况设置
        )
        
        logger.info(f"Search completed in {response_time:.3f}s, strategy: {strategy}, results: {len(results)}")
        return results
    
    async def _determine_best_strategy(self, query: str) -> str:
        """根据查询特征自动选择最佳检索策略
        
        该方法使用多维度分析来选择最合适的检索策略：
        1. 查询特征分析：分析查询的长度、结构、关键词等特征
        2. 历史性能分析：利用历史查询数据分析不同策略的性能表现
        3. 用户反馈分析：考虑用户对不同策略结果的反馈
        4. 动态权重调整：根据实时数据动态调整各因素的权重
        
        返回值:
            str: 选择的检索策略，可能是"semantic"、"fulltext"或"hybrid"
        """
        # 1. 查询特征分析
        feature_score = self._analyze_query_features(query)
        
        # 2. 历史性能分析（如果可用）
        history_score = await self._analyze_historical_performance(query)
        
        # 3. 计算最终得分并选择策略
        strategy = self._select_strategy_by_scores(feature_score, history_score)
        
        logger.debug(f"Strategy selection for query '{query}': {strategy} (feature_score={feature_score}, history_score={history_score})")
        return strategy
    
    def _analyze_query_features(self, query: str) -> dict:
        """分析查询特征，返回各策略的得分"""
        # 初始化各策略得分
        scores = {
            "semantic": 0.0,
            "fulltext": 0.0,
            "hybrid": 0.5  # 混合策略有一个基础分
        }
        
        # 1. 查询长度分析
        query_length = len(query)
        if query_length < 5:  # 非常短的查询
            scores["fulltext"] += 0.4
        elif 5 <= query_length <= 10:  # 中等长度查询
            scores["hybrid"] += 0.2
        else:  # 长查询
            scores["semantic"] += 0.3
        
        # 2. 查询结构分析
        # 2.1 引号检测（精确匹配需求）
        if '"' in query or "'" in query:
            scores["fulltext"] += 0.5
        
        # 2.2 特殊符号检测
        special_chars = set([':', '/', '+', '-', '&', '|', '!', '(', ')', '*'])
        if any(char in query for char in special_chars):
            scores["fulltext"] += 0.3
        
        # 3. 关键词分析
        # 3.1 定义类查询
        definition_terms = ["定义", "是什么", "概念", "解释", "含义"]
        if any(term in query for term in definition_terms):
            scores["fulltext"] += 0.4
        
        # 3.2 操作类查询
        operation_terms = ["如何", "怎么", "方法", "步骤", "流程", "教程"]
        if any(term in query for term in operation_terms):
            scores["fulltext"] += 0.3
            scores["hybrid"] += 0.1
        
        # 3.3 比较类查询
        comparison_terms = ["比较", "区别", "差异", "优缺点", "vs", "versus"]
        if any(term in query for term in comparison_terms):
            scores["semantic"] += 0.3
            scores["hybrid"] += 0.2
        
        # 3.4 开放式问题
        open_terms = ["为什么", "原因", "影响", "作用", "意义"]
        if any(term in query for term in open_terms):
            scores["semantic"] += 0.4
        
        # 4. 语言复杂度分析（简单启发式）
        words = query.split()
        if len(words) > 7:  # 较复杂的查询
            scores["semantic"] += 0.2
        
        return scores
    
    async def _analyze_historical_performance(self, query: str) -> dict:
        """分析历史查询性能，返回各策略的得分"""
        # 初始化各策略得分
        scores = {
            "semantic": 0.0,
            "fulltext": 0.0,
            "hybrid": 0.0
        }
        
        try:
            # 1. 尝试查找相似的历史查询
            similar_queries = await self._find_similar_queries(query)
            if not similar_queries:
                return scores  # 没有相似查询，返回空得分
            
            # 2. 分析各策略在相似查询上的表现
            strategy_performance = {}
            for strategy in ["semantic", "fulltext", "hybrid"]:
                # 计算该策略的平均响应时间和正面反馈率
                strategy_logs = [log for log in similar_queries if log.get("strategy") == strategy]
                if not strategy_logs:
                    continue
                
                # 计算平均响应时间（越短越好）
                avg_response_time = sum(log.get("response_time", 1.0) for log in strategy_logs) / len(strategy_logs)
                # 响应时间得分（反比例）
                time_score = 1.0 / (1.0 + avg_response_time)  # 归一化到0-1之间
                
                # 计算平均结果数
                avg_result_count = sum(log.get("result_count", 0) for log in strategy_logs) / len(strategy_logs)
                # 结果数得分（适中为佳）
                result_count_score = 0.0
                if 1 <= avg_result_count <= 20:  # 理想结果数范围
                    result_count_score = 0.3
                
                # 综合得分
                strategy_performance[strategy] = time_score * 0.7 + result_count_score * 0.3
            
            # 3. 更新策略得分
            for strategy, performance in strategy_performance.items():
                scores[strategy] = performance
            
        except Exception as e:
            logger.warning(f"Error analyzing historical performance: {str(e)}")
            # 出错时返回空得分
        
        return scores
    
    async def _find_similar_queries(self, query: str, limit: int = 5) -> list:
        """查找与当前查询相似的历史查询记录"""
        try:
            # 简化实现：基于关键词匹配查找相似查询
            # 实际系统中可以使用向量相似度或更复杂的算法
            
            # 提取查询关键词（简单分词）
            keywords = set(query.split())
            
            # 从最近的100条记录中查找
            recent_logs = []
            if hasattr(self.analytics_service, "search_logs") and self.analytics_service.search_logs:
                recent_logs = self.analytics_service.search_logs[-100:]
            
            # 计算相似度并排序
            similar_queries = []
            for log in recent_logs:
                log_query = log.get("query", "")
                log_keywords = set(log_query.split())
                
                # 计算关键词重叠度
                if log_keywords:
                    overlap = len(keywords.intersection(log_keywords)) / len(keywords.union(log_keywords))
                    if overlap > 0.3:  # 相似度阈值
                        log["similarity"] = overlap
                        similar_queries.append(log)
            
            # 按相似度排序并限制数量
            similar_queries.sort(key=lambda x: x.get("similarity", 0), reverse=True)
            return similar_queries[:limit]
            
        except Exception as e:
            logger.warning(f"Error finding similar queries: {str(e)}")
            return []
    
    def _select_strategy_by_scores(self, feature_score: dict, history_score: dict) -> str:
        """根据各项得分选择最佳策略"""
        # 合并得分
        final_scores = {
            "semantic": feature_score.get("semantic", 0) * 0.7 + history_score.get("semantic", 0) * 0.3,
            "fulltext": feature_score.get("fulltext", 0) * 0.7 + history_score.get("fulltext", 0) * 0.3,
            "hybrid": feature_score.get("hybrid", 0) * 0.7 + history_score.get("hybrid", 0) * 0.3
        }
        
        # 选择得分最高的策略
        best_strategy = max(final_scores.items(), key=lambda x: x[1])[0]
        
        # 如果最高分不明显优于其他策略，选择混合策略
        max_score = final_scores[best_strategy]
        if best_strategy != "hybrid":
            hybrid_score = final_scores["hybrid"]
            if max_score - hybrid_score < 0.1:  # 分数差异小于阈值
                return "hybrid"
        
        return best_strategy
    
    async def _semantic_search(self, query: str, knowledge_base_ids: List[str], max_results: int, min_score: float) -> List[SearchResult]:
        """执行语义检索"""
        try:
            # 获取查询的向量表示
            query_vector = await self.vector_service.encode_text(query)
            
            # 在向量数据库中搜索相似向量
            vector_results = await self.vector_service.search(
                query_vector=query_vector,
                knowledge_base_ids=knowledge_base_ids,
                limit=max_results,
                min_score=min_score
            )
            
            # 转换为SearchResult格式
            results = []
            for item in vector_results:
                result = SearchResult(
                    id=str(uuid.uuid4()),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    source=item.get("knowledge_base_name", ""),
                    document_id=item.get("document_id", ""),
                    score=item.get("score", 0.0),
                    timestamp=item.get("created_at", datetime.now()),
                    metadata=item.get("metadata", {})
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}", exc_info=True)
            raise
    
    async def _fulltext_search(self, query: str, knowledge_base_ids: List[str], max_results: int, min_score: float) -> List[SearchResult]:
        """执行全文检索"""
        try:
            # 使用BM25算法进行全文检索
            fulltext_results = await self.fulltext_service.search(
                query=query,
                knowledge_base_ids=knowledge_base_ids,
                limit=max_results,
                min_score=min_score
            )
            
            # 转换为SearchResult格式
            results = []
            for item in fulltext_results:
                result = SearchResult(
                    id=str(uuid.uuid4()),
                    title=item.get("title", ""),
                    content=item.get("content", ""),
                    source=item.get("knowledge_base_name", ""),
                    document_id=item.get("document_id", ""),
                    score=item.get("score", 0.0),
                    timestamp=item.get("created_at", datetime.now()),
                    metadata=item.get("metadata", {})
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Fulltext search error: {str(e)}", exc_info=True)
            raise
    
    async def _hybrid_search(self, query: str, knowledge_base_ids: List[str], semantic_weight: float, fulltext_weight: float, max_results: int, min_score: float) -> List[SearchResult]:
        """执行混合检索（结合语义检索和全文检索）"""
        try:
            # 使用Milvus 2.5原生混合检索功能
            if self._can_use_native_hybrid_search():
                return await self._native_hybrid_search(query, knowledge_base_ids, semantic_weight, fulltext_weight, max_results, min_score)
            else:
                # 回退到传统方法：分别执行语义检索和全文检索，然后合并结果
                return await self._legacy_hybrid_search(query, knowledge_base_ids, semantic_weight, fulltext_weight, max_results, min_score)
            
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}", exc_info=True)
            raise
    
    def _can_use_native_hybrid_search(self) -> bool:
        """检查是否可以使用Milvus 2.5的原生混合检索功能"""
        try:
            # 检查Milvus版本是否支持混合检索
            # 实际应用中应该检查Milvus服务器版本
            # 这里简化处理，假设已经支持
            return True
        except Exception as e:
            logger.warning(f"Failed to check Milvus version: {str(e)}", exc_info=True)
            return False
    
    async def _native_hybrid_search(self, query: str, knowledge_base_ids: List[str], semantic_weight: float, fulltext_weight: float, max_results: int, min_score: float) -> List[SearchResult]:
        """使用Milvus 2.5原生混合检索功能"""
        try:
            # 获取查询的向量表示
            query_vector = await self.vector_service.encode_text(query)
            
            collection = Collection(settings.MILVUS_COLLECTION)
            collection.load()
            
            # 构建查询条件
            search_params = {
                "metric_type": "COSINE",
                "params": {
                    "ef": 100,
                    "bm25_k1": 1.2,  # BM25算法参数
                    "bm25_b": 0.75,
                    "bm25_boost": 1.0,
                    "vector_weight": semantic_weight,  # 向量搜索权重
                    "text_weight": fulltext_weight      # 文本搜索权重
                }
            }
            
            # 如果指定了知识库ID，添加过滤条件
            expr = None
            if knowledge_base_ids:
                kb_conditions = [f'knowledge_base_id == "{kb_id}"' for kb_id in knowledge_base_ids]
                expr = " || ".join(kb_conditions)
            
            # 执行混合搜索
            results = collection.search(
                data=[query_vector],  # 向量查询部分
                anns_field="vector",   # 向量字段
                param=search_params,
                limit=max_results,
                expr=expr,
                output_fields=["knowledge_base_id", "document_id", "chunk_id", "chunk_type", 
                              "parent_id", "title", "content", "metadata", "created_at"],
                text_query=query,      # 文本查询部分
                text_field="content",   # 文本字段
                search_type="HYBRID"    # 混合搜索类型
            )
            
            # 处理搜索结果
            search_results = []
            for hits in results:
                for hit in hits:
                    if hit.score < min_score:
                        continue
                        
                    # 构建结果对象
                    result = SearchResult(
                        id=str(uuid.uuid4()),
                        title=hit.entity.get("title", ""),
                        content=hit.entity.get("content", ""),
                        source="知识库" + hit.entity.get("knowledge_base_id", "")[-4:],
                        document_id=hit.entity.get("document_id", ""),
                        score=hit.score,
                        timestamp=datetime.fromisoformat(hit.entity.get("created_at")),
                        metadata=hit.entity.get("metadata", {})
                    )
                    
                    search_results.append(result)
            
            # 释放集合
            collection.release()
            
            return search_results
            
        except Exception as e:
            logger.error(f"Native hybrid search error: {str(e)}", exc_info=True)
            # 如果原生混合搜索失败，回退到传统方法
            return await self._legacy_hybrid_search(query, knowledge_base_ids, semantic_weight, fulltext_weight, max_results, min_score)
    
    async def _legacy_hybrid_search(self, query: str, knowledge_base_ids: List[str], semantic_weight: float, fulltext_weight: float, max_results: int, min_score: float) -> List[SearchResult]:
        """传统混合检索方法（分别执行语义检索和全文检索，然后合并结果）"""
        try:
            # 并行执行语义检索和全文检索
            semantic_results = await self._semantic_search(query, knowledge_base_ids, max_results, min_score * 0.8)
            fulltext_results = await self._fulltext_search(query, knowledge_base_ids, max_results, min_score * 0.8)
            
            # 合并结果并重新计算分数
            result_map = {}
            
            # 处理语义检索结果
            for result in semantic_results:
                result_key = f"{result.document_id}:{result.content[:50]}"
                result_map[result_key] = {
                    "result": result,
                    "semantic_score": result.score,
                    "fulltext_score": 0.0
                }
            
            # 处理全文检索结果
            for result in fulltext_results:
                result_key = f"{result.document_id}:{result.content[:50]}"
                if result_key in result_map:
                    # 更新已存在的结果
                    result_map[result_key]["fulltext_score"] = result.score
                else:
                    # 添加新结果
                    result_map[result_key] = {
                        "result": result,
                        "semantic_score": 0.0,
                        "fulltext_score": result.score
                    }
            
            # 计算混合分数并排序
            combined_results = []
            for key, data in result_map.items():
                result = data["result"]
                # 计算加权混合分数
                combined_score = (data["semantic_score"] * semantic_weight + 
                                 data["fulltext_score"] * fulltext_weight)
                
                # 更新结果分数
                result.score = combined_score
                
                # 只保留分数高于阈值的结果
                if combined_score >= min_score:
                    combined_results.append(result)
            
            # 按分数降序排序
            combined_results.sort(key=lambda x: x.score, reverse=True)
            
            return combined_results
            
        except Exception as e:
            logger.error(f"Legacy hybrid search error: {str(e)}", exc_info=True)
            raise
    
    async def _rerank_results(self, query: str, results: List[SearchResult]) -> List[SearchResult]:
        """使用重排序模型对结果进行重排序"""
        try:
            # 提取结果内容
            texts = [result.content for result in results]
            
            # 使用重排序服务计算新的分数
            reranked_scores = await self.reranking_service.rerank(query, texts)
            
            # 更新结果分数
            for i, result in enumerate(results):
                result.score = reranked_scores[i]
            
            # 按新分数排序
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Reranking error: {str(e)}", exc_info=True)
            # 如果重排序失败，返回原始结果
            return results
    
    async def _cluster_results(self, results: List[SearchResult]) -> Tuple[List[SearchResult], List[ClusterInfo]]:
        """对搜索结果进行聚类"""
        try:
            if len(results) <= 1:
                # 结果太少，不需要聚类
                return results, []
            
            # 获取结果的向量表示
            texts = [result.content for result in results]
            vectors = await self.vector_service.encode_batch(texts)
            
            # 使用DBSCAN进行聚类
            clustering = DBSCAN(eps=0.3, min_samples=1, metric='cosine').fit(vectors)
            labels = clustering.labels_
            
            # 为每个结果分配聚类标签
            cluster_map = {}
            for i, result in enumerate(results):
                cluster_id = int(labels[i])
                if cluster_id not in cluster_map:
                    cluster_map[cluster_id] = []
                cluster_map[cluster_id].append(result)
            
            # 为每个聚类生成名称
            clusters = []
            for cluster_id, cluster_results in cluster_map.items():
                # 使用最高分结果的标题作为聚类名称
                top_result = max(cluster_results, key=lambda x: x.score)
                cluster_name = top_result.title if top_result.title else f"聚类 {cluster_id + 1}"
                
                # 为每个结果设置聚类字段
                for result in cluster_results:
                    result.cluster = cluster_name
                
                # 添加聚类信息
                clusters.append(ClusterInfo(
                    name=cluster_name,
                    count=len(cluster_results)
                ))
            
            # 重新组织结果：每个聚类的最高分结果优先
            clustered_results = []
            for cluster_id in sorted(cluster_map.keys()):
                # 按分数排序聚类内的结果
                sorted_results = sorted(cluster_map[cluster_id], key=lambda x: x.score, reverse=True)
                clustered_results.extend(sorted_results)
            
            return clustered_results, clusters
            
        except Exception as e:
            logger.error(f"Clustering error: {str(e)}", exc_info=True)
            # 如果聚类失败，返回原始结果
            return results, []