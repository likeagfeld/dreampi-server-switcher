#!/usr/bin/env python3
"""
DreamPi Server Switcher Portal - Python 3.5 Compatible with Fixed Script Download
"""

from flask import Flask, render_template, jsonify
import subprocess
import os
import time

app = Flask(__name__)

# Scripts location
SCRIPTS_DIR = "/home/pi/dreampi_custom_scripts"
SCRIPTS_REPO = "https://github.com/scrivanidc/dreampi_custom_scripts.git"

def ensure_scripts():
    """Make sure scripts exist and are executable - Python 3.5 compatible"""
    try:
        if not os.path.exists(SCRIPTS_DIR):
            print("Scripts directory not found, cloning from GitHub...")
            # Use subprocess.call for Python 3.5
            subprocess.call(['git', 'clone', SCRIPTS_REPO, SCRIPTS_DIR])
            subprocess.call(['chown', '-R', 'pi:pi', SCRIPTS_DIR])
            print("Scripts cloned successfully")
        
        # Make all .sh files executable
        for file in os.listdir(SCRIPTS_DIR):
            if file.endswith('.sh'):
                filepath = os.path.join(SCRIPTS_DIR, file)
                os.chmod(filepath, 0o755)
                print("Made executable: {}".format(filepath))
        
        # List what we have
        scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')]
        print("Available scripts: {}".format(', '.join(scripts)))
        return True
    except Exception as e:
        print("Error ensuring scripts: {}".format(e))
        return False

def get_current_server():
    """Simple detection - just check if dreampi.py contains dcnet"""
    try:
        with open("/home/pi/dreampi/dreampi.py", 'r') as f:
            content = f.read().lower()
            if 'dcnet' in content or 'dc-net' in content or 'flycast' in content:
                return "dcnet"
        return "dclive"
    except Exception as e:
        print("Error detecting server: {}".format(e))
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

@app.route('/')
def index():
    # Ensure scripts on every page load
    ensure_scripts()
    return render_template('index.html', 
                         current_server=get_current_server(),
                         dreampi_active=is_dreampi_active())

@app.route('/api/switch/<server>')
def switch_server(server):
    """Switch server by running the appropriate script"""
    # Make sure scripts exist
    if not ensure_scripts():
        return jsonify({'success': False, 'error': 'Failed to download scripts'})
    
    if server == 'dclive':
        script_name = 'switch_to_dclive.sh'
    elif server == 'dcnet':
        script_name = 'switch_to_dcnet.sh'
    else:
        return jsonify({'success': False, 'error': 'Invalid server'})
    
    script = os.path.join(SCRIPTS_DIR, script_name)
    
    # Check if specific script exists
    if not os.path.exists(script):
        # Try to update scripts
        subprocess.call(['git', 'pull'], cwd=SCRIPTS_DIR)
        
        # Check again
        if not os.path.exists(script):
            # List what scripts we do have
            available = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')]
            return jsonify({
                'success': False, 
                'error': 'Script {} not found in {}'.format(script_name, SCRIPTS_DIR),
                'available_scripts': available
            })
    
    try:
        print("Running script: {}".format(script))
        
        # Run the script - Python 3.5 compatible
        proc = subprocess.Popen(['sudo', 'bash', script],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        
        print("Script output: {}".format(stdout.decode('utf-8')))
        if stderr:
            print("Script error: {}".format(stderr.decode('utf-8')))
        
        # Give it time to restart
        time.sleep(5)
        
        # Check result
        new_server = get_current_server()
        dreampi_active = is_dreampi_active()
        
        return jsonify({
            'success': dreampi_active and new_server == server,
            'current_server': new_server,
            'dreampi_active': dreampi_active,
            'output': stdout.decode('utf-8'),
            'error': stderr.decode('utf-8')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def status():
    # Check what scripts we have
    scripts = []
    if os.path.exists(SCRIPTS_DIR):
        scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')]
    
    return jsonify({
        'current_server': get_current_server(),
        'dreampi_active': is_dreampi_active(),
        'scripts_dir_exists': os.path.exists(SCRIPTS_DIR),
        'available_scripts': scripts
    })

@app.route('/api/update-scripts')
def update_scripts():
    """Manually update scripts"""
    try:
        if not os.path.exists(SCRIPTS_DIR):
            subprocess.call(['git', 'clone', SCRIPTS_REPO, SCRIPTS_DIR])
            subprocess.call(['chown', '-R', 'pi:pi', SCRIPTS_DIR])
        else:
            subprocess.call(['git', 'pull'], cwd=SCRIPTS_DIR)
        
        # Make executable
        for file in os.listdir(SCRIPTS_DIR):
            if file.endswith('.sh'):
                os.chmod(os.path.join(SCRIPTS_DIR, file), 0o755)
        
        scripts = [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.sh')]
        return jsonify({'success': True, 'scripts': scripts})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Starting DreamPi Portal...")
    ensure_scripts()
    app.run(host='0.0.0.0', port=8080, debug=False)
