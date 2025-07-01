"""
Mock streaming classes for testing
"""
import tempfile
import threading
from typing import Dict, Any, Optional, Tuple
from unittest.mock import MagicMock


class MockHTTPServer:
    """Mock HTTP server for testing"""
    
    def __init__(self, address: Tuple[str, int], handler_class):
        self.server_address = address
        self.handler_class = handler_class
        self.serving = False
        self.temp_dir = None
        
    def serve_forever(self):
        """Mock serve forever"""
        self.serving = True
        # In tests, this would normally block, but we'll just set a flag
        
    def shutdown(self):
        """Mock shutdown"""
        self.serving = False
        
    def server_close(self):
        """Mock server close"""
        pass


class MockStreamingService:
    """Mock streaming service for testing"""
    
    def __init__(self, device_manager=None):
        self.servers = {}
        self.temp_dirs = {}
        self.file_to_session_map = {}
        self.device_manager = device_manager
        self._next_port = 9000
        
    def get_serve_ip(self, target_ip: Optional[str] = None) -> str:
        """Mock get serve IP"""
        return "127.0.0.1"
        
    def start_server(self, files: Dict[str, str], serve_ip: str, 
                    serve_port: Optional[int] = None,
                    port_range: Optional[Tuple[int, int]] = None,
                    device_name: Optional[str] = None) -> Tuple[Dict[str, str], Any]:
        """Mock start server"""
        # Use the next available port
        if serve_port:
            port = serve_port
        else:
            port = self._next_port
            self._next_port += 1
            
        # Create mock URLs
        files_urls = {}
        for file_key, file_path in files.items():
            files_urls[file_key] = f"http://{serve_ip}:{port}/{file_key}"
            
        # Create mock server
        server = MockHTTPServer((serve_ip, port), None)
        server.temp_dir = tempfile.TemporaryDirectory()
        
        # Store server
        server_id = f"{serve_ip}:{port}"
        self.servers[server_id] = server
        self.temp_dirs[server_id] = server.temp_dir
        
        # Mock session registration
        if device_name:
            for file_key in files:
                session_id = f"session-{server_id}-{file_key}"
                self.file_to_session_map[f"{server_id}/{file_key}"] = session_id
        
        return files_urls, server
        
    def stop_server(self, server: Any) -> None:
        """Mock stop server"""
        # Find and remove server
        server_id = None
        for sid, s in list(self.servers.items()):
            if s == server:
                server_id = sid
                break
                
        if server_id:
            server.shutdown()
            del self.servers[server_id]
            if server_id in self.temp_dirs:
                self.temp_dirs[server_id].cleanup()
                del self.temp_dirs[server_id]
                
    def stop_all_servers(self) -> None:
        """Mock stop all servers"""
        for server_id, server in list(self.servers.items()):
            server.shutdown()
            if server_id in self.temp_dirs:
                self.temp_dirs[server_id].cleanup()
                
        self.servers.clear()
        self.temp_dirs.clear()
        self.file_to_session_map.clear()
        
    def get_or_create_stream(self, video_path: str, device_name: str = "overlay") -> Dict[str, Any]:
        """Mock get or create stream"""
        # Check for existing stream
        basename = video_path.split('/')[-1]
        for map_key, session_id in self.file_to_session_map.items():
            if basename in map_key:
                server_part = map_key.split('/')[0]
                port = int(server_part.split(':')[1])
                return {
                    "port": port,
                    "url": f"http://{server_part}/{basename}"
                }
                
        # Create new stream
        files = {"video": video_path}
        serve_ip = self.get_serve_ip()
        files_urls, server = self.start_server(
            files=files,
            serve_ip=serve_ip,
            port_range=(9000, 9100),
            device_name=device_name
        )
        
        return {
            "port": server.server_address[1],
            "url": files_urls["video"]
        }


class MockStreamingSessionRegistry:
    """Mock streaming session registry"""
    
    def __init__(self):
        self.sessions = {}
        
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if not hasattr(cls, '_instance'):
            cls._instance = cls()
        return cls._instance
        
    def register_session(self, device_name: str, video_path: str,
                        server_ip: str, server_port: int) -> MagicMock:
        """Mock register session"""
        session = MagicMock()
        session.session_id = f"session-{device_name}-{server_port}"
        session.device_name = device_name
        session.video_path = video_path
        session.server_ip = server_ip
        session.server_port = server_port
        session.status = "active"
        session.active = True
        
        self.sessions[session.session_id] = session
        return session
        
    def unregister_session(self, session_id: str):
        """Mock unregister session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            
    def get_session(self, session_id: str):
        """Mock get session"""
        return self.sessions.get(session_id)
        
    def update_session_activity(self, session_id: str, **kwargs):
        """Mock update session activity"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            for key, value in kwargs.items():
                setattr(session, key, value)