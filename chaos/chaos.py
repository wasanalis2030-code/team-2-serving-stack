import time
import urllib.request

TARGET = "http://localhost:8000/crash"

print("Chaos started", flush=True)

while True:
    time.sleep(11)
    print("Chaos: crashing serving...", flush=True)

    try:
        urllib.request.urlopen(TARGET, timeout=3)
    except Exception:
        print("Chaos: serving crashed", flush=True)