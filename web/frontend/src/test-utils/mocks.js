/**
 * Centralized mock services and data
 */

// Mock API responses
export const mockDevices = {
  devices: [
    {
      id: '1',
      name: 'Test Device 1',
      type: 'dlna',
      status: 'online',
      hostname: '192.168.1.100',
      friendly_name: 'Living Room TV',
      currentVideo: null
    },
    {
      id: '2',
      name: 'Test Device 2',
      type: 'airplay',
      status: 'playing',
      hostname: '192.168.1.101',
      friendly_name: 'Bedroom Apple TV',
      currentVideo: {
        id: 'v1',
        name: 'Test Video.mp4',
        duration: 120
      }
    }
  ],
  total: 2
};

export const mockVideos = {
  videos: [
    {
      id: 'v1',
      name: 'Test Video.mp4',
      path: '/videos/test.mp4',
      duration: 120,
      resolution: '1920x1080',
      format: 'mp4',
      file_size: 1024000
    },
    {
      id: 'v2',
      name: 'Another Video.mkv',
      path: '/videos/another.mkv',
      duration: 3600,
      resolution: '3840x2160',
      format: 'mkv',
      file_size: 5120000
    }
  ],
  total: 2
};

export const mockRenderers = {
  renderers: [
    {
      id: 'r1',
      type: 'chrome',
      status: 'running',
      url: 'https://example.com',
      device_id: '1'
    }
  ]
};

export const mockScenes = {
  scenes: [
    { id: 's1', name: 'Scene 1', type: 'animation' },
    { id: 's2', name: 'Scene 2', type: 'static' }
  ]
};

export const mockProjectors = {
  projectors: [
    { id: 'p1', name: 'Main Projector', status: 'idle' }
  ]
};

export const mockOverlayConfigs = {
  configs: [
    {
      id: 'oc1',
      name: 'Default Overlay',
      video_id: 'v1',
      widgets: [
        { id: 'w1', type: 'clock', visible: true },
        { id: 'w2', type: 'weather', visible: false }
      ]
    }
  ]
};

// Mock service implementations
export const createMockApiService = () => ({
  // Device APIs
  getDevices: jest.fn(() => Promise.resolve(mockDevices)),
  getDevice: jest.fn((id) => Promise.resolve(mockDevices.devices.find(d => d.id === id))),
  createDevice: jest.fn((device) => Promise.resolve({ id: '3', ...device })),
  updateDevice: jest.fn((id, updates) => Promise.resolve({ id, ...updates })),
  deleteDevice: jest.fn(() => Promise.resolve()),
  discoverDevices: jest.fn(() => Promise.resolve({ devices: [] })),
  pauseDevice: jest.fn(() => Promise.resolve()),
  stopDevice: jest.fn(() => Promise.resolve()),
  startDiscovery: jest.fn(() => Promise.resolve()),
  stopDiscovery: jest.fn(() => Promise.resolve()),
  enableAutoMode: jest.fn(() => Promise.resolve()),
  
  // Video APIs
  getVideos: jest.fn(() => Promise.resolve(mockVideos)),
  getVideo: jest.fn((id) => Promise.resolve(mockVideos.videos.find(v => v.id === id))),
  createVideo: jest.fn((video) => Promise.resolve({ id: 'v3', ...video })),
  updateVideo: jest.fn((id, updates) => Promise.resolve({ id, ...updates })),
  deleteVideo: jest.fn(() => Promise.resolve()),
  uploadVideo: jest.fn(() => Promise.resolve({ id: 'v3', name: 'uploaded.mp4' })),
  scanDirectory: jest.fn(() => Promise.resolve({ videos_found: 5 })),
  playVideoOnDevice: jest.fn(() => Promise.resolve()),
  
  // Renderer APIs
  getRenderers: jest.fn(() => Promise.resolve(mockRenderers)),
  getScenes: jest.fn(() => Promise.resolve(mockScenes)),
  getProjectors: jest.fn(() => Promise.resolve(mockProjectors)),
  startRenderer: jest.fn(() => Promise.resolve({ id: 'r2', status: 'starting' })),
  stopRenderer: jest.fn(() => Promise.resolve()),
  pauseRenderer: jest.fn(() => Promise.resolve()),
  resumeRenderer: jest.fn(() => Promise.resolve()),
  getRendererStatus: jest.fn(() => Promise.resolve({ status: 'running', uptime: 120 })),
  discoverAirPlayDevices: jest.fn(() => Promise.resolve({ devices: [] })),
  startProjector: jest.fn(() => Promise.resolve()),
  
  // Settings APIs
  loadConfig: jest.fn(() => Promise.resolve()),
  saveConfig: jest.fn(() => Promise.resolve()),
  
  // Overlay APIs
  getOverlayConfigs: jest.fn(() => Promise.resolve(mockOverlayConfigs)),
  createOverlayConfig: jest.fn((config) => Promise.resolve({ id: 'oc2', ...config })),
  updateOverlayConfig: jest.fn((id, updates) => Promise.resolve({ id, ...updates })),
  deleteOverlayConfig: jest.fn(() => Promise.resolve()),
  updateBrightness: jest.fn(() => Promise.resolve()),
  syncOverlays: jest.fn(() => Promise.resolve()),
});

// Mock HTTP client
export const createMockHttpClient = () => {
  const mockClient = {
    get: jest.fn(() => Promise.resolve({ data: {} })),
    post: jest.fn(() => Promise.resolve({ data: {} })),
    put: jest.fn(() => Promise.resolve({ data: {} })),
    patch: jest.fn(() => Promise.resolve({ data: {} })),
    delete: jest.fn(() => Promise.resolve({ data: {} })),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() }
    }
  };
  
  return mockClient;
};