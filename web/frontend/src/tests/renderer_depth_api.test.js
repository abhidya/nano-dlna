import axios from 'axios';
import MockAdapter from 'axios-mock-adapter';
import { rendererApi, depthApi } from '../services/api';

// Create a mock for the axios instance
const mock = new MockAdapter(axios);

describe('Renderer API', () => {
  // Reset mocks before each test
  beforeEach(() => {
    mock.reset();
  });

  test('listRenderers should fetch active renderers', async () => {
    const mockData = {
      renderers: [
        {
          id: 'renderer-1',
          projector_id: 'proj-hccast',
          scene_id: 'overlay-frontdoor',
          status: 'running',
          target_name: 'Hccast-3ADE76'
        }
      ]
    };

    mock.onGet('/api/renderer/list').reply(200, mockData);

    const response = await rendererApi.listRenderers();
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('listProjectors should fetch available projectors', async () => {
    const mockData = {
      projectors: [
        {
          id: 'proj-hccast',
          name: 'Hallway Projector',
          sender: 'dlna',
          target_name: 'Hccast-3ADE76_dlna',
          scene: 'overlay-frontdoor',
          fallback_sender: 'direct',
          fallback_target: 'display-1'
        }
      ]
    };

    mock.onGet('/api/renderer/projectors').reply(200, mockData);

    const response = await rendererApi.listProjectors();
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('listScenes should fetch available scenes', async () => {
    const mockData = {
      scenes: [
        {
          id: 'overlay-frontdoor',
          name: 'Front Door Overlay',
          template: 'overlay_frontdoor/index.html',
          data: {
            video_file: 'door6.mp4'
          }
        }
      ]
    };

    mock.onGet('/api/renderer/scenes').reply(200, mockData);

    const response = await rendererApi.listScenes();
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('getRendererStatus should fetch status for a projector', async () => {
    const projectorId = 'proj-hccast';
    const mockData = {
      projector_id: projectorId,
      projector_name: 'Hallway Projector',
      status: 'running',
      scene_id: 'overlay-frontdoor',
      scene_name: 'Front Door Overlay',
      renderer_type: 'chrome',
      details: {
        process_id: 12345,
        uptime: 120,
        memory_usage: 156000000
      }
    };

    mock.onGet(`/api/renderer/status/${projectorId}`).reply(200, mockData);

    const response = await rendererApi.getRendererStatus(projectorId);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('startRenderer should start a renderer for a scene on a projector', async () => {
    const scene = 'overlay-frontdoor';
    const projector = 'proj-hccast';
    const options = { loop: true };
    const mockData = {
      success: true,
      renderer_id: 'renderer-1',
      message: 'Renderer started successfully'
    };

    mock.onPost('/api/renderer/start').reply(200, mockData);

    const response = await rendererApi.startRenderer(scene, projector, options);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
    expect(mock.history.post[0].data).toBe(JSON.stringify({ scene, projector, options }));
  });

  test('stopRenderer should stop a renderer on a projector', async () => {
    const projector = 'proj-hccast';
    const mockData = {
      success: true,
      message: 'Renderer stopped successfully'
    };

    mock.onPost('/api/renderer/stop').reply(200, mockData);

    const response = await rendererApi.stopRenderer(projector);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
    expect(mock.history.post[0].data).toBe(JSON.stringify({ projector }));
  });

  test('startProjector should start a projector with its default scene', async () => {
    const projectorId = 'proj-hccast';
    const mockData = {
      success: true,
      renderer_id: 'renderer-1',
      message: 'Projector started with default scene'
    };

    mock.onPost(`/api/renderer/start_projector?projector_id=${projectorId}`).reply(200, mockData);

    const response = await rendererApi.startProjector(projectorId);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('startRenderer should handle errors', async () => {
    const scene = 'overlay-frontdoor';
    const projector = 'nonexistent-projector';
    const options = {};
    const mockError = {
      detail: 'Projector not found'
    };

    mock.onPost('/api/renderer/start').reply(404, mockError);

    await expect(rendererApi.startRenderer(scene, projector, options)).rejects.toThrow();
  });
});

describe('Depth Processing API', () => {
  // Reset mocks before each test
  beforeEach(() => {
    mock.reset();
  });

  test('uploadDepthMap should upload a depth map file', async () => {
    const formData = new FormData();
    formData.append('file', new Blob(['depth map data'], { type: 'image/png' }));
    formData.append('normalize', 'true');

    const mockData = {
      success: true,
      depth_id: 'depth-uuid-1',
      message: 'Depth map uploaded and normalized'
    };

    mock.onPost('/api/depth/upload').reply(200, mockData);

    const response = await depthApi.uploadDepthMap(formData);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('previewDepthMap should return the correct URL', () => {
    const depthId = 'depth-uuid-1';
    const url = depthApi.previewDepthMap(depthId);
    expect(url).toBe(`/api/depth/preview/${depthId}`);
  });

  test('segmentDepthMap should segment a depth map', async () => {
    const depthId = 'depth-uuid-1';
    const segmentationParams = {
      method: 'kmeans',
      n_clusters: 5
    };

    const mockData = {
      success: true,
      depth_id: depthId,
      segment_count: 5,
      segments: [0, 1, 2, 3, 4],
      message: 'Depth map segmented using kmeans with 5 clusters'
    };

    mock.onPost(`/api/depth/segment/${depthId}`).reply(200, mockData);

    const response = await depthApi.segmentDepthMap(depthId, segmentationParams);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
    expect(mock.history.post[0].data).toBe(JSON.stringify(segmentationParams));
  });

  test('previewSegmentation should return the correct URL', () => {
    const depthId = 'depth-uuid-1';
    const alpha = 0.7;
    const url = depthApi.previewSegmentation(depthId, alpha);
    expect(url).toBe(`/api/depth/segmentation_preview/${depthId}?alpha=${alpha}`);
  });

  test('exportMasks should export masks for segments', async () => {
    const depthId = 'depth-uuid-1';
    const segmentIds = [1, 2, 3];
    const cleanMask = true;
    const minArea = 100;
    const kernelSize = 3;

    const mockData = {
      success: true,
      depth_id: depthId,
      segment_ids: segmentIds,
      message: 'Masks exported successfully'
    };

    mock.onPost(`/api/depth/export_masks/${depthId}`).reply(200, mockData);

    const response = await depthApi.exportMasks(depthId, segmentIds, cleanMask, minArea, kernelSize);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
    expect(JSON.parse(mock.history.post[0].data)).toEqual({
      segment_ids: segmentIds,
      clean_mask: cleanMask,
      min_area: minArea,
      kernel_size: kernelSize
    });
  });

  test('deleteDepthMap should delete a depth map', async () => {
    const depthId = 'depth-uuid-1';
    const mockData = {
      success: true,
      message: 'Depth map deleted successfully'
    };

    mock.onDelete(`/api/depth/${depthId}`).reply(200, mockData);

    const response = await depthApi.deleteDepthMap(depthId);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('getMask should return the correct URL', () => {
    const depthId = 'depth-uuid-1';
    const segmentId = 2;
    const clean = true;
    const minArea = 100;
    const kernelSize = 3;
    const url = depthApi.getMask(depthId, segmentId, clean, minArea, kernelSize);
    expect(url).toBe(`/api/depth/mask/${depthId}/${segmentId}?clean=${clean}&min_area=${minArea}&kernel_size=${kernelSize}`);
  });

  test('createProjection should create a projection mapping configuration', async () => {
    const config = {
      name: 'Test Projection',
      depth_id: 'depth-uuid-1',
      segments: [1, 2, 3],
      videos: {
        '1': 'video1.mp4',
        '2': 'video2.mp4',
        '3': 'video3.mp4'
      }
    };

    const mockData = {
      success: true,
      config_id: 'projection-uuid-1',
      message: 'Projection mapping configuration created successfully'
    };

    mock.onPost('/api/depth/projection/create').reply(200, mockData);

    const response = await depthApi.createProjection(config);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
    expect(mock.history.post[0].data).toBe(JSON.stringify(config));
  });

  test('getProjection should return the correct URL', () => {
    const configId = 'projection-uuid-1';
    const url = depthApi.getProjection(configId);
    expect(url).toBe(`/api/depth/projection/${configId}`);
  });

  test('deleteProjection should delete a projection configuration', async () => {
    const configId = 'projection-uuid-1';
    const mockData = {
      success: true,
      message: 'Projection configuration deleted successfully'
    };

    mock.onDelete(`/api/depth/projection/${configId}`).reply(200, mockData);

    const response = await depthApi.deleteProjection(configId);
    expect(response.status).toBe(200);
    expect(response.data).toEqual(mockData);
  });

  test('segmentDepthMap should handle errors', async () => {
    const depthId = 'nonexistent-uuid';
    const segmentationParams = {
      method: 'kmeans',
      n_clusters: 5
    };

    const mockError = {
      detail: 'Depth map not found'
    };

    mock.onPost(`/api/depth/segment/${depthId}`).reply(404, mockError);

    await expect(depthApi.segmentDepthMap(depthId, segmentationParams)).rejects.toThrow();
  });
});
