const STORAGE_KEYS = {
  TOKEN: 'token',
  USER_INFO: 'userInfo'
};

function login() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => {
        if (res.code) {
          const app = getApp();
          const apiBase = app && app.globalData && app.globalData.apiBase ? app.globalData.apiBase : 'http://106.53.188.248:5001/api';
          wx.request({
            url: apiBase + '/users/wx-login',
            method: 'POST',
            data: { code: res.code },
            success: (response) => {
              if (response.data && response.data.success) {
                const { token, user } = response.data;
                wx.setStorageSync(STORAGE_KEYS.TOKEN, token);
                wx.setStorageSync(STORAGE_KEYS.USER_INFO, user);
                if (app && app.globalData) {
                  app.globalData.userInfo = user;
                }
                resolve({ success: true, token, user });
              } else {
                reject(new Error((response.data && response.data.message) || 'Login failed'));
              }
            },
            fail: (err) => {
              reject(new Error(err.errMsg || 'Request failed'));
            }
          });
        } else {
          reject(new Error('wx.login failed: no code returned'));
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || 'wx.login failed'));
      }
    });
  });
}

function getToken() {
  try {
    return wx.getStorageSync(STORAGE_KEYS.TOKEN);
  } catch (e) {
    return null;
  }
}

function getUserInfo() {
  try {
    return wx.getStorageSync(STORAGE_KEYS.USER_INFO) || (getApp() && getApp().globalData && getApp().globalData.userInfo);
  } catch (e) {
    return null;
  }
}

function isLoggedIn() {
  return !!getToken();
}

function logout() {
  try {
    wx.removeStorageSync(STORAGE_KEYS.TOKEN);
    wx.removeStorageSync(STORAGE_KEYS.USER_INFO);
    const app = getApp();
    if (app && app.globalData) {
      app.globalData.userInfo = null;
    }
  } catch (e) {
    console.error('Logout failed:', e);
  }
}

module.exports = {
  login,
  getToken,
  getUserInfo,
  isLoggedIn,
  logout
};
