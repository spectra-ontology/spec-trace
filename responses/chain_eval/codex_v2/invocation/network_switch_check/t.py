import socket, os, sys
s = socket.socket(); s.settimeout(3)
try:
    s.connect(("127.0.0.1", 7687)); print("tcp ok")
except Exception as e: print("tcp fail", type(e).__name__, e)
try:
    open(os.path.expanduser("~/x_should_fail_write"), "w"); print("home write ok (bad)")
except Exception as e: print("home write fail", type(e).__name__)
