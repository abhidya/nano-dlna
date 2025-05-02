import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  CardHeader,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
  Box,
  Chip,
  Divider,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

function Devices() {
  const navigate = useNavigate();
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [newDevice, setNewDevice] = useState({
    name: '',
    type: 'dlna',
    hostname: '',
    friendly_name: '',
    action_url: '',
  });
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  const [discovering, setDiscovering] = useState(false);

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/api/devices');
      setDevices(response.data.devices);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching devices:', err);
      setError('Failed to load devices. Please try again later.');
      setLoading(false);
    }
  };

  const handleAddDevice = async () => {
    try {
      await axios.post('/api/devices', newDevice);
      setOpenAddDialog(false);
      setNewDevice({
        name: '',
        type: 'dlna',
        hostname: '',
        friendly_name: '',
        action_url: '',
      });
      setSnackbar({
        open: true,
        message: 'Device added successfully',
        severity: 'success'
      });
      fetchDevices();
    } catch (err) {
      console.error('Error adding device:', err);
      setSnackbar({
        open: true,
        message: 'Failed to add device',
        severity: 'error'
      });
    }
  };

  const handleDeleteDevice = async () => {
    try {
      await axios.delete(`/api/devices/${selectedDevice.id}`);
      setOpenDeleteDialog(false);
      setSelectedDevice(null);
      setSnackbar({
        open: true,
        message: 'Device deleted successfully',
        severity: 'success'
      });
      fetchDevices();
    } catch (err) {
      console.error('Error deleting device:', err);
      setSnackbar({
        open: true,
        message: 'Failed to delete device',
        severity: 'error'
      });
    }
  };

  const handleDeviceAction = async (deviceId, action) => {
    try {
      await axios.post(`/api/devices/${deviceId}/${action}`);
      setSnackbar({
        open: true,
        message: `Device ${action} successful`,
        severity: 'success'
      });
      fetchDevices();
    } catch (err) {
      console.error(`Error performing ${action} action:`, err);
      setSnackbar({
        open: true,
        message: `Failed to ${action} device`,
        severity: 'error'
      });
    }
  };

  const handleDiscoverDevices = async () => {
    try {
      setDiscovering(true);
      const response = await axios.get('/api/devices/discover');
      setSnackbar({
        open: true,
        message: `Device discovery completed. Found ${response.data.total} devices.`,
        severity: 'success'
      });
      fetchDevices();
    } catch (err) {
      console.error('Error discovering devices:', err);
      setSnackbar({
        open: true,
        message: 'Failed to discover devices',
        severity: 'error'
      });
    } finally {
      setDiscovering(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewDevice(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({
      ...prev,
      open: false
    }));
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error" variant="h6">{error}</Typography>
        <Button variant="contained" onClick={fetchDevices}>
          Retry
        </Button>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Header */}
      <Grid item xs={12}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h4">Devices</Typography>
          <Box>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={fetchDevices}
              sx={{ mr: 1 }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              color="secondary"
              startIcon={<AddIcon />}
              onClick={() => setOpenAddDialog(true)}
            >
              Add Device
            </Button>
          </Box>
        </Box>
        <Divider sx={{ mb: 2 }} />
      </Grid>

      {/* Discover Devices */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Discover DLNA Devices</Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={discovering ? <CircularProgress size={20} color="inherit" /> : <RefreshIcon />}
              onClick={handleDiscoverDevices}
              disabled={discovering}
            >
              {discovering ? 'Discovering...' : 'Discover Devices'}
            </Button>
          </Box>
          <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
            Scan your network for DLNA devices. This may take a few moments.
          </Typography>
        </Paper>
      </Grid>

      {/* Device List */}
      {devices.length === 0 ? (
        <Grid item xs={12}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              No devices found
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Add a device manually or discover devices on your network
            </Typography>
          </Paper>
        </Grid>
      ) : (
        devices.map(device => (
          <Grid item xs={12} sm={6} md={4} key={device.id}>
            <Card>
              <CardHeader
                title={device.friendly_name}
                subheader={`Type: ${device.type}`}
                action={
                  <IconButton onClick={() => { setSelectedDevice(device); setOpenDeleteDialog(true); }}>
                    <DeleteIcon />
                  </IconButton>
                }
              />
              <CardContent>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Status: <Chip 
                    label={device.status} 
                    color={device.status === 'connected' ? 'success' : 'default'} 
                    size="small" 
                  />
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Playing: <Chip 
                    label={device.is_playing ? 'Yes' : 'No'} 
                    color={device.is_playing ? 'success' : 'default'} 
                    size="small" 
                  />
                </Typography>
                {device.current_video && (
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Current Video: {device.current_video.split('/').pop()}
                  </Typography>
                )}
                <Typography variant="body2" color="textSecondary">
                  Hostname: {device.hostname}
                </Typography>
              </CardContent>
              <CardActions>
                {device.is_playing ? (
                  <>
                    <Button 
                      size="small" 
                      color="primary"
                      onClick={() => handleDeviceAction(device.id, 'pause')}
                      startIcon={<PauseIcon />}
                    >
                      Pause
                    </Button>
                    <Button 
                      size="small" 
                      color="secondary"
                      onClick={() => handleDeviceAction(device.id, 'stop')}
                      startIcon={<StopIcon />}
                    >
                      Stop
                    </Button>
                  </>
                ) : (
                  <Button 
                    size="small" 
                    color="primary"
                    onClick={() => navigate(`/devices/${device.id}`)}
                  >
                    Details
                  </Button>
                )}
                <Button 
                  size="small" 
                  color="primary"
                  onClick={() => navigate(`/devices/${device.id}/play`)}
                  startIcon={<PlayIcon />}
                >
                  Play Video
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))
      )}

      {/* Add Device Dialog */}
      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)}>
        <DialogTitle>Add New Device</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter the details of the device you want to add.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Device Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newDevice.name}
            onChange={handleInputChange}
            sx={{ mb: 2 }}
          />
          <FormControl fullWidth variant="outlined" sx={{ mb: 2 }}>
            <InputLabel>Device Type</InputLabel>
            <Select
              name="type"
              value={newDevice.type}
              onChange={handleInputChange}
              label="Device Type"
            >
              <MenuItem value="dlna">DLNA</MenuItem>
              <MenuItem value="transcreen">Transcreen</MenuItem>
            </Select>
          </FormControl>
          <TextField
            margin="dense"
            name="hostname"
            label="Hostname/IP"
            type="text"
            fullWidth
            variant="outlined"
            value={newDevice.hostname}
            onChange={handleInputChange}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="friendly_name"
            label="Friendly Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newDevice.friendly_name}
            onChange={handleInputChange}
            sx={{ mb: 2 }}
          />
          {newDevice.type === 'dlna' && (
            <TextField
              margin="dense"
              name="action_url"
              label="Action URL (DLNA only)"
              type="text"
              fullWidth
              variant="outlined"
              value={newDevice.action_url}
              onChange={handleInputChange}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>Cancel</Button>
          <Button onClick={handleAddDevice} variant="contained" color="primary">Add</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Device Dialog */}
      <Dialog open={openDeleteDialog} onClose={() => setOpenDeleteDialog(false)}>
        <DialogTitle>Delete Device</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the device "{selectedDevice?.friendly_name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDeleteDevice} variant="contained" color="error">Delete</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Grid>
  );
}

export default Devices;
