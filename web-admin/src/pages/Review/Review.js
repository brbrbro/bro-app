import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, Form, Input, Select, message } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { getBatches, getBatchQuestions, approveQuestion, rejectQuestion } from '../../services/api';
import './Review.css';

const { TextArea } = Input;
const { Option } = Select;

const ReviewPage = () => {
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [reviewModalVisible, setReviewModalVisible] = useState(false);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadBatches();
  }, []);

  const loadBatches = async () => {
    const res = await getBatches();
    setBatches(res.data.batches.filter(b => b.status === 'reviewing'));
  };

  const loadQuestions = async (batchId) => {
    setSelectedBatch(batchId);
    const res = await getBatchQuestions(batchId, 'pending');
    setQuestions(res.data.questions);
  };

  const openReviewModal = (question) => {
    setCurrentQuestion(question);
    form.setFieldsValue({
      content: question.content,
      options: question.options?.join('\n'),
      answer: question.answer,
      explanation: question.explanation,
      type: question.type,
      difficulty: question.difficulty,
      subject: question.subject
    });
    setReviewModalVisible(true);
  };

  const handleApprove = async (values) => {
    try {
      await approveQuestion(currentQuestion.id, {
        ...values,
        options: values.options?.split('\n').filter(o => o.trim()),
        region: 'mainland'
      });
      message.success('审核通过');
      setReviewModalVisible(false);
      loadQuestions(selectedBatch);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const handleReject = async () => {
    try {
      await rejectQuestion(currentQuestion.id, {
        notes: form.getFieldValue('reviewNotes')
      });
      message.success('已拒绝');
      setReviewModalVisible(false);
      loadQuestions(selectedBatch);
    } catch (error) {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '内容', dataIndex: 'content', key: 'content', ellipsis: true },
    { title: '题型', dataIndex: 'type', key: 'type' },
    { title: '难度', dataIndex: 'difficulty', key: 'difficulty' },
    { title: '置信度', dataIndex: 'confidence', key: 'confidence', render: v => `${(v * 100).toFixed(1)}%` },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button type="primary" icon={<EyeOutlined />} onClick={() => openReviewModal(record)}>
          审核
        </Button>
      )
    }
  ];

  return (
    <div className="review-page">
      <Card title="待审核批次" className="batch-card">
        {batches.map(batch => (
          <Button
            key={batch.id}
            type={selectedBatch === batch.id ? 'primary' : 'default'}
            onClick={() => loadQuestions(batch.id)}
            style={{ marginRight: 8, marginBottom: 8 }}
          >
            {batch.source_file} ({batch.parsed_questions}题)
          </Button>
        ))}
      </Card>

      {selectedBatch && (
        <Card title={`待审核题目 (${questions.length})`}>
          <Table
            dataSource={questions}
            columns={columns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
          />
        </Card>
      )}

      <Modal
        title="题目审核"
        visible={reviewModalVisible}
        onCancel={() => setReviewModalVisible(false)}
        width={800}
        footer={[
          <Button key="reject" danger onClick={handleReject}>拒绝</Button>,
          <Button key="approve" type="primary" onClick={() => form.submit()}>通过</Button>
        ]}
      >
        <Form form={form} onFinish={handleApprove} layout="vertical">
          <Form.Item label="题目内容" name="content" rules={[{ required: true }]}>
            <TextArea rows={4} />
          </Form.Item>

          <Form.Item label="选项（每行一个）" name="options">
            <TextArea rows={4} placeholder="A. 选项1&#10;B. 选项2&#10;C. 选项3&#10;D. 选项4" />
          </Form.Item>

          <Form.Item label="答案" name="answer">
            <Input />
          </Form.Item>

          <Form.Item label="解析" name="explanation">
            <TextArea rows={3} />
          </Form.Item>

          <Form.Item label="题型" name="type" rules={[{ required: true }]}>
            <Select>
              <Option value="choice">选择题</Option>
              <Option value="blank">填空题</Option>
              <Option value="comprehensive">解答题</Option>
            </Select>
          </Form.Item>

          <Form.Item label="难度" name="difficulty" rules={[{ required: true }]}>
            <Select>
              {[1, 2, 3, 4, 5].map(d => (
                <Option key={d} value={d}>{d}星</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item label="科目" name="subject" rules={[{ required: true }]}>
            <Input />
          </Form.Item>

          <Form.Item label="审核备注" name="reviewNotes">
            <TextArea rows={2} placeholder="拒绝时请填写原因" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ReviewPage;