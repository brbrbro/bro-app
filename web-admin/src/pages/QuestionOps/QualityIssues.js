import React, { useEffect, useState } from 'react';
import { Button, Card, Form, Input, Popconfirm, Select, Space, Table, Tag, message } from 'antd';
import { DeleteOutlined, ReloadOutlined, StopOutlined } from '@ant-design/icons';
import { archiveAdminQuestion, deleteAdminQuestion, getQualityIssues } from '../../services/api';
import './QualityIssues.css';

const { Option } = Select;

const issueTypes = [
  'missing_answer',
  'missing_explanation',
  'invalid_options',
  'duplicate_content',
  'unknown_type',
  'missing_taxonomy',
  'low_confidence_import'
];

const QualityIssuesPage = () => {
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form] = Form.useForm();

  const loadIssues = async () => {
    setLoading(true);
    try {
      const res = await getQualityIssues(form.getFieldsValue());
      setIssues(res.data.issues || res.data.items || []);
    } catch (e) {
      message.error(e.response?.data?.error || '加载质量问题失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadIssues(); }, []);

  const handleArchive = async (questionId) => {
    try {
      await archiveAdminQuestion(questionId);
      message.success('已下架');
      loadIssues();
    } catch (e) {
      message.error(e.response?.data?.error || '下架失败');
    }
  };

  const handleDelete = async (questionId) => {
    try {
      await deleteAdminQuestion(questionId);
      message.success('已删除');
      loadIssues();
    } catch (e) {
      message.error(e.response?.data?.error || '删除失败');
    }
  };

  const handleIgnore = (row) => {
    setIssues(items => items.filter(item => item !== row));
    message.success('已忽略');
  };

  const columns = [
    { title: '问题类型', dataIndex: 'issue_type', key: 'issue_type', width: 180 },
    { title: '严重级别', dataIndex: 'severity', key: 'severity', width: 120, render: severity => <Tag color={severity === 'high' ? 'red' : severity === 'medium' ? 'orange' : 'blue'}>{severity}</Tag> },
    { title: '正式题ID', dataIndex: 'question_id', key: 'question_id', width: 120 },
    { title: '解析题ID', dataIndex: 'parsed_question_id', key: 'parsed_question_id', width: 120 },
    { title: '科目', dataIndex: 'subject', key: 'subject', width: 100 },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '建议', dataIndex: 'suggestion', key: 'suggestion', ellipsis: true },
    {
      title: '操作',
      key: 'action',
      width: 260,
      render: (_, row) => (
        <Space>
          <Button type="link" onClick={() => { window.location.href = row.question_id ? `/ops/questions?id=${row.question_id}` : `/ops/review?question=${row.parsed_question_id}`; }}>Open</Button>
          {row.question_id && <Button type="link" icon={<StopOutlined />} onClick={() => handleArchive(row.question_id)}>下架</Button>}
          {row.question_id && <Popconfirm title="确认删除该题？" onConfirm={() => handleDelete(row.question_id)}><Button type="link" danger icon={<DeleteOutlined />}>删除</Button></Popconfirm>}
          <Button type="link" onClick={() => handleIgnore(row)}>忽略</Button>
        </Space>
      )
    }
  ];

  return (
    <Card title="质量问题" className="ops-card">
      <Form form={form} layout="inline" className="ops-filter" onFinish={loadIssues}>
        <Form.Item name="issue_type" label="问题类型">
          <Select allowClear placeholder="issue_type" style={{ width: 240 }}>
            {issueTypes.map(type => <Option key={type} value={type}>{type}</Option>)}
          </Select>
        </Form.Item>
        <Form.Item name="severity" label="严重级别">
          <Select allowClear placeholder="severity" style={{ width: 140 }}>
            <Option value="high">high</Option>
            <Option value="medium">medium</Option>
            <Option value="low">low</Option>
          </Select>
        </Form.Item>
        <Form.Item name="subject" label="科目"><Input placeholder="科目" style={{ width: 120 }} /></Form.Item>
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">查询</Button>
            <Button icon={<ReloadOutlined />} onClick={loadIssues}>Refresh</Button>
          </Space>
        </Form.Item>
      </Form>
      <Table rowKey={(row) => `${row.issue_type}-${row.question_id || row.parsed_question_id}`} columns={columns} dataSource={issues} loading={loading} scroll={{ x: 1300 }} pagination={{ pageSize: 20 }} />
    </Card>
  );
};

export default QualityIssuesPage;
