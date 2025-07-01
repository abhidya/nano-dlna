/**
 * Test to verify our test architecture is working correctly
 */

import React from 'react';
import { screen } from '@testing-library/react';
import { render } from '../test-utils/render';
import { createMockApiService, createMockHttpClient } from '../test-utils/mocks';
import { deviceBuilder, videoBuilder } from '../test-utils/builders';
import { getApiBaseURL, isTestEnvironment } from '../utils/environment';

describe('Test Architecture Verification', () => {
  test('environment utilities work in test environment', () => {
    expect(isTestEnvironment()).toBe(true);
    // Check what we actually get
    const apiUrl = getApiBaseURL();
    console.log('API Base URL:', apiUrl);
    expect(apiUrl).toBe('http://localhost:3000/api');
  });

  test('mock API service has all required methods', () => {
    const mockApi = createMockApiService();
    
    // Device methods
    expect(mockApi.getDevices).toBeDefined();
    expect(mockApi.getDevice).toBeDefined();
    expect(mockApi.deleteDevice).toBeDefined();
    expect(mockApi.pauseDevice).toBeDefined();
    expect(mockApi.stopDevice).toBeDefined();
    
    // Video methods
    expect(mockApi.getVideos).toBeDefined();
    expect(mockApi.getVideo).toBeDefined();
    expect(mockApi.uploadVideo).toBeDefined();
    expect(mockApi.playVideoOnDevice).toBeDefined();
  });

  test('test data builders create valid objects', () => {
    const device = deviceBuilder();
    expect(device).toHaveProperty('id');
    expect(device).toHaveProperty('name');
    expect(device).toHaveProperty('type');
    expect(device).toHaveProperty('status');
    
    const video = videoBuilder();
    expect(video).toHaveProperty('id');
    expect(video).toHaveProperty('name');
    expect(video).toHaveProperty('path');
    expect(video).toHaveProperty('duration');
  });

  test('custom render includes router', () => {
    const TestComponent = () => <div>Test Component</div>;
    
    render(<TestComponent />);
    
    expect(screen.getByText('Test Component')).toBeInTheDocument();
  });

  test('mock HTTP client works', async () => {
    const mockClient = createMockHttpClient();
    mockClient.get.mockResolvedValue({ data: { test: 'data' } });
    
    const response = await mockClient.get('/test');
    
    expect(response.data).toEqual({ test: 'data' });
    expect(mockClient.get).toHaveBeenCalledWith('/test');
  });
});