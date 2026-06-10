const storage = require('../../utils/storage.js');

Page({
  data: { favorites: [] },
  onShow() { this.setData({ favorites: storage.getFavorites() }); },
  goPractice(e) { wx.navigateTo({ url: `/pages/practice/practice?id=${e.currentTarget.dataset.id}` }); },
  removeFav(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '提示', content: '确定从书包移除这道题？',
      success: (res) => {
        if (res.confirm) {
          storage.removeFavorite(id);
          this.setData({ favorites: storage.getFavorites() });
          wx.showToast({ title: '已移除', icon: 'success' });
        }
      }
    });
  }
});
