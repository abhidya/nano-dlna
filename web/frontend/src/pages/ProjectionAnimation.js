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
} from '@mui/icons-material';
import { api } from '../services/api';

function ProjectionAnimation() {
    const [mask, setMask] = useState(null);
    const [zones, setZones] = useState([]);
    const [animations, setAnimations] = useState([]);
    const [videos, setVideos] = useState([]);
    const [zoneAssignments, setZoneAssignments] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [codePenDialog, setCodePenDialog] = useState(false);
    const [codePenUrl, setCodePenUrl] = useState('');
    const [projectionWindow, setProjectionWindow] = useState(null);

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
        setAnimations(animationLibrary);
    }, []);

    const fetchVideos = async () => {
        try {
            const response = await api.get('/videos');
            setVideos(response.data.videos || []);
        } catch (error) {
            console.error('Error fetching videos:', error);
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
            
            // Initialize zone assignments
            const assignments = {};
            response.data.zones.forEach(zone => {
                assignments[zone.id] = { type: 'empty', content: null };
            });
            setZoneAssignments(assignments);
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

            // Create session configuration
            const sessionData = {
                maskId: mask.id,
                zones: zones.map(zone => ({
                    ...zone,
                    assignment: zoneAssignments[zone.id] || { type: 'empty' }
                }))
            };

            const response = await api.post('/projection/sessions/create', sessionData);
            const sessionId = response.data.id;

            // Open projection window
            const projWindow = window.open(
                `/backend-static/projection_animation.html?session=${sessionId}`,
                'projection_animation',
                'width=1920,height=1080'
            );

            setProjectionWindow(projWindow);
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

            {/* Zone Assignments Section */}
            <Grid item xs={12} md={8}>
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
                                        <ListItemSecondaryAction sx={{ width: '300px' }}>
                                            <FormControl fullWidth size="small">
                                                <InputLabel>Content Type</InputLabel>
                                                <Select
                                                    value={zoneAssignments[zone.id]?.type || 'empty'}
                                                    onChange={(e) => {
                                                        const type = e.target.value;
                                                        console.log('Selected type:', type, 'for zone:', zone.id);
                                                        console.log('Current assignments:', zoneAssignments);
                                                        console.log('Animations array:', animations);
                                                        handleZoneAssignment(zone.id, type, null);
                                                    }}
                                                    label="Content Type"
                                                >
                                                    <MenuItem value="empty">Empty</MenuItem>
                                                    <MenuItem value="animation">Animation</MenuItem>
                                                    <MenuItem value="video">Video</MenuItem>
                                                </Select>
                                            </FormControl>

                                            {console.log('Zone:', zone.id, 'Type:', zoneAssignments[zone.id]?.type, 'Should show animation dropdown:', zoneAssignments[zone.id]?.type === 'animation')}
                                            {zoneAssignments[zone.id]?.type === 'animation' && (
                                                <FormControl fullWidth size="small" sx={{ mt: 1 }}>
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
                                                <FormControl fullWidth size="small" sx={{ mt: 1 }}>
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
                                        </ListItemSecondaryAction>
                                    </ListItem>
                                ))}
                            </List>
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
        </Grid>
    );
}

export default ProjectionAnimation;