import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import Renderer from '../pages/Renderer';
import { rendererApi } from '../services/api';

// Mock the API
jest.mock('../services/api', () => ({
  rendererApi: {
    listProjectors: jest.fn(),
    listScenes: jest.fn(),
    listRenderers: jest.fn(),
    startRenderer: jest.fn(),
    stopRenderer: jest.fn(),
    getRendererStatus: jest.fn(),
    discoverAirPlayDevices: jest.fn(),
    listAirPlayDevices: jest.fn(),
    getAllAirPlayDevices: jest.fn(),
  }
}));

describe('AirPlay Discovery UI', () => {
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks();
    
    // Setup default mock responses
    rendererApi.listProjectors.mockResolvedValue({
      data: { data: { projectors: [] } }
    });
    rendererApi.listScenes.mockResolvedValue({
      data: { data: { scenes: [] } }
    });
    rendererApi.listRenderers.mockResolvedValue({
      data: { data: { renderers: [] } }
    });
    rendererApi.discoverAirPlayDevices.mockResolvedValue({
      data: { data: { devices: [] } }
    });
    rendererApi.listAirPlayDevices.mockResolvedValue({
      data: { data: { devices: [] } }
    });
    rendererApi.getAllAirPlayDevices.mockResolvedValue({
      data: { data: { devices: [] } }
    });
  });

  test('renders AirPlay discovery button', async () => {
    render(
      <BrowserRouter>
        <Renderer />
      </BrowserRouter>
    );
    
    // Wait for the component to load
    await waitFor(() => {
      expect(rendererApi.listProjectors).toHaveBeenCalled();
    });
    
    // Check if the AirPlay discovery button is rendered
    const discoveryButton = screen.getByText('Discover AirPlay Devices');
    expect(discoveryButton).toBeInTheDocument();
  });

  test('opens AirPlay discovery dialog when button is clicked', async () => {
    render(
      <BrowserRouter>
        <Renderer />
      </BrowserRouter>
    );
    
    // Wait for the component to load
    await waitFor(() => {
      expect(rendererApi.listProjectors).toHaveBeenCalled();
    });
    
    // Click the discovery button
    const discoveryButton = screen.getByText('Discover AirPlay Devices');
    fireEvent.click(discoveryButton);
    
    // Check if the dialog is opened
    const dialogTitle = screen.getByText('AirPlay Devices');
    expect(dialogTitle).toBeInTheDocument();
    
    // Check if the API calls were made
    expect(rendererApi.discoverAirPlayDevices).toHaveBeenCalled();
    expect(rendererApi.listAirPlayDevices).toHaveBeenCalled();
    expect(rendererApi.getAllAirPlayDevices).toHaveBeenCalled();
  });

  test('displays AirPlay devices when discovered', async () => {
    // Mock AirPlay devices
    const mockDevices = [
      { id: '1', name: 'Apple TV', type: 'AppleTV', status: 'available', source: 'network' },
      { id: '2', name: 'Living Room TV', type: 'TV', status: 'available', source: 'system' }
    ];
    
    rendererApi.getAllAirPlayDevices.mockResolvedValue({
      data: { data: { devices: mockDevices } }
    });
    
    render(
      <BrowserRouter>
        <Renderer />
      </BrowserRouter>
    );
    
    // Wait for the component to load
    await waitFor(() => {
      expect(rendererApi.listProjectors).toHaveBeenCalled();
    });
    
    // Click the discovery button
    const discoveryButton = screen.getByText('Discover AirPlay Devices');
    fireEvent.click(discoveryButton);
    
    // Wait for the devices to load
    await waitFor(() => {
      expect(rendererApi.getAllAirPlayDevices).toHaveBeenCalled();
    });
    
    // Check if the devices are displayed
    const appleTV = screen.getByText('Apple TV');
    expect(appleTV).toBeInTheDocument();
    
    const livingRoomTV = screen.getByText('Living Room TV');
    expect(livingRoomTV).toBeInTheDocument();
  });

  test('refreshes AirPlay devices when refresh button is clicked', async () => {
    render(
      <BrowserRouter>
        <Renderer />
      </BrowserRouter>
    );
    
    // Wait for the component to load
    await waitFor(() => {
      expect(rendererApi.listProjectors).toHaveBeenCalled();
    });
    
    // Click the discovery button
    const discoveryButton = screen.getByText('Discover AirPlay Devices');
    fireEvent.click(discoveryButton);
    
    // Wait for the dialog to open
    await waitFor(() => {
      expect(rendererApi.discoverAirPlayDevices).toHaveBeenCalled();
    });
    
    // Reset the mock calls
    jest.clearAllMocks();
    
    // Click the refresh button
    const refreshButton = screen.getByText('Refresh');
    fireEvent.click(refreshButton);
    
    // Check if the API calls were made again
    await waitFor(() => {
      expect(rendererApi.discoverAirPlayDevices).toHaveBeenCalled();
      expect(rendererApi.listAirPlayDevices).toHaveBeenCalled();
      expect(rendererApi.getAllAirPlayDevices).toHaveBeenCalled();
    });
  });

  test('switches between tabs in AirPlay discovery dialog', async () => {
    // Mock AirPlay devices
    const mockDevices = [
      { id: '1', name: 'Apple TV', type: 'AppleTV', status: 'available', source: 'network' },
      { id: '2', name: 'Living Room TV', type: 'TV', status: 'available', source: 'system' }
    ];
    
    rendererApi.getAllAirPlayDevices.mockResolvedValue({
      data: { data: { devices: mockDevices } }
    });
    
    render(
      <BrowserRouter>
        <Renderer />
      </BrowserRouter>
    );
    
    // Wait for the component to load
    await waitFor(() => {
      expect(rendererApi.listProjectors).toHaveBeenCalled();
    });
    
    // Click the discovery button
    const discoveryButton = screen.getByText('Discover AirPlay Devices');
    fireEvent.click(discoveryButton);
    
    // Wait for the devices to load
    await waitFor(() => {
      expect(rendererApi.getAllAirPlayDevices).toHaveBeenCalled();
    });
    
    // Check if the "All Devices" tab is active by default
    const allDevicesTab = screen.getByText('All Devices');
    expect(allDevicesTab).toBeInTheDocument();
    
    // Click the "Network Discovery" tab
    const networkDiscoveryTab = screen.getByText('Network Discovery');
    fireEvent.click(networkDiscoveryTab);
    
    // Check if the "Network Discovery" tab is active
    expect(networkDiscoveryTab).toBeInTheDocument();
    
    // Click the "System Preferences" tab
    const systemPreferencesTab = screen.getByText('System Preferences');
    fireEvent.click(systemPreferencesTab);
    
    // Check if the "System Preferences" tab is active
    expect(systemPreferencesTab).toBeInTheDocument();
  });

  test('closes AirPlay discovery dialog when close button is clicked', async () => {
    render(
      <BrowserRouter>
        <Renderer />
      </BrowserRouter>
    );
    
    // Wait for the component to load
    await waitFor(() => {
      expect(rendererApi.listProjectors).toHaveBeenCalled();
    });
    
    // Click the discovery button
    const discoveryButton = screen.getByText('Discover AirPlay Devices');
    fireEvent.click(discoveryButton);
    
    // Wait for the dialog to open
    await waitFor(() => {
      expect(rendererApi.discoverAirPlayDevices).toHaveBeenCalled();
    });
    
    // Click the close button
    const closeButton = screen.getByText('Close');
    fireEvent.click(closeButton);
    
    // Check if the dialog is closed
    await waitFor(() => {
      expect(screen.queryByText('AirPlay Devices')).not.toBeInTheDocument();
    });
  });
});
