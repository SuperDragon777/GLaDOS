import subprocess
import sys
import threading
import os
import time
import signal
from typing import Optional, List, Callable, Dict, Any

class ParallelRunner:
    def __init__(self):
        self.processes = {}
        self.lock = threading.Lock()
    
    def run(
        self,
        script_name: str,
        args: Optional[List[str]] = None,
        show_output: bool = True,
        callback: Optional[Callable[[str], None]] = None,
        wait: bool = False,
        tag: Optional[str] = None
    ) -> str:
        
        if not os.path.exists(script_name):
            raise FileNotFoundError(f"Файл не найден: {script_name}")
        
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        process_id = tag or f"proc_{process.pid}"
        
        with self.lock:
            self.processes[process_id] = {
                'process': process,
                'thread': None,
                'running': True
            }
        
        def read_output():
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output = line.rstrip('\n')
                    if show_output and callback:
                        callback(output)
                    elif show_output:
                        print(f"[{process_id}]: {output}")
                    elif callback:
                        callback(output)
            
            with self.lock:
                if process_id in self.processes:
                    self.processes[process_id]['running'] = False
        
        thread = threading.Thread(target=read_output)
        thread.daemon = True
        thread.start()
        
        with self.lock:
            self.processes[process_id]['thread'] = thread
        
        if wait:
            process.wait()
            thread.join()
        
        return process_id
    
    def stop(self, process_id: str, force: bool = False) -> bool:
        with self.lock:
            if process_id not in self.processes:
                return False
            
            proc_info = self.processes[process_id]
            process = proc_info['process']
        
        if process.poll() is None:
            if force:
                process.kill()
            else:
                process.terminate()
            
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                if force:
                    process.kill()
                    process.wait()
            
            with self.lock:
                del self.processes[process_id]
            
            return True
        
        with self.lock:
            del self.processes[process_id]
        
        return True
    
    def stop_all(self, force: bool = False):
        with self.lock:
            ids = list(self.processes.keys())
        
        for pid in ids:
            self.stop(pid, force)
    
    def is_running(self, process_id: str) -> bool:
        with self.lock:
            if process_id not in self.processes:
                return False
            
            proc_info = self.processes[process_id]
            process = proc_info['process']
        
        return process.poll() is None
    
    def list(self) -> Dict[str, Any]:
        result = {}
        with self.lock:
            for pid, info in self.processes.items():
                process = info['process']
                result[pid] = {
                    'pid': process.pid,
                    'running': process.poll() is None,
                    'returncode': process.poll(),
                    'alive': info['running']
                }
        return result
    
    def wait(self, process_id: str, timeout: Optional[float] = None) -> Optional[int]:
        with self.lock:
            if process_id not in self.processes:
                return None
            process = self.processes[process_id]['process']
        
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            return None
    
    def wait_all(self, timeout: Optional[float] = None):
        with self.lock:
            processes = [info['process'] for info in self.processes.values()]
        
        for process in processes:
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                continue


_runner = ParallelRunner()

def run(script: str, *args, wait: bool = False, tag: Optional[str] = None) -> str:
    return _runner.run(script, list(args), wait=wait, tag=tag)

def stop(pid: str, force: bool = False):
    return _runner.stop(pid, force)

def stop_all(force: bool = False):
    _runner.stop_all(force)

def kill(pid: str):
    return _runner.stop(pid, force=True)

def kill_all():
    _runner.stop_all(force=True)

def is_running(pid: str) -> bool:
    return _runner.is_running(pid)

def list_processes() -> Dict[str, Any]:
    return _runner.list()

def wait(pid: str, timeout: Optional[float] = None) -> Optional[int]:
    return _runner.wait(pid, timeout)

def wait_all(timeout: Optional[float] = None):
    _runner.wait_all(timeout)


class Script:
    def __init__(self, script_name: str, *args, **kwargs):
        self.script_name = script_name
        self.args = args
        self.kwargs = kwargs
        self.pid = None
    
    def __enter__(self):
        self.pid = run(self.script_name, *self.args, **self.kwargs)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pid and is_running(self.pid):
            stop(self.pid)
    
    def stop(self):
        if self.pid:
            stop(self.pid)
    
    def is_alive(self):
        if self.pid:
            return is_running(self.pid)
        return False