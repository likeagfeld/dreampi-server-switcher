#!/usr/bin/env python3
"""
DreamPi Server Switcher Portal - With Auto-Update
Uses existing DreamPi custom scripts and can update them from GitHub
"""

from flask import Flask, render_template, jsonify
import subprocess
import os
import time

app = Flask(__name__)

# Configuration
SCRIPTS_DIR = "/home/pi/dreampi_custom_scripts"
SCRIPTS_REPO = "https://github.com/scrivanidc/dreampi_custom_scripts.git"
SWITCH_DCLIVE_SCRIPT = os.path.join(SCRIPTS_DIR, "switch_to_dclive.sh")
SWITCH_DCNET_SCRIPT = os.path.join(SCRIPTS_DIR, "switch_to_dcnet.sh")

def update_scripts():
    """Update custom scripts from GitHub"""
    try:
        if os.path.exists(SCRIPTS_DIR):
            # Pull latest changes
            result = subprocess.run(
                ['git', 'pull'],
                cwd=SCRIPTS_DIR,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Make scripts executable
                subprocess.run(['chmod', '+x'] + [os.path.join(SCRIPTS_DIR, '*.sh')], shell=True)
                return True, "Scripts updated successfully"
            else:
                return False, "Git pull failed: " + result.stderr
        else:
            # Clone repository
            result = subprocess.run(
                ['git', 'clone', SCRIPTS_REPO, SCRIPTS_DIR],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                subprocess.run(['chown', '-R', 'pi:pi', SCRIPTS_DIR])
                subprocess.run(['chmod', '+x'] + [os.path.join(SCRIPTS_DIR, '*.sh')], shell=True)
                return True, "Scripts downloaded successfully"
            else:
                return False, "Git clone failed: " + result.stderr
    except Exception as e:
        return False, str(e)

def get_current_server():
    """Detect current server by checking dreampi.py content"""
    try:
        with open("/home/pi/dreampi/dreampi.py", 'r') as f:
            content = f.read()
            if 'dcnet' in content.lower() or 'flycast' in content.lower():
                return "dcnet"
        return "dclive"
    except:
        return "unknown"

def get_service_status():
    """Get dreampi service status"""
    try:
        result = subprocess.run(['systemctl', 'is-active', 'dreampi'], 
                              capture_output=True, text=True)
        status = result.stdout.strip()
        return {'active': status == 'active', 'status': status}
    except:
        return {'active': False, 'status': 'error'}

def run_script(script_path):
    """Run a shell script with sudo"""
    try:
        # Update scripts before running
        update_scripts()
        
        # Make sure script is executable
        subprocess.run(['sudo', 'chmod', '+x', script_path])
        
        # Run the script
        result = subprocess.run(['sudo', 'bash', script_path], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            return True, "Success"
        else:
            return False, result.stderr or "Script failed"
    except Exception as e:
        return False, str(e)

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         current_server=get_current_server(),
                         service_status=get_service_status())

@app.route('/api/status')
def api_status():
    """Get current status"""
    return jsonify({
        'current_server': get_current_server(),
        'service_status': get_service_status(),
        'scripts_exist': {
            'dclive': os.path.exists(SWITCH_DCLIVE_SCRIPT),
            'dcnet': os.path.exists(SWITCH_DCNET_SCRIPT)
        }
    })

@app.route('/api/switch/<server>')
def api_switch(server):
    """Switch to specified server using existing scripts"""
    if server == 'dclive':
        script_path = SWITCH_DCLIVE_SCRIPT
    elif server == 'dcnet':
        script_path = SWITCH_DCNET_SCRIPT
    else:
        return jsonify({'success': False, 'error': 'Invalid server'}), 400
    
    # Check if scripts exist, if not try to update
    if not os.path.exists(script_path):
        update_success, update_msg = update_scripts()
        if not update_success:
            return jsonify({
                'success': False,
                'error': 'Scripts not found and update failed: ' + update_msg
            }), 500
    
    # Run the switch script
    success, message = run_script(script_path)
    
    # Wait a moment for service to restart
    time.sleep(3)
    
    return jsonify({
        'success': success,
        'message': message,
        'current_server': get_current_server(),
        'service_status': get_service_status()
    })

@app.route('/api/restart')
def api_restart():
    """Restart DreamPi service"""
    try:
        subprocess.run(['sudo', 'systemctl', 'restart', 'dreampi'])
        time.sleep(3)
        return jsonify({
            'success': True,
            'service_status': get_service_status()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update-scripts')
def api_update_scripts():
    """Manually update scripts from GitHub"""
    success, message = update_scripts()
    return jsonify({
        'success': success,
        'message': message,
        'scripts_exist': {
            'dclive': os.path.exists(SWITCH_DCLIVE_SCRIPT),
            'dcnet': os.path.exists(SWITCH_DCNET_SCRIPT)
        }
    })

@app.route('/api/check-scripts')
def api_check_scripts():
    """Check if required scripts exist"""
    return jsonify({
        'scripts_dir_exists': os.path.exists(SCRIPTS_DIR),
        'dclive_script_exists': os.path.exists(SWITCH_DCLIVE_SCRIPT),
        'dcnet_script_exists': os.path.exists(SWITCH_DCNET_SCRIPT),
        'paths': {
            'scripts_dir': SCRIPTS_DIR,
            'dclive_script': SWITCH_DCLIVE_SCRIPT,
            'dcnet_script': SWITCH_DCNET_SCRIPT
        }
    })

# Initialize by updating scripts on startup
print("DreamPi Portal starting...")
print("Checking for custom scripts updates...")
update_success, update_msg = update_scripts()
if update_success:
    print("✅ " + update_msg)
else:
    print("⚠️  " + update_msg)

if __name__ == '__main__':
    print("Portal ready on port 8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
