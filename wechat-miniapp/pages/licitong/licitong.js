const api = require('../../utils/api.js');

const FALLBACK_CARDS = [
  { word: '函数', definition: '数学：自变量与因变量之间的对应关系', example: 'y = 2x + 1 是一次函数' },
  { word: '导数', definition: '函数在某点变化率的极限', example: 'f(x) = x² 的导数是 2x' },
  { word: '极限', definition: '函数值无限接近某常数的过程', example: 'lim(x→0) sin(x)/x = 1' },
  { word: '积分', definition: '与微分互为逆运算的求和过程', example: '∫x dx = ½x² + C' },
  { word: '向量', definition: '既有大小又有方向的量', example: '(3, 4) 表示长度 5 的向量' }
];

Page({
  data: { index: 0, showAnswer: false, cards: [] },

  onLoad() { this.loadCards(); },

  loadCards() {
    api.getLexicon({ limit: 50 })
      .then(res => {
        const cards = (res.words || []).map(w => ({ word: w.word, definition: w.definition, example: w.example, def: w.definition }));
        this.setData({ cards: cards.length ? cards : FALLBACK_CARDS, index: 0, showAnswer: false });
      })
      .catch(() => this.setData({ cards: FALLBACK_CARDS, index: 0, showAnswer: false }));
  },

  flip() { this.setData({ showAnswer: !this.data.showAnswer }); },

  prev() {
    if (this.data.index > 0) this.setData({ index: this.data.index - 1, showAnswer: false });
  },

  next() {
    if (this.data.index < this.data.cards.length - 1) {
      this.setData({ index: this.data.index + 1, showAnswer: false });
    } else {
      wx.showToast({ title: '已经是最后一张了', icon: 'none' });
    }
  }
});
