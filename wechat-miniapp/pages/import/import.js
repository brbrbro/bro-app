const api = require('../../utils/api.js');

const knowledgePoints = {
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

Page({
  data: {
    examTypes: [
      { key: 'dse', label: 'DSE' },
      { key: 'gaokao', label: '高考' }
    ],
    selectedExamType: '',
    subjects: ['数学', '物理', '化学', '生物'],
    selectedSubject: '',
    grades: [],
    selectedGrade: '',
    knowledgePoints: ['不详'],
    selectedKnowledgePoint: '不详',
    uploading: false,
    tempImagePath: ''
  },

  selectExamType(e) {
    const examType = e.currentTarget.dataset.type;
    this.setData({
      selectedExamType: examType,
      grades: gradeMap[examType] || [],
      selectedGrade: '',
      knowledgePoints: ['不详'],
      selectedKnowledgePoint: '不详',
      selectedSubject: ''
    });
  },

  selectSubject(e) {
    this.setData({ selectedSubject: e.currentTarget.dataset.subject });
    this.updateKnowledgePoints();
  },

  onGradeChange(e) {
    const gradeIndex = e.detail.value;
    const grade = this.data.grades[gradeIndex];
    this.setData({ selectedGrade: grade });
    this.updateKnowledgePoints();
  },

  onKnowledgePointChange(e) {
    const kpIndex = e.detail.value;
    const kp = this.data.knowledgePoints[kpIndex];
    this.setData({ selectedKnowledgePoint: kp });
  },

  updateKnowledgePoints() {
    const { selectedExamType, selectedSubject, selectedGrade } = this.data;
    if (selectedExamType && selectedSubject && selectedGrade) {
      const points = knowledgePoints[selectedExamType]?.[selectedSubject]?.[selectedGrade] || [];
      this.setData({
        knowledgePoints: ['不详', ...points],
        selectedKnowledgePoint: '不详'
      });
    } else {
      this.setData({
        knowledgePoints: ['不详'],
        selectedKnowledgePoint: '不详'
      });
    }
  },

  chooseImage() {
    if (!this.data.selectedExamType) {
      wx.showToast({ title: '请选择考试体系', icon: 'none' });
      return;
    }
    if (!this.data.selectedSubject) {
      wx.showToast({ title: '请选择科目', icon: 'none' });
      return;
    }

    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: ['album', 'camera'],
      success: (res) => {
        this.setData({ tempImagePath: res.tempFiles[0].tempFilePath });
        this.uploadImage(res.tempFiles[0].tempFilePath);
      }
    });
  },

  uploadImage(filePath) {
    this.setData({ uploading: true });
    
    wx.uploadFile({
      url: `${getApp().globalData.apiBase}/import/upload`,
      filePath: filePath,
      name: 'file',
      formData: {
        exam_type: this.data.selectedExamType,
        subject: this.data.selectedSubject,
        grade: this.data.selectedGrade,
        knowledge_point: this.data.selectedKnowledgePoint,
        created_by: 'user'
      },
      success: (res) => {
        const data = JSON.parse(res.data);
        if (data.success) {
          wx.showModal({
            title: '上传成功',
            content: `已识别 ${data.total_questions} 道题目，等待管理员审核`,
            showCancel: false
          });
        } else {
          wx.showToast({ title: data.error || '上传失败', icon: 'none' });
        }
      },
      fail: () => {
        wx.showToast({ title: '上传失败', icon: 'none' });
      },
      complete: () => {
        this.setData({ uploading: false, tempImagePath: '' });
      }
    });
  }
});

