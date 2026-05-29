const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');
const api = require('../../utils/api.js');

Page({
  data: {
    userInfo: null,
    isLoggedIn: false,
    stats: { totalQuestions: 0, correctRate: 0, notesCount: 0 },
    cloudStats: null
  },

  onShow() {
    const userInfo = storage.getUserInfo();
    const progress = storage.getProgress();
    const notes = storage.getNotes();
    const total = progress.length;
    const correct = progress.filter(p => p.is_correct).length;
    const isLoggedIn = auth.isLoggedIn();

    this.setData({
      userInfo,
      isLoggedIn,
      stats: {
        totalQuestions: total,
        correctRate: total > 0 ? Math.round(correct / total * 100) : 0,
        notesCount: notes.length
      }
    });

    if (isLoggedIn) {
      api.getStats()
        .then(stats => {
          this.setData({ cloudStats: stats });
        })
        .catch(() => {
          // Silent fail - keep local stats
        });
    }
  },

  goSync() { wx.navigateTo({ url: '/pages/sync/sync' }); }
});