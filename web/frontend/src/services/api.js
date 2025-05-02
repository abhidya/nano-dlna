import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor
api.interceptors.request.use(
  (config) => {
    // You can add auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors here
    if (error.response) {
      // The request was made and the server responded with a status code
      // that falls out of the range of 2xx
      console.error('API Error Response:', error.response.data);
      console.error('Status:', error.response.status);
    } else if (error.request) {
      // The request was made but no response was received
      console.error('API Error Request:', error.request);
    } else {
      // Something happened in setting up the request that triggered an Error
      console.error('API Error Message:', error.message);
    }
    return Promise.reject(error);
  }
);

// Device API
const deviceApi = {
  getDevices: (params = {}) => api.get('/devices', { params }),
  getDevice: (id) => api.get(`/devices/${id}`),
  createDevice: (data) => api.post('/devices', data),
  updateDevice: (id, data) => api.put(`/devices/${id}`, data),
  deleteDevice: (id) => api.delete(`/devices/${id}`),
  discoverDevices: () => api.get('/devices/discover'),
  playVideo: (deviceId, videoId, loop = false) => 
    api.post(`/devices/${deviceId}/play`, { video_id: videoId, loop }),
  stopVideo: (deviceId) => api.post(`/devices/${deviceId}/stop`),
  pauseVideo: (deviceId) => api.post(`/devices/${deviceId}/pause`),
  seekVideo: (deviceId, position) => 
    api.post(`/devices/${deviceId}/seek`, null, { params: { position } }),
  loadConfig: (configFile) => 
    api.post('/devices/load-config', null, { params: { config_file: configFile } }),
  saveConfig: (configFile) => 
    api.post('/devices/save-config', null, { params: { config_file: configFile } }),
};

// Video API
const videoApi = {
  getVideos: (params = {}) => api.get('/videos', { params }),
  getVideo: (id) => api.get(`/videos/${id}`),
  createVideo: (data) => api.post('/videos', data),
  updateVideo: (id, data) => api.put(`/videos/${id}`, data),
  deleteVideo: (id) => api.delete(`/videos/${id}`),
  uploadVideo: (formData) => api.post('/videos/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  streamVideo: (id, serveIp) => 
    api.post(`/videos/${id}/stream`, null, { params: { serve_ip: serveIp } }),
  scanDirectory: (directory) => 
    api.post('/videos/scan-directory', null, { params: { directory } }),
};

// Settings API (placeholder for future implementation)
const settingsApi = {
  getSettings: () => Promise.resolve({ 
    autoDiscoverDevices: true,
    defaultVideoDirectory: '/tmp/nanodlna/uploads',
    enableLogging: true,
    logLevel: 'info',
    serverPort: 8000,
    enableSubtitles: true
  }),
  updateSettings: (settings) => Promise.resolve(settings),
};

export { api, deviceApi, videoApi, settingsApi };
