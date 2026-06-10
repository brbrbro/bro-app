const auth = require('../../utils/auth.js');

Page({
  data: { inviteCode: '', inviteText: '' },

  onLoad() {
    const user = auth.getUserInfo();
    const code = user && user.id ? `BRO${String(user.id).padStart(6, '0')}` : 'BROGUEST';
    const text = `我在 BRO 刷题，邀请你一起备考！邀请码：${code}，下载小程序后输入即可绑定同学关系。`;
    this.setData({ inviteCode: code, inviteText: text });
  },

  copyCode() {
    wx.setClipboardData({
      data: this.data.inviteCode,
      success: () => wx.showToast({ title: '邀请码已复制', icon: 'success' })
    });
  },

  copyText() {
    wx.setClipboardData({
      data: this.data.inviteText,
      success: () => wx.showToast({ title: '邀请文案已复制', icon: 'success' })
    });
  },

  onShareAppMessage() {
    return { title: 'BRO 刷题 - 一起备考', path: `/pages/index/index?invite=${this.data.inviteCode}` };
  }
});
