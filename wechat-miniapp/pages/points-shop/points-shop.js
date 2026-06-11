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
        if (!res.confirm) return;
        api.redeem(item.id)
          .then(r => {
            this.setData({ userPoints: r.remaining_points });
            wx.showToast({ title: '兑换成功', icon: 'success' });
          })
          .catch(err => {
            const msg = err && err.error === 'insufficient_points' ? '积分不足' : '兑换失败';
            wx.showToast({ title: msg, icon: 'none' });
          });
      }
    });
  }
});
