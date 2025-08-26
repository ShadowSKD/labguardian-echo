import configparser
import os
import subprocess
import sys

def main():
    config = configparser.ConfigParser()
    config.read('settings.ini')
    try:
        api_key = config['gemini']['api_key']
    except KeyError:
        print("Gemini API key not found in settings.ini.")
        sys.exit(1)

    # Set the environment variable for the subprocess
    env = os.environ.copy()
    env['GEMINI_API_KEY'] = api_key

    # Run client.py with the environment variable set
    subprocess.run([sys.executable, 'client.py'], env=env)

if __name__ == "__main__":
    main()