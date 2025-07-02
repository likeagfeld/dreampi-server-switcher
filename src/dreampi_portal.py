#!/usr/bin/env python3
"""
DreamPi Server Switcher Portal - Simplified Safe Version
Works with Python 3.5+ and minimal dependencies
"""

from flask import Flask, render_template, jsonify
import os
import subprocess
import shutil
import time

app = Flask(__name__)

# Configuration
DREAMPI_DIR = "/home/pi/dreampi"
DREAMPI_SCRIPT = os.path.join(DREAMPI_DIR, "dreampi.py")
DREAMPI_ORIGINAL_BACKUP = os.path.join(DREAMPI_DIR, "dreampi_original.py")
DREAMPI_DCNET_BACKUP = os.path.join(DREAMPI_DIR, "dreampi_dcnet.py")

class DreamPiController:
    def __init__(self):
        self.current_server = self.detect_current_server()
        print("DreamPi Controller initialized. Current server: {}".format(self.current_server))
    
    def detect_current_server(self):
        """Detect which server is currently active"""
        try:
            if os.path.exists(DREAMPI_SCRIPT):
                with open(DREAMPI_SCRIPT, 'r') as f:
                    content = f.read()
                    if 'dcnet' in content.lower() or 'DCNET_MODE = True' in content:
                        return "dcnet"
            return "dclive"
        except Exception as e:
            print("Error detecting server: {}".format(e))
            return "unknown"
    
    def get_service_status(self):
        """Get dreampi service status"""
        try:
            result = subprocess.Popen(
                ['systemctl', 'is-active', 'dreampi'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, _ = result.communicate()
            status = stdout.decode('utf-8').strip()
            return {'active': status == 'active', 'status': status}
        except Exception as e:
            print("Error getting service status: {}".format(e))
            return {'active': False, 'status': 'error'}
    
    def create_backups(self):
        """Create backup files if they don't exist"""
        try:
            # Create original backup if it doesn't exist
            if not os.path.exists(DREAMPI_ORIGINAL_BACKUP):
                if os.path.exists(DREAMPI_SCRIPT):
                    shutil.copy2(DREAMPI_SCRIPT, DREAMPI_ORIGINAL_BACKUP)
                    print("Created original dreampi backup")
                else:
                    print("No dreampi.py found to backup")
                    return False
            
            # Create DCNet version if it doesn't exist
            if not os.path.exists(DREAMPI_DCNET_BACKUP):
                with open(DREAMPI_ORIGINAL_BACKUP, 'r') as f:
                    content = f.read()
                
                # Add DCNet marker at the beginning
                modified_content = "#!/usr/bin/env python3\n# DCNet Mode Enabled\nDCNET_MODE = True\n\n" + content
                
                with open(DREAMPI_DCNET_BACKUP, 'w') as f:
                    f.write(modified_content)
                
                os.chmod(DREAMPI_DCNET_BACKUP, 0o755)
                print("Created DCNet script")
            
            return True
        except Exception as e:
            print("Error creating backups: {}".format(e))
            return False
    
    def switch_to_dclive(self):
        """Switch to DCLive server"""
        try:
            if not os.path.exists(DREAMPI_ORIGINAL_BACKUP):
                print("Original backup not found")
                return False
            
            # Stop service
            subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
            time.sleep(2)
            
            # Copy original script
            shutil.copy2(DREAMPI_ORIGINAL_BACKUP, DREAMPI_SCRIPT)
            
            # Start service
            subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
            
            self.current_server = "dclive"
            print("Switched to DCLive")
            return True
        except Exception as e:
            print("Error switching to DCLive: {}".format(e))
            return False
    
    def switch_to_dcnet(self):
        """Switch to DCNet server"""
        try:
            # Create backups first if needed
            if not os.path.exists(DREAMPI_DCNET_BACKUP):
                if not self.create_backups():
                    return False
            
            # Stop service
            subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
            time.sleep(2)
            
            # Copy DCNet script
            shutil.copy2(DREAMPI_DCNET_BACKUP, DREAMPI_SCRIPT)
            
            # Start service
            subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
            
            self.current_server = "dcnet"
            print("Switched to DCNet")
            return True
        except Exception as e:
            print("Error switching to DCNet: {}".format(e))
            return False
    
    def restart_service(self):
        """Restart DreamPi service"""
        try:
            subprocess.call(['sudo', 'systemctl', 'restart', 'dreampi'])
            print("DreamPi service restarted")
            return True
        except Exception as e:
            print("Error restarting service: {}".format(e))
            return False

# Initialize controller
try:
    controller = DreamPiController()
    controller.create_backups()  # Create backups on startup
except Exception as e:
    print("Failed to initialize controller: {}".format(e))
    controller = None

# Routes
@app.route('/')
def index():
    """Main page"""
    if controller:
        return render_template('index.html', 
                             current_server=controller.current_server,
                             service_status=controller.get_service_status())
    else:
        return "Error: Controller not initialized", 500

@app.route('/api/status')
def api_status():
    """Get current status"""
    if controller:
        return jsonify({
            'current_server': controller.current_server,
            'service_status': controller.get_service_status()
        })
    else:
        return jsonify({'error': 'Controller not initialized'}), 500

@app.route('/api/switch/<server>')
def api_switch(server):
    """Switch to specified server"""
    if not controller:
        return jsonify({'success': False, 'error': 'Controller not initialized'}), 500
    
    if server == 'dclive':
        success = controller.switch_to_dclive()
    elif server == 'dcnet':
        success = controller.switch_to_dcnet()
    else:
        return jsonify({'success': False, 'error': 'Invalid server'}), 400
    
    return jsonify({
        'success': success,
        'current_server': controller.current_server
    })

@app.route('/api/restart')
def api_restart():
    """Restart DreamPi service"""
    if controller:
        success = controller.restart_service()
        return jsonify({'success': success})
    else:
        return jsonify({'success': False, 'error': 'Controller not initialized'}), 500

if __name__ == '__main__':
    print("Starting DreamPi Portal on port 8080...")
    try:
        app.run(host='0.0.0.0', port=8080, debug=False)
    except Exception as e:
        print("Failed to start server: {}".format(e))
