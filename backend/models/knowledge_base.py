from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class KnowledgeBaseCreate(BaseModel):
    """知识库创建模型"""
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")

class KnowledgeBaseUpdate(BaseModel):
    """知识库更新模型"""
    name: Optional[str] = Field(None, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    status: Optional[str] = Field(None, description="知识库状态: active, inactive")

class KnowledgeBase(BaseModel):
    """知识库模型"""
    id: str = Field(..., description="知识库ID")
    name: str = Field(..., description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    document_count: int = Field(0, description="文档数量")
    last_updated: Optional[datetime] = Field(None, description="最后更新时间")
    status: str = Field("active", description="知识库状态: active, inactive")
    created_at: datetime = Field(..., description="创建时间")

class DocumentCreate(BaseModel):
    """文档创建模型"""
    name: str = Field(..., description="文档名称")
    content_type: str = Field(..., description="内容类型")

class Document(BaseModel):
    """文档模型"""
    id: str = Field(..., description="文档ID")
    knowledge_base_id: str = Field(..., description="所属知识库ID")
    name: str = Field(..., description="文档名称")
    content_type: str = Field(..., description="内容类型")
    size: int = Field(..., description="文档大小(字节)")
    chunk_count: int = Field(0, description="分块数量")
    status: str = Field("processed", description="文档状态: processing, processed, failed")
    error: Optional[str] = Field(None, description="处理错误信息")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class Chunk(BaseModel):
    """文档分块模型"""
    id: str = Field(..., description="分块ID")
    document_id: str = Field(..., description="所属文档ID")
    knowledge_base_id: str = Field(..., description="所属知识库ID")
    content: str = Field(..., description="分块内容")
    chunk_type: str = Field("child", description="分块类型: parent, child")
    parent_id: Optional[str] = Field(None, description="父块ID")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    vector: Optional[List[float]] = Field(None, description="向量表示")
    created_at: datetime = Field(..., description="创建时间")