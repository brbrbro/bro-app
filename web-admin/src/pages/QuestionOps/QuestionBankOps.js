import React, { useEffect, useState } from 'react';
import { Button, Card, Drawer, Form, Input, Popconfirm, Select, Space, Table, Tag, message } from 'antd';
import { DeleteOutlined, EditOutlined, EyeOutlined, SearchOutlined, StopOutlined, UndoOutlined } from '@ant-design/icons';
import { archiveAdminQuestion, deleteAdminQuestion, getAdminQuestions, updateAdminQuestion } from '../../services/api';
import './QuestionBankOps.css';

const { TextArea } = Input;
const { Option } = Select;

const QuestionBankOpsPage = () => {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [current, setCurrent] = useState(null);
  const [filterForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const res = await getAdminQuestions(filterForm.getFieldsValue());
      setQuestions(res.data.questions || res.data.items || []);
    } catch (e) {
      message.error(e.response?.data?.error || '加载题库失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadQuestions(); }, []);

  const openEditor = (question) => {
    setCurrent(question);
    editForm.setFieldsValue({
      ...question,
      options: Array.isArray(question.options) ? question.options.map(o => typeof o === 'string' ? o : `${o.key || ''}. ${o.text || ''}`).join('\n') : question.options
    });
    setDrawerOpen(true);
  };

  const handleSave = async () => {
    const values = await editForm.validateFields();
    const payload = {
      ...values,
      options: (values.options || '').split('\n').map(line => line.trim()).filter(Boolean)
    };
    try {
      await updateAdminQuestion(current.id, payload);
      message.success('已保存');
      setDrawerOpen(false);
      loadQuestions();
    } catch (e) {
      message.error(e.response?.data?.error || '保存失败');
    }
  };

  const handleArchive = async (id) => {
    try {
      await archiveAdminQuestion(id);
      message.success('已下架');
      loadQuestions();
    } catch (e) {
      message.error(e.response?.data?.error || '下架失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteAdminQuestion(id);
      message.success('已删除');
      loadQuestions();
    } catch (e) {
      message.error(e.response?.data?.error || '删除失败');
    }
  };

  const handleUnarchive = async (id) => {
    try {
      await updateAdminQuestion(id, { status: 'approved' });
      message.success('已恢复');
      loadQuestions();
    } catch (e) {
      message.error(e.response?.data?.error || '恢复失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '科目', dataIndex: 'subject', key: 'subject', width: 100 },
    { title: '年级', dataIndex: 'grade', key: 'grade', width: 100 },
    { title: '知识点', dataIndex: 'knowledge_point', key: 'knowledge_point', width: 160, ellipsis: true },
    { title: '题型', dataIndex: 'type', key: 'type', width: 110 },
    { title: '难度', dataIndex: 'difficulty', key: 'difficulty', width: 80 },
    { title: '来源', dataIndex: 'source', key: 'source', width: 120 },
    { title: '状态', dataIndex: 'status', key: 'status', width: 100, render: status => <Tag>{status}</Tag> },
    { title: '做题次数', dataIndex: 'solved_count', key: 'solved_count', width: 100 },
    { title: '正确率', dataIndex: 'correct_rate', key: 'correct_rate', width: 100, render: value => value === undefined || value === null ? '-' : `${Math.round(Number(value) * 100)}%` },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    {
      title: '操作',
      key: 'actions',
      width: 260,
      render: (_, row) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => setDetail(row)}>详情</Button>
          <Button type="link" icon={<EditOutlined />} onClick={() => openEditor(row)}>编辑</Button>
          {row.status === 'archived' && <Button type="link" icon={<UndoOutlined />} onClick={() => handleUnarchive(row.id)}>恢复</Button>}
          {row.status !== 'archived' && <Button type="link" icon={<StopOutlined />} onClick={() => handleArchive(row.id)}>下架</Button>}
          <Popconfirm title="确认删除该题？" onConfirm={() => handleDelete(row.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <Card title="正式题库运营" className="ops-card">
      <Form form={filterForm} layout="inline" className="ops-filter" onFinish={loadQuestions}>
        <Form.Item name="keyword" label="关键词"><Input placeholder="题干关键词" style={{ width: 180 }} /></Form.Item>
        <Form.Item name="subject" label="科目"><Input placeholder="科目" style={{ width: 120 }} /></Form.Item>
        <Form.Item name="grade" label="年级"><Input placeholder="年级" style={{ width: 120 }} /></Form.Item>
        <Form.Item name="knowledge_point" label="知识点"><Input placeholder="知识点" style={{ width: 160 }} /></Form.Item>
        <Form.Item name="type" label="题型">
          <Select allowClear placeholder="题型" style={{ width: 130 }}>
            <Option value="choice">choice</Option>
            <Option value="blank">blank</Option>
            <Option value="comprehensive">comprehensive</Option>
            <Option value="unknown">unknown</Option>
          </Select>
        </Form.Item>
        <Form.Item name="difficulty" label="难度"><Select allowClear placeholder="难度" style={{ width: 100 }}>{[1,2,3,4,5].map(d => <Option key={d} value={d}>{d}</Option>)}</Select></Form.Item>
        <Form.Item name="source" label="来源"><Input placeholder="来源" style={{ width: 120 }} /></Form.Item>
        <Form.Item name="status" label="状态">
          <Select allowClear placeholder="状态" style={{ width: 120 }}>
            <Option value="approved">approved</Option>
            <Option value="archived">archived</Option>
            <Option value="rejected">rejected</Option>
          </Select>
        </Form.Item>
        <Form.Item><Button type="primary" htmlType="submit" icon={<SearchOutlined />}>搜索</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={questions} loading={loading} scroll={{ x: 1700 }} pagination={{ pageSize: 20 }} />
      <Drawer title="题目详情" width={720} open={!!detail} onClose={() => setDetail(null)}>
        {detail && <div className="question-detail">
          <Card size="small" title="题干" className="detail-card">
            <div className="detail-content">{detail.content || '—'}</div>
          </Card>
          <Card size="small" title="答案" className="detail-card">
            <div className="detail-answer">{detail.answer || '—'}</div>
          </Card>
          <Card size="small" title="解析" className="detail-card">
            <div className="detail-explanation">{detail.explanation || '—'}</div>
          </Card>
          {Array.isArray(detail.options) && detail.options.length > 0 && <Card size="small" title="选项" className="detail-card">
            {detail.options.map((option, index) => (
              <div key={index} className="detail-option">
                {typeof option === 'string' ? option : `${option.key || ''}. ${option.text || ''}`}
              </div>
            ))}
          </Card>}
          <Card size="small" title="基础信息" className="detail-card">
            <Space wrap>
              <Tag>科目：{detail.subject || '—'}</Tag>
              <Tag>年级：{detail.grade || '—'}</Tag>
              <Tag>知识点：{detail.knowledge_point || '—'}</Tag>
              <Tag>题型：{detail.type || '—'}</Tag>
              <Tag>难度：{detail.difficulty || '—'}</Tag>
              <Tag>状态：{detail.status || '—'}</Tag>
            </Space>
          </Card>
        </div>}
      </Drawer>
      <Drawer title="编辑题目" width={640} open={drawerOpen} onClose={() => setDrawerOpen(false)} extra={<Button type="primary" onClick={handleSave}>保存</Button>}>
        <Form form={editForm} layout="vertical">
          <Form.Item label="题干" name="content" rules={[{ required: true }]}><TextArea rows={5} /></Form.Item>
          <Form.Item label="选项" name="options"><TextArea rows={4} /></Form.Item>
          <Form.Item label="答案" name="answer"><Input /></Form.Item>
          <Form.Item label="解析" name="explanation"><TextArea rows={4} /></Form.Item>
          <Form.Item label="科目" name="subject"><Input /></Form.Item>
          <Form.Item label="年级" name="grade"><Input /></Form.Item>
          <Form.Item label="知识点" name="knowledge_point"><Input /></Form.Item>
          <Form.Item label="题型" name="type"><Input /></Form.Item>
          <Form.Item label="难度" name="difficulty"><Select>{[1,2,3,4,5].map(d => <Option key={d} value={d}>{d}</Option>)}</Select></Form.Item>
          <Form.Item label="状态" name="status"><Input /></Form.Item>
        </Form>
      </Drawer>
    </Card>
  );
};

export default QuestionBankOpsPage;
