const api = require('../../utils/api.js');
const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');

Page({
  data: { question: null, userAnswer: '', submitted: false, isCorrect: null, loading: true },

  onLoad(options) {
    this.loadQuestion(options.id);
  },

  loadQuestion(id) {
    this.setData({ loading: true });
    api.getQuestion(id).then(res => {
      this.setData({ question: res, loading: false, userAnswer: '', submitted: false });
    });
  },

  selectOption(e) {
    if (this.data.submitted) return;
    this.setData({ userAnswer: e.currentTarget.dataset.option });
  },

  submitAnswer() {
    const { question, userAnswer } = this.data;
    if (!userAnswer) { wx.showToast({ title: '请选择答案', icon: 'none' }); return; }
    const isCorrect = userAnswer === question.answer;
    storage.saveProgress({ question_id: question.id, user_answer: userAnswer, is_correct: isCorrect, answered_at: Date.now() });
    this.setData({ submitted: true, isCorrect });
    if (auth.isLoggedIn()) {
      api.submitProgress({
        question_id: question.id,
        user_answer: userAnswer,
        is_correct: isCorrect,
        time_spent: 0
      }).catch(err => console.error('Backend sync failed:', err));
    }
  },

  addToNotes() {
    wx.navigateTo({ url: `/pages/share/post?question_id=${this.data.question.id}&type=note` });
  },

  nextQuestion() {
    const app = getApp();
    api.getRandomQuestion({ region: app.globalData.region, subject: app.globalData.subject })
      .then(res => { wx.redirectTo({ url: `/pages/practice/practice?id=${res.id}` }); });
  }
});