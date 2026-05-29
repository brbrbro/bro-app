import React, { useState, useEffect } from 'react';
import { Upload, message, Card, List, Tag, Button, Select } from 'antd';
import { InboxOutlined, FilePdfOutlined, FileWordOutlined, FileImageOutlined } from '@ant-design/icons';
import { uploadFile, getBatches } from '../../services/api';
import './Import.css';

const { Dragger } = Upload;
const { Option } = Select;

const knowledgePointsData = {
  dse: {
    '数学': {
      '中四': [
        '二次方程',
        '函数与图像',
        '直线方程',
        '多项式',
        '指数函数',
        '对数函数',
        '基础三角学',
        '圆的几何-弦与切线',
        '圆心角与圆周角定理',
        '概率的基本定义',
        '概率的运算法则'
      ],
      '中五': [
        '圆与切线进阶',
        '不等式',
        '线性规划',
        '函数图像进阶',
        '排列',
        '组合',
        '概率进阶',
        '圆的方程',
        '轨迹',
        '平面三角学',
        '解三角形',
        '离差的量度',
        '统计的应用'
      ],
      '中六': [
        '等差数列',
        '等比数列',
        '数列求和',
        '立体三角学',
        '三维问题',
        '坐标几何',
        '统计与概率',
        '图像变换',
        '对数函数进阶',
        '微积分与统计-M1',
        '代数与微积分-M2'
      ]
    },
    '物理': {
      '中四': [
        '温度',
        '热与内能',
        '热转移',
        '物态改变',
        '位置与移动',
        '力与运动',
        '牛顿定律',
        '功',
        '能量',
        '功率',
        '动量',
        '抛体运动'
      ],
      '中五': [
        '匀速圆周运动',
        '引力',
        '波的本质',
        '波的特性',
        '光的反射',
        '光的折射',
        '透镜',
        '光的波动性',
        '声音',
        '静电学',
        '电路',
        '家居用电',
        '电磁学'
      ],
      '中六': [
        '放射现象',
        '核能',
        '天文学和航天科学',
        '原子世界',
        '能量和能源的使用',
        '医学物理学'
      ]
    },
    '化学': {
      '中四': [
        '大气',
        '海洋',
        '岩石与矿物',
        '原子结构',
        '周期表',
        '化学键'
      ],
      '中五': [
        '金属',
        '酸和碱',
        '化石燃料',
        '碳化合物',
        '微观世界II',
        '氧化还原反应',
        '化学电池',
        '电解'
      ],
      '中六': [
        '化学反应和能量',
        '焓变',
        '反应速率',
        '化学平衡',
        '工业化学',
        '分析化学'
      ]
    },
    '生物': {
      '中四': [
        '物质穿越细胞膜',
        '酶',
        '新陈代谢',
        '人的营养',
        '人体气体交换',
        '人体内物质转运',
        '植物营养',
        '植物气体交换',
        '植物蒸腾',
        '植物转运',
        '植物支持',
        '细胞周期',
        '细胞分裂',
        '有花植物生殖'
      ],
      '中五': [
        '人的生殖',
        '光合作用',
        '呼吸作用',
        '非传染病',
        '传染病预防',
        '身体防御机制',
        '免疫',
        '孟德尔定律',
        'DNA',
        '基因表达',
        '生物工程入门'
      ],
      '中六': [
        '生物多样性',
        '进化',
        '个人健康',
        '疾病',
        '身体防御机制进阶',
        '人体生理学-调节与控制',
        '应用生态学',
        '微生物与人类',
        '生物工程'
      ]
    }
  },
  gaokao: {
    '数学': {
      '高一': [
        '集合',
        '常用逻辑用语',
        '一元二次函数',
        '一元二次方程',
        '一元二次不等式',
        '函数概念',
        '函数性质',
        '指数函数',
        '对数函数',
        '三角函数',
        '平面向量',
        '复数',
        '立体几何初步',
        '统计',
        '概率'
      ],
      '高二': [
        '空间向量',
        '立体几何',
        '平面解析几何',
        '数列',
        '导数',
        '导数应用',
        '计数原理',
        '随机变量',
        '随机变量分布',
        '成对数据',
        '统计分析'
      ],
      '高三': [
        '函数综合',
        '数列综合',
        '立体几何综合',
        '解析几何综合',
        '概率统计综合',
        '导数综合'
      ]
    },
    '物理': {
      '高一': [
        '机械运动',
        '物理模型',
        '相互作用',
        '牛顿运动定律',
        '机械能',
        '机械能守恒',
        '曲线运动',
        '万有引力',
        '牛顿力学局限性',
        '相对论初步'
      ],
      '高二': [
        '动量守恒',
        '机械振动',
        '机械波',
        '静电场',
        '电路',
        '电磁场',
        '电磁波',
        '固体',
        '液体',
        '气体',
        '热力学定律',
        '原子结构',
        '原子核',
        '波粒二象性'
      ],
      '高三': [
        '力学综合',
        '电磁学综合',
        '热学综合',
        '光学综合',
        '近代物理综合'
      ]
    },
    '化学': {
      '高一': [
        '化学实验',
        '常见无机物',
        '物质结构',
        '化学反应与能量',
        '化学可持续发展'
      ],
      '高二': [
        '化学反应与能量',
        '化学反应速率',
        '化学平衡',
        '水溶液离子反应',
        '离子平衡',
        '有机物组成',
        '有机物结构',
        '烃',
        '衍生物',
        '生物大分子',
        '合成高分子'
      ],
      '高三': [
        '元素化合物综合',
        '反应原理综合',
        '有机化学综合',
        '结构化学综合',
        '实验综合'
      ]
    },
    '生物': {
      '高一': [
        '细胞分子组成',
        '细胞结构',
        '细胞代谢',
        '细胞生命历程'
      ],
      '高二': [
        '遗传细胞基础',
        '遗传分子基础',
        '遗传基本规律',
        '生物变异',
        '现代生物进化理论'
      ],
      '高三': [
        '内环境与稳态',
        '动物生命活动调节',
        '植物激素调节',
        '种群',
        '群落',
        '生态系统',
        '生态环境保护'
      ]
    }
  }
};

const gradeMap = {
  dse: ['中四', '中五', '中六'],
  gaokao: ['高一', '高二', '高三']
};

const subjects = ['数学', '物理', '化学', '生物'];

const ImportPage = () => {
  const [uploading, setUploading] = useState(false);
  const [batches, setBatches] = useState([]);
  const [examType, setExamType] = useState('');
  const [subject, setSubject] = useState('');
  const [grade, setGrade] = useState('');
  const [knowledgePoint, setKnowledgePoint] = useState('不详');
  const [knowledgePoints, setKnowledgePoints] = useState(['不详']);

  useEffect(() => {
    if (examType && subject && grade) {
      const points = knowledgePointsData[examType]?.[subject]?.[grade] || [];
      setKnowledgePoints(['不详', ...points]);
      setKnowledgePoint('不详');
    } else {
      setKnowledgePoints(['不详']);
      setKnowledgePoint('不详');
    }
  }, [examType, subject, grade]);

  const loadBatches = async () => {
    try {
      const res = await getBatches();
      setBatches(res.data.batches);
    } catch (error) {
      message.error('加载批次失败');
    }
  };

  const handleUpload = async (file) => {
    if (!examType) {
      message.warning('请选择考试体系');
      return;
    }
    if (!subject) {
      message.warning('请选择科目');
      return;
    }

    setUploading(true);
    try {
      const res = await uploadFile(file, examType, subject, grade, knowledgePoint);
      message.success(`成功导入 ${res.data.total_questions} 道题目`);
      loadBatches();
    } catch (error) {
      message.error('上传失败: ' + error.message);
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (type) => {
    if (type === 'pdf') return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
    if (type in {doc: 1, docx: 1}) return <FileWordOutlined style={{ color: '#1890ff' }} />;
    return <FileImageOutlined style={{ color: '#52c41a' }} />;
  };

  const getStatusTag = (status) => {
    const colors = {
      pending: 'default',
      processing: 'processing',
      reviewing: 'warning',
      completed: 'success',
      error: 'error'
    };
    const labels = {
      pending: '等待中',
      processing: '处理中',
      reviewing: '审核中',
      completed: '完成',
      error: '错误'
    };
    return <Tag color={colors[status]}>{labels[status]}</Tag>;
  };

  return (
    <div className="import-page">
      <Card title="文件上传" className="upload-card">
        {/* 考试体系选择 */}
        <div className="form-item">
          <label className="form-label">选择考试体系 <span className="required">*</span></label>
          <div className="button-group">
            <button 
              className={`option-btn ${examType === 'dse' ? 'selected' : ''}`}
              onClick={() => { setExamType('dse'); setGrade(''); }}
            >
              DSE
            </button>
            <button 
              className={`option-btn ${examType === 'gaokao' ? 'selected' : ''}`}
              onClick={() => { setExamType('gaokao'); setGrade(''); }}
            >
              高考
            </button>
          </div>
        </div>

        {/* 科目选择 */}
        <div className="form-item">
          <label className="form-label">选择科目 <span className="required">*</span></label>
          <div className="button-group">
            {subjects.map(s => (
              <button 
                key={s}
                className={`option-btn ${subject === s ? 'selected' : ''}`}
                onClick={() => setSubject(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>

        {/* 年级选择 */}
        <div className="form-item">
          <label className="form-label">选择年级 <span className="optional">(可选)</span></label>
          <Select 
            style={{ width: 200 }}
            placeholder={examType ? '请选择年级' : '请先选择考试体系'}
            value={grade || undefined}
            onChange={setGrade}
            disabled={!examType}
          >
            {(gradeMap[examType] || []).map(g => (
              <Option key={g} value={g}>{g}</Option>
            ))}
          </Select>
        </div>

        {/* 知识点选择 */}
        <div className="form-item">
          <label className="form-label">选择知识点 <span className="optional">(可选)</span></label>
          <Select 
            style={{ width: 400 }}
            placeholder="请选择知识点"
            value={knowledgePoint}
            onChange={setKnowledgePoint}
          >
            {knowledgePoints.map(kp => (
              <Option key={kp} value={kp}>{kp}</Option>
            ))}
          </Select>
        </div>

        <Dragger
          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
          beforeUpload={(file) => {
            handleUpload(file);
            return false;
          }}
          showUploadList={false}
          disabled={uploading}
        >
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此处上传</p>
          <p className="ant-upload-hint">
            支持 PDF、Word、图片格式。文件将经过 AI 识别后进入审核流程。
          </p>
        </Dragger>
      </Card>

      <Card title="导入历史" className="history-card">
        <Button onClick={loadBatches} style={{ marginBottom: 16 }}>刷新</Button>
        <List
          dataSource={batches}
          renderItem={item => (
            <List.Item>
              <List.Item.Meta
                avatar={getFileIcon(item.source_type)}
                title={item.source_file}
                description={
                  <span>
                    {getStatusTag(item.status)} | 
                    {item.exam_type && ` ${item.exam_type.toUpperCase()} |`}
                    {item.subject && ` ${item.subject} |`}
                    {item.grade && ` ${item.grade} |`}
                    解析: {item.parsed_questions} 题 | 
                    通过: {item.approved_questions} 题
                  </span>
                }
              />
              <span>{item.created_at}</span>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default ImportPage;
