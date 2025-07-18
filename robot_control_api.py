from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# 6-joint robot arm, initial values all zero
joint_values = [0, 0, 0, 0, 0, 0]

@app.route('/joints', methods=['GET'])
def get_joints():
    return jsonify(joint_values)

@app.route('/joints', methods=['POST'])
def set_joints():
    data = request.get_json()
    if not data or 'values' not in data or len(data['values']) != len(joint_values):
        return jsonify({'error': 'Invalid input'}), 400
    for i, v in enumerate(data['values']):
        joint_values[i] = v
    return jsonify({'status': 'ok', 'values': joint_values})

@app.route('/joint/<int:idx>', methods=['POST'])
def set_joint(idx):
    if idx < 0 or idx >= len(joint_values):
        return jsonify({'error': 'Invalid joint index'}), 400
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid input'}), 400
    if 'delta' in data:
        joint_values[idx] += data['delta']
    elif 'value' in data:
        joint_values[idx] = data['value']
    else:
        return jsonify({'error': 'Invalid input'}), 400
    print(joint_values)
    return jsonify({'status': 'ok', 'values': joint_values})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050) 