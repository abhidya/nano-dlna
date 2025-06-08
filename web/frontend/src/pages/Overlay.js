import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardHeader,
  Box,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Switch,
  FormControlLabel,
  Slider,
  Divider,
  IconButton
} from '@mui/material';
import {
  GridOn as OverlayIcon,
  Upload as UploadIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon
} from '@mui/icons-material';

function Overlay() {
  const [selectedDevice, setSelectedDevice] = useState('');
  const [overlayImage, setOverlayImage] = useState(null);
  const [overlaySettings, setOverlaySettings] = useState({
    opacity: 0.5,
    scale: 1.0,
    rotation: 0,
    offsetX: 0,
    offsetY: 0,
    enabled: false
  });
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // Placeholder for fetching available devices
    // This would typically load from your API
    setDevices([
      { id: '1', name: 'Living Room TV' },
      { id: '2', name: 'Bedroom Display' },
      { id: '3', name: 'Projector' }
    ]);
  }, []);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setOverlayImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSettingChange = (setting, value) => {
    setOverlaySettings(prev => ({
      ...prev,
      [setting]: value
    }));
  };

  const handleApplyOverlay = () => {
    setLoading(true);
    // Placeholder for API call to apply overlay
    setTimeout(() => {
      setLoading(false);
      console.log('Applying overlay with settings:', overlaySettings);
    }, 1000);
  };

  const handleStopOverlay = () => {
    setOverlaySettings(prev => ({ ...prev, enabled: false }));
    // Placeholder for API call to stop overlay
    console.log('Stopping overlay');
  };

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h4" gutterBottom>
            <OverlayIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Overlay Projection
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Project overlay images onto your display devices with customizable settings.
          </Typography>
        </Paper>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader
            title="Overlay Image"
            action={
              <IconButton component="label">
                <UploadIcon />
                <input
                  type="file"
                  hidden
                  accept="image/*"
                  onChange={handleImageUpload}
                />
              </IconButton>
            }
          />
          <CardContent>
            {overlayImage ? (
              <Box
                component="img"
                src={overlayImage}
                alt="Overlay preview"
                sx={{
                  width: '100%',
                  maxHeight: 300,
                  objectFit: 'contain',
                  border: '1px solid #ccc',
                  borderRadius: 1
                }}
              />
            ) : (
              <Box
                sx={{
                  height: 200,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  bgcolor: 'grey.100',
                  borderRadius: 1
                }}
              >
                <Typography color="text.secondary">
                  No overlay image selected
                </Typography>
              </Box>
            )}
            
            <Button
              variant="contained"
              component="label"
              fullWidth
              sx={{ mt: 2 }}
              startIcon={<UploadIcon />}
            >
              Upload Overlay Image
              <input
                type="file"
                hidden
                accept="image/*"
                onChange={handleImageUpload}
              />
            </Button>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardHeader
            title="Overlay Settings"
            avatar={<SettingsIcon />}
          />
          <CardContent>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>Target Device</InputLabel>
              <Select
                value={selectedDevice}
                onChange={(e) => setSelectedDevice(e.target.value)}
                label="Target Device"
              >
                <MenuItem value="">
                  <em>Select a device</em>
                </MenuItem>
                {devices.map(device => (
                  <MenuItem key={device.id} value={device.id}>
                    {device.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Divider sx={{ my: 2 }} />

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>Opacity</Typography>
              <Slider
                value={overlaySettings.opacity}
                onChange={(e, value) => handleSettingChange('opacity', value)}
                min={0}
                max={1}
                step={0.1}
                valueLabelDisplay="auto"
                marks={[
                  { value: 0, label: '0%' },
                  { value: 0.5, label: '50%' },
                  { value: 1, label: '100%' }
                ]}
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>Scale</Typography>
              <Slider
                value={overlaySettings.scale}
                onChange={(e, value) => handleSettingChange('scale', value)}
                min={0.1}
                max={2}
                step={0.1}
                valueLabelDisplay="auto"
                marks={[
                  { value: 0.5, label: '0.5x' },
                  { value: 1, label: '1x' },
                  { value: 1.5, label: '1.5x' },
                  { value: 2, label: '2x' }
                ]}
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Typography gutterBottom>Rotation (degrees)</Typography>
              <Slider
                value={overlaySettings.rotation}
                onChange={(e, value) => handleSettingChange('rotation', value)}
                min={-180}
                max={180}
                step={1}
                valueLabelDisplay="auto"
                marks={[
                  { value: -180, label: '-180°' },
                  { value: 0, label: '0°' },
                  { value: 180, label: '180°' }
                ]}
              />
            </Box>

            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6}>
                <TextField
                  label="Offset X"
                  type="number"
                  value={overlaySettings.offsetX}
                  onChange={(e) => handleSettingChange('offsetX', parseInt(e.target.value) || 0)}
                  fullWidth
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  label="Offset Y"
                  type="number"
                  value={overlaySettings.offsetY}
                  onChange={(e) => handleSettingChange('offsetY', parseInt(e.target.value) || 0)}
                  fullWidth
                />
              </Grid>
            </Grid>

            <FormControlLabel
              control={
                <Switch
                  checked={overlaySettings.enabled}
                  onChange={(e) => handleSettingChange('enabled', e.target.checked)}
                />
              }
              label="Enable Overlay"
            />
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              color="primary"
              size="large"
              startIcon={<PlayIcon />}
              onClick={handleApplyOverlay}
              disabled={!selectedDevice || !overlayImage || loading}
            >
              Apply Overlay
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              size="large"
              startIcon={<StopIcon />}
              onClick={handleStopOverlay}
              disabled={!overlaySettings.enabled}
            >
              Stop Overlay
            </Button>
          </Box>
        </Paper>
      </Grid>

      {overlaySettings.enabled && (
        <Grid item xs={12}>
          <Alert severity="success">
            Overlay is currently active on the selected device.
          </Alert>
        </Grid>
      )}
    </Grid>
  );
}

export default Overlay;