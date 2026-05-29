# Connect Mini-Program to Backend APIs - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect the WeChat mini-program to the deployed Flask backend APIs with JWT authentication, local-first data strategy, and optional cloud sync.

**Architecture:** Auto-login on app launch to get JWT token, update API client with auth headers, integrate key pages with backend endpoints while maintaining local storage as primary data source.

**Tech Stack:** WeChat Mini-Program (WXML/WXSS/JS) / Flask Backend / JWT

---

## File Structure

```
wechat-miniapp/
├── app.js                      修改：添加 auto-login 逻辑
├── utils/
│   ├── auth.js                 新增：登录/登出/Token 管理
│   ├── api.js                  修改：添加 auth header + 新 API 方法
│   ├── storage.js              已存在（无需修改）
│   └── sync.js                 修改：对接真实 API
├── pages/
│   ├── practice/practice.js    修改：提交答案到云端
│   ├── profile/profile.js      修改：获取云端统计
│   ├── wrongbook/wrongbook.js  修改：合并云端错题
│   └── sync/sync.js            修改：对接真实同步 API
```

---

## Task 1: Create Auth Module

**Files:**
- Create: `wechat-miniapp/utils/auth.js`

**Context:**
- Backend login endpoint: POST `http://106.53.188.248:5001/api/users/wx-login`
- Request body: `{code: string}` (WeChat login code)
- Response: `{success: true, token: string, user: {...}}`
- Backend validates JWT from `Authorization: Bearer <token>` header

- [ ] **Step 1: Create auth.js with login function**

```javascript
const app = getApp();

const AUTH_KEY = 'jwt_token';
const USER_KEY = 'user_info';

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        if (res.code) {
          wx.request({
            url: app.globalData.apiBase + '/users/wx-login',
            method: 'POST',
            data: { code: res.code },
            header: { 'Content-Type': 'application/json' },
            success: (loginRes) => {
              if (loginRes.statusCode === 200 && loginRes.data.success) {
                const token = loginRes.data.token;
                const user = loginRes.data.user;
                wx.setStorageSync(AUTH_KEY, token);
                wx.setStorageSync(USER_KEY, user);
                app.globalData.token = token;
                app.globalData.userInfo = user;
                resolve({ success: true, token, user });
              } else {
                reject(new Error(loginRes.data.error || 'Login failed'));
              }
            },
            fail: reject
          });
        } else {
          reject(new Error('Failed to get WeChat login code'));
        }
      },
      fail: reject
    });
  });
}

function getToken() {
  return wx.getStorageSync(AUTH_KEY) || app.globalData.token;
}

function getUserInfo() {
  return wx.getStorageSync(USER_KEY) || app.globalData.userInfo;
}

function isLoggedIn() {
  return !!getToken();
}

function logout() {
  wx.removeStorageSync(AUTH_KEY);
  wx.removeStorageSync(USER_KEY);
  app.globalData.token = null;
  app.globalData.userInfo = null;
}

module.exports = {
  login,
  getToken,
  getUserInfo,
  isLoggedIn,
  logout
};
```

- [ ] **Step 2: Update app.js to auto-login on launch**

Modify `wechat-miniapp/app.js`:

```javascript
const auth = require('./utils/auth.js');

App({
  globalData: {
    userInfo: null,
    token: null,
    region: 'mainland',
    apiBase: 'http://106.53.188.248:5001/api'
  },
  onLaunch() {
    // Try auto-login
    auth.login().then(() => {
      console.log('Auto-login success');
    }).catch((err) => {
      console.log('Auto-login failed:', err);
    });
  }
});
```

---

## Task 2: Update API Client

**Files:**
- Modify: `wechat-miniapp/utils/api.js`

**Context:**
- Current api.js makes simple requests without auth
- Need to add `Authorization: Bearer <token>` header to all requests
- Add new methods for progress tracking endpoints

- [ ] **Step 1: Update request function to include auth header**

```javascript
const app = getApp();
const auth = require('./auth.js');

function request(url, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const headers = { 'Content-Type': 'application/json' };
    const token = auth.getToken();
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    
    wx.request({
      url: app.globalData.apiBase + url,
      method,
      data,
      header: headers,
      success: (res) => {
        if (res.statusCode === 200 || res.statusCode === 201) resolve(res.data);
        else reject(res.data);
      },
      fail: reject
    });
  });
}
```

- [ ] **Step 2: Add new API methods for progress tracking**

Add to module.exports in api.js:

```javascript
module.exports = {
  request,
  // Existing methods
  getQuestions: (params) => request('/questions', 'GET', params),
  getQuestion: (id) => request(`/questions/${id}`),
  getRandomQuestion: (params) => request('/questions/random', 'GET', params),
  submitAnswer: (data) => request('/practice/submit', 'POST', data),
  
  // New progress methods
  submitProgress: (data) => request('/progress', 'POST', data),
  getProgress: (params) => request('/progress', 'GET', params),
  getWrongQuestions: (params) => request('/progress/wrong', 'GET', params),
  getStats: () => request('/progress/stats'),
  
  // User methods
  getProfile: () => request('/users/profile'),
  updateProfile: (data) => request('/users/profile', 'PUT', data)
};
```

---

## Task 3: Connect Practice Page

**Files:**
- Modify: `wechat-miniapp/pages/practice/practice.js`

**Context:**
- Currently saves answer only to local storage
- Should also submit to backend if user is logged in
- Must handle offline gracefully (don't block user if API fails)

- [ ] **Step 1: Update submitAnswer to submit to backend**

Modify `submitAnswer()` function in practice.js:

```javascript
const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');

submitAnswer() {
  const { question, userAnswer } = this.data;
  if (!userAnswer) { 
    wx.showToast({ title: '请选择答案', icon: 'none' }); 
    return; 
  }
  const isCorrect = userAnswer === question.answer;
  
  // Save locally first
  storage.saveProgress({ 
    question_id: question.id, 
    user_answer: userAnswer, 
    is_correct: isCorrect, 
    answered_at: Date.now() 
  });
  
  // Submit to cloud if logged in
  if (auth.isLoggedIn()) {
    api.submitProgress({
      question_id: question.id,
      user_answer: userAnswer,
      is_correct: isCorrect,
      time_spent: 0  // TODO: track actual time
    }).then(() => {
      console.log('Progress synced to cloud');
    }).catch((err) => {
      console.error('Failed to sync progress:', err);
      // Silently fail - data is already saved locally
    });
  }
  
  this.setData({ submitted: true, isCorrect });
}
```

---

## Task 4: Connect Profile Page

**Files:**
- Modify: `wechat-miniapp/pages/profile/profile.js`

**Context:**
- Currently shows only local stats
- Should fetch cloud stats if logged in for richer data
- Display user info from backend

- [ ] **Step 1: Update profile.js to fetch cloud stats**

```javascript
const storage = require('../../utils/storage.js');
const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');

Page({
  data: { 
    userInfo: null, 
    stats: { totalQuestions: 0, correctRate: 0, notesCount: 0 },
    cloudStats: null,
    isLoggedIn: false
  },

  onShow() {
    const userInfo = auth.getUserInfo();
    const progress = storage.getProgress();
    const notes = storage.getNotes();
    const total = progress.length;
    const correct = progress.filter(p => p.is_correct).length;
    
    this.setData({ 
      userInfo, 
      isLoggedIn: auth.isLoggedIn(),
      stats: { 
        totalQuestions: total, 
        correctRate: total > 0 ? Math.round(correct / total * 100) : 0, 
        notesCount: notes.length 
      } 
    });
    
    // Fetch cloud stats if logged in
    if (auth.isLoggedIn()) {
      api.getStats().then(res => {
        this.setData({ cloudStats: res });
      }).catch(err => {
        console.error('Failed to fetch stats:', err);
      });
    }
  },

  goSync() { 
    wx.navigateTo({ url: '/pages/sync/sync' }); 
  }
});
```

---

## Task 5: Connect Wrong Book Page

**Files:**
- Modify: `wechat-miniapp/pages/wrongbook/wrongbook.js`

**Context:**
- Currently loads wrong questions from local storage only
- Should merge with cloud wrong questions if logged in
- Deduplicate by question_id

- [ ] **Step 1: Update wrongbook.js to merge cloud data**

```javascript
const storage = require('../../utils/storage.js');
const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');

Page({
  data: { wrongQuestions: [], loading: false },

  onShow() { 
    this.loadWrongBook(); 
  },

  loadWrongBook() {
    this.setData({ loading: true });
    
    // Get local wrong questions
    const localWrong = storage.getProgress().filter(p => !p.is_correct);
    
    if (!auth.isLoggedIn()) {
      // Not logged in, show local only
      this.loadQuestionsFromIds(localWrong.map(p => p.question_id));
      return;
    }
    
    // Fetch cloud wrong questions and merge
    api.getWrongQuestions().then(res => {
      const cloudWrong = res.wrong_questions || [];
      
      // Merge and deduplicate by question_id
      const mergedMap = new Map();
      
      // Add local entries
      localWrong.forEach(p => {
        mergedMap.set(p.question_id, { 
          question_id: p.question_id, 
          source: 'local' 
        });
      });
      
      // Add cloud entries
      cloudWrong.forEach(q => {
        mergedMap.set(q.question_id, { 
          question_id: q.question_id, 
          source: 'cloud' 
        });
      });
      
      const mergedIds = Array.from(mergedMap.keys());
      this.loadQuestionsFromIds(mergedIds);
    }).catch(() => {
      // Fallback to local only
      this.loadQuestionsFromIds(localWrong.map(p => p.question_id));
    });
  },
  
  loadQuestionsFromIds(ids) {
    if (ids.length === 0) {
      this.setData({ wrongQuestions: [], loading: false });
      return;
    }
    
    Promise.all(ids.map(id => api.getQuestion(id)))
      .then(questions => {
        this.setData({ wrongQuestions: questions, loading: false });
      })
      .catch(() => {
        this.setData({ loading: false });
      });
  },

  goPractice(e) { 
    wx.navigateTo({ url: `/pages/practice/practice?id=${e.currentTarget.dataset.id}` }); 
  }
});
```

---

## Task 6: Update Sync Page

**Files:**
- Modify: `wechat-miniapp/pages/sync/sync.js`
- Modify: `wechat-miniapp/utils/sync.js`

**Context:**
- Current sync.js uploads/downloads but endpoints don't match backend
- Backend sync endpoints: POST/GET `/progress`
- Need to handle authentication and merge conflicts

- [ ] **Step 1: Update sync.js to use real API**

```javascript
const storage = require('./storage.js');
const api = require('./api.js');
const auth = require('./auth.js');

async function uploadToCloud() {
  if (!auth.isLoggedIn()) {
    return { success: false, error: 'not_logged_in' };
  }
  
  const progress = storage.getProgress();
  const lastSync = storage.getSyncTime();
  
  // Filter unsynced entries
  const unsynced = progress.filter(p => p.answered_at > (lastSync || 0));
  
  if (unsynced.length === 0) {
    return { success: true, message: 'No new data to sync' };
  }
  
  try {
    // Upload each progress entry
    for (const entry of unsynced) {
      await api.submitProgress({
        question_id: entry.question_id,
        user_answer: entry.user_answer,
        is_correct: entry.is_correct,
        time_spent: entry.time_spent || 0
      });
    }
    
    storage.setSyncTime(Date.now());
    return { success: true, synced_count: unsynced.length };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

async function downloadFromCloud() {
  if (!auth.isLoggedIn()) {
    return { success: false, error: 'not_logged_in' };
  }
  
  try {
    const res = await api.getProgress({ per_page: 1000 });
    const cloudProgress = res.progress || [];
    
    // Get local progress
    const localProgress = storage.getProgress();
    const localMap = new Map(localProgress.map(p => [p.question_id, p]));
    
    // Merge cloud data (cloud wins on conflict)
    cloudProgress.forEach(p => {
      localMap.set(p.question_id, {
        question_id: p.question_id,
        user_answer: p.user_answer,
        is_correct: p.is_correct,
        time_spent: p.time_spent,
        answered_at: new Date(p.answered_at).getTime()
      });
    });
    
    storage.set(storage.STORAGE_KEYS.PROGRESS, Array.from(localMap.values()));
    storage.setSyncTime(Date.now());
    
    return { success: true, downloaded_count: cloudProgress.length };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

module.exports = { uploadToCloud, downloadFromCloud };
```

- [ ] **Step 2: Update sync page UI**

Update sync.js page to show sync status:

```javascript
const sync = require('../../utils/sync.js');
const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');

Page({
  data: { 
    syncStatus: 'idle', 
    lastSyncTime: null, 
    localCount: 0,
    isLoggedIn: false
  },

  onShow() {
    const lastSyncTime = storage.getSyncTime();
    const progress = storage.getProgress();
    const notes = storage.getNotes();
    this.setData({ 
      lastSyncTime, 
      localCount: progress.length + notes.length,
      isLoggedIn: auth.isLoggedIn()
    });
  },

  async uploadToCloud() {
    if (!auth.isLoggedIn()) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    
    this.setData({ syncStatus: 'uploading' });
    const result = await sync.uploadToCloud();
    if (result.success) {
      this.setData({ syncStatus: 'success', lastSyncTime: Date.now() });
      wx.showToast({ 
        title: result.synced_count ? `同步 ${result.synced_count} 条` : '无需同步', 
        icon: 'success' 
      });
    } else {
      this.setData({ syncStatus: 'error' });
      wx.showToast({ title: result.error || '上传失败', icon: 'none' });
    }
  },

  async downloadFromCloud() {
    if (!auth.isLoggedIn()) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    
    this.setData({ syncStatus: 'downloading' });
    const result = await sync.downloadFromCloud();
    if (result.success) {
      this.setData({ syncStatus: 'success' });
      wx.showToast({ 
        title: `下载 ${result.downloaded_count} 条`, 
        icon: 'success' 
      });
    } else {
      this.setData({ syncStatus: 'error' });
      wx.showToast({ title: result.error || '下载失败', icon: 'none' });
    }
  }
});
```

---

## 部署验证

- [ ] **Step 1: Test auto-login**

Check WeChat Developer Tools console for "Auto-login success" message.

- [ ] **Step 2: Test practice submission**

Answer a question, verify:
1. Local storage updated
2. Backend receives POST /progress (check server logs)

- [ ] **Step 3: Test sync**

1. Answer a few questions
2. Go to sync page
3. Upload to cloud
4. Check backend database for UserProgress entries

- [ ] **Step 4: Test profile stats**

Verify profile page shows both local and cloud statistics.

---

**Plan complete.** Ready for subagent-driven execution.
