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
