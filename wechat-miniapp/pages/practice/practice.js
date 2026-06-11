const api = require('../../utils/api.js');
const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');

Page({
  data: { question: null, userAnswer: '', submitted: false, isCorrect: null, loading: true, isFav: false },

  onLoad(options) {
    this.isChallenge = options.challenge === '1';
    this.loadQuestion(options.id);
  },

  loadQuestion(id) {
    this.setData({ loading: true });
    api.getQuestion(id).then(res => {
      this.setData({
        question: res,
        loading: false,
        userAnswer: '',
        submitted: false,
        isFav: storage.isFavorited(res.id)
      });
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
    storage.saveProgress({
      question_id: question.id, user_answer: userAnswer, is_correct: isCorrect,
      answered_at: Date.now(), subject: question.subject
    });
    if (auth.isLoggedIn()) {
      api.submitProgress({
        question_id: question.id, user_answer: userAnswer,
        is_correct: isCorrect, is_challenge: !!this.isChallenge, time_spent: 0
      }).then(res => {
        if (res && res.points_awarded > 0) {
          wx.showToast({ title: `+${res.points_awarded} 积分`, icon: 'success' });
        }
      }).catch(() => {});
    }
    this.setData({ submitted: true, isCorrect });
  },

  toggleFav() {
    const q = this.data.question;
    if (!q) return;
    if (this.data.isFav) {
      storage.removeFavorite(q.id);
      this.setData({ isFav: false });
      wx.showToast({ title: '已移出书包', icon: 'success' });
    } else {
      storage.addFavorite({ id: q.id, content: q.content, subject: q.subject, difficulty: q.difficulty });
      this.setData({ isFav: true });
      wx.showToast({ title: '已加入书包', icon: 'success' });
    }
  },

  nextQuestion() {
    const app = getApp();
    api.getRandomQuestion({ region: app.globalData.region })
      .then(res => { wx.redirectTo({ url: `/pages/practice/practice?id=${res.id}` }); });
  }
});
