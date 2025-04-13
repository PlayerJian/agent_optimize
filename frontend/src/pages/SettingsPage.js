import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Select, Switch, Slider, InputNumber, Button, Tabs, Table, Divider, Space, Tag, message, Radio, Checkbox } from 'antd';
import { SaveOutlined, PlusOutlined, DeleteOutlined, SyncOutlined, DatabaseOutlined, ApiOutlined, SettingOutlined, StarOutlined } from '@ant-design/icons';
import { settingsAPI, knowledgeBaseAPI } from '../services/api';

const { Option } = Select;
const { TabPane } = Tabs;



const SettingsPage = () => {
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('retrieval');
  const [cacheEnabled, setCacheEnabled] = useState(true);
  const [cacheSize, setCacheSize] = useState(500);
  const [cacheTTL, setCacheTTL] = useState(24);
  const [crossKbEnabled, setCrossKbEnabled] = useState(true);
  const [knowledgeBases, setKnowledgeBases] = useState([]);
  const [cacheStats, setCacheStats] = useState(null);
  const [settings, setSettings] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  // 在组件加载时获取数据
  useEffect(() => {
    loadData();
  }, []);

  // 加载数据
  const loadData = () => {
    setIsLoading(true);

    // 获取知识库列表
    knowledgeBaseAPI.getAll()
      .then(response => {
        const kbs = response.data.map(kb => ({
          key: kb.id,
          name: kb.name,
          documentCount: kb.document_count,
          lastUpdated: kb.last_updated,
          status: kb.status
        }));
        setKnowledgeBases(kbs);
      })
      .catch(error => {
        console.error('获取知识库失败:', error);
        message.error('获取知识库失败');
      });

    // 获取系统设置
    settingsAPI.getSettings()
      .then(response => {
        const data = response.data;
        setSettings(data);

        // 更新表单值
        form.setFieldsValue({
          defaultStrategy: data.default_search_strategy,
          semanticModel: data.semantic_model,
          maxResults: data.max_results,
          minScore: data.min_score,
          reranking: data.use_reranking,
          rerankingModel: data.reranking_model,
          clustering: data.use_clustering,
          clusterThreshold: data.cluster_threshold
        });

        // 更新缓存设置
        setCacheEnabled(data.cache_enabled);
        setCacheSize(data.cache_size);
        setCacheTTL(data.cache_ttl);
        setCrossKbEnabled(data.cross_kb_search_enabled);
      })
      .catch(error => {
        console.error('获取系统设置失败:', error);
        message.error('获取系统设置失败');

        // 保存设置
        const handleSaveSettings = (values) => {
          setIsLoading(true);

          // 转换为后端API需要的格式
          const settingsData = {
            default_search_strategy: values.defaultStrategy,
            semantic_model: values.semanticModel,
            max_results: values.maxResults,
            min_score: values.minScore,
            use_reranking: values.reranking,
            reranking_model: values.rerankingModel,
            use_clustering: values.clustering,
            cluster_threshold: values.clusterThreshold,
            cache_enabled: cacheEnabled,
            cache_size: cacheSize,
            cache_ttl: cacheTTL,
            cross_kb_search_enabled: crossKbEnabled
          };

          // 调用API保存设置
          settingsAPI.updateSettings(settingsData)
            .then(response => {
              message.success('设置已保存');
              setSettings(response.data);
              setIsLoading(false);
            })
            .catch(error => {
              console.error('保存设置失败:', error);
              message.error('保存设置失败');
              setIsLoading(false);
            });
        };

        // 获取缓存统计信息
        const handleGetCacheStats = () => {
          settingsAPI.getCacheStats()
            .then(response => {
              setCacheStats(response.data);
            })
            .catch(error => {
              console.error('获取缓存统计信息失败:', error);
              message.error('获取缓存统计信息失败');
            });
        };

        // 清空缓存
        const handleClearCache = () => {
          settingsAPI.clearCache()
            .then(() => {
              message.success('缓存已清空');
              handleGetCacheStats(); // 刷新缓存统计信息
            })
            .catch(error => {
              console.error('清空缓存失败:', error);
              message.error('清空缓存失败');
            });
        };

        // 知识库表格列配置
        const knowledgeBaseColumns = [
          {
            title: '知识库名称',
            dataIndex: 'name',
            key: 'name',
          },
          {
            title: '文档数量',
            dataIndex: 'documentCount',
            key: 'documentCount',
          },
          {
            title: '最后更新',
            dataIndex: 'lastUpdated',
            key: 'lastUpdated',
          },
          {
            title: '状态',
            dataIndex: 'status',
            key: 'status',
            render: (status) => (
              <Tag color={status === 'active' ? 'green' : 'red'}>
                {status === 'active' ? '已启用' : '已禁用'}
              </Tag>
            ),
          },
          {
            title: '操作',
            key: 'action',
            render: (_, record) => (
              <Space size="middle">
                <a>编辑</a>
                <a>同步</a>
                <a>禁用</a>
              </Space>
            ),
          },
        ];

        // 渲染检索设置面板
        const renderRetrievalSettings = () => {
          return (
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                defaultStrategy: 'auto',
                semanticModel: 'default',
                maxResults: 10,
                minScore: 0.7,
                reranking: true,
                rerankingModel: 'default',
                clustering: true,
                clusterThreshold: 0.8,
              }}
              onFinish={handleSaveSettings}
            >
              <Card title="检索策略设置" style={{ marginBottom: 16 }}>
                <Form.Item name="defaultStrategy" label="默认检索策略">
                  <Radio.Group>
                    <Radio.Button value="auto">智能选择</Radio.Button>
                    <Radio.Button value="semantic">语义检索</Radio.Button>
                    <Radio.Button value="fulltext">全文检索</Radio.Button>
                    <Radio.Button value="hybrid">混合检索</Radio.Button>
                  </Radio.Group>
                </Form.Item>

                <Form.Item name="semanticModel" label="语义模型">
                  <Select>
                    <Option value="default">默认模型</Option>
                    <Option value="model1">高精度模型</Option>
                    <Option value="model2">高性能模型</Option>
                    <Option value="custom">自定义模型</Option>
                  </Select>
                </Form.Item>

                <Form.Item name="maxResults" label="最大结果数">
                  <Slider
                    min={1}
                    max={50}
                    onChange={value => form.setFieldsValue({ maxResults: value })}
                    marks={{
                      1: '1',
                      10: '10',
                      20: '20',
                      30: '30',
                      40: '40',
                      50: '50'
                    }}
                  />
                </Form.Item>

                <Form.Item name="minScore" label="最小相关性分数">
                  <Slider
                    min={0}
                    max={1}
                    step={0.05}
                    onChange={value => form.setFieldsValue({ minScore: value })}
                    marks={{
                      0: '0',
                      0.5: '0.5',
                      1: '1'
                    }}
                  />
                </Form.Item>
              </Card>

              <Card title="结果优化设置" style={{ marginBottom: 16 }}>
                <Form.Item name="reranking" label="启用结果重排序" valuePropName="checked">
                  <Switch />
                </Form.Item>

                <Form.Item name="rerankingModel" label="重排序模型">
                  <Select>
                    <Option value="default">默认模型</Option>
                    <Option value="quality">质量优先</Option>
                    <Option value="feedback">反馈优先</Option>
                    <Option value="custom">自定义模型</Option>
                  </Select>
                </Form.Item>

                <Form.Item name="clustering" label="启用结果聚类" valuePropName="checked">
                  <Switch />
                </Form.Item>

                <Form.Item name="clusterThreshold" label="聚类相似度阈值">
                  <Slider
                    min={0}
                    max={1}
                    step={0.05}
                    onChange={value => form.setFieldsValue({ clusterThreshold: value })}
                    marks={{
                      0: '0',
                      0.5: '0.5',
                      1: '1'
                    }}
                  />
                </Form.Item>
              </Card>

              <Form.Item>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                  保存检索设置
                </Button>
              </Form.Item>
            </Form>
          );
        };

        // 渲染缓存设置面板
        const renderCacheSettings = () => {
          return (
            <Card title="检索缓存设置" style={{ marginBottom: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ marginRight: 16 }}>启用检索缓存：</span>
                  <Switch checked={cacheEnabled} onChange={setCacheEnabled} />
                </div>

                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ marginRight: 16 }}>缓存容量上限：</span>
                  <InputNumber
                    min={100}
                    max={10000}
                    value={cacheSize}
                    onChange={setCacheSize}
                    disabled={!cacheEnabled}
                    addonAfter="条"
                  />
                </div>

                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ marginRight: 16 }}>缓存过期时间：</span>
                  <InputNumber
                    min={1}
                    max={72}
                    value={cacheTTL}
                    onChange={setCacheTTL}
                    disabled={!cacheEnabled}
                    addonAfter="小时"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: 16 }}>
                <Button type="primary" icon={<SaveOutlined />}>
                  保存缓存设置
                </Button>
                <Button icon={<DeleteOutlined />} disabled={!cacheEnabled}>
                  清空缓存
                </Button>
                <Button icon={<SyncOutlined />} disabled={!cacheEnabled}>
                  刷新缓存
                </Button>
              </div>
            </Card>
          );
        };

        // 渲染跨库检索设置面板
        const renderCrossKbSettings = () => {
          return (
            <Card title="跨知识库检索设置" style={{ marginBottom: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ marginRight: 16 }}>启用跨知识库检索：</span>
                  <Switch checked={crossKbEnabled} onChange={setCrossKbEnabled} />
                </div>

                <div style={{ marginBottom: 16 }}>
                  <span style={{ display: 'block', marginBottom: 8 }}>默认检索知识库：</span>
                  <Select
                    mode="multiple"
                    style={{ width: '100%' }}
                    placeholder="选择默认检索的知识库"
                    defaultValue={['kb1', 'kb2']}
                    disabled={!crossKbEnabled}
                  >
                    {mockKnowledgeBases.map(kb => (
                      <Option key={kb.key} value={kb.key}>{kb.name}</Option>
                    ))}
                  </Select>
                </div>

                <div style={{ marginBottom: 16 }}>
                  <span style={{ display: 'block', marginBottom: 8 }}>跨库检索策略：</span>
                  <Radio.Group defaultValue="parallel" disabled={!crossKbEnabled}>
                    <Radio.Button value="parallel">并行检索</Radio.Button>
                    <Radio.Button value="sequential">顺序检索</Radio.Button>
                    <Radio.Button value="adaptive">自适应检索</Radio.Button>
                  </Radio.Group>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ marginRight: 16 }}>跨库结果合并方式：</span>
                  <Select
                    style={{ width: 200 }}
                    defaultValue="interleave"
                    disabled={!crossKbEnabled}
                  >
                    <Option value="interleave">交错合并</Option>
                    <Option value="append">追加合并</Option>
                    <Option value="weighted">加权合并</Option>
                  </Select>
                </div>
              </div>

              <Button type="primary" icon={<SaveOutlined />}>
                保存跨库检索设置
              </Button>
            </Card>
          );
        };

        // 渲染用户反馈设置面板
        const renderFeedbackSettings = () => {
          return (
            <Card title="用户反馈设置" style={{ marginBottom: 16 }}>
              <div style={{ marginBottom: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ marginRight: 16 }}>启用用户反馈收集：</span>
                  <Switch defaultChecked />
                </div>

                <div style={{ display: 'flex', alignItems: 'center', marginBottom: 16 }}>
                  <span style={{ marginRight: 16 }}>反馈影响检索排序：</span>
                  <Switch defaultChecked />
                </div>

                <div style={{ marginBottom: 16 }}>
                  <span style={{ display: 'block', marginBottom: 8 }}>反馈权重：</span>
                  <Slider
                    defaultValue={0.3}
                    min={0}
                    max={1}
                    step={0.05}
                    marks={{
                      0: '0',
                      0.3: '0.3',
                      0.5: '0.5',
                      1: '1'
                    }}
                  />
                </div>

                <div style={{ marginBottom: 16 }}>
                  <span style={{ display: 'block', marginBottom: 8 }}>反馈收集方式：</span>
                  <Checkbox.Group defaultValue={['thumbs', 'rating', 'comment']}>
                    <Checkbox value="thumbs">点赞/踩</Checkbox>
                    <Checkbox value="rating">星级评分</Checkbox>
                    <Checkbox value="comment">评论反馈</Checkbox>
                  </Checkbox.Group>
                </div>
              </div>

              <Button type="primary" icon={<SaveOutlined />}>
                保存反馈设置
              </Button>
            </Card>
          );
        };

        // 渲染知识库管理面板
        const renderKnowledgeBaseManagement = () => {
          return (
            <div>
              <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end' }}>
                <Button type="primary" icon={<PlusOutlined />}>
                  添加知识库
                </Button>
              </div>

              <Table
                columns={knowledgeBaseColumns}
                dataSource={mockKnowledgeBases}
                pagination={false}
              />
            </div>
          );
        };

        return (
          <div className="settings-container">
            <div style={{ marginBottom: 24 }}>
              <h2>检索设置</h2>
              <p>配置知识库检索的各项参数和功能</p>
            </div>

            <Tabs activeKey={activeTab} onChange={setActiveTab}>
              <TabPane
                tab={<span><SettingOutlined />检索策略</span>}
                key="retrieval"
              >
                {renderRetrievalSettings()}
              </TabPane>
              <TabPane
                tab={<span><DatabaseOutlined />缓存管理</span>}
                key="cache"
              >
                {renderCacheSettings()}
              </TabPane>
              <TabPane
                tab={<span><ApiOutlined />跨库检索</span>}
                key="crossKb"
              >
                {renderCrossKbSettings()}
              </TabPane>
              <TabPane
                tab={<span><StarOutlined />用户反馈</span>}
                key="feedback"
              >
                {renderFeedbackSettings()}
              </TabPane>
              <TabPane
                tab={<span><DatabaseOutlined />知识库管理</span>}
                key="knowledgeBase"
              >
                {renderKnowledgeBaseManagement()}
              </TabPane>
            </Tabs>
          </div>
        );
      });
  };
};
export default SettingsPage;