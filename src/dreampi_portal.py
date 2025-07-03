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
        if os.path.exists(DREAMPI_SCRIPT):
            shutil.copy2(DREAMPI_SCRIPT, DREAMPI_BACKUP)
            print("Created backup: {}".format(DREAMPI_BACKUP))

def run_interactive_script(script_path, script_input):
    """
    Runs an interactive shell script and provides input to it.
    This version uses byte streams and is compatible with older Python 3.
    script_path: The full path to the shell script.
    script_input: The string to be sent to the script's standard input.
    """
    try:
        print("Attempting to run interactive script: {}".format(script_path))
        # Ensure the script is executable
        subprocess.run(['sudo', 'chmod', '+x', script_path], check=True)
        
        # Command to be executed
        command = ['sudo', 'bash', script_path]
        print("Executing command: {}".format(' '.join(command)))

        # Run the script and pipe the input as bytes
        proc = subprocess.Popen(
            command, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        # Encode input to bytes and send it. Add a timeout to prevent hangs.
        input_bytes = "{}\n".format(script_input).encode('utf-8')
        print("Sending input to script: {!r}".format(input_bytes))
        stdout_bytes, stderr_bytes = proc.communicate(input=input_bytes, timeout=15)
        
        # Decode output for logging
        stdout = stdout_bytes.decode('utf-8', errors='ignore')
        stderr = stderr_bytes.decode('utf-8', errors='ignore')

        print("Script {} return code: {}".format(os.path.basename(script_path), proc.returncode))
        print("Script {} STDOUT:\n---\n{}\n---".format(os.path.basename(script_path), stdout))
        if stderr:
            print("Script {} STDERR:\n---\n{}\n---".format(os.path.basename(script_path), stderr))
        
        return True # Assume success if it doesn't crash
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout_bytes, stderr_bytes = proc.communicate()
        print("Error: Script timed out! It may be stuck waiting for input.")
        print("STDOUT so far: {}".format(stdout_bytes.decode('utf-8', errors='ignore')))
        print("STDERR so far: {}".format(stderr_bytes.decode('utf-8', errors='ignore')))
        return False
    except Exception as e:
        print("Failed to run interactive script {}: {}".format(script_path, e))
        return False

@app.route('/')
def index():
    return render_template('index.html',
                         current_server=get_current_server(),
                         dreampi_active=is_dreampi_active())

@app.route('/api/switch/<server>')
def switch_server(server):
    """Switch server"""
    try:
        create_backup()

        subprocess.call(['sudo', 'systemctl', 'stop', 'dreampi'])
        time.sleep(2)

        if server == 'dclive':
            if get_current_server() == 'dcnet' and os.path.exists(DCNET_SCRIPT):
                print("Using dcnet_on_off.sh to switch to DCLive (Standard)...")
                run_interactive_script(DCNET_SCRIPT, "2")
            elif os.path.exists(DREAMPI_BACKUP):
                shutil.copy2(DREAMPI_BACKUP, DREAMPI_SCRIPT)
            elif os.path.exists(DREAMPI_ORIGINAL):
                shutil.copy2(DREAMPI_ORIGINAL, DREAMPI_SCRIPT)
            else:
                return jsonify({'success': False, 'error': 'No original dreampi.py found to restore'})

        elif server == 'dcnet':
            dcnet_v2_script_py = None
            if os.path.exists(DCNET_V2_DIR):
                for file in os.listdir(DCNET_V2_DIR):
                    if file == 'dreampi.py' or file.endswith('_dreampi.py'):
                        dcnet_v2_script_py = os.path.join(DCNET_V2_DIR, file)
                        break
            
            if dcnet_v2_script_py and os.path.exists(dcnet_v2_script_py):
                shutil.copy2(dcnet_v2_script_py, DREAMPI_SCRIPT)
            elif os.path.exists(DCNET_SCRIPT):
                print("Using dcnet_on_off.sh to switch to DCNET...")
                run_interactive_script(DCNET_SCRIPT, "1")
            else:
                return jsonify({'success': False, 'error': 'No DCNet script (python or shell) found'})
        else:
            return jsonify({'success': False, 'error': 'Invalid server'})

        if os.path.exists(DREAMPI_SCRIPT):
            os.chmod(DREAMPI_SCRIPT, 0o755)

        subprocess.call(['sudo', 'systemctl', 'start', 'dreampi'])
        time.sleep(5)

        new_server = get_current_server()
        dreampi_active = is_dreampi_active()

        return jsonify({
            'success': dreampi_active and new_server == server,
            'current_server': new_server,
            'dreampi_active': dreampi_active
        })

    except Exception as e:
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
