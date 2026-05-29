const storage = require('./storage.js');
const api = require('./api.js');
const auth = require('./auth.js');

async function uploadToCloud() {
  if (!auth.isLoggedIn()) return { success: false, error: 'not_logged_in' };
  const progress = storage.getProgress();
  const lastSync = storage.getSyncTime();
  const unsynced = progress.filter(p => p.answered_at > (lastSync || 0));
  
  try {
    let synced_count = 0;
    for (const entry of unsynced) {
      const data = {
        question_id: entry.question_id,
        user_answer: entry.user_answer,
        is_correct: entry.is_correct,
        time_spent: entry.time_spent
      };
      await api.submitProgress(data);
      synced_count++;
    }
    if (synced_count > 0) storage.setSyncTime(Date.now());
    return { success: true, synced_count };
  } catch (error) { return { success: false, error: error.message }; }
}

async function downloadFromCloud() {
  if (!auth.isLoggedIn()) return { success: false, error: 'not_logged_in' };
  try {
    const res = await api.getProgress({ per_page: 1000 });
    const cloudProgress = res.progress || [];
    const localProgress = storage.getProgress();
    const map = new Map([...localProgress, ...cloudProgress].map(p => [p.question_id, p]));
    storage.set(storage.STORAGE_KEYS.PROGRESS, Array.from(map.values()));
    storage.setSyncTime(Date.now());
    return { success: true, downloaded_count: cloudProgress.length };
  } catch (error) { return { success: false, error: error.message }; }
}

module.exports = { uploadToCloud, downloadFromCloud };
