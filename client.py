
import psutil
import requests
import time
import socket
import json

# Admin server URL
ADMIN_SERVER = "http://localhost:5000/alert"
LOG_FILE = "activity_log.json"

# List of forbidden applications
FORBIDDEN_APPS = ["chrome.exe", "firefox.exe", "edge.exe", "notepad.exe"]

# List of allowed websites (resource bank)
ALLOWED_WEBSITES = ["example.com", "labresources.edu"]

def send_alert(message):
    try:
        requests.post(ADMIN_SERVER, json={"alert": message})
    except requests.exceptions.RequestException as e:
        print("Failed to send alert:", e)

def log_activity(activity):
    try:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(json.dumps(activity) + "\n")
    except Exception as e:
        print("Failed to write log:", e)

def monitor_processes():
    while True:
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] in FORBIDDEN_APPS:
                alert_msg = f"Forbidden app detected: {process.info['name']}"
                send_alert(alert_msg)
                log_activity({"type": "process", "name": process.info['name'], "timestamp": time.time()})
                time.sleep(5)  # Avoid spamming alerts
        time.sleep(1)

def monitor_network():
    while True:
        connections = psutil.net_connections()
        for conn in connections:
            if conn.status == psutil.CONN_ESTABLISHED:
                try:
                    remote_host = socket.gethostbyaddr(conn.raddr.ip)[0]
                    if not any(allowed in remote_host for allowed in ALLOWED_WEBSITES):
                        alert_msg = f"Unauthorized network access: {remote_host}"
                        send_alert(alert_msg)
                        log_activity({"type": "network", "host": remote_host, "timestamp": time.time()})
                except (socket.herror, socket.gaierror, IndexError):
                    pass
        time.sleep(5)

def send_log_to_admin():
    while True:
        try:
            with open(LOG_FILE, "r") as log_file:
                logs = log_file.readlines()
            if logs:
                requests.post(ADMIN_SERVER, json={"logs": logs})
                open(LOG_FILE, "w").close()  # Clear log after sending
        except Exception as e:
            print("Failed to send logs:", e)
        time.sleep(10)

if __name__ == "__main__":
    from threading import Thread
    Thread(target=monitor_processes).start()
    Thread(target=monitor_network).start()
    Thread(target=send_log_to_admin).start()
