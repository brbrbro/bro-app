import React, { useEffect, useState } from 'react';
import { Button, Card, DatePicker, Drawer, Form, Input, Popconfirm, Select, Space, Table, Tag, message } from 'antd';
import { DeleteOutlined, EyeOutlined, ReloadOutlined, SearchOutlined } from '@ant-design/icons';
import { deleteAdminBatch, getAdminBatches, reparseAdminBatch } from '../../services/api';
import './ImportBatches.css';

const { Option } = Select;
const { RangePicker } = DatePicker;

const ImportBatchesPage = () => {
  const [batches, setBatches] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState(null);
  const [form] = Form.useForm();

  const loadBatches = async () => {
    setLoading(true);
    try {
      const values = form.getFieldsValue();
      const params = { ...values };
      if (values.date_range?.length === 2) {
        params.start_date = values.date_range[0].startOf('day').toISOString();
        params.end_date = values.date_range[1].endOf('day').toISOString();
      }
      delete params.date_range;
      const res = await getAdminBatches(params);
      setBatches(res.data.batches || res.data.items || []);
    } catch (e) {
      message.error(e.response?.data?.error || '加载批次失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadBatches(); }, []);

  const handleReparse = async (id) => {
    try {
      await reparseAdminBatch(id);
      message.success('已发起重解析');
      loadBatches();
    } catch (e) {
      message.error(e.response?.data?.error || '重解析失败');
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteAdminBatch(id);
      message.success('已删除');
      loadBatches();
    } catch (e) {
      message.error(e.response?.data?.error || '删除失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '文件', dataIndex: 'source_file', key: 'source_file', ellipsis: true },
    { title: '类型', dataIndex: 'source_type', key: 'source_type', width: 100 },
    { title: '考试类型', dataIndex: 'exam_type', key: 'exam_type', width: 120 },
    { title: '科目', dataIndex: 'subject', key: 'subject', width: 100 },
    { title: '年级', dataIndex: 'grade', key: 'grade', width: 100 },
    { title: '知识点', dataIndex: 'knowledge_point', key: 'knowledge_point', width: 150, ellipsis: true },
    { title: '状态', dataIndex: 'status', key: 'status', width: 110, render: status => <Tag>{status}</Tag> },
    { title: '失败原因', dataIndex: 'failure_reason', key: 'failure_reason', width: 180, ellipsis: true },
    { title: '解析/总数', key: 'parsed_total', width: 110, render: (_, row) => `${row.parsed_questions || row.parsed_count || 0}/${row.total_questions || row.total_count || 0}` },
    { title: '已通过', dataIndex: 'approved_questions', key: 'approved_questions', width: 90 },
    { title: '低置信', dataIndex: 'low_confidence_count', key: 'low_confidence_count', width: 90 },
    { title: '成功率', dataIndex: 'success_rate', key: 'success_rate', width: 100, render: value => value === undefined || value === null ? '-' : `${Math.round(Number(value) * 100)}%` },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
    {
      title: '操作',
      key: 'actions',
      width: 190,
      render: (_, row) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />} onClick={() => setDetail(row)}>详情</Button>
          <Button type="link" onClick={() => { window.location.href = `/ops/review?batch=${row.id}`; }}>审核</Button>
          <Button type="link" icon={<ReloadOutlined />} onClick={() => handleReparse(row.id)}>重解析</Button>
          <Popconfirm title="确认删除该批次？" onConfirm={() => handleDelete(row.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>删除</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <Card title="导入批次运营" className="ops-card">
      <Form form={form} layout="inline" className="ops-filter" onFinish={loadBatches}>
        <Form.Item name="status" label="状态">
          <Select allowClear placeholder="状态" style={{ width: 140 }}>
            <Option value="processing">processing</Option>
            <Option value="reviewing">reviewing</Option>
            <Option value="completed">completed</Option>
            <Option value="failed">failed</Option>
          </Select>
        </Form.Item>
        <Form.Item name="subject" label="科目"><Input placeholder="科目" style={{ width: 140 }} /></Form.Item>
        <Form.Item name="source_type" label="来源类型"><Input placeholder="source_type" style={{ width: 140 }} /></Form.Item>
        <Form.Item name="date_range" label="创建时间"><RangePicker /></Form.Item>
        <Form.Item><Button type="primary" htmlType="submit" icon={<SearchOutlined />}>查询</Button></Form.Item>
      </Form>
      <Table rowKey="id" columns={columns} dataSource={batches} loading={loading} scroll={{ x: 1600 }} pagination={{ pageSize: 20 }} />
      <Drawer title="批次详情" width={640} open={!!detail} onClose={() => setDetail(null)}>
        <pre>{JSON.stringify(detail, null, 2)}</pre>
      </Drawer>
    </Card>
  );
};

export default ImportBatchesPage;
