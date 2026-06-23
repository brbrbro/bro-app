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

const knowledgePointsData = {
  gaokao: {
    grades: ['高一', '高二', '高三'],
    subjects: {
      数学: {
        高一: ['集合', '常用逻辑用语', '函数概念', '函数性质', '指数函数', '对数函数', '三角函数', '平面向量', '复数', '统计', '概率'],
        高二: ['空间向量', '立体几何', '平面解析几何', '数列', '导数', '导数应用', '计数原理', '随机变量', '统计分析'],
        高三: ['函数综合', '数列综合', '立体几何综合', '解析几何综合', '概率统计综合', '导数综合']
      },
      物理: {
        高一: ['机械运动', '相互作用', '牛顿运动定律', '机械能', '曲线运动', '万有引力'],
        高二: ['动量守恒', '静电场', '恒定电流', '磁场', '电磁感应', '交变电流'],
        高三: ['热学', '机械振动', '机械波', '光学', '近代物理', '实验专题']
      },
      化学: {
        高一: ['物质的量', '离子反应', '氧化还原反应', '元素周期律', '化学键', '金属及其化合物'],
        高二: ['化学反应速率', '化学平衡', '弱电解质电离', '盐类水解', '原电池', '电解池'],
        高三: ['有机化学基础', '物质结构', '化学实验', '工业流程', '反应原理综合', '计算专题']
      },
      生物: {
        高一: ['细胞结构', '细胞代谢', '酶', '光合作用', '呼吸作用', '细胞增殖'],
        高二: ['遗传规律', 'DNA', '基因表达', '变异', '进化', '稳态与调节'],
        高三: ['生态系统', '免疫调节', '植物激素', '实验设计', '生物技术', '综合专题']
      }
    }
  },
  dse: {
    grades: ['中四', '中五', '中六'],
    subjects: {
      数学: {
        中四: ['二次方程', '函数与图像', '直线方程', '多项式', '指数函数', '对数函数', '基础三角学', '概率基础'],
        中五: ['圆的方程', '轨迹', '不等式', '线性规划', '排列组合', '概率进阶', '统计应用'],
        中六: ['等差数列', '等比数列', '数列求和', '立体三角学', '坐标几何', '图像变换', 'M1 微积分', 'M2 代数与微积分']
      },
      物理: {
        中四: ['温度', '热与内能', '力与运动', '牛顿定律', '功', '能量', '功率', '动量'],
        中五: ['圆周运动', '引力', '波的本质', '光的反射', '光的折射', '透镜', '静电学', '电路', '电磁学'],
        中六: ['放射现象', '核能', '原子世界', '天文学', '能源使用', '医学物理']
      },
      化学: {
        中四: ['大气', '海洋', '岩石与矿物', '原子结构', '周期表', '化学键'],
        中五: ['金属', '酸和碱', '化石燃料', '碳化合物', '氧化还原反应', '化学电池', '电解'],
        中六: ['化学反应和能量', '焓变', '反应速率', '化学平衡', '工业化学', '分析化学']
      },
      生物: {
        中四: ['细胞膜运输', '酶', '新陈代谢', '人的营养', '气体交换', '物质转运', '植物营养', '细胞分裂'],
        中五: ['人的生殖', '光合作用', '呼吸作用', '传染病', '免疫', '孟德尔定律', 'DNA', '基因表达'],
        中六: ['生物多样性', '进化', '个人健康', '人体调节', '应用生态学', '微生物与人类', '生物工程']
      }
    }
  }
};

const getGradeOptions = (examType) => knowledgePointsData[examType]?.grades || [];
const getKnowledgeOptions = (examType, subject, grade) => knowledgePointsData[examType]?.subjects?.[subject]?.[grade] || [];

const ImportPage = () => {
  const [batches, setBatches] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [form] = Form.useForm();
  const [singleForm] = Form.useForm();

  const batchExamType = Form.useWatch('examType', form);
  const batchSubject = Form.useWatch('subject', form);
  const batchGrade = Form.useWatch('grade', form);
  const singleExamType = Form.useWatch('examType', singleForm);
  const singleSubject = Form.useWatch('subject', singleForm);
  const singleGrade = Form.useWatch('grade', singleForm);

  useEffect(() => { loadBatches(); }, []);

  useEffect(() => {
    form.setFieldsValue({ grade: undefined, knowledgePoint: undefined });
  }, [batchExamType, form]);

  useEffect(() => {
    form.setFieldsValue({ knowledgePoint: undefined });
  }, [batchSubject, batchGrade, form]);

  useEffect(() => {
    singleForm.setFieldsValue({ grade: undefined, knowledgePoint: undefined });
  }, [singleExamType, singleForm]);

  useEffect(() => {
    singleForm.setFieldsValue({ knowledgePoint: undefined });
  }, [singleSubject, singleGrade, singleForm]);

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

  const renderMetaForm = (targetForm, examType, subject, grade) => {
    const gradeOptions = getGradeOptions(examType);
    const knowledgeOptions = getKnowledgeOptions(examType, subject, grade);

    return (
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
          <Select style={{ width: 120 }} placeholder={examType ? '年级' : '先选体系'} disabled={!examType}>
            {gradeOptions.map(g => <Option key={g} value={g}>{g}</Option>)}
          </Select>
        </Form.Item>
        <Form.Item name="knowledgePoint" label="知识点">
          <Select
            showSearch
            allowClear
            style={{ width: 220 }}
            placeholder={examType && subject && grade ? '知识点' : '先选体系/科目/年级'}
            disabled={!examType || !subject || !grade}
            optionFilterProp="children"
          >
            {knowledgeOptions.map(k => <Option key={k} value={k}>{k}</Option>)}
          </Select>
        </Form.Item>
      </Form>
    );
  };

  return (
    <div className="import-page">
      <Tabs defaultActiveKey="batch" items={[
        {
          key: 'batch',
          label: '试卷批量导入',
          children: (
            <Card title="上传试卷文件" className="upload-card">
              {renderMetaForm(form, batchExamType, batchSubject, batchGrade)}
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
              {renderMetaForm(singleForm, singleExamType, singleSubject, singleGrade)}
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
