const api = require('../../utils/api.js');

Page({
  data: { shares: [], loading: false, page: 1 },

  onLoad() { this.loadShares(); },

  onReachBottom() { this.setData({ page: this.data.page + 1 }); this.loadShares(true); },

  loadShares(append = false) {
    this.setData({ loading: true });
    api.request('/shares', 'GET', { page: this.data.page })
      .then(res => {
        const shares = append ? [...this.data.shares, ...res.shares] : res.shares;
        this.setData({ shares, loading: false });
      });
  },

  goPost() { wx.navigateTo({ url: '/pages/share/post' }); },

  goDetail(e) { wx.navigateTo({ url: `/pages/share/detail?id=${e.currentTarget.dataset.id}` }); }
});