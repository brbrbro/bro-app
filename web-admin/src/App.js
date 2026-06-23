import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  UploadOutlined,
  CheckCircleOutlined,
  DatabaseOutlined,
  WarningOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import ImportPage from './pages/Import/Import';
import ReviewPage from './pages/Review/Review';
import ImportBatchesPage from './pages/QuestionOps/ImportBatches';
import QuestionBankOpsPage from './pages/QuestionOps/QuestionBankOps';
import QualityIssuesPage from './pages/QuestionOps/QualityIssues';
import ImportStatsPage from './pages/QuestionOps/ImportStats';

const { Header, Sider, Content } = Layout;

const menuItems = [
  {
    type: 'group',
    label: '题库运营',
    children: [
      {
        key: '/import',
        icon: <UploadOutlined />,
        label: <Link to="/import">题目导入</Link>
      },
      {
        key: '/ops/import-batches',
        icon: <UploadOutlined />,
        label: <Link to="/ops/import-batches">导入批次</Link>
      },
      {
        key: '/ops/review',
        icon: <CheckCircleOutlined />,
        label: <Link to="/ops/review">审核校验</Link>
      },
      {
        key: '/ops/questions',
        icon: <DatabaseOutlined />,
        label: <Link to="/ops/questions">题库管理</Link>
      },
      {
        key: '/ops/quality',
        icon: <WarningOutlined />,
        label: <Link to="/ops/quality">质量问题</Link>
      },
      {
        key: '/ops/stats',
        icon: <BarChartOutlined />,
        label: <Link to="/ops/stats">识别统计</Link>
      }
    ]
  }
];

const AppLayout = () => {
  const location = useLocation();
  const selectedKey = location.pathname === '/review' ? '/ops/review'
    : location.pathname === '/bank' ? '/ops/questions'
      : location.pathname;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider theme="light">
        <div style={{ padding: '16px', fontSize: '18px', fontWeight: 'bold', textAlign: 'center' }}>
          BRO 管理后台
        </div>
        <Menu mode="inline" selectedKeys={[selectedKey]} items={menuItems} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', fontSize: '18px' }}>
          题库导入平台
        </Header>
        <Content style={{ margin: '24px', padding: '24px', background: '#fff' }}>
          <Routes>
            <Route path="/" element={<Navigate to="/ops/import-batches" replace />} />
            <Route path="/ops/import-batches" element={<ImportBatchesPage />} />
            <Route path="/ops/review" element={<ReviewPage />} />
            <Route path="/ops/questions" element={<QuestionBankOpsPage />} />
            <Route path="/ops/quality" element={<QualityIssuesPage />} />
            <Route path="/ops/stats" element={<ImportStatsPage />} />
            <Route path="/import" element={<ImportPage />} />
            <Route path="/review" element={<ReviewPage />} />
            <Route path="/bank" element={<QuestionBankOpsPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
};

function App() {
  return (
    <Router>
      <AppLayout />
    </Router>
  );
}

export default App;
