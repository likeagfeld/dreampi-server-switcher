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

# Paths
SCRIPTS_DIR = "/home/pi/dreampi_custom_scripts"
DREAMPI_DIR = "/home/pi/dreampi"
DREAMPI_SCRIPT = os.path.join(DREAMPI_DIR, "dreampi.py")
DREAMPI_BACKUP = os.path.join(DREAMPI_DIR, "dreampi_original.py")

# Script files in the repository
DCNET_V2_DIR = os.path.join(SCRIPTS_DIR, "DCNET_V2")
# CORRECTED PATH: dcnet_on_off.sh is inside DCNET_V2 subdirectory
DCNET_SCRIPT = os.path.join(DCNET_V2_DIR, "dcnet_on_off.sh")
# Ensured no invisible characters on this line
DREAMPI_ORIGINAL = os.path.join(SCRIPTS_DIR, "dreampi.py")  # Original DCLive version


def get_current_server():
    """Detect current server"""
    try:
        with open(DREAMPI_SCRIPT, 'r') as f:
            content = f.read().lower()
            if 'dcnet' in content or 'dc-net' in content or 'flycast' in content:
                return "dcnet"
        return "dclive"
    except Exception as e:
        print(f"Error detecting current server: {e}")
        return "unknown"

def is_dreampi_active():
    """Check if dreampi service is running"""
    try:
        proc = subprocess.Popen(['systemctl', 'is-active', 'dreampi'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        return stdout.decode('utf-8').strip() == 'active'
    except Exception as e:
        print(f"Error checking dreampi service status: {e}")
        return False

def create_backup():
    """Create backup of original dreampi.py if it doesn't exist"""
    if not os.path.exists(DREAMPI_BACKUP):
        try:
            shutil.copy2(DREAMPI_SCRIPT, DREAMPI_BACKUP)
            print("Created backup: {}".format(DREAMPI_BACKUP))
        except Exception as e:
            print(f"Error creating backup: {e}")

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
        print("Stopping dreampi service...")
        subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
        time.sleep(2)
        print("Dreampi service stopped.")

        if server == 'dclive':
            # Switch to DCLive (original)
            print("Attempting to switch to DCLive server...")
            if os.path.exists(DREAMPI_BACKUP):
                # Use our backup
                shutil.copy2(DREAMPI_BACKUP, DREAMPI_SCRIPT)
                print(f"Copied {DREAMPI_BACKUP} to {DREAMPI_SCRIPT}")
            elif os.path.exists(DREAMPI_ORIGINAL):
                # Use the one from the repository
                shutil.copy2(DREAMPI_ORIGINAL, DREAMPI_SCRIPT)
                print(f"Copied {DREAMPI_ORIGINAL} to {DREAMPI_SCRIPT}")
            else:
                return jsonify({'success': False, 'error': 'No original dreampi.py found for DCLive'})

        elif server == 'dcnet':
            # Check if we have a DCNet version
            print("Attempting to switch to DCNET server...")
            dcnet_v2_dreampi_script = None

            # Look for dreampi.py or *_dreampi.py in DCNET_V2 directory
            if os.path.exists(DCNET_V2_DIR):
                for file in os.listdir(DCNET_V2_DIR):
                    if file == 'dreampi.py' or file.endswith('_dreampi.py'):
                        dcnet_v2_dreampi_script = os.path.join(DCNET_V2_DIR, file)
                        break

            if dcnet_v2_dreampi_script and os.path.exists(dcnet_v2_dreampi_script):
                # If a specific dreampi.py for DCNET_V2 exists, use it
                shutil.copy2(dcnet_v2_dreampi_script, DREAMPI_SCRIPT)
                print(f"Copied {dcnet_v2_dreampi_script} to {DREAMPI_SCRIPT}")
            elif os.path.exists(DCNET_SCRIPT):
                # Otherwise, try running the dcnet_on_off.sh script
                print(f"Running {DCNET_SCRIPT}...")
                subprocess.call(['sudo', 'bash', DCNET_SCRIPT])
                print(f"{DCNET_SCRIPT} executed.")
            else:
                return jsonify({'success': False, 'error': 'No DCNet specific dreampi.py or dcnet_on_off.sh found'})
        else:
            return jsonify({'success': False, 'error': 'Invalid server specified'})

        # Ensure correct permissions
        print(f"Setting permissions for {DREAMPI_SCRIPT}...")
        os.chmod(DREAMPI_SCRIPT, 0o755)
        print("Permissions set.")

        # Start DreamPi service
        print("Starting dreampi service...")
        subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
        time.sleep(5) # Give it time to start
        print("Dreampi service started (or attempted).")

        # Check result
        new_server = get_current_server()
        dreampi_active = is_dreampi_active()

        print(f"Switch attempt complete. New server: {new_server}, DreamPi active: {dreampi_active}")

        return jsonify({
            'success': dreampi_active and new_server == server,
            'current_server': new_server,
            'dreampi_active': dreampi_active
        })

    except Exception as e:
        print(f"An error occurred during server switch: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def status():
    """Get current status and available scripts information."""
    scripts = {}
    if os.path.exists(SCRIPTS_DIR):
        scripts['dcnet_on_off.sh'] = os.path.exists(DCNET_SCRIPT)
        scripts['original_dreampi.py'] = os.path.exists(DREAMPI_ORIGINAL)
        scripts['backup_exists'] = os.path.exists(DREAMPI_BACKUP)
        scripts['dcnet_v2_dir'] = os.path.exists(DCNET_V2_DIR)

        # Check what's in DCNET_V2
        if os.path.exists(DCNET_V2_DIR):
            scripts['dcnet_v2_files'] = os.listdir(DCNET_V2_DIR)
        else:
            scripts['dcnet_v2_files'] = [] # Directory does not exist

    return jsonify({
        'current_server': get_current_server(),
        'dreampi_active': is_dreampi_active(),
        'scripts': scripts
    })

@app.route('/api/check-scripts')
def check_scripts():
    """Debug endpoint to see what scripts we have in SCRIPTS_DIR"""
    info = {
        'scripts_dir_exists': os.path.exists(SCRIPTS_DIR),
        'files': []
    }

    if os.path.exists(SCRIPTS_DIR):
        for item in os.listdir(SCRIPTS_DIR):
            item_path = os.path.join(SCRIPTS_DIR, item)
            info['files'].append({
                'name': item,
                'is_dir': os.path.isdir(item_path),
                'executable': os.access(item_path, os.X_OK),
                'full_path': item_path # Added for more detailed debugging
            })
    return jsonify(info)

if __name__ == '__main__':
    print("DreamPi Portal starting...")
    print(f"Scripts directory: {SCRIPTS_DIR}")
    print(f"DCNET_SCRIPT expected path: {DCNET_SCRIPT}")
    app.run(host='0.0.0.0', port=8080, debug=False)
