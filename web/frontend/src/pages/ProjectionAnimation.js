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
    List,
    ListItem,
    ListItemText,
    ListItemSecondaryAction,
    IconButton,
    Dialog,
    DialogTitle,
    DialogContent,
    DialogActions,
    TextField,
    Select,
    MenuItem,
    FormControl,
    InputLabel,
    CircularProgress,
    Chip,
    Divider,
    Collapse,
    Slider,
    Stack,
    Tooltip,
} from '@mui/material';
import {
    CloudUpload as UploadIcon,
    Delete as DeleteIcon,
    PlayArrow as PlayIcon,
    Add as AddIcon,
    Videocam as VideoIcon,
    Animation as AnimationIcon,
    Code as CodeIcon,
    Link as LinkIcon,
    Launch as LaunchIcon,
    Save as SaveIcon,
    ContentCopy as CopyIcon,
    ExpandMore as ExpandMoreIcon,
    ExpandLess as ExpandLessIcon,
    Settings as SettingsIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

function ProjectionAnimation() {
    const [mask, setMask] = useState(null);
    const [zones, setZones] = useState([]);
    const [animations, setAnimations] = useState([]);
    const [videos, setVideos] = useState([]);
    const [zoneAssignments, setZoneAssignments] = useState({});
    const [zoneTransforms, setZoneTransforms] = useState({});
    const [expandedZones, setExpandedZones] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [codePenDialog, setCodePenDialog] = useState(false);
    const [codePenUrl, setCodePenUrl] = useState('');
    const [projectionWindow, setProjectionWindow] = useState(null);
    
    // Configuration management state
    const [projectionConfigs, setProjectionConfigs] = useState([]);
    const [selectedConfig, setSelectedConfig] = useState(null);
    const [configNameDialog, setConfigNameDialog] = useState(false);
    const [newConfigName, setNewConfigName] = useState('');

    // Predefined animation library
    const animationLibrary = [
        {
            id: 'neural_noise',
            name: 'Neural Noise',
            description: 'Flowing neural network patterns',
            dataInputs: ['weather'],
            thumbnail: '🧠',
        },
        {
            id: 'moving_clouds',
            name: 'Moving Clouds',
            description: 'Drifting cloud layers',
            dataInputs: ['weather'],
            thumbnail: '☁️',
        },
        {
            id: 'spectrum_bars',
            name: 'Spectrum Bars',
            description: 'Animated spectrum visualization',
            dataInputs: ['transit'],
            thumbnail: '📊',
        },
        {
            id: 'webgl_flowers',
            name: 'WebGL Flowers',
            description: 'Blooming flower patterns',
            dataInputs: ['weather', 'transit'],
            thumbnail: '🌸',
        },
        {
            id: 'gradient_bubbles',
            name: 'Gradient Bubbles',
            description: 'Floating gradient orbs',
            dataInputs: ['weather'],
            thumbnail: '🫧',
        },
        {
            id: 'milk_physics',
            name: 'Milk Physics',
            description: 'Liquid particle simulation',
            dataInputs: ['weather'],
            thumbnail: '🥛',
        },
        {
            id: 'rainstorm',
            name: 'Rainstorm',
            description: 'Weather-driven rain effects',
            dataInputs: ['weather'],
            thumbnail: '🌧️',
        },
        {
            id: 'segment_clock',
            name: '7-Segment Clock',
            description: 'Digital time display',
            dataInputs: ['weather'],
            thumbnail: '🕐',
        },
        {
            id: 'pride_spectrum',
            name: 'Pride Spectrum',
            description: 'Rainbow spectrum waves',
            dataInputs: ['weather', 'transit'],
            thumbnail: '🌈',
        },
        {
            id: 'pipes_flow',
            name: 'Pipes Flow',
            description: 'Organic flowing circles',
            dataInputs: ['weather', 'transit'],
            thumbnail: '🔵',
        },
        {
            id: 'skillet_switch',
            name: 'Skillet Switch',
            description: 'System state indicators',
            dataInputs: ['weather', 'transit'],
            thumbnail: '🎚️',
        },
    ];

    useEffect(() => {
        fetchVideos();
        fetchConfigurations();
        setAnimations(animationLibrary);
    }, []);
    
    useEffect(() => {
        // Listen for messages from projection window
        const handleMessage = (event) => {
            if (event.data.type === 'zoneTransformUpdate') {
                const { zoneId, transform } = event.data;
                setZoneTransforms(prev => ({
                    ...prev,
                    [zoneId]: transform
                }));
            }
        };
        
        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, []);

    const fetchVideos = async () => {
        try {
            const response = await api.get('/videos');
            setVideos(response.data.videos || []);
        } catch (error) {
            console.error('Error fetching videos:', error);
        }
    };
    
    const fetchConfigurations = async () => {
        try {
            const response = await api.get('/projection/configs');
            setProjectionConfigs(response.data || []);
        } catch (error) {
            console.error('Error fetching configurations:', error);
        }
    };

    const handleMaskUpload = async (event) => {
        const files = Array.from(event.target.files);
        if (!files.length) return;

        setLoading(true);
        setError('');

        const formData = new FormData();
        files.forEach(file => {
            formData.append('masks', file);
        });

        try {
            const response = await api.post('/projection/mask', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setMask(response.data);
            setZones(response.data.zones || []);
            
            // Initialize zone assignments and transforms
            const assignments = {};
            const transforms = {};
            response.data.zones.forEach(zone => {
                assignments[zone.id] = { type: 'empty', content: null };
                transforms[zone.id] = { x: 0, y: 0, scale: 1, rotation: 0 };
            });
            setZoneAssignments(assignments);
            setZoneTransforms(transforms);
        } catch (error) {
            console.error('Error uploading mask:', error);
            setError('Failed to upload masks. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleZoneAssignment = (zoneId, type, contentId) => {
        setZoneAssignments(prev => ({
            ...prev,
            [zoneId]: { type, content: contentId }
        }));
    };
    
    const handleZoneTransform = (zoneId, property, value) => {
        setZoneTransforms(prev => ({
            ...prev,
            [zoneId]: {
                ...prev[zoneId],
                [property]: parseFloat(value)
            }
        }));
        
        // Send update to projection window if it's open
        if (projectionWindow && !projectionWindow.closed) {
            projectionWindow.postMessage({
                type: 'updateTransforms',
                transforms: {
                    ...zoneTransforms,
                    [zoneId]: {
                        ...zoneTransforms[zoneId],
                        [property]: parseFloat(value)
                    }
                }
            }, '*');
        }
    };
    
    const toggleZoneExpanded = (zoneId) => {
        setExpandedZones(prev => ({
            ...prev,
            [zoneId]: !prev[zoneId]
        }));
    };

    const handleCodePenImport = async () => {
        if (!codePenUrl) return;

        setLoading(true);
        try {
            const response = await api.post('/projection/animations/import', {
                url: codePenUrl
            });

            // Add imported animation to library
            setAnimations(prev => [...prev, response.data]);
            setCodePenDialog(false);
            setCodePenUrl('');
        } catch (error) {
            console.error('Error importing CodePen:', error);
            setError('Failed to import CodePen animation.');
        } finally {
            setLoading(false);
        }
    };

    const saveConfiguration = async () => {
        if (!mask || zones.length === 0 || !newConfigName) {
            setError('Please provide a configuration name');
            return;
        }
        
        setLoading(true);
        try {
            const configData = {
                name: newConfigName,
                mask_data: {
                    id: mask.id,
                    name: mask.name,
                    width: mask.width,
                    height: mask.height,
                    filepath: mask.filepath,
                    url: mask.url
                },
                zones: zones.map(zone => ({
                    ...zone,
                    assignment: zoneAssignments[zone.id] || { type: 'empty' },
                    transform: zoneTransforms[zone.id] || { x: 0, y: 0, scale: 1, rotation: 0 }
                })),
                api_configs: {
                    weather_api_key: localStorage.getItem('weather_api_key') || '',
                    transit_stop_id: localStorage.getItem('transit_stop_id') || '',
                    timezone: localStorage.getItem('timezone') || 'America/Los_Angeles'
                }
            };
            
            const response = await api.post('/projection/configs', configData);
            setProjectionConfigs([...projectionConfigs, response.data]);
            setSelectedConfig(response.data);
            setConfigNameDialog(false);
            setNewConfigName('');
        } catch (error) {
            console.error('Error saving configuration:', error);
            setError('Failed to save configuration');
        } finally {
            setLoading(false);
        }
    };
    
    const loadConfiguration = (config) => {
        setSelectedConfig(config);
        setMask(config.mask_data);
        setZones(config.zones);
        
        // Load assignments and transforms
        const assignments = {};
        const transforms = {};
        config.zones.forEach(zone => {
            assignments[zone.id] = zone.assignment || { type: 'empty', content: null };
            transforms[zone.id] = zone.transform || { x: 0, y: 0, scale: 1, rotation: 0 };
        });
        setZoneAssignments(assignments);
        setZoneTransforms(transforms);
    };
    
    const deleteConfiguration = async (configId) => {
        try {
            await api.delete(`/projection/configs/${configId}`);
            setProjectionConfigs(projectionConfigs.filter(c => c.id !== configId));
            if (selectedConfig?.id === configId) {
                setSelectedConfig(null);
            }
        } catch (error) {
            console.error('Error deleting configuration:', error);
            setError('Failed to delete configuration');
        }
    };
    
    const duplicateConfiguration = async (config) => {
        const duplicateName = `${config.name} (Copy)`;
        try {
            const response = await api.post(`/projection/configs/${config.id}/duplicate?new_name=${encodeURIComponent(duplicateName)}`);
            setProjectionConfigs([...projectionConfigs, response.data]);
        } catch (error) {
            console.error('Error duplicating configuration:', error);
            setError('Failed to duplicate configuration');
        }
    };
    
    const launchProjection = async () => {
        if (!mask || zones.length === 0) {
            setError('Please upload a mask first');
            return;
        }

        setLoading(true);
        try {
            // Close existing window if any
            if (projectionWindow && !projectionWindow.closed) {
                projectionWindow.close();
            }

            let sessionId;
            
            if (selectedConfig) {
                // Launch from saved config
                const response = await api.post(`/projection/configs/${selectedConfig.id}/launch`);
                sessionId = response.data.id;
            } else {
                // Create temporary session
                const sessionData = {
                    maskId: mask.id,
                    zones: zones.map(zone => ({
                        ...zone,
                        assignment: zoneAssignments[zone.id] || { type: 'empty' },
                        transform: zoneTransforms[zone.id] || { x: 0, y: 0, scale: 1, rotation: 0 }
                    }))
                };

                const response = await api.post('/projection/sessions/create', sessionData);
                sessionId = response.data.id;
            }

            // Open projection window
            const projWindow = window.open(
                `/backend-static/projection_animation.html?session=${sessionId}`,
                'projection_animation',
                'width=1920,height=1080'
            );

            setProjectionWindow(projWindow);
            
            // Send initial transforms after window loads
            setTimeout(() => {
                if (projWindow && !projWindow.closed) {
                    projWindow.postMessage({
                        type: 'updateTransforms',
                        transforms: zoneTransforms
                    }, '*');
                }
            }, 1000);
        } catch (error) {
            console.error('Error launching projection:', error);
            setError('Failed to launch projection');
        } finally {
            setLoading(false);
        }
    };

    const getZoneSizeLabel = (area) => {
        const totalArea = mask ? mask.width * mask.height : 1;
        const percentage = (area / totalArea) * 100;
        
        if (percentage > 20) return 'Large';
        if (percentage > 5) return 'Medium';
        return 'Small';
    };

    return (
        <Grid container spacing={3}>
            <Grid item xs={12}>
                <Paper sx={{ p: 3 }}>
                    <Typography variant="h4" gutterBottom>
                        Projection Animation
                    </Typography>
                    <Typography variant="body1" color="text.secondary">
                        Upload a mask, assign animations or videos to zones, and launch your projection
                    </Typography>
                </Paper>
            </Grid>

            {/* Mask Upload Section */}
            <Grid item xs={12} md={4}>
                <Card>
                    <CardHeader 
                        title="Mask Upload"
                        avatar={<UploadIcon />}
                    />
                    <CardContent>
                        <input
                            accept="image/png"
                            style={{ display: 'none' }}
                            id="mask-upload"
                            type="file"
                            multiple
                            onChange={handleMaskUpload}
                        />
                        <label htmlFor="mask-upload">
                            <Button
                                variant="contained"
                                component="span"
                                fullWidth
                                startIcon={<UploadIcon />}
                                disabled={loading}
                            >
                                Upload PNG Masks
                            </Button>
                        </label>

                        {mask && (
                            <Box sx={{ mt: 2 }}>
                                <Typography variant="body2">
                                    <strong>Mask:</strong> {mask.name}
                                </Typography>
                                <Typography variant="body2">
                                    <strong>Size:</strong> {mask.width} x {mask.height}
                                </Typography>
                                <Typography variant="body2">
                                    <strong>Zones detected:</strong> {zones.length}
                                </Typography>
                            </Box>
                        )}

                        {loading && (
                            <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                                <CircularProgress />
                            </Box>
                        )}
                    </CardContent>
                </Card>
            </Grid>

            {/* Configuration Management Section */}
            <Grid item xs={12} md={8}>
                <Card>
                    <CardHeader 
                        title="Projection Configurations"
                        avatar={<SaveIcon />}
                        action={
                            <Tooltip title="Save current setup as configuration">
                                <span>
                                    <IconButton 
                                        onClick={() => setConfigNameDialog(true)}
                                        disabled={!mask || zones.length === 0}
                                    >
                                        <AddIcon />
                                    </IconButton>
                                </span>
                            </Tooltip>
                        }
                    />
                    <CardContent>
                        {projectionConfigs.length === 0 ? (
                            <Alert severity="info">
                                No saved configurations yet. Set up your zones and click + to save.
                            </Alert>
                        ) : (
                            <List>
                                {projectionConfigs.map(config => (
                                    <ListItem
                                        key={config.id}
                                        button
                                        selected={selectedConfig?.id === config.id}
                                        onClick={() => loadConfiguration(config)}
                                    >
                                        <ListItemText
                                            primary={config.name}
                                            secondary={`${config.zones.length} zones • Created ${new Date(config.created_at).toLocaleDateString()}`}
                                        />
                                        <ListItemSecondaryAction>
                                            <Tooltip title="Duplicate configuration">
                                                <IconButton
                                                    edge="end"
                                                    onClick={() => duplicateConfiguration(config)}
                                                    sx={{ mr: 1 }}
                                                >
                                                    <CopyIcon />
                                                </IconButton>
                                            </Tooltip>
                                            <Tooltip title="Delete configuration">
                                                <IconButton
                                                    edge="end"
                                                    onClick={() => deleteConfiguration(config.id)}
                                                >
                                                    <DeleteIcon />
                                                </IconButton>
                                            </Tooltip>
                                        </ListItemSecondaryAction>
                                    </ListItem>
                                ))}
                            </List>
                        )}
                    </CardContent>
                </Card>
            </Grid>

            {/* Zone Assignments Section */}
            <Grid item xs={12}>
                <Card>
                    <CardHeader 
                        title="Zone Assignments"
                        avatar={<AnimationIcon />}
                    />
                    <CardContent>
                        {zones.length === 0 ? (
                            <Typography color="text.secondary">
                                Upload a mask to see detected zones
                            </Typography>
                        ) : (
                            <>
                                <List>
                                    {zones.map((zone, index) => (
                                    <ListItem key={zone.id} divider>
                                        <ListItemText
                                            primary={`Zone ${index + 1}${zone.sourceMask ? ` - ${zone.sourceMask}` : ''}`}
                                            secondary={
                                                <Box component="span" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                    <span>
                                                        Position: ({zone.bounds.x}, {zone.bounds.y}) • 
                                                        Size: {zone.bounds.width} x {zone.bounds.height}
                                                    </span>
                                                    <Chip 
                                                        label={getZoneSizeLabel(zone.area)} 
                                                        size="small" 
                                                        component="span"
                                                    />
                                                </Box>
                                            }
                                            secondaryTypographyProps={{ component: 'div' }}
                                        />
                                        <ListItemSecondaryAction sx={{ width: '350px' }}>
                                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                                <FormControl size="small" sx={{ minWidth: 120 }}>
                                                    <InputLabel>Content Type</InputLabel>
                                                    <Select
                                                        value={zoneAssignments[zone.id]?.type || 'empty'}
                                                        onChange={(e) => {
                                                            const type = e.target.value;
                                                            handleZoneAssignment(zone.id, type, null);
                                                        }}
                                                        label="Content Type"
                                                    >
                                                        <MenuItem value="empty">Empty</MenuItem>
                                                        <MenuItem value="animation">Animation</MenuItem>
                                                        <MenuItem value="video">Video</MenuItem>
                                                    </Select>
                                                </FormControl>

                                                {zoneAssignments[zone.id]?.type === 'animation' && (
                                                    <FormControl size="small" sx={{ minWidth: 150 }}>
                                                        <InputLabel>Animation</InputLabel>
                                                        <Select
                                                            value={zoneAssignments[zone.id]?.content || ''}
                                                            onChange={(e) => 
                                                                handleZoneAssignment(zone.id, 'animation', e.target.value)
                                                            }
                                                            label="Animation"
                                                        >
                                                            {animations.map(anim => (
                                                                <MenuItem key={anim.id} value={anim.id}>
                                                                    {anim.thumbnail} {anim.name}
                                                                </MenuItem>
                                                            ))}
                                                        </Select>
                                                    </FormControl>
                                                )}

                                                {zoneAssignments[zone.id]?.type === 'video' && (
                                                    <FormControl size="small" sx={{ minWidth: 150 }}>
                                                        <InputLabel>Video</InputLabel>
                                                        <Select
                                                            value={zoneAssignments[zone.id]?.content || ''}
                                                            onChange={(e) => 
                                                                handleZoneAssignment(zone.id, 'video', e.target.value)
                                                            }
                                                            label="Video"
                                                        >
                                                            {videos.map(video => (
                                                                <MenuItem key={video.id} value={video.id}>
                                                                    {video.name}
                                                                </MenuItem>
                                                            ))}
                                                        </Select>
                                                    </FormControl>
                                                )}
                                                
                                                <Tooltip title="Transform settings">
                                                    <IconButton
                                                        onClick={() => toggleZoneExpanded(zone.id)}
                                                        size="small"
                                                    >
                                                        {expandedZones[zone.id] ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                                                    </IconButton>
                                                </Tooltip>
                                            </Box>
                                        </ListItemSecondaryAction>
                                    </ListItem>
                                ))}
                            </List>
                            
                            {/* Transform Controls for Each Zone */}
                            {zones.map((zone, index) => (
                                <Collapse key={zone.id} in={expandedZones[zone.id]} timeout="auto" unmountOnExit>
                                    <Box sx={{ p: 2, pl: 4, bgcolor: 'grey.50', borderTop: '1px solid #e0e0e0' }}>
                                        <Typography variant="subtitle2" gutterBottom>
                                            Transform Settings - Zone {index + 1}
                                        </Typography>
                                        <Grid container spacing={2}>
                                            <Grid item xs={12} sm={6}>
                                                <Typography variant="body2">X Position: {zoneTransforms[zone.id]?.x || 0}px</Typography>
                                                <Slider
                                                    value={zoneTransforms[zone.id]?.x || 0}
                                                    onChange={(e, value) => handleZoneTransform(zone.id, 'x', value)}
                                                    min={-500}
                                                    max={500}
                                                    valueLabelDisplay="auto"
                                                />
                                            </Grid>
                                            <Grid item xs={12} sm={6}>
                                                <Typography variant="body2">Y Position: {zoneTransforms[zone.id]?.y || 0}px</Typography>
                                                <Slider
                                                    value={zoneTransforms[zone.id]?.y || 0}
                                                    onChange={(e, value) => handleZoneTransform(zone.id, 'y', value)}
                                                    min={-500}
                                                    max={500}
                                                    valueLabelDisplay="auto"
                                                />
                                            </Grid>
                                            <Grid item xs={12} sm={6}>
                                                <Typography variant="body2">Scale: {(zoneTransforms[zone.id]?.scale || 1).toFixed(1)}x</Typography>
                                                <Slider
                                                    value={zoneTransforms[zone.id]?.scale || 1}
                                                    onChange={(e, value) => handleZoneTransform(zone.id, 'scale', value)}
                                                    min={0.1}
                                                    max={3}
                                                    step={0.1}
                                                    valueLabelDisplay="auto"
                                                />
                                            </Grid>
                                            <Grid item xs={12} sm={6}>
                                                <Typography variant="body2">Rotation: {zoneTransforms[zone.id]?.rotation || 0}°</Typography>
                                                <Slider
                                                    value={zoneTransforms[zone.id]?.rotation || 0}
                                                    onChange={(e, value) => handleZoneTransform(zone.id, 'rotation', value)}
                                                    min={-180}
                                                    max={180}
                                                    valueLabelDisplay="auto"
                                                />
                                            </Grid>
                                            <Grid item xs={12}>
                                                <Button
                                                    size="small"
                                                    onClick={() => {
                                                        handleZoneTransform(zone.id, 'x', 0);
                                                        handleZoneTransform(zone.id, 'y', 0);
                                                        handleZoneTransform(zone.id, 'scale', 1);
                                                        handleZoneTransform(zone.id, 'rotation', 0);
                                                    }}
                                                >
                                                    Reset Transform
                                                </Button>
                                            </Grid>
                                        </Grid>
                                    </Box>
                                </Collapse>
                            ))}
                            </>
                        )}
                    </CardContent>
                </Card>
            </Grid>

            {/* Animation Library Section */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardHeader 
                        title="Animation Library"
                        avatar={<AnimationIcon />}
                        action={
                            <Button
                                startIcon={<CodeIcon />}
                                onClick={() => setCodePenDialog(true)}
                            >
                                Import from CodePen
                            </Button>
                        }
                    />
                    <CardContent>
                        <Grid container spacing={2}>
                            {animations.map(anim => (
                                <Grid item xs={12} sm={6} key={anim.id}>
                                    <Paper sx={{ p: 2, cursor: 'pointer' }}>
                                        <Typography variant="h4" align="center">
                                            {anim.thumbnail}
                                        </Typography>
                                        <Typography variant="subtitle1" align="center">
                                            {anim.name}
                                        </Typography>
                                        <Typography variant="body2" color="text.secondary" align="center">
                                            {anim.description}
                                        </Typography>
                                        {anim.dataInputs && (
                                            <Box sx={{ mt: 1, textAlign: 'center' }}>
                                                {anim.dataInputs.map(input => (
                                                    <Chip 
                                                        key={input} 
                                                        label={input} 
                                                        size="small" 
                                                        sx={{ mr: 0.5 }}
                                                    />
                                                ))}
                                            </Box>
                                        )}
                                    </Paper>
                                </Grid>
                            ))}
                        </Grid>
                    </CardContent>
                </Card>
            </Grid>

            {/* Launch Section */}
            <Grid item xs={12} md={6}>
                <Card>
                    <CardHeader 
                        title="Launch Projection"
                        avatar={<LaunchIcon />}
                    />
                    <CardContent>
                        <Box sx={{ textAlign: 'center' }}>
                            <Button
                                variant="contained"
                                size="large"
                                color="primary"
                                startIcon={<PlayIcon />}
                                onClick={launchProjection}
                                disabled={!mask || zones.length === 0 || loading}
                                sx={{ mb: 2 }}
                            >
                                Launch Projection Window
                            </Button>
                            
                            {projectionWindow && !projectionWindow.closed && (
                                <Alert severity="success">
                                    Projection window is running
                                </Alert>
                            )}
                        </Box>

                        <Divider sx={{ my: 2 }} />

                        <Box>
                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                <strong>Tips:</strong>
                            </Typography>
                            <Typography variant="body2" color="text.secondary" component="div">
                                <ul>
                                    <li>Each uploaded mask file becomes one zone</li>
                                    <li>Animations adapt automatically to zone sizes</li>
                                    <li>Videos will be cropped to fit zones</li>
                                    <li>Weather and transit data update in real-time</li>
                                </ul>
                            </Typography>
                        </Box>
                    </CardContent>
                </Card>
            </Grid>

            {/* Error Alert */}
            {error && (
                <Grid item xs={12}>
                    <Alert severity="error" onClose={() => setError('')}>
                        {error}
                    </Alert>
                </Grid>
            )}

            {/* CodePen Import Dialog */}
            <Dialog open={codePenDialog} onClose={() => setCodePenDialog(false)}>
                <DialogTitle>Import from CodePen</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="CodePen URL"
                        type="url"
                        fullWidth
                        variant="outlined"
                        value={codePenUrl}
                        onChange={(e) => setCodePenUrl(e.target.value)}
                        placeholder="https://codepen.io/username/pen/xxxxx"
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        The animation will be automatically adapted to work without mouse interaction
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setCodePenDialog(false)}>Cancel</Button>
                    <Button onClick={handleCodePenImport} variant="contained" disabled={!codePenUrl || loading}>
                        Import
                    </Button>
                </DialogActions>
            </Dialog>
            
            {/* Save Configuration Dialog */}
            <Dialog open={configNameDialog} onClose={() => setConfigNameDialog(false)}>
                <DialogTitle>Save Configuration</DialogTitle>
                <DialogContent>
                    <TextField
                        autoFocus
                        margin="dense"
                        label="Configuration Name"
                        type="text"
                        fullWidth
                        variant="outlined"
                        value={newConfigName}
                        onChange={(e) => setNewConfigName(e.target.value)}
                        placeholder="My Projection Setup"
                    />
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                        This will save your current mask, zone assignments, and transform settings
                    </Typography>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setConfigNameDialog(false)}>Cancel</Button>
                    <Button onClick={saveConfiguration} variant="contained" disabled={!newConfigName || loading}>
                        Save
                    </Button>
                </DialogActions>
            </Dialog>
        </Grid>
    );
}

export default ProjectionAnimation;