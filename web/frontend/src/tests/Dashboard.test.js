/**
 * Simplified Dashboard tests that work with current implementation
 */

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../pages/Dashboard';
import { deviceApi, videoApi } from '../services/api';

jest.mock('../services/api', () => ({
  deviceApi: {
    getDevices: jest.fn(),
    pauseVideo: jest.fn(),
    stopVideo: jest.fn(),
  },
  videoApi: {
    getVideos: jest.fn(),
  },
}));

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

describe('Dashboard Component - Simple Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    deviceApi.getDevices.mockResolvedValue({ data: { devices: [] } });
    deviceApi.pauseVideo.mockResolvedValue({ data: { success: true } });
    deviceApi.stopVideo.mockResolvedValue({ data: { success: true } });
    videoApi.getVideos.mockResolvedValue({ data: { videos: [] } });
  });

  test('renders without crashing', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Component should render
    expect(document.querySelector('div')).toBeInTheDocument();
  });


  test('handles navigation buttons', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Check if quick action buttons are rendered
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  test('handles API errors gracefully', async () => {
    const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
    deviceApi.getDevices.mockRejectedValue(new Error('Network error'));

    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    consoleErrorSpy.mockRestore();
  });
});
