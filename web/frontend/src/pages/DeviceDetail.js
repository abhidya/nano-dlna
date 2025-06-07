import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardActions,
  CircularProgress,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Typography,
  Alert,
  Snackbar,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Info as InfoIcon,
  Router as RouterIcon,
  Computer as ComputerIcon,
  Link as LinkIcon,
  Movie as MovieIcon
} from '@mui/icons-material';
import { deviceApi } from '../services/api';

function DeviceDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [device, setDevice] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });

  useEffect(() => {
    fetchDevice();
    // Poll for device updates every 5 seconds
    const interval = setInterval(fetchDevice, 5000);
    return () => clearInterval(interval);
  }, [id]);

  const fetchDevice = async () => {
    try {
      setLoading(true);
      const response = await deviceApi.getDevice(id);
      setDevice(response.data);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching device:', err);
      setError('Failed to load device. Please try again later.');
      setLoading(false);
    }
  };

  const handleDeviceAction = async (action) => {
    try {
      if (action === 'pause') {
        await deviceApi.pauseVideo(id);
      } else if (action === 'stop') {
        await deviceApi.stopVideo(id);
      }
      setSnackbar({
        open: true,
        message: `Device ${action} successful`,
        severity: 'success'
      });
      fetchDevice();
    } catch (err) {
      console.error(`Error performing ${action} action:`, err);
      setSnackbar({
        open: true,
        message: `Failed to ${action} device`,
        severity: 'error'
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({
      ...prev,
      open: false
    }));
  };

  if (loading && !device) {
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
        <Button variant="contained" onClick={fetchDevice}>
          Retry
        </Button>
      </Box>
    );
  }

  if (!device) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h6">Device not found</Typography>
        <Button variant="contained" onClick={() => navigate('/devices')}>
          Back to Devices
        </Button>
      </Box>
    );
  }

  return (
    <Grid container spacing={3}>
      {/* Header */}
      <Grid item xs={12}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/devices')}
            sx={{ mr: 2 }}
          >
            Back
          </Button>
          <Typography variant="h4">{device.friendly_name || device.name}</Typography>
        </Box>
        <Divider sx={{ mb: 2 }} />
      </Grid>

      {/* Device Info */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Device Information</Typography>
          <List>
            <ListItem>
              <ListItemIcon>
                <InfoIcon />
              </ListItemIcon>
              <ListItemText 
                primary="Status" 
                secondary={
                  <Chip 
                    label={device.status} 
                    color={device.status === 'connected' ? 'success' : 'default'} 
                    size="small" 
                  />
                } 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <MovieIcon />
              </ListItemIcon>
              <ListItemText 
                primary="Playing" 
                secondary={
                  <Chip 
                    label={device.is_playing ? 'Yes' : 'No'} 
                    color={device.is_playing ? 'success' : 'default'} 
                    size="small" 
                  />
                } 
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <ComputerIcon />
              </ListItemIcon>
              <ListItemText primary="Type" secondary={device.type} />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <RouterIcon />
              </ListItemIcon>
              <ListItemText primary="Hostname" secondary={device.hostname} />
            </ListItem>
            {device.action_url && (
              <ListItem>
                <ListItemIcon>
                  <LinkIcon />
                </ListItemIcon>
                <ListItemText 
                  primary="Action URL" 
                  secondary={device.action_url} 
                  secondaryTypographyProps={{ 
                    sx: { 
                      wordBreak: 'break-all' 
                    } 
                  }} 
                />
              </ListItem>
            )}
            {device.current_video && (
              <>
                <ListItem>
                  <ListItemIcon>
                    <MovieIcon />
                  </ListItemIcon>
                  <ListItemText 
                    primary="Current Video" 
                    secondary={device.current_video.split('/').pop()} 
                    secondaryTypographyProps={{ 
                      sx: { 
                        wordBreak: 'break-all' 
                      } 
                    }} 
                  />
                </ListItem>
                {device.is_playing && device.playback_progress !== null && (
                  <ListItem>
                    <Box sx={{ width: '100%' }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="caption" color="textSecondary">
                          {device.playback_position || "00:00:00"}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {device.playback_duration || "00:00:00"}
                        </Typography>
                      </Box>
                      <Box sx={{ width: '100%', mr: 1 }}>
                        <LinearProgress 
                          variant="determinate" 
                          value={device.playback_progress || 0} 
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                      </Box>
                    </Box>
                  </ListItem>
                )}
              </>
            )}
          </List>
        </Paper>
      </Grid>

      {/* Device Controls */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>Device Controls</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <Button
              variant="contained"
              color="primary"
              startIcon={<PlayIcon />}
              onClick={() => navigate(`/devices/${id}/play`)}
              fullWidth
            >
              Play Video
            </Button>
            {device.is_playing && (
              <>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<PauseIcon />}
                  onClick={() => handleDeviceAction('pause')}
                  fullWidth
                >
                  Pause
                </Button>
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<StopIcon />}
                  onClick={() => handleDeviceAction('stop')}
                  fullWidth
                >
                  Stop
                </Button>
              </>
            )}
          </Box>
        </Paper>
      </Grid>

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

export default DeviceDetail;
