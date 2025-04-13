# Dify 知识库检索增强与优化

## 项目概述

本项目旨在增强和优化Dify的知识库检索功能，提供更准确和高效的检索结果。项目包含前端交互界面和后端API设计，实现多策略检索、结果重排序、内容聚类、缓存机制、日志分析、跨库检索和用户反馈等功能。

## 主要功能

1. **多策略检索算法**：支持混合检索、语义检索和全文检索的智能切换和融合
2. **检索结果重排序**：基于相关性、内容质量和用户反馈进行排序
3. **检索结果聚类**：将相似内容分组展示，减少冗余
4. **检索缓存机制**：提高频繁查询的响应速度
5. **检索日志和分析**：记录检索性能和用户行为
6. **跨知识库检索**：支持在多个知识库中同时搜索
7. **检索结果评分API**：支持用户反馈的收集和利用

## 项目结构

```
├── frontend/               # 前端代码
│   ├── public/            # 静态资源
│   ├── src/               # 源代码
│   │   ├── components/    # 组件
│   │   ├── pages/         # 页面
│   │   ├── services/      # API服务
│   │   ├── utils/         # 工具函数
│   │   └── App.js         # 主应用
│   ├── package.json       # 依赖配置
│   └── README.md          # 前端说明
├── backend/                # 后端代码
│   ├── api/               # API接口
│   ├── models/            # 数据模型
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── README.md          # 后端说明
└── README.md              # 项目说明
```

## 安装与运行

### 前端

```bash
cd frontend
npm install
npm start
```

### 后端

```bash
cd backend
pip install -r requirements.txt
python app.py
```

## 技术栈

- 前端：React, Ant Design, Axios
- 后端：Python, FastAPI
- 数据库：MongoDB/PostgreSQL

## 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 Apache 2.0 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件