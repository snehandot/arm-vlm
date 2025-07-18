import requests
from PIL import Image
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoTokenizer, AutoProcessor
from qwen_vl_utils import process_vision_info
import io
import re
import time
import os

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
    "Qwen/Qwen2.5-VL-3B-Instruct", torch_dtype="auto", device_map="auto"
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-3B-Instruct")

# --- Feedback Loop ---
conversation = []
prev_value = None
image_history = []  # Store last 2 images

os.environ["TOKENIZERS_PARALLELISM"] = "false"
while True:
    local_image = get_image()
    # local_image.show()
    # Maintain a rolling history of the last 2 images
    image_history.append(local_image)
    if len(image_history) > 2:
        image_history.pop(0)
    # Build the prompt with only LLM outputs as history
    messages = []
    for turn in conversation:
        messages.append(turn)
    # Add the latest user message (last 2 images + instruction)
    user_content = []
    for img in image_history:
        user_content.append({"type": "image", "image": img})
    if prev_value is not None:
        user_content.append({"type": "text", "text": f"Do not repeat the previous value: {prev_value}"})
    user_content.append({"type": "text", "text": "You have tools in which you can change the arm degree. Output your thought followed by a single list [joint_number, degree_change], for example [0, 20] or [1, -10] or [2, 15], with the single list at the end. The first element is the joint number: 0 for base axis (rotation), 1 for blue line y axis (base joint), 2 for mid joint (end effector). The degree change (positive or negative between -50 and 50) change direction with reverse. You can output only one list and one direction change per try. Your task is to align the arm end grip straight line along the blue line towards top and base rotor opposite to red line , change only appropriate joints, use negative to reverse."})
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

    # Parse list output and send to backend as delta
    import ast
    try:
        # Look for a list in the output, e.g., [0, 20] or [1, -20] or [2, 15]
        list_match = re.search(r'\[\s*(-?\d+)\s*,\s*(-?\d+)\s*\]', output_text)
        if list_match:
            joint_idx = int(list_match.group(1))
            degree_delta = int(list_match.group(2))
            print(f"Parsed joint: {joint_idx}, degree change: {degree_delta}")
            # Always send as delta
            resp = requests.post(f'{ROBOT_API_URL}/joint/{joint_idx}', json={'delta': degree_delta})
            resp.raise_for_status()
            print("API response:", resp.json())
            prev_value = [joint_idx, degree_delta]
        else:
            print("No valid [joint, degree] list found in LLM output.")
            break
    except Exception as e:
        print(f"Error parsing LLM output: {e}")
        break

    # Wait a bit for the system to update (e.g., for the GUI to reflect the change)
    # time.sleep(2)
