import React, { useState, useEffect } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  CardMedia,
  CardHeader,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  TextField,
  CircularProgress,
  Box,
  Divider,
  Alert,
  Snackbar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Avatar,
  Chip
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  VideoLibrary as VideoIcon,
  PlayArrow as PlayIcon,
  Folder as FolderIcon
} from '@mui/icons-material';
import { videoApi } from '../services/api';
import { useNavigate } from 'react-router-dom';

function Videos() {
  const navigate = useNavigate();
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [openAddDialog, setOpenAddDialog] = useState(false);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const [openScanDialog, setOpenScanDialog] = useState(false);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [newVideo, setNewVideo] = useState({
    name: '',
    path: '',
  });
  const [scanDirectory, setScanDirectory] = useState('');
  const [snackbar, setSnackbar] = useState({
    open: false,
    message: '',
    severity: 'success'
  });
  const [scanning, setScanning] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      setLoading(true);
      const response = await videoApi.getVideos();
      setVideos(response.data.videos);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching videos:', err);
      setError('Failed to load videos. Please try again later.');
      setLoading(false);
    }
  };

  const handleAddVideo = async () => {
    try {
      await videoApi.addVideo(newVideo);
      setOpenAddDialog(false);
      setNewVideo({
        name: '',
        path: '',
      });
      setSnackbar({
        open: true,
        message: 'Video added successfully',
        severity: 'success'
      });
      fetchVideos();
    } catch (err) {
      console.error('Error adding video:', err);
      setSnackbar({
        open: true,
        message: 'Failed to add video',
        severity: 'error'
      });
    }
  };

  const handleDeleteVideo = async () => {
    try {
      await videoApi.deleteVideo(selectedVideo.id);
      setOpenDeleteDialog(false);
      setSelectedVideo(null);
      setSnackbar({
        open: true,
        message: 'Video deleted successfully',
        severity: 'success'
      });
      fetchVideos();
    } catch (err) {
      console.error('Error deleting video:', err);
      setSnackbar({
        open: true,
        message: 'Failed to delete video',
        severity: 'error'
      });
    }
  };

  const handleScanDirectory = async () => {
    try {
      setScanning(true);
      const response = await videoApi.scanDirectory(scanDirectory);
      setOpenScanDialog(false);
      setScanDirectory('');
      setSnackbar({
        open: true,
        message: `Scan completed. Found ${response.data.videos.length} videos.`,
        severity: 'success'
      });
      fetchVideos();
    } catch (err) {
      console.error('Error scanning directory:', err);
      setSnackbar({
        open: true,
        message: 'Failed to scan directory',
        severity: 'error'
      });
    } finally {
      setScanning(false);
    }
  };

  const handleUploadVideo = async () => {
    if (!uploadFile) return;

    const formData = new FormData();
    formData.append('file', uploadFile);
    formData.append('name', uploadFile.name.split('.')[0]);

    try {
      const response = await videoApi.uploadVideo(formData);
      setSnackbar({
        open: true,
        message: 'Video uploaded successfully',
        severity: 'success'
      });
      setUploadFile(null);
      fetchVideos();
    } catch (err) {
      console.error('Error uploading video:', err);
      setSnackbar({
        open: true,
        message: 'Failed to upload video',
        severity: 'error'
      });
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setNewVideo(prev => ({
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

  const formatDuration = (seconds) => {
    if (!seconds) return 'Unknown';
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'Unknown';
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
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
        <Button variant="contained" onClick={fetchVideos}>
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
          <Typography variant="h4">Videos</Typography>
          <Box>
            <Button
              variant="contained"
              color="primary"
              startIcon={<RefreshIcon />}
              onClick={fetchVideos}
              sx={{ mr: 1 }}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              color="primary"
              startIcon={<FolderIcon />}
              onClick={() => setOpenScanDialog(true)}
              sx={{ mr: 1 }}
            >
              Scan Directory
            </Button>
            <Button
              variant="contained"
              color="secondary"
              startIcon={<AddIcon />}
              onClick={() => setOpenAddDialog(true)}
            >
              Add Video
            </Button>
          </Box>
        </Box>
        <Divider sx={{ mb: 2 }} />
      </Grid>

      {/* Upload Video */}
      <Grid item xs={12}>
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Upload Video
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
            <TextField
              type="file"
              inputProps={{ accept: 'video/*' }}
              onChange={(e) => setUploadFile(e.target.files[0])}
              fullWidth
              variant="outlined"
              sx={{ mr: 2 }}
            />
            <Button
              variant="contained"
              color="primary"
              onClick={handleUploadVideo}
              disabled={!uploadFile}
            >
              Upload
            </Button>
          </Box>
        </Paper>
      </Grid>

      {/* Video List */}
      {videos.length === 0 ? (
        <Grid item xs={12}>
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="h6" color="textSecondary">
              No videos found
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Add a video manually, upload a video, or scan a directory for videos
            </Typography>
          </Paper>
        </Grid>
      ) : (
        videos.map(video => (
          <Grid item xs={12} sm={6} md={4} key={video.id}>
            <Card>
              <CardHeader
                title={video.name}
                subheader={`Format: ${video.format || 'Unknown'}`}
                action={
                  <IconButton onClick={() => { setSelectedVideo(video); setOpenDeleteDialog(true); }}>
                    <DeleteIcon />
                  </IconButton>
                }
              />
              <CardMedia
                component="div"
                sx={{
                  height: 140,
                  backgroundColor: 'rgba(0, 0, 0, 0.1)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <VideoIcon sx={{ fontSize: 60, opacity: 0.7 }} />
              </CardMedia>
              <CardContent>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Duration: {formatDuration(video.duration)}
                </Typography>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Size: {formatFileSize(video.file_size)}
                </Typography>
                {video.resolution && (
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Resolution: {video.resolution}
                  </Typography>
                )}
                {video.has_subtitle && (
                  <Chip label="Has Subtitles" size="small" color="primary" sx={{ mt: 1 }} />
                )}
              </CardContent>
              <CardActions>
                <Button 
                  size="small" 
                  color="primary"
                  onClick={() => navigate(`/videos/${video.id}`)}
                >
                  Details
                </Button>
                <Button 
                  size="small" 
                  color="primary"
                  startIcon={<PlayIcon />}
                  onClick={() => navigate(`/videos/${video.id}/play`)}
                >
                  Play
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))
      )}

      {/* Add Video Dialog */}
      <Dialog open={openAddDialog} onClose={() => setOpenAddDialog(false)}>
        <DialogTitle>Add New Video</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter the details of the video you want to add.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Video Name"
            type="text"
            fullWidth
            variant="outlined"
            value={newVideo.name}
            onChange={handleInputChange}
            sx={{ mb: 2 }}
          />
          <TextField
            margin="dense"
            name="path"
            label="Video Path"
            type="text"
            fullWidth
            variant="outlined"
            value={newVideo.path}
            onChange={handleInputChange}
            helperText="Full path to the video file"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAddDialog(false)}>Cancel</Button>
          <Button onClick={handleAddVideo} variant="contained" color="primary">Add</Button>
        </DialogActions>
      </Dialog>

      {/* Delete Video Dialog */}
      <Dialog open={openDeleteDialog} onClose={() => setOpenDeleteDialog(false)}>
        <DialogTitle>Delete Video</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the video "{selectedVideo?.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDeleteVideo} variant="contained" color="error">Delete</Button>
        </DialogActions>
      </Dialog>

      {/* Scan Directory Dialog */}
      <Dialog open={openScanDialog} onClose={() => setOpenScanDialog(false)}>
        <DialogTitle>Scan Directory for Videos</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Enter the directory path to scan for video files.
          </DialogContentText>
          <TextField
            autoFocus
            margin="dense"
            name="directory"
            label="Directory Path"
            type="text"
            fullWidth
            variant="outlined"
            value={scanDirectory}
            onChange={(e) => setScanDirectory(e.target.value)}
            helperText="Full path to the directory containing videos"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenScanDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleScanDirectory} 
            variant="contained" 
            color="primary"
            disabled={scanning}
            startIcon={scanning ? <CircularProgress size={20} /> : null}
          >
            {scanning ? 'Scanning...' : 'Scan'}
          </Button>
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

export default Videos;
