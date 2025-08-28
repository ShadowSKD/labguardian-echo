# [LabGuardian Echo](https://github.com/ShadowSKD/labguardian-echo)

LabGuardian Echo is a client API for LabGuardian VisageAI.  
**Important:** Never commit your API keys or sensitive configuration to version control.

Please first setup the Admin Server available in the repository: [LabGuardian Visage](https://github.com/ShadowSKD/labguardian-visage-ai)

## Setup

1. **Clone the repository.**

2. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Configure your settings:**

    - Copy `settings.ini.example` to `settings.ini` and fill in your Gemini API key and other configuration options:

      ```ini
      [gemini]
      GEMINI_API_KEY = YOUR_API_KEY_HERE

      [DEFAULT]
      ADMIN_SERVER = YOUR_ADMIN_SERVER_URL
      LOG_FILE = activity_log.json
      CLIENT_USERNAME = Client_Name
      LAB_CODE = Lab_Code
      ```

    - **Never commit your `settings.ini` file.**  
      The `.gitignore` file already includes `settings.ini` to help prevent accidental leaks.

4. **Run the client:**

    ```sh
    python run_client.py
    ```

    This script will securely load your Gemini API key from `settings.ini` and launch [`client.py`](client.py).

## Configuration

- Edit `settings.ini` to change:
  - `ADMIN_SERVER` (admin server URL)
  - `CLIENT_USERNAME` and `LAB_CODE`
  - `LOG_FILE`
  - `GEMINI_API_KEY` (in `[gemini]` section)

- Edit [`client.py`](client.py) to adjust:
  - `FORBIDDEN_APPS` and `ALLOWED_WEBSITES` as needed

## Security Notes

- **Never share or commit your `settings.ini` or API keys.**
- If you suspect your API key has been exposed, revoke and regenerate it immediately.
- Always use `.gitignore` to exclude sensitive files from version control.

## Updates

- Now features integration with Gemini API, allowing advanced AI-powered analysis and automation capabilities.
- Uses `settings.ini` for secure configuration management.
- Use `run_client.py` to launch the client with your API key securely loaded.

---
