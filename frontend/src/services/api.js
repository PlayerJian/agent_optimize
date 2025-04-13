import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api', // 后端API基础URL
  timeout: 10000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json',
  },
});

// 搜索API
export const searchAPI = {
  // 执行搜索
  search: (params) => api.post('/search/', params),
  // 获取可用的检索策略
  getStrategies: () => api.get('/search/strategies'),
};

// 反馈API
export const feedbackAPI = {
  // 提交简单反馈
  submitFeedback: (params) => api.post('/feedback/', params),
  // 提交详细反馈
  submitDetailedFeedback: (params) => api.post('/feedback/detailed', params),
  // 获取可用的反馈类型
  getFeedbackTypes: () => api.get('/feedback/types'),
};

// 知识库API
export const knowledgeBaseAPI = {
  // 获取所有知识库
  getAll: () => api.get('/knowledge-base/'),
  // 获取知识库详情
  getById: (id) => api.get(`/knowledge-base/${id}`),
  // 创建知识库
  create: (data) => api.post('/knowledge-base/', data),
  // 更新知识库
  update: (id, data) => api.put(`/knowledge-base/${id}`, data),
  // 删除知识库
  delete: (id) => api.delete(`/knowledge-base/${id}`),
  // 上传文档到知识库
  uploadDocument: (knowledgeBaseId, formData) => api.post(`/knowledge-base/${knowledgeBaseId}/documents`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
};

// 分析API
export const analyticsAPI = {
  // 获取性能指标
  getPerformanceMetrics: (timeRange, knowledgeBaseId) => {
    const params = { time_range: timeRange };
    if (knowledgeBaseId) params.knowledge_base_id = knowledgeBaseId;
    return api.get('/analytics/performance', { params });
  },
  // 获取搜索趋势
  getSearchTrends: (timeRange, knowledgeBaseId) => {
    const params = { time_range: timeRange };
    if (knowledgeBaseId) params.knowledge_base_id = knowledgeBaseId;
    return api.get('/analytics/search-trends', { params });
  },
  // 获取用户行为日志
  getUserBehavior: (timeRange, knowledgeBaseId, limit = 100) => {
    const params = { time_range: timeRange, limit };
    if (knowledgeBaseId) params.knowledge_base_id = knowledgeBaseId;
    return api.get('/analytics/user-behavior', { params });
  },
  // 获取热门查询
  getTopQueries: (timeRange, knowledgeBaseId, limit = 10) => {
    const params = { time_range: timeRange, limit };
    if (knowledgeBaseId) params.knowledge_base_id = knowledgeBaseId;
    return api.get('/analytics/top-queries', { params });
  },
};

// 设置API
export const settingsAPI = {
  // 获取系统设置
  getSettings: () => api.get('/settings/'),
  // 更新系统设置
  updateSettings: (data) => api.put('/settings/', data),
  // 获取缓存统计信息
  getCacheStats: () => api.get('/settings/cache-stats'),
  // 清空缓存
  clearCache: () => api.post('/settings/clear-cache'),
};

export default api;