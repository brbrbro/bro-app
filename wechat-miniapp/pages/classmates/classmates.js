Page({
  data: { classmates: [] },
  onShow() {
    const stored = wx.getStorageSync('classmates_list') || [];
    this.setData({ classmates: stored });
  },
  goInvite() { wx.navigateTo({ url: '/pages/invite/invite' }); }
});
