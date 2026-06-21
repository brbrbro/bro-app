import React, { useState, useEffect } from 'react';
import { Upload, message, Card, List, Tag, Button, Select, Tabs, Form, Input } from 'antd';
import { InboxOutlined, FilePdfOutlined, FileWordOutlined, FileImageOutlined, FileTextOutlined } from '@ant-design/icons';
import { uploadFile, getBatches, importSingleQuestion } from '../../services/api';
import './Import.css';

const { Dragger } = Upload;
const { Option } = Select;
const { TextArea } = Input;

const examOptions = [
  { value: 'gaokao', label: '高考' },
  { value: 'dse', label: '香港 DSE' }
];
const subjectOptions = ['数学', '物理', '化学', '生物'];
const gradeOptions = ['高一', '高二', '高三', '中四', '中五', '中六'];

const ImportPage = () => {
  const [batches, setBatches] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();
  const [singleForm] = Form.useForm();

  useEffect(() => { loadBatches(); }, []);

  const loadBatches = async () => {
    const res = await getBatches();
    setBatches(res.data.batches || []);
  };

  const handleBatchUpload = async ({ file }) => {
    const values = form.getFieldsValue();
    if (!values.examType || !values.subject) {
      message.error('请选择考试体系和科目');
      return;
    }
    setUploading(true);
    try {
      const res = await uploadFile(file, values.examType, values.subject, values.grade || '', values.knowledgePoint || '不详');
      message.success(`解析完成：${res.data.total_questions} 道题等待审核`);
      loadBatches();
    } catch (e) {
      message.error(e.response?.data?.error || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleSingleSubmit = async (values) => {
    try {
      const res = await importSingleQuestion({
        text: values.text,
        exam_type: values.examType,
        subject: values.subject,
        grade: values.grade || '',
        knowledge_point: values.knowledgePoint || '不详',
        created_by: 'admin'
      });
      message.success(`单题解析成功：${res.data.total_questions} 道题等待审核`);
      singleForm.resetFields(['text']);
      loadBatches();
    } catch (e) {
      message.error(e.response?.data?.error || '单题导入失败');
    }
  };

  const getFileIcon = (type) => {
    if (type === 'pdf') return <FilePdfOutlined />;
    if (type === 'doc' || type === 'docx') return <FileWordOutlined />;
    if (['png', 'jpg', 'jpeg'].includes(type)) return <FileImageOutlined />;
    return <FileTextOutlined />;
  };

  const renderMetaForm = (targetForm) => (
    <Form form={targetForm} layout="inline" className="meta-form">
      <Form.Item name="examType" label="考试体系" rules={[{ required: true }]}>
        <Select style={{ width: 140 }} placeholder="考试体系">
          {examOptions.map(o => <Option key={o.value} value={o.value}>{o.label}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="subject" label="科目" rules={[{ required: true }]}>
        <Select style={{ width: 120 }} placeholder="科目">
          {subjectOptions.map(s => <Option key={s} value={s}>{s}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="grade" label="年级">
        <Select style={{ width: 120 }} placeholder="年级">
          {gradeOptions.map(g => <Option key={g} value={g}>{g}</Option>)}
        </Select>
      </Form.Item>
      <Form.Item name="knowledgePoint" label="知识点">
        <Input style={{ width: 160 }} placeholder="可选" />
      </Form.Item>
    </Form>
  );

  return (
    <div className="import-page">
      <Tabs defaultActiveKey="batch" items={[
        {
          key: 'batch',
          label: '试卷批量导入',
          children: (
            <Card title="上传试卷文件" className="upload-card">
              {renderMetaForm(form)}
              <Dragger customRequest={handleBatchUpload} showUploadList={false} disabled={uploading} accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.txt">
                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
                <p className="ant-upload-hint">支持 PDF、Word、图片、TXT；上传后进入待审核队列</p>
              </Dragger>
            </Card>
          )
        },
        {
          key: 'single',
          label: '单题导入',
          children: (
            <Card title="粘贴单题文本" className="upload-card">
              {renderMetaForm(singleForm)}
              <Form form={singleForm} layout="vertical" onFinish={handleSingleSubmit} className="single-form">
                <Form.Item name="text" label="题目内容" rules={[{ required: true, message: '请输入题目内容' }]}>
                  <TextArea rows={8} placeholder="例：1. 已知 x²=4，求 x。\n答案：±2\n解析：平方根定义。" />
                </Form.Item>
                <Button type="primary" htmlType="submit">解析单题</Button>
              </Form>
            </Card>
          )
        }
      ]} />

      <Card title="导入历史" className="history-card">
        <List
          dataSource={batches}
          renderItem={batch => (
            <List.Item>
              <List.Item.Meta
                avatar={getFileIcon(batch.source_type)}
                title={`${batch.source_file} (${batch.parsed_questions || 0} 题)`}
                description={`${batch.subject || '-'} / ${batch.grade || '-'} / ${batch.created_at}`}
              />
              <Tag color={batch.status === 'reviewing' ? 'orange' : batch.status === 'completed' ? 'green' : 'blue'}>{batch.status}</Tag>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default ImportPage;
