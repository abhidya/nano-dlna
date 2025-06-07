"""
Direct output implementation for local displays.
"""

import logging
import os
import subprocess
import time
from typing import Dict, Optional

from .base import Sender


class DirectSender(Sender):
    """Direct output implementation for local display."""
    
    def __init__(self, config: Dict, logger: Optional[logging.Logger] = None):
        """Initialize the Direct sender.
        
        Args:
            config: Configuration dictionary with Direct-specific parameters:
                - default_display: Default display to use (default: 0)
                - browser_path: Path to browser executable (optional)
                - kiosk_mode: Whether to use kiosk mode (default: True)
            logger: Optional logger for sender logging
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Set configuration values
        self.default_display = config.get("default_display", 0)
        self.browser_path = config.get("browser_path", "")
        self.kiosk_mode = config.get("kiosk_mode", True)
        
        # Instance variables
        self.display = self.default_display
        self.connected = False
        self.process = None
        self.content_url = None
    
    def connect(self, target_id: str) -> bool:
        """Connect to the specified display.
        
        Args:
            target_id: Display number or identifier
            
        Returns:
            bool: True if connection was successful, False otherwise
        """
        try:
            # For direct display, target_id is typically the display number
            self.display = int(target_id)
        except ValueError:
            self.logger.warning(f"Invalid display number: {target_id}, using default: {self.default_display}")
            self.display = self.default_display
            
        self.logger.info(f"Connected to display: {self.display}")
        self.connected = True
        return True
    
    def disconnect(self) -> bool:
        """Disconnect from the display by terminating any running browser process.
        
        Returns:
            bool: True if disconnection was successful, False otherwise
        """
        if self.process:
            try:
                self.logger.info(f"Terminating browser process on display {self.display}")
                self.process.terminate()
                
                # Give it a moment to terminate gracefully
                time.sleep(0.5)
                
                # Force kill if still running
                if self.process.poll() is None:
                    self.process.kill()
                    
                self.process = None
                
            except Exception as e:
                self.logger.error(f"Error terminating browser process: {str(e)}")
                # Consider disconnection successful even if there was an error
        
        self.connected = False
        self.content_url = None
        return True
    
    def send_content(self, content_url: str) -> bool:
        """Display content on the local display by launching a browser.
        
        Args:
            content_url: URL or file path to the content to be displayed
            
        Returns:
            bool: True if content was successfully sent, False otherwise
        """
        if not self.connected:
            self.logger.warning("Cannot send content - not connected to display")
            return False
            
        # If there's already a process running, terminate it first
        if self.process and self.process.poll() is None:
            self.disconnect()
            
        try:
            # Determine browser path
            browser_cmd = self._get_browser_command()
            if not browser_cmd:
                self.logger.error("No suitable browser found")
                return False
                
            # Prepare the command with arguments
            cmd = self._prepare_browser_command(browser_cmd, content_url)
            
            # Launch the browser
            self.logger.info(f"Launching browser with command: {' '.join(cmd)}")
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Store content URL
            self.content_url = content_url
            
            # Wait briefly to see if the process stays alive
            time.sleep(0.5)
            if self.process.poll() is not None:
                stderr = self.process.stderr.read().decode('utf-8')
                self.logger.error(f"Browser process exited immediately: {stderr}")
                return False
                
            self.logger.info(f"Content {content_url} displayed on display {self.display}")
            return True
                
        except Exception as e:
            self.logger.error(f"Error displaying content: {str(e)}")
            return False
    
    def _get_browser_command(self) -> str:
        """Get the browser command to use.
        
        Returns:
            str: Path to browser executable or command
        """
        # Use specified browser if available
        if self.browser_path and os.path.exists(self.browser_path):
            return self.browser_path
            
        # Common browser paths on macOS
        mac_browsers = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Safari.app/Contents/MacOS/Safari",
            "/Applications/Firefox.app/Contents/MacOS/firefox"
        ]
        
        # Common browser paths on Linux
        linux_browsers = [
            "/usr/bin/google-chrome",
            "/usr/bin/firefox",
            "/usr/bin/chromium-browser"
        ]
        
        # Check common paths
        for browser in mac_browsers + linux_browsers:
            if os.path.exists(browser):
                return browser
                
        # Fall back to standard commands
        for browser in ["google-chrome", "chrome", "firefox", "safari"]:
            try:
                result = subprocess.run(["which", browser], capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout.strip()
            except:
                pass
                
        # Last resort - try the webbrowser module in a subprocess
        return "python"
    
    def _prepare_browser_command(self, browser_cmd: str, content_url: str) -> list:
        """Prepare the browser command with appropriate arguments.
        
        Args:
            browser_cmd: Browser command or path
            content_url: URL to display
            
        Returns:
            list: Command and arguments as a list
        """
        if browser_cmd == "python":
            # Use Python's webbrowser module as a last resort
            return [
                "python", 
                "-c", 
                f"import webbrowser; webbrowser.open('{content_url}')"
            ]
        
        # For Chrome/Chromium
        if "chrome" in browser_cmd.lower() or "chromium" in browser_cmd.lower():
            args = [browser_cmd]
            
            if self.kiosk_mode:
                args.extend(["--kiosk", "--disable-infobars", "--no-first-run"])
                
            # Add display number for X11 systems
            if os.name != "nt":  # Not Windows
                args.append(f"--display=:{self.display}")
                
            args.append(content_url)
            return args
            
        # For Firefox
        elif "firefox" in browser_cmd.lower():
            args = [browser_cmd]
            
            if self.kiosk_mode:
                args.append("--kiosk")
                
            # Add display setting for X11
            if os.name != "nt":  # Not Windows
                os.environ["DISPLAY"] = f":{self.display}"
                
            args.append(content_url)
            return args
            
        # Generic case
        return [browser_cmd, content_url]
    
    def is_connected(self) -> bool:
        """Check if still connected to display.
        
        Returns:
            bool: True if connected, False otherwise
        """
        # For direct display, consider connected if the display is set
        if not self.connected:
            return False
            
        # If there's a process, check if it's still running
        if self.process:
            is_running = self.process.poll() is None
            if not is_running and self.connected:
                self.logger.info(f"Browser process on display {self.display} has terminated")
                self.connected = False
                
        return self.connected
    
    def get_status(self) -> Dict:
        """Get current status information.
        
        Returns:
            Dict: Status information dictionary
        """
        status = {
            "type": "direct",
            "connected": self.is_connected(),
            "display": self.display
        }
        
        # Add process status if available
        if self.process:
            status["process_running"] = self.process.poll() is None
            
        # Add content URL if available
        if self.content_url:
            status["content_url"] = self.content_url
            
        return status
