import sys
import threading
import time
import os
#consistent seg fault crash PoC for perf trampoline
def heavy_workload():
    """
    Runs continuous Python bytecode loops.
    This keeps the thread inside the 'py_trampoline_evaluator' function
    in the C runtime, making it vulnerable when the state is freed.
    """
    while True:
        # Simple arithmetic to keep the interpreter busy
        _ = sum(i * i for i in range(500))
        

def trigger_race():
    print(f"[+] PID: {os.getpid()}")
    print("[+] Spawning worker threads to occupy the evaluator...")
    
    # Spawn multiple threads to increase the probability that one is 
    # inside the critical section when we deactivate.
    for _ in range(8):
        t = threading.Thread(target=heavy_workload, daemon=True)
        t.start()

    print("[+] Starting toggle loop (Activate <-> Deactivate)...")
    print("[!] This may take a few seconds to crash the interpreter.")

    iteration = 0

    while True:
        sys.activate_stack_trampoline("perf")
        # No sleep, no prints, just pure race
        sys.deactivate_stack_trampoline()

if __name__ == "__main__":
    trigger_race()