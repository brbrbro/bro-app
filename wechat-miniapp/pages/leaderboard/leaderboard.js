const api = require('../../utils/api.js');

Page({
  data: { metric: 'correct', ranking: [], loading: true },

  onShow() { this.loadRanking(); },

  switchMetric(e) {
    this.setData({ metric: e.currentTarget.dataset.metric, loading: true });
    this.loadRanking();
  },

  loadRanking() {
    api.getLeaderboard({ metric: this.data.metric, limit: 50 })
      .then(res => this.setData({ ranking: res.ranking || [], loading: false }))
      .catch(() => this.setData({ ranking: [], loading: false }));
  }
});
