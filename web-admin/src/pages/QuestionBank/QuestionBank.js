import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Input, Select, message } from 'antd';
import { SearchOutlined, DeleteOutlined } from '@ant-design/icons';

const { Option } = Select;

const QuestionBankPage = () => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    subject: '',
    type: '',
    keyword: ''
  });

  const loadQuestions = async () => {
    setLoading(true);
    try {
      message.info('题库数据加载功能待实现');
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadQuestions();
  }, []);

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '科目', dataIndex: 'subject', key: 'subject' },
    { title: '题型', dataIndex: 'type', key: 'type' },
    { title: '难度', dataIndex: 'difficulty', key: 'difficulty' },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    {
      title: '操作',
      key: 'action',
      render: () => (
        <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
      )
    }
  ];

  return (
    <div>
      <Card title="题库管理">
        <div style={{ marginBottom: 16, display: 'flex', gap: 8 }}>
          <Select
            placeholder="科目"
            style={{ width: 120 }}
            value={filters.subject}
            onChange={(v) => setFilters({...filters, subject: v})}
            allowClear
          >
            <Option value="数学">数学</Option>
            <Option value="语文">语文</Option>
            <Option value="英语">英语</Option>
          </Select>

          <Select
            placeholder="题型"
            style={{ width: 120 }}
            value={filters.type}
            onChange={(v) => setFilters({...filters, type: v})}
            allowClear
          >
            <Option value="choice">选择题</Option>
            <Option value="blank">填空题</Option>
            <Option value="comprehensive">解答题</Option>
          </Select>

          <Input
            placeholder="关键词搜索"
            value={filters.keyword}
            onChange={(e) => setFilters({...filters, keyword: e.target.value})}
            style={{ width: 200 }}
          />

          <Button type="primary" icon={<SearchOutlined />} onClick={loadQuestions}>
            搜索
          </Button>
        </div>

        <Table
          dataSource={questions}
          columns={columns}
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 20 }}
        />
      </Card>
    </div>
  );
};

export default QuestionBankPage;
