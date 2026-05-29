const sync = require('../../utils/sync.js');
const storage = require('../../utils/storage.js');
const auth = require('../../utils/auth.js');

Page({
  data: { syncStatus: 'idle', lastSyncTime: null, localCount: 0, isLoggedIn: false },

  onShow() {
    const lastSyncTime = storage.getSyncTime();
    const progress = storage.getProgress();
    const notes = storage.getNotes();
    this.setData({ lastSyncTime, localCount: progress.length + notes.length, isLoggedIn: auth.isLoggedIn() });
  },

  async uploadToCloud() {
    if (!auth.isLoggedIn()) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    this.setData({ syncStatus: 'uploading' });
    const result = await sync.uploadToCloud();
    if (result.success) { this.setData({ syncStatus: 'success', lastSyncTime: Date.now() }); wx.showToast({ title: `上传成功: ${result.synced_count} 条`, icon: 'success' }); }
    else { this.setData({ syncStatus: 'error' }); wx.showToast({ title: result.error || '上传失败', icon: 'none' }); }
  },

  async downloadFromCloud() {
    if (!auth.isLoggedIn()) {
      wx.showToast({ title: '请先登录', icon: 'none' });
      return;
    }
    this.setData({ syncStatus: 'downloading' });
    const result = await sync.downloadFromCloud();
    if (result.success) { this.setData({ syncStatus: 'success' }); wx.showToast({ title: `下载成功: ${result.downloaded_count} 条`, icon: 'success' }); }
    else { this.setData({ syncStatus: 'error' }); wx.showToast({ title: result.error || '下载失败', icon: 'none' }); }
  }
});
