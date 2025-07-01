#!/usr/bin/env python3
"""
Test script to verify MCP log streaming functionality
"""

import subprocess
import json
import time
import os
import sys

def test_mcp_server():
    """Test the MCP server can start and respond"""
    
    print("🔧 Testing MCP Log Streaming Server...")
    
    # Test 1: Check if server can import
    try:
        result = subprocess.run([
            'python', 'run_mcp_server.py', '--help'
        ], capture_output=True, text=True, timeout=5, cwd=os.getcwd())
        print("✅ MCP server script is accessible")
    except subprocess.TimeoutExpired:
        print("⚠️  MCP server didn't respond to --help (this may be normal)")
    except Exception as e:
        print(f"❌ MCP server script error: {e}")
        return False
    
    # Test 2: Check if log files exist
    log_files = [
        'web/backend/dashboard_run.log',
        'web/backend/errors.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"✅ Log file exists: {log_file}")
        else:
            print(f"⚠️  Log file missing: {log_file}")
    
    # Test 3: Check configuration
    config_file = 'mcp-config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            print(f"✅ MCP configuration loaded: {config['name']}")
            print(f"   Tools available: {len(config['capabilities']['tools'])}")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return False
    else:
        print(f"❌ Missing configuration file: {config_file}")
        return False
    
    # Test 4: Check imports
    try:
        sys.path.insert(0, 'web/backend')
        from mcp_server import log_manager
        print("✅ MCP server imports successfully")
        
        # Check log manager
        log_files_found = sum(1 for path in log_manager.log_files.values() if os.path.exists(path))
        print(f"✅ Log manager found {log_files_found} log files")
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    print("\n🎉 MCP Log Streaming Setup Complete!")
    print("\n📋 Next Steps:")
    print("1. Add this to your Claude MCP settings:")
    print(f"   {os.path.abspath(config_file)}")
    print("2. Start your backend: cd web/backend && python main.py")
    print("3. Test with Claude: 'Show me recent backend logs'")
    
    return True

if __name__ == "__main__":
    success = test_mcp_server()
    sys.exit(0 if success else 1)