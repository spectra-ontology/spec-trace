"""Keep the native scheduler bytes and replace only its observation transport."""
from pathlib import Path
import runpy
import sys

from fresh_windows_memory import host_guard

HERE = Path(__file__).resolve().parent
BASE = next(p for p in HERE.parents if p.name == 'overnight_reaudit')
sys.path.insert(0, str(BASE))
import capture_native

capture_native.host_guard = host_guard
controller = HERE / 'AUTH33_root_guarded_native_execution.py'
runpy.run_path(str(controller), run_name='__main__')
