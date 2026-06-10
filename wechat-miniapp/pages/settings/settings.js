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
