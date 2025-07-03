#!/usr/bin/env python3
"""
DreamPi Server Switcher Portal - Direct File Copy Version
Simply copies the correct dreampi.py files without relying on scripts
"""

from flask import Flask, render_template, jsonify
import subprocess
import os
import time
import shutil

app = Flask(__name__)

# Paths
SCRIPTS_DIR = "/home/pi/dreampi_custom_scripts"
DREAMPI_DIR = "/home/pi/dreampi"
DREAMPI_SCRIPT = os.path.join(DREAMPI_DIR, "dreampi.py")

# Known file locations
DCLIVE_SCRIPT = os.path.join(SCRIPTS_DIR, "dreampi.py")
DCNET_SCRIPT = os.path.join(SCRIPTS_DIR, "DCNET_V2", "dreampi_dcnet.py")

# Backup location
DREAMPI_BACKUP = os.path.join(DREAMPI_DIR, "dreampi_dclive_backup.py")

def get_current_server():
    """Detect current server by checking for dcnet references"""
    try:
        with open(DREAMPI_SCRIPT, 'r') as f:
            content = f.read()
            # Check for DCNet indicators
            if 'dcnet.rpi' in content or 'dreampi_dcnet' in content:
                return "dcnet"
        return "dclive"
    except:
        return "unknown"

def is_dreampi_active():
    """Check if dreampi service is running"""
    try:
        proc = subprocess.Popen(['systemctl', 'is-active', 'dreampi'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        return stdout.decode('utf-8').strip() == 'active'
    except:
        return False

def create_backup():
    """Create backup of DCLive version if needed"""
    # Only create backup if current version is DCLive
    if get_current_server() == "dclive" and not os.path.exists(DREAMPI_BACKUP):
        shutil.copy2(DREAMPI_SCRIPT, DREAMPI_BACKUP)
        print("Created DCLive backup: {}".format(DREAMPI_BACKUP))

@app.route('/')
def index():
    return render_template('index.html', 
                         current_server=get_current_server(),
                         dreampi_active=is_dreampi_active())

@app.route('/api/switch/<server>')
def switch_server(server):
    """Switch server by copying the appropriate dreampi.py file"""
    try:
        # Create backup of DCLive if needed
        create_backup()
        
        # Stop DreamPi service
        print("Stopping DreamPi service...")
        subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
        time.sleep(2)
        
        if server == 'dclive':
            # Switch to DCLive
            print("Switching to DCLive...")
            
            # Use backup if available
            if os.path.exists(DREAMPI_BACKUP):
                print("Restoring from DCLive backup")
                shutil.copy2(DREAMPI_BACKUP, DREAMPI_SCRIPT)
            elif os.path.exists(DCLIVE_SCRIPT):
                print("Copying DCLive script from repository")
                shutil.copy2(DCLIVE_SCRIPT, DREAMPI_SCRIPT)
            else:
                return jsonify({
                    'success': False, 
                    'error': 'No DCLive dreampi.py found',
                    'checked_locations': [DREAMPI_BACKUP, DCLIVE_SCRIPT]
                })
            
        elif server == 'dcnet':
            # Switch to DCNet
            print("Switching to DCNet...")
            
            if os.path.exists(DCNET_SCRIPT):
                print("Copying DCNet script from: {}".format(DCNET_SCRIPT))
                shutil.copy2(DCNET_SCRIPT, DREAMPI_SCRIPT)
            else:
                return jsonify({
                    'success': False, 
                    'error': 'DCNet dreampi.py not found',
                    'expected_location': DCNET_SCRIPT
                })
        
        else:
            return jsonify({'success': False, 'error': 'Invalid server'})
        
        # Ensure correct permissions
        os.chmod(DREAMPI_SCRIPT, 0o755)
        
        # Start DreamPi service
        print("Starting DreamPi service...")
        subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
        
        # Wait for service to fully start
        time.sleep(5)
        
        # Check result
        new_server = get_current_server()
        dreampi_active = is_dreampi_active()
        success = dreampi_active and new_server == server
        
        print("Switch result: server={}, active={}, success={}".format(
            new_server, dreampi_active, success))
        
        return jsonify({
            'success': success,
            'current_server': new_server,
            'dreampi_active': dreampi_active
        })
        
    except Exception as e:
        print("Error during switch: {}".format(str(e)))
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def status():
    return jsonify({
        'current_server': get_current_server(),
        'dreampi_active': is_dreampi_active(),
        'files_exist': {
            'dclive': os.path.exists(DCLIVE_SCRIPT),
            'dcnet': os.path.exists(DCNET_SCRIPT),
            'backup': os.path.exists(DREAMPI_BACKUP)
        }
    })

@app.route('/api/restart')
def restart():
    """Just restart the DreamPi service"""
    try:
        subprocess.call(['sudo', 'systemctl', 'restart', 'dreampi'])
        time.sleep(5)
        return jsonify({
            'success': True,
            'dreampi_active': is_dreampi_active()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("DreamPi Portal starting...")
    print("Current server: {}".format(get_current_server()))
    print("Files found:")
    print("  DCLive script: {}".format(os.path.exists(DCLIVE_SCRIPT)))
    print("  DCNet script: {}".format(os.path.exists(DCNET_SCRIPT)))
    print("  Backup exists: {}".format(os.path.exists(DREAMPI_BACKUP)))
    
    app.run(host='0.0.0.0', port=8080, debug=False)
