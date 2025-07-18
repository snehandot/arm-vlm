import requests
import time

class RobotArmClient:
    def __init__(self, host='localhost', port=5050):
        self.base_url = f'http://{host}:{port}'

    def get_joints(self):
        resp = requests.get(f'{self.base_url}/joints')
        resp.raise_for_status()
        return resp.json()

    def set_joints(self, values):
        resp = requests.post(f'{self.base_url}/joints', json={'values': values})
        resp.raise_for_status()
        return resp.json()

    def set_joint(self, idx, value):
        resp = requests.post(f'{self.base_url}/joint/{idx}', json={'value': value})
        resp.raise_for_status()
        return resp.json()

# Example usage:
if __name__ == '__main__':
    client = RobotArmClient()
    increment = 1  # degrees to increase each joint per second
    try:
        while True:
            joints = client.get_joints()
            # Increase each joint by increment, wrap at 360
            new_joints = [(v + increment) % 360 for v in joints]
            print('Setting joints to:', new_joints)
            client.set_joints(new_joints)
            time.sleep(1)
    except KeyboardInterrupt:
        print('Stopped by user.') 