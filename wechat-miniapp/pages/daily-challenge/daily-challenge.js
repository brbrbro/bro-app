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
