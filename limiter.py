import sys
import ctypes
import subprocess
import time
import threading

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    input("У вас нет прав администратора. Запустите скрипт с правами администратора.")
    sys.exit(1)

def kill_process(process_name):
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", process_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=0x08000000,
            timeout=0.5
        )
    except:
        pass

def process_killer(stop_event):
    while not stop_event.is_set():
        kill_process("taskmgr.exe")
        time.sleep(0.1)

try:
    print("Скрипт запущен")
    
    stop_event = threading.Event()
    thread = threading.Thread(target=process_killer, args=(stop_event,), daemon=True)
    thread.start()
    
    while thread.is_alive():
        time.sleep(0.5)
        
except KeyboardInterrupt:
    print("\nОстановка...")
    stop_event.set()
    thread.join(timeout=1)
    print("Скрипт выключен")