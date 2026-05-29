const storage = require('../../utils/storage.js');
const api = require('../../utils/api.js');
const auth = require('../../utils/auth.js');

Page({
  data: { wrongQuestions: [], loading: false },

  onShow() { this.loadWrongBook(); },

  loadWrongBook() {
    this.setData({ loading: true });
    const localProgress = storage.getProgress().filter(p => !p.is_correct);
    const localIds = localProgress.map(p => p.question_id);

    if (!auth.isLoggedIn()) {
      this.loadQuestions(localIds);
      return;
    }

    api.getWrongQuestions()
      .then(res => {
        const cloudIds = (res.wrong_questions || []).map(q => q.question_id);
        const mergedIds = [...new Set([...localIds, ...cloudIds])];
        this.loadQuestions(mergedIds);
      })
      .catch(() => {
        this.loadQuestions(localIds);
      });
  },

  loadQuestions(ids) {
    if (ids.length === 0) {
      this.setData({ wrongQuestions: [], loading: false });
      return;
    }
    Promise.all(ids.map(id => api.getQuestion(id)))
      .then(questions => {
        this.setData({ wrongQuestions: questions, loading: false });
      })
      .catch(() => {
        this.setData({ loading: false });
      });
  },

  goPractice(e) {
    wx.navigateTo({ url: `/pages/practice/practice?id=${e.currentTarget.dataset.id}` });
  }
});
