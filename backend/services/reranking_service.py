import logging
from typing import List, Dict, Any, Optional
import numpy as np
import asyncio
import torch
from sentence_transformers import SentenceTransformer

from config import settings

logger = logging.getLogger("retrieval")

class RerankingService:
    def __init__(self):
        # 加载BGE模型进行重排序
        try:
            self.model = SentenceTransformer('BAAI/bge-reranker-v2-m3')
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
            self.model.to(self.device)
            logger.info(f"BGE reranking model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load BGE model: {str(e)}", exc_info=True)
            self.model = None
    
    async def rerank(self, query: str, texts: List[str]) -> List[float]:
        """对检索结果进行重排序
        
        使用BGE模型计算查询和文本之间的相关性分数
        """
        try:
            if self.model is None:
                logger.warning("BGE model not loaded, falling back to default scoring")
                return [1.0] * len(texts)
                
            # 使用异步执行模型推理，避免阻塞主线程
            loop = asyncio.get_event_loop()
            
            # 定义一个在线程池中执行的函数
            def compute_similarity():
                with torch.no_grad():
                    # 编码查询和文本
                    query_embedding = self.model.encode(query, convert_to_tensor=True)
                    text_embeddings = self.model.encode(texts, convert_to_tensor=True, batch_size=16)
                    
                    # 计算余弦相似度
                    similarities = torch.nn.functional.cosine_similarity(query_embedding.unsqueeze(0), text_embeddings)
                    
                    # 转换为Python列表并确保分数在0-1之间
                    scores = similarities.cpu().numpy().tolist()
                    scores = [max(0.0, min(1.0, score)) for score in scores]
                    
                    return scores
            
            # 在线程池中执行计算
            scores = await loop.run_in_executor(None, compute_similarity)
            
            return scores
            
        except Exception as e:
            logger.error(f"Reranking error: {str(e)}", exc_info=True)
            # 如果重排序失败，返回原始分数（全为1.0）
            return [1.0] * len(texts)
            
        except Exception as e:
            logger.error(f"Reranking error: {str(e)}", exc_info=True)
            # 如果重排序失败，返回原始分数（全为1.0）
            return [1.0] * len(texts)
    
    async def batch_rerank(self, queries: List[str], texts_list: List[List[str]]) -> List[List[float]]:
        """批量对检索结果进行重排序"""
        try:
            # 使用异步任务并行处理多个查询
            tasks = [self.rerank(query, texts) for query, texts in zip(queries, texts_list)]
            results = await asyncio.gather(*tasks)
            return results
        except Exception as e:
            logger.error(f"Batch reranking error: {str(e)}", exc_info=True)
            # 如果重排序失败，返回原始分数
            return [[1.0] * len(texts) for texts in texts_list]