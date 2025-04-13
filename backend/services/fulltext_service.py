import logging
from typing import List, Dict, Any, Optional
import asyncio
import uuid
from datetime import datetime
from pymilvus import Collection, connections, utility

from config import settings

logger = logging.getLogger("retrieval")

class FulltextService:
    def __init__(self):
        # 连接到Milvus
        try:
            # 使用与VectorService相同的连接
            if not connections.has_connection("default"):
                connections.connect(
                    alias="default", 
                    host=settings.MILVUS_HOST,
                    port=settings.MILVUS_PORT
                )
                logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}", exc_info=True)
            raise
    
    async def search(self, query: str, knowledge_base_ids: List[str], limit: int = 10, min_score: float = 0.7) -> List[Dict[str, Any]]:
        """使用Milvus的全文检索功能进行检索"""
        try:
            collection = Collection(settings.MILVUS_COLLECTION)
            collection.load()
            
            # 构建查询条件 - 使用BM25算法进行全文检索
            search_params = {
                "metric_type": "IP",  # 对于全文检索，使用IP（内积）度量
                "params": {
                    "bm25_k1": 1.2,  # BM25算法参数k1，控制词频缩放
                    "bm25_b": 0.75,   # BM25算法参数b，控制文档长度归一化
                    "bm25_boost": 1.0  # 提升因子
                }
            }
            
            # 如果指定了知识库ID，添加过滤条件
            expr = None
            if knowledge_base_ids:
                kb_conditions = [f'knowledge_base_id == "{kb_id}"' for kb_id in knowledge_base_ids]
                expr = " || ".join(kb_conditions)
            
            # 执行全文检索
            # Milvus 2.5支持全文检索，使用BM25算法
            results = collection.search(
                data=[query],  # 直接使用查询文本
                anns_field="content",  # 在content字段上进行全文检索
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["knowledge_base_id", "document_id", "chunk_id", "chunk_type", 
                              "parent_id", "title", "content", "metadata", "created_at"],
                search_type="BM25"  # 明确指定使用BM25搜索类型
            )
            
            # 处理搜索结果
            search_results = []
            for hits in results:
                for hit in hits:
                    if hit.score < min_score:
                        continue
                        
                    # 构建结果对象
                    result = {
                        "id": hit.id,
                        "knowledge_base_id": hit.entity.get("knowledge_base_id"),
                        "document_id": hit.entity.get("document_id"),
                        "chunk_id": hit.entity.get("chunk_id"),
                        "chunk_type": hit.entity.get("chunk_type"),
                        "parent_id": hit.entity.get("parent_id"),
                        "title": hit.entity.get("title", ""),
                        "content": hit.entity.get("content", ""),
                        "metadata": hit.entity.get("metadata", {}),
                        "score": hit.score,
                        "created_at": datetime.fromisoformat(hit.entity.get("created_at"))
                    }
                    
                    # 添加知识库名称（实际应用中应从数据库获取）
                    result["knowledge_base_name"] = "知识库" + result["knowledge_base_id"][-4:]
                    
                    search_results.append(result)
            
            # 释放集合
            collection.release()
            
            return search_results
            
        except Exception as e:
            logger.error(f"Fulltext search error: {str(e)}", exc_info=True)
            raise
    
    async def index_document(self, document: Dict[str, Any]) -> bool:
        """索引文档 - 在Milvus 2.5中，全文索引与向量索引共用同一集合"""
        try:
            # 由于全文索引与向量索引共用同一集合，此处不需要额外操作
            # 文档已经通过VectorService.insert方法添加到Milvus中
            return True
            
        except Exception as e:
            logger.error(f"Index document error: {str(e)}", exc_info=True)
            return False
    
    async def delete_document(self, document_id: str) -> bool:
        """删除文档 - 在Milvus 2.5中，全文索引与向量索引共用同一集合"""
        try:
            # 由于全文索引与向量索引共用同一集合，此处不需要额外操作
            # 文档已经通过VectorService.delete_by_document方法从Milvus中删除
            return True
            
        except Exception as e:
            logger.error(f"Delete document error: {str(e)}", exc_info=True)
            return False