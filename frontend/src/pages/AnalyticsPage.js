import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Select, DatePicker, Button, Table, Tabs, Statistic, Divider, Radio, Alert, Tooltip, Badge, Progress } from 'antd';
import { LineChartOutlined, PieChartOutlined, BarChartOutlined, UserOutlined, SearchOutlined, ClockCircleOutlined, DownloadOutlined, ReloadOutlined, QuestionCircleOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { analyticsAPI, knowledgeBaseAPI } from '../services/api';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;

// 模拟分析数据
const mockPerformanceData = {
  dailySearches: [150, 160, 165, 170, 180, 190, 210, 220, 200, 195, 205, 215, 225, 235],
  avgResponseTime: [120, 115, 110, 105, 100, 95, 90, 85, 80, 82, 85, 80, 75, 70],
  searchStrategies: {
    semantic: 45,
    fulltext: 25,
    hybrid: 30
  },
  cacheHitRate: 68,
  topQueries: [
    { query: "如何配置知识库", count: 45 },
    { query: "检索结果排序", count: 38 },
    { query: "语义检索原理", count: 32 },
    { query: "混合检索策略", count: 28 },
    { query: "检索性能优化", count: 25 }
  ],
  userFeedback: {
    positive: 78,
    negative: 22
  }
};

const mockUserBehaviorData = [
  { key: '1', userId: 'user001', query: '如何配置知识库', strategy: '语义检索', responseTime: '85ms', timestamp: '2023-09-15 10:23:45', feedback: '正面' },
  { key: '2', userId: 'user002', query: '检索结果排序', strategy: '混合检索', responseTime: '92ms', timestamp: '2023-09-15 11:15:32', feedback: '正面' },
  { key: '3', userId: 'user003', query: '语义检索原理', strategy: '语义检索', responseTime: '78ms', timestamp: '2023-09-15 13:45:21', feedback: '正面' },
  { key: '4', userId: 'user004', query: '混合检索策略', strategy: '混合检索', responseTime: '105ms', timestamp: '2023-09-15 14:32:18', feedback: '负面' },
  { key: '5', userId: 'user005', query: '检索性能优化', strategy: '全文检索', responseTime: '65ms', timestamp: '2023-09-15 16:12:45', feedback: '正面' },
];

const AnalyticsPage = () => {
  const [timeRange, setTimeRange] = useState('week');
  const [knowledgeBase, setKnowledgeBase] = useState('all');
  const [activeTab, setActiveTab] = useState('performance');
  const [performanceData, setPerformanceData] = useState(null);
  const [searchTrends, setSearchTrends] = useState(null);
  const [userBehaviorData, setUserBehaviorData] = useState([]);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  
  // 在组件加载时获取数据
  useEffect(() => {
    // 获取知识库列表
    knowledgeBaseAPI.getAll()
      .then(response => {
        setKnowledgeBases(response.data);
      })
      .catch(error => {
        console.error('获取知识库失败:', error);
      });
      
    // 加载初始数据
    loadAnalyticsData();
  }, []);
  
  // 当时间范围或知识库选择变化时重新加载数据
  useEffect(() => {
    loadAnalyticsData();
  }, [timeRange, knowledgeBase]);
  
  // 加载分析数据
  const loadAnalyticsData = () => {
    setIsLoading(true);
    
    // 获取性能指标
    analyticsAPI.getPerformanceMetrics(timeRange, knowledgeBase !== 'all' ? knowledgeBase : null)
      .then(response => {
        setPerformanceData(response.data);
      })
      .catch(error => {
        console.error('获取性能指标失败:', error);
      });
      
    // 获取搜索趋势
    analyticsAPI.getSearchTrends(timeRange, knowledgeBase !== 'all' ? knowledgeBase : null)
      .then(response => {
        setSearchTrends(response.data);
      })
      .catch(error => {
        console.error('获取搜索趋势失败:', error);
      });
      
    // 获取用户行为数据
    analyticsAPI.getUserBehavior(timeRange, knowledgeBase !== 'all' ? knowledgeBase : null)
      .then(response => {
        setUserBehaviorData(response.data);
        setIsLoading(false);
      })
      .catch(error => {
        console.error('获取用户行为数据失败:', error);
        setIsLoading(false);
      });
  };

  // 搜索量趋势图配置
  const getSearchTrendOption = () => {
    const days = Array.from({ length: 14 }, (_, i) => `9/${i + 1}`);
    
    return {
      title: {
        text: '搜索量趋势',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: days
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: mockPerformanceData.dailySearches,
        type: 'line',
        smooth: true,
        lineStyle: {
          color: '#1890ff',
          width: 3
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [{
              offset: 0, color: 'rgba(24,144,255,0.3)'
            }, {
              offset: 1, color: 'rgba(24,144,255,0.1)'
            }]
          }
        }
      }]
    };
  };

  // 响应时间趋势图配置
  const getResponseTimeOption = () => {
    const days = Array.from({ length: 14 }, (_, i) => `9/${i + 1}`);
    
    return {
      title: {
        text: '平均响应时间趋势 (ms)',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis'
      },
      xAxis: {
        type: 'category',
        data: days
      },
      yAxis: {
        type: 'value'
      },
      series: [{
        data: mockPerformanceData.avgResponseTime,
        type: 'line',
        smooth: true,
        lineStyle: {
          color: '#52c41a',
          width: 3
        }
      }]
    };
  };

  // 检索策略分布图配置
  const getSearchStrategyOption = () => {
    return {
      title: {
        text: '检索策略分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
      },
      series: [
        {
          type: 'pie',
          radius: '60%',
          data: [
            { value: mockPerformanceData.searchStrategies.semantic, name: '语义检索' },
            { value: mockPerformanceData.searchStrategies.fulltext, name: '全文检索' },
            { value: mockPerformanceData.searchStrategies.hybrid, name: '混合检索' }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  };

  // 用户反馈分布图配置
  const getUserFeedbackOption = () => {
    return {
      title: {
        text: '用户反馈分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item'
      },
      legend: {
        orient: 'vertical',
        left: 'left',
      },
      series: [
        {
          type: 'pie',
          radius: '60%',
          data: [
            { value: mockPerformanceData.userFeedback.positive, name: '正面反馈', itemStyle: { color: '#52c41a' } },
            { value: mockPerformanceData.userFeedback.negative, name: '负面反馈', itemStyle: { color: '#f5222d' } }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  };

  // 热门查询图配置
  const getTopQueriesOption = () => {
    return {
      title: {
        text: '热门查询',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow'
        }
      },
      xAxis: {
        type: 'value'
      },
      yAxis: {
        type: 'category',
        data: mockPerformanceData.topQueries.map(item => item.query).reverse()
      },
      series: [
        {
          type: 'bar',
          data: mockPerformanceData.topQueries.map(item => item.count).reverse(),
          itemStyle: {
            color: '#1890ff'
          }
        }
      ]
    };
  };

  // 用户行为日志表格列配置
  const userBehaviorColumns = [
    {
      title: '用户ID',
      dataIndex: 'userId',
      key: 'userId',
    },
    {
      title: '查询内容',
      dataIndex: 'query',
      key: 'query',
    },
    {
      title: '检索策略',
      dataIndex: 'strategy',
      key: 'strategy',
    },
    {
      title: '响应时间',
      dataIndex: 'responseTime',
      key: 'responseTime',
    },
    {
      title: '时间戳',
      dataIndex: 'timestamp',
      key: 'timestamp',
    },
    {
      title: '用户反馈',
      dataIndex: 'feedback',
      key: 'feedback',
      render: (text) => (
        <span style={{ color: text === '正面' ? '#52c41a' : '#f5222d' }}>{text}</span>
      ),
    },
  ];

  // 渲染性能分析面板
  const renderPerformancePanel = () => {
    return (
      <div>
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="今日搜索量"
                value={235}
                prefix={<SearchOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="平均响应时间"
                value={70}
                suffix="ms"
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="缓存命中率"
                value={mockPerformanceData.cacheHitRate}
                suffix="%"
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="用户满意度"
                value={mockPerformanceData.userFeedback.positive}
                suffix="%"
                prefix={<UserOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card>
              <ReactECharts option={getSearchTrendOption()} style={{ height: 300 }} />
            </Card>
          </Col>
          <Col span={12}>
            <Card>
              <ReactECharts option={getResponseTimeOption()} style={{ height: 300 }} />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={8}>
            <Card>
              <ReactECharts option={getSearchStrategyOption()} style={{ height: 300 }} />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <ReactECharts option={getUserFeedbackOption()} style={{ height: 300 }} />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <ReactECharts option={getTopQueriesOption()} style={{ height: 300 }} />
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  // 渲染用户行为日志面板
  const renderUserBehaviorPanel = () => {
    return (
      <Card>
        <Table 
          columns={userBehaviorColumns} 
          dataSource={mockUserBehaviorData} 
          pagination={{ pageSize: 10 }}
        />
      </Card>
    );
  };

  // 渲染性能趋势面板
  const renderPerformanceTrends = () => {
    return (
      <div>
        <Alert 
          message="性能提示" 
          description="检索响应时间较上周降低了15%，用户满意度提升了8%。建议继续优化语义检索模型以进一步提升性能。" 
          type="info" 
          showIcon 
          style={{ marginBottom: 16 }}
        />
        
        <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Card>
              <Statistic
                title={<span>今日搜索量 <Tooltip title="较昨日增长10%"><RiseOutlined style={{ color: '#52c41a' }} /></Tooltip></span>}
                value={235}
                prefix={<SearchOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={<span>平均响应时间 <Tooltip title="较昨日降低5%"><FallOutlined style={{ color: '#52c41a' }} /></Tooltip></span>}
                value={70}
                suffix="ms"
                prefix={<ClockCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="缓存命中率"
                value={mockPerformanceData.cacheHitRate}
                suffix="%"
                valueStyle={{ color: '#faad14' }}
              />
              <Progress percent={mockPerformanceData.cacheHitRate} status="active" strokeColor="#faad14" />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title={<span>用户满意度 <Tooltip title="较昨日提升3%"><RiseOutlined style={{ color: '#52c41a' }} /></Tooltip></span>}
                value={mockPerformanceData.userFeedback.positive}
                suffix="%"
                prefix={<UserOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
              <Progress percent={mockPerformanceData.userFeedback.positive} status="active" strokeColor="#52c41a" />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Card title="搜索量趋势" extra={<ReloadOutlined />}>
              <ReactECharts option={getSearchTrendOption()} style={{ height: 300 }} />
            </Card>
          </Col>
          <Col span={12}>
            <Card title="响应时间趋势" extra={<ReloadOutlined />}>
              <ReactECharts option={getResponseTimeOption()} style={{ height: 300 }} />
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  // 渲染策略分析面板
  const renderStrategyAnalysis = () => {
    return (
      <div style={{ marginTop: 16 }}>
        <Row gutter={[16, 16]}>
          <Col span={8}>
            <Card title="检索策略分布" extra={<QuestionCircleOutlined />}>
              <ReactECharts option={getSearchStrategyOption()} style={{ height: 300 }} />
            </Card>
          </Col>
          <Col span={8}>
            <Card title="用户反馈分布" extra={<QuestionCircleOutlined />}>
              <ReactECharts option={getUserFeedbackOption()} style={{ height: 300 }} />
            </Card>
          </Col>
          <Col span={8}>
            <Card title="热门查询" extra={<QuestionCircleOutlined />}>
              <ReactECharts option={getTopQueriesOption()} style={{ height: 300 }} />
            </Card>
          </Col>
        </Row>
      </div>
    );
  };

  return (
    <div className="analytics-container">
      <div style={{ marginBottom: 24 }}>
        <h2>检索分析</h2>
        <p>分析检索性能和用户行为，优化检索体验</p>
      </div>
      
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <div>
          <Radio.Group 
            value={timeRange} 
            onChange={e => setTimeRange(e.target.value)} 
            style={{ marginRight: 16 }}
            buttonStyle="solid"
          >
            <Radio.Button value="today">今日</Radio.Button>
            <Radio.Button value="week">本周</Radio.Button>
            <Radio.Button value="month">本月</Radio.Button>
            <Radio.Button value="custom">自定义</Radio.Button>
          </Radio.Group>
          
          {timeRange === 'custom' && (
            <RangePicker style={{ marginRight: 16 }} />
          )}
          
          <Select 
            value={knowledgeBase} 
            onChange={setKnowledgeBase} 
            style={{ width: 150 }}
          >
            <Option value="all">所有知识库</Option>
            <Option value="kb1">产品文档</Option>
            <Option value="kb2">技术文档</Option>
            <Option value="kb3">常见问题</Option>
            <Option value="kb4">用户指南</Option>
          </Select>
        </div>
        
        <div>
          <Button icon={<ReloadOutlined />} style={{ marginRight: 8 }}>刷新数据</Button>
          <Button type="primary" icon={<DownloadOutlined />}>导出报告</Button>
        </div>
      </div>
      
      <Tabs activeKey={activeTab} onChange={setActiveTab} type="card">
        <TabPane 
          tab={<span><BarChartOutlined />性能趋势</span>} 
          key="performance"
        >
          {renderPerformanceTrends()}
          {renderStrategyAnalysis()}
        </TabPane>
        <TabPane 
          tab={<span><UserOutlined />用户行为</span>} 
          key="userBehavior"
        >
          {renderUserBehaviorPanel()}
        </TabPane>
        <TabPane 
          tab={<span><PieChartOutlined />知识库分析</span>} 
          key="knowledgeBase"
        >
          <Card title="知识库使用情况" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <ReactECharts 
                  option={{
                    title: { text: '知识库检索分布', left: 'center' },
                    tooltip: { trigger: 'item' },
                    legend: { orient: 'vertical', left: 'left' },
                    series: [{
                      type: 'pie',
                      radius: '60%',
                      data: [
                        { value: 45, name: '产品文档' },
                        { value: 30, name: '技术文档' },
                        { value: 15, name: '常见问题' },
                        { value: 10, name: '用户指南' }
                      ],
                      emphasis: {
                        itemStyle: {
                          shadowBlur: 10,
                          shadowOffsetX: 0,
                          shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                      }
                    }]
                  }} 
                  style={{ height: 400 }} 
                />
              </Col>
              <Col span={12}>
                <ReactECharts 
                  option={{
                    title: { text: '知识库内容更新频率', left: 'center' },
                    tooltip: { trigger: 'axis' },
                    legend: { data: ['产品文档', '技术文档', '常见问题', '用户指南'] },
                    xAxis: { type: 'category', data: ['1月', '2月', '3月', '4月', '5月', '6月'] },
                    yAxis: { type: 'value' },
                    series: [
                      { name: '产品文档', type: 'line', data: [12, 15, 10, 18, 20, 15] },
                      { name: '技术文档', type: 'line', data: [8, 10, 12, 15, 10, 8] },
                      { name: '常见问题', type: 'line', data: [5, 8, 6, 10, 12, 8] },
                      { name: '用户指南', type: 'line', data: [3, 5, 8, 6, 4, 7] }
                    ]
                  }}
                  style={{ height: 400 }}
                />
              </Col>
            </Row>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default AnalyticsPage;