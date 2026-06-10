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
