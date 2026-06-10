const api = require('../../utils/api.js');

Page({
  data: { shares: [], loading: true, page: 1 },

  onLoad() { this.loadShares(); },

  onReachBottom() {
    this.setData({ page: this.data.page + 1 });
    this.loadShares(true);
  },

  loadShares(append = false) {
    this.setData({ loading: true });
    api.request('/shares', 'GET', { page: this.data.page, per_page: 20 })
      .then(res => {
        const list = res.shares || [];
        const shares = append ? [...this.data.shares, ...list] : list;
        this.setData({ shares, loading: false });
      })
      .catch(() => this.setData({ loading: false }));
  }
});
