import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://127.0.0.1:5001/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
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
  
  return api.post('/import/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const getBatches = (page = 1) => {
  return api.get('/import/batches', { params: { page } });
};

export const getBatchQuestions = (batchId, status = 'pending') => {
  return api.get(`/import/batch/${batchId}/questions`, { params: { status } });
};

export const approveQuestion = (questionId, data) => {
  return api.post(`/import/question/${questionId}/approve`, data);
};

export const rejectQuestion = (questionId, data) => {
  return api.post(`/import/question/${questionId}/reject`, data);
};

export default api;
