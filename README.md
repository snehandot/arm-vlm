# 3D Robot Arm LLM Control

This project allows you to control a 3D robot arm via a web GUI and LLM feedback loop, with real-time visual feedback.

## Requirements

- Python 3.8+
- Node.js (for frontend)
- Chrome browser
- ChromeDriver (for Selenium screenshot server)

## Python dependencies
Install all Python dependencies:
```sh
pip install -r requirements.txt
```

Download [ChromeDriver](https://sites.google.com/chromium.org/driver/) and ensure it is in your PATH.

## 1. Start the Python Backend (Robot Control API)
This serves the robot joint state and accepts control commands.
```sh
python3 robot_control_api.py
```

## 2. Start the Screenshot Server (Selenium-based)
This captures real-time screenshots of the robot GUI for the LLM.
```sh
python3 screenshot_server.py
```

## 3. Start the Frontend (Web GUI)
```sh
cd robot-gui
npm install
npm start
```
This will serve the GUI at [http://localhost:8000](http://localhost:8000).

## 4. Run the LLM Feedback Loop
- For Qwen-based LLM:
  ```sh
  python3 llm.py
  ```
- For Gemma-based LLM (if available):
  ```sh
  python3 llm-gemma.py
  ```

## Usage
- Open the GUI in your browser at [http://localhost:8000](http://localhost:8000).
- The LLM script will iteratively update the robot joints based on visual feedback.
- The screenshot server provides up-to-date images for the LLM.

## Notes
- Make sure all servers are running before starting the LLM script.
- If you encounter issues with ChromeDriver, ensure it matches your Chrome version and is in your PATH.
- You can adjust the camera zoom in `robot-gui/js/THREEScene.js` for a wider or closer view.

--- 