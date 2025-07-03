#!/usr/bin/env python3
"""
DreamPi Server Switcher Portal - Python 3.5 Compatible
Works with old Python version on Raspbian Stretch
"""

from flask import Flask, render_template, jsonify
import subprocess
import os
import time

app = Flask(__name__)

# Scripts location
SCRIPTS_DIR = "/home/pi/dreampi_custom_scripts"

def ensure_scripts():
    """Make sure scripts exist and are executable"""
    if not os.path.exists(SCRIPTS_DIR):
        subprocess.run(['git', 'clone', 'https://github.com/scrivanidc/dreampi_custom_scripts.git', SCRIPTS_DIR])
        subprocess.run(['chown', '-R', 'pi:pi', SCRIPTS_DIR])
    
    # Make all .sh files executable
    try:
        for file in os.listdir(SCRIPTS_DIR):
            if file.endswith('.sh'):
                os.chmod(os.path.join(SCRIPTS_DIR, file), 0o755)
    except:
        pass

def get_current_server():
    """Simple detection - just check if dreampi.py contains dcnet"""
    try:
        with open("/home/pi/dreampi/dreampi.py", 'r') as f:
            content = f.read().lower()
            if 'dcnet' in content or 'dc-net' in content:
                return "dcnet"
        return "dclive"
    except:
        return "unknown"

def is_dreampi_active():
    """Check if dreampi service is running"""
    try:
        # Python 3.5 compatible way
        proc = subprocess.Popen(['systemctl', 'is-active', 'dreampi'], 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        return stdout.decode('utf-8').strip() == 'active'
    except:
        return False

@app.route('/')
def index():
    return render_template('index.html', 
                         current_server=get_current_server(),
                         dreampi_active=is_dreampi_active())

@app.route('/api/switch/<server>')
def switch_server(server):
    """Switch server by running the appropriate script"""
    ensure_scripts()
    
    if server == 'dclive':
        script = os.path.join(SCRIPTS_DIR, 'switch_to_dclive.sh')
    elif server == 'dcnet':
        script = os.path.join(SCRIPTS_DIR, 'switch_to_dcnet.sh')
    else:
        return jsonify({'success': False, 'error': 'Invalid server'})
    
    if not os.path.exists(script):
        return jsonify({'success': False, 'error': 'Script not found'})
    
    try:
        # Run the script - Python 3.5 compatible
        proc = subprocess.Popen(['sudo', 'bash', script],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        
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
    return jsonify({
        'current_server': get_current_server(),
        'dreampi_active': is_dreampi_active()
    })

if __name__ == '__main__':
    ensure_scripts()
    app.run(host='0.0.0.0', port=8080, debug=False)
