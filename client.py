import psutil
import requests
import time
import json
import threading
import os

# Admin server URL
ADMIN_SERVER = "http://localhost:5000/alert"
LOG_FILE = "activity_log.json"
CLIENT_USERNAME = "admin"

# List of forbidden applications
FORBIDDEN_APPS = {"chrome.exe", "firefox.exe", "edge.exe", "notepad.exe"}

last_alerted_processes = set()

def send_alert(message):
    try:
        requests.post(ADMIN_SERVER, json={"alert": message, "client_username": CLIENT_USERNAME}, timeout=3)
    except requests.exceptions.RequestException:
        print("Failed to send alert. Server may be down.")

def log_activity(activity):
    try:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(json.dumps(activity) + "\n")
            log_file.flush()
            os.fsync(log_file.fileno())
    except Exception:
        print("Failed to write log.")

def monitor_processes():
    global last_alerted_processes
    while True:
        current_processes = {p.info['name'] for p in psutil.process_iter(['name']) if p.info['name'] in FORBIDDEN_APPS}
        new_alerts = current_processes - last_alerted_processes
        for process in new_alerts:
            send_alert(f"Forbidden app detected: {process}")
            log_activity({"type": "process", "name": process, "timestamp": time.time()})
        last_alerted_processes = current_processes
        time.sleep(5)

if __name__ == "__main__":
    monitor_thread = threading.Thread(target=monitor_processes, daemon=True)
    monitor_thread.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping monitoring...")
        exit(0)
