# Dify 知识库检索增强与优化 - 前端

## 概述

本前端项目为Dify知识库检索功能提供了现代化的Web交互界面，实现了多策略检索、结果重排序、内容聚类、跨库检索和用户反馈等功能的可视化展示和操作。

## 主要功能

1. **高级搜索界面**：支持多种检索策略选择和参数配置
2. **结果展示区域**：包含列表视图和聚类视图两种展示方式
3. **用户反馈机制**：支持对检索结果进行评分和反馈
4. **跨库搜索选项**：可选择多个知识库进行联合检索
5. **性能分析面板**：展示检索性能和用户行为数据

## 组件结构

- **SearchBar**：高级搜索栏，包含检索策略选择和参数配置
- **ResultList**：检索结果列表，支持排序和筛选
- **ClusterView**：聚类视图，将相似内容分组展示
- **FeedbackPanel**：用户反馈面板，支持评分和反馈
- **PerformanceChart**：性能分析图表，展示检索性能数据
- **KnowledgeBaseSelector**：知识库选择器，支持多选

## 技术栈

- React 18
- Ant Design 5
- Axios
- ECharts
- React Router

## 开发指南

```bash
# 安装依赖
npm install

# 启动开发服务器
npm start

# 构建生产版本
npm run build
```

## 目录结构

```
├── public/            # 静态资源
├── src/               # 源代码
│   ├── components/    # 组件
│   ├── pages/         # 页面
│   ├── services/      # API服务
│   ├── utils/         # 工具函数
│   ├── App.js         # 主应用
│   └── index.js       # 入口文件
└── package.json       # 依赖配置
```