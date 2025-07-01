// Mock implementation of the API service
import { createMockApiService } from '../../test-utils/mocks';

// Create a mock API instance
const mockApi = createMockApiService();

// Export all the API methods
module.exports = mockApi;

// Also export as ES modules
export default mockApi;
export const {
  // Device APIs
  getDevices,
  getDevice,
  createDevice,
  updateDevice,
  deleteDevice,
  discoverDevices,
  pauseDevice,
  stopDevice,
  startDiscovery,
  stopDiscovery,
  enableAutoMode,
  
  // Video APIs
  getVideos,
  getVideo,
  createVideo,
  updateVideo,
  deleteVideo,
  uploadVideo,
  scanDirectory,
  playVideoOnDevice,
  
  // Renderer APIs
  getRenderers,
  getScenes,
  getProjectors,
  startRenderer,
  stopRenderer,
  pauseRenderer,
  resumeRenderer,
  getRendererStatus,
  discoverAirPlayDevices,
  startProjector,
  
  // Settings APIs
  loadConfig,
  saveConfig,
  
  // Overlay APIs
  getOverlayConfigs,
  createOverlayConfig,
  updateOverlayConfig,
  deleteOverlayConfig,
  updateBrightness,
  syncOverlays,
} = mockApi;