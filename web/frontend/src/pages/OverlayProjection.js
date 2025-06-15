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
    List,
    ListItem,
    ListItemText,
    ListItemIcon,
    ListItemSecondaryAction,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    Chip,
    CircularProgress,
    Tooltip,
    Slider,
    Stack
} from '@mui/material';
import {
    Add as AddIcon,
    Delete as DeleteIcon,
    Videocam as VideoIcon,
    Launch as LaunchIcon,
    Settings as SettingsIcon,
    WbSunny as WeatherIcon,
    Schedule as TimeIcon,
    DirectionsBus as TransitIcon,
    Visibility as VisibilityIcon,
    VisibilityOff as VisibilityOffIcon,
    NightsStay as NightsStayIcon,
    Brightness4 as BrightnessIcon,
    LightMode as LightModeIcon,
    DarkMode as DarkModeIcon,
    Sync as SyncIcon
} from '@mui/icons-material';
import { api } from '../services/api';

function OverlayProjection() {
    const [videos, setVideos] = useState([]);
    const [selectedVideo, setSelectedVideo] = useState(null);
    const [overlayConfigs, setOverlayConfigs] = useState([]);
    const [selectedConfig, setSelectedConfig] = useState(null);
    const [projectionWindow, setProjectionWindow] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [apiConfigDialog, setApiConfigDialog] = useState(false);
    const [configNameDialog, setConfigNameDialog] = useState(false);
    const [newConfigName, setNewConfigName] = useState('');
    const [brightness, setBrightness] = useState(100);
    const [brightnessLoading, setBrightnessLoading] = useState(false);
    
    useEffect(() => {
        fetchVideos();
        fetchBrightness();
    }, []);
    
    useEffect(() => {
        if (selectedVideo) {
            fetchOverlayConfigs(selectedVideo.id);
        }
    }, [selectedVideo]);
    
    const fetchVideos = async () => {
        try {
            const response = await api.get('/videos');
            console.log("Videos API response:", response.data);
            setVideos(response.data.videos);
        } catch (error) {
            console.error('Error fetching videos:', error);
            setError('Failed to load videos');
        }
    };
    
    const fetchOverlayConfigs = async (videoId) => {
        try {
            const response = await api.get(`/overlay/configs?video_id=${videoId}`);
            setOverlayConfigs(response.data);
        } catch (error) {
            console.error('Error fetching overlay configs:', error);
            // If endpoint doesn't exist yet, just set empty array
            setOverlayConfigs([]);
        }
    };
    
    const fetchBrightness = async () => {
        try {
            const response = await api.get('/overlay/brightness');
            setBrightness(response.data.brightness);
        } catch (error) {
            console.error('Error fetching brightness:', error);
        }
    };
    
    const updateBrightness = async (value) => {
        setBrightness(value);
        setBrightnessLoading(true);
        try {
            await api.post(`/overlay/brightness?brightness=${value}`);
        } catch (error) {
            console.error('Error updating brightness:', error);
            setError('Failed to update brightness');
        } finally {
            setBrightnessLoading(false);
        }
    };
    
    const createNewConfig = async () => {
        const newConfig = {
            name: newConfigName || `Config ${new Date().toLocaleString()}`,
            video_id: selectedVideo.id,
            video_transform: { x: 0, y: 0, scale: 1, rotation: 0 },
            widgets: [
                {
                    id: 'weather-1',
                    type: 'weather',
                    position: { x: 50, y: 50 },
                    size: { width: 400, height: 200 },
                    config: {
                        city: 'San Francisco',
                        units: 'metric'
                    },
                    visible: true
                },
                {
                    id: 'time-1',
                    type: 'time',
                    position: { x: 1470, y: 50 },
                    size: { width: 300, height: 100 },
                    config: {
                        format: '24h',
                        showSeconds: true
                    },
                    visible: true
                },
                {
                    id: 'transit-1',
                    type: 'transit',
                    position: { x: 50, y: 830 },
                    size: { width: 400, height: 200 },
                    config: {
                        stopName: 'Carl St & Stanyan St',
                        routeFilter: 'N Judah'
                    },
                    visible: true
                },
                {
                    id: 'lights-1',
                    type: 'lights',
                    position: { x: 50, y: 950 },
                    size: { width: 120, height: 60 },
                    config: {},
                    visible: true,
                    rotation: 0
                }
            ],
            api_configs: {
                weather_api_key: localStorage.getItem('weather_api_key') || '',
                transit_stop_id: localStorage.getItem('transit_stop_id') || '13915',
                timezone: 'America/Los_Angeles'
            }
        };
        
        try {
            const response = await api.post('/overlay/configs', newConfig);
            setOverlayConfigs([...overlayConfigs, response.data]);
            setSelectedConfig(response.data);
            setConfigNameDialog(false);
            setNewConfigName('');
        } catch (error) {
            console.error('Error creating config:', error);
            setError('Failed to create configuration');
        }
    };
    
    const updateConfig = async (config) => {
        try {
            // Extract only the fields that the backend expects
            const updateData = {
                name: config.name,
                video_transform: config.video_transform,
                widgets: config.widgets,
                api_configs: config.api_configs
            };
            
            const response = await api.put(`/overlay/configs/${config.id}`, updateData);
            const updatedConfigs = overlayConfigs.map(c => 
                c.id === config.id ? response.data : c
            );
            setOverlayConfigs(updatedConfigs);
            setSelectedConfig(response.data);
        } catch (error) {
            console.error('Error updating config:', error);
        }
    };
    
    const deleteConfig = async (configId) => {
        try {
            await api.delete(`/overlay/configs/${configId}`);
            setOverlayConfigs(overlayConfigs.filter(c => c.id !== configId));
            if (selectedConfig?.id === configId) {
                setSelectedConfig(null);
            }
        } catch (error) {
            console.error('Error deleting config:', error);
            setError('Failed to delete configuration');
        }
    };
    
    const launchProjection = async () => {
        if (!selectedVideo || !selectedConfig) return;
        
        setLoading(true);
        setError('');
        
        try {
            // Close existing window if any
            if (projectionWindow && !projectionWindow.closed) {
                projectionWindow.close();
            }
            
            // Open projection window
            const projWindow = window.open(
                '/backend-static/overlay_window.html',
                'overlay_projection',
                'width=1920,height=1080'
            );
            
            setProjectionWindow(projWindow);
            
            // Function to send configuration
            const sendConfiguration = async () => {
                if (projWindow.closed) return; // Don't send if window was closed
                
                try {
                    // Get streaming URL from backend
                    const streamResponse = await api.post('/overlay/stream', {
                        video_id: selectedVideo.id,
                        config_id: selectedConfig.id
                    });
                    
                    projWindow.postMessage({
                        type: 'init',
                        config: selectedConfig,
                        streamingUrl: streamResponse.data.streaming_url,
                        videoPath: selectedVideo.file_path
                    }, '*');
                } catch (error) {
                    console.error('Error getting streaming URL:', error);
                    // Fallback to direct URL if backend fails
                    let streamingUrl = '';
                    if (selectedVideo && selectedVideo.file_path) {
                        streamingUrl = `http://localhost:9000/file_video/${selectedVideo.file_path.split('/').pop()}`;
                    }
                    projWindow.postMessage({
                        type: 'init',
                        config: selectedConfig,
                        streamingUrl: streamingUrl,
                        videoPath: selectedVideo ? selectedVideo.file_path : ''
                    }, '*');
                }
            };
            
            // Send config immediately and then retry to ensure delivery
            setTimeout(sendConfiguration, 100);
            setTimeout(sendConfiguration, 500);
            setTimeout(sendConfiguration, 1000);
            
            setLoading(false);
        } catch (error) {
            console.error('Error launching projection:', error);
            setError('Failed to launch projection window');
            setLoading(false);
        }
    };
    
    // Listen for updates from projection window
    useEffect(() => {
        const handleMessage = async (event) => {
            if (event.data.type === 'updateConfig' && selectedConfig) {
                updateConfig(event.data.config);
            }
        };
        
        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [selectedConfig]);
    
    const toggleWidgetVisibility = (widgetId) => {
        if (!selectedConfig) return;
        
        const updatedConfig = {
            ...selectedConfig,
            widgets: selectedConfig.widgets.map(w => 
                w.id === widgetId ? { ...w, visible: !w.visible } : w
            )
        };
        updateConfig(updatedConfig);
    };
    
    const updateApiConfig = (key, value) => {
        if (!selectedConfig) return;
        
        const updatedConfig = {
            ...selectedConfig,
            api_configs: {
                ...selectedConfig.api_configs,
                [key]: value
            }
        };
        updateConfig(updatedConfig);
        
        // Save to localStorage for persistence
        localStorage.setItem(key, value);
    };
    
    const getWidgetIcon = (type) => {
        switch(type) {
            case 'weather': return <WeatherIcon />;
            case 'time': return <TimeIcon />;
            case 'transit': return <TransitIcon />;
            case 'lights': return <NightsStayIcon />;
            default: return <SettingsIcon />;
        }
    };
    
    return (
        <Grid container spacing={3}>
            <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h4" gutterBottom>
                        Overlay Projection
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Select a video and configure live information overlays for projection via AirPlay
                    </Typography>
                </Paper>
            </Grid>
            
            {/* Video Selection */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardHeader 
                        title="Video Selection"
                        avatar={<VideoIcon />}
                    />
                    <CardContent>
                        <FormControl fullWidth>
                            <InputLabel>Select Video</InputLabel>
                            <Select
                                value={selectedVideo?.id || ''}
                                onChange={(e) => {
                                    const video = videos.find(v => v.id === e.target.value);
                                    setSelectedVideo(video);
                                    setSelectedConfig(null);
                                }}
                                label="Select Video"
                            >
                                <MenuItem value="">
                                    <em>Choose a video...</em>
                                </MenuItem>
                                {videos.map(video => (
                                    <MenuItem key={video.id} value={video.id}>
                                        {video.name}
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                        
                        {selectedVideo && (
                            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.100', borderRadius: 1 }}>
                                <Typography variant="body2">
                                    <strong>File:</strong> {selectedVideo.file_path}
                                </Typography>
                                <Typography variant="body2">
                                    <strong>Duration:</strong> {selectedVideo.duration || 'Unknown'}
                                </Typography>
                            </Box>
                        )}
                    </CardContent>
                </Card>
            </Grid>
            
            {/* Configuration Selection */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardHeader 
                        title="Overlay Configurations"
                        action={
                            <Tooltip title="Create new configuration">
                                <span>
                                    <IconButton 
                                        onClick={() => setConfigNameDialog(true)}
                                        disabled={!selectedVideo}
                                    >
                                        <AddIcon />
                                    </IconButton>
                                </span>
                            </Tooltip>
                        }
                    />
                    <CardContent>
                        {!selectedVideo ? (
                            <Alert severity="info">
                                Select a video to view configurations
                            </Alert>
                        ) : overlayConfigs.length === 0 ? (
                            <Alert severity="info">
                                No configurations yet. Click + to create one.
                            </Alert>
                        ) : (
                            <List>
                                {overlayConfigs.map(config => (
                                    <ListItem
                                        key={config.id}
                                        button
                                        selected={selectedConfig?.id === config.id}
                                        onClick={() => setSelectedConfig(config)}
                                    >
                                        <ListItemText
                                            primary={config.name}
                                            secondary={`${config.widgets.filter(w => w.visible).length} active widgets`}
                                        />
                                        <ListItemSecondaryAction>
                                            <IconButton
                                                edge="end"
                                                onClick={() => deleteConfig(config.id)}
                                            >
                                                <DeleteIcon />
                                            </IconButton>
                                        </ListItemSecondaryAction>
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </CardContent>
                </Card>
            </Grid>
            
            {/* Widget Configuration */}
            {selectedConfig && (
                <Grid item xs={12}>
                    <Card>
                        <CardHeader 
                            title="Widget Configuration"
                            action={
                                <Button
                                    startIcon={<SettingsIcon />}
                                    onClick={() => setApiConfigDialog(true)}
                                >
                                    API Settings
                                </Button>
                            }
                        />
                        <CardContent>
                            <List>
                                {selectedConfig.widgets.map(widget => (
                                    <ListItem key={widget.id}>
                                        <ListItemIcon>
                                            {getWidgetIcon(widget.type)}
                                        </ListItemIcon>
                                        <ListItemText
                                            primary={widget.type.charAt(0).toUpperCase() + widget.type.slice(1)}
                                            secondary={
                                                <Box>
                                                    Position: ({widget.position.x}, {widget.position.y}) • 
                                                    Size: {widget.size.width}x{widget.size.height}
                                                </Box>
                                            }
                                        />
                                        <ListItemSecondaryAction>
                                            <IconButton
                                                onClick={() => toggleWidgetVisibility(widget.id)}
                                                color={widget.visible ? 'primary' : 'default'}
                                            >
                                                {widget.visible ? <VisibilityIcon /> : <VisibilityOffIcon />}
                                            </IconButton>
                                        </ListItemSecondaryAction>
                                    </ListItem>
                                ))}
                            </List>
                        </CardContent>
                    </Card>
                </Grid>
            )}
            
            {/* Launch Controls */}
            <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                    {/* Brightness Control */}
                    <Box sx={{ mb: 4 }}>
                        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <BrightnessIcon />
                            Brightness Control
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            Adjust brightness for all overlay projections
                        </Typography>
                        
                        <Box sx={{ px: 2 }}>
                            <Stack spacing={2} direction="row" sx={{ mb: 2 }} alignItems="center">
                                <DarkModeIcon />
                                <Slider
                                    value={brightness}
                                    onChange={(e, value) => updateBrightness(value)}
                                    aria-labelledby="brightness-slider"
                                    valueLabelDisplay="auto"
                                    step={5}
                                    marks={[
                                        { value: 0, label: '0%' },
                                        { value: 25, label: '25%' },
                                        { value: 50, label: '50%' },
                                        { value: 75, label: '75%' },
                                        { value: 100, label: '100%' }
                                    ]}
                                    min={0}
                                    max={100}
                                    disabled={brightnessLoading}
                                    sx={{
                                        '& .MuiSlider-valueLabel': {
                                            backgroundColor: 'primary.main',
                                        }
                                    }}
                                />
                                <LightModeIcon />
                            </Stack>
                            
                            <Stack direction="row" spacing={1} justifyContent="center">
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={() => updateBrightness(0)}
                                    disabled={brightnessLoading}
                                >
                                    Lights Off
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={() => updateBrightness(25)}
                                    disabled={brightnessLoading}
                                >
                                    Dim
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={() => updateBrightness(75)}
                                    disabled={brightnessLoading}
                                >
                                    Normal
                                </Button>
                                <Button
                                    variant="outlined"
                                    size="small"
                                    onClick={() => updateBrightness(100)}
                                    disabled={brightnessLoading}
                                >
                                    Full
                                </Button>
                            </Stack>
                        </Box>
                    </Box>
                    
                    {/* Sync Button */}
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'center' }}>
                        <Button
                            variant="outlined"
                            startIcon={<SyncIcon />}
                            onClick={async () => {
                                try {
                                    await api.post('/overlay/sync', null, {
                                        params: {
                                            triggered_by: 'manual',
                                            video_name: selectedVideo?.name
                                        }
                                    });
                                    // Visual feedback
                                    setError('');
                                } catch (error) {
                                    console.error('Sync error:', error);
                                    setError('Failed to sync overlays');
                                }
                            }}
                        >
                            Sync All Overlays
                        </Button>
                    </Box>
                    
                    {/* Launch Button */}
                    <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', alignItems: 'center' }}>
                        <Button
                            variant="contained"
                            color="primary"
                            size="large"
                            startIcon={loading ? <CircularProgress size={20} /> : <LaunchIcon />}
                            onClick={launchProjection}
                            disabled={!selectedVideo || !selectedConfig || loading}
                        >
                            Launch Projection Window
                        </Button>
                        
                        {projectionWindow && !projectionWindow.closed && (
                            <Chip
                                label="Projection Active"
                                color="success"
                                onDelete={() => {
                                    projectionWindow.close();
                                    setProjectionWindow(null);
                                }}
                            />
                        )}
                    </Box>
                    
                    {error && (
                        <Alert severity="error" sx={{ mt: 2 }}>
                            {error}
                        </Alert>
                    )}
                    
                    <Alert severity="info" sx={{ mt: 2 }}>
                        After launching, use AirPlay to extend the projection window to your projector
                    </Alert>
                </Paper>
            </Grid>
            
            {/* Config Name Dialog */}
            <Dialog open={configNameDialog} onClose={() => setConfigNameDialog(false)}>
                <DialogTitle>New Configuration</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Configuration Name"
                        fullWidth
                        variant="outlined"
                        value={newConfigName}
                        onChange={(e) => setNewConfigName(e.target.value)}
                        placeholder="e.g., Living Room Display"
                    />
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfigNameDialog(false)}>Cancel</Button>
                    <Button onClick={createNewConfig} variant="contained">Create</Button>
                </DialogActions>
            </Dialog>
            
            {/* API Config Dialog */}
            <Dialog open={apiConfigDialog} onClose={() => setApiConfigDialog(false)} maxWidth="sm" fullWidth>
                <DialogTitle>API Configuration</DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
                        <TextField
                            label="Weather API Key (OpenWeatherMap)"
                            fullWidth
                            value={selectedConfig?.api_configs?.weather_api_key || ''}
                            onChange={(e) => updateApiConfig('weather_api_key', e.target.value)}
                            helperText="Get your API key from openweathermap.org"
                        />
                        <TextField
                            label="Transit Stop ID"
                            fullWidth
                            value={selectedConfig?.api_configs?.transit_stop_id || ''}
                            onChange={(e) => updateApiConfig('transit_stop_id', e.target.value)}
                            helperText="e.g., 13915 for Carl St & Stanyan St"
                        />
                        <TextField
                            label="Timezone"
                            fullWidth
                            value={selectedConfig?.api_configs?.timezone || 'America/Los_Angeles'}
                            onChange={(e) => updateApiConfig('timezone', e.target.value)}
                        />
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setApiConfigDialog(false)}>Close</Button>
                </DialogActions>
            </Dialog>
        </Grid>
    );
}

export default OverlayProjection;
