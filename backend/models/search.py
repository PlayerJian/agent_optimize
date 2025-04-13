from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class SearchResult(BaseModel):
    """搜索结果模型"""
    id: str = Field(..., description="结果ID")
    title: str = Field(..., description="结果标题")
    content: str = Field(..., description="结果内容")
    source: str = Field(..., description="来源知识库")
    document_id: str = Field(..., description="文档ID")
    score: float = Field(..., description="相关性评分")
    timestamp: datetime = Field(..., description="索引时间")
    cluster: Optional[str] = Field(None, description="聚类分组")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")

class ClusterInfo(BaseModel):
    """聚类信息模型"""
    name: str = Field(..., description="聚类名称")
    count: int = Field(..., description="包含结果数量")

class SearchRequest(BaseModel):
    """搜索请求模型"""
    query: str = Field(..., description="搜索查询")
    knowledge_base_ids: List[str] = Field(..., description="要搜索的知识库ID列表")
    strategy: str = Field("auto", description="检索策略: auto, semantic, fulltext, hybrid")
    semantic_weight: float = Field(0.7, description="语义检索权重 (0-1)")
    fulltext_weight: float = Field(0.3, description="全文检索权重 (0-1)")
    max_results: int = Field(10, description="最大结果数")
    min_score: float = Field(0.7, description="最小相关性分数 (0-1)")
    use_reranking: bool = Field(True, description="是否使用结果重排序")
    use_clustering: bool = Field(True, description="是否使用结果聚类")

class SearchResponse(BaseModel):
    """搜索响应模型"""
    query: str = Field(..., description="搜索查询")
    results: List[SearchResult] = Field(..., description="搜索结果列表")
    strategy_used: str = Field(..., description="实际使用的检索策略")
    total_found: int = Field(..., description="找到的结果总数")
    clusters: Optional[List[ClusterInfo]] = Field([], description="聚类信息")
    response_time: float = Field(..., description="响应时间(秒)")