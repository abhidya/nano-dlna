#!/usr/bin/env python3
# encoding: UTF-8

import os
import socket
import threading
import unicodedata
import re
import tempfile
import time

import twisted.internet.error
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File

import logging
import json
from typing import Dict, Any, Optional

# from twisted.python import log

# Create logger
logger = logging.getLogger(__name__)

# Global flag to track if the reactor is running
reactor_running = False
reactor_lock = threading.Lock()

# Global flag to track if there's a thread active
server_thread = None
server_active = False

def normalize_file_name(value):
    value = unicodedata\
        .normalize("NFKD", value)\
        .encode("ascii", "ignore")\
        .decode("ascii")
    value = re.sub(r"[^\.\w\s-]", "", value.lower())
    value = re.sub(r"[-\s]+", "-", value).strip("-_")
    return value


def set_files(files, serve_ip, serve_port):

    logging.debug("Setting streaming files: {}".format(
        json.dumps({
            "files": files,
            "serve_ip": serve_ip,
            "serve_port": serve_port
        })
    ))

    files_index = {file_key: (normalize_file_name(os.path.basename(file_path)),
                              os.path.abspath(file_path),
                              os.path.dirname(os.path.abspath(file_path)))
                   for file_key, file_path in files.items()}

    files_serve = {file_name: file_path
                   for file_name, file_path, file_dir in files_index.values()}

    files_urls = {
        file_key: "http://{0}:{1}/{2}/{3}".format(
            serve_ip, serve_port, file_key, file_name)
        for file_key, (file_name, file_path, file_dir)
        in files_index.items()}

    logging.debug("Streaming files information: {}".format(
        json.dumps({
            "files_index": files_index,
            "files_serve": files_serve,
            "files_urls": files_urls
        })
    ))

    return files_index, files_serve, files_urls

class FileStreamer(Resource):
    """
    File streamer resource for Twisted Web.
    """
    
    isLeaf = True
    
    def __init__(self, files_dict: Dict[str, str]) -> None:
        """
        Constructor.
        
        Args:
            files_dict: Dictionary mapping file names to file paths.
        """
        super().__init__()
        self.files_dict = files_dict
        
    def render_GET(self, request: Any) -> bytes:
        """
        Render GET request.
        
        Args:
            request: Request object.
            
        Returns:
            bytes: Response.
        """
        # Get file index and file path
        file_index = request.path.decode("utf-8").lstrip("/")
        
        if file_index in self.files_dict:
            file_path = self.files_dict[file_index]
            logger.debug("Streaming file: %s", file_path)
            
            # Stream the file
            try:
                file_handle = open(file_path, "rb")
                request.setResponseCode(200)
                
                # Set content type based on file extension
                if file_path.endswith(".srt"):
                    request.setHeader(b"Content-Type", b"text/srt")
                else:
                    request.setHeader(b"Content-Type", b"video/mp4")
                
                # Stream the file in chunks to avoid loading the whole file into memory
                chunk_size = 1024 * 1024  # 1 MB
                data = file_handle.read(chunk_size)
                while data:
                    request.write(data)
                    data = file_handle.read(chunk_size)
                
                file_handle.close()
                return b""
            except OSError as e:
                logger.error("Error streaming file: %s", e)
                request.setResponseCode(500)
                return b"Error streaming file"
        else:
            logger.error("File not found: %s", file_index)
            request.setResponseCode(404)
            return b"File not found"


def start_server(files_dict: Dict[str, str], ip: str = "0.0.0.0", port: int = 9000) -> tuple:
    """
    Start a streaming server.
    
    Args:
        files_dict: Dictionary mapping file names to file paths.
        ip: IP address to bind to.
        port: Port to bind to.
        
    Returns:
        tuple: URL mapping and server object.
    """
    global reactor_running, server_thread, server_active, reactor_lock
    
    # Create URL mapping
    url_dict = {}
    for file_index, file_path in files_dict.items():
        url_dict[file_index] = f"http://{ip}:{port}/{file_index}"
    
    # Create server resource
    file_streamer = FileStreamer(files_dict)
    site = Site(file_streamer)
    
    # Start the server in a thread
    def run_server():
        global reactor_running, server_active, reactor_lock
        try:
            with reactor_lock:
                if not reactor_running:
                    logger.debug("Starting reactor")
                    reactor_running = True
                    server_active = True
                    
                    # Start the server
                    try:
                        reactor.listenTCP(port, site, interface=ip)
                        reactor.run(installSignalHandlers=False)
                    except twisted.internet.error.CannotListenError:
                        logger.error(f"Cannot listen on port {port}, it might already be in use")
                        reactor_running = False
                        server_active = False
                    except Exception as e:
                        logger.error(f"Error starting reactor: {e}")
                        reactor_running = False
                        server_active = False
                else:
                    logger.debug("Reactor already running, not starting it again")
                    server_active = True
        except Exception as e:
            logger.error(f"Error in run_server: {e}")
            with reactor_lock:
                reactor_running = False
                server_active = False
    
    with reactor_lock:
        if server_thread is None or not server_thread.is_alive():
            # Create a new thread if one doesn't exist or if it's not alive
            server_thread = threading.Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()
            # Small delay to give the reactor time to start
            time.sleep(0.5)
        else:
            logger.debug("Server thread already running")
            server_active = True
    
    return url_dict, None  # Return None for server for backwards compatibility


def stop_server() -> None:
    """
    Stop the streaming server.
    """
    global reactor_running, server_active, reactor_lock
    
    with reactor_lock:
        if not reactor_running:
            logger.debug("Reactor not running, nothing to stop")
            return
        
        try:
            logger.debug("Stopping reactor")
            reactor.callFromThread(reactor.stop)
            reactor_running = False
            server_active = False
        except twisted.internet.error.ReactorNotRunning:
            logger.debug("Reactor not running (ReactorNotRunning exception)")
            reactor_running = False
            server_active = False
        except Exception as e:
            logger.error(f"Error stopping reactor: {e}")
            # Force reactor_running to be False to allow restarting
            reactor_running = False
            server_active = False


def is_server_active() -> bool:
    """
    Check if the server is active.
    
    Returns:
        bool: True if the server is active, False otherwise.
    """
    global server_active
    return server_active

def get_serve_ip(target_ip, target_port=80):
    logging.debug("Identifying server IP")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect((target_ip, target_port))
    serve_ip = s.getsockname()[0]
    s.close()
    logging.debug("Server IP identified: {}".format(serve_ip))
    return serve_ip


if __name__ == "__main__":

    import sys

    files = {"file_{0}".format(i): file_path for i,
             file_path in enumerate(sys.argv[1:], 1)}
    print(files)

    files_urls = start_server(files, "localhost")
    print(files_urls)
