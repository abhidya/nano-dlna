# nano-dlna Dashboard

A web dashboard for managing DLNA and projector devices.

## Features

- Discover and manage DLNA devices on your network
- Stream videos to DLNA-compatible devices
- Upload and manage video files
- Control playback (play, pause, stop, seek)

## Running with Docker

The easiest way to run the application is using Docker Compose:

### Prerequisites

1. Install Docker:
   - For macOS: [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
   - For Windows: [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
   - For Linux: [Docker Engine](https://docs.docker.com/engine/install/)

2. Make sure Docker is running before proceeding.

### Starting the Application

```bash
# Start the application
./run.sh

# Stop the application
./stop.sh
```

This will start both the backend API and the frontend web interface.

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Directory Structure

- `backend/`: FastAPI backend
- `frontend/`: React frontend
- `data/`: Database and persistent data
- `uploads/`: Uploaded video files

## Development

For development, you can run the backend and frontend separately:

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py --reload

# Frontend
cd frontend
npm install
npm start
```
