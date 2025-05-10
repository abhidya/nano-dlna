# Renderer Service Implementation Plan

## 1. Process Model & CLI Flags

### Process Model

The Renderer Service will be an independent process that:

1. **Accepts commands** to render scenes on specific projectors
2. **Manages the lifecycle** of rendering processes (Chrome/Tauri windows)
3. **Handles output** to different display targets (direct, DLNA, AirPlay)
4. **Monitors health** of running renderers (watchdogs)
5. **Emits events** for status changes

### Architecture

```
renderer_service/
├── __init__.py             # Package initialization
├── service.py              # Main service entry point
├── renderer/
│   ├── __init__.py
│   ├── base.py             # Abstract renderer class
│   ├── chrome.py           # Chrome-based renderer
│   └── tauri.py            # Future Tauri-based renderer
├── sender/
│   ├── __init__.py
│   ├── base.py             # Abstract sender interface
│   ├── direct.py           # Direct display output (local screen)
│   ├── dlna.py             # DLNA sender implementation
│   ├── airplay.py          # AirPlay sender implementation
│   └── chromecast.py       # Future Chromecast implementation
├── watchdog.py             # Monitoring and auto-recovery
└── events.py               # Event emission system
```

### CLI Flags

```
python -m renderer_service [options]

Options:
  --host TEXT                 Host to bind service to [default: 127.0.0.1]
  --port INTEGER              Port to run service on [default: 7500]
  --log-level TEXT            Logging level (DEBUG, INFO, WARNING, ERROR) [default: INFO]
  --config-file PATH          Path to configuration file [default: ./renderer_config.json]
  --enable-senders TEXT       Comma-separated list of enabled senders [default: direct,dlna,airplay]
  --renderer-type TEXT        Renderer implementation to use [default: chrome]
  --cache-dir PATH            Directory for cached renderer data [default: ./cache]
  --event-socket PATH         Socket path for publishing events [default: ./events.sock]
  --health-check-interval INTEGER
                              Seconds between health checks [default: 10]
  --help                      Show this message and exit.
```

## 2. Sender Abstraction Interface

### Core Sender Interface

```python
class Sender(ABC):
    """Abstract base class for all sender implementations."""
    
    @abstractmethod
    def __init__(self, config: dict, logger: logging.Logger):
        """Initialize the sender with configuration."""
        pass
    
    @abstractmethod
    def connect(self, target_id: str) -> bool:
        """Connect to the target device/display."""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect from the target device/display."""
        pass
    
    @abstractmethod
    def send_content(self, content_url: str) -> bool:
        """Send content to the target device/display."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if sender is connected to target device/display."""
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        """Get current status of the sender."""
        pass
```

### AirPlay Sender Implementation

```python
class AirPlaySender(Sender):
    """AirPlay implementation of the sender interface."""
    
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.applescript_path = os.path.join(
            os.path.dirname(__file__), 
            "scripts", 
            "airplay_mirror.scpt"
        )
        self.target_name = None
        self.process = None
        self.connected = False
    
    def connect(self, target_id: str) -> bool:
        """Connect to the AirPlay device by name."""
        self.target_name = target_id
        self.logger.info(f"Connecting to AirPlay device: {target_id}")
        
        try:
            # Execute the AppleScript to start mirroring
            cmd = [
                "osascript", 
                self.applescript_path, 
                "start",
                target_id
            ]
            
            self.process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            # Wait briefly and check status
            time.sleep(2)
            if self.process.poll() is None:
                self.connected = True
                return True
            else:
                stderr = self.process.stderr.read().decode('utf-8')
                self.logger.error(f"AirPlay connection failed: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to AirPlay: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """Stop AirPlay mirroring."""
        if not self.connected:
            return True
            
        try:
            # Execute the AppleScript to stop mirroring
            cmd = [
                "osascript", 
                self.applescript_path, 
                "stop"
            ]
            
            result = subprocess.run(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                self.connected = False
                # Kill the process if still running
                if self.process and self.process.poll() is None:
                    self.process.terminate()
                    self.process = None
                return True
            else:
                stderr = result.stderr.decode('utf-8')
                self.logger.error(f"AirPlay disconnection failed: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error disconnecting AirPlay: {str(e)}")
            return False
    
    def send_content(self, content_url: str) -> bool:
        """
        AirPlay mirroring doesn't need explicit content URLs,
        as it mirrors the entire screen. This is a no-op.
        """
        if not self.connected:
            self.logger.warning("Cannot send content - not connected to AirPlay device")
            return False
        return True
    
    def is_connected(self) -> bool:
        """Check if still connected to AirPlay device."""
        if not self.process:
            return False
            
        # Check if the process is still running
        return self.process.poll() is None
    
    def get_status(self) -> dict:
        """Get current status information."""
        status = {
            "type": "airplay",
            "connected": self.is_connected(),
            "target": self.target_name
        }
        
        # Add additional status if available
        if self.process and self.process.poll() is None:
            status["process_running"] = True
        else:
            status["process_running"] = False
            
        return status
```

### DLNA Sender Implementation

```python
class DLNASender(Sender):
    """DLNA implementation of the sender interface."""
    
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.dlna_device = None
        self.target_id = None
        self.streaming_server = None
    
    def connect(self, target_id: str) -> bool:
        """Connect to the DLNA device by ID or name."""
        from nanodlna.dlna import DlnaDevice
        from core.twisted_streaming import TwistedStreamingServer
        
        self.target_id = target_id
        self.logger.info(f"Connecting to DLNA device: {target_id}")
        
        try:
            # Find and connect to the DLNA device
            # This could use the existing device_manager to get a registered device
            from services.device_service import DeviceService
            device_service = DeviceService()
            self.dlna_device = device_service.get_device_instance(target_id)
            
            if not self.dlna_device:
                self.logger.error(f"DLNA device not found: {target_id}")
                return False
                
            # Initialize streaming server if needed
            if not self.streaming_server:
                self.streaming_server = TwistedStreamingServer()
                self.streaming_server.start_server()
                
            return True
                
        except Exception as e:
            self.logger.error(f"Error connecting to DLNA device: {str(e)}")
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from the DLNA device."""
        if not self.dlna_device:
            return True
            
        try:
            # Stop any playback
            self.dlna_device.stop()
            
            # Stop streaming server if it's running
            if self.streaming_server:
                self.streaming_server.stop_server()
                self.streaming_server = None
                
            self.dlna_device = None
            return True
                
        except Exception as e:
            self.logger.error(f"Error disconnecting DLNA device: {str(e)}")
            return False
    
    def send_content(self, content_url: str) -> bool:
        """Send content to the DLNA device."""
        if not self.dlna_device:
            self.logger.warning("Cannot send content - not connected to DLNA device")
            return False
            
        try:
            # Translate content_url to a local file path if it's a URL
            if content_url.startswith("http"):
                self.logger.warning("Remote URLs not supported, must be local file path")
                return False
                
            # Play the file on the DLNA device
            loop = self.config.get("loop", True)
            self.dlna_device.play(content_url, loop=loop)
            return True
                
        except Exception as e:
            self.logger.error(f"Error sending content to DLNA device: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check if still connected to DLNA device."""
        if not self.dlna_device:
            return False
            
        try:
            # Check connection by querying device state
            return self.dlna_device.is_connected()
        except:
            return False
    
    def get_status(self) -> dict:
        """Get current status information."""
        status = {
            "type": "dlna",
            "connected": self.is_connected(),
            "target": self.target_id
        }
        
        # Add additional status if available
        if self.dlna_device:
            try:
                status["is_playing"] = self.dlna_device.is_playing
                status["current_video"] = self.dlna_device.current_video
            except:
                pass
            
        return status
```

### Direct Sender Implementation

```python
class DirectSender(Sender):
    """Direct output implementation for local display."""
    
    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.display = config.get("display", 0)  # Display number to use
        self.connected = False
        self.window = None
    
    def connect(self, target_id: str) -> bool:
        """Connect to the specified display."""
        # For direct display, target_id is the display number
        try:
            self.display = int(target_id)
        except ValueError:
            self.logger.error(f"Invalid display number: {target_id}")
            return False
            
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from the display."""
        if self.window:
            try:
                self.window.close()
            except:
                pass
        self.window = None
        self.connected = False
        return True
    
    def send_content(self, content_url: str) -> bool:
        """Display content on the local display."""
        if not self.connected:
            return False
            
        # This would typically launch a browser window in kiosk mode
        # on the specified display
        try:
            import webbrowser
            
            # In a real implementation, we'd use a more controlled browser window
            # This is simplified
            self.window = webbrowser.open(content_url)
            return True
        except Exception as e:
            self.logger.error(f"Error displaying content: {str(e)}")
            return False
    
    def is_connected(self) -> bool:
        """Check if still connected to display."""
        return self.connected
    
    def get_status(self) -> dict:
        """Get current status information."""
        return {
            "type": "direct",
            "connected": self.connected,
            "display": self.display,
            "has_window": self.window is not None
        }
```

## 3. Renderer Service API

### REST API Endpoints

```
POST /renderer/start
{
  "scene": "scene-id",
  "projector": "projector-id",
  "options": {
    "loop": true,
    "timeout": 300
  }
}

POST /renderer/stop
{
  "projector": "projector-id"
}

GET /renderer/status
{
  "projector": "projector-id"
}

GET /renderer/list
Returns a list of all active renderers
```

### Events Published

```
renderer.started
{
  "scene": "scene-id",
  "projector": "projector-id",
  "timestamp": "2025-05-02T12:30:45Z"
}

renderer.stopped
{
  "scene": "scene-id", 
  "projector": "projector-id",
  "timestamp": "2025-05-02T12:40:45Z",
  "reason": "user_requested" | "error" | "timeout"
}

renderer.error
{
  "scene": "scene-id",
  "projector": "projector-id",
  "timestamp": "2025-05-02T12:35:45Z",
  "error": "Error description",
  "code": "ERROR_CODE"
}

renderer.healthcheck
{
  "scene": "scene-id",
  "projector": "projector-id",
  "timestamp": "2025-05-02T12:32:45Z", 
  "status": "healthy" | "degraded" | "failed",
  "details": {
    "cpu": 0.2,
    "memory": 156000000,
    "uptime": 120
  }
}
```

## 4. Migration Path from Stand-alone Launcher

### Phase 1: Extract Common Code

1. **Identify reusable components** from the front-door launcher:
   - AppleScript execution logic
   - Process management
   - Watchdog functionality
   - Error handling

2. **Move these components** into the new modular structure:
   - Create `sender/airplay.py` with the AppleScript logic
   - Create `watchdog.py` with monitoring functionality
   - Create `renderer/chrome.py` with the browser launch logic

3. **Create adapter layer** for backward compatibility:
   - Implement a lightweight wrapper using the new components
   - Ensure existing invocations continue to work

### Phase 2: Update Invocation Methods

1. **Update run_dashboard.sh** to use the new Renderer Service
   ```bash
   # Start the renderer service
   python -m renderer_service --host 127.0.0.1 --port 7500 &
   RENDERER_PID=$!
   
   # Register it for cleanup
   echo $RENDERER_PID >> $PIDS_FILE
   ```

2. **Modify frontend** to use REST API:
   ```javascript
   // Before: Direct script call
   const launchFrontDoor = () => {
     fetch('/api/launch_frontdoor', { method: 'POST' });
   }
   
   // After: Use Renderer Service API
   const launchFrontDoor = () => {
     fetch('/api/renderer/start', {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         scene: 'frontdoor-v1',
         projector: 'proj-hallway'
       })
     });
   }
   ```

3. **Update backend API** to proxy requests to the Renderer Service:
   ```python
   @router.post("/renderer/start")
   async def start_renderer(request: RendererStartRequest):
       """Start a renderer for a scene on a projector."""
       response = httpx.post(
           "http://127.0.0.1:7500/renderer/start",
           json=request.dict()
       )
       return response.json()
   ```

### Phase 3: Deprecate Old Launcher

1. **Add deprecation warning** to the standalone launcher:
   ```python
   import warnings
   warnings.warn(
       "frontdoor_launcher.py is deprecated and will be removed in a future version. "
       "Please use the Renderer Service API instead.",
       DeprecationWarning, 
       stacklevel=2
   )
   ```

2. **Monitor usage** and provide migration assistance:
   - Log all invocations of the old launcher
   - Create migration documentation
   - Assist users in updating their scripts

3. **Remove the old launcher** after successful migration:
   - Set a deprecation timeline
   - Send final notices before removal
   - Remove the deprecated code

## 5. Implementation Roadmap

### Sprint 1: Core Infrastructure

1. Create the basic service structure
2. Implement the Sender abstraction layer
3. Create the base implementations for DirectSender and DLNASender
4. Implement the REST API endpoints
5. Set up the event emission system

### Sprint 2: AirPlay Integration

1. Port the AppleScript logic from the standalone launcher 
2. Implement the AirPlaySender class
3. Create the watchdog monitoring
4. Add health check status API
5. Connect all components

### Sprint 3: Migration & Testing

1. Create the adapter layer for backward compatibility
2. Update dashboard to use the new API
3. Implement comprehensive tests
4. Create documentation for the new service
5. Deploy and test in production environment

## 6. Testing Strategy

### Unit Tests

1. **Sender Tests**
   - Test each sender implementation in isolation
   - Mock device responses
   - Verify connection handling
   - Test error scenarios

2. **Renderer Tests**
   - Test renderer lifecycle management
   - Verify correct parameters are passed
   - Test error handling and recovery

3. **API Tests**
   - Test each endpoint for correct behavior
   - Verify parameter validation
   - Test authentication (if applicable)

### Integration Tests

1. **Sender-Renderer Integration**
   - Test full rendering pipeline
   - Verify sender selection logic
   - Test multiple concurrent renderers

2. **Service-Dashboard Integration**
   - Test API communication
   - Verify event propagation
   - Test dashboard UI controls

### Mock Testing

1. **Mock Devices**
   - Create mock DLNA devices
   - Create mock AirPlay receivers
   - Simulate various error conditions

2. **Mock Browsers**
   - Test browser launch without actual GUI
   - Verify process management

## 7. AppleScript Implementation

The AppleScript for AirPlay mirroring will be stored in `renderer_service/sender/scripts/airplay_mirror.scpt`:

```applescript
on run argv
    set command to item 1 of argv
    
    if command is "start" then
        set deviceName to item 2 of argv
        startMirroring(deviceName)
    else if command is "stop" then
        stopMirroring()
    else
        error "Unknown command: " & command
    end if
end run

on startMirroring(deviceName)
    tell application "System Preferences"
        reveal pane "com.apple.preference.displays"
        delay 1
        tell application "System Events"
            tell process "System Preferences"
                # Click AirPlay dropdown 
                click pop up button 1 of tab group 1 of window 1
                delay 0.5
                
                # Find and click the device with matching name
                repeat with menuItem in menu items of menu 1 of pop up button 1 of tab group 1 of window 1
                    if name of menuItem contains deviceName then
                        click menuItem
                        delay 0.5
                        # Success
                        return 0
                    end if
                end repeat
                
                # Device not found
                error "AirPlay device not found: " & deviceName
            end tell
        end tell
    end tell
end startMirroring

on stopMirroring()
    tell application "System Preferences"
        reveal pane "com.apple.preference.displays"
        delay 1
        tell application "System Events"
            tell process "System Preferences"
                # Click AirPlay dropdown 
                click pop up button 1 of tab group 1 of window 1
                delay 0.5
                
                # Click "This Mac" to stop mirroring
                click menu item "This Mac" of menu 1 of pop up button 1 of tab group 1 of window 1
                delay 0.5
                # Success
                return 0
            end tell
        end tell
    end tell
end stopMirroring
```

## 8. Configuration Schema

The Renderer Service will use a configuration file in JSON format:

```json
{
  "senders": {
    "direct": {
      "enabled": true,
      "default_display": 0
    },
    "dlna": {
      "enabled": true,
      "stream_port": 8000,
      "connect_timeout": 5
    },
    "airplay": {
      "enabled": true,
      "script_path": "auto",
      "connect_timeout": 10
    }
  },
  "renderers": {
    "chrome": {
      "path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
      "args": ["--kiosk", "--disable-infobars", "--no-first-run"],
      "timeout": 30
    }
  },
  "scenes": {
    "frontdoor-v1": {
      "template": "overlay_frontdoor/index.html",
      "data": {
        "weather_key": "env:WEATHER_API",
        "muni_stop": 13915,
        "video_host": "http://10.0.0.74",
        "video_ports": [9000, 8999, 8998],
        "video_file": "door6.mp4"
      }
    }
  },
  "projectors": {
    "proj-hallway": {
      "sender": "airplay",
      "target_name": "Hallway TV",
      "fallback_sender": "dlna",
      "fallback_target": "Hallway_TV_DLNA"
    },
    "proj-kitchen": {
      "sender": "dlna",
      "target_name": "Kitchen_TV_DLNA"
    }
  }
}
```

## 9. Conclusion

The Renderer Service provides a unified framework for managing projections across multiple display technologies. It maintains the proven technology behind the current front-door overlay while establishing a foundation for future expansion to more scene types and display technologies.

By separating the rendering process from the send mechanism, we achieve greater flexibility and can support a wide range of scenarios without duplicating code. The event-based architecture ensures all components remain up-to-date on system status, and the health monitoring provides automatic recovery from common failure scenarios.

This design aligns with the overall roadmap for evolving the system into a comprehensive projection management platform. 