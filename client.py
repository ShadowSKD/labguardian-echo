import psutil
import requests
import time
import socket
import json
import threading
import os
import msvcrt
import google.generativeai as genai

def get_wifi_ip():
    """Retrieve the IP address of the WiFi connection."""
    try:
        hostname = socket.gethostname()
        wifi_ip = socket.gethostbyname(hostname)
        print(f"WiFi IP Address: {wifi_ip}")
        return wifi_ip
    except socket.error as e:
        print(f"Failed to retrieve WiFi IP address: {e}")
        return None

# Retrieve and print the WiFi IP address at startup
wifi_ip = get_wifi_ip()

# Admin server URL
ADMIN_SERVER = "http://localhost:5000"
LOG_FILE = "activity_log.json"
CLIENT_USERNAME = "Client-1"
LAB_CODE = "lab1"

# List of forbidden applications
FORBIDDEN_APPS = {"chrome.exe", "firefox.exe", "Notepad.exe"}

# List of allowed websites (resource bank)
ALLOWED_WEBSITES = {"example.com", "labresources.edu"}

def check_server_status(max_retries=5):
    """Check if the admin server is reachable before starting monitoring."""
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(f"{ADMIN_SERVER}/", timeout=3)
            print("Server Status:", response.status_code)
            if response.status_code == 200:
                print("Server is active and monitoring started.")
                return
        except requests.exceptions.RequestException:
            print("Server is not reachable. Retrying in 5 seconds...")
        time.sleep(5)
        retries += 1
    
    print("Server is not reachable. Switching to manual mode. \nMonitoring started in manual mode.")
    print("Please ensure the server is running to receive alerts and logs.")

    while True:
        choice = input("Server is not reachable. Retry connecting? (y/n): ").strip().lower()
        if choice == 'y':
            check_server_status()
            break
        elif choice == 'n':
            print("Exiting as per user request.")
            exit(1)
        else:
            print("Please enter 'y' or 'n'.")

def get_client_id():
    """Get a unique client ID from the admin server."""
    check_server_status()
    try:
        response = requests.post(f"{ADMIN_SERVER}/api/clients/register", json={"labCode": LAB_CODE, "clientName": CLIENT_USERNAME}, timeout=3)
        if response.status_code == 201:
            client_id = response.json().get("clientId")
            lab_prompt = response.json().get("labPrompt")
            if client_id and lab_prompt:
                print(f"Received client ID: {client_id}")
                return client_id, lab_prompt
            else:
                print("Failed to retrieve client ID and Lab activity prompt from response.")
            
        else:
            print(f"Failed to register client. Status code: {response.status_code}")
            while True:
                choice = input("Retry registering client? (y/n): ").strip().lower()
                if choice == 'y':
                    return get_client_id()
                elif choice == 'n':
                    print("Exiting as per user request.")
                    exit(1)
                else:
                    print("Please enter 'y' or 'n'.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to communicate with server: {e}")
    return None

# Get client ID at the start
client_data = get_client_id()
client_id, lab_prompt = client_data if client_data else (None, None)
if not client_id:
    print("Exiting due to failure in obtaining client ID.")
    exit(1)

def send_heartbeat():
    """Send a heartbeat to the admin server periodically."""
    while True:
        try:
            response = requests.post(f"{ADMIN_SERVER}/api/clients/heartbeat", json={"clientId": client_id}, timeout=3)
            if response.status_code != 200:
                print(f"Failed to send heartbeat. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Failed to send heartbeat: {e}")
        time.sleep(10)

def send_alert(message):
    """Send an alert to the admin server."""
    try:
        requests.post(f"{ADMIN_SERVER}/api/alerts/{LAB_CODE}/{client_id}", json={"message": message, "timestamp": time.time()}, timeout=3)
    except requests.exceptions.RequestException:
        print("Failed to send alert. Server may be down.")

def log_activity(activity):
    """Log activity to a file with proper flushing."""
    try:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(json.dumps(activity) + "\n")
            log_file.flush()  # Ensure immediate write
            os.fsync(log_file.fileno())  # Force disk write
    except Exception as e:
        print("Failed to write log. Server may be down.")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # Ensure the API key is set
if not GEMINI_API_KEY:
    print("GEMINI_API_KEY environment variable not set. Exiting.")
    exit(1)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Load whitelist of safe processes from safe_processes.json
try:
    with open("safe_processes.json", "r") as f:
        white_list = set(json.load(f))
except Exception as e:
    print(f"Failed to load safe_processes.json: {e}")
    white_list = set()

def is_app_forbidden(app_name, retries=3):
    """Check with Gemini API if an application is forbidden."""
    if app_name in white_list:
        return False
    prompt = ("(excluding apps that run in background for basic functionality of OS / Not used for malpractice) Is the following application a web browser, communication tool, or any app unsuitable for a restricted lab exam environment? Answer only with 'Yes' or 'No'." if not lab_prompt else "(excluding apps that run in background for basic functionality of OS / Not used for malpractice)"+lab_prompt)  + f"App name: {app_name}"
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            # Simple check for "Yes" in the response text, case-insensitive
            if 'yes' in response.text.lower():
                return True
            return False
        except Exception as e:
            print(f"Gemini API call failed for {app_name}: {e}. Retrying... ({attempt + 1}/{retries})")
            time.sleep(2)
    print(f"Could not verify {app_name} with Gemini API after {retries} retries.")
    return False

def monitor_processes_AI():
    """Monitor running processes using Gemini API to identify forbidden applications."""
    checked_apps = set()
    while True:
        current_processes = {p.info['name'] for p in psutil.process_iter(['name']) if p.info['name']}
        
        new_processes = current_processes - checked_apps
        
        for app_name in new_processes:
            print(f"Checking new process: {app_name}")
            if is_app_forbidden(app_name):
                alert_msg = f"Forbidden app detected by AI: {app_name}"
                print(alert_msg)
                send_alert(alert_msg)
                log_activity({"type": "process", "name": app_name, "timestamp": time.time()})
            
            checked_apps.add(app_name)
            
        time.sleep(5)

def monitor_processes_old_no_AI():
    """Monitor running processes for forbidden applications."""
    foundApps = set()
    while True:
        for process in psutil.process_iter(['name']):
            if process.info['name'] in FORBIDDEN_APPS:
                if process.info['name'] not in foundApps:
                    alert_msg = f"Forbidden app detected: {process.info['name']}"
                    send_alert(alert_msg)
                    log_activity({"type": "process", "name": process.info['name'], "timestamp": time.time()})
                    foundApps.add(process.info['name'])
                    time.sleep(5)
        time.sleep(1)

def monitor_network():
    """Monitor active network connections for unauthorized websites."""
    while True:
        try:
            for conn in psutil.net_connections(kind='inet'):
                if conn.status == psutil.CONN_ESTABLISHED and conn.raddr:
                    try:
                        remote_host = socket.gethostbyaddr(conn.raddr.ip)[0]
                        if not any(allowed in remote_host for allowed in ALLOWED_WEBSITES):
                            alert_msg = f"Unauthorized network access: {remote_host}"
                            send_alert(alert_msg)
                            log_activity({"type": "network", "host": remote_host, "timestamp": time.time()})
                    except (socket.herror, socket.gaierror, IndexError):
                        pass
        except psutil.AccessDenied:
            print("Access denied while retrieving network connections.")
        time.sleep(5)

def send_log_to_admin():
    """Send logs to the admin server periodically."""
    while True:
        try:
            with open(LOG_FILE, "r") as log_file:
                logs = log_file.readlines()
            if logs:
                requests.post(f"{ADMIN_SERVER}/api/alerts/{client_id}", json={"logs": logs}, timeout=3)
                open(LOG_FILE, "w").close()  # Clear log after sending
        except Exception as e:
            print("Failed to send logs. Server may be down.")
        time.sleep(10)

if __name__ == "__main__":

    # Start monitoring threads
    threads = [
        threading.Thread(target=monitor_processes_AI, daemon=True),
        # threading.Thread(target=monitor_network, daemon=True),
        threading.Thread(target=send_log_to_admin, daemon=True),
        threading.Thread(target=send_heartbeat, daemon=True)
    ]
    
    for thread in threads:
        thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        exit(0)