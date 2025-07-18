from flask import Flask, send_file, abort
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import io
import time

app = Flask(__name__)
CORS(app)

GUI_URL = 'http://localhost:8000'
SCREENSHOT_WIDTH = 600
SCREENSHOT_HEIGHT = 600

@app.route('/screenshot')
def get_screenshot():
    options = Options()
    options.add_argument('--headless')
    options.add_argument(f'--window-size={SCREENSHOT_WIDTH},{SCREENSHOT_HEIGHT}')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(GUI_URL)
        time.sleep(2)  # Wait for the page to fully render
        png = driver.get_screenshot_as_png()
        img = Image.open(io.BytesIO(png)).convert('RGB')
        img = img.resize((SCREENSHOT_WIDTH, SCREENSHOT_HEIGHT))
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=80)
        buf.seek(0)
        return send_file(buf, mimetype='image/jpeg')
    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5051) 