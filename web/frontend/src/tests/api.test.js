import axios from 'axios';
import { deviceApi, videoApi } from '../services/api';

// Mock axios
jest.mock('axios');

describe('API Service', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Device API', () => {
    test('getDevices should make a GET request to /api/devices', async () => {
      // Mock successful response
      const mockResponse = { data: { devices: [], total: 0 } };
      axios.get.mockResolvedValueOnce(mockResponse);
      
      // Call the API
      const result = await deviceApi.getDevices();
      
      // Verify the request was made with the correct URL
      expect(axios.get).toHaveBeenCalledWith('/api/devices', { params: {} });
      
      // Verify the result
      expect(result).toEqual(mockResponse);
    });

    test('discoverDevices should make a GET request to /api/devices/discover', async () => {
      // Mock successful response
      const mockResponse = { data: { devices: [], total: 0 } };
      axios.get.mockResolvedValueOnce(mockResponse);
      
      // Call the API
      const result = await deviceApi.discoverDevices();
      
      // Verify the request was made with the correct URL
      expect(axios.get).toHaveBeenCalledWith('/api/devices/discover');
      
      // Verify the result
      expect(result).toEqual(mockResponse);
    });

    test('playVideo should make a POST request to /api/devices/:id/play', async () => {
      // Mock successful response
      const mockResponse = { data: { success: true } };
      axios.post.mockResolvedValueOnce(mockResponse);
      
      // Call the API
      const deviceId = 1;
      const videoId = 2;
      const loop = true;
      const result = await deviceApi.playVideo(deviceId, videoId, loop);
      
      // Verify the request was made with the correct URL and data
      expect(axios.post).toHaveBeenCalledWith(
        `/api/devices/${deviceId}/play`, 
        { video_id: videoId, loop }
      );
      
      // Verify the result
      expect(result).toEqual(mockResponse);
    });

    test('stopVideo should make a POST request to /api/devices/:id/stop', async () => {
      // Mock successful response
      const mockResponse = { data: { success: true } };
      axios.post.mockResolvedValueOnce(mockResponse);
      
      // Call the API
      const deviceId = 1;
      const result = await deviceApi.stopVideo(deviceId);
      
      // Verify the request was made with the correct URL
      expect(axios.post).toHaveBeenCalledWith(`/api/devices/${deviceId}/stop`);
      
      // Verify the result
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Video API', () => {
    test('getVideos should make a GET request to /api/videos', async () => {
      // Mock successful response
      const mockResponse = { data: { videos: [], total: 0 } };
      axios.get.mockResolvedValueOnce(mockResponse);
      
      // Call the API
      const result = await videoApi.getVideos();
      
      // Verify the request was made with the correct URL
      expect(axios.get).toHaveBeenCalledWith('/api/videos', { params: {} });
      
      // Verify the result
      expect(result).toEqual(mockResponse);
    });

    test('uploadVideo should make a POST request to /api/videos/upload with FormData', async () => {
      // Mock successful response
      const mockResponse = { data: { id: 1, name: 'test.mp4' } };
      axios.post.mockResolvedValueOnce(mockResponse);
      
      // Create a mock FormData
      const formData = new FormData();
      formData.append('file', new Blob(['test'], { type: 'video/mp4' }), 'test.mp4');
      
      // Call the API
      const result = await videoApi.uploadVideo(formData);
      
      // Verify the request was made with the correct URL and data
      expect(axios.post).toHaveBeenCalledWith(
        '/api/videos/upload', 
        formData, 
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );
      
      // Verify the result
      expect(result).toEqual(mockResponse);
    });

    test('scanDirectory should make a POST request to /api/videos/scan-directory', async () => {
      // Mock successful response
      const mockResponse = { data: { videos: [], total: 0 } };
      axios.post.mockResolvedValueOnce(mockResponse);
      
      // Call the API
      const directory = '/path/to/videos';
      const result = await videoApi.scanDirectory(directory);
      
      // Verify the request was made with the correct URL and params
      expect(axios.post).toHaveBeenCalledWith(
        '/api/videos/scan-directory', 
        null, 
        { params: { directory } }
      );
      
      // Verify the result
      expect(result).toEqual(mockResponse);
    });
  });

  describe('Error Handling', () => {
    test('should handle 404 errors correctly', async () => {
      // Mock a 404 error response
      const errorResponse = {
        response: {
          status: 404,
          data: { detail: 'Not found' },
        },
        config: { url: '/api/devices' }
      };
      axios.get.mockRejectedValueOnce(errorResponse);
      
      // Call the API and expect it to reject
      await expect(deviceApi.getDevices()).rejects.toEqual(errorResponse);
    });

    test('should handle network errors correctly', async () => {
      // Mock a network error
      const errorResponse = {
        request: {},
        message: 'Network Error'
      };
      axios.get.mockRejectedValueOnce(errorResponse);
      
      // Call the API and expect it to reject
      await expect(deviceApi.getDevices()).rejects.toEqual(errorResponse);
    });
  });
});
