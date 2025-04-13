import os
from typing import Dict, List, Optional, Union
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # 应用设置
    APP_NAME: str = "Dify Knowledge Retrieval"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # 数据库设置
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "dify_retrieval"
    DATABASE_URL: Optional[str] = None
    
    # Milvus设置
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "dify_vectors"
    VECTOR_DIM: int = 768  # 向量维度，根据使用的模型调整
    
    # Redis设置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_CACHE_EXPIRE: int = 3600  # 缓存过期时间（秒）
    
    # 检索设置
    DEFAULT_SEARCH_STRATEGY: str = "auto"  # auto, semantic, fulltext, hybrid
    MAX_RESULTS: int = 10
    MIN_SCORE: float = 0.7
    SEMANTIC_WEIGHT: float = 0.7
    FULLTEXT_WEIGHT: float = 0.3
    USE_RERANKING: bool = True
    USE_CLUSTERING: bool = True
    CLUSTER_THRESHOLD: float = 0.8
    
    # 日志设置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/retrieval.log"
    
    # 父子块设置
    PARENT_BLOCK_SIZE: int = 1000  # 父块大小（字符数）
    CHILD_BLOCK_SIZE: int = 200    # 子块大小（字符数）
    BLOCK_OVERLAP: int = 50        # 块重叠大小（字符数）
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 构建数据库URL
        if not self.DATABASE_URL:
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()