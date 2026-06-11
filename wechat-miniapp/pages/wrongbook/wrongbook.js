const storage = require('../../utils/storage.js');
const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');

Page({
  data: { wrongQuestions: [], loading: false },

  onShow() { this.loadWrongBook(); },

  loadWrongBook() {
    this.setData({ loading: true });
    const localIds = [...new Set(storage.getProgress().filter(p => !p.is_correct).map(p => p.question_id))];

    if (!auth.isLoggedIn()) {
      this.loadByIds(localIds);
      return;
    }

    api.getWrongQuestions({ per_page: 200 })
      .then(res => {
        const cloudIds = (res.wrong_questions || []).map(q => q.question_id);
        const mergedIds = [...new Set([...localIds, ...cloudIds])];
        this.loadByIds(mergedIds);
      })
      .catch(() => this.loadByIds(localIds));
  },

  loadByIds(ids) {
    if (ids.length === 0) {
      this.setData({ wrongQuestions: [], loading: false });
      return;
    }
    Promise.all(ids.map(id => api.getQuestion(id).catch(() => null)))
      .then(list => {
        this.setData({ wrongQuestions: list.filter(q => q !== null), loading: false });
      });
  },

  goPractice(e) {
    wx.navigateTo({ url: `/pages/practice/practice?id=${e.currentTarget.dataset.id}` });
  }
});
