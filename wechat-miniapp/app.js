const auth = require('./utils/auth.js');

App({
  globalData: {
    userInfo: null,
    token: null,
    region: 'mainland',
    apiBase: 'http://106.53.188.248/api'
  },
  onLaunch() {
    // Try auto-login with longer timeout
    auth.login()
      .then(() => console.log('Auto-login success'))
      .catch((err) => {
        console.log('Auto-login failed (expected in dev):', err.message || err);
        // Continue without login - app works in local mode
      });
  }
});