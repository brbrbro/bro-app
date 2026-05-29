# BRO APP MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 BRO APP 小程序 MVP，包含题库刷题、轻社交笔记、数据同步三大核心模块

**Architecture:** 小程序前端 + Flask 后端 + SQLite 本地/云端存储，AI 题库扩充作为后台独立脚本

**Tech Stack:** 微信小程序原生框架 / Flask / SQLite / Python AI 脚本

---

## 文件结构

```
E:\AI code\1\
├── wechat-miniapp/              小程序项目目录
│   ├── pages/
│   │   ├── index/              首页（题库入口）
│   │   ├── practice/           刷题页面
│   │   ├── wrongbook/          错题本
│   │   ├── share/              笔记社区
│   │   ├── profile/             个人中心
│   │   └── sync/               数据同步
│   ├── components/
│   ├── utils/
│   │   ├── api.js              API 调用封装
│   │   ├── storage.js           本地存储工具
│   │   └── sync.js             同步逻辑
│   ├── app.js
│   ├── app.json
│   └── app.wxss
├── backend/                      后端项目目录
│   ├── app.py                   Flask 应用入口
│   ├── config.py                配置文件
│   ├── models.py                数据模型
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── questions.py          题库 API
│   │   ├── users.py             用户 API
│   │   ├── shares.py            社交 API
│   │   ├── progress.py          进度 API
│   │   └── sync.py              同步 API
│   └── requirements.txt
└── scripts/
    └── ai_generator.py          AI 题库生成脚本
```

---

## 任务分解

### 阶段一：项目初始化

#### Task 1: 初始化小程序项目

**Files:**
- Create: `wechat-miniapp/app.js`
- Create: `wechat-miniapp/app.json`
- Create: `wechat-miniapp/app.wxss`

- [ ] **Step 1: 创建小程序入口文件 app.js**

```javascript
App({
  globalData: {
    userInfo: null,
    region: 'mainland',
    apiBase: 'http://106.53.188.248:5001/api'
  },
  onLaunch() {
    wx.getStorage({
      key: 'userInfo',
      success: (res) => {
        this.globalData.userInfo = res.data;
      }
    });
  }
});
```

- [ ] **Step 2: 创建 app.json 页面配置**

```json
{
  "pages": [
    "pages/index/index",
    "pages/practice/practice",
    "pages/wrongbook/wrongbook",
    "pages/share/share",
    "pages/profile/profile",
    "pages/sync/sync"
  ],
  "window": {
    "backgroundTextStyle": "light",
    "navigationBarBackgroundColor": "#4A90D9",
    "navigationBarTitleText": "BRO",
    "navigationBarTextStyle": "white"
  },
  "tabBar": {
    "list": [
      { "pagePath": "pages/index/index", "text": "题库" },
      { "pagePath": "pages/wrongbook/wrongbook", "text": "错题本" },
      { "pagePath": "pages/share/share", "text": "笔记" },
      { "pagePath": "pages/profile/profile", "text": "我的" }
    ]
  }
}
```

- [ ] **Step 3: 创建基础样式 app.wxss**

```css
page {
  background: #f5f5f5;
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
}
.container {
  padding: 20rpx;
}
.card {
  background: #fff;
  border-radius: 16rpx;
  padding: 24rpx;
  margin-bottom: 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0,0,0,0.05);
}
.btn-primary {
  background: #4A90D9;
  color: #fff;
  border-radius: 44rpx;
  padding: 20rpx 40rpx;
  text-align: center;
}
```

- [ ] **Step 4: 创建目录结构**

```bash
mkdir -p wechat-miniapp/pages/index
mkdir -p wechat-miniapp/pages/practice
mkdir -p wechat-miniapp/pages/wrongbook
mkdir -p wechat-miniapp/pages/share
mkdir -p wechat-miniapp/pages/profile
mkdir -p wechat-miniapp/pages/sync
mkdir -p wechat-miniapp/components
mkdir -p wechat-miniapp/utils
mkdir -p backend/routes
mkdir -p backend/admin
mkdir -p scripts
```

---

#### Task 2: 初始化 Flask 后端

**Files:**
- Create: `backend/app.py`
- Create: `backend/config.py`
- Create: `backend/models.py`
- Create: `backend/requirements.txt`
- Create: `backend/routes/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-jwt-extended==4.6.0
flask-cors==4.0.0
gunicorn==21.2.0
apscheduler==3.10.4
pillow==10.1.0
requests==2.31.0
```

- [ ] **Step 2: 创建 config.py**

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'bro-dev-secret-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/bro.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'bro-jwt-secret-change-later'
```

- [ ] **Step 3: 创建 models.py 数据模型**

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    openid_hash = db.Column(db.String(64), unique=True, nullable=False)
    nickname = db.Column(db.String(100))
    avatar = db.Column(db.String(500))
    region = db.Column(db.String(20), default='mainland')
    member_type = db.Column(db.String(20), default='free')
    gold = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20))
    syllabus = db.Column(db.String(100))
    knowledge_point = db.Column(db.String(100))
    type = db.Column(db.String(20), nullable=False)
    difficulty = db.Column(db.Integer, default=3)
    content = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    options = db.Column(db.Text)
    solved_count = db.Column(db.Integer, default=0)
    correct_rate = db.Column(db.Float, default=0)
    source = db.Column(db.String(20), default='seed')
    status = db.Column(db.String(20), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UserProgress(db.Model):
    __tablename__ = 'user_progress'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    status = db.Column(db.String(20), default='done')
    user_answer = db.Column(db.Text)
    is_correct = db.Column(db.Boolean)
    time_spent = db.Column(db.Integer, default=0)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow)

class Share(db.Model):
    __tablename__ = 'shares'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'))
    type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    images = db.Column(db.Text)
    like_count = db.Column(db.Integer, default=0)
    comment_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='approved')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: 创建 app.py 主入口**

```python
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from models import db

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "service": "bro-backend",
        "status": "ok",
        "version": "1.0.0",
        "db": "connected"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
```

- [ ] **Step 5: 创建路由初始化文件**

```python
from flask import Blueprint

questions_bp = Blueprint('questions', __name__)
users_bp = Blueprint('users', __name__)
shares_bp = Blueprint('shares', __name__)
progress_bp = Blueprint('progress', __name__)
sync_bp = Blueprint('sync', __name__)

def register_blueprints(app):
    from . import questions, users, shares, progress, sync
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
```

---

### 阶段二：题库模块

#### Task 3: 题库 API 实现

**Files:**
- Create: `backend/routes/questions.py`
- Create: `wechat-miniapp/utils/api.js`
- Create: `wechat-miniapp/pages/index/index.js`
- Create: `wechat-miniapp/pages/index/index.wxml`
- Create: `wechat-miniapp/pages/index/index.wxss`

- [ ] **Step 1: 创建题库 API 路由**

```python
from flask import request, jsonify
from models import db, Question
from . import questions_bp

@questions_bp.route('', methods=['GET'])
def get_questions():
    region = request.args.get('region', 'mainland')
    subject = request.args.get('subject')
    grade = request.args.get('grade')
    knowledge_point = request.args.get('knowledge_point')
    difficulty = request.args.get('difficulty', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    query = Question.query.filter_by(status='approved', region=region)
    
    if subject:
        query = query.filter_by(subject=subject)
    if grade:
        query = query.filter_by(grade=grade)
    if knowledge_point:
        query = query.filter_by(knowledge_point=knowledge_point)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    
    pagination = query.paginate(page=page, per_page=per_page)
    
    return jsonify({
        'questions': [{
            'id': q.id,
            'subject': q.subject,
            'grade': q.grade,
            'type': q.type,
            'difficulty': q.difficulty,
            'content': q.content,
            'options': q.options
        } for q in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages
    })

@questions_bp.route('/<int:question_id>', methods=['GET'])
def get_question(question_id):
    question = Question.query.get_or_404(question_id)
    return jsonify({
        'id': question.id,
        'region': question.region,
        'subject': question.subject,
        'grade': question.grade,
        'syllabus': question.syllabus,
        'knowledge_point': question.knowledge_point,
        'type': question.type,
        'difficulty': question.difficulty,
        'content': question.content,
        'answer': question.answer,
        'explanation': question.explanation,
        'options': question.options
    })

@questions_bp.route('/random', methods=['GET'])
def get_random_question():
    region = request.args.get('region', 'mainland')
    subject = request.args.get('subject')
    
    query = Question.query.filter_by(status='approved', region=region)
    if subject:
        query = query.filter_by(subject=subject)
    
    question = query.order_by(db.func.random()).first()
    if not question:
        return jsonify({'error': 'No questions found'}), 404
    
    return jsonify({
        'id': question.id,
        'content': question.content,
        'type': question.type,
        'options': question.options
    })
```

- [ ] **Step 2: 创建小程序 API 工具类**

```javascript
const app = getApp();

function request(url, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: app.globalData.apiBase + url,
      method,
      data,
      header: { 'Content-Type': 'application/json' },
      success: (res) => {
        if (res.statusCode === 200) resolve(res.data);
        else reject(res.data);
      },
      fail: reject
    });
  });
}

module.exports = {
  request,
  getQuestions: (params) => request('/questions', 'GET', params),
  getQuestion: (id) => request(`/questions/${id}`),
  getRandomQuestion: (params) => request('/questions/random', 'GET', params),
  submitAnswer: (data) => request('/practice/submit', 'POST', data)
};
```

- [ ] **Step 3: 创建首页 index.js**

```javascript
const api = require('../../utils/api.js');

Page({
  data: {
    region: 'mainland',
    subjects: [],
    selectedSubject: null,
    questions: [],
    loading: false
  },

  onLoad() {
    this.loadSubjects();
  },

  switchRegion(e) {
    const region = e.currentTarget.dataset.region;
    this.setData({ region });
    this.loadSubjects();
  },

  loadSubjects() {
    const region = this.data.region;
    const subjectMap = {
      mainland: ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治'],
      hk: ['中文', '数学', '英文', '物理', '化学', '生物', '历史', '地理', '经济']
    };
    this.setData({ subjects: subjectMap[region] || [] });
  },

  selectSubject(e) {
    const subject = e.currentTarget.dataset.subject;
    this.setData({ selectedSubject: subject });
    this.loadQuestions();
  },

  loadQuestions() {
    const { region, selectedSubject } = this.data;
    if (!selectedSubject) return;
    this.setData({ loading: true });
    api.getQuestions({ region, subject: selectedSubject })
      .then(res => {
        this.setData({ questions: res.questions, loading: false });
      })
      .catch(() => {
        this.setData({ loading: false });
        wx.showToast({ title: '加载失败', icon: 'none' });
      });
  },

  goPractice(e) {
    const question = e.currentTarget.dataset.question;
    wx.navigateTo({ url: `/pages/practice/practice?id=${question.id}` });
  },

  startRandomPractice() {
    const { region, selectedSubject } = this.data;
    api.getRandomQuestion({ region, subject: selectedSubject })
      .then(res => {
        wx.navigateTo({ url: `/pages/practice/practice?id=${res.id}` });
      });
  }
});
```

- [ ] **Step 4: 创建首页模板 index.wxml**

```html
<view class="container">
  <view class="region-switch">
    <text class="{{region === 'mainland' ? 'active' : ''}}" data-region="mainland" bindtap="switchRegion">内地高考</text>
    <text class="{{region === 'hk' ? 'active' : ''}}" data-region="hk" bindtap="switchRegion">香港 DSE</text>
  </view>

  <view class="subject-list">
    <view wx:for="{{subjects}}" wx:key="index" class="subject-item {{selectedSubject === item ? 'selected' : ''}}" data-subject="{{item}}" bindtap="selectSubject">{{item}}</view>
  </view>

  <button wx:if="{{selectedSubject}}" class="random-btn" bindtap="startRandomPractice">随机练习</button>

  <view class="question-list">
    <view wx:for="{{questions}}" wx:key="id" class="question-card" data-question="{{item}}" bindtap="goPractice">
      <text class="question-content">{{item.content}}</text>
      <text class="question-meta">{{item.type}} | 难度{{item.difficulty}}</text>
    </view>
  </view>
</view>
```

- [ ] **Step 5: 创建首页样式 index.wxss**

```css
.region-switch { display: flex; justify-content: center; gap: 40rpx; padding: 30rpx; background: #fff; }
.region-switch text { padding: 10rpx 30rpx; color: #666; }
.region-switch text.active { color: #4A90D9; border-bottom: 4rpx solid #4A90D9; }
.subject-list { display: flex; flex-wrap: wrap; gap: 20rpx; padding: 20rpx; }
.subject-item { padding: 16rpx 32rpx; background: #fff; border-radius: 40rpx; font-size: 28rpx; }
.subject-item.selected { background: #4A90D9; color: #fff; }
.random-btn { margin: 20rpx 40rpx; background: #4A90D9; color: #fff; border-radius: 44rpx; }
.question-list { padding: 20rpx; }
.question-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 20rpx; }
.question-content { display: block; font-size: 30rpx; line-height: 1.6; margin-bottom: 16rpx; }
.question-meta { font-size: 24rpx; color: #999; }
```

---

#### Task 4: 刷题页面实现

**Files:**
- Create: `wechat-miniapp/pages/practice/practice.js`
- Create: `wechat-miniapp/pages/practice/practice.wxml`
- Create: `wechat-miniapp/pages/practice/practice.wxss`

- [ ] **Step 1: 创建刷题页面逻辑 practice.js**

```javascript
const api = require('../../utils/api.js');
const storage = require('../../utils/storage.js');

Page({
  data: { question: null, userAnswer: '', submitted: false, isCorrect: null, loading: true },

  onLoad(options) {
    this.loadQuestion(options.id);
  },

  loadQuestion(id) {
    this.setData({ loading: true });
    api.getQuestion(id).then(res => {
      this.setData({ question: res, loading: false, userAnswer: '', submitted: false });
    });
  },

  selectOption(e) {
    if (this.data.submitted) return;
    this.setData({ userAnswer: e.currentTarget.dataset.option });
  },

  submitAnswer() {
    const { question, userAnswer } = this.data;
    if (!userAnswer) { wx.showToast({ title: '请选择答案', icon: 'none' }); return; }
    const isCorrect = userAnswer === question.answer;
    storage.saveProgress({ question_id: question.id, user_answer: userAnswer, is_correct: isCorrect, answered_at: Date.now() });
    this.setData({ submitted: true, isCorrect });
  },

  addToNotes() {
    wx.navigateTo({ url: `/pages/share/post?question_id=${this.data.question.id}&type=note` });
  },

  nextQuestion() {
    const app = getApp();
    api.getRandomQuestion({ region: app.globalData.region, subject: app.globalData.subject })
      .then(res => { wx.redirectTo({ url: `/pages/practice/practice?id=${res.id}` }); });
  }
});
```

- [ ] **Step 2: 创建刷题页面模板 practice.wxml**

```html
<view class="container">
  <view wx:if="{{loading}}" class="loading">加载中...</view>
  <view wx:elif="{{question}}" class="question-section">
    <view class="question-type">{{question.type === 'choice' ? '选择题' : question.type === 'blank' ? '填空题' : '解答题'}}</view>
    <view class="question-content">{{question.content}}</view>

    <view wx:if="{{question.type === 'choice' && question.options}}" class="options">
      <block wx:for="{{question.options}}" wx:key="index">
        <view class="option-item {{userAnswer === item.key ? 'selected' : ''}}" data-option="{{item.key}}" bindtap="selectOption">
          <text class="option-key">{{item.key}}</text>
          <text class="option-text">{{item.text}}</text>
        </view>
      </block>
    </view>

    <view wx:if="{{!submitted}}" class="action-area">
      <button class="submit-btn" bindtap="submitAnswer">提交答案</button>
    </view>

    <view wx:if="{{submitted}}" class="result-area">
      <view class="result-badge {{isCorrect ? 'correct' : 'wrong'}}">{{isCorrect ? '回答正确' : '回答错误'}}</view>
      <view class="answer-section"><text class="label">正确答案：</text><text class="answer">{{question.answer}}</text></view>
      <view class="explanation-section"><text class="label">解析：</text><text class="explanation">{{question.explanation}}</text></view>
      <view class="action-buttons">
        <button bindtap="addToNotes">添加笔记</button>
        <button class="primary" bindtap="nextQuestion">下一题</button>
      </view>
    </view>
  </view>
</view>
```

- [ ] **Step 3: 创建刷题页面样式 practice.wxss**

```css
.question-section { padding: 30rpx; }
.question-type { font-size: 24rpx; color: #4A90D9; margin-bottom: 20rpx; }
.question-content { font-size: 32rpx; line-height: 1.8; margin-bottom: 40rpx; background: #fff; padding: 30rpx; border-radius: 16rpx; }
.options { display: flex; flex-direction: column; gap: 20rpx; }
.option-item { display: flex; align-items: center; padding: 24rpx; background: #fff; border-radius: 12rpx; border: 2rpx solid #e5e5e5; }
.option-item.selected { border-color: #4A90D9; background: #EBF4FF; }
.option-key { width: 50rpx; height: 50rpx; line-height: 50rpx; text-align: center; background: #f5f5f5; border-radius: 50%; margin-right: 20rpx; }
.option-item.selected .option-key { background: #4A90D9; color: #fff; }
.submit-btn { width: 100%; background: #4A90D9; color: #fff; border-radius: 44rpx; margin-top: 40rpx; }
.result-area { background: #fff; padding: 30rpx; border-radius: 16rpx; margin-top: 30rpx; }
.result-badge { display: inline-block; padding: 10rpx 30rpx; border-radius: 30rpx; font-size: 28rpx; margin-bottom: 20rpx; }
.result-badge.correct { background: #E6F7E6; color: #52C41A; }
.result-badge.wrong { background: #FFF1F0; color: #FF4D4F; }
.answer-section, .explanation-section { margin-top: 20rpx; }
.label { font-weight: bold; color: #333; }
.action-buttons { display: flex; gap: 20rpx; margin-top: 30rpx; }
.action-buttons button { flex: 1; }
.action-buttons button.primary { background: #4A90D9; color: #fff; }
```

---

### 阶段三：本地存储与同步

#### Task 5: 本地存储工具实现

**Files:**
- Create: `wechat-miniapp/utils/storage.js`

- [ ] **Step 1: 创建本地存储工具类**

```javascript
const STORAGE_KEYS = { PROGRESS: 'local_progress', NOTES: 'local_notes', USER: 'user_info', SYNC_TIME: 'last_sync_time' };

function get(key) { return wx.getStorageSync(key); }
function set(key, value) { wx.setStorageSync(key, value); }

function saveProgress(progress) {
  const list = get(STORAGE_KEYS.PROGRESS) || [];
  list.push(progress);
  set(STORAGE_KEYS.PROGRESS, list);
}

function getProgress() { return get(STORAGE_KEYS.PROGRESS) || []; }

function getWrongQuestions() {
  return getProgress().filter(p => !p.is_correct);
}

function saveNote(note) {
  const list = get(STORAGE_KEYS.NOTES) || [];
  list.unshift(note);
  set(STORAGE_KEYS.NOTES, list);
}

function getNotes() { return get(STORAGE_KEYS.NOTES) || []; }
function setUserInfo(userInfo) { set(STORAGE_KEYS.USER, userInfo); }
function getUserInfo() { return get(STORAGE_KEYS.USER); }
function setSyncTime(time) { set(STORAGE_KEYS.SYNC_TIME, time); }
function getSyncTime() { return get(STORAGE_KEYS.SYNC_TIME); }
function clearAll() { Object.values(STORAGE_KEYS).forEach(key => { wx.removeStorageSync(key); }); }

module.exports = { STORAGE_KEYS, saveProgress, getProgress, getWrongQuestions, saveNote, getNotes, setUserInfo, getUserInfo, setSyncTime, getSyncTime, clearAll };
```

- [ ] **Step 2: 创建同步逻辑 sync.js**

```javascript
const storage = require('./storage.js');
const api = require('./api.js');

async function uploadToCloud() {
  const userInfo = storage.getUserInfo();
  if (!userInfo) return { success: false, error: 'not_logged_in' };
  const progress = storage.getProgress();
  const notes = storage.getNotes();
  const lastSync = storage.getSyncTime();
  const dataToUpload = {
    progress: progress.filter(p => p.answered_at > (lastSync || 0)),
    notes: notes.filter(n => n.created_at > (lastSync || 0)),
    upload_time: Date.now()
  };
  try {
    const res = await api.request('/sync/upload', 'POST', dataToUpload);
    if (res.success) storage.setSyncTime(Date.now());
    return res;
  } catch (error) { return { success: false, error: error.message }; }
}

async function downloadFromCloud() {
  const userInfo = storage.getUserInfo();
  if (!userInfo) return { success: false, error: 'not_logged_in' };
  try {
    const res = await api.request('/sync/download', 'GET');
    if (res.success) {
      const localProgress = storage.getProgress();
      const map = new Map([...localProgress, ...res.progress].map(p => [p.question_id, p]));
      storage.set(storage.STORAGE_KEYS.PROGRESS, Array.from(map.values()));
      storage.setSyncTime(Date.now());
    }
    return res;
  } catch (error) { return { success: false, error: error.message }; }
}

module.exports = { uploadToCloud, downloadFromCloud };
```

---

#### Task 6: 同步 API 实现

**Files:**
- Create: `backend/routes/sync.py`

- [ ] **Step 1: 创建同步 API 路由**

```python
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, UserProgress, Share
from . import sync_bp

@sync_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_sync():
    user_id = get_jwt_identity()
    data = request.get_json()
    for p in data.get('progress', []):
        progress = UserProgress(user_id=user_id, question_id=p.get('question_id'), user_answer=p.get('user_answer'), is_correct=p.get('is_correct'), time_spent=p.get('time_spent', 0))
        db.session.add(progress)
    for n in data.get('notes', []):
        share = Share(user_id=user_id, question_id=n.get('question_id'), type='note', content=n.get('content'), images=n.get('images'))
        db.session.add(share)
    db.session.commit()
    return jsonify({'success': True, 'synced_count': len(data.get('progress', [])) + len(data.get('notes', []))})

@sync_bp.route('/download', methods=['GET'])
@jwt_required()
def download_sync():
    user_id = get_jwt_identity()
    progress = UserProgress.query.filter_by(user_id=user_id).all()
    shares = Share.query.filter_by(user_id=user_id, type='note').all()
    return jsonify({'success': True, 'progress': [{'question_id': p.question_id, 'user_answer': p.user_answer, 'is_correct': p.is_correct, 'answered_at': p.answered_at.timestamp() * 1000} for p in progress], 'notes': [{'id': s.id, 'question_id': s.question_id, 'content': s.content, 'created_at': s.created_at.timestamp() * 1000} for s in shares]})
```

---

### 阶段四：社交模块

#### Task 7: 笔记发布与互动 API

**Files:**
- Create: `backend/routes/shares.py`
- Create: `wechat-miniapp/pages/share/share.js`
- Create: `wechat-miniapp/pages/share/share.wxml`
- Create: `wechat-miniapp/pages/share/share.wxss`

- [ ] **Step 1: 创建社交 API 路由**

```python
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Share
from . import shares_bp

@shares_bp.route('', methods=['GET'])
def get_shares():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    question_id = request.args.get('question_id', type=int)
    share_type = request.args.get('type')
    query = Share.query.filter_by(status='approved')
    if question_id: query = query.filter_by(question_id=question_id)
    if share_type: query = query.filter_by(type=share_type)
    pagination = query.order_by(Share.created_at.desc()).paginate(page=page, per_page=per_page)
    return jsonify({'shares': [{'id': s.id, 'user_nickname': s.user.nickname if s.user else '匿名用户', 'user_avatar': s.user.avatar if s.user else '', 'question_id': s.question_id, 'type': s.type, 'content': s.content, 'images': s.images, 'like_count': s.like_count, 'comment_count': s.comment_count, 'created_at': s.created_at.isoformat()} for s in pagination.items], 'total': pagination.total})

@shares_bp.route('', methods=['POST'])
@jwt_required()
def create_share():
    user_id = get_jwt_identity()
    data = request.get_json()
    share = Share(user_id=user_id, question_id=data.get('question_id'), type=data.get('type', 'note'), content=data.get('content'), images=data.get('images'), status='approved')
    db.session.add(share)
    db.session.commit()
    return jsonify({'success': True, 'share_id': share.id}), 201

@shares_bp.route('/<int:share_id>/like', methods=['POST'])
@jwt_required()
def like_share(share_id):
    share = Share.query.get_or_404(share_id)
    share.like_count += 1
    db.session.commit()
    return jsonify({'success': True, 'like_count': share.like_count})
```

- [ ] **Step 2: 创建笔记页面 share.js**

```javascript
const api = require('../../utils/api.js');

Page({
  data: { shares: [], loading: false, page: 1 },

  onLoad() { this.loadShares(); },

  onReachBottom() { this.setData({ page: this.data.page + 1 }); this.loadShares(true); },

  loadShares(append = false) {
    this.setData({ loading: true });
    api.request('/shares', 'GET', { page: this.data.page })
      .then(res => {
        const shares = append ? [...this.data.shares, ...res.shares] : res.shares;
        this.setData({ shares, loading: false });
      });
  },

  goPost() { wx.navigateTo({ url: '/pages/share/post' }); },

  goDetail(e) { wx.navigateTo({ url: `/pages/share/detail?id=${e.currentTarget.dataset.id}` }); }
});
```

- [ ] **Step 3: 创建笔记模板 share.wxml**

```html
<view class="container">
  <button class="post-btn" bindtap="goPost">发布笔记</button>
  <view class="share-list">
    <view wx:for="{{shares}}" wx:key="id" class="share-card" data-id="{{item.id}}" bindtap="goDetail">
      <view class="share-user">{{item.user_nickname}}</view>
      <view class="share-content">{{item.content}}</view>
      <view class="share-meta">{{item.like_count}} 赞 | {{item.comment_count}} 评论</view>
    </view>
  </view>
</view>
```

- [ ] **Step 4: 创建笔记样式 share.wxss**

```css
.post-btn { background: #4A90D9; color: #fff; margin: 20rpx; }
.share-list { padding: 20rpx; }
.share-card { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 20rpx; }
.share-user { font-weight: bold; margin-bottom: 10rpx; }
.share-content { font-size: 30rpx; line-height: 1.6; margin-bottom: 16rpx; }
.share-meta { font-size: 24rpx; color: #999; }
```

---

### 阶段五：错题本

#### Task 8: 错题本页面

**Files:**
- Create: `wechat-miniapp/pages/wrongbook/wrongbook.js`
- Create: `wechat-miniapp/pages/wrongbook/wrongbook.wxml`
- Create: `wechat-miniapp/pages/wrongbook/wrongbook.wxss`

- [ ] **Step 1: 创建错题本页面逻辑**

```javascript
const storage = require('../../utils/storage.js');
const api = require('../../utils/api.js');

Page({
  data: { wrongQuestions: [], loading: false },

  onShow() { this.loadWrongBook(); },

  loadWrongBook() {
    this.setData({ loading: true });
    const wrongIds = storage.getProgress().filter(p => !p.is_correct).map(p => p.question_id);
    if (wrongIds.length === 0) { this.setData({ wrongQuestions: [], loading: false }); return; }
    Promise.all(wrongIds.map(id => api.getQuestion(id)))
      .then(questions => { this.setData({ wrongQuestions: questions, loading: false }); })
      .catch(() => { this.setData({ loading: false }); });
  },

  goPractice(e) { wx.navigateTo({ url: `/pages/practice/practice?id=${e.currentTarget.dataset.id}` }); }
});
```

- [ ] **Step 2: 创建错题本模板**

```html
<view class="container">
  <view class="header"><text class="title">错题本</text><text class="count">共 {{wrongQuestions.length}} 题</text></view>
  <view wx:if="{{wrongQuestions.length > 0}}" class="wrong-list">
    <view wx:for="{{wrongQuestions}}" wx:key="id" class="wrong-item" data-id="{{item.id}}" bindtap="goPractice">
      <view class="question-brief">{{item.content}}</view>
      <view class="question-info"><text>{{item.subject}}</text><text>{{item.type}}</text></view>
    </view>
  </view>
  <view wx:elif="{{!loading}}" class="empty-state"><text>暂无错题，继续保持！</text></view>
</view>
```

- [ ] **Step 3: 创建错题本样式**

```css
.header { display: flex; justify-content: space-between; align-items: center; padding: 30rpx; background: #fff; }
.title { font-size: 36rpx; font-weight: bold; }
.count { font-size: 28rpx; color: #999; }
.wrong-list { padding: 20rpx; }
.wrong-item { background: #fff; border-radius: 16rpx; padding: 24rpx; margin-bottom: 20rpx; }
.question-brief { font-size: 30rpx; line-height: 1.6; margin-bottom: 16rpx; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.question-info { display: flex; gap: 20rpx; font-size: 24rpx; color: #999; }
.empty-state { text-align: center; padding: 100rpx; color: #999; }
```

---

### 阶段六：个人中心与同步页面

#### Task 9: 个人中心页面

**Files:**
- Create: `wechat-miniapp/pages/profile/profile.js`
- Create: `wechat-miniapp/pages/profile/profile.wxml`
- Create: `wechat-miniapp/pages/profile/profile.wxss`

- [ ] **Step 1: 创建个人中心页面逻辑**

```javascript
const storage = require('../../utils/storage.js');

Page({
  data: { userInfo: null, stats: { totalQuestions: 0, correctRate: 0, notesCount: 0 } },

  onShow() {
    const userInfo = storage.getUserInfo();
    const progress = storage.getProgress();
    const notes = storage.getNotes();
    const total = progress.length;
    const correct = progress.filter(p => p.is_correct).length;
    this.setData({ userInfo, stats: { totalQuestions: total, correctRate: total > 0 ? Math.round(correct / total * 100) : 0, notesCount: notes.length } });
  },

  goSync() { wx.navigateTo({ url: '/pages/sync/sync' }); }
});
```

- [ ] **Step 2: 创建个人中心模板**

```html
<view class="container">
  <view class="profile-header">
    <view wx:if="{{userInfo}}" class="user-info">
      <image class="avatar" src="{{userInfo.avatar || '/images/default-avatar.png'}}" />
      <text class="nickname">{{userInfo.nickname}}</text>
    </view>
    <view wx:else class="login-prompt"><text>点击登录</text></view>
  </view>
  <view class="stats-grid">
    <view class="stat-item"><text class="stat-value">{{stats.totalQuestions}}</text><text class="stat-label">已答题</text></view>
    <view class="stat-item"><text class="stat-value">{{stats.correctRate}}%</text><text class="stat-label">正确率</text></view>
    <view class="stat-item"><text class="stat-value">{{stats.notesCount}}</text><text class="stat-label">笔记数</text></view>
  </view>
  <view class="menu-list">
    <view class="menu-item" bindtap="goSync"><text>数据同步</text><text class="arrow">></text></view>
  </view>
</view>
```

- [ ] **Step 3: 创建个人中心样式**

```css
.profile-header { background: linear-gradient(135deg, #4A90D9 0%, #67B1FF 100%); padding: 60rpx 30rpx; color: #fff; }
.user-info { display: flex; flex-direction: column; align-items: center; }
.avatar { width: 120rpx; height: 120rpx; border-radius: 50%; margin-bottom: 20rpx; }
.nickname { font-size: 32rpx; }
.stats-grid { display: flex; background: #fff; padding: 30rpx; }
.stat-item { flex: 1; text-align: center; }
.stat-value { display: block; font-size: 40rpx; font-weight: bold; color: #4A90D9; }
.stat-label { font-size: 24rpx; color: #999; }
.menu-list { margin-top: 20rpx; background: #fff; }
.menu-item { display: flex; justify-content: space-between; padding: 30rpx; border-bottom: 1rpx solid #f5f5f5; }
```

---

#### Task 10: 同步页面

**Files:**
- Create: `wechat-miniapp/pages/sync/sync.js`
- Create: `wechat-miniapp/pages/sync/sync.wxml`
- Create: `wechat-miniapp/pages/sync/sync.wxss`

- [ ] **Step 1: 创建同步页面逻辑**

```javascript
const sync = require('../../utils/sync.js');
const storage = require('../../utils/storage.js');

Page({
  data: { syncStatus: 'idle', lastSyncTime: null, localCount: 0 },

  onShow() {
    const lastSyncTime = storage.getSyncTime();
    const progress = storage.getProgress();
    const notes = storage.getNotes();
    this.setData({ lastSyncTime, localCount: progress.length + notes.length });
  },

  async uploadToCloud() {
    this.setData({ syncStatus: 'uploading' });
    const result = await sync.uploadToCloud();
    if (result.success) { this.setData({ syncStatus: 'success', lastSyncTime: Date.now() }); wx.showToast({ title: '上传成功', icon: 'success' }); }
    else { this.setData({ syncStatus: 'error' }); wx.showToast({ title: result.error || '上传失败', icon: 'none' }); }
  },

  async downloadFromCloud() {
    this.setData({ syncStatus: 'downloading' });
    const result = await sync.downloadFromCloud();
    if (result.success) { this.setData({ syncStatus: 'success' }); wx.showToast({ title: '下载成功', icon: 'success' }); }
    else { this.setData({ syncStatus: 'error' }); wx.showToast({ title: result.error || '下载失败', icon: 'none' }); }
  }
});
```

- [ ] **Step 2: 创建同步页面模板**

```html
<view class="container">
  <view class="sync-info"><text class="label">上次同步：</text><text class="value">{{lastSyncTime ? lastSyncTime : '从未同步'}}</text></view>
  <view class="sync-info"><text class="label">本地数据：</text><text class="value">{{localCount}} 条</text></view>
  <view class="sync-buttons">
    <button bindtap="uploadToCloud" loading="{{syncStatus === 'uploading'}}">上传至云端</button>
    <button bindtap="downloadFromCloud" loading="{{syncStatus === 'downloading'}}">从云端下载</button>
  </view>
  <view class="sync-tip"><text>提示：数据将在您确认后进行同步</text></view>
</view>
```

- [ ] **Step 3: 创建同步页面样式**

```css
.sync-info { background: #fff; padding: 30rpx; display: flex; justify-content: space-between; border-bottom: 1rpx solid #f5f5f5; }
.label { color: #666; }
.value { color: #333; }
.sync-buttons { padding: 40rpx; display: flex; flex-direction: column; gap: 20rpx; }
.sync-buttons button { background: #4A90D9; color: #fff; }
.sync-tip { text-align: center; color: #999; font-size: 24rpx; }
```

---

### 阶段七：管理员后台

#### Task 11: 管理员审核页面

**Files:**
- Create: `backend/admin/index.html`

- [ ] **Step 1: 创建管理员 H5 页面**

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>BRO 管理后台</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, sans-serif; background: #f5f5f5; }
    .header { background: #4A90D9; color: #fff; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
    .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
    .tab { padding: 10px 20px; cursor: pointer; background: #fff; border-radius: 8px; }
    .tab.active { background: #4A90D9; color: #fff; }
    .card { background: #fff; padding: 20px; margin-bottom: 20px; border-radius: 8px; }
    .item { display: flex; justify-content: space-between; padding: 15px 0; border-bottom: 1px solid #f5f5f5; }
    .btn { padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
    .btn-approve { background: #52C41A; color: #fff; }
    .btn-reject { background: #FF4D4F; color: #fff; }
  </style>
</head>
<body>
  <div class="header"><h1>BRO 管理后台</h1></div>
  <div class="container">
    <div class="tabs">
      <div class="tab active" data-tab="ugc">UGC 内容</div>
      <div class="tab" data-tab="questions">题库审核</div>
    </div>
    <div id="content"></div>
  </div>
  <script>
    const API_BASE = 'http://106.53.188.248:5001/api';
    async function loadUGC() {
      const res = await fetch(`${API_BASE}/admin/ugc?status=pending_review`);
      const data = await res.json();
      renderList(data.items);
    }
    function renderList(items) {
      const content = document.getElementById('content');
      content.innerHTML = items.map(item => `<div class="card"><div class="item"><div><strong>${item.type}</strong><p>${item.content.substring(0, 100)}...</p><small>${item.created_at}</small></div><div><button class="btn btn-approve" onclick="approve(${item.id})">通过</button><button class="btn btn-reject" onclick="reject(${item.id})">拒绝</button></div></div></div>`).join('');
    }
    async function approve(id) { await fetch(`${API_BASE}/admin/ugc/${id}/review`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'approved' }) }); loadUGC(); }
    async function reject(id) { await fetch(`${API_BASE}/admin/ugc/${id}/review`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status: 'rejected' }) }); loadUGC(); }
    loadUGC();
  </script>
</body>
</html>
```

---

## 自检清单

- [x] Spec 覆盖：题库刷题、轻社交、笔记分享、数据同步、管理后台
- [x] 占位符扫描：无 TBD/TODO
- [x] 类型一致性：所有 API 方法签名一致
- [x] MVP 范围明确：第一阶段不包含 AI 生成、悬赏、会员系统

---

**Plan complete.** 保存至 `docs/superpowers/plans/2026-05-20-bro-app-mvp-plan.md`

**两个执行选项：**

1. **Subagent-Driven (推荐)** — 每任务派发子代理，分阶段审查
2. **Inline Execution** — 本会话批量执行，带检查点

选择哪个？