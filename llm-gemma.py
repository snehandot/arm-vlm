# 

import requests
from PIL import Image
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info
import io
import re
import time

# --- Robot Arm API Function ---
ROBOT_API_URL = 'http://localhost:5050'
SCREENSHOT_SERVER_URL = 'http://localhost:5051/screenshot'

def set_joint_1(value):
    """Set joint 1 to the given value (degrees) via the robot API."""
    resp = requests.post(f'{ROBOT_API_URL}/joint/1', json={'value': value})
    resp.raise_for_status()
    return resp.json()

def get_image():
    """Fetch the latest screenshot from the screenshot server and return as PIL Image."""
    resp = requests.get(SCREENSHOT_SERVER_URL)
    resp.raise_for_status()
    img = Image.open(io.BytesIO(resp.content)).convert('RGB')
    return img

# --- LLM Setup ---
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct", torch_dtype="auto", device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")

# --- Feedback Loop ---
conversation = []
prev_value = None

while True:
    local_image = get_image()
    local_image.show()
    # Build the prompt with only LLM outputs as history
    messages = []
    for turn in conversation:
        messages.append(turn)
    # Add the latest user message (image + instruction)
    user_content = [
        {"type": "image", "image": local_image},
    ]
    if prev_value is not None:
        user_content.append({"type": "text", "text": f"Do not repeat the previous value: {prev_value}"})
    user_content.append({"type": "text", "text": "The white structure is the arm. Experiment with different values, Output a single number answer betwen 0 and 180, look at the image and give me a degree to change the arm tip to look up.You are not allowed to repeat the previous values, If the task is done, type 'done'."})
    messages.append({"role": "user", "content": user_content})

    # Prepare for inference
    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )
    inputs = inputs.to("mps")

    # Inference
    generated_ids = model.generate(**inputs, max_new_tokens=128)
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]
    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    print("LLM output:", output_text)

    # Add LLM output to conversation history
    conversation.append({"role": "assistant", "content": [{"type": "text", "text": output_text}]})

    # Check for 'done'
    if 'done' in output_text.lower():
        print("LLM indicated the task is done.")
        break

    # Parse number and send to backend
    match = re.search(r'(\d+)', output_text)
    if match:
        value = int(match.group(1))
        # if prev_value is not None and value == prev_value:
        #     print(f"LLM repeated the previous value {value}, skipping action.")
        #     break
        print(f"Setting joint 1 to {value} via API...")
        result = set_joint_1(value)
        print("API response:", result)
        prev_value = value
    else:
        print("No number found in LLM output.")
        break

    # Wait a bit for the system to update (e.g., for the GUI to reflect the change)
    time.sleep(2)
