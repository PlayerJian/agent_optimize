import React from 'react';
import { Layout, Menu, Typography } from 'antd';
import { Routes, Route, Link } from 'react-router-dom';
import { SearchOutlined, BarChartOutlined, SettingOutlined } from '@ant-design/icons';
import './App.css';

// 页面组件
import SearchPage from './pages/SearchPage';
import AnalyticsPage from './pages/AnalyticsPage';
import SettingsPage from './pages/SettingsPage';

const { Header, Content, Footer } = Layout;
const { Title } = Typography;

function App() {
  return (
    <Layout className="app-container">
      <Header>
        <div className="logo">Dify</div>
        <Menu
          theme="dark"
          mode="horizontal"
          className="header-menu"
          defaultSelectedKeys={['search']}
          items={[
            {
              key: 'search',
              icon: <SearchOutlined />,
              label: <Link to="/">知识库检索</Link>,
            },
            {
              key: 'analytics',
              icon: <BarChartOutlined />,
              label: <Link to="/analytics">检索分析</Link>,
            },
            {
              key: 'settings',
              icon: <SettingOutlined />,
              label: <Link to="/settings">设置</Link>,
            },
          ]}
        />
      </Header>
      <Content className="site-layout-content">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Content>
      <Footer style={{ textAlign: 'center' }}>
        Dify 知识库检索增强与优化 ©{new Date().getFullYear()} Created by Dify Team
      </Footer>
    </Layout>
  );
}

export default App;