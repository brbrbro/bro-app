const app = getApp();
const auth = require('./auth');

function request(url, method = 'GET', data = null) {
  return new Promise((resolve, reject) => {
    const headers = { 'Content-Type': 'application/json' };
    const token = auth.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    wx.request({
      url: app.globalData.apiBase + url,
      method,
      data,
      header: headers,
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