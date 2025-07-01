# Function Signature Cleanup Plan

## Priority Classification

### Critical Issues (Must Fix First)

#### 1. DeviceManager Core Methods
**File**: `web/backend/core/device_manager.py`

```python
# BEFORE (Problematic)
def update_device_status(self, device_name: str, status: str, is_playing: bool = None, 
                       current_video: str = None, error: str = None) -> None:

# AFTER (Recommended)
@dataclass
class DeviceStatusUpdate:
    device_name: str
    status: str
    is_playing: Optional[bool] = None
    current_video: Optional[str] = None
    error: Optional[str] = None

def update_device_status(self, update: DeviceStatusUpdate) -> None:
```

**Issues**: 
- 5 parameters (too many)
- Optional parameters create unclear call sites
- Missing parameter validation

**Impact**: High - Used throughout the application

#### 2. CLI Module Type Annotations
**File**: `nanodlna/cli.py`

```python
# BEFORE (No types)
def play_video_on_device(device_name, video_file, args):
def monitor_and_restart_threads(threads, devices_config, args):

# AFTER (Fully typed)
def play_video_on_device(
    device_name: str, 
    video_file: Path, 
    args: argparse.Namespace
) -> None:

def monitor_and_restart_threads(
    threads: List[threading.Thread], 
    devices_config: List[Dict[str, Any]], 
    args: argparse.Namespace
) -> None:
```

**Issues**:
- Zero type annotations in main CLI module
- Unclear parameter types
- Missing return type specifications

**Impact**: Critical - Entry point to application

#### 3. DLNADevice Method Decomposition
**File**: `web/backend/core/dlna_device.py`

```python
# BEFORE (173 lines, multiple responsibilities)
def auto_play_video(self, device: Device, video_path: str, loop: bool = True, 
                   config: Optional[Dict[str, Any]] = None) -> bool:
    # 173 lines of mixed responsibilities

# AFTER (Decomposed)
def validate_video_file(self, video_path: str) -> bool:
def setup_streaming_server(self, video_path: str, device: Device) -> StreamingConfig:
def start_device_playback(self, device: Device, streaming_url: str, loop: bool) -> bool:
def update_device_status_after_play(self, device: Device, success: bool) -> None:

def auto_play_video(self, device: Device, video_path: str, loop: bool = True, 
                   config: Optional[Dict[str, Any]] = None) -> bool:
    if not self.validate_video_file(video_path):
        return False
    
    streaming_config = self.setup_streaming_server(video_path, device)
    success = self.start_device_playback(device, streaming_config.url, loop)
    self.update_device_status_after_play(device, success)
    return success
```

**Issues**:
- Single method doing too many things
- Hard to test individual components
- Error handling scattered throughout

**Impact**: High - Core playback functionality

### High Priority Issues

#### 4. API Endpoint Return Types
**Files**: `web/backend/routers/*.py`

```python
# BEFORE (Generic returns)
def get_discovery_status() -> Dict:
def delete_video(video_id: int) -> Dict:
def stream_video(video_id: int, serve_ip: Optional[str]) -> Dict:

# AFTER (Specific return types)
@dataclass
class DiscoveryStatusResponse:
    is_running: bool
    last_scan_time: Optional[datetime]
    devices_found: int

def get_discovery_status() -> DiscoveryStatusResponse:
def delete_video(video_id: int) -> DeleteVideoResponse:
def stream_video(video_id: int, serve_ip: Optional[str]) -> StreamVideoResponse:
```

**Issues**:
- Generic `Dict` returns provide no type safety
- API contract unclear from signatures
- Frontend integration lacks type information

**Impact**: Medium-High - API consistency

#### 5. Service Layer Type Improvements
**File**: `web/backend/services/device_service.py`

```python
# BEFORE (Missing return type)
def get_device_instance(self, device_id: int):
def discover_devices(self, timeout: float = 5.0):

# AFTER (Explicit return types)
def get_device_instance(self, device_id: int) -> Optional[Device]:
def discover_devices(self, timeout: float = 5.0) -> List[DeviceInfo]:
```

### Medium Priority Issues

#### 6. Boolean Trap Elimination
**File**: `web/backend/core/dlna_device.py`

```python
# BEFORE (Boolean trap)
def play(self, video_url: str, loop: bool = False) -> bool:

# AFTER (Enum-based)
from enum import Enum

class PlaybackMode(Enum):
    ONCE = "once"
    LOOP = "loop"
    SHUFFLE = "shuffle"

def play(self, video_url: str, mode: PlaybackMode = PlaybackMode.ONCE) -> bool:
```

#### 7. Magic Number Elimination
**File**: `web/backend/core/dlna_device.py`

```python
# BEFORE (Magic numbers)
def find_device_with_retry(args, device_name=None, max_retries=99999999, sleep_interval=5):

# AFTER (Named constants)
MAX_RETRY_ATTEMPTS = sys.maxsize
DEFAULT_SLEEP_INTERVAL = 5

def find_device_with_retry(
    args: argparse.Namespace, 
    device_name: Optional[str] = None, 
    max_retries: int = MAX_RETRY_ATTEMPTS, 
    sleep_interval: int = DEFAULT_SLEEP_INTERVAL
) -> Optional[Device]:
```

### Low Priority Issues

#### 8. Constructor Type Annotations
**Files**: Various service classes

```python
# BEFORE
def __init__(self):

# AFTER
def __init__(self) -> None:
```

#### 9. Private Method Type Hints
**Files**: Internal service methods

```python
# BEFORE
def _handle_streaming_issue(self, session):

# AFTER
def _handle_streaming_issue(self, session: StreamingSession) -> None:
```

## Implementation Strategy

### Week 1: Critical Issues
1. **Day 1-2**: CLI module type annotations
2. **Day 3-4**: DeviceManager signature cleanup
3. **Day 5**: DLNADevice method decomposition planning

### Week 2: High Priority Issues
1. **Day 1-3**: API endpoint return type standardization
2. **Day 4-5**: Service layer type improvements

### Week 3: Medium Priority Issues
1. **Day 1-2**: Boolean trap elimination
2. **Day 3-4**: Magic number cleanup
3. **Day 5**: Testing and validation

### Week 4: Low Priority & Documentation
1. **Day 1-2**: Constructor and private method annotations
2. **Day 3-4**: Documentation updates
3. **Day 5**: Final testing and validation

## Tools and Automation

### Type Checking
```bash
# Install mypy for type checking
pip install mypy

# Run type checking
mypy web/backend/ --strict
```

### Code Quality Tools
```bash
# Install black for formatting
pip install black

# Install pylint for code analysis
pip install pylint

# Run formatting
black web/backend/
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

## Success Metrics

### Type Safety
- [ ] 100% of public methods have return type annotations
- [ ] 95% of parameters have type hints
- [ ] All API endpoints use specific return types
- [ ] mypy passes with --strict flag

### Code Quality
- [ ] No functions with >5 parameters
- [ ] No methods with >50 lines
- [ ] All boolean parameters replaced with enums
- [ ] All magic numbers replaced with constants

### Testing
- [ ] All refactored methods have unit tests
- [ ] Integration tests pass after changes
- [ ] No performance regression in core functionality

## Risk Mitigation

### Backward Compatibility
- Keep old method signatures during transition period
- Add deprecation warnings for old interfaces
- Provide migration guides for API changes

### Testing Strategy
- Comprehensive unit tests for refactored methods
- Integration tests for API changes
- Performance benchmarks for critical paths

### Rollback Plan
- Feature flags for new implementations
- Blue-green deployment for API changes
- Database migration rollback scripts

This cleanup plan provides a systematic approach to improving function signatures across the codebase while maintaining stability and backward compatibility.