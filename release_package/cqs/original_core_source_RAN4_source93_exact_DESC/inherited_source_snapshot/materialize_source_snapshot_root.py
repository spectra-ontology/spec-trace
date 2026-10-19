"""Isolated standard-library entrypoint; no native/API."""
import importlib.util, sys
from pathlib import Path
sys.dont_write_bytecode=True
p=Path(__file__).resolve().with_name('source_snapshot_common.py')
s=importlib.util.spec_from_file_location('source_snapshot_common',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
if __name__=='__main__':m.materialize_main()

