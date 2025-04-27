#!/usr/bin/env python3

# execute: nohup python3 monitor.py > monitor.log 2>&1 &

import os
import psutil
import time
from datetime import datetime

# config
CPU_THRESHOLD = 90
MIN_LIFETIME = 15
CHECK_INTERVAL = 10

shell_lst = [
    "/workspace/shell/dash-0.5.12/src/dash",
    "/workspace/shell/bash-5.2/bash",
]

def is_shell_proc(proc):
    try:
        exe_path = os.path.realpath(proc.exe())
        return exe_path in shell_lst
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False

def monitor():
    while True:
        now = time.time()
        for proc in psutil.process_iter(['pid', 'name', 'create_time', 'exe']):
            if not is_shell_proc(proc):
                continue
            try:
                lifetime = now - proc.info['create_time']
                if lifetime < MIN_LIFETIME:
                    continue
                
                print(f"[{datetime.now()}] Kill {proc.name()} {proc.cmdline()} (pid={proc.pid} exe={proc.exe()}) "
                        f"lifetime={lifetime:.1f}s")
                proc.kill()
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()