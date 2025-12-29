# Use-After-Free in Python Perf Trampoline

**Bug Type:** Race Condition / Use-After-Free (UAF)  
**Component:** `Python/perf_trampoline.c`  
**Affected Versions:** Python 3.12, 3.13, 3.14 (Fixed in latest branch)

## Description
I discovered a **Race Condition** and **Use-After-Free (UAF)** vulnerability in Python's `perf_trampoline` implementation (used for Linux `perf` profiling support).

The vulnerability occurs when `sys.activate_stack_trampoline("perf")` and `sys.deactivate_stack_trampoline()` are toggled concurrently while multiple threads are executing Python bytecode.

## Root Cause
The crash happens because the runtime frees executable memory pages while worker threads are still using them:
1.  **Thread A** calls `sys.deactivate_stack_trampoline()`, which triggers `free_code_arenas` and eventually `munmap()` to release the memory.
2.  **Thread B** is simultaneously executing code or performing a stack unwind (e.g., `_Unwind_ForcedUnwind`) inside that exact memory region.
3.  **Result:** The memory is unmapped while the instruction pointer (IP) is still inside it, leading to an immediate **SIGSEGV** (Python 3.12) or **SystemError** (Python 3.13+).

## Impact
* **Python 3.12:** Immediate Segmentation Fault (SIGSEGV).
* **Python 3.13 / 3.14:** Interpreter crash with `SystemError: error return without exception set`.

## Proof of Concept
The included `poc.py` reproduces the race condition by spinning up threads that execute a dummy function while the main thread rapidly toggles the trampoline state. Pinning the process to a single core (`taskset -c 0`) increases the likelihood of hitting the specific thread interleaving required to trigger the UAF.

```bash
# How to run the PoC
taskset -c 0 python3 poc.py
```

## Status
Reported to the Python Security Team and fixed in PR #143233.

* **Issue Tracker:** [python/cpython#143228](https://github.com/python/cpython/issues/143228)
* **Fix Commit:** [3ccc76f](https://github.com/python/cpython/commit/3ccc76f)
