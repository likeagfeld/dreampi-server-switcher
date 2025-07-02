#!/usr/bin/env python3
"""
DreamPi Server Switcher Web Portal - Production Version
======================================================
"""

from flask import Flask, render_template, request, jsonify
import os
import subprocess
import shutil
import json
import logging
import time
from datetime import datetime
import urllib.request
import sys

app = Flask(__name__)

# Configuration
DREAMPI_DIR = "/home/pi/dreampi"
DREAMPI_SCRIPT = f"{DREAMPI_DIR}/dreampi.py"
DREAMPI_ORIGINAL_BACKUP = f"{DREAMPI_DIR}/dreampi_original.py"
DREAMPI_DCNET_BACKUP = f"{DREAMPI_DIR}/dreampi_dcnet.py"
LOG_FILE = "/var/log/dreampi_portal.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DreamPiController:
    def __init__(self):
        self.validate_environment()
        self.current_server = self.detect_current_server()
    
    def validate_environment(self):
        if not os.path.exists(DREAMPI_DIR):
            raise Exception(f"DreamPi directory not found: {DREAMPI_DIR}")
        if not os.path.exists(DREAMPI_SCRIPT):
            raise Exception(f"DreamPi script not found: {DREAMPI_SCRIPT}")
    
    def detect_current_server(self):
        try:
            if os.path.exists(DREAMPI_SCRIPT):
                with open(DREAMPI_SCRIPT, 'r') as f:
                    content = f.read()
                    if 'dcnet' in content.lower() or 'DCNET_MODE = True' in content:
                        return "dcnet"
            return "dclive"
        except Exception as e:
            logger.error(f"Error detecting current server: {e}")
            return "unknown"
    
    def get_service_status(self):
        try:
            result = subprocess.run(['systemctl', 'is-active', 'dreampi'], 
                                  capture_output=True, text=True)
            status = result.stdout.strip()
            return {'active': status == 'active', 'status': status}
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {'active': False, 'status': 'error'}
    
    def create_backups(self):
        try:
            if os.path.exists(DREAMPI_SCRIPT) and not os.path.exists(DREAMPI_ORIGINAL_BACKUP):
                shutil.copy2(DREAMPI_SCRIPT, DREAMPI_ORIGINAL_BACKUP)
                logger.info("Created original dreampi backup")
            return True
        except Exception as e:
            logger.error(f"Error creating backups: {e}")
            return False
    
    def create_dcnet_script(self):
        try:
            if not os.path.exists(DREAMPI_ORIGINAL_BACKUP):
                if not self.create_backups():
                    return False
            
            with open(DREAMPI_ORIGINAL_BACKUP, 'r') as f:
                content = f.read()
            
            # Simple DCNet marker
            modified_content = "# DCNet Mode Enabled\nDCNET_MODE = True\n\n" + content
            
            with open(DREAMPI_DCNET_BACKUP, 'w') as f:
                f.write(modified_content)
            
            os.chmod(DREAMPI_DCNET_BACKUP, 0o755)
            logger.info("Created DCNet script")
            return True
        except Exception as e:
            logger.error(f"Error creating DCNet script: {e}")
            return False
    
    def switch_to_dclive(self):
        try:
            if not os.path.exists(DREAMPI_ORIGINAL_BACKUP):
                return False
            
            subprocess.run(['sudo', 'systemctl', 'stop', 'dreampi'], check=True)
            time.sleep(2)
            shutil.copy2(DREAMPI_ORIGINAL_BACKUP, DREAMPI_SCRIPT)
            subprocess.run(['sudo', 'systemctl', 'start', 'dreampi'], check=True)
            
            self.current_server = "dclive"
            logger.info("Switched to DCLive")
            return True
        except Exception as e:
            logger.error(f"Error switching to DCLive: {e}")
            return False
    
    def switch_to_dcnet(self):
        try:
            if not os.path.exists(DREAMPI_DCNET_BACKUP):
                if not self.create_dcnet_script():
                    return False
            
            subprocess.run(['sudo', 'systemctl', 'stop', 'dreampi'], check=True)
            time.sleep(2)
            shutil.copy2(DREAMPI_DCNET_BACKUP, DREAMPI_SCRIPT)
            subprocess.run(['sudo', 'systemctl', 'start', 'dreampi'], check=True)
            
            self.current_server = "dcnet"
            logger.info("Switched to DCNet")
            return True
        except Exception as e:
            logger.error(f"Error switching to DCNet: {e}")
            return False
    
    def restart_service(self):
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'dreampi'], check=True)
            logger.info("DreamPi service restarted")
            return True
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False

# Initialize controller
try:
    controller = DreamPiController()
except Exception as e:
    logger.error(f"Controller init failed: {e}")
    class DummyController:
        def __init__(self):
            self.current_server = "unknown"
        def get_service_status(self):
            return {'active': False, 'status': 'error'}
        def switch_to_dclive(self): return False
        def switch_to_dcnet(self): return False
        def restart_service(self): return False
        def create_backups(self): return False
    controller = DummyController()

# Routes
@app.route('/')
def index():
    status = controller.get_service_status()
    return render_template('index.html', 
                         current_server=controller.current_server,
                         service_status=status)

@app.route('/api/status')
def api_status():
    return jsonify({
        'current_server': controller.current_server,
        'service_status': controller.get_service_status(),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/switch/<server>')
def api_switch(server):
    if server not in ['dclive', 'dcnet']:
        return jsonify({'success': False, 'error': 'Invalid server'}), 400
    
    success = controller.switch_to_dclive() if server == 'dclive' else controller.switch_to_dcnet()
    
    return jsonify({
        'success': success,
        'current_server': controller.current_server,
        'service_status': controller.get_service_status()
    })

@app.route('/api/restart')
def api_restart():
    success = controller.restart_service()
    return jsonify({
        'success': success,
        'service_status': controller.get_service_status()
    })

@app.route('/api/setup')
def api_setup():
    success = controller.create_backups()
    return jsonify({
        'success': success,
        'message': 'Setup completed' if success else 'Setup failed'
    })

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("WARNING: Should be run with sudo for full functionality")
    
    try:
        controller.create_backups()
    except:
        pass
    
    logger.info("Starting DreamPi Web Portal on port 8080")
    print("?? DreamPi Portal starting at http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
