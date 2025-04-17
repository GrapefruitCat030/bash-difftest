#!/usr/bin/env python3

# execute: nohup python3 monitor.py > monitor.log 2>&1 &

import psutil
import time
from datetime import datetime

# config
CPU_THRESHOLD = 90
MIN_LIFETIME = 10
CHECK_INTERVAL = 5

shell_lst = [
    "/home/njucs/project/bash-difftest/shell/dash-0.5.12/dash",
    "/home/njucs/project/bash-difftest/shell/bash-5.1/bash",
]

def is_shell_proc(proc):
    try:
        return proc.exe() in shell_lst
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False

def monitor():
    while True:
        now = time.time()
        for proc in psutil.process_iter(['pid', 'name', 'create_time']):
            if not is_shell_proc(proc):
                continue
            try:
                print(is_shell_proc(proc))
                print(proc)

                lifetime = now - proc.info['create_time']
                if lifetime < MIN_LIFETIME:
                    continue
                
                print(f"[{datetime.now()}] Kill {proc.name()}(pid={proc.pid}) "
                        f"lifetime={lifetime:.1f}s")
                proc.kill()
            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor()