import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json'
  }
});

export const uploadFile = (file, examType, subject, grade, knowledgePoint) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('exam_type', examType);
  formData.append('subject', subject);
  formData.append('grade', grade);
  formData.append('knowledge_point', knowledgePoint);
  formData.append('created_by', 'admin');
  return api.post('/import/batch', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const importSingleQuestion = (data) => api.post('/import/single', data);

export const getBatches = (page = 1) => api.get('/import/batches', { params: { page } });
export const getBatchDetail = (batchId) => api.get(`/import/batch/${batchId}`);
export const getBatchQuestions = (batchId, status = 'pending') => api.get(`/import/batch/${batchId}/questions`, { params: { status } });

export const updateParsedQuestion = (questionId, data) => api.put(`/import/parsed/${questionId}`, data);
export const approveQuestion = (questionId, data) => api.post(`/import/question/${questionId}/approve`, data);
export const rejectQuestion = (questionId, data) => api.post(`/import/question/${questionId}/reject`, data);
export const splitParsedQuestion = (questionId, data) => api.post(`/import/parsed/${questionId}/split`, data);
export const mergeParsedQuestion = (questionId, targetId) => api.post(`/import/parsed/${questionId}/merge`, { target_id: targetId });
export const approveSafeQuestions = (batchId, minConfidence = 0.85) => api.post(`/import/batch/${batchId}/approve-safe`, { min_confidence: minConfidence });

export const getAdminBatches = (params = {}) => api.get('/admin/import/batches', { params });
export const getAdminBatch = (id) => api.get(`/admin/import/batches/${id}`);
export const deleteAdminBatch = (id) => api.delete(`/admin/import/batches/${id}`);
export const reparseAdminBatch = (id) => api.post(`/admin/import/batches/${id}/reparse`);

export const getAdminQuestions = (params = {}) => api.get('/admin/questions', { params });
export const getAdminQuestion = (id) => api.get(`/admin/questions/${id}`);
export const updateAdminQuestion = (id, data) => api.put(`/admin/questions/${id}`, data);
export const archiveAdminQuestion = (id) => api.post(`/admin/questions/${id}/archive`);
export const deleteAdminQuestion = (id) => api.delete(`/admin/questions/${id}`);

export const getQualityIssues = (params = {}) => api.get('/admin/quality/issues', { params });
export const getImportStats = (params = {}) => api.get('/admin/import/stats', { params });

export default api;
