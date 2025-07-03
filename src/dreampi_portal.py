#!/usr/bin/env python3
"""
DreamPi Server Switcher Portal - Works with actual repository structure
"""

from flask import Flask, render_template, jsonify
import subprocess
import os
import time
import shutil

app = Flask(__name__)

# --- Paths ---
SCRIPTS_DIR = "/home/pi/dreampi_custom_scripts"
DREAMPI_DIR = "/home/pi/dreampi"
DREAMPI_SCRIPT = os.path.join(DREAMPI_DIR, "dreampi.py")
DREAMPI_BACKUP = os.path.join(DREAMPI_DIR, "dreampi_original.py")

# --- Script files in the repository ---
DCNET_V2_DIR = os.path.join(SCRIPTS_DIR, "DCNET_V2")
# *** FIXED PATH ***: Point to the script inside the DCNET_V2 directory
DCNET_SCRIPT = os.path.join(DCNET_V2_DIR, "dcnet_on_off.sh") 
DREAMPI_ORIGINAL = os.path.join(SCRIPTS_DIR, "dreampi.py")  # Original DCLive version

def get_current_server():
    """Detect current server"""
    try:
        with open(DREAMPI_SCRIPT, 'r') as f:
            content = f.read().lower()
            if 'dcnet' in content or 'dc-net' in content or 'flycast' in content:
                return "dcnet"
        return "dclive"
    except FileNotFoundError:
        return "unknown"
    except Exception:
        return "unknown"

def is_dreampi_active():
    """Check if dreampi service is running"""
    try:
        proc = subprocess.Popen(['systemctl', 'is-active', 'dreampi'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        return stdout.decode('utf-8').strip() == 'active'
    except Exception:
        return False

def create_backup():
    """Create backup of original dreampi.py if it doesn't exist"""
    if not os.path.exists(DREAMPI_BACKUP):
        # Only create a backup if the main dreampi.py exists
        if os.path.exists(DREAMPI_SCRIPT):
            shutil.copy2(DREAMPI_SCRIPT, DREAMPI_BACKUP)
            print("Created backup: {}".format(DREAMPI_BACKUP))

@app.route('/')
def index():
    return render_template('index.html',
                         current_server=get_current_server(),
                         dreampi_active=is_dreampi_active())

@app.route('/api/switch/<server>')
def switch_server(server):
    """Switch server"""
    try:
        # Create backup first
        create_backup()

        # Stop DreamPi service
        subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
        time.sleep(2)

        if server == 'dclive':
            # Switch to DCLive (original)
            if os.path.exists(DREAMPI_BACKUP):
                # Use our backup
                shutil.copy2(DREAMPI_BACKUP, DREAMPI_SCRIPT)
            elif os.path.exists(DREAMPI_ORIGINAL):
                # Use the one from the repository
                shutil.copy2(DREAMPI_ORIGINAL, DREAMPI_SCRIPT)
            else:
                return jsonify({'success': False, 'error': 'No original dreampi.py found'})

        elif server == 'dcnet':
            # Check if we have a DCNet version of dreampi.py
            dcnet_v2_script_py = None
            
            # Look for dreampi.py in DCNET_V2 directory
            if os.path.exists(DCNET_V2_DIR):
                for file in os.listdir(DCNET_V2_DIR):
                    if file == 'dreampi.py' or file.endswith('_dreampi.py'):
                        dcnet_v2_script_py = os.path.join(DCNET_V2_DIR, file)
                        break
            
            if dcnet_v2_script_py and os.path.exists(dcnet_v2_script_py):
                # If a python script for dcnet exists, copy it
                shutil.copy2(dcnet_v2_script_py, DREAMPI_SCRIPT)
            elif os.path.exists(DCNET_SCRIPT):
                # Otherwise, try running the dcnet_on_off.sh script from the correct path
                # Make sure the script is executable first
                subprocess.call(['sudo', 'chmod', '+x', DCNET_SCRIPT])
                subprocess.call(['sudo', 'bash', DCNET_SCRIPT])
            else:
                return jsonify({'success': False, 'error': 'No DCNet script (python or shell) found'})
        else:
            return jsonify({'success': False, 'error': 'Invalid server'})

        # Ensure correct permissions on the active dreampi.py
        os.chmod(DREAMPI_SCRIPT, 0o755)

        # Start DreamPi service
        subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
        time.sleep(5)

        # Check result
        new_server = get_current_server()
        dreampi_active = is_dreampi_active()

        return jsonify({
            'success': dreampi_active and new_server == server,
            'current_server': new_server,
            'dreampi_active': dreampi_active
        })

    except Exception as e:
        # Try to restart dreampi on failure to avoid leaving it stopped
        subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def status():
    """Get current status and available scripts"""
    scripts = {}
    if os.path.exists(SCRIPTS_DIR):
        scripts['dcnet_on_off.sh_exists'] = os.path.exists(DCNET_SCRIPT)
        scripts['original_dreampi.py_exists'] = os.path.exists(DREAMPI_ORIGINAL)
        scripts['backup_exists'] = os.path.exists(DREAMPI_BACKUP)
        scripts['dcnet_v2_dir_exists'] = os.path.exists(DCNET_V2_DIR)
        
        # Check what's in DCNET_V2
        if os.path.exists(DCNET_V2_DIR):
            scripts['dcnet_v2_files'] = os.listdir(DCNET_V2_DIR)
    
    return jsonify({
        'current_server': get_current_server(),
        'dreampi_active': is_dreampi_active(),
        'scripts': scripts
    })

@app.route('/api/check-scripts')
def check_scripts():
    """Debug endpoint to see what scripts we have"""
    info = {
        'scripts_dir_exists': os.path.exists(SCRIPTS_DIR),
        'files_in_scripts_dir': []
    }
    
    if os.path.exists(SCRIPTS_DIR):
        for item in os.listdir(SCRIPTS_DIR):
            item_path = os.path.join(SCRIPTS_DIR, item)
            info['files_in_scripts_dir'].append({
                'name': item,
                'is_dir': os.path.isdir(item_path),
                'executable': os.access(item_path, os.X_OK)
            })
    
    return jsonify(info)

if __name__ == '__main__':
    print("DreamPi Portal starting...")
    print("Scripts directory: {}".format(SCRIPTS_DIR))
    print("DCNET script path: {}".format(DCNET_SCRIPT))
    app.run(host='0.0.0.0', port=8080, debug=False)
