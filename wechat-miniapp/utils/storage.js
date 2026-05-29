const STORAGE_KEYS = { PROGRESS: 'local_progress', NOTES: 'local_notes', USER: 'user_info', SYNC_TIME: 'last_sync_time' };

function get(key) { return wx.getStorageSync(key); }
function set(key, value) { wx.setStorageSync(key, value); }

function saveProgress(progress) {
  const list = get(STORAGE_KEYS.PROGRESS) || [];
  list.push(progress);
  set(STORAGE_KEYS.PROGRESS, list);
}

function getProgress() { return get(STORAGE_KEYS.PROGRESS) || []; }

function getWrongQuestions() {
  return getProgress().filter(p => !p.is_correct);
}

function saveNote(note) {
  const list = get(STORAGE_KEYS.NOTES) || [];
  list.unshift(note);
  set(STORAGE_KEYS.NOTES, list);
}

function getNotes() { return get(STORAGE_KEYS.NOTES) || []; }
function setUserInfo(userInfo) { set(STORAGE_KEYS.USER, userInfo); }
function getUserInfo() { return get(STORAGE_KEYS.USER); }
function setSyncTime(time) { set(STORAGE_KEYS.SYNC_TIME, time); }
function getSyncTime() { return get(STORAGE_KEYS.SYNC_TIME); }
function clearAll() { Object.values(STORAGE_KEYS).forEach(key => { wx.removeStorageSync(key); }); }

module.exports = { STORAGE_KEYS, saveProgress, getProgress, getWrongQuestions, saveNote, getNotes, setUserInfo, getUserInfo, setSyncTime, getSyncTime, clearAll };