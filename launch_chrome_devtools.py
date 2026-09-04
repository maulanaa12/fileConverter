import os
import sys
import time
import json
import socket
import urllib.request
import subprocess

CHROME_PATH = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
PROFILE_DIR = r'C:\ChromeDevProfile'
PORT = 9222
USER_DATA_ACTIVE_PORT = os.path.expandvars(
    r'%LOCALAPPDATA%\Google\Chrome\User Data\DevToolsActivePort'
)

def is_port_listening(port=PORT):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_websocket_path():
    url = f'http://127.0.0.1:{PORT}/json/version'
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            ws_url = data.get('webSocketDebuggerUrl', '')
            if ws_url:
                return '/' + ws_url.split('/', 3)[3]
    except Exception as e:
        return None
    return None

def start_chrome():
    os.makedirs(PROFILE_DIR, exist_ok=True)
    if not is_port_listening():
        print(f'Starting Chrome with remote debugging port {PORT}...')
        cmd = [
            CHROME_PATH,
            f'--remote-debugging-port={PORT}',
            '--remote-allow-origins=*',
            f'--user-data-dir={PROFILE_DIR}',
            '--no-first-run',
            '--no-default-browser-check'
        ]
        flags = 0x00000008 | 0x00000200
        subprocess.Popen(
            cmd,
            creationflags=flags,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        for _ in range(15):
            time.sleep(1)
            if is_port_listening():
                break
        else:
            print('Error: Chrome started but port 9222 did not become active.')
            return False

    ws_path = None
    for _ in range(10):
        ws_path = get_websocket_path()
        if ws_path:
            break
        time.sleep(0.5)

    if not ws_path:
        print('Error: Could not retrieve WebSocket debugger URL from Chrome.')
        return False

    os.makedirs(os.path.dirname(USER_DATA_ACTIVE_PORT), exist_ok=True)
    with open(USER_DATA_ACTIVE_PORT, 'w', encoding='utf-8') as f:
        f.write(f'{PORT}\n{ws_path}\n')

    print('Success: Chrome DevTools is ready!')
    print(f'  Port: {PORT}')
    print(f'  WS Path: {ws_path}')
    print(f'  DevToolsActivePort updated at: {USER_DATA_ACTIVE_PORT}')
    return ws_path

if __name__ == '__main__':
    ws_path = start_chrome()
    if not ws_path:
        sys.exit(1)
    if '--daemon' in sys.argv:
        print('Running in daemon mode. Press Ctrl+C to stop.')
        sys.stdout.flush()
        try:
            while True:
                time.sleep(5)
                if not is_port_listening():
                    print('Chrome disconnected. Re-launching...')
                    ws_path = start_chrome()
                else:
                    # Keep DevToolsActivePort up-to-date
                    with open(USER_DATA_ACTIVE_PORT, 'w', encoding='utf-8') as f:
                        f.write(f'{PORT}\n{ws_path}\n')
        except KeyboardInterrupt:
            print('Daemon stopped.')
    sys.exit(0)

