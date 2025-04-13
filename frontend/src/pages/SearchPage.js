import React, { useState, useEffect } from 'react';
import { Input, Select, Button, Card, List, Tag, Rate, Divider, Switch, Radio, Collapse, Badge, Tooltip, message, Slider, Spin, Tabs, Popover, Space, Modal, Form } from 'antd';
import { SearchOutlined, FilterOutlined, SortAscendingOutlined, ClusterOutlined, StarOutlined, LikeOutlined, DislikeOutlined, InfoCircleOutlined, HistoryOutlined, FileTextOutlined, SettingOutlined, QuestionCircleOutlined } from '@ant-design/icons';

const { Search } = Input;
const { Option } = Select;
const { Panel } = Collapse;

// 模拟知识库数据
const mockKnowledgeBases = [
  { id: 'kb1', name: '产品文档' },
  { id: 'kb2', name: '技术文档' },
  { id: 'kb3', name: '常见问题' },
  { id: 'kb4', name: '用户指南' },
];

// 模拟搜索结果数据
const mockSearchResults = [
  {
    id: 1,
    title: 'Dify知识库检索功能介绍',
    content: 'Dify提供强大的知识库检索功能，支持多种检索策略和结果优化...',
    source: '产品文档',
    score: 0.95,
    timestamp: '2023-04-15',
    cluster: '功能介绍',
  },
  {
    id: 2,
    title: '如何使用语义检索功能',
    content: '语义检索可以理解用户意图，提供更准确的检索结果...',
    source: '技术文档',
    score: 0.88,
    timestamp: '2023-05-20',
    cluster: '使用指南',
  },
  {
    id: 3,
    title: '混合检索策略配置指南',
    content: '混合检索策略结合了语义检索和全文检索的优点，可以根据查询类型自动切换...',
    source: '技术文档',
    score: 0.85,
    timestamp: '2023-06-10',
    cluster: '使用指南',
  },
  {
    id: 4,
    title: '检索结果排序算法说明',
    content: 'Dify使用多因素排序算法，综合考虑相关性、内容质量和用户反馈...',
    source: '技术文档',
    score: 0.82,
    timestamp: '2023-07-05',
    cluster: '技术细节',
  },
  {
    id: 5,
    title: '常见检索问题解答',
    content: '解答用户在使用知识库检索过程中遇到的常见问题...',
    source: '常见问题',
    score: 0.78,
    timestamp: '2023-08-15',
    cluster: '问题解答',
  },
];

// 模拟聚类数据
const mockClusters = [
  { name: '功能介绍', count: 1 },
  { name: '使用指南', count: 2 },
  { name: '技术细节', count: 1 },
  { name: '问题解答', count: 1 },
];

const SearchPage = () => {
  // 状态管理
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedKbs, setSelectedKbs] = useState([]);
  const [searchStrategy, setSearchStrategy] = useState('auto');
  const [sortBy, setSortBy] = useState('relevance');
  const [showClusters, setShowClusters] = useState(true);
  const [activeCluster, setActiveCluster] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [advancedMode, setAdvancedMode] = useState(false);
  // 新增状态
  const [viewMode, setViewMode] = useState('list'); // 'list' 或 'cluster'
  const [searchHistory, setSearchHistory] = useState([]);
  const [relevanceThreshold, setRelevanceThreshold] = useState(0.7);
  const [maxResults, setMaxResults] = useState(10);
  const [showFeedbackPanel, setShowFeedbackPanel] = useState(false);
  const [currentFeedback, setCurrentFeedback] = useState(null);
  const [searchParams, setSearchParams] = useState({
    semanticWeight: 0.7,
    fulltextWeight: 0.3,
    useReranking: true,
    useClustering: true,
  });
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [availableStrategies, setAvailableStrategies] = useState({});
  const [feedbackTypes, setFeedbackTypes] = useState({});
  
  // 在组件加载时获取知识库数据
  useEffect(() => {
    // 获取知识库列表
    knowledgeBaseAPI.getAll()
      .then(response => {
        const kbs = response.data;
        setKnowledgeBases(kbs);
        if (kbs.length > 0) {
          setSelectedKbs([kbs[0].id]); // 默认选择第一个知识库
        }
      })
      .catch(error => {
        console.error('获取知识库失败:', error);
        message.error('获取知识库失败，请刷新页面重试');
      });
    
    // 获取可用的检索策略
    searchAPI.getStrategies()
      .then(response => {
        setAvailableStrategies(response.data);
      })
      .catch(error => {
        console.error('获取检索策略失败:', error);
      });
    
    // 获取可用的反馈类型
    feedbackAPI.getFeedbackTypes()
      .then(response => {
        setFeedbackTypes(response.data);
      })
      .catch(error => {
        console.error('获取反馈类型失败:', error);
      });
  }, []);

  // 处理搜索
  const handleSearch = (value) => {
    if (!value.trim()) return;
    
    setIsLoading(true);
    setSearchQuery(value);
    
    // 保存到搜索历史
    const newHistory = [value, ...searchHistory.filter(item => item !== value)].slice(0, 10);
    setSearchHistory(newHistory);
    
    // 构建搜索请求参数
    const searchParams = {
      query: value,
      knowledge_base_ids: selectedKbs,
      strategy: searchStrategy,
      semantic_weight: searchParams.semanticWeight,
      fulltext_weight: searchParams.fulltextWeight,
      max_results: maxResults,
      min_score: relevanceThreshold,
      use_reranking: searchParams.useReranking,
      use_clustering: searchParams.useClustering
    };
    
    // 调用搜索API
    searchAPI.search(searchParams)
      .then(response => {
        const data = response.data;
        setSearchResults(data.results);
        
        // 如果启用了聚类，更新聚类数据
        if (searchParams.useClustering && data.clusters) {
          setClusters(data.clusters);
        }
        
        setIsLoading(false);
        message.success(`找到 ${data.total_found} 条结果，耗时 ${data.response_time.toFixed(2)}s`);
      })
      .catch(error => {
        console.error('搜索失败:', error);
        setIsLoading(false);
        message.error('搜索失败，请重试');
      });
  };

  // 处理知识库选择
  const handleKbChange = (values) => {
    setSelectedKbs(values);
  };

  // 处理检索策略切换
  const handleStrategyChange = (value) => {
    setSearchStrategy(value);
  };

  // 处理排序方式切换
  const handleSortChange = (value) => {
    setSortBy(value);
  };

  // 处理视图模式切换
  const handleViewModeChange = (mode) => {
    setViewMode(mode);
  };

  // 处理用户反馈
  const handleFeedback = (itemId, feedbackType) => {
    // 构建反馈请求参数
    const feedbackParams = {
      result_id: itemId,
      feedback_type: feedbackType,
      user_id: localStorage.getItem('userId') // 假设用户ID存储在localStorage中
    };
    
    // 调用反馈API
    feedbackAPI.submitFeedback(feedbackParams)
      .then(response => {
        message.success('感谢您的反馈！');
      })
      .catch(error => {
        console.error('提交反馈失败:', error);
        message.error('提交反馈失败，请重试');
      });
  };

  // 处理聚类筛选
  const handleClusterFilter = (clusterName) => {
    setActiveCluster(activeCluster === clusterName ? null : clusterName);
  };

  // 处理详细反馈
  const handleDetailedFeedback = (item) => {
    setCurrentFeedback(item);
    setShowFeedbackPanel(true);
  };

  // 提交详细反馈
  const submitDetailedFeedback = (values) => {
    // 构建详细反馈请求参数
    const feedbackParams = {
      result_id: currentFeedback.id,
      rating: values.rating || 0,
      feedback_type: values.feedbackType,
      comment: values.comment,
      user_id: localStorage.getItem('userId') // 假设用户ID存储在localStorage中
    };
    
    // 调用详细反馈API
    feedbackAPI.submitDetailedFeedback(feedbackParams)
      .then(response => {
        message.success('感谢您的详细反馈！');
        setShowFeedbackPanel(false);
        setCurrentFeedback(null);
      })
      .catch(error => {
        console.error('提交详细反馈失败:', error);
        message.error('提交详细反馈失败，请重试');
      });
  };

  // 渲染搜索历史
  const renderSearchHistory = () => {
    if (searchHistory.length === 0) return null;
    
    return (
      <Popover
        title="搜索历史"
        content={
          <List
            size="small"
            dataSource={searchHistory}
            renderItem={item => (
              <List.Item 
                style={{ cursor: 'pointer' }}
                onClick={() => handleSearch(item)}
              >
                <HistoryOutlined style={{ marginRight: 8 }} />
                {item}
              </List.Item>
            )}
          />
        }
        trigger="click"
      >
        <Button icon={<HistoryOutlined />}>历史</Button>
      </Popover>
    );
  };

  // 渲染高级搜索选项
  const renderAdvancedOptions = () => {
    if (!advancedMode) return null;
    
    return (
      <Card size="small" style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '24px' }}>
          <div style={{ minWidth: 200 }}>
            <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center' }}>
              <span>语义检索权重</span>
              <Tooltip title="调整语义检索在混合检索中的权重">
                <InfoCircleOutlined style={{ marginLeft: 8 }} />
              </Tooltip>
            </div>
            <Slider
              min={0}
              max={1}
              step={0.1}
              value={searchParams.semanticWeight}
              onChange={(value) => setSearchParams({...searchParams, semanticWeight: value, fulltextWeight: 1-value})}
              marks={{
                0: '0',
                0.5: '0.5',
                1: '1'
              }}
            />
          </div>
          
          <div style={{ minWidth: 200 }}>
            <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center' }}>
              <span>相关性阈值</span>
              <Tooltip title="只显示相关性分数高于此阈值的结果">
                <InfoCircleOutlined style={{ marginLeft: 8 }} />
              </Tooltip>
            </div>
            <Slider
              min={0}
              max={1}
              step={0.05}
              value={relevanceThreshold}
              onChange={setRelevanceThreshold}
              marks={{
                0: '0',
                0.5: '0.5',
                1: '1'
              }}
            />
          </div>
          
          <div style={{ minWidth: 200 }}>
            <div style={{ marginBottom: 8 }}>最大结果数</div>
            <Slider
              min={5}
              max={50}
              step={5}
              value={maxResults}
              onChange={setMaxResults}
              marks={{
                5: '5',
                25: '25',
                50: '50'
              }}
            />
          </div>
          
          <div>
            <div style={{ marginBottom: 8 }}>结果优化</div>
            <Space>
              <Switch 
                checkedChildren="重排序" 
                unCheckedChildren="重排序" 
                checked={searchParams.useReranking}
                onChange={(checked) => setSearchParams({...searchParams, useReranking: checked})}
              />
              <Switch 
                checkedChildren="聚类" 
                unCheckedChildren="聚类" 
                checked={searchParams.useClustering}
                onChange={(checked) => setSearchParams({...searchParams, useClustering: checked})}
              />
            </Space>
          </div>
        </div>
      </Card>
    );
  };

  // 渲染聚类视图
  const renderClusterView = () => {
    if (viewMode !== 'cluster') return null;
    
    const clusterGroups = {};
    searchResults.forEach(item => {
      if (!clusterGroups[item.cluster]) {
        clusterGroups[item.cluster] = [];
      }
      clusterGroups[item.cluster].push(item);
    });
    
    return (
      <div className="cluster-view">
        <Tabs type="card">
          {Object.keys(clusterGroups).map(cluster => (
            <Tabs.TabPane 
              tab={
                <span>
                  {cluster} <Badge count={clusterGroups[cluster].length} style={{ backgroundColor: '#52c41a' }} />
                </span>
              } 
              key={cluster}
            >
              <List
                itemLayout="vertical"
                dataSource={clusterGroups[cluster]}
                renderItem={item => renderResultItem(item)}
              />
            </Tabs.TabPane>
          ))}
        </Tabs>
      </div>
    );
  };

  // 渲染单个结果项
  const renderResultItem = (item) => {
    return (
      <List.Item
        key={item.id}
        className="result-item"
        actions={[
          <Tooltip title="相关性评分">
            <span><StarOutlined /> {item.score.toFixed(2)}</span>
          </Tooltip>,
          <Tooltip title="来源">
            <span><FileTextOutlined /> {item.source}</span>
          </Tooltip>,
          <Tooltip title="时间">
            <span>{item.timestamp}</span>
          </Tooltip>,
          <span>
            <Tooltip title="有帮助">
              <Button 
                type="text" 
                icon={<LikeOutlined />} 
                onClick={() => handleFeedback(item.id, 'like')}
              />
            </Tooltip>
            <Tooltip title="没帮助">
              <Button 
                type="text" 
                icon={<DislikeOutlined />} 
                onClick={() => handleFeedback(item.id, 'dislike')}
              />
            </Tooltip>
            <Tooltip title="详细反馈">
              <Button 
                type="text" 
                icon={<QuestionCircleOutlined />} 
                onClick={() => handleDetailedFeedback(item)}
              />
            </Tooltip>
          </span>,
        ]}
      >
        <List.Item.Meta
          title={<a href="#">{item.title}</a>}
          description={
            <div>
              <Tag color="blue">{item.cluster}</Tag>
              <Tag color="green">{item.source}</Tag>
            </div>
          }
        />
        <div className="result-content">{item.content}</div>
        <div className="result-actions">
          <Rate allowHalf defaultValue={item.score} disabled style={{ fontSize: 12 }} />
        </div>
      </List.Item>
    );
  };

  // 过滤结果
  const filteredResults = activeCluster
    ? searchResults.filter(item => item.cluster === activeCluster)
    : searchResults;

  // 渲染搜索结果
  const renderSearchResults = () => {
    return (
      <List
        itemLayout="vertical"
        size="large"
        loading={isLoading}
        dataSource={filteredResults}
        renderItem={item => (
          <List.Item
            key={item.id}
            className="result-item"
            actions={[
              <Tooltip title="相关性评分">
                <span><StarOutlined /> {item.score.toFixed(2)}</span>
              </Tooltip>,
              <Tooltip title="来源">
                <span>{item.source}</span>
              </Tooltip>,
              <Tooltip title="时间">
                <span>{item.timestamp}</span>
              </Tooltip>,
              <span>
                <Tooltip title="点赞">
                  <Button 
                    type="text" 
                    icon={<LikeOutlined />} 
                    onClick={() => handleFeedback(item.id, 'like')}
                  />
                </Tooltip>
                <Tooltip title="踩">
                  <Button 
                    type="text" 
                    icon={<DislikeOutlined />} 
                    onClick={() => handleFeedback(item.id, 'dislike')}
                  />
                </Tooltip>
              </span>,
            ]}
          >
            <List.Item.Meta
              title={<a href="#">{item.title}</a>}
              description={
                <Tag color="blue">{item.cluster}</Tag>
              }
            />
            <div className="result-content">{item.content}</div>
            <div className="result-actions">
              <Rate allowHalf defaultValue={item.score} disabled style={{ fontSize: 12 }} />
            </div>
          </List.Item>
        )}
      />
    );
  };

  // 渲染聚类视图
  const renderClusters = () => {
    if (!showClusters) return null;
    
    return (
      <div className="cluster-container">
        <div className="cluster-title">内容聚类</div>
        <div style={{ marginBottom: 16 }}>
          {clusters.map(cluster => (
            <Badge count={cluster.count} key={cluster.name}>
              <Tag 
                color={activeCluster === cluster.name ? 'blue' : 'default'}
                style={{ marginRight: 8, cursor: 'pointer' }}
                onClick={() => handleClusterFilter(cluster.name)}
              >
                {cluster.name}
              </Tag>
            </Badge>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="search-container">
      <div className="search-header">
        <h2>知识库检索</h2>
        <p>通过多策略检索算法，获取最准确的知识库内容</p>
      </div>
      
      <div className="search-form">
        <Search
          placeholder="输入您的检索问题"
          enterButton={<Button type="primary" icon={<SearchOutlined />}>搜索</Button>}
          size="large"
          onSearch={handleSearch}
          style={{ marginBottom: 16 }}
        />
        
        <div className="search-options">
          <Collapse ghost>
            <Panel 
              header={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>检索选项</span>
                  <Switch 
                    checkedChildren="高级" 
                    unCheckedChildren="基础" 
                    checked={advancedMode}
                    onChange={setAdvancedMode}
                    size="small"
                  />
                </div>
              } 
              key="1"
            >
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px' }}>
                <div>
                  <div style={{ marginBottom: 8 }}>选择知识库</div>
                  <Select
                    mode="multiple"
                    style={{ width: 300 }}
                    placeholder="选择知识库"
                    value={selectedKbs}
                    onChange={handleKbChange}
                  >
                    {knowledgeBases.map(kb => (
                      <Option key={kb.id} value={kb.id}>{kb.name}</Option>
                    ))}
                  </Select>
                </div>
                
                <div>
                  <div style={{ marginBottom: 8 }}>检索策略</div>
                  <Radio.Group value={searchStrategy} onChange={e => handleStrategyChange(e.target.value)}>
                    <Radio.Button value="auto">智能选择</Radio.Button>
                    <Radio.Button value="semantic">语义检索</Radio.Button>
                    <Radio.Button value="fulltext">全文检索</Radio.Button>
                    <Radio.Button value="hybrid">混合检索</Radio.Button>
                  </Radio.Group>
                </div>
                
                <div>
                  <div style={{ marginBottom: 8 }}>排序方式</div>
                  <Select
                    style={{ width: 150 }}
                    value={sortBy}
                    onChange={handleSortChange}
                  >
                    <Option value="relevance">相关性</Option>
                    <Option value="quality">内容质量</Option>
                    <Option value="feedback">用户反馈</Option>
                    <Option value="time">时间</Option>
                  </Select>
                </div>
                
                <div>
                  <div style={{ marginBottom: 8 }}>视图模式</div>
                  <Radio.Group value={viewMode} onChange={e => handleViewModeChange(e.target.value)}>
                    <Radio.Button value="list">列表视图</Radio.Button>
                    <Radio.Button value="cluster">聚类视图</Radio.Button>
                  </Radio.Group>
                </div>
              </div>
              
              {renderAdvancedOptions()}
            </Panel>
          </Collapse>
        </div>
      </div>
      
      {isLoading ? (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>正在检索中，请稍候...</div>
        </div>
      ) : searchResults.length > 0 && (
        <div className="search-results">
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
            <div>
              <span>找到 {filteredResults.length} 条结果</span>
              {activeCluster && (
                <Tag color="blue" closable onClose={() => setActiveCluster(null)} style={{ marginLeft: 8 }}>
                  聚类: {activeCluster}
                </Tag>
              )}
            </div>
            <div>
              <Button icon={<FilterOutlined />} style={{ marginRight: 8 }}>筛选</Button>
              <Button icon={<SortAscendingOutlined />} style={{ marginRight: 8 }}>排序</Button>
              <Radio.Group value={viewMode} onChange={e => handleViewModeChange(e.target.value)} buttonStyle="solid" size="small">
                <Radio.Button value="list">列表</Radio.Button>
                <Radio.Button value="cluster">聚类</Radio.Button>
              </Radio.Group>
            </div>
          </div>
          
          {viewMode === 'list' ? (
            <>
              {showClusters && renderClusters()}
              {renderSearchResults()}
            </>
          ) : (
            renderClusterView()
          )}
        </div>
      )}
      
      {/* 详细反馈面板 */}
      <Modal
        title="提供详细反馈"
        visible={showFeedbackPanel}
        onCancel={() => setShowFeedbackPanel(false)}
        footer={null}
      >
        {currentFeedback && (
          <Form onFinish={submitDetailedFeedback}>
            <div style={{ marginBottom: 16 }}>
              <strong>对结果：</strong> {currentFeedback.title}
            </div>
            
            <Form.Item name="rating" label="评分">
              <Rate allowHalf />
            </Form.Item>
            
            <Form.Item name="feedbackType" label="反馈类型">
              <Radio.Group>
                <Radio value="relevant">相关且有帮助</Radio>
                <Radio value="partially">部分相关</Radio>
                <Radio value="irrelevant">不相关</Radio>
                <Radio value="outdated">信息过时</Radio>
                <Radio value="incomplete">信息不完整</Radio>
                <Radio value="other">其他问题</Radio>
              </Radio.Group>
            </Form.Item>
            
            <Form.Item name="comment" label="详细说明">
              <Input.TextArea rows={4} placeholder="请详细描述您的反馈..." />
            </Form.Item>
            
            <Form.Item>
              <Button type="primary" htmlType="submit">提交反馈</Button>
            </Form.Item>
          </Form>
        )}
      </Modal>
    </div>
  );
};

export default SearchPage;