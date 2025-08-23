# [LabGuardian Echo](https://github.com/ShadowSKD/labguardian-echo)
 LabGuardian Echo is client API for LabGuardian VisageAI.
 Please first setup Admin Server available in repository: [LabGuardian Visage](https://github.com/ShadowSKD/labguardian-visage-ai)

## Setup

1. Clone the repository.
2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
3. Set your Gemini API key:
    ```sh
    set GEMINI_API_KEY=your-gemini-api-key
    ```
4. Edit `client.py` to configure:
    - `ADMIN_SERVER` (admin server URL)
    - `CLIENT_USERNAME` and `LAB_CODE`
    - `FORBIDDEN_APPS` and `ALLOWED_WEBSITES` as needed
