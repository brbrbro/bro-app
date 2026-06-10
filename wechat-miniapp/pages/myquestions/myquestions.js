const auth = require('../../utils/auth.js');
const api = require('../../utils/api.js');

Page({
  data: { isLoggedIn: false, activeTab: 'all', questions: [], loading: true },

  onShow() {
    const isLoggedIn = auth.isLoggedIn();
    this.setData({ isLoggedIn });
    if (isLoggedIn) this.loadQuestions();
    else this.setData({ loading: false });
  },

  switchTab(e) {
    this.setData({ activeTab: e.currentTarget.dataset.tab, loading: true });
    this.loadQuestions();
  },

  loadQuestions() {
    const status = this.data.activeTab === 'all' ? '' : this.data.activeTab;
    api.getMyQuestions({ status })
      .then(res => this.setData({ questions: res.questions || [], loading: false }))
      .catch(() => this.setData({ questions: [], loading: false }));
  },

  goSubmit() {
    wx.navigateTo({ url: '/pages/import/import' });
  }
});
