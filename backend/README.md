# Dify Knowledge Retrieval 后端系统

## 项目概述

Dify Knowledge Retrieval 是一个高性能的知识库检索系统，专为大规模文档检索和问答场景设计。系统采用多策略检索算法，能够根据查询特征自动选择最佳检索策略，提供精准的搜索结果。

## 技术架构

### 核心组件

- **FastAPI**: 高性能的异步Web框架，提供API服务
- **Milvus**: 向量数据库，支持高效的向量相似度搜索和全文检索
- **PostgreSQL**: 关系型数据库，存储用户数据、搜索日志和反馈信息
- **Redis**: 缓存服务，提高检索性能
- **SentenceTransformer**: 用于文本向量化和结果重排序

### 系统架构图

```
+----------------+     +----------------+     +----------------+
|                |     |                |     |                |
|  客户端应用    | --> |  FastAPI 服务  | --> |  检索服务层    |
|                |     |                |     |                |
+----------------+     +----------------+     +-------+--------+
                                                     |
                                                     v
                       +----------------+     +------+--------+
                       |                |     |               |
                       |  分析服务层    | <-- |  存储层       |
                       |                |     |               |
                       +----------------+     +---------------+
                                              | Milvus/PG/Redis |
                                              +---------------+
```

## 核心功能

### 多策略检索

系统支持多种检索策略，能够根据查询特征自动选择最佳策略：

1. **语义检索 (Semantic Search)**: 基于向量相似度的检索方式，适合复杂语义理解和开放式问题
2. **全文检索 (Fulltext Search)**: 基于BM25算法的传统检索方式，适合关键词匹配和精确查询
3. **混合检索 (Hybrid Search)**: 结合语义检索和全文检索的优势，平衡召回率和精确度
4. **自动策略选择**: 根据查询特征、历史性能和用户反馈自动选择最佳检索策略

### 结果优化

1. **结果重排序**: 使用BGE重排序模型对初步检索结果进行精排序，提高结果相关性
2. **结果聚类**: 对相似结果进行聚类，减少冗余，提供更多样化的信息
3. **缓存机制**: 缓存热门查询结果，减少重复计算，提高响应速度

### 分析与监控

1. **搜索日志**: 记录查询、策略选择和响应时间等信息
2. **用户反馈**: 收集用户对搜索结果的反馈，用于系统优化
3. **性能指标**: 监控系统性能，包括响应时间、缓存命中率和正面反馈率等

## 安装与部署

### 环境要求

- Python 3.8+
- PostgreSQL 13+
- Redis 6+
- Milvus 2.5+

### 安装步骤

1. 克隆代码库

```bash
git clone https://github.com/your-org/dify-knowledge-retrieval.git
cd dify-knowledge-retrieval/backend
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 配置环境变量

创建`.env`文件，参考`config.py`中的设置项进行配置：

```
# 应用设置
APP_NAME=Dify Knowledge Retrieval
HOST=0.0.0.0
PORT=8000
DEBUG=True

# 数据库设置
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=dify_retrieval

# Milvus设置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION=dify_vectors

# Redis设置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
REDIS_CACHE_EXPIRE=3600
```

4. 启动服务

```bash
python app.py
```

或使用uvicorn：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## API文档

启动服务后，访问 `http://localhost:8000/docs` 查看Swagger API文档。

### 主要API端点

- **POST /api/search**: 执行知识库检索
- **GET /api/search/strategies**: 获取支持的检索策略
- **POST /api/feedback**: 提交搜索结果反馈
- **GET /api/analytics/performance**: 获取系统性能指标

### 搜索API示例

```json
// 请求
POST /api/search
{
  "query": "什么是向量数据库",
  "knowledge_base_ids": ["kb001", "kb002"],
  "strategy": "auto",
  "semantic_weight": 0.7,
  "fulltext_weight": 0.3,
  "max_results": 10,
  "min_score": 0.7,
  "use_reranking": true,
  "use_clustering": true
}

// 响应
{
  "query": "什么是向量数据库",
  "results": [
    {
      "id": "res001",
      "title": "向量数据库简介",
      "content": "向量数据库是一种专门设计用于存储和检索向量数据的数据库系统...",
      "source": "知识库001",
      "document_id": "doc123",
      "score": 0.92,
      "timestamp": "2023-10-01T10:30:00",
      "cluster": "基础概念",
      "metadata": {"author": "张三", "tags": ["数据库", "AI"]}
    },
    // 更多结果...
  ],
  "strategy_used": "semantic",
  "total_found": 15,
  "clusters": [
    {"name": "基础概念", "count": 3},
    {"name": "应用场景", "count": 2}
  ],
  "response_time": 0.235
}
```

## 配置说明

系统配置项在`config.py`中定义，主要包括：

### 检索配置

- **DEFAULT_SEARCH_STRATEGY**: 默认检索策略 (auto, semantic, fulltext, hybrid)
- **MAX_RESULTS**: 最大返回结果数
- **MIN_SCORE**: 最小相关性分数
- **SEMANTIC_WEIGHT**: 语义检索权重
- **FULLTEXT_WEIGHT**: 全文检索权重
- **USE_RERANKING**: 是否使用结果重排序
- **USE_CLUSTERING**: 是否使用结果聚类
- **CLUSTER_THRESHOLD**: 聚类阈值

### 缓存配置

- **REDIS_CACHE_EXPIRE**: 缓存过期时间（秒）

## 开发指南

### 项目结构

```
backend/
├── api/                # API路由定义
│   ├── analytics.py    # 分析API
│   ├── feedback.py     # 反馈API
│   ├── knowledge_base.py # 知识库API
│   ├── router.py       # 路由注册
│   ├── search.py       # 搜索API
│   └── settings.py     # 设置API
├── app.py              # 应用入口
├── config.py           # 配置定义
├── models/             # 数据模型
│   ├── analytics.py    # 分析模型
│   ├── feedback.py     # 反馈模型
│   ├── knowledge_base.py # 知识库模型
│   ├── search.py       # 搜索模型
│   └── settings.py     # 设置模型
├── services/           # 业务服务
│   ├── analytics_service.py  # 分析服务
│   ├── cache_service.py      # 缓存服务
│   ├── feedback_service.py   # 反馈服务
│   ├── fulltext_service.py   # 全文检索服务
│   ├── knowledge_base_service.py # 知识库服务
│   ├── reranking_service.py  # 重排序服务
│   ├── search_service.py     # 搜索服务
│   ├── settings_service.py   # 设置服务
│   └── vector_service.py     # 向量服务
└── utils/              # 工具函数
    ├── logger.py       # 日志工具
    └── metrics.py      # 指标工具
```

### 添加新功能

1. 在`models/`目录下定义数据模型
2. 在`services/`目录下实现业务逻辑
3. 在`api/`目录下创建API端点
4. 在`api/router.py`中注册新的路由

## 性能优化

1. **向量索引优化**: 调整Milvus的HNSW索引参数，平衡查询速度和准确性
2. **缓存策略优化**: 根据查询频率和数据更新频率调整缓存策略
3. **批量处理**: 使用批量API减少网络开销
4. **异步处理**: 利用FastAPI的异步特性提高并发性能

## 故障排除

### 常见问题

1. **连接数据库失败**: 检查数据库配置和网络连接
2. **检索结果不准确**: 调整检索参数，如相似度阈值和权重
3. **响应时间过长**: 检查数据库索引和缓存配置

### 日志查看

系统日志位于`logs/retrieval.log`，可通过查看日志定位问题：

```bash
tail -f logs/retrieval.log
```

## 贡献指南

欢迎贡献代码和提出建议！请遵循以下步骤：

1. Fork代码库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见LICENSE文件