import logging
from typing import List, Dict, Any, Optional
import numpy as np
from datetime import datetime
import uuid
import asyncio
from pymilvus import Collection, connections, utility

from config import settings

logger = logging.getLogger("retrieval")

class VectorService:
    def __init__(self):
        # 连接到Milvus
        try:
            connections.connect(
                alias="default", 
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT
            )
            logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
            
            # 检查集合是否存在，不存在则创建
            self._ensure_collection()
            
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {str(e)}", exc_info=True)
            raise
    
    def _ensure_collection(self):
        """确保Milvus集合存在，不存在则创建"""
        collection_name = settings.MILVUS_COLLECTION
        
        if not utility.has_collection(collection_name):
            from pymilvus import FieldSchema, CollectionSchema, DataType
            
            # 定义集合字段
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
                FieldSchema(name="knowledge_base_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="chunk_type", dtype=DataType.VARCHAR, max_length=10),  # parent or child
                FieldSchema(name="parent_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="title", dtype=DataType.VARCHAR, max_length=256),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=settings.VECTOR_DIM),
                FieldSchema(name="metadata", dtype=DataType.JSON),
                FieldSchema(name="created_at", dtype=DataType.VARCHAR, max_length=30)
            ]
            
            # 创建集合模式
            schema = CollectionSchema(fields=fields, description="Dify knowledge retrieval vectors")
            
            # 创建集合
            collection = Collection(name=collection_name, schema=schema)
            
            # 创建向量索引
            vector_index_params = {
                "index_type": "HNSW",
                "metric_type": "COSINE",
                "params": {"M": 16, "efConstruction": 200}
            }
            collection.create_index(field_name="vector", index_params=vector_index_params)
            
            # 创建全文索引 - Milvus 2.5支持BM25全文检索
            fulltext_index_params = {
                "index_type": "FULLTEXT",
                "metric_type": "IP",
                "params": {
                    "bm25_k1": 1.2,  # BM25算法参数k1
                    "bm25_b": 0.75,   # BM25算法参数b
                    "bm25_boost": 1.0  # 提升因子
                }
            }
            collection.create_index(field_name="content", index_params=fulltext_index_params)
            
            logger.info(f"Created Milvus collection: {collection_name}")
        else:
            logger.info(f"Milvus collection {collection_name} already exists")
    
    async def encode_text(self, text: str) -> List[float]:
        """将文本编码为向量"""
        try:
            # 这里应该使用实际的文本嵌入模型
            # 为了演示，我们使用随机向量
            # 在实际实现中，应该使用如sentence-transformers等模型
            
            # 模拟异步操作
            await asyncio.sleep(0.01)
            
            # 生成随机向量并归一化
            vector = np.random.random(settings.VECTOR_DIM).astype(np.float32)
            vector = vector / np.linalg.norm(vector)
            
            return vector.tolist()
        except Exception as e:
            logger.error(f"Text encoding error: {str(e)}", exc_info=True)
            raise
    
    async def encode_batch(self, texts: List[str]) -> np.ndarray:
        """批量将文本编码为向量"""
        try:
            # 为每个文本生成向量
            vectors = []
            for text in texts:
                vector = await self.encode_text(text)
                vectors.append(vector)
            
            return np.array(vectors)
        except Exception as e:
            logger.error(f"Batch encoding error: {str(e)}", exc_info=True)
            raise
    
    async def search(self, query_vector: List[float], knowledge_base_ids: List[str], limit: int = 10, min_score: float = 0.7) -> List[Dict[str, Any]]:
        """在向量数据库中搜索相似向量"""
        try:
            collection = Collection(settings.MILVUS_COLLECTION)
            collection.load()
            
            # 构建查询条件
            search_params = {"metric_type": "COSINE", "params": {"ef": 100}}
            
            # 如果指定了知识库ID，添加过滤条件
            expr = None
            if knowledge_base_ids:
                kb_conditions = [f'knowledge_base_id == "{kb_id}"' for kb_id in knowledge_base_ids]
                expr = " || ".join(kb_conditions)
            
            # 执行向量搜索
            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=["knowledge_base_id", "document_id", "chunk_id", "chunk_type", 
                              "parent_id", "title", "content", "metadata", "created_at"]
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
            logger.error(f"Vector search error: {str(e)}", exc_info=True)
            raise
    
    async def insert(self, vectors: List[Dict[str, Any]]) -> List[str]:
        """向向量数据库插入向量"""
        try:
            if not vectors:
                return []
                
            collection = Collection(settings.MILVUS_COLLECTION)
            
            # 准备插入数据
            ids = [v.get("id", str(uuid.uuid4())) for v in vectors]
            knowledge_base_ids = [v.get("knowledge_base_id") for v in vectors]
            document_ids = [v.get("document_id") for v in vectors]
            chunk_ids = [v.get("chunk_id") for v in vectors]
            chunk_types = [v.get("chunk_type", "child") for v in vectors]
            parent_ids = [v.get("parent_id") for v in vectors]
            titles = [v.get("title", "") for v in vectors]
            contents = [v.get("content", "") for v in vectors]
            vector_data = [v.get("vector") for v in vectors]
            metadata = [v.get("metadata", {}) for v in vectors]
            created_at = [v.get("created_at", datetime.now().isoformat()) for v in vectors]
            
            # 执行插入
            collection.insert([
                ids, knowledge_base_ids, document_ids, chunk_ids, chunk_types,
                parent_ids, titles, contents, vector_data, metadata, created_at
            ])
            
            # 刷新集合以确保数据可见
            collection.flush()
            
            return ids
        except Exception as e:
            logger.error(f"Vector insert error: {str(e)}", exc_info=True)
            raise
    
    async def delete_by_document(self, document_id: str) -> int:
        """删除与文档关联的所有向量"""
        try:
            collection = Collection(settings.MILVUS_COLLECTION)
            expr = f'document_id == "{document_id}"'
            
            # 执行删除
            collection.delete(expr)
            
            # 刷新集合
            collection.flush()
            
            return 1  # 成功删除
        except Exception as e:
            logger.error(f"Vector delete error: {str(e)}", exc_info=True)
            raise
    
    async def delete_by_knowledge_base(self, knowledge_base_id: str) -> int:
        """删除与知识库关联的所有向量"""
        try:
            collection = Collection(settings.MILVUS_COLLECTION)
            expr = f'knowledge_base_id == "{knowledge_base_id}"'
            
            # 执行删除
            collection.delete(expr)
            
            # 刷新集合
            collection.flush()
            
            return 1  # 成功删除
        except Exception as e:
            logger.error(f"Vector delete error: {str(e)}", exc_info=True)
            raise