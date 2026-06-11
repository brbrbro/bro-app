const auth = require('./utils/auth.js');

App({
  globalData: {
    userInfo: null,
    token: null,
    region: 'mainland',
    apiBase: 'http://127.0.0.1:5001/api',
    pendingInvite: null
  },
  onLaunch(options) {
    if (options && options.query && options.query.invite) {
      this.globalData.pendingInvite = options.query.invite;
    }
    auth.login()
      .then(() => {
        console.log('Auto-login success');
        const invite = this.globalData.pendingInvite;
        if (invite) {
          const api = require('./utils/api.js');
          api.bindInvite(invite)
            .then(() => { wx.showToast({ title: '邀请绑定成功 +50', icon: 'success' }); })
            .catch(() => {});
          this.globalData.pendingInvite = null;
        }
      })
      .catch((err) => {
        console.log('Auto-login failed:', err.message || err);
      });
  }
});
