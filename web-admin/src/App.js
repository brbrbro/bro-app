import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  UploadOutlined,
  CheckCircleOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import ImportPage from './pages/Import/Import';
import ReviewPage from './pages/Review/Review';
import QuestionBankPage from './pages/QuestionBank/QuestionBank';

const { Header, Sider, Content } = Layout;

function App() {
  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider theme="light">
          <div style={{ padding: '16px', fontSize: '18px', fontWeight: 'bold', textAlign: 'center' }}>
            BRO 管理后台
          </div>
          <Menu mode="inline" defaultSelectedKeys={['1']}>
            <Menu.Item key="1" icon={<UploadOutlined />}>
              <Link to="/">题目导入</Link>
            </Menu.Item>
            <Menu.Item key="2" icon={<CheckCircleOutlined />}>
              <Link to="/review">审核校验</Link>
            </Menu.Item>
            <Menu.Item key="3" icon={<DatabaseOutlined />}>
              <Link to="/bank">题库管理</Link>
            </Menu.Item>
          </Menu>
        </Sider>
        <Layout>
          <Header style={{ background: '#fff', padding: '0 24px', fontSize: '18px' }}>
            题库导入平台
          </Header>
          <Content style={{ margin: '24px', padding: '24px', background: '#fff' }}>
            <Routes>
              <Route path="/" element={<ImportPage />} />
              <Route path="/review" element={<ReviewPage />} />
              <Route path="/bank" element={<QuestionBankPage />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;
