const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');
const api = require('../../utils/api.js');

Page({
  data: {
    isLoggedIn: false,
    totalAnswered: 0,
    correctCount: 0,
    wrongCount: 0,
    correctRate: 0,
    bySubject: [],
    loading: true
  },

  onShow() {
    this.loadStats();
  },

  loadStats() {
    const isLoggedIn = auth.isLoggedIn();
    this.setData({ isLoggedIn });
    if (isLoggedIn) {
      api.getStats()
        .then(stats => {
          this.setData({
            totalAnswered: stats.total_answered,
            correctCount: stats.correct_count,
            wrongCount: stats.wrong_count,
            correctRate: stats.correct_rate,
            loading: false
          });
        })
        .catch(() => this.loadLocalStats());
    } else {
      this.loadLocalStats();
    }
  },

  loadLocalStats() {
    const progress = storage.getProgress();
    const total = progress.length;
    const correct = progress.filter(p => p.is_correct).length;
    const subjectMap = {};
    progress.forEach(p => {
      const subj = p.subject || '未分类';
      if (!subjectMap[subj]) subjectMap[subj] = { subject: subj, total: 0, correct: 0 };
      subjectMap[subj].total += 1;
      if (p.is_correct) subjectMap[subj].correct += 1;
    });
    const bySubject = Object.values(subjectMap).map(s => ({
      subject: s.subject,
      total: s.total,
      rate: s.total > 0 ? Math.round(s.correct / s.total * 100) : 0
    }));
    this.setData({
      totalAnswered: total,
      correctCount: correct,
      wrongCount: total - correct,
      correctRate: total > 0 ? Math.round(correct / total * 100) : 0,
      bySubject,
      loading: false
    });
  }
});
