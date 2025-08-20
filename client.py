import psutil
import requests
import time
import socket
import json
import threading
import os

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
ADMIN_SERVER = "http://192.168.72.14:5000"
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

def get_client_id():
    """Get a unique client ID from the admin server."""
    check_server_status()
    try:
        response = requests.post(f"{ADMIN_SERVER}/api/clients/register", json={"labCode": LAB_CODE, "clientName": CLIENT_USERNAME}, timeout=3)
        if response.status_code == 201:
            client_id = response.json().get("clientId")
            if client_id:
                print(f"Received client ID: {client_id}")
                return client_id
            else:
                print("Failed to retrieve client ID from response.")
        else:
            print(f"Failed to register client. Status code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to communicate with server: {e}")
    return None

# Get client ID at the start
client_id = get_client_id()
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

def monitor_processes():
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
        threading.Thread(target=monitor_processes, daemon=True),
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