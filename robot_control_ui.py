import tkinter as tk
from tkinter import ttk
import requests

API_URL = 'http://localhost:5050'

class RobotArmUI:
    def __init__(self, root):
        self.root = root
        self.root.title('Robot Arm Joint Control')
        self.joint_vars = [tk.DoubleVar(value=0) for _ in range(6)]
        self.create_widgets()
        self.refresh_joints()

    def create_widgets(self):
        mainframe = ttk.Frame(self.root, padding="10 10 10 10")
        mainframe.grid(row=0, column=0, sticky="nwes")

        for i in range(6):
            ttk.Label(mainframe, text=f'Joint {i}').grid(row=i, column=0, sticky="w")
            slider = ttk.Scale(mainframe, from_=0, to=360, variable=self.joint_vars[i], orient=tk.HORIZONTAL, length=200)
            slider.grid(row=i, column=1, sticky="we")
            entry = ttk.Entry(mainframe, textvariable=self.joint_vars[i], width=6)
            entry.grid(row=i, column=2, sticky="w")

        set_btn = ttk.Button(mainframe, text='Set', command=self.set_joints)
        set_btn.grid(row=6, column=1, sticky=tk.E)
        refresh_btn = ttk.Button(mainframe, text='Refresh', command=self.refresh_joints)
        refresh_btn.grid(row=6, column=2, sticky=tk.W)

        self.status_label = ttk.Label(mainframe, text='')
        self.status_label.grid(row=7, column=0, columnspan=3, sticky=tk.W)

    def set_joints(self):
        values = [var.get() for var in self.joint_vars]
        try:
            resp = requests.post(f'{API_URL}/joints', json={'values': values}, timeout=2)
            resp.raise_for_status()
            self.status_label.config(text='Joints updated!', foreground='green')
        except Exception as e:
            self.status_label.config(text=f'Error: {e}', foreground='red')

    def refresh_joints(self):
        try:
            resp = requests.get(f'{API_URL}/joints', timeout=2)
            resp.raise_for_status()
            joints = resp.json()
            for i in range(6):
                self.joint_vars[i].set(joints[i])
            self.status_label.config(text='Joints refreshed.', foreground='blue')
        except Exception as e:
            self.status_label.config(text=f'Error: {e}', foreground='red')

def main():
    root = tk.Tk()
    app = RobotArmUI(root)
    root.mainloop()

if __name__ == '__main__':
    main() 