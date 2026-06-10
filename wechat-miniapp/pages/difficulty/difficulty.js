const STORAGE_KEY = 'difficulty_pref';

Page({
  data: {
    selected: 3,
    options: [
      { value: 1, label: '入门', desc: '基础题为主，适合刚开始备考' },
      { value: 2, label: '简单', desc: '难度较低，巩固基础知识' },
      { value: 3, label: '中等', desc: '推荐难度，覆盖常见考点' },
      { value: 4, label: '困难', desc: '挑战难题，冲刺高分' },
      { value: 5, label: '专家', desc: '竞赛级题目，挑战极限' }
    ]
  },

  onLoad() {
    const stored = wx.getStorageSync(STORAGE_KEY);
    if (stored) this.setData({ selected: stored });
  },

  select(e) {
    const value = e.currentTarget.dataset.value;
    this.setData({ selected: value });
    wx.setStorageSync(STORAGE_KEY, value);
    wx.showToast({ title: '已保存', icon: 'success' });
  }
});
