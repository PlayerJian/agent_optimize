from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class RetrievalSettings(BaseModel):
    """检索设置模型"""
    default_strategy: str = Field("auto", description="默认检索策略: auto, semantic, fulltext, hybrid")
    semantic_model: str = Field("default", description="语义模型")
    max_results: int = Field(10, description="最大结果数")
    min_score: float = Field(0.7, description="最小相关性分数 (0-1)")
    reranking: bool = Field(True, description="启用结果重排序")
    reranking_model: str = Field("default", description="重排序模型")
    clustering: bool = Field(True, description="启用结果聚类")
    cluster_threshold: float = Field(0.8, description="聚类相似度阈值 (0-1)")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class CacheSettings(BaseModel):
    """缓存设置模型"""
    enabled: bool = Field(True, description="启用缓存")
    max_size: int = Field(500, description="缓存容量上限(条)")
    ttl: int = Field(24, description="缓存生存时间(小时)")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class CrossKbSettings(BaseModel):
    """跨库检索设置模型"""
    enabled: bool = Field(True, description="启用跨库检索")
    max_knowledge_bases: int = Field(5, description="最大同时检索知识库数")
    merge_strategy: str = Field("interleave", description="结果合并策略: interleave, weighted, separate")
    updated_at: Optional[datetime] = Field(None, description="更新时间")