#!/usr/bin/env python3
"""
DreamPi Server Switcher Portal - Fixed for actual repository structure
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
DREAMPI_BACKUP = os.path.join(DREAMPI_DIR, "dreampi_original_backup.py")

# Look for scripts in subdirectories
DCNET_V2_DIR = os.path.join(SCRIPTS_DIR, "DCNET_V2")
DCNET_VM_DIR = os.path.join(SCRIPTS_DIR, "DCNET_VM")

def find_dcnet_script():
    """Find the DCNet on/off script in various locations"""
    possible_locations = [
        os.path.join(DCNET_V2_DIR, "dcnet_on_off.sh"),
        os.path.join(DCNET_VM_DIR, "dcnet_on_off.sh"),
        os.path.join(SCRIPTS_DIR, "dcnet_on_off.sh")
    ]
    
    for location in possible_locations:
        if os.path.exists(location):
            return location
    return None

def find_dreampi_files():
    """Find all dreampi.py variants"""
    files = {
        'original': None,
        'dcnet': None
    }
    
    # Look for original DCLive version
    if os.path.exists(os.path.join(SCRIPTS_DIR, "dreampi.py")):
        files['original'] = os.path.join(SCRIPTS_DIR, "dreampi.py")
    
    # Look for DCNet version in subdirectories
    for subdir in [DCNET_V2_DIR, DCNET_VM_DIR]:
        if os.path.exists(subdir):
            for file in os.listdir(subdir):
                if file.endswith('.py') and 'dreampi' in file:
                    files['dcnet'] = os.path.join(subdir, file)
                    break
    
    return files

def get_current_server():
    """Detect current server"""
    try:
        with open(DREAMPI_SCRIPT, 'r') as f:
            content = f.read().lower()
            if 'dcnet' in content or 'dc-net' in content or 'flycast' in content:
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
    """Create backup of original dreampi.py if it doesn't exist"""
    if not os.path.exists(DREAMPI_BACKUP) and os.path.exists(DREAMPI_SCRIPT):
        shutil.copy2(DREAMPI_SCRIPT, DREAMPI_BACKUP)
        print("Created backup: {}".format(DREAMPI_BACKUP))

@app.route('/')
def index():
    return render_template('index.html', 
                         current_server=get_current_server(),
                         dreampi_active=is_dreampi_active())

@app.route('/api/switch/<server>')
def switch_server(server):
    """Switch server using the correct scripts"""
    try:
        # Create backup first
        create_backup()
        
        # Find available scripts
        dcnet_script = find_dcnet_script()
        dreampi_files = find_dreampi_files()
        
        if server == 'dclive':
            # Switch to DCLive
            print("Switching to DCLive...")
            
            # Try to use the on/off script if it exists
            if dcnet_script and os.path.exists(dcnet_script):
                # Some scripts toggle, so we might need to run it to switch back
                print("Running DCNet script to switch back to DCLive: {}".format(dcnet_script))
                result = subprocess.Popen(['sudo', 'bash', dcnet_script, 'off'], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = result.communicate()
                print("Script output: {}".format(stdout.decode('utf-8')))
                if stderr:
                    print("Script error: {}".format(stderr.decode('utf-8')))
            
            # If we have a backup or original file, use it
            if os.path.exists(DREAMPI_BACKUP):
                print("Restoring from backup")
                subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
                time.sleep(2)
                shutil.copy2(DREAMPI_BACKUP, DREAMPI_SCRIPT)
                subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
            elif dreampi_files['original']:
                print("Using original dreampi.py from repository")
                subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
                time.sleep(2)
                shutil.copy2(dreampi_files['original'], DREAMPI_SCRIPT)
                subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
            else:
                return jsonify({'success': False, 'error': 'No original dreampi.py found'})
            
        elif server == 'dcnet':
            # Switch to DCNet
            print("Switching to DCNet...")
            
            # First try the on/off script
            if dcnet_script and os.path.exists(dcnet_script):
                print("Running DCNet script: {}".format(dcnet_script))
                result = subprocess.Popen(['sudo', 'bash', dcnet_script, 'on'], 
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = result.communicate()
                print("Script output: {}".format(stdout.decode('utf-8')))
                if stderr:
                    print("Script error: {}".format(stderr.decode('utf-8')))
            
            # If that doesn't work, try copying a DCNet dreampi.py
            elif dreampi_files['dcnet']:
                print("Using DCNet dreampi.py from: {}".format(dreampi_files['dcnet']))
                subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
                time.sleep(2)
                shutil.copy2(dreampi_files['dcnet'], DREAMPI_SCRIPT)
                subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
            else:
                return jsonify({'success': False, 'error': 'No DCNet script or dreampi.py found'})
        
        else:
            return jsonify({'success': False, 'error': 'Invalid server'})
        
        # Wait for service to restart
        time.sleep(5)
        
        # Check result
        new_server = get_current_server()
        dreampi_active = is_dreampi_active()
        
        return jsonify({
            'success': dreampi_active and new_server == server,
            'current_server': new_server,
            'dreampi_active': dreampi_active,
            'dcnet_script': dcnet_script,
            'dreampi_files': dreampi_files
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def status():
    dcnet_script = find_dcnet_script()
    dreampi_files = find_dreampi_files()
    
    return jsonify({
        'current_server': get_current_server(),
        'dreampi_active': is_dreampi_active(),
        'scripts_found': {
            'dcnet_script': dcnet_script,
            'dreampi_files': dreampi_files
        }
    })

@app.route('/api/debug')
def debug():
    """Debug endpoint to see all available files"""
    info = {
        'main_dir': [],
        'dcnet_v2': [],
        'dcnet_vm': []
    }
    
    # List main directory
    if os.path.exists(SCRIPTS_DIR):
        info['main_dir'] = os.listdir(SCRIPTS_DIR)
    
    # List DCNET_V2
    if os.path.exists(DCNET_V2_DIR):
        info['dcnet_v2'] = os.listdir(DCNET_V2_DIR)
    
    # List DCNET_VM
    if os.path.exists(DCNET_VM_DIR):
        info['dcnet_vm'] = os.listdir(DCNET_VM_DIR)
    
    # Find all .sh files
    sh_files = []
    for root, dirs, files in os.walk(SCRIPTS_DIR):
        for file in files:
            if file.endswith('.sh'):
                sh_files.append(os.path.join(root, file))
    
    info['all_sh_files'] = sh_files
    
    return jsonify(info)

if __name__ == '__main__':
    print("DreamPi Portal starting...")
    print("Looking for scripts...")
    dcnet_script = find_dcnet_script()
    if dcnet_script:
        print("Found DCNet script at: {}".format(dcnet_script))
    else:
        print("WARNING: No DCNet script found!")
    
    dreampi_files = find_dreampi_files()
    print("Found dreampi files: {}".format(dreampi_files))
    
    app.run(host='0.0.0.0', port=8080, debug=False)
