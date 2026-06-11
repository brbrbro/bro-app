const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');

const FALLBACK = [
  { id: 1, type: 'system', title: '欢迎使用 BRO', content: '一起开启刷题之旅吧！', time: '刚刚', read: false },
  { id: 2, type: 'tip', title: '小贴士', content: '每日签到可领取积分，连续签到奖励更多', time: '今天', read: false }
];

Page({
  data: { notifications: [] },

  onShow() {
    api.getNotifications()
      .then(res => {
        const list = (res.notifications || []).map(n => ({
          id: n.id, type: n.type, title: n.title, content: n.content,
          time: (n.created_at || '').slice(0, 10), read: n.read
        }));
        this.setData({ notifications: list.length ? list : FALLBACK });
      })
      .catch(() => this.setData({ notifications: FALLBACK }));
  },

  markRead(e) {
    const id = e.currentTarget.dataset.id;
    const notifications = this.data.notifications.map(n => n.id === id ? { ...n, read: true } : n);
    this.setData({ notifications });
    if (auth.isLoggedIn()) {
      api.markNotifRead(id).catch(() => {});
    }
  },

  clearAll() {
    wx.showModal({
      title: '提示', content: '清空所有通知？',
      success: (res) => {
        if (!res.confirm) return;
        this.setData({ notifications: [] });
        if (auth.isLoggedIn()) api.markAllNotifRead().catch(() => {});
        wx.showToast({ title: '已清空', icon: 'success' });
      }
    });
  }
});
