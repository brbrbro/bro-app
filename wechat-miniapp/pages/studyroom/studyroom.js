const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');

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

    // Override with cloud total if logged in
    if (auth.isLoggedIn()) {
      api.getStudyToday()
        .then(r => this.setData({ todayMinutes: r.today_minutes }))
        .catch(() => {});
    }
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

    if (auth.isLoggedIn() && seconds > 0) {
      api.submitStudySession(seconds)
        .then(() => api.getStudyToday())
        .then(r => this.setData({ todayMinutes: r.today_minutes }))
        .catch(() => {});
    }
  },

  format(sec) {
    const h = String(Math.floor(sec / 3600)).padStart(2, '0');
    const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
    const s = String(sec % 60).padStart(2, '0');
    return `${h}:${m}:${s}`;
  }
});
