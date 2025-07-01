/**
 * Test data builders for creating consistent test objects
 */

// Device builder
export const deviceBuilder = (overrides = {}) => ({
  id: '1',
  name: 'Test Device',
  type: 'dlna',
  status: 'online',
  hostname: '192.168.1.100',
  friendly_name: 'Test DLNA Device',
  action_url: 'http://192.168.1.100:8080/action',
  location: 'http://192.168.1.100:8080/description.xml',
  currentVideo: null,
  playback_progress: 0,
  ...overrides
});

// Video builder
export const videoBuilder = (overrides = {}) => ({
  id: '1',
  name: 'Test Video.mp4',
  path: '/videos/test-video.mp4',
  duration: 120,
  resolution: '1920x1080',
  format: 'mp4',
  file_size: 1024000,
  has_subtitle: false,
  ...overrides
});

// Renderer builder
export const rendererBuilder = (overrides = {}) => ({
  id: '1',
  type: 'chrome',
  status: 'idle',
  url: '',
  device_id: null,
  ...overrides
});

// Scene builder
export const sceneBuilder = (overrides = {}) => ({
  id: '1',
  name: 'Default Scene',
  type: 'animation',
  config: {},
  ...overrides
});

// Projector builder
export const projectorBuilder = (overrides = {}) => ({
  id: '1',
  name: 'Main Projector',
  status: 'idle',
  resolution: '1920x1080',
  ...overrides
});

// Overlay config builder
export const overlayConfigBuilder = (overrides = {}) => ({
  id: '1',
  name: 'Default Overlay',
  video_id: null,
  widgets: [],
  brightness: 100,
  ...overrides
});

// Widget builder
export const widgetBuilder = (overrides = {}) => ({
  id: '1',
  type: 'clock',
  visible: true,
  position: { x: 0, y: 0 },
  size: { width: 200, height: 100 },
  config: {},
  ...overrides
});

// Error response builder
export const errorBuilder = (overrides = {}) => ({
  message: 'An error occurred',
  status: 500,
  detail: 'Internal server error',
  ...overrides
});

// Success response builder
export const successBuilder = (overrides = {}) => ({
  success: true,
  message: 'Operation completed successfully',
  ...overrides
});

// Batch builders for lists
export const buildDeviceList = (count = 3, overrides = []) => 
  Array.from({ length: count }, (_, i) => 
    deviceBuilder({
      id: `device-${i + 1}`,
      name: `Device ${i + 1}`,
      ...overrides[i]
    })
  );

export const buildVideoList = (count = 3, overrides = []) =>
  Array.from({ length: count }, (_, i) =>
    videoBuilder({
      id: `video-${i + 1}`,
      name: `Video ${i + 1}.mp4`,
      ...overrides[i]
    })
  );