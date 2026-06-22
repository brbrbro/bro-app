import React, { useEffect, useState } from 'react';
import { Button, Card, Form, Input, List, Select, Space, Tag, message, Modal } from 'antd';
import { CheckOutlined, CloseOutlined, SaveOutlined, SplitCellsOutlined, MergeCellsOutlined } from '@ant-design/icons';
import { getBatches, getBatchQuestions, updateParsedQuestion, approveQuestion, rejectQuestion, splitParsedQuestion, mergeParsedQuestion, approveSafeQuestions } from '../../services/api';
import './Review.css';

const { TextArea } = Input;
const { Option } = Select;

const ReviewPage = () => {
  const [batches, setBatches] = useState([]);
  const [selectedBatch, setSelectedBatch] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [current, setCurrent] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => { loadBatches(); }, []);

  const loadBatches = async () => {
    const res = await getBatches();
    setBatches((res.data.batches || []).filter(b => ['reviewing', 'processing', 'failed'].includes(b.status)));
  };

  const loadQuestions = async (batchId) => {
    setSelectedBatch(batchId);
    const res = await getBatchQuestions(batchId, 'pending');
    setQuestions(res.data.questions || []);
    setCurrent(null);
  };

  const selectQuestion = (q) => {
    setCurrent(q);
    form.setFieldsValue({
      content: q.content,
      options: (q.options || []).map(o => typeof o === 'string' ? o : `${o.key || ''}. ${o.text || ''}`).join('\n'),
      answer: q.answer,
      explanation: q.explanation,
      type: q.type,
      difficulty: q.difficulty,
      subject: q.subject,
      grade: q.grade,
      knowledge_point: q.knowledge_point,
      formula_latex: (q.formula_latex || []).join('\n')
    });
  };

  const valuesToPayload = (values) => ({
    ...values,
    options: (values.options || '').split('\n').map(line => line.trim()).filter(Boolean),
    formula_latex: (values.formula_latex || '').split('\n').map(line => line.trim()).filter(Boolean)
  });

  const saveDraft = async () => {
    if (!current) return;
    const values = await form.validateFields();
    const res = await updateParsedQuestion(current.id, valuesToPayload(values));
    message.success('已保存');
    const updated = res.data.question;
    setCurrent(updated);
    setQuestions(qs => qs.map(q => q.id === updated.id ? updated : q));
  };

  const approve = async () => {
    if (!current) return;
    const values = await form.validateFields();
    await updateParsedQuestion(current.id, valuesToPayload(values));
    await approveQuestion(current.id, { ...valuesToPayload(values), region: 'mainland' });
    message.success('已通过并入库');
    loadQuestions(selectedBatch);
  };

  const reject = async () => {
    if (!current) return;
    await rejectQuestion(current.id, { notes: '管理员驳回' });
    message.success('已驳回');
    loadQuestions(selectedBatch);
  };

  const splitQuestion = async () => {
    if (!current) return;
    const values = await form.validateFields();
    Modal.confirm({
      title: '拆分题目',
      content: '将当前题复制拆分为两条待审核题，第二题内容可在生成后编辑。',
      onOk: async () => {
        await splitParsedQuestion(current.id, {
          first: valuesToPayload(values),
          second: { content: '新拆分题目', answer: '', options: [], explanation: '' }
        });
        message.success('已拆分');
        loadQuestions(selectedBatch);
      }
    });
  };

  const mergeToPrevious = async () => {
    if (!current) return;
    const idx = questions.findIndex(q => q.id === current.id);
    if (idx <= 0) { message.warning('没有上一题可合并'); return; }
    await mergeParsedQuestion(current.id, questions[idx - 1].id);
    message.success('已合并到上一题');
    loadQuestions(selectedBatch);
  };

  const approveSafe = async () => {
    if (!selectedBatch) return;
    const res = await approveSafeQuestions(selectedBatch, 0.85);
    message.success(`已批量通过 ${res.data.approved_count} 题`);
    loadQuestions(selectedBatch);
  };

  return (
    <div className="review-workspace">
      <aside className="review-left">
        <Card title="导入批次" size="small">
          <List
            dataSource={batches}
            renderItem={b => (
              <List.Item className={selectedBatch === b.id ? 'selected-batch' : ''} onClick={() => loadQuestions(b.id)}>
                <List.Item.Meta title={b.source_file} description={`${b.subject || '-'} · ${b.parsed_questions || 0}题`} />
                <Tag>{b.status}</Tag>
              </List.Item>
            )}
          />
        </Card>

        {selectedBatch && <Card title={`题目列表 (${questions.length})`} size="small" className="question-list-card" extra={<Button size="small" onClick={approveSafe}>高置信批量通过</Button>}>
          <List
            dataSource={questions}
            renderItem={(q, i) => (
              <List.Item className={current?.id === q.id ? 'selected-question' : ''} onClick={() => selectQuestion(q)}>
                <div className="q-list-row">
                  <span>#{i + 1}</span>
                  <Tag color={(q.confidence || 0) >= 0.85 ? 'green' : 'orange'}>{Math.round((q.confidence || 0) * 100)}%</Tag>
                  <span className="q-list-content">{q.content}</span>
                </div>
              </List.Item>
            )}
          />
        </Card>}
      </aside>

      <main className="review-middle">
        <Card title="原文 / 原图预览">
          {!current && <div className="empty-preview">请选择一道题</div>}
          {current && <>
            <div className="preview-meta">来源页：{current.source_page || '-'}　题型：{current.type}</div>
            <div className="preview-ocr"><pre>{current.raw_ocr_text || current.content}</pre></div>
            <div className="preview-images">
              {(current.images || []).map((img, i) => <img key={i} alt="关联图" src={img.url || img} />)}
              {(current.formula_images || []).map((url, i) => <img key={`f-${i}`} alt="公式截图" src={url} />)}
            </div>
          </>}
        </Card>
      </main>

      <aside className="review-right">
        <Card title="结构化编辑器">
          {!current && <div className="empty-preview">等待选择题目</div>}
          {current && <Form form={form} layout="vertical">
            <Form.Item label="题干" name="content" rules={[{ required: true }]}><TextArea rows={5} /></Form.Item>
            <Form.Item label="选项（每行一个）" name="options"><TextArea rows={4} /></Form.Item>
            <Form.Item label="答案" name="answer"><Input /></Form.Item>
            <Form.Item label="解析" name="explanation"><TextArea rows={3} /></Form.Item>
            <Form.Item label="LaTeX 公式（每行一个）" name="formula_latex"><TextArea rows={2} /></Form.Item>
            <Space wrap>
              <Form.Item label="题型" name="type" rules={[{ required: true }]}><Select style={{ width: 120 }}><Option value="choice">选择题</Option><Option value="blank">填空题</Option><Option value="comprehensive">解答题</Option><Option value="unknown">未知</Option></Select></Form.Item>
              <Form.Item label="难度" name="difficulty"><Select style={{ width: 100 }}>{[1,2,3,4,5].map(d => <Option key={d} value={d}>{d}星</Option>)}</Select></Form.Item>
              <Form.Item label="科目" name="subject"><Input style={{ width: 120 }} /></Form.Item>
              <Form.Item label="年级" name="grade"><Input style={{ width: 120 }} /></Form.Item>
              <Form.Item label="知识点" name="knowledge_point"><Input style={{ width: 160 }} /></Form.Item>
            </Space>
            <Space wrap className="editor-actions">
              <Button icon={<SaveOutlined />} onClick={saveDraft}>保存草稿</Button>
              <Button type="primary" icon={<CheckOutlined />} onClick={approve}>通过入库</Button>
              <Button danger icon={<CloseOutlined />} onClick={reject}>驳回</Button>
              <Button icon={<SplitCellsOutlined />} onClick={splitQuestion}>拆分</Button>
              <Button icon={<MergeCellsOutlined />} onClick={mergeToPrevious}>合并上一题</Button>
            </Space>
          </Form>}
        </Card>
      </aside>
    </div>
  );
};

export default ReviewPage;
