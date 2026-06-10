# BRO App 功能补齐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按优先级补齐 BRO 小程序剩余功能：(1) 修复后端服务器；(2) 补齐 6 个个人中心子页面；(3) 实现 9 个主页/菜单占位按钮对应的页面；(4) 签到/积分接入后端持久化。

**Architecture:** 后端 Flask + SQLite + JWT 已存在，扩展 User 模型加积分字段、新增 DailyCheckIn 模型与签到 API；小程序端新增 15 个独立页面，每个页面遵循现有 `pages/<name>/<name>.{js,wxml,wxss,json}` 结构；新增 API 方法集中在 `utils/api.js`。

**Tech Stack:** 微信小程序原生框架 / Flask 3.0 / SQLAlchemy / Flask-JWT-Extended / pytest

---

## 阅前必读：项目背景

**项目路径：** `E:\Opencode\越己\Bro app\bro-app`

**关键现有文件：**
- 小程序入口：`wechat-miniapp/app.js`、`wechat-miniapp/app.json`
- 小程序主页：`wechat-miniapp/pages/index/index.{js,wxml,wxss}`
- 工具类：`wechat-miniapp/utils/{api.js,auth.js,storage.js,i18n.js}`
- 后端入口：`backend/app.py`
- 后端模型：`backend/models.py`
- 后端路由：`backend/routes/{users,questions,progress,sync,shares,import,auth}.py`
- 蓝图注册：`backend/routes/__init__.py`

**关键约定：**
- 所有小程序页面尺寸使用 `rpx` 单位
- 所有页面 4 个文件齐备：`.js`、`.wxml`、`.wxss`、`.json`（json 至少含 `{"navigationBarTitleText": "..."}`）
- 已用 JWT 鉴权：受保护接口需 `Authorization: Bearer <token>` 请求头
- `utils/api.js` 已自动注入 token；新增 API 方法只需在 module.exports 内追加
- 后端使用 `jwt_required()` 装饰器；`get_jwt_identity()` 返回字符串 user_id
- 项目 git 仓库：远端 `https://github.com/brbrbro/bro-app.git`（私有）

**配色规范（沿用现有）：**
- 主蓝 `#4A90D9`、辅蓝 `#6BA8E8`
- 红 `#E74C3C`、绿 `#2ECC71`、橙 `#F39C12`
- 紫 `#9B59B6`、青 `#1ABC9C`、金 `#FFD700`
- 灰底 `#f5f5f5`、卡片白 `#fff`、边框 `#e5e5e5`

---

## 文件结构

```
bro-app/
├── backend/
│   ├── models.py                       修改：User 加 points 字段，新增 DailyCheckIn 模型
│   ├── routes/
│   │   ├── __init__.py                 修改：注册 checkin_bp、leaderboard_bp
│   │   ├── checkin.py                  新增：签到 API
│   │   ├── leaderboard.py              新增：排行榜 API
│   │   ├── import.py                   修改：加 /my-questions 端点
│   │   └── users.py                    修改：profile 返回 points
│   └── tests/                          新增目录
│       ├── conftest.py
│       ├── test_health.py
│       ├── test_leaderboard.py
│       └── test_checkin.py
└── wechat-miniapp/
    ├── app.json                        修改：注册 15 个新页面
    ├── app.js                          修改：dev apiBase 切到本地
    ├── utils/
    │   ├── api.js                      修改：加签到 + 新页面所需 API
    │   └── storage.js                  修改：加收藏方法
    ├── pages/
    │   ├── index/index.js              修改：signIn 接入后端、占位按钮跳页
    │   ├── stats/                      新增：我的战绩
    │   ├── myquestions/                新增：我的题目
    │   ├── mybag/                      新增：我的书包（收藏）
    │   ├── classmates/                 新增：我的同学
    │   ├── invite/                     新增：邀请同学
    │   ├── membership/                 新增：我的会员
    │   ├── daily-challenge/            新增：每日挑战
    │   ├── leaderboard/                新增：排行榜
    │   ├── points-shop/                新增：积分商城
    │   ├── licitong/                   新增：理词通
    │   ├── square/                     新增：广场
    │   ├── studyroom/                  新增：自习室
    │   ├── notifications/              新增：通知中心
    │   ├── difficulty/                 新增：难度偏好
    │   └── settings/                   新增：系统设置
```

---

# Phase 1：后端服务器修复与基础设施

## Task 1.1：本地拉起后端 dev server

**目的：** 远端 `106.53.188.248` 无响应，先在 Windows 本地拉起，让后续开发不依赖远端。

**Files:**
- Modify: `wechat-miniapp/app.js`

- [ ] **Step 1：检查 Python 与依赖**

```powershell
python --version
pip show flask flask-sqlalchemy flask-jwt-extended flask-cors
```
Expected: Python 3.8+；任一缺失跳到 Step 2。

- [ ] **Step 2：安装 backend 依赖**

```powershell
pip install -r backend/requirements.txt
```

- [ ] **Step 3：本地启动后端**

工作目录 `backend`，运行：
```powershell
python app.py
```
Expected: 输出 `Running on http://0.0.0.0:5001`。保持窗口运行。

- [ ] **Step 4：另开终端验证 health**

```powershell
curl.exe -s http://127.0.0.1:5001/api/health
```
Expected: `{"db":"connected","service":"bro-backend","status":"ok","version":"1.0.0"}`

- [ ] **Step 5：切换小程序 apiBase 到本地**

修改 `wechat-miniapp/app.js`，把 `apiBase: 'http://106.53.188.248/api'` 改为：
```javascript
apiBase: 'http://127.0.0.1:5001/api'
```

> **说明：** 微信开发者工具勾选"不校验合法域名"即可访问 127.0.0.1。

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/app.js
git commit -m "chore: switch dev apiBase to localhost 127.0.0.1:5001"
```

---

## Task 1.2：建立 pytest 测试骨架

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Modify: `backend/requirements.txt`

- [ ] **Step 1：追加 pytest 到 requirements.txt**

文件末尾追加：
```
pytest==8.3.3
```

- [ ] **Step 2：安装 pytest**

```powershell
pip install pytest==8.3.3
```

- [ ] **Step 3：创建 tests 目录与空 __init__.py**

```powershell
New-Item -ItemType Directory -Path "backend\tests" -Force
New-Item -ItemType File -Path "backend\tests\__init__.py" -Force
```

- [ ] **Step 4：写 conftest.py**

创建 `backend/tests/conftest.py`：
```python
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app as flask_app
from models import db


@pytest.fixture
def app():
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    resp = client.post('/api/users/wx-login', json={'code': 'test_code_1'})
    token = resp.get_json()['token']
    return {'Authorization': f'Bearer {token}'}
```

- [ ] **Step 5：写 test_health.py**

创建 `backend/tests/test_health.py`：
```python
def test_health_returns_ok(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'ok'
    assert data['service'] == 'bro-backend'
```

- [ ] **Step 6：运行测试**

工作目录 `backend`：
```powershell
pytest tests/test_health.py -v
```
Expected: `1 passed`

- [ ] **Step 7：Commit**

```powershell
git add backend/tests backend/requirements.txt
git commit -m "test: add pytest scaffold with health check test"
```

---

# Phase 2：6 个个人中心子页面

## Task 2.1：一次性注册 15 个新页面到 app.json

**Files:**
- Modify: `wechat-miniapp/app.json`

- [ ] **Step 1：覆写 app.json**

```json
{
  "pages": [
    "pages/index/index",
    "pages/practice/practice",
    "pages/wrongbook/wrongbook",
    "pages/share/share",
    "pages/profile/profile",
    "pages/sync/sync",
    "pages/import/import",
    "pages/stats/stats",
    "pages/myquestions/myquestions",
    "pages/mybag/mybag",
    "pages/classmates/classmates",
    "pages/invite/invite",
    "pages/membership/membership",
    "pages/daily-challenge/daily-challenge",
    "pages/leaderboard/leaderboard",
    "pages/points-shop/points-shop",
    "pages/licitong/licitong",
    "pages/square/square",
    "pages/studyroom/studyroom",
    "pages/notifications/notifications",
    "pages/difficulty/difficulty",
    "pages/settings/settings"
  ],
  "window": {
    "backgroundTextStyle": "light",
    "navigationBarBackgroundColor": "#4A90D9",
    "navigationBarTitleText": "BRO",
    "navigationBarTextStyle": "white"
  },
  "tabBar": {
    "custom": true,
    "list": [
      { "pagePath": "pages/index/index", "text": "首页" },
      { "pagePath": "pages/practice/practice", "text": "练习" }
    ]
  }
}
```

- [ ] **Step 2：Commit**

```powershell
git add wechat-miniapp/app.json
git commit -m "feat: register 15 new pages in app.json"
```

---

## Task 2.2：我的战绩 (stats)

**Files:**
- Create: `wechat-miniapp/pages/stats/stats.{js,wxml,wxss,json}`

- [ ] **Step 1：创建 stats.json**

```json
{
  "navigationBarTitleText": "我的战绩",
  "navigationBarBackgroundColor": "#4A90D9",
  "navigationBarTextStyle": "white"
}
```

- [ ] **Step 2：创建 stats.js**

```javascript
const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');
const api = require('../../utils/api.js');

Page({
  data: {
    isLoggedIn: false,
    totalAnswered: 0,
    correctCount: 0,
    wrongCount: 0,
    correctRate: 0,
    bySubject: [],
    loading: true
  },

  onShow() {
    this.loadStats();
  },

  loadStats() {
    const isLoggedIn = auth.isLoggedIn();
    this.setData({ isLoggedIn });
    if (isLoggedIn) {
      api.getStats()
        .then(stats => {
          this.setData({
            totalAnswered: stats.total_answered,
            correctCount: stats.correct_count,
            wrongCount: stats.wrong_count,
            correctRate: stats.correct_rate,
            loading: false
          });
        })
        .catch(() => this.loadLocalStats());
    } else {
      this.loadLocalStats();
    }
  },

  loadLocalStats() {
    const progress = storage.getProgress();
    const total = progress.length;
    const correct = progress.filter(p => p.is_correct).length;
    const subjectMap = {};
    progress.forEach(p => {
      const subj = p.subject || '未分类';
      if (!subjectMap[subj]) subjectMap[subj] = { subject: subj, total: 0, correct: 0 };
      subjectMap[subj].total += 1;
      if (p.is_correct) subjectMap[subj].correct += 1;
    });
    const bySubject = Object.values(subjectMap).map(s => ({
      subject: s.subject,
      total: s.total,
      rate: s.total > 0 ? Math.round(s.correct / s.total * 100) : 0
    }));
    this.setData({
      totalAnswered: total,
      correctCount: correct,
      wrongCount: total - correct,
      correctRate: total > 0 ? Math.round(correct / total * 100) : 0,
      bySubject,
      loading: false
    });
  }
});
```

- [ ] **Step 3：创建 stats.wxml**

```xml
<view class="container">
  <view wx:if="{{loading}}" class="loading">加载中...</view>
  <block wx:else>
    <view class="hero-card">
      <view class="hero-rate">{{correctRate}}<text class="hero-rate-unit">%</text></view>
      <view class="hero-label">总正确率</view>
    </view>
    <view class="stat-row">
      <view class="stat-cell"><text class="stat-num">{{totalAnswered}}</text><text class="stat-label">已答题</text></view>
      <view class="stat-cell"><text class="stat-num green">{{correctCount}}</text><text class="stat-label">答对</text></view>
      <view class="stat-cell"><text class="stat-num red">{{wrongCount}}</text><text class="stat-label">答错</text></view>
    </view>
    <view wx:if="{{bySubject.length > 0}}" class="section">
      <view class="section-title">分科目正确率</view>
      <view wx:for="{{bySubject}}" wx:key="subject" class="subject-row">
        <text class="subject-name">{{item.subject}}</text>
        <view class="subject-bar"><view class="subject-bar-fill" style="width: {{item.rate}}%"></view></view>
        <text class="subject-rate">{{item.rate}}%</text>
      </view>
    </view>
    <view wx:if="{{totalAnswered === 0}}" class="empty">还没有答题记录，去练习吧！</view>
  </block>
</view>
```

- [ ] **Step 4：创建 stats.wxss**

```css
.container { padding: 30rpx; background: #f5f5f5; min-height: 100vh; }
.loading { text-align: center; padding: 200rpx 0; color: #999; }
.hero-card { background: linear-gradient(135deg, #4A90D9, #6BA8E8); border-radius: 24rpx; padding: 60rpx 30rpx; text-align: center; color: #fff; margin-bottom: 30rpx; box-shadow: 0 8rpx 24rpx rgba(74,144,217,0.3); }
.hero-rate { font-size: 120rpx; font-weight: bold; line-height: 1; }
.hero-rate-unit { font-size: 48rpx; margin-left: 8rpx; }
.hero-label { font-size: 28rpx; margin-top: 10rpx; opacity: 0.9; }
.stat-row { display: flex; background: #fff; border-radius: 16rpx; padding: 30rpx; margin-bottom: 30rpx; }
.stat-cell { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 10rpx; }
.stat-num { font-size: 48rpx; font-weight: bold; color: #333; }
.stat-num.green { color: #2ECC71; }
.stat-num.red { color: #E74C3C; }
.stat-label { font-size: 24rpx; color: #999; }
.section { background: #fff; border-radius: 16rpx; padding: 30rpx; }
.section-title { font-size: 30rpx; font-weight: bold; margin-bottom: 24rpx; color: #333; }
.subject-row { display: flex; align-items: center; gap: 16rpx; padding: 18rpx 0; border-bottom: 2rpx solid #f5f5f5; }
.subject-row:last-child { border-bottom: none; }
.subject-name { width: 120rpx; font-size: 26rpx; color: #333; }
.subject-bar { flex: 1; height: 16rpx; background: #f0f0f0; border-radius: 8rpx; overflow: hidden; }
.subject-bar-fill { height: 100%; background: linear-gradient(90deg, #4A90D9, #6BA8E8); border-radius: 8rpx; }
.subject-rate { width: 80rpx; text-align: right; font-size: 26rpx; color: #4A90D9; font-weight: bold; }
.empty { text-align: center; padding: 100rpx 0; color: #999; font-size: 28rpx; }
```

- [ ] **Step 5：手动验证**

开发者工具：主页打开左侧个人面板 → 点"我的战绩"。
Expected: 页面打开，无报错。

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/stats
git commit -m "feat: add stats (我的战绩) page"
```

---

## Task 2.3：我的题目 (myquestions)

**Files:**
- Create: `wechat-miniapp/pages/myquestions/myquestions.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/utils/api.js`
- Modify: `backend/routes/import.py`

- [ ] **Step 1：在 api.js 加 getMyQuestions**

把 `wechat-miniapp/utils/api.js` 的 `module.exports` 完整覆写为：
```javascript
module.exports = {
  request,
  getQuestions: (params) => request('/questions', 'GET', params),
  getQuestion: (id) => request(`/questions/${id}`),
  getRandomQuestion: (params) => request('/questions/random', 'GET', params),
  submitAnswer: (data) => request('/practice/submit', 'POST', data),
  submitProgress: (data) => request('/progress', 'POST', data),
  getProgress: (params) => request('/progress', 'GET', params),
  getWrongQuestions: (params) => request('/progress/wrong', 'GET', params),
  getStats: () => request('/progress/stats'),
  getProfile: () => request('/users/profile'),
  updateProfile: (data) => request('/users/profile', 'PUT', data),
  getMyQuestions: (params) => request('/import/my-questions', 'GET', params)
};
```

- [ ] **Step 2：后端追加 /my-questions 端点**

在 `backend/routes/import.py` 文件末尾追加：
```python
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import ParsedQuestion

@import_bp.route('/my-questions', methods=['GET'])
@jwt_required()
def my_questions():
    status = request.args.get('status', '')
    query = ParsedQuestion.query
    if status:
        query = query.filter_by(status=status)
    items = query.order_by(ParsedQuestion.created_at.desc()).limit(50).all()
    return jsonify({
        'questions': [{
            'id': q.id,
            'content': q.content or q.raw_content or '',
            'subject': q.subject,
            'status': q.status,
            'created_at': q.created_at.strftime('%Y-%m-%d %H:%M')
        } for q in items]
    })
```

> **说明：** `ParsedQuestion` 无 `created_by` 字段，MVP 阶段返回所有 ParsedQuestion。后续可独立任务加 created_by。

- [ ] **Step 3：创建 myquestions.json**

```json
{
  "navigationBarTitleText": "我的题目",
  "navigationBarBackgroundColor": "#4A90D9",
  "navigationBarTextStyle": "white"
}
```

- [ ] **Step 4：创建 myquestions.js**

```javascript
const auth = require('../../utils/auth.js');
const api = require('../../utils/api.js');

Page({
  data: { isLoggedIn: false, activeTab: 'all', questions: [], loading: true },

  onShow() {
    const isLoggedIn = auth.isLoggedIn();
    this.setData({ isLoggedIn });
    if (isLoggedIn) this.loadQuestions();
    else this.setData({ loading: false });
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab, loading: true });
    this.loadQuestions();
  },

  loadQuestions() {
    const status = this.data.activeTab === 'all' ? '' : this.data.activeTab;
    api.getMyQuestions({ status })
      .then(res => this.setData({ questions: res.questions || [], loading: false }))
      .catch(() => this.setData({ questions: [], loading: false }));
  },

  goSubmit() {
    wx.navigateTo({ url: '/pages/import/import' });
  }
});
```

- [ ] **Step 5：创建 myquestions.wxml**

```xml
<view class="container">
  <view wx:if="{{!isLoggedIn}}" class="empty"><text>请先登录后查看你的题目</text></view>
  <block wx:else>
    <view class="tabs">
      <view class="tab {{activeTab === 'all' ? 'active' : ''}}" data-tab="all" bindtap="switchTab">全部</view>
      <view class="tab {{activeTab === 'pending' ? 'active' : ''}}" data-tab="pending" bindtap="switchTab">审核中</view>
      <view class="tab {{activeTab === 'approved' ? 'active' : ''}}" data-tab="approved" bindtap="switchTab">已入库</view>
      <view class="tab {{activeTab === 'rejected' ? 'active' : ''}}" data-tab="rejected" bindtap="switchTab">未通过</view>
    </view>
    <view wx:if="{{loading}}" class="loading">加载中...</view>
    <block wx:elif="{{questions.length > 0}}">
      <view class="q-card" wx:for="{{questions}}" wx:key="id">
        <view class="q-status status-{{item.status}}">{{item.status === 'pending' ? '审核中' : item.status === 'approved' ? '已入库' : '未通过'}}</view>
        <view class="q-content">{{item.content}}</view>
        <view class="q-meta"><text>{{item.subject || '—'}}</text><text>·</text><text>{{item.created_at}}</text></view>
      </view>
    </block>
    <view wx:else class="empty">
      <text>还没有提交过题目</text>
      <button class="submit-btn" bindtap="goSubmit">去提交</button>
    </view>
  </block>
</view>
```

- [ ] **Step 6：创建 myquestions.wxss**

```css
.container { padding: 0; background: #f5f5f5; min-height: 100vh; }
.tabs { display: flex; background: #fff; border-bottom: 2rpx solid #f0f0f0; position: sticky; top: 0; z-index: 10; }
.tab { flex: 1; padding: 28rpx 0; text-align: center; font-size: 28rpx; color: #666; }
.tab.active { color: #4A90D9; font-weight: bold; border-bottom: 4rpx solid #4A90D9; }
.loading, .empty { text-align: center; padding: 200rpx 30rpx; color: #999; display: flex; flex-direction: column; align-items: center; gap: 30rpx; }
.submit-btn { background: #4A90D9; color: #fff; padding: 16rpx 60rpx; border-radius: 40rpx; font-size: 28rpx; }
.q-card { background: #fff; margin: 20rpx; padding: 24rpx; border-radius: 16rpx; position: relative; }
.q-status { position: absolute; top: 24rpx; right: 24rpx; padding: 6rpx 16rpx; border-radius: 20rpx; font-size: 22rpx; }
.q-status.status-pending { background: #FFF3E0; color: #F39C12; }
.q-status.status-approved { background: #E8F5E9; color: #2ECC71; }
.q-status.status-rejected { background: #FFEBEE; color: #E74C3C; }
.q-content { font-size: 28rpx; color: #333; line-height: 1.6; padding-right: 120rpx; margin-bottom: 16rpx; }
.q-meta { display: flex; gap: 12rpx; font-size: 22rpx; color: #999; }
```

- [ ] **Step 7：验证 + Commit**

重启 backend，小程序中打开"我的题目"切 4 个 tab 不报错。
```powershell
git add wechat-miniapp/pages/myquestions wechat-miniapp/utils/api.js backend/routes/import.py
git commit -m "feat: add myquestions page + /import/my-questions endpoint"
```

---

## Task 2.4：我的书包 (mybag)

**Files:**
- Create: `wechat-miniapp/pages/mybag/mybag.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/utils/storage.js`

- [ ] **Step 1：扩展 storage.js**

把 `wechat-miniapp/utils/storage.js` 完整覆写为：
```javascript
const STORAGE_KEYS = { PROGRESS: 'local_progress', NOTES: 'local_notes', USER: 'user_info', SYNC_TIME: 'last_sync_time', FAVORITES: 'local_favorites' };

function get(key) { return wx.getStorageSync(key); }
function set(key, value) { wx.setStorageSync(key, value); }

function saveProgress(progress) {
  const list = get(STORAGE_KEYS.PROGRESS) || [];
  list.push(progress);
  set(STORAGE_KEYS.PROGRESS, list);
}

function getProgress() { return get(STORAGE_KEYS.PROGRESS) || []; }
function getWrongQuestions() { return getProgress().filter(p => !p.is_correct); }

function saveNote(note) {
  const list = get(STORAGE_KEYS.NOTES) || [];
  list.unshift(note);
  set(STORAGE_KEYS.NOTES, list);
}

function getNotes() { return get(STORAGE_KEYS.NOTES) || []; }

function addFavorite(question) {
  const list = get(STORAGE_KEYS.FAVORITES) || [];
  if (list.find(q => q.id === question.id)) return false;
  list.unshift({ ...question, favorited_at: Date.now() });
  set(STORAGE_KEYS.FAVORITES, list);
  return true;
}

function removeFavorite(id) {
  const list = (get(STORAGE_KEYS.FAVORITES) || []).filter(q => q.id !== id);
  set(STORAGE_KEYS.FAVORITES, list);
}

function getFavorites() { return get(STORAGE_KEYS.FAVORITES) || []; }
function isFavorited(id) { return !!(get(STORAGE_KEYS.FAVORITES) || []).find(q => q.id === id); }

function setUserInfo(userInfo) { set(STORAGE_KEYS.USER, userInfo); }
function getUserInfo() { return get(STORAGE_KEYS.USER); }
function setSyncTime(time) { set(STORAGE_KEYS.SYNC_TIME, time); }
function getSyncTime() { return get(STORAGE_KEYS.SYNC_TIME); }
function clearAll() { Object.values(STORAGE_KEYS).forEach(key => { wx.removeStorageSync(key); }); }

module.exports = { STORAGE_KEYS, saveProgress, getProgress, getWrongQuestions, saveNote, getNotes, setUserInfo, getUserInfo, setSyncTime, getSyncTime, clearAll, addFavorite, removeFavorite, getFavorites, isFavorited };
```

- [ ] **Step 2：mybag.json**

```json
{"navigationBarTitleText":"我的书包","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 3：mybag.js**

```javascript
const storage = require('../../utils/storage.js');

Page({
  data: { favorites: [] },
  onShow() { this.setData({ favorites: storage.getFavorites() }); },
  goPractice(e) { wx.navigateTo({ url: `/pages/practice/practice?id=${e.currentTarget.dataset.id}` }); },
  removeFav(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示', content: '确定从书包移除这道题？',
      success: (res) => {
        if (res.confirm) {
          storage.removeFavorite(id);
          this.setData({ favorites: storage.getFavorites() });
          wx.showToast({ title: '已移除', icon: 'success' });
        }
      }
    });
  }
});
```

- [ ] **Step 4：mybag.wxml**

```xml
<view class="container">
  <view class="header"><text class="title">我的书包</text><text class="count">共 {{favorites.length}} 题</text></view>
  <view wx:if="{{favorites.length > 0}}" class="fav-list">
    <view wx:for="{{favorites}}" wx:key="id" class="fav-item">
      <view class="fav-main" data-id="{{item.id}}" bindtap="goPractice">
        <view class="fav-content">{{item.content}}</view>
        <view class="fav-meta"><text>{{item.subject || '—'}}</text><text wx:if="{{item.difficulty}}">·难度{{item.difficulty}}</text></view>
      </view>
      <view class="fav-remove" data-id="{{item.id}}" catchtap="removeFav">×</view>
    </view>
  </view>
  <view wx:else class="empty"><view class="empty-icon">🎒</view><text>书包是空的，刷题时点击收藏可加入这里</text></view>
</view>
```

- [ ] **Step 5：mybag.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding-bottom: 30rpx; }
.header { display: flex; justify-content: space-between; align-items: center; padding: 30rpx; background: #fff; }
.title { font-size: 34rpx; font-weight: bold; color: #333; }
.count { font-size: 26rpx; color: #999; }
.fav-list { padding: 20rpx; }
.fav-item { display: flex; background: #fff; border-radius: 16rpx; margin-bottom: 20rpx; overflow: hidden; }
.fav-main { flex: 1; padding: 24rpx; }
.fav-content { font-size: 28rpx; color: #333; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-bottom: 12rpx; }
.fav-meta { display: flex; gap: 12rpx; font-size: 22rpx; color: #999; }
.fav-remove { width: 80rpx; display: flex; align-items: center; justify-content: center; font-size: 48rpx; color: #ccc; border-left: 2rpx solid #f5f5f5; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 200rpx 30rpx; color: #999; gap: 30rpx; }
.empty-icon { font-size: 120rpx; }
```

- [ ] **Step 6：手动验证**

控制台执行：`wx.setStorageSync('local_favorites', [{id:1,content:'测试题',subject:'数学',difficulty:3}])` 再打开页面。

- [ ] **Step 7：Commit**

```powershell
git add wechat-miniapp/pages/mybag wechat-miniapp/utils/storage.js
git commit -m "feat: add mybag page + favorites storage methods"
```

---

## Task 2.5：我的同学 (classmates)

**Files:**
- Create: `wechat-miniapp/pages/classmates/classmates.{js,wxml,wxss,json}`

- [ ] **Step 1：classmates.json**

```json
{"navigationBarTitleText":"我的同学","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：classmates.js**

```javascript
Page({
  data: { classmates: [] },
  onShow() {
    const stored = wx.getStorageSync('classmates_list') || [];
    this.setData({ classmates: stored });
  },
  goInvite() { wx.navigateTo({ url: '/pages/invite/invite' }); }
});
```

- [ ] **Step 3：classmates.wxml**

```xml
<view class="container">
  <view wx:if="{{classmates.length > 0}}" class="cm-list">
    <view wx:for="{{classmates}}" wx:key="id" class="cm-item">
      <view class="cm-avatar">{{item.nickname[0] || '👤'}}</view>
      <view class="cm-info">
        <text class="cm-name">{{item.nickname}}</text>
        <text class="cm-meta">{{item.subject || '未设置科目'}}</text>
      </view>
      <view class="cm-badge">Lv.{{item.level || 1}}</view>
    </view>
  </view>
  <view wx:else class="empty">
    <view class="empty-icon">👥</view>
    <text class="empty-title">还没有同学</text>
    <text class="empty-desc">邀请同学一起刷题，互相督促进步</text>
    <button class="invite-btn" bindtap="goInvite">邀请同学</button>
  </view>
</view>
```

- [ ] **Step 4：classmates.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding: 20rpx; }
.cm-list { display: flex; flex-direction: column; gap: 16rpx; }
.cm-item { display: flex; align-items: center; gap: 20rpx; background: #fff; padding: 24rpx; border-radius: 16rpx; }
.cm-avatar { width: 80rpx; height: 80rpx; border-radius: 50%; background: linear-gradient(135deg, #4A90D9, #6BA8E8); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 32rpx; }
.cm-info { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.cm-name { font-size: 30rpx; color: #333; font-weight: bold; }
.cm-meta { font-size: 24rpx; color: #999; }
.cm-badge { padding: 6rpx 16rpx; background: #FFD700; color: #fff; border-radius: 20rpx; font-size: 22rpx; font-weight: bold; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 160rpx 30rpx; gap: 24rpx; }
.empty-icon { font-size: 120rpx; }
.empty-title { font-size: 32rpx; color: #333; font-weight: bold; }
.empty-desc { font-size: 26rpx; color: #999; text-align: center; }
.invite-btn { background: #4A90D9; color: #fff; padding: 16rpx 60rpx; border-radius: 40rpx; font-size: 28rpx; margin-top: 20rpx; }
```

- [ ] **Step 5：Commit**

```powershell
git add wechat-miniapp/pages/classmates
git commit -m "feat: add classmates page"
```

---

## Task 2.6：邀请同学 (invite)

**Files:**
- Create: `wechat-miniapp/pages/invite/invite.{js,wxml,wxss,json}`

- [ ] **Step 1：invite.json**

```json
{"navigationBarTitleText":"邀请同学","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：invite.js**

```javascript
const auth = require('../../utils/auth.js');

Page({
  data: { inviteCode: '', inviteText: '' },

  onLoad() {
    const user = auth.getUserInfo();
    const code = user && user.id ? `BRO${String(user.id).padStart(6, '0')}` : 'BROGUEST';
    const text = `我在 BRO 刷题，邀请你一起备考！邀请码：${code}，下载小程序后输入即可绑定同学关系。`;
    this.setData({ inviteCode: code, inviteText: text });
  },

  copyCode() {
    wx.setClipboardData({
      data: this.data.inviteCode,
      success: () => wx.showToast({ title: '邀请码已复制', icon: 'success' })
    });
  },

  copyText() {
    wx.setClipboardData({
      data: this.data.inviteText,
      success: () => wx.showToast({ title: '邀请文案已复制', icon: 'success' })
    });
  },

  onShareAppMessage() {
    return { title: 'BRO 刷题 - 一起备考', path: `/pages/index/index?invite=${this.data.inviteCode}` };
  }
});
```

- [ ] **Step 3：invite.wxml**

```xml
<view class="container">
  <view class="hero">
    <view class="hero-icon">🎁</view>
    <view class="hero-title">邀请同学一起刷题</view>
    <view class="hero-desc">每邀请一位同学，双方都得 50 积分</view>
  </view>
  <view class="code-card">
    <view class="code-label">我的邀请码</view>
    <view class="code-value">{{inviteCode}}</view>
    <button class="copy-btn" bindtap="copyCode">复制邀请码</button>
  </view>
  <view class="text-card">
    <view class="text-label">邀请文案</view>
    <view class="text-value">{{inviteText}}</view>
    <button class="copy-btn" bindtap="copyText">复制文案</button>
  </view>
  <button class="share-btn" open-type="share">分享给微信好友</button>
</view>
```

- [ ] **Step 4：invite.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding: 30rpx; }
.hero { background: linear-gradient(135deg, #4A90D9, #6BA8E8); border-radius: 24rpx; padding: 50rpx 30rpx; text-align: center; color: #fff; margin-bottom: 30rpx; }
.hero-icon { font-size: 100rpx; }
.hero-title { font-size: 34rpx; font-weight: bold; margin-top: 20rpx; }
.hero-desc { font-size: 26rpx; opacity: 0.9; margin-top: 12rpx; }
.code-card, .text-card { background: #fff; border-radius: 16rpx; padding: 30rpx; margin-bottom: 24rpx; }
.code-label, .text-label { font-size: 26rpx; color: #999; margin-bottom: 16rpx; }
.code-value { font-size: 56rpx; font-weight: bold; color: #4A90D9; letter-spacing: 4rpx; text-align: center; margin: 20rpx 0; font-family: monospace; }
.text-value { font-size: 28rpx; color: #333; line-height: 1.6; padding: 20rpx; background: #f9f9f9; border-radius: 12rpx; margin-bottom: 20rpx; }
.copy-btn { background: #4A90D9; color: #fff; border-radius: 40rpx; font-size: 28rpx; }
.share-btn { background: #2ECC71; color: #fff; border-radius: 40rpx; font-size: 30rpx; margin-top: 30rpx; }
```

- [ ] **Step 5：Commit**

```powershell
git add wechat-miniapp/pages/invite
git commit -m "feat: add invite page with share support"
```

---

## Task 2.7：我的会员 (membership)

**Files:**
- Create: `wechat-miniapp/pages/membership/membership.{js,wxml,wxss,json}`

- [ ] **Step 1：membership.json**

```json
{"navigationBarTitleText":"我的会员","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：membership.js**

```javascript
const auth = require('../../utils/auth.js');
const api = require('../../utils/api.js');

Page({
  data: {
    memberType: 'free',
    expireDate: '',
    benefits: [
      { icon: '🚫', title: '免广告', free: false, premium: true },
      { icon: '📚', title: '完整题库', free: false, premium: true },
      { icon: '🤖', title: 'AI 解析无限次', free: false, premium: true },
      { icon: '📊', title: '详细学习报告', free: false, premium: true },
      { icon: '💾', title: '云端同步', free: true, premium: true },
      { icon: '✏️', title: '错题本', free: true, premium: true }
    ]
  },

  onShow() {
    const userInfo = auth.getUserInfo();
    if (userInfo) this.setData({ memberType: userInfo.member_type || 'free' });
    if (auth.isLoggedIn()) {
      api.getProfile()
        .then(p => this.setData({ memberType: p.member_type || 'free' }))
        .catch(() => {});
    }
  },

  upgrade() {
    wx.showModal({ title: '会员升级', content: '会员功能即将上线，敬请期待！', showCancel: false });
  }
});
```

- [ ] **Step 3：membership.wxml**

```xml
<view class="container">
  <view class="hero {{memberType}}">
    <view class="hero-crown">{{memberType === 'premium' ? '👑' : '👤'}}</view>
    <view class="hero-type">{{memberType === 'premium' ? 'Premium 会员' : '免费用户'}}</view>
    <view wx:if="{{memberType === 'premium' && expireDate}}" class="hero-expire">到期时间：{{expireDate}}</view>
  </view>
  <view class="section-title">会员权益对比</view>
  <view class="benefits-table">
    <view class="bt-header">
      <view class="bt-cell name">权益</view>
      <view class="bt-cell">免费</view>
      <view class="bt-cell highlight">Premium</view>
    </view>
    <view wx:for="{{benefits}}" wx:key="title" class="bt-row">
      <view class="bt-cell name"><text class="b-icon">{{item.icon}}</text><text>{{item.title}}</text></view>
      <view class="bt-cell">{{item.free ? '✓' : '—'}}</view>
      <view class="bt-cell highlight">{{item.premium ? '✓' : '—'}}</view>
    </view>
  </view>
  <button wx:if="{{memberType !== 'premium'}}" class="upgrade-btn" bindtap="upgrade">升级 Premium</button>
</view>
```

- [ ] **Step 4：membership.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding-bottom: 60rpx; }
.hero { padding: 60rpx 30rpx; text-align: center; color: #fff; }
.hero.free { background: linear-gradient(135deg, #95a5a6, #bdc3c7); }
.hero.premium { background: linear-gradient(135deg, #FFD700, #FFA500); }
.hero-crown { font-size: 100rpx; }
.hero-type { font-size: 36rpx; font-weight: bold; margin-top: 20rpx; }
.hero-expire { font-size: 24rpx; opacity: 0.9; margin-top: 10rpx; }
.section-title { font-size: 30rpx; font-weight: bold; color: #333; padding: 30rpx 30rpx 16rpx; }
.benefits-table { margin: 0 30rpx; background: #fff; border-radius: 16rpx; overflow: hidden; }
.bt-header, .bt-row { display: flex; border-bottom: 2rpx solid #f0f0f0; }
.bt-header { background: #f9f9f9; }
.bt-row:last-child { border-bottom: none; }
.bt-cell { flex: 1; padding: 24rpx 16rpx; text-align: center; font-size: 26rpx; color: #666; }
.bt-cell.name { flex: 2; text-align: left; display: flex; align-items: center; gap: 12rpx; color: #333; }
.bt-cell.highlight { color: #F39C12; font-weight: bold; }
.b-icon { font-size: 32rpx; }
.upgrade-btn { margin: 40rpx 30rpx 0; background: linear-gradient(135deg, #FFD700, #FFA500); color: #fff; font-size: 32rpx; font-weight: bold; border-radius: 50rpx; padding: 20rpx 0; }
```

- [ ] **Step 5：Commit**

```powershell
git add wechat-miniapp/pages/membership
git commit -m "feat: add membership page"
```

---

---

# Phase 3：主页占位按钮对应页面

## Task 3.1：每日挑战 (daily-challenge)

**Files:**
- Create: `wechat-miniapp/pages/daily-challenge/daily-challenge.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：daily-challenge.json**

```json
{"navigationBarTitleText":"每日挑战","navigationBarBackgroundColor":"#E74C3C","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：daily-challenge.js**

```javascript
const api = require('../../utils/api.js');

const TODAY_KEY = 'daily_challenge_date';
const TODAY_DONE = 'daily_challenge_done';

Page({
  data: { loading: true, question: null, alreadyDone: false, todayDate: '' },

  onLoad() {
    const today = this.getTodayStr();
    const lastDate = wx.getStorageSync(TODAY_KEY);
    const done = lastDate === today && wx.getStorageSync(TODAY_DONE);
    this.setData({ todayDate: today, alreadyDone: !!done });
    if (!done) this.loadChallenge();
    else this.setData({ loading: false });
  },

  getTodayStr() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
  },

  loadChallenge() {
    api.getRandomQuestion({})
      .then(q => this.setData({ question: q, loading: false }))
      .catch(() => {
        this.setData({ loading: false });
        wx.showToast({ title: '暂无题目', icon: 'none' });
      });
  },

  goAnswer() {
    if (!this.data.question) return;
    wx.setStorageSync(TODAY_KEY, this.data.todayDate);
    wx.setStorageSync(TODAY_DONE, true);
    wx.navigateTo({ url: `/pages/practice/practice?id=${this.data.question.id}&challenge=1` });
  }
});
```

- [ ] **Step 3：daily-challenge.wxml**

```xml
<view class="container">
  <view class="hero">
    <view class="hero-flame">🔥</view>
    <view class="hero-title">每日挑战</view>
    <view class="hero-date">{{todayDate}}</view>
    <view class="hero-bonus">答对得 2 倍积分</view>
  </view>
  <view wx:if="{{loading}}" class="loading">加载中...</view>
  <view wx:elif="{{alreadyDone}}" class="done-card">
    <view class="done-icon">✅</view>
    <view class="done-title">今日挑战已完成</view>
    <view class="done-desc">明天再来吧</view>
  </view>
  <block wx:elif="{{question}}">
    <view class="question-card">
      <view class="q-type">{{question.type === 'choice' ? '选择题' : question.type === 'blank' ? '填空题' : '解答题'}}</view>
      <view class="q-content">{{question.content}}</view>
    </view>
    <button class="answer-btn" bindtap="goAnswer">开始答题</button>
  </block>
  <view wx:else class="empty">题库为空，请先导入题目</view>
</view>
```

- [ ] **Step 4：daily-challenge.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding-bottom: 60rpx; }
.hero { background: linear-gradient(135deg, #E74C3C, #FF6B6B); padding: 60rpx 30rpx; text-align: center; color: #fff; }
.hero-flame { font-size: 120rpx; }
.hero-title { font-size: 40rpx; font-weight: bold; margin-top: 16rpx; }
.hero-date { font-size: 26rpx; opacity: 0.9; margin-top: 10rpx; }
.hero-bonus { display: inline-block; margin-top: 20rpx; padding: 8rpx 24rpx; background: rgba(255,255,255,0.25); border-radius: 30rpx; font-size: 24rpx; }
.loading, .empty { text-align: center; padding: 100rpx 0; color: #999; }
.done-card { margin: 40rpx 30rpx; background: #fff; border-radius: 16rpx; padding: 60rpx 30rpx; text-align: center; }
.done-icon { font-size: 100rpx; }
.done-title { font-size: 32rpx; font-weight: bold; margin-top: 20rpx; color: #333; }
.done-desc { font-size: 26rpx; color: #999; margin-top: 12rpx; }
.question-card { margin: 30rpx; background: #fff; border-radius: 16rpx; padding: 30rpx; }
.q-type { display: inline-block; padding: 6rpx 16rpx; background: #FFEBEE; color: #E74C3C; border-radius: 20rpx; font-size: 22rpx; margin-bottom: 16rpx; }
.q-content { font-size: 30rpx; color: #333; line-height: 1.8; }
.answer-btn { margin: 30rpx; background: #E74C3C; color: #fff; border-radius: 50rpx; font-size: 32rpx; font-weight: bold; }
```

- [ ] **Step 5：修改 index.js 的 goDailyChallenge**

把 `index.js` 中：
```javascript
  goDailyChallenge() {
    wx.showToast({ title: '每日挑战', icon: 'none' });
  },
```
改为：
```javascript
  goDailyChallenge() {
    wx.navigateTo({ url: '/pages/daily-challenge/daily-challenge' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/daily-challenge wechat-miniapp/pages/index/index.js
git commit -m "feat: add daily-challenge page"
```

---

## Task 3.2：排行榜 (leaderboard) + 后端 API

**Files:**
- Create: `backend/routes/leaderboard.py`
- Modify: `backend/routes/__init__.py`
- Create: `backend/tests/test_leaderboard.py`
- Create: `wechat-miniapp/pages/leaderboard/leaderboard.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/utils/api.js`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：在 routes/__init__.py 注册 leaderboard_bp**

把 `backend/routes/__init__.py` 完整覆写为：
```python
from flask import Blueprint
import importlib

questions_bp = Blueprint('questions', __name__)
users_bp = Blueprint('users', __name__)
shares_bp = Blueprint('shares', __name__)
progress_bp = Blueprint('progress', __name__)
sync_bp = Blueprint('sync', __name__)
import_bp = Blueprint('import', __name__)
leaderboard_bp = Blueprint('leaderboard', __name__)

def register_blueprints(app):
    from . import questions, shares, sync, users, progress, leaderboard
    importlib.import_module('.import', 'routes')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(import_bp, url_prefix='/api/import')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
```

- [ ] **Step 2：写 leaderboard.py**

创建 `backend/routes/leaderboard.py`：
```python
from flask import request, jsonify
from sqlalchemy import func, Integer
from models import db, User, UserProgress
from . import leaderboard_bp


@leaderboard_bp.route('', methods=['GET'])
def get_leaderboard():
    limit = request.args.get('limit', 50, type=int)
    metric = request.args.get('metric', 'correct')

    if metric == 'total':
        rows = db.session.query(
            User.id, User.nickname, User.avatar,
            func.count(UserProgress.id).label('score')
        ).join(UserProgress, UserProgress.user_id == User.id) \
         .group_by(User.id).order_by(func.count(UserProgress.id).desc()).limit(limit).all()
    else:
        rows = db.session.query(
            User.id, User.nickname, User.avatar,
            func.sum(func.cast(UserProgress.is_correct, Integer)).label('score')
        ).join(UserProgress, UserProgress.user_id == User.id) \
         .group_by(User.id).order_by(func.sum(func.cast(UserProgress.is_correct, Integer)).desc()).limit(limit).all()

    return jsonify({
        'metric': metric,
        'ranking': [
            {
                'rank': i + 1,
                'user_id': r.id,
                'nickname': r.nickname or '匿名',
                'avatar': r.avatar or '',
                'score': int(r.score or 0)
            }
            for i, r in enumerate(rows)
        ]
    })
```

- [ ] **Step 3：写 test_leaderboard.py**

创建 `backend/tests/test_leaderboard.py`：
```python
def test_leaderboard_empty(client):
    resp = client.get('/api/leaderboard')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ranking'] == []
    assert data['metric'] == 'correct'


def test_leaderboard_metric_total(client):
    resp = client.get('/api/leaderboard?metric=total')
    assert resp.status_code == 200
    assert resp.get_json()['metric'] == 'total'
```

- [ ] **Step 4：运行测试**

工作目录 `backend`：
```powershell
pytest tests/test_leaderboard.py -v
```
Expected: `2 passed`

- [ ] **Step 5：api.js 加 getLeaderboard**

把 `utils/api.js` 的 module.exports 完整覆写为：
```javascript
module.exports = {
  request,
  getQuestions: (params) => request('/questions', 'GET', params),
  getQuestion: (id) => request(`/questions/${id}`),
  getRandomQuestion: (params) => request('/questions/random', 'GET', params),
  submitAnswer: (data) => request('/practice/submit', 'POST', data),
  submitProgress: (data) => request('/progress', 'POST', data),
  getProgress: (params) => request('/progress', 'GET', params),
  getWrongQuestions: (params) => request('/progress/wrong', 'GET', params),
  getStats: () => request('/progress/stats'),
  getProfile: () => request('/users/profile'),
  updateProfile: (data) => request('/users/profile', 'PUT', data),
  getMyQuestions: (params) => request('/import/my-questions', 'GET', params),
  getLeaderboard: (params) => request('/leaderboard', 'GET', params)
};
```

- [ ] **Step 6：leaderboard.json**

```json
{"navigationBarTitleText":"排行榜","navigationBarBackgroundColor":"#9B59B6","navigationBarTextStyle":"white"}
```

- [ ] **Step 7：leaderboard.js**

```javascript
const api = require('../../utils/api.js');

Page({
  data: { metric: 'correct', ranking: [], loading: true },

  onShow() { this.loadRanking(); },

  switchMetric(e) {
    this.setData({ metric: e.currentTarget.dataset.metric, loading: true });
    this.loadRanking();
  },

  loadRanking() {
    api.getLeaderboard({ metric: this.data.metric, limit: 50 })
      .then(res => this.setData({ ranking: res.ranking || [], loading: false }))
      .catch(() => this.setData({ ranking: [], loading: false }));
  }
});
```

- [ ] **Step 8：leaderboard.wxml**

```xml
<view class="container">
  <view class="tabs">
    <view class="tab {{metric === 'correct' ? 'active' : ''}}" data-metric="correct" bindtap="switchMetric">答对排行</view>
    <view class="tab {{metric === 'total' ? 'active' : ''}}" data-metric="total" bindtap="switchMetric">答题排行</view>
  </view>
  <view wx:if="{{loading}}" class="loading">加载中...</view>
  <view wx:elif="{{ranking.length > 0}}" class="rank-list">
    <view wx:for="{{ranking}}" wx:key="user_id" class="rank-item rank-{{item.rank <= 3 ? item.rank : 'normal'}}">
      <view class="rank-num">{{item.rank}}</view>
      <view class="rank-avatar">{{item.nickname[0] || '👤'}}</view>
      <view class="rank-name">{{item.nickname}}</view>
      <view class="rank-score">{{item.score}}</view>
    </view>
  </view>
  <view wx:else class="empty">还没有排行数据</view>
</view>
```

- [ ] **Step 9：leaderboard.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; }
.tabs { display: flex; background: #fff; }
.tab { flex: 1; padding: 28rpx 0; text-align: center; font-size: 28rpx; color: #666; }
.tab.active { color: #9B59B6; font-weight: bold; border-bottom: 4rpx solid #9B59B6; }
.loading, .empty { text-align: center; padding: 200rpx 0; color: #999; }
.rank-list { padding: 20rpx; }
.rank-item { display: flex; align-items: center; gap: 20rpx; background: #fff; padding: 20rpx 24rpx; border-radius: 16rpx; margin-bottom: 16rpx; }
.rank-item.rank-1 { background: linear-gradient(135deg, #FFD700, #FFE57F); }
.rank-item.rank-2 { background: linear-gradient(135deg, #C0C0C0, #E0E0E0); }
.rank-item.rank-3 { background: linear-gradient(135deg, #CD7F32, #D9A06B); }
.rank-num { width: 60rpx; text-align: center; font-size: 36rpx; font-weight: bold; color: #999; }
.rank-item.rank-1 .rank-num, .rank-item.rank-2 .rank-num, .rank-item.rank-3 .rank-num { color: #fff; }
.rank-avatar { width: 70rpx; height: 70rpx; border-radius: 50%; background: linear-gradient(135deg, #4A90D9, #6BA8E8); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 30rpx; }
.rank-name { flex: 1; font-size: 30rpx; color: #333; }
.rank-item.rank-1 .rank-name, .rank-item.rank-2 .rank-name, .rank-item.rank-3 .rank-name { color: #fff; font-weight: bold; }
.rank-score { font-size: 32rpx; font-weight: bold; color: #9B59B6; }
.rank-item.rank-1 .rank-score, .rank-item.rank-2 .rank-score, .rank-item.rank-3 .rank-score { color: #fff; }
```

- [ ] **Step 10：index.js 的 goLeaderboard**

把 `goLeaderboard()` 内 toast 替换为：
```javascript
  goLeaderboard() {
    wx.navigateTo({ url: '/pages/leaderboard/leaderboard' });
  },
```

- [ ] **Step 11：curl 验证 + Commit**

```powershell
curl.exe -s http://127.0.0.1:5001/api/leaderboard
```
Expected: `{"metric":"correct","ranking":[]}`

```powershell
git add backend/routes/leaderboard.py backend/routes/__init__.py backend/tests/test_leaderboard.py wechat-miniapp/pages/leaderboard wechat-miniapp/utils/api.js wechat-miniapp/pages/index/index.js
git commit -m "feat: add leaderboard page + backend API + tests"
```

---

## Task 3.3：积分商城 (points-shop)

**Files:**
- Create: `wechat-miniapp/pages/points-shop/points-shop.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：points-shop.json**

```json
{"navigationBarTitleText":"积分商城","navigationBarBackgroundColor":"#1ABC9C","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：points-shop.js**

```javascript
const auth = require('../../utils/auth.js');
const api = require('../../utils/api.js');

Page({
  data: {
    userPoints: 0,
    items: [
      { id: 1, name: 'AI 解析 1 次', icon: '🤖', cost: 50 },
      { id: 2, name: '错题 PDF 导出', icon: '📄', cost: 200 },
      { id: 3, name: '免广告 7 天', icon: '🚫', cost: 500 },
      { id: 4, name: 'Premium 1 月', icon: '👑', cost: 2000 },
      { id: 5, name: '专属头像框', icon: '🖼️', cost: 1000 },
      { id: 6, name: '能量饮料 (虚拟)', icon: '⚡', cost: 30 }
    ]
  },

  onShow() {
    if (auth.isLoggedIn()) {
      api.getProfile()
        .then(p => this.setData({ userPoints: p.points || 0 }))
        .catch(() => {});
    }
  },

  redeem(e) {
    const item = this.data.items.find(i => i.id === e.currentTarget.dataset.id);
    if (!item) return;
    if (this.data.userPoints < item.cost) {
      wx.showToast({ title: '积分不足', icon: 'none' });
      return;
    }
    wx.showModal({
      title: '确认兑换', content: `用 ${item.cost} 积分兑换「${item.name}」？`,
      success: (res) => {
        if (res.confirm) wx.showToast({ title: '功能即将上线', icon: 'none' });
      }
    });
  }
});
```

- [ ] **Step 3：points-shop.wxml**

```xml
<view class="container">
  <view class="balance">
    <text class="bal-label">我的积分</text>
    <text class="bal-value">{{userPoints}}</text>
  </view>
  <view class="grid">
    <view wx:for="{{items}}" wx:key="id" class="item-card" data-id="{{item.id}}" bindtap="redeem">
      <view class="item-icon">{{item.icon}}</view>
      <view class="item-name">{{item.name}}</view>
      <view class="item-cost">{{item.cost}} 积分</view>
    </view>
  </view>
</view>
```

- [ ] **Step 4：points-shop.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding-bottom: 30rpx; }
.balance { background: linear-gradient(135deg, #1ABC9C, #48C9B0); padding: 40rpx 30rpx; color: #fff; display: flex; justify-content: space-between; align-items: center; }
.bal-label { font-size: 28rpx; opacity: 0.9; }
.bal-value { font-size: 60rpx; font-weight: bold; }
.grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20rpx; padding: 20rpx; }
.item-card { background: #fff; border-radius: 16rpx; padding: 30rpx 20rpx; text-align: center; display: flex; flex-direction: column; gap: 12rpx; }
.item-card:active { opacity: 0.8; transform: scale(0.97); }
.item-icon { font-size: 80rpx; }
.item-name { font-size: 28rpx; color: #333; font-weight: bold; }
.item-cost { display: inline-block; padding: 8rpx 0; background: #E8F8F5; color: #1ABC9C; font-size: 24rpx; border-radius: 20rpx; margin: 0 auto; width: 70%; }
```

- [ ] **Step 5：index.js 的 goPointsShop**

替换为：
```javascript
  goPointsShop() {
    wx.navigateTo({ url: '/pages/points-shop/points-shop' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/points-shop wechat-miniapp/pages/index/index.js
git commit -m "feat: add points-shop page"
```

---

## Task 3.4：理词通 (licitong)

**Files:**
- Create: `wechat-miniapp/pages/licitong/licitong.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：licitong.json**

```json
{"navigationBarTitleText":"理词通","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：licitong.js**

```javascript
Page({
  data: {
    index: 0,
    showAnswer: false,
    cards: [
      { word: '函数', def: '数学：自变量与因变量之间的对应关系', example: 'y = 2x + 1 是一次函数' },
      { word: '导数', def: '函数在某点变化率的极限', example: 'f(x) = x² 的导数是 2x' },
      { word: '极限', def: '函数值无限接近某常数的过程', example: 'lim(x→0) sin(x)/x = 1' },
      { word: '积分', def: '与微分互为逆运算的求和过程', example: '∫x dx = ½x² + C' },
      { word: '向量', def: '既有大小又有方向的量', example: '(3, 4) 表示长度 5 的向量' }
    ]
  },

  flip() { this.setData({ showAnswer: !this.data.showAnswer }); },

  prev() {
    if (this.data.index > 0) this.setData({ index: this.data.index - 1, showAnswer: false });
  },

  next() {
    if (this.data.index < this.data.cards.length - 1) {
      this.setData({ index: this.data.index + 1, showAnswer: false });
    } else {
      wx.showToast({ title: '已经是最后一张了', icon: 'none' });
    }
  }
});
```

- [ ] **Step 3：licitong.wxml**

```xml
<view class="container">
  <view class="progress">{{index + 1}} / {{cards.length}}</view>
  <view class="card {{showAnswer ? 'flipped' : ''}}" bindtap="flip">
    <view wx:if="{{!showAnswer}}" class="card-front">
      <view class="card-word">{{cards[index].word}}</view>
      <view class="card-hint">点击查看释义</view>
    </view>
    <view wx:else class="card-back">
      <view class="card-def">{{cards[index].def}}</view>
      <view class="card-ex">例：{{cards[index].example}}</view>
    </view>
  </view>
  <view class="actions">
    <button class="act-btn" bindtap="prev" disabled="{{index === 0}}">上一个</button>
    <button class="act-btn primary" bindtap="next">下一个</button>
  </view>
</view>
```

- [ ] **Step 4：licitong.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 40rpx 30rpx; }
.progress { font-size: 26rpx; color: #999; margin-bottom: 30rpx; }
.card { width: 100%; height: 600rpx; background: #fff; border-radius: 24rpx; display: flex; align-items: center; justify-content: center; padding: 40rpx; box-sizing: border-box; box-shadow: 0 8rpx 24rpx rgba(0,0,0,0.08); transition: all 0.3s; }
.card:active { transform: scale(0.98); }
.card.flipped { background: #EBF4FF; }
.card-front, .card-back { text-align: center; width: 100%; }
.card-word { font-size: 100rpx; font-weight: bold; color: #4A90D9; }
.card-hint { font-size: 26rpx; color: #999; margin-top: 30rpx; }
.card-def { font-size: 36rpx; color: #333; line-height: 1.6; }
.card-ex { font-size: 28rpx; color: #666; margin-top: 30rpx; padding: 20rpx; background: #fff; border-radius: 12rpx; font-style: italic; }
.actions { display: flex; gap: 20rpx; width: 100%; margin-top: 40rpx; }
.act-btn { flex: 1; background: #fff; color: #4A90D9; border-radius: 50rpx; font-size: 28rpx; }
.act-btn.primary { background: #4A90D9; color: #fff; }
.act-btn[disabled] { opacity: 0.4; }
```

- [ ] **Step 5：index.js 的 goLiCiTong**

替换为：
```javascript
  goLiCiTong() {
    wx.navigateTo({ url: '/pages/licitong/licitong' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/licitong wechat-miniapp/pages/index/index.js
git commit -m "feat: add licitong flashcard page"
```

---

## Task 3.5：广场 (square)

**Files:**
- Create: `wechat-miniapp/pages/square/square.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：square.json**

```json
{"navigationBarTitleText":"广场","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：square.js**

```javascript
const api = require('../../utils/api.js');

Page({
  data: { shares: [], loading: true, page: 1 },

  onLoad() { this.loadShares(); },

  onReachBottom() {
    this.setData({ page: this.data.page + 1 });
    this.loadShares(true);
  },

  loadShares(append = false) {
    this.setData({ loading: true });
    api.request('/shares', 'GET', { page: this.data.page, per_page: 20 })
      .then(res => {
        const list = res.shares || [];
        const shares = append ? [...this.data.shares, ...list] : list;
        this.setData({ shares, loading: false });
      })
      .catch(() => this.setData({ loading: false }));
  }
});
```

- [ ] **Step 3：square.wxml**

```xml
<view class="container">
  <view wx:if="{{shares.length > 0}}" class="feed">
    <view wx:for="{{shares}}" wx:key="id" class="post">
      <view class="post-header">
        <view class="post-avatar">{{item.user_nickname[0] || '👤'}}</view>
        <view class="post-meta">
          <text class="post-name">{{item.user_nickname || '匿名'}}</text>
          <text class="post-time">{{item.created_at}}</text>
        </view>
      </view>
      <view class="post-content">{{item.content}}</view>
      <view class="post-actions">
        <text>👍 {{item.like_count || 0}}</text>
        <text>💬 {{item.comment_count || 0}}</text>
      </view>
    </view>
  </view>
  <view wx:elif="{{!loading}}" class="empty">
    <view class="empty-icon">🏛️</view>
    <text>广场还没有内容</text>
  </view>
  <view wx:if="{{loading}}" class="loading">加载中...</view>
</view>
```

- [ ] **Step 4：square.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding: 20rpx; }
.feed { display: flex; flex-direction: column; gap: 16rpx; }
.post { background: #fff; border-radius: 16rpx; padding: 24rpx; }
.post-header { display: flex; align-items: center; gap: 16rpx; margin-bottom: 16rpx; }
.post-avatar { width: 70rpx; height: 70rpx; border-radius: 50%; background: linear-gradient(135deg, #4A90D9, #6BA8E8); color: #fff; display: flex; align-items: center; justify-content: center; font-size: 28rpx; }
.post-meta { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
.post-name { font-size: 28rpx; color: #333; font-weight: bold; }
.post-time { font-size: 22rpx; color: #999; }
.post-content { font-size: 28rpx; color: #333; line-height: 1.6; margin-bottom: 16rpx; }
.post-actions { display: flex; gap: 30rpx; font-size: 24rpx; color: #999; }
.empty { text-align: center; padding: 200rpx 0; color: #999; display: flex; flex-direction: column; align-items: center; gap: 20rpx; }
.empty-icon { font-size: 120rpx; }
.loading { text-align: center; padding: 40rpx 0; color: #999; }
```

- [ ] **Step 5：index.js 的 goSquare**

替换为：
```javascript
  goSquare() {
    wx.navigateTo({ url: '/pages/square/square' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/square wechat-miniapp/pages/index/index.js
git commit -m "feat: add square page wired to /api/shares"
```

---

## Task 3.6：自习室 (studyroom)

**Files:**
- Create: `wechat-miniapp/pages/studyroom/studyroom.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：studyroom.json**

```json
{"navigationBarTitleText":"自习室","navigationBarBackgroundColor":"#2ECC71","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：studyroom.js**

```javascript
const STORAGE_KEY_DAY = 'studyroom_day';
const STORAGE_KEY_SEC = 'studyroom_seconds';

Page({
  data: { running: false, elapsedStr: '00:00:00', todayMinutes: 0 },
  _start: 0,
  _timer: null,

  onLoad() {
    const today = new Date().toDateString();
    const stored = wx.getStorageSync(STORAGE_KEY_DAY);
    const seconds = stored === today ? (wx.getStorageSync(STORAGE_KEY_SEC) || 0) : 0;
    if (stored !== today) {
      wx.setStorageSync(STORAGE_KEY_DAY, today);
      wx.setStorageSync(STORAGE_KEY_SEC, 0);
    }
    this.setData({ todayMinutes: Math.floor(seconds / 60) });
  },

  onUnload() {
    if (this.data.running) this.stop();
  },

  toggle() {
    if (this.data.running) this.stop();
    else this.start();
  },

  start() {
    this._start = Date.now();
    this.setData({ running: true });
    this._timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this._start) / 1000);
      this.setData({ elapsedStr: this.format(elapsed) });
    }, 1000);
  },

  stop() {
    if (this._timer) clearInterval(this._timer);
    this._timer = null;
    const seconds = Math.floor((Date.now() - this._start) / 1000);
    const total = (wx.getStorageSync(STORAGE_KEY_SEC) || 0) + seconds;
    wx.setStorageSync(STORAGE_KEY_SEC, total);
    this.setData({ running: false, elapsedStr: '00:00:00', todayMinutes: Math.floor(total / 60) });
    wx.showToast({ title: `本次专注 ${Math.floor(seconds / 60)} 分钟`, icon: 'success' });
  },

  format(sec) {
    const h = String(Math.floor(sec / 3600)).padStart(2, '0');
    const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return `${h}:${m}:${s}`;
  }
});
```

- [ ] **Step 3：studyroom.wxml**

```xml
<view class="container">
  <view class="hero">
    <view class="hero-icon">📖</view>
    <view class="hero-title">自习室</view>
    <view class="hero-desc">专注学习，记录时长</view>
  </view>
  <view class="timer-card">
    <view class="timer-label">本次专注</view>
    <view class="timer-value">{{elapsedStr}}</view>
    <button class="timer-btn {{running ? 'stop' : 'start'}}" bindtap="toggle">{{running ? '结束专注' : '开始专注'}}</button>
  </view>
  <view class="today-card">
    <text class="today-label">今日累计</text>
    <text class="today-value">{{todayMinutes}} 分钟</text>
  </view>
</view>
```

- [ ] **Step 4：studyroom.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding-bottom: 60rpx; }
.hero { background: linear-gradient(135deg, #2ECC71, #58D68D); padding: 50rpx 30rpx; text-align: center; color: #fff; }
.hero-icon { font-size: 100rpx; }
.hero-title { font-size: 36rpx; font-weight: bold; margin-top: 16rpx; }
.hero-desc { font-size: 26rpx; opacity: 0.9; margin-top: 10rpx; }
.timer-card { margin: 30rpx; background: #fff; border-radius: 24rpx; padding: 60rpx 40rpx; text-align: center; }
.timer-label { font-size: 26rpx; color: #999; margin-bottom: 20rpx; }
.timer-value { font-size: 96rpx; font-weight: bold; color: #2ECC71; font-family: monospace; margin-bottom: 40rpx; }
.timer-btn { color: #fff; border-radius: 50rpx; font-size: 30rpx; padding: 20rpx 0; }
.timer-btn.start { background: #2ECC71; }
.timer-btn.stop { background: #E74C3C; }
.today-card { margin: 0 30rpx; background: #fff; border-radius: 16rpx; padding: 30rpx; display: flex; justify-content: space-between; align-items: center; }
.today-label { font-size: 28rpx; color: #666; }
.today-value { font-size: 32rpx; font-weight: bold; color: #2ECC71; }
```

- [ ] **Step 5：index.js 的 goStudyRoom**

替换为：
```javascript
  goStudyRoom() {
    wx.navigateTo({ url: '/pages/studyroom/studyroom' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/studyroom wechat-miniapp/pages/index/index.js
git commit -m "feat: add studyroom page with focus timer"
```

---

## Task 3.7：通知中心 (notifications)

**Files:**
- Create: `wechat-miniapp/pages/notifications/notifications.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：notifications.json**

```json
{"navigationBarTitleText":"通知中心","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：notifications.js**

```javascript
Page({
  data: {
    notifications: [
      { id: 1, type: 'system', title: '欢迎使用 BRO', content: '一起开启刷题之旅吧！', time: '刚刚', read: false },
      { id: 2, type: 'tip', title: '小贴士', content: '每日签到可领取积分，连续签到奖励更多', time: '今天', read: false }
    ]
  },

  markRead(e) {
    const id = e.currentTarget.dataset.id;
    const notifications = this.data.notifications.map(n => n.id === id ? { ...n, read: true } : n);
    this.setData({ notifications });
  },

  clearAll() {
    wx.showModal({
      title: '提示', content: '清空所有通知？',
      success: (res) => {
        if (res.confirm) {
          this.setData({ notifications: [] });
          wx.showToast({ title: '已清空', icon: 'success' });
        }
      }
    });
  }
});
```

- [ ] **Step 3：notifications.wxml**

```xml
<view class="container">
  <view wx:if="{{notifications.length > 0}}">
    <view class="actions-bar"><text class="clear-btn" bindtap="clearAll">清空</text></view>
    <view wx:for="{{notifications}}" wx:key="id" class="notif-item {{item.read ? 'read' : ''}}" data-id="{{item.id}}" bindtap="markRead">
      <view class="notif-icon">{{item.type === 'system' ? '🔔' : '💡'}}</view>
      <view class="notif-body">
        <view class="notif-title">{{item.title}}</view>
        <view class="notif-content">{{item.content}}</view>
        <view class="notif-time">{{item.time}}</view>
      </view>
      <view wx:if="{{!item.read}}" class="dot"></view>
    </view>
  </view>
  <view wx:else class="empty">
    <view class="empty-icon">🔕</view>
    <text>暂无新通知</text>
  </view>
</view>
```

- [ ] **Step 4：notifications.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; }
.actions-bar { padding: 16rpx 30rpx; background: #fff; text-align: right; border-bottom: 2rpx solid #f0f0f0; }
.clear-btn { font-size: 26rpx; color: #4A90D9; }
.notif-item { display: flex; gap: 20rpx; padding: 24rpx 30rpx; background: #fff; border-bottom: 2rpx solid #f5f5f5; position: relative; }
.notif-item.read { opacity: 0.6; }
.notif-icon { width: 70rpx; height: 70rpx; border-radius: 50%; background: #EBF4FF; display: flex; align-items: center; justify-content: center; font-size: 36rpx; flex-shrink: 0; }
.notif-body { flex: 1; display: flex; flex-direction: column; gap: 8rpx; }
.notif-title { font-size: 30rpx; font-weight: bold; color: #333; }
.notif-content { font-size: 26rpx; color: #666; line-height: 1.5; }
.notif-time { font-size: 22rpx; color: #999; }
.dot { width: 16rpx; height: 16rpx; border-radius: 50%; background: #E74C3C; position: absolute; top: 30rpx; right: 30rpx; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 200rpx 0; gap: 20rpx; color: #999; }
.empty-icon { font-size: 120rpx; }
```

- [ ] **Step 5：index.js 的 goNotifications**

替换为：
```javascript
  goNotifications() {
    wx.navigateTo({ url: '/pages/notifications/notifications' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/notifications wechat-miniapp/pages/index/index.js
git commit -m "feat: add notifications page"
```

---

## Task 3.8：难度偏好 (difficulty)

**Files:**
- Create: `wechat-miniapp/pages/difficulty/difficulty.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：difficulty.json**

```json
{"navigationBarTitleText":"难度偏好","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：difficulty.js**

```javascript
const STORAGE_KEY = 'difficulty_pref';

Page({
  data: {
    selected: 3,
    options: [
      { value: 1, label: '入门', desc: '基础题为主，适合刚开始备考' },
      { value: 2, label: '简单', desc: '难度较低，巩固基础知识' },
      { value: 3, label: '中等', desc: '推荐难度，覆盖常见考点' },
      { value: 4, label: '困难', desc: '挑战难题，冲刺高分' },
      { value: 5, label: '专家', desc: '竞赛级题目，挑战极限' }
    ]
  },

  onLoad() {
    const stored = wx.getStorageSync(STORAGE_KEY);
    if (stored) this.setData({ selected: stored });
  },

  select(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ selected: value });
    wx.setStorageSync(STORAGE_KEY, value);
    wx.showToast({ title: '已保存', icon: 'success' });
  }
});
```

- [ ] **Step 3：difficulty.wxml**

```xml
<view class="container">
  <view class="hint">选择你偏好的题目难度，将影响随机题、每日挑战等推送</view>
  <view class="option-list">
    <view wx:for="{{options}}" wx:key="value" class="option {{selected === item.value ? 'selected' : ''}}" data-value="{{item.value}}" bindtap="select">
      <view class="option-stars">
        <text wx:for="{{[1,2,3,4,5]}}" wx:for-item="s" wx:key="*this" class="star {{s <= item.value ? 'fill' : ''}}">★</text>
      </view>
      <view class="option-meta">
        <view class="option-label">{{item.label}}</view>
        <view class="option-desc">{{item.desc}}</view>
      </view>
      <view wx:if="{{selected === item.value}}" class="check">✓</view>
    </view>
  </view>
</view>
```

- [ ] **Step 4：difficulty.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding: 30rpx; }
.hint { font-size: 26rpx; color: #999; padding: 20rpx 0 30rpx; line-height: 1.6; }
.option-list { display: flex; flex-direction: column; gap: 16rpx; }
.option { display: flex; align-items: center; gap: 20rpx; padding: 24rpx; background: #fff; border-radius: 16rpx; border: 4rpx solid transparent; transition: all 0.2s; }
.option.selected { border-color: #4A90D9; background: #EBF4FF; }
.option-stars { display: flex; gap: 4rpx; }
.star { font-size: 28rpx; color: #ddd; }
.star.fill { color: #FFD700; }
.option-meta { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
.option-label { font-size: 30rpx; font-weight: bold; color: #333; }
.option-desc { font-size: 24rpx; color: #999; }
.check { font-size: 40rpx; color: #4A90D9; font-weight: bold; }
```

- [ ] **Step 5：index.js 的 goDifficulty**

替换为：
```javascript
  goDifficulty() {
    wx.navigateTo({ url: '/pages/difficulty/difficulty' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/difficulty wechat-miniapp/pages/index/index.js
git commit -m "feat: add difficulty preference page"
```

---

## Task 3.9：系统设置 (settings)

**Files:**
- Create: `wechat-miniapp/pages/settings/settings.{js,wxml,wxss,json}`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：settings.json**

```json
{"navigationBarTitleText":"系统设置","navigationBarBackgroundColor":"#4A90D9","navigationBarTextStyle":"white"}
```

- [ ] **Step 2：settings.js**

```javascript
const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');

Page({
  data: { isLoggedIn: false, version: '1.0.0' },

  onShow() {
    this.setData({ isLoggedIn: auth.isLoggedIn() });
  },

  clearCache() {
    wx.showModal({
      title: '清理缓存', content: '将删除本地答题记录和收藏，确定吗？',
      success: (res) => {
        if (res.confirm) {
          storage.clearAll();
          wx.showToast({ title: '已清理', icon: 'success' });
        }
      }
    });
  },

  logout() {
    wx.showModal({
      title: '退出登录', content: '确定退出当前账号？',
      success: (res) => {
        if (res.confirm) {
          auth.logout();
          this.setData({ isLoggedIn: false });
          wx.showToast({ title: '已退出', icon: 'success' });
        }
      }
    });
  },

  about() {
    wx.showModal({
      title: '关于 BRO',
      content: `版本：${this.data.version}\nBRO 是一款专为高考/DSE 设计的刷题学习应用。`,
      showCancel: false
    });
  },

  contact() {
    wx.setClipboardData({
      data: 'support@broapp.com',
      success: () => wx.showToast({ title: '邮箱已复制', icon: 'success' })
    });
  }
});
```

- [ ] **Step 3：settings.wxml**

```xml
<view class="container">
  <view class="section">
    <view class="item" bindtap="clearCache">
      <text class="item-label">清理缓存</text>
      <text class="item-arrow">></text>
    </view>
    <view class="item" bindtap="about">
      <text class="item-label">关于 BRO</text>
      <text class="item-sub">v{{version}}</text>
      <text class="item-arrow">></text>
    </view>
    <view class="item" bindtap="contact">
      <text class="item-label">联系我们</text>
      <text class="item-arrow">></text>
    </view>
  </view>
  <view wx:if="{{isLoggedIn}}" class="section">
    <view class="item danger" bindtap="logout">
      <text class="item-label">退出登录</text>
    </view>
  </view>
</view>
```

- [ ] **Step 4：settings.wxss**

```css
.container { background: #f5f5f5; min-height: 100vh; padding: 20rpx 0; }
.section { background: #fff; margin-bottom: 20rpx; }
.item { display: flex; align-items: center; padding: 30rpx; border-bottom: 2rpx solid #f5f5f5; }
.item:last-child { border-bottom: none; }
.item-label { flex: 1; font-size: 30rpx; color: #333; }
.item-sub { font-size: 26rpx; color: #999; margin-right: 16rpx; }
.item-arrow { font-size: 28rpx; color: #ccc; }
.item.danger { justify-content: center; }
.item.danger .item-label { flex: none; color: #E74C3C; font-weight: bold; }
```

- [ ] **Step 5：index.js 的 goSettings**

替换为：
```javascript
  goSettings() {
    wx.navigateTo({ url: '/pages/settings/settings' });
  },
```

- [ ] **Step 6：Commit**

```powershell
git add wechat-miniapp/pages/settings wechat-miniapp/pages/index/index.js
git commit -m "feat: add settings page"
```

---

# Phase 4：签到/积分接入后端持久化

## Task 4.1：扩展 User 模型加 points 字段，新增 DailyCheckIn 模型

**Files:**
- Modify: `backend/models.py`
- Create: `backend/migrate_add_points.py`（一次性迁移脚本）

- [ ] **Step 1：修改 models.py**

把 `backend/models.py` 完整覆写为（在 `User` 加 `points`、文件末尾加 `DailyCheckIn`）：
```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

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
    points = db.Column(db.Integer, default=0)
    exp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    region = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    grade = db.Column(db.String(20))
    syllabus = db.Column(db.String(100))
    knowledge_point = db.Column(db.String(200))
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

class ImportBatch(db.Model):
    __tablename__ = 'import_batches'
    id = db.Column(db.Integer, primary_key=True)
    source_type = db.Column(db.String(20), nullable=False)
    source_file = db.Column(db.String(500))
    source_url = db.Column(db.String(500))
    status = db.Column(db.String(20), default='pending')
    total_questions = db.Column(db.Integer, default=0)
    parsed_questions = db.Column(db.Integer, default=0)
    approved_questions = db.Column(db.Integer, default=0)
    exam_type = db.Column(db.String(20))
    subject = db.Column(db.String(50))
    grade = db.Column(db.String(20))
    knowledge_point = db.Column(db.String(200))
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

class ParsedQuestion(db.Model):
    __tablename__ = 'parsed_questions'
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('import_batches.id'))
    raw_content = db.Column(db.Text)
    content = db.Column(db.Text)
    options = db.Column(db.Text)
    answer = db.Column(db.Text)
    explanation = db.Column(db.Text)
    images = db.Column(db.Text)
    formulas = db.Column(db.Text)
    exam_type = db.Column(db.String(20))
    subject = db.Column(db.String(50))
    grade = db.Column(db.String(20))
    knowledge_point = db.Column(db.String(200))
    type = db.Column(db.String(20))
    difficulty = db.Column(db.Integer, default=3)
    status = db.Column(db.String(20), default='pending')
    confidence = db.Column(db.Float)
    review_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class QuestionImage(db.Model):
    __tablename__ = 'question_images'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer)
    image_type = db.Column(db.String(20))
    original_url = db.Column(db.String(500))
    processed_url = db.Column(db.String(500))
    ocr_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DailyCheckIn(db.Model):
    __tablename__ = 'daily_checkins'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    check_date = db.Column(db.Date, nullable=False, default=date.today)
    points_awarded = db.Column(db.Integer, default=10)
    exp_awarded = db.Column(db.Integer, default=5)
    streak = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'check_date', name='uq_user_date'),)
```

- [ ] **Step 2：写迁移脚本（针对已存在的 bro.db）**

创建 `backend/migrate_add_points.py`：
```python
"""一次性脚本：给已存在的 SQLite 数据库添加新字段和新表。
首次部署时如果是空数据库，db.create_all() 会自动建表，不需要本脚本。
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'bro.db')

def column_exists(cur, table, column):
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def table_exists(cur, table):
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None

def main():
    if not os.path.exists(DB_PATH):
        print(f"DB not found at {DB_PATH}, skip migration; db.create_all() will handle a fresh DB.")
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for col, default in [('points', 0), ('exp', 0), ('level', 1)]:
        if not column_exists(cur, 'users', col):
            cur.execute(f"ALTER TABLE users ADD COLUMN {col} INTEGER DEFAULT {default}")
            print(f"Added users.{col}")

    if not table_exists(cur, 'daily_checkins'):
        cur.execute('''
            CREATE TABLE daily_checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                check_date DATE NOT NULL,
                points_awarded INTEGER DEFAULT 10,
                exp_awarded INTEGER DEFAULT 5,
                streak INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, check_date),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        print("Created daily_checkins")

    conn.commit()
    conn.close()
    print("Migration done.")

if __name__ == '__main__':
    main()
```

- [ ] **Step 3：运行迁移**

工作目录 `backend`：
```powershell
python migrate_add_points.py
```
Expected: 输出 `Added users.points` / `Created daily_checkins` 或 `Migration done.`

- [ ] **Step 4：Commit**

```powershell
git add backend/models.py backend/migrate_add_points.py
git commit -m "feat: add points/exp/level to User model, add DailyCheckIn model + migration"
```

---

## Task 4.2：签到 API + profile 返回 points

**Files:**
- Create: `backend/routes/checkin.py`
- Modify: `backend/routes/__init__.py`
- Modify: `backend/routes/users.py`
- Create: `backend/tests/test_checkin.py`

- [ ] **Step 1：注册 checkin_bp**

把 `backend/routes/__init__.py` 完整覆写为：
```python
from flask import Blueprint
import importlib

questions_bp = Blueprint('questions', __name__)
users_bp = Blueprint('users', __name__)
shares_bp = Blueprint('shares', __name__)
progress_bp = Blueprint('progress', __name__)
sync_bp = Blueprint('sync', __name__)
import_bp = Blueprint('import', __name__)
leaderboard_bp = Blueprint('leaderboard', __name__)
checkin_bp = Blueprint('checkin', __name__)

def register_blueprints(app):
    from . import questions, shares, sync, users, progress, leaderboard, checkin
    importlib.import_module('.import', 'routes')
    app.register_blueprint(questions_bp, url_prefix='/api/questions')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(shares_bp, url_prefix='/api/shares')
    app.register_blueprint(progress_bp, url_prefix='/api/progress')
    app.register_blueprint(sync_bp, url_prefix='/api/sync')
    app.register_blueprint(import_bp, url_prefix='/api/import')
    app.register_blueprint(leaderboard_bp, url_prefix='/api/leaderboard')
    app.register_blueprint(checkin_bp, url_prefix='/api/checkin')
```

- [ ] **Step 2：写 checkin.py**

创建 `backend/routes/checkin.py`：
```python
from datetime import date, timedelta
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, DailyCheckIn
from . import checkin_bp


@checkin_bp.route('/today', methods=['GET'])
@jwt_required()
def today_status():
    user_id = int(get_jwt_identity())
    today = date.today()
    record = DailyCheckIn.query.filter_by(user_id=user_id, check_date=today).first()
    user = User.query.get(user_id)
    return jsonify({
        'already_checked': record is not None,
        'today': today.isoformat(),
        'points': user.points if user else 0,
        'streak': record.streak if record else 0
    })


@checkin_bp.route('', methods=['POST'])
@jwt_required()
def do_checkin():
    user_id = int(get_jwt_identity())
    today = date.today()

    existing = DailyCheckIn.query.filter_by(user_id=user_id, check_date=today).first()
    if existing:
        user = User.query.get(user_id)
        return jsonify({
            'success': False,
            'error': 'already_checked',
            'points': user.points,
            'streak': existing.streak
        }), 409

    yesterday = today - timedelta(days=1)
    last = DailyCheckIn.query.filter_by(user_id=user_id, check_date=yesterday).first()
    streak = (last.streak + 1) if last else 1

    points_award = 10 + min(streak, 7) * 2
    exp_award = 5 + min(streak, 7)

    record = DailyCheckIn(
        user_id=user_id, check_date=today,
        points_awarded=points_award, exp_awarded=exp_award, streak=streak
    )
    db.session.add(record)

    user = User.query.get(user_id)
    user.points = (user.points or 0) + points_award
    user.exp = (user.exp or 0) + exp_award
    while user.exp >= 100:
        user.exp -= 100
        user.level += 1

    db.session.commit()
    return jsonify({
        'success': True,
        'points_awarded': points_award,
        'exp_awarded': exp_award,
        'streak': streak,
        'total_points': user.points,
        'level': user.level,
        'exp': user.exp
    })


@checkin_bp.route('/history', methods=['GET'])
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    records = DailyCheckIn.query.filter_by(user_id=user_id) \
        .order_by(DailyCheckIn.check_date.desc()).limit(30).all()
    return jsonify({
        'records': [{
            'date': r.check_date.isoformat(),
            'points': r.points_awarded,
            'exp': r.exp_awarded,
            'streak': r.streak
        } for r in records]
    })
```

- [ ] **Step 3：修改 users.py 让 profile 返回 points/exp/level**

把 `backend/routes/users.py` 中 `get_profile` 函数替换为：
```python
@users_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)

    return jsonify({
        'id': user.id,
        'nickname': user.nickname,
        'avatar': user.avatar,
        'region': user.region,
        'member_type': user.member_type,
        'gold': user.gold,
        'points': user.points or 0,
        'exp': user.exp or 0,
        'level': user.level or 1,
        'created_at': user.created_at.isoformat()
    })
```

- [ ] **Step 4：写 test_checkin.py**

创建 `backend/tests/test_checkin.py`：
```python
def test_today_status_default(client, auth_headers):
    resp = client.get('/api/checkin/today', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['already_checked'] is False
    assert data['points'] == 0


def test_first_checkin_succeeds(client, auth_headers):
    resp = client.post('/api/checkin', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] is True
    assert data['streak'] == 1
    assert data['points_awarded'] >= 10
    assert data['total_points'] >= 10


def test_double_checkin_returns_409(client, auth_headers):
    client.post('/api/checkin', headers=auth_headers)
    resp = client.post('/api/checkin', headers=auth_headers)
    assert resp.status_code == 409
    assert resp.get_json()['error'] == 'already_checked'


def test_profile_returns_points_after_checkin(client, auth_headers):
    client.post('/api/checkin', headers=auth_headers)
    resp = client.get('/api/users/profile', headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['points'] >= 10
    assert 'level' in data
```

- [ ] **Step 5：运行测试**

工作目录 `backend`：
```powershell
pytest tests/test_checkin.py -v
```
Expected: `4 passed`

- [ ] **Step 6：手动 curl 验证**

```powershell
$body = '{"code":"smoke_test_user"}'
$tok = (curl.exe -s -X POST -H "Content-Type: application/json" -d $body http://127.0.0.1:5001/api/users/wx-login | ConvertFrom-Json).token
curl.exe -s -H "Authorization: Bearer $tok" http://127.0.0.1:5001/api/checkin/today
curl.exe -s -X POST -H "Authorization: Bearer $tok" http://127.0.0.1:5001/api/checkin
```
Expected: 第一次返回 `{"success":true,"streak":1,...}`；再次执行返回 409。

- [ ] **Step 7：Commit**

```powershell
git add backend/routes/checkin.py backend/routes/__init__.py backend/routes/users.py backend/tests/test_checkin.py
git commit -m "feat: add checkin API + tests, expose points/level in profile"
```

---

## Task 4.3：小程序 api.js 加签到方法 + index.js 接入

**Files:**
- Modify: `wechat-miniapp/utils/api.js`
- Modify: `wechat-miniapp/pages/index/index.js`

- [ ] **Step 1：api.js 加签到方法**

把 `wechat-miniapp/utils/api.js` 的 `module.exports` 完整覆写为：
```javascript
module.exports = {
  request,
  getQuestions: (params) => request('/questions', 'GET', params),
  getQuestion: (id) => request(`/questions/${id}`),
  getRandomQuestion: (params) => request('/questions/random', 'GET', params),
  submitAnswer: (data) => request('/practice/submit', 'POST', data),
  submitProgress: (data) => request('/progress', 'POST', data),
  getProgress: (params) => request('/progress', 'GET', params),
  getWrongQuestions: (params) => request('/progress/wrong', 'GET', params),
  getStats: () => request('/progress/stats'),
  getProfile: () => request('/users/profile'),
  updateProfile: (data) => request('/users/profile', 'PUT', data),
  getMyQuestions: (params) => request('/import/my-questions', 'GET', params),
  getLeaderboard: (params) => request('/leaderboard', 'GET', params),
  getCheckinStatus: () => request('/checkin/today'),
  doCheckin: () => request('/checkin', 'POST'),
  getCheckinHistory: () => request('/checkin/history')
};
```

- [ ] **Step 2：修改 index.js 的 loadUserData 接入后端 profile**

打开 `wechat-miniapp/pages/index/index.js`，把 `loadUserData()` 函数替换为：
```javascript
  loadUserData() {
    const userInfo = auth.getUserInfo();
    const isLoggedIn = auth.isLoggedIn();

    this.setData({
      userInfo,
      isLoggedIn,
      userLevel: isLoggedIn ? 1 : 1,
      userExp: 0,
      maxExp: 100,
      userPoints: 0,
      isMember: isLoggedIn && userInfo && userInfo.member_type === 'premium'
    });

    if (!isLoggedIn) return;

    const api = require('../../utils/api.js');
    api.getProfile()
      .then(profile => {
        this.setData({
          userLevel: profile.level || 1,
          userExp: profile.exp || 0,
          userPoints: profile.points || 0,
          isMember: profile.member_type === 'premium'
        });
      })
      .catch(() => {});

    api.getCheckinStatus()
      .then(s => this.setData({ hasSignedIn: s.already_checked }))
      .catch(() => {});
  },
```

- [ ] **Step 3：修改 index.js 的 signIn 调用后端**

把 `signIn()` 函数替换为：
```javascript
  signIn() {
    if (this.data.hasSignedIn) {
      wx.showToast({ title: '今日已签到', icon: 'none' });
      return;
    }
    if (!auth.isLoggedIn()) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    const api = require('../../utils/api.js');
    api.doCheckin()
      .then(res => {
        this.setData({
          userPoints: res.total_points,
          userExp: res.exp,
          userLevel: res.level,
          hasSignedIn: true
        });
        wx.showToast({ title: `签到+${res.points_awarded}积分`, icon: 'success' });
      })
      .catch(err => {
        if (err && err.error === 'already_checked') {
          this.setData({ hasSignedIn: true });
          wx.showToast({ title: '今日已签到', icon: 'none' });
        } else {
          wx.showToast({ title: '签到失败', icon: 'none' });
        }
      });
  },
```

- [ ] **Step 4：手动验证全流程**

1. 重启 backend
2. 微信开发者工具刷新小程序，确认 console 输出 `Auto-login success`
3. 打开左侧个人面板，点签到按钮
4. Expected: toast 显示 `签到+10积分`；积分数从 0 变为 10；按钮变为"已签到"
5. 再次点签到 → toast `今日已签到`
6. 杀掉小程序重新进入，积分应该仍为 10（说明后端持久化）

- [ ] **Step 5：Commit**

```powershell
git add wechat-miniapp/utils/api.js wechat-miniapp/pages/index/index.js
git commit -m "feat: wire signIn and points to backend checkin API"
```

---

# Phase 5：最终验收

## Task 5.1：跑全部后端测试

- [ ] **Step 1：运行 pytest 全集**

工作目录 `backend`：
```powershell
pytest -v
```
Expected: 全部 PASS（health 1 + leaderboard 2 + checkin 4 = 7 个）

## Task 5.2：小程序端到端冒烟测试

逐项点击验证（每项都应能打开页面或显示空状态而非报错）：

- [ ] 主页 6 个网格按钮：题库、每日挑战、我要出题、错题本、排行榜、理词通
- [ ] 主页底部 3 个按钮：广场、做题、自习室
- [ ] 顶部头像 → 左侧个人面板 → 6 个菜单项（我的战绩/我的题目/我的书包/我的同学/邀请同学/我的会员）+ 积分商城 + 签到
- [ ] 顶部菜单 → 右侧面板 → 通知、难度偏好、扫一扫、语言切换、系统设置

## Task 5.3：清理 + Push

- [ ] **Step 1：git 状态确认**

```powershell
git status
```
Expected: nothing to commit

- [ ] **Step 2：git log 检查提交历史**

```powershell
git log --oneline -30
```
Expected: 看到清晰的 feat/test/chore commit 序列

- [ ] **Step 3：推送到远端**

```powershell
git push origin main
```

---

## 自检清单

- [x] Phase 1：本地 backend 启动 + pytest 骨架
- [x] Phase 2：6 个个人中心子页面（stats/myquestions/mybag/classmates/invite/membership）
- [x] Phase 3：9 个主页按钮对应页面（daily-challenge/leaderboard/points-shop/licitong/square/studyroom/notifications/difficulty/settings）
- [x] Phase 4：签到/积分后端持久化（User+DailyCheckIn 模型 + checkin API + 小程序接入）
- [x] Phase 5：验收
- [x] 无 TBD/TODO 占位符
- [x] 所有 API 方法签名一致（getMyQuestions/getLeaderboard/doCheckin/getCheckinStatus/getCheckinHistory 全在 api.js 末尾追加）
- [x] 每个任务都有 commit
- [x] 关键后端任务有 pytest 测试

---

**Plan complete.** 保存至 `docs/superpowers/plans/2026-06-10-bro-app-feature-buildout.md`
